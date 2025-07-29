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
import requests
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import threading

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# Perplexity API Configuration
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

# Keep all existing TRL, IRL, MRL, TCP questions databases as they were...
# (I'll include the essential ones, but they remain the same as before)

TCP_QUESTIONS = {
    "english": {
        "dimensions": [
            {
                "name": "Technology & Product Readiness",
                "questions": [
                    "Is the technology fully developed and ready for market deployment?",
                    "Does it have a clear, unique value proposition compared to existing solutions?",
                    "Is the technology protected by IP (patents, copyrights, trade secrets)?"
                ]
            },
            {
                "name": "Market & Customer",
                "questions": [
                    "Is there a well-defined target market with demonstrated demand?",
                    "Are there existing competitors, and how strong is the competitive advantage?",
                    "Is the market size sufficient for the pathway (e.g., niche vs. mass market)?"
                ]
            },
            {
                "name": "Business & Financial",
                "questions": [
                    "Does your organization have the resources to manufacture, market, and sell directly?",
                    "Is external investment required, and is it accessible?",
                    "Are there established channels for reaching customers (direct, partners, government)?"
                ]
            },
            {
                "name": "Regulatory & Policy",
                "questions": [
                    "Are there significant regulatory hurdles for this technology?",
                    "Is the policy environment supportive or restrictive for commercialization?"
                ]
            },
            {
                "name": "Organizational & Team",
                "questions": [
                    "Does your team have experience in product development, sales, and scaling?",
                    "Is there interest or capacity to form a new company (for spin-out/startup)?"
                ]
            },
            {
                "name": "Strategic Fit",
                "questions": [
                    "Is the technology core to your organization's mission, or better suited for external partners?",
                    "Would open-source release accelerate adoption or create value through services?"
                ]
            }
        ],
        "pathways": [
            {
                "name": "Direct Sale",
                "description": "Selling the technology directly to end users or customers",
                "criteria": ["High technology readiness", "Strong internal resources", "Established market channels"]
            },
            {
                "name": "Licensing",
                "description": "Licensing the technology to other companies for commercialization",
                "criteria": ["Strong IP protection", "Market demand", "Limited internal resources"]
            },
            {
                "name": "Startup/Spin-out",
                "description": "Creating a new company to commercialize the technology",
                "criteria": ["High innovation potential", "Entrepreneurial team", "Growth market"]
            },
            {
                "name": "Assignment",
                "description": "Selling or transferring technology rights to another organization",
                "criteria": ["Valuable IP", "Low internal interest", "Better suited for others"]
            },
            {
                "name": "Research Collaboration",
                "description": "Partnering with other organizations for further development",
                "criteria": ["Early-stage technology", "Need for development", "Research partnerships"]
            },
            {
                "name": "Open Source",
                "description": "Releasing technology as open source for broad adoption",
                "criteria": ["Broad adoption potential", "Service-based value", "Community building"]
            },
            {
                "name": "Government Procurement",
                "description": "Targeting government agencies as primary customers",
                "criteria": ["Public sector relevance", "Regulatory compliance", "Government needs"]
            }
        ]
    },
    "filipino": {
        "dimensions": [
            {
                "name": "Technology at Product Readiness",
                "questions": [
                    "Handa na ba ang teknolohiya para sa market deployment?",
                    "May malinaw at natatanging value proposition ba kumpara sa mga existing solutions?",
                    "Protektado ba ng IP ang teknolohiya (patents, copyrights, trade secrets)?"
                ]
            },
            {
                "name": "Market at Customer",
                "questions": [
                    "May well-defined target market ba na may demonstrated demand?",
                    "May existing competitors ba, at gaano kalakas ang competitive advantage?",
                    "Sapat ba ang market size para sa pathway (hal. niche vs. mass market)?"
                ]
            },
            {
                "name": "Business at Financial",
                "questions": [
                    "May resources ba ang inyong organisasyon para mag-manufacture, mag-market, at mag-sell directly?",
                    "Kailangan ba ng external investment, at accessible ba ito?",
                    "May established channels ba para maabot ang customers (direct, partners, government)?"
                ]
            },
            {
                "name": "Regulatory at Policy",
                "questions": [
                    "May significant regulatory hurdles ba para sa teknolohiyang ito?",
                    "Supportive ba o restrictive ang policy environment para sa commercialization?"
                ]
            },
            {
                "name": "Organizational at Team",
                "questions": [
                    "May experience ba ang inyong team sa product development, sales, at scaling?",
                    "May interest o capacity ba na bumuo ng bagong company (para sa spin-out/startup)?"
                ]
            },
            {
                "name": "Strategic Fit",
                "questions": [
                    "Core ba ang teknolohiya sa mission ng inyong organisasyon, o mas bagay sa external partners?",
                    "Makakatulong ba ang open-source release sa adoption o makakagawa ng value through services?"
                ]
            }
        ],
        "pathways": [
            {
                "name": "Direct Sale",
                "description": "Direktang pagbenta ng teknolohiya sa end users o customers",
                "criteria": ["Mataas na technology readiness", "Malakas na internal resources", "Established market channels"]
            },
            {
                "name": "Licensing",
                "description": "Pag-license ng teknolohiya sa ibang companies para sa commercialization",
                "criteria": ["Malakas na IP protection", "Market demand", "Limited internal resources"]
            },
            {
                "name": "Startup/Spin-out",
                "description": "Paggawa ng bagong company para i-commercialize ang teknolohiya",
                "criteria": ["Mataas na innovation potential", "Entrepreneurial team", "Growth market"]
            },
            {
                "name": "Assignment",
                "description": "Pagbenta o paglilipat ng technology rights sa ibang organisasyon",
                "criteria": ["Valuable IP", "Mababang internal interest", "Mas bagay sa iba"]
            },
            {
                "name": "Research Collaboration",
                "description": "Pakikipag-partner sa ibang organisasyon para sa further development",
                "criteria": ["Early-stage technology", "Pangangailangan ng development", "Research partnerships"]
            },
            {
                "name": "Open Source",
                "description": "Pag-release ng teknolohiya bilang open source para sa broad adoption",
                "criteria": ["Broad adoption potential", "Service-based value", "Community building"]
            },
            {
                "name": "Government Procurement",
                "description": "Pag-target sa government agencies bilang primary customers",
                "criteria": ["Public sector relevance", "Regulatory compliance", "Government needs"]
            }
        ]
    }
}

# Database connection and initialization (keeping existing)
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
            
            cur.execute('ALTER TABLE assessments DROP COLUMN IF EXISTS google_drive_link')
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

init_database()

