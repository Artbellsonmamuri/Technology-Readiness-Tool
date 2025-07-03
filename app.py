from flask import Flask, render_template, request, jsonify, send_file
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import json
from datetime import datetime

app = Flask(__name__)

# TRL Questions Database
TRL_QUESTIONS = {
    'english': [
        {
            'level': 1,
            'question': 'Have the basic principles of your technology been observed and reported?',
            'description': 'Basic principles observed - lowest level of technology readiness'
        },
        {
            'level': 2,
            'question': 'Has the technology concept and/or application been formulated?',
            'description': 'Technology concept formulated - invention begins'
        },
        {
            'level': 3,
            'question': 'Has analytical and experimental critical function and/or characteristic proof of concept been achieved?',
            'description': 'Experimental proof of concept - active R&D initiated'
        },
        {
            'level': 4,
            'question': 'Has the technology component and/or breadboard been validated in laboratory environment?',
            'description': 'Technology validated in lab - basic technological components integrated'
        },
        {
            'level': 5,
            'question': 'Has the technology component and/or breadboard been validated in relevant environment?',
            'description': 'Technology validated in relevant environment - large scale components integrated'
        },
        {
            'level': 6,
            'question': 'Has the technology system/subsystem model or prototype been demonstrated in a relevant environment?',
            'description': 'Technology demonstrated in relevant environment - engineering feasibility fully demonstrated'
        },
        {
            'level': 7,
            'question': 'Has the technology system prototype been demonstrated in an operational environment?',
            'description': 'System prototype demonstration in operational environment'
        },
        {
            'level': 8,
            'question': 'Has the technology system been completed and qualified through test and demonstration?',
            'description': 'Technology complete and qualified - actual system completed and qualified'
        },
        {
            'level': 9,
            'question': 'Has the actual technology system been proven through successful mission operations?',
            'description': 'Actual system proven in operational environment - technology in final form'
        }
    ],
    'filipino': [
        {
            'level': 1,
            'question': 'Naobserbahan at naiulat na ba ang mga pangunahing prinsipyo ng inyong teknolohiya?',
            'description': 'Naobserbahan ang mga pangunahing prinsipyo - pinakamababang antas ng technology readiness'
        },
        {
            'level': 2,
            'question': 'Naformulate na ba ang konsepto at/o aplikasyon ng teknolohiya?',
            'description': 'Naformulate ang konsepto ng teknolohiya - nagsisimula ang imbensyon'
        },
        {
            'level': 3,
            'question': 'Nakamit na ba ang analytical at experimental na critical function at/o characteristic proof of concept?',
            'description': 'Experimental proof of concept - nagsimula ang aktibong R&D'
        },
        {
            'level': 4,
            'question': 'Na-validate na ba ang technology component at/o breadboard sa laboratory environment?',
            'description': 'Na-validate ang teknolohiya sa lab - nagsama ang mga basic technological components'
        },
        {
            'level': 5,
            'question': 'Na-validate na ba ang technology component at/o breadboard sa relevant environment?',
            'description': 'Na-validate ang teknolohiya sa relevant environment - nagsama ang malalaking scale components'
        },
        {
            'level': 6,
            'question': 'Na-demonstrate na ba ang technology system/subsystem model o prototype sa relevant environment?',
            'description': 'Na-demonstrate ang teknolohiya sa relevant environment - lubos nang napatunayan ang engineering feasibility'
        },
        {
            'level': 7,
            'question': 'Na-demonstrate na ba ang technology system prototype sa operational environment?',
            'description': 'System prototype demonstration sa operational environment'
        },
        {
            'level': 8,
            'question': 'Nakumpleto at na-qualify na ba ang technology system sa pamamagitan ng test at demonstration?',
            'description': 'Kumpleto at qualified na ang teknolohiya - aktwal na sistema ay kumpleto at qualified na'
        },
        {
            'level': 9,
            'question': 'Napatunayan na ba ang aktwal na technology system sa pamamagitan ng matagumpay na mission operations?',
            'description': 'Aktwal na sistema ay napatunayan sa operational environment - teknolohiya sa final form'
        }
    ]
}

