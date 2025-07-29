from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime, timedelta
import io
import traceback
import json
import os
from threading import Lock
import uuid
from collections import defaultdict
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Drive Integration
try:
    from googleapiclient.discovery import build
    from google.oauth2.service_account import Credentials
    from googleapiclient.http import MediaIoBaseUpload
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False
    print("Google Drive libraries not installed. Install with: pip install google-api-python-client google-auth")

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Database connection
def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DATABASE_HOST'),
            database=os.getenv('DATABASE_NAME'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('DATABASE_PASSWORD'),
            port=os.getenv('DATABASE_PORT', 5432)
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Database initialization
def init_database():
    """Initialize PostgreSQL database with required tables"""
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database!")
        return
    
    try:
        with conn.cursor() as cur:
            # Create assessments table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS assessments (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255),
                    assessment_type VARCHAR(10),
                    technology_title VARCHAR(500),
                    description TEXT,
                    level_achieved INTEGER,
                    recommended_pathway VARCHAR(100),
                    language VARCHAR(10),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    google_drive_link VARCHAR(1000),
                    ip_address INET,
                    user_agent TEXT,
                    consent_given BOOLEAN DEFAULT TRUE,
                    completed BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create assessment_answers table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS assessment_answers (
                    id SERIAL PRIMARY KEY,
                    assessment_id INTEGER REFERENCES assessments(id) ON DELETE CASCADE,
                    level_number INTEGER,
                    question_index INTEGER,
                    answer BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create tcp_answers table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS tcp_answers (
                    id SERIAL PRIMARY KEY,
                    assessment_id INTEGER REFERENCES assessments(id) ON DELETE CASCADE,
                    dimension_name VARCHAR(100),
                    question_index INTEGER,
                    score INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cur.execute('CREATE INDEX IF NOT EXISTS idx_assessments_timestamp ON assessments(timestamp)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_assessments_type ON assessments(assessment_type)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_assessments_completed ON assessments(completed)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_assessments_created_at ON assessments(created_at)')
            
            conn.commit()
            print("Database initialized successfully!")
            
    except Exception as e:
        print(f"Database initialization error: {e}")
        conn.rollback()
    finally:
        conn.close()

# Initialize database on startup
init_database()

# [Keep all the question databases from previous implementation]
# TRL_QUESTIONS, IRL_QUESTIONS, MRL_QUESTIONS, TCP_QUESTIONS...

# Google Drive Manager (same as before)
class GoogleDriveManager:
    def __init__(self):
        self.service = None
        self.root_folder_id = None
        self._initialize_service()
    
    def _initialize_service(self):
        if not GOOGLE_DRIVE_AVAILABLE:
            print("Google Drive integration disabled - missing dependencies")
            return
            
        try:
            if os.path.exists('google-drive-credentials.json'):
                credentials = Credentials.from_service_account_file(
                    'google-drive-credentials.json',
                    scopes=['https://www.googleapis.com/auth/drive']
                )
                self.service = build('drive', 'v3', credentials=credentials)
                self._setup_folder_structure()
                print("Google Drive integration initialized successfully")
            else:
                print("Google Drive credentials file not found")
        except Exception as e:
            print(f"Failed to initialize Google Drive: {str(e)}")
    
    def _setup_folder_structure(self):
        if not self.service:
            return
            
        try:
            # Find or create root folder
            root_folder_name = "MMSU Technology Assessment Reports"
            folders = self.service.files().list(
                q=f"name='{root_folder_name}' and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name)"
            ).execute().get('files', [])
            
            if folders:
                self.root_folder_id = folders[0]['id']
            else:
                # Create root folder
                folder_metadata = {
                    'name': root_folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                self.root_folder_id = folder.get('id')
                
                # Make folder publicly viewable
                permission = {
                    'type': 'anyone',
                    'role': 'reader'
                }
                self.service.permissions().create(
                    fileId=self.root_folder_id,
                    body=permission
                ).execute()
                
        except Exception as e:
            print(f"Error setting up folder structure: {str(e)}")
    
    def _get_or_create_folder(self, parent_folder_id, folder_name):
        if not self.service:
            return None
            
        try:
            # Check if folder exists
            folders = self.service.files().list(
                q=f"name='{folder_name}' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name)"
            ).execute().get('files', [])
            
            if folders:
                return folders[0]['id']
            else:
                # Create folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_folder_id]
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                return folder.get('id')
                
        except Exception as e:
            print(f"Error creating folder {folder_name}: {str(e)}")
            return None
    
    def upload_pdf(self, pdf_buffer, filename, assessment_type, timestamp):
        if not self.service or not self.root_folder_id:
            return None
            
        try:
            # Create folder structure: Year/Month/AssessmentType
            year = timestamp.strftime('%Y')
            month = timestamp.strftime('%B')
            
            year_folder_id = self._get_or_create_folder(self.root_folder_id, year)
            if not year_folder_id:
                return None
                
            month_folder_id = self._get_or_create_folder(year_folder_id, month)
            if not month_folder_id:
                return None
                
            type_folder_id = self._get_or_create_folder(month_folder_id, assessment_type.upper())
            if not type_folder_id:
                return None
            
            # Upload file
            media = MediaIoBaseUpload(pdf_buffer, mimetype='application/pdf')
            file_metadata = {
                'name': filename,
                'parents': [type_folder_id]
            }
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink'
            ).execute()
            
            # Make file publicly viewable
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            self.service.permissions().create(
                fileId=file.get('id'),
                body=permission
            ).execute()
            
            return file.get('webViewLink')
            
        except Exception as e:
            print(f"Error uploading to Google Drive: {str(e)}")
            return None
    
    def get_public_folder_link(self):
        if self.root_folder_id:
            return f"https://drive.google.com/drive/folders/{self.root_folder_id}"
        return None

# Initialize Google Drive Manager
drive_manager = GoogleDriveManager()

# Statistics Functions (Updated for PostgreSQL)
def get_statistics():
    """Get comprehensive statistics from PostgreSQL database"""
    conn = get_db_connection()
    if not conn:
        return {}
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Total assessments
            cur.execute('SELECT COUNT(*) as count FROM assessments WHERE completed = true')
            total = cur.fetchone()['count']
            
            # Assessments by type
            cur.execute('''
                SELECT assessment_type, COUNT(*) as count 
                FROM assessments 
                WHERE completed = true 
                GROUP BY assessment_type
                ORDER BY count DESC
            ''')
            by_type = cur.fetchall()
            
            # Monthly statistics (last 12 months)
            cur.execute('''
                SELECT 
                    TO_CHAR(timestamp, 'YYYY-MM') as month,
                    assessment_type,
                    COUNT(*) as count
                FROM assessments 
                WHERE completed = true AND timestamp >= CURRENT_DATE - INTERVAL '12 months'
                GROUP BY TO_CHAR(timestamp, 'YYYY-MM'), assessment_type
                ORDER BY month
            ''')
            monthly = cur.fetchall()
            
            # Success rates (average levels achieved)
            cur.execute('''
                SELECT 
                    assessment_type,
                    ROUND(AVG(level_achieved)::numeric, 2) as avg_level,
                    COUNT(*) as count
                FROM assessments 
                WHERE completed = true AND level_achieved IS NOT NULL
                GROUP BY assessment_type
            ''')
            success_rates = cur.fetchall()
            
            # TCP pathway distribution
            cur.execute('''
                SELECT 
                    recommended_pathway,
                    COUNT(*) as count
                FROM assessments 
                WHERE completed = true AND assessment_type = 'TCP' AND recommended_pathway IS NOT NULL
                GROUP BY recommended_pathway
                ORDER BY count DESC
            ''')
            tcp_pathways = cur.fetchall()
            
            # Recent activity (last 20 assessments)
            cur.execute('''
                SELECT 
                    assessment_type,
                    technology_title,
                    level_achieved,
                    recommended_pathway,
                    timestamp,
                    language
                FROM assessments 
                WHERE completed = true
                ORDER BY timestamp DESC 
                LIMIT 20
            ''')
            recent = cur.fetchall()
            
            # Completion rates
            cur.execute('SELECT COUNT(*) as count FROM assessments')
            total_started = cur.fetchone()['count']
            completion_rate = (total / total_started * 100) if total_started > 0 else 0
            
            # Geographic distribution (by IP address prefix)
            cur.execute('''
                SELECT 
                    HOST(ip_address) as ip_address,
                    COUNT(*) as count
                FROM assessments 
                WHERE completed = true AND ip_address IS NOT NULL
                GROUP BY HOST(ip_address)
                ORDER BY count DESC
                LIMIT 10
            ''')
            geographic = cur.fetchall()
            
            # Daily statistics for the last 30 days
            cur.execute('''
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as count
                FROM assessments 
                WHERE completed = true AND timestamp >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE(timestamp)
                ORDER BY date
            ''')
            daily_stats = cur.fetchall()
            
            return {
                'total_assessments': total,
                'assessments_by_type': [dict(row) for row in by_type],
                'monthly_statistics': [dict(row) for row in monthly],
                'success_rates': [dict(row) for row in success_rates],
                'tcp_pathways': [dict(row) for row in tcp_pathways],
                'recent_activity': [dict(row) for row in recent],
                'completion_rate': round(completion_rate, 2),
                'geographic_distribution': [dict(row) for row in geographic],
                'daily_statistics': [dict(row) for row in daily_stats],
                'total_started': total_started
            }
            
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {}
    finally:
        conn.close()

def save_assessment_to_db(assessment_data, answers_data, google_drive_link=None):
    """Save assessment data to PostgreSQL database"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            # Insert main assessment record
            cur.execute('''
                INSERT INTO assessments (
                    session_id, assessment_type, technology_title, description,
                    level_achieved, recommended_pathway, language, timestamp,
                    google_drive_link, ip_address, user_agent, consent_given, completed
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