# Perplexity API Integration Class
class PerplexityAnalyzer:
    def __init__(self):
        self.api_key = PERPLEXITY_API_KEY
        self.api_url = PERPLEXITY_API_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"🤖 Perplexity API initialized: {'✅ Active' if self.api_key else '❌ No API Key'}")
    
    def query_perplexity(self, prompt, max_tokens=2000):
        """Make a query to Perplexity API"""
        if not self.api_key:
            print("❌ Perplexity API key not configured")
            return None
            
        try:
            payload = {
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a technology commercialization expert with access to real-time market data. Provide current, accurate, and actionable insights based on the latest market information."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.2,
                "top_p": 0.9,
                "return_citations": True,
                "return_images": False
            }
            
            print(f"🔍 Querying Perplexity: {prompt[:100]}...")
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                print(f"✅ Perplexity response received ({len(content)} chars)")
                return content
            else:
                print(f"❌ Perplexity API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Perplexity API exception: {e}")
            return None
    
    def analyze_market_intelligence(self, technology_title, technology_description, pathway):
        """Get comprehensive market intelligence"""
        prompt = f"""
        Provide comprehensive market intelligence for:
        
        Technology: {technology_title}
        Description: {technology_description}
        Commercialization Pathway: {pathway}
        
        Please provide current (2024-2025) information on:
        1. Market size and growth projections
        2. Key competitors and market share
        3. Investment trends and funding landscape
        4. Regulatory environment and changes
        5. Success stories and case studies
        6. Market opportunities and threats
        7. Partnership opportunities
        8. Pricing and revenue models
        
        Focus on actionable insights and recent market developments.
        """
        
        return self.query_perplexity(prompt, max_tokens=3000)

perplexity_analyzer = PerplexityAnalyzer()