# IRL Questions Database
IRL_QUESTIONS = {
    'english': [
        {
            'level': 1,
            'question': 'Is there a clear market opportunity identified for your technology?',
            'description': 'Market opportunity identification - basic market research completed'
        },
        {
            'level': 2,
            'question': 'Has a preliminary business model been developed?',
            'description': 'Business model formulation - initial business concept developed'
        },
        {
            'level': 3,
            'question': 'Has market validation been conducted with potential customers?',
            'description': 'Market validation - customer feedback and market research conducted'
        },
        {
            'level': 4,
            'question': 'Is there a detailed business plan with financial projections?',
            'description': 'Business plan development - comprehensive business strategy formulated'
        },
        {
            'level': 5,
            'question': 'Has the management team been assembled with relevant expertise?',
            'description': 'Management team formation - key personnel and advisors identified'
        },
        {
            'level': 6,
            'question': 'Are there initial customer commitments or letters of intent?',
            'description': 'Customer commitment - early adopters and strategic partnerships established'
        },
        {
            'level': 7,
            'question': 'Has pilot testing or beta trials been completed successfully?',
            'description': 'Pilot validation - real-world testing with customers completed'
        },
        {
            'level': 8,
            'question': 'Is there proven revenue generation and scalable business operations?',
            'description': 'Revenue generation - sustainable business model demonstrated'
        },
        {
            'level': 9,
            'question': 'Has the venture achieved profitability and market penetration?',
            'description': 'Market success - profitable operations and significant market share achieved'
        }
    ],
    'filipino': [
        {
            'level': 1,
            'question': 'May nakilalang malinaw na market opportunity ba para sa inyong teknolohiya?',
            'description': 'Market opportunity identification - natapos ang basic market research'
        },
        {
            'level': 2,
            'question': 'Nakabuo na ba ng preliminary business model?',
            'description': 'Business model formulation - nabuo ang initial business concept'
        },
        {
            'level': 3,
            'question': 'Naisagawa na ba ang market validation kasama ang mga potensyal na customer?',
            'description': 'Market validation - nakuha ang customer feedback at naisagawa ang market research'
        },
        {
            'level': 4,
            'question': 'May detalyadong business plan ba kasama ang financial projections?',
            'description': 'Business plan development - nabuo ang comprehensive business strategy'
        },
        {
            'level': 5,
            'question': 'Nabuo na ba ang management team na may kaukulang expertise?',
            'description': 'Management team formation - nakilala ang mga key personnel at advisors'
        },
        {
            'level': 6,
            'question': 'May mga initial customer commitments o letters of intent ba?',
            'description': 'Customer commitment - naitatag ang early adopters at strategic partnerships'
        },
        {
            'level': 7,
            'question': 'Natapos na ba nang matagumpay ang pilot testing o beta trials?',
            'description': 'Pilot validation - natapos ang real-world testing kasama ang mga customers'
        },
        {
            'level': 8,
            'question': 'May napatunayang revenue generation at scalable business operations ba?',
            'description': 'Revenue generation - napatunayan ang sustainable business model'
        },
        {
            'level': 9,
            'question': 'Nakamit na ba ng venture ang profitability at market penetration?',
            'description': 'Market success - nakamit ang profitable operations at malaking market share'
        }
    ]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/questions/<mode>/<language>')
def get_questions(mode, language):
    if mode.upper() == 'TRL':
        questions = TRL_QUESTIONS.get(language.lower(), TRL_QUESTIONS['english'])
    else:  # IRL
        questions = IRL_QUESTIONS.get(language.lower(), IRL_QUESTIONS['english'])
    
    return jsonify(questions)

@app.route('/api/assess', methods=['POST'])
def assess_technology():
    data = request.json
    mode = data.get('mode')
    language = data.get('language')
    technology_title = data.get('technology_title')
    description = data.get('description')
    answers = data.get('answers', [])
    
    # Calculate level based on consecutive True answers
    level = 0
    for i, answer in enumerate(answers):
        if answer:
            level = i + 1
        else:
            break
    
    # Generate detailed explanation
    if mode.upper() == 'TRL':
        questions = TRL_QUESTIONS.get(language.lower(), TRL_QUESTIONS['english'])
        mode_full = 'Technology Readiness Level' if language == 'english' else 'Technology Readiness Level'
    else:
        questions = IRL_QUESTIONS.get(language.lower(), IRL_QUESTIONS['english'])
        mode_full = 'Investment Readiness Level' if language == 'english' else 'Investment Readiness Level'
    
    explanation = generate_explanation(level, mode, language, questions)
    
    result = {
        'level': level,
        'mode': mode,
        'mode_full': mode_full,
        'technology_title': technology_title,
        'description': description,
        'explanation': explanation,
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(result)

def generate_explanation(level, mode, language, questions):
    if language == 'filipino':
        if level == 0:
            base_explanation = f"Ang inyong teknolohiya ay hindi pa umabot sa antas 1 ng {mode}. Kailangan pang matugunan ang mga pangunahing requirement."
        else:
            achieved_description = questions[level-1]['description']
            base_explanation = f"Ang inyong teknolohiya ay nakakamit ang antas {level} ng {mode}. {achieved_description}"
        
        if level < 9:
            next_level = level + 1
            if next_level <= len(questions):
                next_description = questions[next_level-1]['description']
                base_explanation += f" Upang makamit ang susunod na antas ({next_level}), kailangan: {next_description}"
    else:
        if level == 0:
            base_explanation = f"Your technology has not yet reached {mode} level 1. Basic requirements need to be addressed."
        else:
            achieved_description = questions[level-1]['description']
            base_explanation = f"Your technology has achieved {mode} level {level}. {achieved_description}"
        
        if level < 9:
            next_level = level + 1
            if next_level <= len(questions):
                next_description = questions[next_level-1]['description']
                base_explanation += f" To achieve the next level ({next_level}), you need: {next_description}"
    
    return base_explanation

@app.route('/api/generate_pdf', methods=['POST'])
def generate_pdf():
    data = request.json
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.darkblue)
    story.append(Paragraph(f"{data['mode_full']} Assessment Report", title_style))
    story.append(Spacer(1, 12))
    
    # Technology Information
    story.append(Paragraph(f"<b>Technology Title:</b> {data['technology_title']}", styles['Normal']))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<b>Description:</b> {data['description']}", styles['Normal']))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<b>Assessment Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Results
    result_style = ParagraphStyle('Result', parent=styles['Heading2'], fontSize=14, textColor=colors.darkgreen)
    story.append(Paragraph(f"Assessment Result: {data['mode']} Level {data['level']}", result_style))
    story.append(Spacer(1, 12))
    
    # Explanation
    story.append(Paragraph("<b>Detailed Explanation:</b>", styles['Heading3']))
    story.append(Paragraph(data['explanation'], styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        io.BytesIO(buffer.read()),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{data['technology_title']}_{data['mode']}_Assessment.pdf"
    )

if __name__ == '__main__':
    app.run(debug=True)
