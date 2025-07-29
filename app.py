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
import uuid
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# Import question databases and helper functions from separate files
from question_data import TRL_QUESTIONS, IRL_QUESTIONS, MRL_QUESTIONS, TCP_QUESTIONS
from database_functions import (
    get_db_connection, init_database, save_assessment_to_db, 
    get_all_pdfs, get_pdf_by_id, save_pdf_to_db, get_statistics
)
from assessment_functions import (
    assess_standard, assess_tcp_enhanced, generate_enhanced_explanation,
    get_mode_full_name
)
from pdf_functions import create_enhanced_pdf
from email_functions import EmailManager

# Initialize database and email manager
init_database()
email_manager = EmailManager()

# Helper Functions
def get_client_ip_address():
    try:
        x_forwarded_for = request.environ.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.environ.get('REMOTE_ADDR')
    except Exception as e:
        return None

# ROUTES
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/overview")
def overview():
    try:
        stats = get_statistics()
        return render_template("overview.html", stats=stats)
    except Exception as e:
        print(f"Error in overview route: {e}")
        empty_stats = {'total_assessments': 0, 'assessments_by_type': [], 'completion_rate': 0}
        return render_template("overview.html", stats=empty_stats)

@app.route("/admin/statistics")
def admin_statistics():
    try:
        stats = get_statistics()
        return render_template("admin_statistics.html", stats=stats)
    except Exception as e:
        print(f"Error in admin_statistics route: {e}")
        empty_stats = {'total_assessments': 0, 'assessments_by_type': [], 'completion_rate': 0}
        return render_template("admin_statistics.html", stats=empty_stats)

@app.route("/admin/pdfs")
def admin_pdfs():
    try:
        pdfs = get_all_pdfs()
        admin_email = os.getenv('ADMIN_EMAIL')
        return render_template("admin_pdfs.html", pdfs=pdfs, admin_email=admin_email)
    except Exception as e:
        print(f"Error in admin_pdfs route: {e}")
        return render_template("admin_pdfs.html", pdfs=[], admin_email=None)

@app.route("/admin/pdf/<int:assessment_id>")
def download_pdf(assessment_id):
    try:
        pdf_data, filename = get_pdf_by_id(assessment_id)
        if pdf_data and filename:
            return send_file(
                io.BytesIO(pdf_data),
                mimetype="application/pdf",
                as_attachment=True,
                download_name=filename
            )
        else:
            return "PDF not found", 404
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        return "Error downloading PDF", 500

@app.route("/api/statistics")
def api_statistics():
    try:
        stats = get_statistics()
        return jsonify(stats)
    except Exception as e:
        print(f"Error in api_statistics: {e}")
        return jsonify({'error': 'Database connection failed'})

@app.route("/consent")
def consent_page():
    return render_template("consent.html")

@app.route("/api/consent", methods=["POST"])
def handle_consent():
    data = request.json
    session_id = str(uuid.uuid4())
    return jsonify({"session_id": session_id, "consent_given": data.get("consent", False)})

@app.route("/api/questions/<mode>/<language>")
def get_questions(mode, language):
    if mode.upper() == "TRL":
        return jsonify(TRL_QUESTIONS.get(language.lower(), TRL_QUESTIONS["english"]))
    elif mode.upper() == "IRL":
        return jsonify(IRL_QUESTIONS.get(language.lower(), IRL_QUESTIONS["english"]))
    elif mode.upper() == "MRL":
        return jsonify(MRL_QUESTIONS.get(language.lower(), MRL_QUESTIONS["english"]))
    elif mode.upper() == "TCP":
        return jsonify(TCP_QUESTIONS.get(language.lower(), TCP_QUESTIONS["english"]))
    return jsonify([])

@app.route("/api/assess", methods=["POST"])
def assess_technology():
    data = request.json
    mode = data["mode"]
    
    if mode.upper() == "TCP":
        return assess_tcp_enhanced(data)
    else:
        return assess_standard(data)

@app.route("/api/generate_pdf", methods=["POST"])
def generate_pdf():
    try:
        data = request.json
        print(f"📄 Enhanced PDF Generation - Mode: {data.get('mode', 'Unknown')}")
        
        if not data or 'mode' not in data:
            return jsonify({"error": "Invalid data provided"}), 400
        
        # Generate enhanced PDF
        buf = create_enhanced_pdf(data)
        
        # Generate filename
        now = datetime.now()
        date_str = now.strftime('%m%d%y')
        tech_title = data.get('technology_title', 'Assessment').replace(' ', '_').replace('/', '_')
        filename = f"{date_str}_{tech_title}_Enhanced.pdf"
        
        # Save to database
        assessment_data = {
            'session_id': data.get('session_id'),
            'mode': data['mode'],
            'technology_title': data.get('technology_title'),
            'description': data.get('description'),
            'level': data.get('level'),
            'recommended_pathway': data.get('recommended_pathway'),
            'language': data.get('language', 'english'),
            'timestamp': now.isoformat(),
            'ip_address': get_client_ip_address(),
            'user_agent': request.headers.get('User-Agent'),
            'consent_given': data.get('consent_given', True),
            'tcp_data': data.get('tcp_data'),
            'answers': data.get('answers')
        }
        
        assessment_id = save_assessment_to_db(assessment_data, data.get('answers', []))
        
        if assessment_id:
            buf_for_db = io.BytesIO(buf.getvalue())
            save_pdf_to_db(buf_for_db, filename, assessment_id)
        
        # Send enhanced email
        buf_for_email = io.BytesIO(buf.getvalue())
        email_manager.send_pdf_email(buf_for_email, filename, assessment_data)
        
        buf.seek(0)
        return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"❌ Enhanced PDF Generation Error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"PDF generation failed: {e}"}), 500

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