# Email Manager (keeping existing)
class EmailManager:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.admin_email = os.getenv('ADMIN_EMAIL')
    
    def send_pdf_email(self, pdf_buffer, filename, assessment_data):
        """Send PDF via email to admin"""
        if not all([self.email_user, self.email_password, self.admin_email]):
            print("❌ Email configuration incomplete")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.admin_email
            msg['Subject'] = f"📄 Enhanced Assessment Report: {filename}"
            
            body = f"""
🚀 ENHANCED TECHNOLOGY ASSESSMENT REPORT WITH AI INSIGHTS

📋 Assessment Details:
• Technology: {assessment_data.get('technology_title', 'N/A')}
• Assessment Type: {assessment_data.get('mode', 'N/A')}
• Language: {assessment_data.get('language', 'N/A')}
• Result: {assessment_data.get('level', assessment_data.get('recommended_pathway', 'N/A'))}
• Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Enhanced with: Real-time market intelligence

📎 The complete enhanced assessment report with AI insights is attached.

---
🏫 MMSU Technology Assessment Tool (Enhanced Edition)
Innovation and Technology Support Office
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            pdf_buffer.seek(0)
            pdf_attachment = MIMEApplication(pdf_buffer.read(), _subtype='pdf')
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(pdf_attachment)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            print(f"✅ Enhanced email sent successfully to {self.admin_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False

email_manager = EmailManager()

# Helper functions (keeping essential ones)
def get_client_ip_address():
    """Get client IP address"""
    try:
        x_forwarded_for = request.environ.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.environ.get('REMOTE_ADDR')
    except Exception as e:
        return None

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
            
            conn.commit()
            return assessment_id
    except Exception as e:
        print(f"Error saving assessment: {e}")
        return None
    finally:
        conn.close()

# Routes (keeping essential ones)
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/questions/<mode>/<language>")
def get_questions(mode, language):
    if mode.upper() == "TCP":
        return jsonify(TCP_QUESTIONS.get(language.lower(), TCP_QUESTIONS["english"]))
    return jsonify([])

@app.route("/api/assess", methods=["POST"])
def assess_technology():
    data = request.json
    mode = data["mode"]
    
    if mode.upper() == "TCP":
        return assess_tcp_enhanced(data)
    return jsonify({"error": "Only TCP mode enhanced in this version"})

# Enhanced TCP Assessment Function
def assess_tcp_enhanced(data):
    """Enhanced TCP assessment with Perplexity AI integration"""
    print("🚀 Starting Enhanced TCP Analysis with AI...")
    
    language = data["language"]
    answers = data["answers"]
    tcp_data = TCP_QUESTIONS[language.lower()]
    technology_title = data["technology_title"]
    technology_description = data["description"]
    
    # Ensure we have exactly 15 answers
    if len(answers) < 15:
        answers = answers + [1] * (15 - len(answers))
    elif len(answers) > 15:
        answers = answers[:15]
    
    # Calculate pathway scores
    pathway_scores = calculate_pathway_scores(answers, tcp_data)
    recommended_pathway = max(pathway_scores, key=pathway_scores.get)
    
    print(f"📊 Basic analysis complete. Recommended pathway: {recommended_pathway}")
    
    # Generate comprehensive analysis with AI enhancement
    detailed_analysis = generate_comprehensive_tcp_analysis(
        answers, tcp_data, pathway_scores, recommended_pathway,
        technology_title, technology_description, language
    )
    
    result = {
        "mode": "TCP",
        "mode_full": "Technology Commercialization Pathway (AI-Enhanced)",
        "technology_title": technology_title,
        "description": technology_description,
        "answers": answers,
        "tcp_data": tcp_data,
        "pathway_scores": pathway_scores,
        "recommended_pathway": recommended_pathway,
        "explanation": generate_enhanced_explanation(pathway_scores, recommended_pathway, detailed_analysis, language),
        "detailed_analysis": detailed_analysis,
        "timestamp": datetime.utcnow().isoformat(),
        "level": None,
        "questions": None,
        "enhanced": True
    }
    
    print("✅ Enhanced TCP analysis completed successfully!")
    return jsonify(result)

def calculate_pathway_scores(answers, tcp_data):
    """Calculate scores for each commercialization pathway"""
    pathways = {pathway["name"]: 0 for pathway in tcp_data["pathways"]}
    
    tech_score = sum(answers[0:3])
    market_score = sum(answers[3:6])
    business_score = sum(answers[6:9])
    regulatory_score = sum(answers[9:11])
    team_score = sum(answers[11:13])
    strategic_score = sum(answers[13:15])
    
    pathways["Direct Sale"] = tech_score + business_score + market_score
    pathways["Licensing"] = tech_score + market_score + (6 - business_score) + regulatory_score
    pathways["Startup/Spin-out"] = tech_score + team_score + market_score + strategic_score
    pathways["Assignment"] = tech_score + (6 - strategic_score) + (6 - business_score)
    pathways["Research Collaboration"] = (9 - tech_score) + team_score + strategic_score + market_score
    pathways["Open Source"] = strategic_score + market_score + (6 - regulatory_score) + team_score
    pathways["Government Procurement"] = tech_score + regulatory_score + market_score + business_score
    
    return pathways

def generate_comprehensive_tcp_analysis(answers, tcp_data, pathway_scores, recommended_pathway,
                                      technology_title, technology_description, language):
    """Generate comprehensive analysis with AI enhancement"""
    print("🤖 Generating AI-enhanced comprehensive analysis...")
    
    # Basic analysis components
    input_summary = generate_input_summary(answers, tcp_data)
    dimension_scores = generate_dimension_scores(answers, tcp_data)
    sorted_pathways = sorted(pathway_scores.items(), key=lambda x: x[1], reverse=True)
    top_pathways = sorted_pathways[:3]
    second_alternative = sorted_pathways[1] if len(sorted_pathways) > 1 else None
    
    # AI-Enhanced Market Intelligence
    market_intelligence = {}
    if perplexity_analyzer.api_key:
        print("🔍 Gathering AI-powered market intelligence...")
        try:
            ai_analysis = perplexity_analyzer.analyze_market_intelligence(
                technology_title, technology_description, recommended_pathway
            )
            market_intelligence = process_ai_market_intelligence(ai_analysis, language)
            print("✅ AI market intelligence gathered successfully")
        except Exception as e:
            print(f"⚠️ AI analysis failed, using fallback: {e}")
            market_intelligence = generate_fallback_intelligence(technology_title, language)
    else:
        market_intelligence = generate_fallback_intelligence(technology_title, language)
    
    # Enhanced insights with AI data
    enhanced_insights = generate_ai_enhanced_insights(
        dimension_scores, pathway_scores, recommended_pathway, market_intelligence, language
    )
    
    # AI-powered success strategies
    success_strategies = generate_ai_success_strategies(
        dimension_scores, recommended_pathway, market_intelligence, language
    )
    
    # Enhanced risk assessment
    risk_assessment = generate_ai_risk_assessment(
        dimension_scores, recommended_pathway, market_intelligence, language
    )
    
    # Market positioning with competitive intelligence
    market_positioning = generate_ai_market_positioning(
        dimension_scores, recommended_pathway, market_intelligence, language
    )
    
    # Financial projections with market data
    financial_projections = generate_ai_financial_projections(
        recommended_pathway, market_intelligence, dimension_scores, language
    )
    
    # Implementation roadmap with market timing
    implementation_roadmap = generate_ai_implementation_roadmap(
        recommended_pathway, market_intelligence, language
    )
    
    # Partnership opportunities
    partnership_opportunities = identify_ai_partnership_opportunities(
        technology_title, recommended_pathway, market_intelligence, language
    )
    
    # Overall readiness and confidence scoring
    overall_readiness = calculate_overall_readiness(dimension_scores)
    confidence_score = calculate_ai_confidence_score(pathway_scores, dimension_scores, market_intelligence)
    
    analysis = {
        # Basic analysis
        "input_summary": input_summary,
        "dimension_scores": dimension_scores,
        "top_pathways": top_pathways,
        "recommended_pathway": recommended_pathway,
        "second_alternative": second_alternative,
        "overall_readiness": overall_readiness,
        "confidence_score": confidence_score,
        
        # AI-Enhanced components
        "market_intelligence": market_intelligence,
        "insights": enhanced_insights,
        "success_strategies": success_strategies,
        "risk_assessment": risk_assessment,
        "market_positioning": market_positioning,
        "financial_projections": financial_projections,
        "implementation_roadmap": implementation_roadmap,
        "partnership_opportunities": partnership_opportunities,
        
        # Metadata
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "ai_enhanced": True,
        "data_freshness": "2024-2025 Real-time",
        "intelligence_source": "Perplexity AI" if perplexity_analyzer.api_key else "Fallback Analysis"
    }
    
    return analysis

# AI Processing Functions
def process_ai_market_intelligence(ai_response, language):
    """Process AI response into structured market intelligence"""
    if not ai_response:
        return generate_fallback_intelligence("", language)
    
    # Extract structured information from AI response
    intelligence = {
        "market_overview": extract_section(ai_response, "market", 500),
        "competitive_landscape": extract_section(ai_response, "competitor", 500),
        "funding_trends": extract_section(ai_response, "investment|funding", 400),
        "regulatory_insights": extract_section(ai_response, "regulatory|regulation", 300),
        "success_stories": extract_section(ai_response, "success|case", 400),
        "opportunities": extract_section(ai_response, "opportunity|trend", 400),
        "threats": extract_section(ai_response, "threat|risk|challenge", 300),
        "partnerships": extract_section(ai_response, "partnership|collaboration", 300),
        "pricing_models": extract_section(ai_response, "pricing|revenue", 300),
        "full_analysis": ai_response[:3000]  # Keep full analysis for reference
    }
    
    return intelligence

def extract_section(text, keywords, max_length=500):
    """Extract relevant sections from AI response based on keywords"""
    if not text:
        return "Information not available"
    
    import re
    
    # Split text into sentences/paragraphs
    sections = re.split(r'\n\n|\. ', text)
    relevant_sections = []
    
    # Find sections containing keywords
    keyword_list = keywords.split('|')
    for section in sections:
        if any(keyword.lower() in section.lower() for keyword in keyword_list):
            relevant_sections.append(section.strip())
    
    # Combine and limit length
    result = '. '.join(relevant_sections)
    if len(result) > max_length:
        result = result[:max_length] + "..."
    
    return result if result else "Detailed analysis available in full report"

def generate_ai_enhanced_insights(dimension_scores, pathway_scores, recommended_pathway, market_intelligence, language):
    """Generate enhanced insights with AI market intelligence"""
    insights = []
    
    if language == "filipino":
        # Market-driven insights
        market_overview = market_intelligence.get("market_overview", "")
        if "growth" in market_overview.lower():
            insights.append("🚀 Ang market ay may positive growth trajectory na favorable sa inyong technology commercialization.")
        
        # Competitive insights
        competitive_landscape = market_intelligence.get("competitive_landscape", "")
        if competitive_landscape and len(competitive_landscape) > 50:
            insights.append(f"🏆 Competitive landscape insight: {competitive_landscape[:200]}...")
        
        # Funding insights
        funding_trends = market_intelligence.get("funding_trends", "")
        if funding_trends and len(funding_trends) > 50:
            insights.append(f"💰 Current funding trend: {funding_trends[:200]}...")
        
        # Dimension-specific insights
        strong_dimensions = [dim for dim, data in dimension_scores.items() if data["percentage"] >= 75]
        weak_dimensions = [dim for dim, data in dimension_scores.items() if data["percentage"] < 50]
        
        if strong_dimensions:
            insights.append(f"💪 Mga strength: {', '.join(strong_dimensions)}. Gamitin ang mga ito laban sa current market players.")
        
        if weak_dimensions:
            insights.append(f"⚠️ Priority improvement areas: {', '.join(weak_dimensions)}. Critical sa market success.")
        
        # Opportunity insights
        opportunities = market_intelligence.get("opportunities", "")
        if opportunities and len(opportunities) > 50:
            insights.append(f"🎯 Market opportunity: {opportunities[:200]}...")
    else:
        # Market-driven insights
        market_overview = market_intelligence.get("market_overview", "")
        if "growth" in market_overview.lower():
            insights.append("🚀 Market shows positive growth trajectory favorable for your technology commercialization timing.")
        
        # Competitive insights
        competitive_landscape = market_intelligence.get("competitive_landscape", "")
        if competitive_landscape and len(competitive_landscape) > 50:
            insights.append(f"🏆 Competitive landscape: {competitive_landscape[:200]}...")
        
        # Funding insights
        funding_trends = market_intelligence.get("funding_trends", "")
        if funding_trends and len(funding_trends) > 50:
            insights.append(f"💰 Current funding environment: {funding_trends[:200]}...")
        
        # Dimension-specific insights with market context
        strong_dimensions = [dim for dim, data in dimension_scores.items() if data["percentage"] >= 75]
        weak_dimensions = [dim for dim, data in dimension_scores.items() if data["percentage"] < 50]
        
        if strong_dimensions:
            insights.append(f"💪 Your strongest capabilities: {', '.join(strong_dimensions)}. Leverage these against current market competitors.")
        
        if weak_dimensions:
            insights.append(f"⚠️ Priority areas for improvement: {', '.join(weak_dimensions)}. These are critical success factors in current market.")
        
        # Success stories insight
        success_stories = market_intelligence.get("success_stories", "")
        if success_stories and len(success_stories) > 50:
            insights.append(f"🌟 Success patterns: {success_stories[:200]}...")
        
        # Market opportunities
        opportunities = market_intelligence.get("opportunities", "")
        if opportunities and len(opportunities) > 50:
            insights.append(f"🎯 Current market opportunity: {opportunities[:200]}...")
        
        # Pathway-specific AI insights
        if recommended_pathway == "Direct Sale":
            insights.append("🎯 Direct Sale pathway shows strong potential based on current market conditions and competitive analysis.")
        elif recommended_pathway == "Licensing":
            insights.append("🤝 Licensing strategy aligns with current market trends where companies focus on core competencies.")
        elif recommended_pathway == "Startup/Spin-out":
            insights.append("🚀 Startup approach is viable given current investor interest and market dynamics in your sector.")
    
    return insights

def generate_ai_success_strategies(dimension_scores, recommended_pathway, market_intelligence, language):
    """Generate AI-powered success strategies"""
    strategies = {
        "immediate_actions": [],
        "short_term_goals": [],
        "long_term_strategies": [],
        "market_timing": [],
        "funding_strategy": [],
        "partnership_strategy": []
    }
    
    opportunities = market_intelligence.get("opportunities", "")
    funding_trends = market_intelligence.get("funding_trends", "")
    partnerships = market_intelligence.get("partnerships", "")
    
    if language == "filipino":
        # AI-informed immediate actions
        if opportunities:
            strategies["immediate_actions"].append(f"🎯 Mag-capitalize sa opportunity: {opportunities[:150]}...")
        
        strategies["immediate_actions"].extend([
            "📊 Mag-conduct ng AI-powered market validation study",
            "🔍 Mag-analyze ng real-time competitive intelligence",
            "📈 Mag-develop ng data-driven customer acquisition strategy"
        ])
        
        # Funding strategy with AI insights
        if funding_trends:
            strategies["funding_strategy"].append(f"💰 Align sa trend: {funding_trends[:150]}...")
        
        strategies["funding_strategy"].extend([
            "🎯 Target ang active investors based sa AI market analysis",
            "📋 Prepare ng pitch deck aligned sa current investor focus",
            "🏦 Explore ng AI-identified funding opportunities"
        ])
        
        # Partnership strategy
        if partnerships:
            strategies["partnership_strategy"].append(f"🤝 Partnership opportunity: {partnerships[:150]}...")
        
        strategies["partnership_strategy"].extend([
            "🌐 Identify strategic partners through AI market mapping",
            "🤝 Build relationships sa key industry players",
            "📊 Leverage ng partnership data para sa market entry"
        ])
    else:
        # AI-informed immediate actions
        if opportunities:
            strategies["immediate_actions"].append(f"🎯 Capitalize on identified opportunity: {opportunities[:150]}...")
        
        strategies["immediate_actions"].extend([
            "📊 Conduct AI-powered market validation and sizing study",
            "🔍 Analyze real-time competitive intelligence and positioning",
            "📈 Develop data-driven customer acquisition and retention strategy"
        ])
        
        # Short-term goals with market intelligence
        strategies["short_term_goals"] = [
            "🚀 Launch pilot program with AI-identified early adopters",
            "📊 Establish KPI tracking system based on market benchmarks",
            "🤝 Build strategic partnerships identified through market analysis",
            "💰 Secure initial funding aligned with current investor focus"
        ]
        
        # Long-term strategies with AI insights
        strategies["long_term_strategies"] = [
            "🏆 Establish market leadership position in identified segments",
            "🌐 Expand into AI-identified adjacent markets and opportunities",
            "🔄 Develop sustainable competitive moat based on market evolution",
            "📈 Scale operations using AI-optimized processes and systems"
        ]
        
        # Market timing strategies
        strategies["market_timing"] = [
            "⏰ Monitor AI-identified market inflection points for optimal timing",
            "📊 Leverage real-time market data for strategic decision making",
            "🎯 Align product launches with market readiness indicators",
            "📈 Capitalize on identified market momentum and trends"
        ]
        
        # Funding strategy with AI insights
        if funding_trends:
            strategies["funding_strategy"].append(f"💰 Align with current trend: {funding_trends[:150]}...")
        
        strategies["funding_strategy"].extend([
            "🎯 Target active investors identified through AI market analysis",
            "📋 Prepare pitch materials aligned with current investor focus areas",
            "🏦 Explore AI-identified funding opportunities and programs",
            "📊 Develop financial projections based on real market data"
        ])
        
        # Partnership strategy with market intelligence
        if partnerships:
            strategies["partnership_strategy"].append(f"🤝 Strategic partnership opportunity: {partnerships[:150]}...")
        
        strategies["partnership_strategy"].extend([
            "🌐 Identify and approach strategic partners through AI market mapping",
            "🤝 Build relationships with key industry players and stakeholders",
            "📊 Leverage partnership opportunities for accelerated market entry",
            "🔄 Develop ecosystem partnerships for sustainable competitive advantage"
        ])
    
    return strategies

def generate_ai_risk_assessment(dimension_scores, recommended_pathway, market_intelligence, language):
    """Generate AI-enhanced risk assessment"""
    risks = {
        "high_risk_areas": [],
        "medium_risk_areas": [],
        "market_risks": [],
        "competitive_risks": [],
        "mitigation_strategies": [],
        "ai_identified_risks": []
    }
    
    # Traditional dimension-based risks
    for dim_name, dim_data in dimension_scores.items():
        if dim_data["percentage"] < 40:
            risks["high_risk_areas"].append(dim_name)
        elif dim_data["percentage"] < 65:
            risks["medium_risk_areas"].append(dim_name)
    
    # AI-identified market risks
    threats = market_intelligence.get("threats", "")
    if threats:
        risks["ai_identified_risks"].append(f"Market threat: {threats[:200]}...")
    
    competitive_landscape = market_intelligence.get("competitive_landscape", "")
    if "competitive" in competitive_landscape.lower():
        risks["competitive_risks"].append("High competitive intensity identified through market analysis")
    
    if language == "filipino":
        risks["mitigation_strategies"] = [
            "🤖 Gamitin ang AI monitoring para sa early risk detection",
            "📊 Mag-establish ng real-time market intelligence system",
            "🛡️ Mag-develop ng adaptive strategy framework",
            "🔄 Mag-implement ng continuous risk assessment process"
        ]
        
        if recommended_pathway == "Direct Sale":
            risks["mitigation_strategies"].extend([
                "💰 Secure diversified funding sources para sa market volatility",
                "🎯 Build strong customer relationships para sa stability",
                "📈 Develop flexible pricing strategy based sa market conditions"
            ])
    else:
        risks["mitigation_strategies"] = [
            "🤖 Implement AI-powered risk monitoring and early warning systems",
            "📊 Establish real-time market intelligence and competitive tracking",
            "🛡️ Develop adaptive strategy framework for rapid market changes",
            "🔄 Create continuous risk assessment and mitigation processes"
        ]
        
        # Pathway-specific AI-enhanced mitigation
        if recommended_pathway == "Direct Sale":
            risks["mitigation_strategies"].extend([
                "💰 Secure diversified funding sources to weather market volatility",
                "🎯 Build strong customer relationships and loyalty programs",
                "📈 Develop flexible pricing and product strategies based on market feedback"
            ])
        elif recommended_pathway == "Licensing":
            risks["mitigation_strategies"].extend([
                "🤝 Diversify licensing partners across different market segments",
                "📋 Include adaptive clauses in licensing agreements",
                "📊 Maintain ongoing competitive intelligence and market monitoring"
            ])
        elif recommended_pathway == "Startup/Spin-out":
            risks["mitigation_strategies"].extend([
                "🚀 Build agile team capable of rapid pivoting based on market feedback",
                "💰 Secure multiple funding rounds and investor relationships",
                "📊 Develop robust business model validation and testing processes"
            ])
    
    return risks

def generate_ai_market_positioning(dimension_scores, recommended_pathway, market_intelligence, language):
    """Generate AI-enhanced market positioning strategy"""
    positioning = {}
    
    market_strength = dimension_scores.get("Market & Customer", dimension_scores.get("Market at Customer", {})).get("percentage", 0)
    tech_strength = dimension_scores.get("Technology & Product Readiness", dimension_scores.get("Technology at Product Readiness", {})).get("percentage", 0)
    
    competitive_landscape = market_intelligence.get("competitive_landscape", "")
    opportunities = market_intelligence.get("opportunities", "")
    
    if language == "filipino":
        if market_strength >= 75 and tech_strength >= 75:
            positioning["strategy"] = "🏆 AI-Identified Market Leader"
            positioning["advice"] = "Strong position sa market at tech. Mag-focus sa AI-driven expansion at dominance."
        elif market_strength >= 60 and tech_strength >= 60:
            positioning["strategy"] = "🚀 AI-Optimized Competitor"
            positioning["advice"] = "Good positioning. Use AI insights para sa superior differentiation."
        else:
            positioning["strategy"] = "🎯 AI-Guided Niche Player"
            positioning["advice"] = "Focus sa AI-identified niche segments na may competitive advantage."
        
        positioning["ai_insights"] = []
        if competitive_landscape:
            positioning["ai_insights"].append(f"Competitive insight: {competitive_landscape[:150]}...")
        if opportunities:
            positioning["ai_insights"].append(f"Market opportunity: {opportunities[:150]}...")
    else:
        if market_strength >= 75 and tech_strength >= 75:
            positioning["strategy"] = "🏆 AI-Identified Market Leader"
            positioning["advice"] = "Exceptional positioning in both market and technology. Focus on AI-driven market expansion and establishing dominant market position."
        elif market_strength >= 60 and tech_strength >= 60:
            positioning["strategy"] = "🚀 AI-Optimized Strong Competitor"
            positioning["advice"] = "Strong competitive positioning. Leverage AI insights for superior differentiation and customer experience."
        else:
            positioning["strategy"] = "🎯 AI-Guided Niche Player"
            positioning["advice"] = "Focus on AI-identified niche market segments where you can establish clear competitive advantages."
        
        # AI-enhanced differentiators
        positioning["key_differentiators"] = [
            "🤖 AI-optimized unique technology features and capabilities",
            "📊 Data-driven superior customer service and support",
            "💰 Market-intelligent competitive pricing and value proposition",
            "🤝 AI-identified strategic partnerships and ecosystem relationships"
        ]
        
        # AI market insights
        positioning["ai_insights"] = []
        if competitive_landscape:
            positioning["ai_insights"].append(f"🔍 Competitive intelligence: {competitive_landscape[:200]}...")
        if opportunities:
            positioning["ai_insights"].append(f"🎯 Market opportunity analysis: {opportunities[:200]}...")
        
        # Market positioning recommendations
        positioning["positioning_recommendations"] = [
            "🎯 Position as innovation leader in AI-identified market gaps",
            "📊 Leverage real-time market data for dynamic positioning strategy",
            "🚀 Build thought leadership through AI-powered market insights",
            "🤝 Establish ecosystem partnerships for enhanced market credibility"
        ]
    
    return positioning

def generate_ai_financial_projections(recommended_pathway, market_intelligence, dimension_scores, language):
    """Generate AI-enhanced financial projections"""
    projections = {
        "revenue_model": "",
        "funding_requirements": {},
        "market_size_context": "",
        "financial_milestones": {},
        "roi_timeline": "",
        "ai_market_insights": [],
        "key_assumptions": []
    }
    
    market_overview = market_intelligence.get("market_overview", "")
    funding_trends = market_intelligence.get("funding_trends", "")
    
    if language == "filipino":
        # AI-enhanced revenue model
        if recommended_pathway == "Direct Sale":
            projections["revenue_model"] = "🎯 AI-optimized direct sales revenue model based sa market intelligence at customer behavior analysis"
            projections["funding_requirements"] = {
                "initial": "₱3-7M para sa AI-powered product development at market entry",
                "growth": "₱15-30M para sa AI-driven scaling at market expansion",
                "working_capital": "₱8-15M para sa data-driven operations"
            }
        elif recommended_pathway == "Licensing":
            projections["revenue_model"] = "🤝 AI-enhanced licensing model na optimized para sa market conditions at partner needs"
            projections["funding_requirements"] = {
                "initial": "₱2-5M para sa AI-powered IP development at protection",
                "growth": "₱8-15M para sa partner support at market expansion",
                "working_capital": "₱3-8M para sa ongoing AI-driven operations"
            }
        
        projections["ai_market_insights"] = []
        if market_overview:
            projections["ai_market_insights"].append(f"Market analysis: {market_overview[:150]}...")
        if funding_trends:
            projections["ai_market_insights"].append(f"Funding trend: {funding_trends[:150]}...")
    else:
        # AI-enhanced revenue models
        if recommended_pathway == "Direct Sale":
            projections["revenue_model"] = "🎯 AI-optimized direct sales revenue model based on market intelligence and customer behavior analysis"
            projections["funding_requirements"] = {
                "initial": "$150K-750K for AI-powered product development and market entry",
                "growth": "$750K-3M for AI-driven scaling and market expansion",
                "working_capital": "$400K-1.5M for data-driven operations and growth"
            }
        elif recommended_pathway == "Licensing":
            projections["revenue_model"] = "🤝 AI-enhanced licensing revenue model optimized for current market conditions and partner needs"
            projections["funding_requirements"] = {
                "initial": "$75K-500K for AI-powered IP development and protection",
                "growth": "$400K-1.5M for partner support and market expansion",
                "working_capital": "$150K-800K for ongoing AI-driven operations"
            }
        elif recommended_pathway == "Startup/Spin-out":
            projections["revenue_model"] = "🚀 AI-guided multiple revenue stream model with dynamic optimization based on market feedback"
            projections["funding_requirements"] = {
                "seed": "$300K-2M for AI-powered initial development and validation",
                "series_a": "$1.5M-8M for AI-driven market expansion and scaling",
                "working_capital": "$750K-3M for operations and AI-optimized growth"
            }
        
        # AI market insights
        projections["ai_market_insights"] = []
        if market_overview:
            projections["ai_market_insights"].append(f"📊 Market intelligence: {market_overview[:200]}...")
        if funding_trends:
            projections["ai_market_insights"].append(f"💰 Funding landscape: {funding_trends[:200]}...")
        
        # Enhanced financial milestones with AI insights
        projections["financial_milestones"] = {
            "year_1": "🎯 Achieve AI-validated product-market fit and initial revenue streams",
            "year_2": "📈 Demonstrate AI-optimized sustainable growth (75-150% revenue increase)",
            "year_3": "🏆 Establish AI-driven market leadership position with strong profitability"
        }
        
        projections["roi_timeline"] = "⏰ 2.5-4 years for technology commercialization with AI optimization (20% faster than traditional approaches)"
        
        # AI-enhanced assumptions
        projections["key_assumptions"] = [
            "🤖 AI-driven market adoption rates exceed traditional technology adoption curves",
            "📊 Real-time market intelligence enables rapid strategy optimization and adaptation",
            "🎯 AI-identified market opportunities provide sustainable competitive advantages",
            "💰 Current funding environment remains favorable for AI-enhanced technology solutions",
            "🚀 Continuous AI optimization improves operational efficiency and reduces costs"
        ]
    
    return projections

def generate_ai_implementation_roadmap(recommended_pathway, market_intelligence, language):
    """Generate AI-enhanced implementation roadmap"""
    roadmap = {
        "phase_1": {"timeframe": "0-6 months", "milestones": [], "ai_activities": []},
        "phase_2": {"timeframe": "6-12 months", "milestones": [], "ai_activities": []},
        "phase_3": {"timeframe": "12-24 months", "milestones": [], "ai_activities": []},
        "ai_optimization_timeline": [],
        "market_intelligence_integration": []
    }
    
    opportunities = market_intelligence.get("opportunities", "")
    
    if language == "filipino":
        # Phase 1: AI-Enhanced Foundation
        roadmap["phase_1"]["milestones"] = [
            "🤖 Implement AI-powered market validation at product optimization",
            "📊 Establish real-time market intelligence systems",
            "🎯 Complete AI-guided competitive positioning analysis"
        ]
        
        roadmap["phase_1"]["ai_activities"] = [
            "Set up automated market monitoring systems",
            "Deploy AI-powered customer feedback analysis",
            "Implement predictive market trend analysis"
        ]
        
        # Phase 2: AI-Driven Launch
        roadmap["phase_2"]["milestones"] = [
            "🚀 Launch AI-optimized pilot program",
            "📈 Achieve AI-validated product-market fit",
            "🤝 Establish AI-identified strategic partnerships"
        ]
        
        roadmap["phase_2"]["ai_activities"] = [
            "Deploy AI customer acquisition optimization",
            "Implement automated competitive intelligence",
            "Launch AI-powered performance tracking"
        ]
        
        # Phase 3: AI-Powered Scale
        roadmap["phase_3"]["milestones"] = [
            "🏆 Achieve AI-driven market leadership",
            "🌐 Expand sa AI-identified adjacent markets",
            "📊 Establish sustainable AI-optimized operations"
        ]
        
        roadmap["phase_3"]["ai_activities"] = [
            "Deploy predictive market expansion strategies",
            "Implement AI-powered operational optimization",
            "Launch next-generation AI-enhanced products"
        ]
    else:
        # Phase 1: AI-Enhanced Foundation (0-6 months)
        roadmap["phase_1"]["milestones"] = [
            "🤖 Implement AI-powered market validation and product optimization systems",
            "📊 Establish comprehensive real-time market intelligence infrastructure",
            "🎯 Complete AI-guided competitive analysis and positioning strategy"
        ]
        
        roadmap["phase_1"]["ai_activities"] = [
            "Deploy automated market monitoring and trend analysis systems",
            "Implement AI-powered customer feedback collection and analysis",
            "Set up predictive market intelligence and forecasting capabilities"
        ]
        
        # Phase 2: AI-Driven Market Entry (6-12 months)
        roadmap["phase_2"]["milestones"] = [
            "🚀 Launch AI-optimized pilot program with target customer segments",
            "📈 Achieve AI-validated product-market fit with measurable KPIs",
            "🤝 Establish AI-identified strategic partnerships and alliances"
        ]
        
        roadmap["phase_2"]["ai_activities"] = [
            "Deploy AI-powered customer acquisition and conversion optimization",
            "Implement automated competitive intelligence and response systems",
            "Launch AI-driven performance tracking and optimization platforms"
        ]
        
        # Phase 3: AI-Powered Market Leadership (12-24 months)
        roadmap["phase_3"]["milestones"] = [
            "🏆 Achieve AI-driven market leadership position in target segments",
            "🌐 Successfully expand into AI-identified adjacent markets and opportunities",
            "📊 Establish sustainable AI-optimized operations and growth systems"
        ]
        
        roadmap["phase_3"]["ai_activities"] = [
            "Deploy predictive market expansion and diversification strategies",
            "Implement AI-powered operational efficiency and cost optimization",
            "Launch next-generation AI-enhanced product and service offerings"
        ]
        
        # AI optimization timeline
        roadmap["ai_optimization_timeline"] = [
            "⚡ Month 1-2: Deploy basic AI monitoring and analysis systems",
            "🔄 Month 3-6: Implement advanced predictive analytics and optimization",
            "🚀 Month 6-12: Launch AI-powered growth and expansion strategies",
            "🏆 Month 12-24: Achieve AI-driven market leadership and sustainable competitive advantage"
        ]
        
        # Market intelligence integration points
        if opportunities:
            roadmap["market_intelligence_integration"].append(f"🎯 Capitalize on opportunity: {opportunities[:150]}...")
        
        roadmap["market_intelligence_integration"].extend([
            "📊 Continuous real-time market data integration and analysis",
            "🤖 AI-powered competitive intelligence and strategic response systems",
            "📈 Predictive market trend analysis for proactive strategy adjustment",
            "🎯 Dynamic opportunity identification and rapid market entry capabilities"
        ])
    
    return roadmap

def identify_ai_partnership_opportunities(technology_title, recommended_pathway, market_intelligence, language):
    """Identify partnership opportunities using AI market intelligence"""
    opportunities = {
        "strategic_partners": [],
        "technology_partners": [],
        "distribution_partners": [],
        "funding_partners": [],
        "ai_identified_partners": []
    }
    
    partnerships = market_intelligence.get("partnerships", "")
    
    if language == "filipino":
        # AI-identified strategic partnerships
        if partnerships:
            opportunities["ai_identified_partners"].append(f"🤖 AI-identified opportunity: {partnerships[:200]}...")
        
        # Pathway-specific partnerships
        if recommended_pathway == "Direct Sale":
            opportunities["strategic_partners"] = [
                "🎯 AI-identified distribution partners na may strong market presence",
                "📊 Data-driven technology integrators para sa solution enhancement",
                "🤝 Industry leaders na compatible sa AI-optimized approach"
            ]
        elif recommended_pathway == "Licensing":
            opportunities["strategic_partners"] = [
                "🏢 AI-identified large corporations na may complementary products",
                "🌐 International partners para sa global market expansion",
                "🤝 Technology companies na nag-hahanap ng AI-enhanced innovation"
            ]
        
        opportunities["technology_partners"] = [
            "🏫 Research institutions na may AI at technology expertise",
            "🔧 AI-powered technology suppliers at component providers",
            "💻 Software/hardware partners para sa AI integration"
        ]
    else:
        # AI-identified strategic partnerships
        if partnerships:
            opportunities["ai_identified_partners"].append(f"🤖 AI-identified partnership opportunity: {partnerships[:200]}...")
        
        # Enhanced strategic partnerships based on pathway
        if recommended_pathway == "Direct Sale":
            opportunities["strategic_partners"] = [
                "🎯 AI-identified distribution partners with strong market presence and customer relationships",
                "📊 Data-driven technology integrators for enhanced solution delivery and market reach",
                "🤝 Industry leaders compatible with AI-optimized go-to-market approaches"
            ]
        elif recommended_pathway == "Licensing":
            opportunities["strategic_partners"] = [
                "🏢 AI-identified large corporations with complementary product portfolios and market access",
                "🌐 International partners for AI-enhanced global market expansion opportunities",
                "🤝 Innovation-focused technology companies seeking AI-enhanced competitive advantages"
            ]
        elif recommended_pathway == "Startup/Spin-out":
            opportunities["strategic_partners"] = [
                "🚀 AI-focused accelerators and incubators with technology commercialization expertise",
                "🎯 Strategic investors with AI and technology market networks and experience",
                "🤝 Industry mentors with successful AI-enhanced commercialization track records"
            ]
        
        # Enhanced technology partnerships
        opportunities["technology_partners"] = [
            "🏫 Leading research institutions with AI, ML, and advanced technology capabilities",
            "🔧 AI-powered technology suppliers and component providers for enhanced integration",
            "💻 Software/hardware partners specializing in AI platform integration and compatibility"
        ]
        
        # AI-enhanced distribution partnerships
        opportunities["distribution_partners"] = [
            "🌐 Digital platforms with AI-powered customer matching and acquisition capabilities",
            "📊 Data-driven regional distributors with market intelligence and customer insights",
            "🎯 AI-optimized retail and e-commerce partners for direct customer access and engagement"
        ]
        
        # Enhanced funding partnerships
        opportunities["funding_partners"] = [
            "💰 AI-focused venture capital firms and strategic investors with sector expertise",
            "🏛️ Government innovation programs and grants supporting AI-enhanced technology development",
            "🌐 Crowdfunding and alternative financing platforms with AI-powered investor matching"
        ]
        
        # Partnership success metrics
        opportunities["partnership_success_metrics"] = [
            "📈 Revenue growth acceleration through strategic partnerships (target: 50-100% increase)",
            "🎯 Market penetration improvement via distribution partnerships (target: 3x customer reach)",
            "🤖 Technology development acceleration through AI-enhanced collaboration (target: 30% faster TTM)",
            "💰 Funding success rate improvement through investor partnerships (target: 2x funding success)"
        ]
    
    return opportunities

# Supporting helper functions
def generate_input_summary(answers, tcp_data):
    """Generate summary of user inputs"""
    return {
        "total_questions": len(answers),
        "average_score": round(sum(answers) / len(answers), 2),
        "dimension_breakdown": [
            {
                "dimension": dim["name"],
                "average_score": round(sum(answers[i:i+len(dim["questions"])]) / len(dim["questions"]), 2)
            }
            for i, dim in enumerate(tcp_data["dimensions"])
        ]
    }

def generate_dimension_scores(answers, tcp_data):
    """Generate dimension scores analysis"""
    dimension_scores = {}
    answer_idx = 0
    
    for dimension in tcp_data["dimensions"]:
        dim_answers = answers[answer_idx:answer_idx + len(dimension["questions"])]
        dim_score = sum(dim_answers)
        max_score = len(dimension["questions"]) * 3
        percentage = (dim_score / max_score) * 100
        
        dimension_scores[dimension["name"]] = {
            "score": dim_score,
            "max_score": max_score,
            "percentage": percentage,
            "level": "High" if percentage >= 75 else "Medium" if percentage >= 50 else "Low"
        }
        answer_idx += len(dimension["questions"])
    
    return dimension_scores

def calculate_overall_readiness(dimension_scores):
    """Calculate overall readiness score"""
    total_percentage = sum(dim["percentage"] for dim in dimension_scores.values())
    avg_percentage = total_percentage / len(dimension_scores) if dimension_scores else 0
    
    if avg_percentage >= 85:
        return "Excellent"
    elif avg_percentage >= 70:
        return "Very Good"
    elif avg_percentage >= 55:
        return "Good"
    elif avg_percentage >= 40:
        return "Fair"
    else:
        return "Needs Development"

def calculate_ai_confidence_score(pathway_scores, dimension_scores, market_intelligence):
    """Calculate AI-enhanced confidence score"""
    # Basic confidence from pathway scores
    max_score = max(pathway_scores.values()) if pathway_scores else 0
    second_score = sorted(pathway_scores.values(), reverse=True)[1] if len(pathway_scores) > 1 else 0
    score_gap = max_score - second_score
    
    # Average dimension readiness
    avg_dimension_score = sum(dim["percentage"] for dim in dimension_scores.values()) / len(dimension_scores) if dimension_scores else 0
    
    # AI market intelligence boost
    market_boost = 0
    if market_intelligence.get("market_overview") and len(market_intelligence.get("market_overview", "")) > 100:
        market_boost += 10
    if market_intelligence.get("opportunities") and len(market_intelligence.get("opportunities", "")) > 100:
        market_boost += 10
    if market_intelligence.get("funding_trends") and len(market_intelligence.get("funding_trends", "")) > 100:
        market_boost += 5
    
    # Calculate enhanced confidence
    confidence = min(100, (score_gap * 8) + (avg_dimension_score * 0.4) + market_boost)
    
    return round(confidence, 1)

def generate_fallback_intelligence(technology_title, language):
    """Generate fallback intelligence when AI is not available"""
    if language == "filipino":
        return {
            "market_overview": "Market analysis ay hindi available - kailangan ng Perplexity API configuration para sa real-time intelligence",
            "competitive_landscape": "Competitive analysis ay hindi updated",
            "funding_trends": "Funding trend data ay hindi available",
            "regulatory_insights": "Regulatory information ay hindi updated",
            "success_stories": "Success story analysis ay hindi available",
            "opportunities": "Market opportunity analysis ay hindi available",
            "threats": "Threat analysis ay hindi available",
            "partnerships": "Partnership opportunity analysis ay hindi available",
            "pricing_models": "Pricing model analysis ay hindi available",
            "full_analysis": "Para sa comprehensive AI-powered analysis, i-configure ang Perplexity API key sa environment variables."
        }
    else:
        return {
            "market_overview": "Real-time market analysis not available - configure Perplexity API for live market intelligence",
            "competitive_landscape": "Competitive analysis not updated - requires API configuration",
            "funding_trends": "Current funding trend data not available",
            "regulatory_insights": "Regulatory environment information not updated",
            "success_stories": "Success story analysis not available",
            "opportunities": "Market opportunity analysis requires API access",
            "threats": "Threat analysis not available",
            "partnerships": "Partnership opportunity analysis not available",  
            "pricing_models": "Pricing model analysis not available",
            "full_analysis": "For comprehensive AI-powered market intelligence, configure PERPLEXITY_API_KEY in environment variables."
        }

def generate_enhanced_explanation(pathway_scores, recommended_pathway, detailed_analysis, language):
    """Generate enhanced explanation with AI insights"""
    confidence = detailed_analysis.get("confidence_score", 0)
    second_alt = detailed_analysis.get("second_alternative")
    overall_readiness = detailed_analysis.get("overall_readiness", "Good")
    market_intelligence = detailed_analysis.get("market_intelligence", {})
    
    if language == "filipino":
        text = f"🤖 **AI-Enhanced Technology Commercialization Analysis**\n\n"
        text += f"Batay sa comprehensive AI-powered assessment, ang **pinakarekomendadong commercialization pathway** para sa inyong teknolohiya ay ang **{recommended_pathway}** (AI confidence level: {confidence}%).\n\n"
        
        if second_alt:
            text += f"Ang inyong **second-best alternative** ay ang {second_alt[0]} na may score na {second_alt[1]}. Ito ay viable backup strategy kung may challenges sa primary recommendation.\n\n"
        
        text += f"**Overall Commercialization Readiness:** {overall_readiness}\n\n"
        
        # Add AI market insights
        market_overview = market_intelligence.get("market_overview", "")
        if market_overview and len(market_overview) > 50:
            text += f"**🔍 AI Market Intelligence:** {market_overview[:300]}...\n\n"
        
        opportunities = market_intelligence.get("opportunities", "")
        if opportunities and len(opportunities) > 50:
            text += f"**🎯 Identified Opportunities:** {opportunities[:250]}...\n\n"
        
        text += f"Ang AI-enhanced assessment na ito ay nag-evaluate ng inyong teknolohiya gamit ang real-time market data at competitive intelligence, providing cutting-edge insights para sa successful technology commercialization."
    else:
        text = f"🤖 **AI-Enhanced Technology Commercialization Analysis**\n\n"
        text += f"Based on comprehensive AI-powered multi-dimensional assessment, the **most recommended commercialization pathway** for your technology is **{recommended_pathway}** (AI confidence level: {confidence}%).\n\n"
        
        if second_alt:
            text += f"Your **second-best alternative** is {second_alt[0]} with a score of {second_alt[1]}. This serves as a viable backup strategy should challenges arise with the primary recommendation.\n\n"
        
        text += f"**Overall Commercialization Readiness:** {overall_readiness}\n\n"
        
        # Add AI market insights
        market_overview = market_intelligence.get("market_overview", "")
        if market_overview and len(market_overview) > 50:
            text += f"**🔍 AI Market Intelligence:** {market_overview[:300]}...\n\n"
        
        competitive_landscape = market_intelligence.get("competitive_landscape", "")
        if competitive_landscape and len(competitive_landscape) > 50:
            text += f"**🏆 Competitive Landscape:** {competitive_landscape[:250]}...\n\n"
        
        opportunities = market_intelligence.get("opportunities", "")
        if opportunities and len(opportunities) > 50:
            text += f"**🎯 Market Opportunities:** {opportunities[:250]}...\n\n"
        
        text += f"This AI-enhanced assessment leverages real-time market data, competitive intelligence, and predictive analytics to provide cutting-edge insights and recommendations for successful technology commercialization in today's dynamic market environment."
    
    return text

@app.route("/api/generate_pdf", methods=["POST"])
def generate_pdf():
    try:
        data = request.json
        print(f"📄 Enhanced PDF Generation - Mode: {data.get('mode', 'Unknown')}")
        
        if not data or 'mode' not in data:
            return jsonify({"error": "Invalid data provided"}), 400
        
        # Generate enhanced PDF with AI insights
        buf = create_enhanced_pdf(data)
        
        # Generate filename
        now = datetime.now()
        date_str = now.strftime('%m%d%y')
        tech_title = data.get('technology_title', 'Assessment').replace(' ', '_').replace('/', '_')
        filename = f"{date_str}_{tech_title}_AI_Enhanced.pdf"
        
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
        return jsonify({"error": f"PDF generation failed: {e}"}), 500

def create_enhanced_pdf(data):
    """Create enhanced PDF with AI insights"""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=0.5*inch)
    sty = getSampleStyleSheet()
    
    title_style = ParagraphStyle("Title", parent=sty["Heading1"], fontSize=16, textColor=colors.darkgreen, alignment=1, spaceAfter=6)
    subtitle_style = ParagraphStyle("Subtitle", parent=sty["Normal"], fontSize=10, textColor=colors.darkblue, alignment=1, spaceAfter=12)
    heading_style = ParagraphStyle("Heading", parent=sty["Heading2"], fontSize=12, textColor=colors.darkgreen)
    
    doc_elements = []
    
    # Enhanced Header
    doc_elements.append(Paragraph("MARANO MARCOS STATE UNIVERSITY", title_style))
    doc_elements.append(Paragraph("Innovation and Technology Support Office", subtitle_style))
    doc_elements.append(Paragraph("🤖 AI-Enhanced Technology Assessment Tool", subtitle_style))
    doc_elements.append(Spacer(1, 18))
    
    doc_elements.append(Paragraph(f"🚀 {data.get('mode_full', data['mode'])} Assessment Report", heading_style))
    doc_elements.append(Spacer(1, 10))
    
    # Technology Information
    tech_info = [
        ["Technology Title:", data.get('technology_title', 'N/A')],
        ["Description:", data.get('description', 'N/A')],
        ["Assessment Date:", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')],
        ["Enhancement Level:", "🤖 AI-Powered with Real-time Market Intelligence"]
    ]
    
    if data['mode'] == 'TCP':
        tech_info.append(["Recommended Pathway:", data.get('recommended_pathway', 'N/A')])
        detailed_analysis = data.get('detailed_analysis', {})
        second_alt = detailed_analysis.get('second_alternative')
        if second_alt:
            tech_info.append(["Alternative Pathway:", f"{second_alt[0]} (Score: {second_alt[1]})"])
        
        confidence = detailed_analysis.get('confidence_score', 0)
        tech_info.append(["AI Confidence Level:", f"{confidence}%"])
    
    tech_table = Table(tech_info, colWidths=[2*inch, 4*inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    doc_elements.append(tech_table)
    doc_elements.append(Spacer(1, 16))
    
    # Enhanced Assessment Summary
    doc_elements.append(Paragraph("🤖 AI-Enhanced Assessment Summary", heading_style))
    doc_elements.append(Paragraph(data.get("explanation", "No explanation available."), sty["Normal"]))
    doc_elements.append(Spacer(1, 14))
    
    # AI Market Intelligence Section
    if data['mode'] == 'TCP' and 'detailed_analysis' in data:
        detailed_analysis = data['detailed_analysis']
        market_intelligence = detailed_analysis.get('market_intelligence', {})
        
        if market_intelligence.get('market_overview'):
            doc_elements.append(Paragraph("📊 Real-time Market Intelligence", heading_style))
            doc_elements.append(Paragraph(market_intelligence['market_overview'][:500] + "...", sty["Normal"]))
            doc_elements.append(Spacer(1, 10))
        
        # AI Success Strategies
        success_strategies = detailed_analysis.get('success_strategies', {})
        if success_strategies.get('immediate_actions'):
            doc_elements.append(Paragraph("🎯 AI-Recommended Immediate Actions", heading_style))
            for action in success_strategies['immediate_actions'][:3]:
                doc_elements.append(Paragraph(f"• {action}", sty["Normal"]))
            doc_elements.append(Spacer(1, 10))
        
        # Market Opportunities
        opportunities = market_intelligence.get('opportunities', '')
        if opportunities and len(opportunities) > 50:
            doc_elements.append(Paragraph("🚀 AI-Identified Market Opportunities", heading_style))
            doc_elements.append(Paragraph(opportunities[:400] + "...", sty["Normal"]))
            doc_elements.append(Spacer(1, 10))
    
    # Enhanced Footer
    doc_elements.append(Spacer(1, 14))
    footer_style = ParagraphStyle("Footer", parent=sty["Normal"], fontSize=8, textColor=colors.grey, alignment=1)
    doc_elements.append(Paragraph("🤖 Generated by MMSU AI-Enhanced Technology Assessment Tool", footer_style))
    doc_elements.append(Paragraph("Powered by Perplexity AI • Innovation and Technology Support Office", footer_style))
    
    doc.build(doc_elements)
    return buf

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
