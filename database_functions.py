import os
import psycopg
from psycopg.rows import dict_row
from datetime import datetime

def get_db_connection():
    """Get PostgreSQL database connection using psycopg3"""
    try:
        host = os.getenv('DATABASE_HOST')
        dbname = os.getenv('DATABASE_NAME')
        user = os.getenv('DATABASE_USER')
        password = os.getenv('DATABASE_PASSWORD')
        port = int(os.getenv('DATABASE_PORT', 5432))
        
        if not all([host, dbname, user, password]):
            print("Missing required database environment variables!")
            return None
        
        conn = psycopg.connect(
            host=host,
            dbname=dbname,
            user=user,
            password=password,
            port=port,
            connect_timeout=10
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize PostgreSQL database with required tables"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
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
                    ip_address INET,
                    user_agent TEXT,
                    consent_given BOOLEAN DEFAULT TRUE,
                    completed BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    pdf_data BYTEA,
                    pdf_filename VARCHAR(255)
                )
            ''')
            
            cur.execute('ALTER TABLE assessments ADD COLUMN IF NOT EXISTS pdf_data BYTEA')
            cur.execute('ALTER TABLE assessments ADD COLUMN IF NOT EXISTS pdf_filename VARCHAR(255)')
            
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
            
            cur.execute('CREATE INDEX IF NOT EXISTS idx_assessments_timestamp ON assessments(timestamp)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_assessments_type ON assessments(assessment_type)')
            
            conn.commit()
            print("Database initialized successfully!")
            
    except Exception as e:
        print(f"Database initialization error: {e}")
        conn.rollback()
    finally:
        conn.close()

def save_pdf_to_db(pdf_buffer, filename, assessment_id):
    """Save PDF to database"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            pdf_data = pdf_buffer.getvalue()
            cur.execute('''
                UPDATE assessments 
                SET pdf_data = %s, pdf_filename = %s 
                WHERE id = %s
            ''', (pdf_data, filename, assessment_id))
            conn.commit()
            print(f"💾 Enhanced PDF saved: {filename}")
            return True
    except Exception as e:
        print(f"Error saving PDF: {e}")
        return False
    finally:
        conn.close()

def get_all_pdfs():
    """Get all PDFs from database for admin view"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute('''
                SELECT id, technology_title, assessment_type, pdf_filename, 
                       timestamp, language, level_achieved, recommended_pathway
                FROM assessments 
                WHERE pdf_data IS NOT NULL 
                ORDER BY timestamp DESC
            ''')
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        print(f"Error getting PDFs: {e}")
        return []
    finally:
        conn.close()

def get_pdf_by_id(assessment_id):
    """Get specific PDF from database"""
    conn = get_db_connection()
    if not conn:
        return None, None
    
    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT pdf_data, pdf_filename 
                FROM assessments 
                WHERE id = %s AND pdf_data IS NOT NULL
            ''', (assessment_id,))
            result = cur.fetchone()
            if result:
                return result[0], result[1]
            return None, None
    except Exception as e:
        print(f"Error getting PDF by ID: {e}")
        return None, None
    finally:
        conn.close()

def get_statistics():
    """Get comprehensive statistics from PostgreSQL database"""
    conn = get_db_connection()
    if not conn:
        return {
            'total_assessments': 0,
            'assessments_by_type': [],
            'completion_rate': 0
        }
    
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute('SELECT COUNT(*) as count FROM assessments WHERE completed = true')
            result = cur.fetchone()
            total = result['count'] if result else 0
            
            cur.execute('SELECT assessment_type, COUNT(*) as count FROM assessments WHERE completed = true GROUP BY assessment_type ORDER BY count DESC')
            by_type = cur.fetchall()
            
            cur.execute('SELECT COUNT(*) as count FROM assessments')
            total_started_result = cur.fetchone()
            total_started = total_started_result['count'] if total_started_result else 0
            
            completion_rate = (total / total_started * 100) if total_started > 0 else 0
            
            return {
                'total_assessments': total,
                'assessments_by_type': [dict(row) for row in by_type],
                'completion_rate': round(completion_rate, 2)
            }
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {
            'total_assessments': 0,
            'assessments_by_type': [],
            'completion_rate': 0
        }
    finally:
        conn.close()

def save_assessment_to_db(assessment_data, answers_data):
    """Save assessment to database"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO assessments (
                    session_id, assessment_type, technology_title, description,
                    level_achieved, recommended_pathway, language, timestamp,
                    ip_address, user_agent, consent_given, completed
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                assessment_data.get('session_id'),
                assessment_data.get('mode'),
                assessment_data.get('technology_title'),
                assessment_data.get('description'),
                assessment_data.get('level'),
                assessment_data.get('recommended_pathway'),
                assessment_data.get('language'),
                assessment_data.get('timestamp'),
                assessment_data.get('ip_address'),
                assessment_data.get('user_agent'),
                assessment_data.get('consent_given', True),
                True
            ))
            
            assessment_id = cur.fetchone()[0]
            
            if assessment_data.get('mode') == 'TCP':
                tcp_data = assessment_data.get('tcp_data', {})
                answers = assessment_data.get('answers', [])
                answer_idx = 0
                
                for dimension in tcp_data.get('dimensions', []):
                    for q_idx, question in enumerate(dimension['questions']):
                        if answer_idx < len(answers):
                            cur.execute('''
                                INSERT INTO tcp_answers (assessment_id, dimension_name, question_index, score)
                                VALUES (%s, %s, %s, %s)
                            ''', (assessment_id, dimension['name'], q_idx, answers[answer_idx]))
                            answer_idx += 1
            else:
                answers = assessment_data.get('answers', [])
                for level_idx, level_answers in enumerate(answers):
                    for q_idx, answer in enumerate(level_answers):
                        cur.execute('''
                            INSERT INTO assessment_answers (assessment_id, level_number, question_index, answer)
                            VALUES (%s, %s, %s, %s)
                        ''', (assessment_id, level_idx, q_idx, answer))
            
            conn.commit()
            return assessment_id
    except Exception as e:
        print(f"Error saving assessment: {e}")
        return None
    finally:
        conn.close()
