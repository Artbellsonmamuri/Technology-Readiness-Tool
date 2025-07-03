from flask import Flask, render_template, request, jsonify, send_file
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime
import io

app = Flask(__name__)

# Complete TRL Questions Database (0-9 with multiple checks per level)
TRL_QUESTIONS = {
    "english": [
        {   # TRL-0: Pre-concept
            "level": 0,
            "title": "Pre-Concept / Exploration",
            "checks": [
                "Has the core idea or problem space been clearly articulated?",
                "Have unmet needs or gaps been identified through initial research?",
                "Is background literature or patent prior-art being reviewed?",
                "Are speculative 'what-if' scenarios being recorded for future study?",
                "Is any form of intellectual-property strategy (trade secret or early disclosure) in place?"
            ]
        },
        {   # TRL-1: Basic principles observed
            "level": 1,
            "title": "Basic Principles Observed",
            "checks": [
                "Have the fundamental scientific principles underpinning the technology been identified?",
                "Is at least one peer-reviewed source or equivalent documentation available?",
                "Have theoretical or mathematical models been drafted to explain feasibility?",
                "Is there preliminary evidence or data supporting the stated principles?"
            ]
        },
        {   # TRL-2: Concept formulated
            "level": 2,
            "title": "Technology Concept Formulated",
            "checks": [
                "Is a specific technology concept or application now defined rather than an abstract idea?",
                "Are the advantages and potential use-cases described in technical language?",
                "Have initial feasibility analyses or simulations been completed?",
                "Is the concept documented in a white-paper, preprint or equivalent outlet?"
            ]
        },
        {   # TRL-3: Proof of concept
            "level": 3,
            "title": "Experimental Proof of Concept",
            "checks": [
                "Have critical functions or key performance parameters been identified?",
                "Have laboratory experiments demonstrated proof-of-concept for at least one function?",
                "Are performance metrics recorded and benchmarked against targets?",
                "Have safety, ethical or regulatory constraints been identified at this stage?"
            ]
        },
        {   # TRL-4: Lab validation
            "level": 4,
            "title": "Technology Validated in Laboratory",
            "checks": [
                "Has a breadboard or prototype subsystem been integrated for laboratory testing?",
                "Do measured performances meet or surpass model predictions within tolerances?",
                "Are test procedures documented and peer-reviewed or independently replicated?",
                "Is a preliminary risk register available for the validated subsystem?"
            ]
        },
        {   # TRL-5: Relevant-environment validation
            "level": 5,
            "title": "Technology Validated in Relevant Environment",
            "checks": [
                "Has the breadboard been upgraded for operation in a relevant (not yet operational) environment?",
                "Do environmental tests include temperature, vibration or other domain-specific stresses?",
                "Has compliance with domain standards been assessed by an external body or advisory board?",
                "Is an updated risk mitigation plan in place reflecting test outcomes?"
            ]
        },
        {   # TRL-6: Prototype demonstrated
            "level": 6,
            "title": "Prototype Demonstrated in Relevant Environment",
            "checks": [
                "Is a system/sub-system model or prototype complete enough to deliver baseline functionality?",
                "Has the prototype been demonstrated end-to-end in a relevant environment?",
                "Do data show the prototype meeting critical performance metrics under realistic constraints?",
                "Is a V&V (verification & validation) report available for this prototype?"
            ]
        },
        {   # TRL-7: System prototype in operational environment
            "level": 7,
            "title": "System Prototype Demonstrated in Operational Environment",
            "checks": [
                "Has the prototype been installed or trialed within the intended operational setting?",
                "Do operational data confirm functionality under real-world duty-cycles?",
                "Are failure modes analysed with corrective actions documented?",
                "Is the supply-chain or manufacturing route for key components identified?"
            ]
        },
        {   # TRL-8: Qualified through test & demo
            "level": 8,
            "title": "System Complete and Qualified",
            "checks": [
                "Is the technology an integrated commercial or mission-ready system?",
                "Has the system passed full acceptance tests, certifications, or regulatory approvals?",
                "Are formal user manuals, maintenance plans and training materials available?",
                "Have pilot customers or early adopters signed off on performance KPIs?"
            ]
        },
        {   # TRL-9: Proven in mission operations
            "level": 9,
            "title": "Actual System Proven in Operational Environment",
            "checks": [
                "Has the technology been deployed in its final form during routine mission operations?",
                "Do longitudinal data confirm sustained performance and reliability?",
                "Are service-level agreements and quality-assurance processes fully operational?",
                "Is a continual improvement framework in place for upgrades or derivative products?"
            ]
        }
    ],
    "filipino": [
        {   # TRL-0
            "level": 0,
            "title": "Pre-Konsepto / Eksplorasyon",
            "checks": [
                "Malinaw bang nailahad ang pangunahing ideya o problemang nais solusyonan?",
                "Natukoy na ba ang hindi natutugunang pangangailangan batay sa paunang pananaliksik?",
                "Isinasagawa ba ang pagsusuri ng literatura o patent upang maiwasan ang duplikasyon?",
                "Naitatala ba ang mga spekulatibong 'paano kung' na senaryo para sa susunod na pag-aaral?",
                "May estratehiya na ba ukol sa proteksyon ng intelektuwal na ari-arian (hal. trade secret o maagang paglalathala)?"
            ]
        },
        {   # TRL-1
            "level": 1,
            "title": "Pangunahing Prinsipyo na-obserbahan",
            "checks": [
                "Natukoy na ba ang mga batayang prinsipyong siyentipiko ng teknolohiya?",
                "Mayroon bang kahit isang peer-reviewed na sanggunian o katumbas na dokumentasyon?",
                "Nabuo na ba ang teoretikal o matematikal na modelo upang patunayan ang posibilidad?",
                "May paunang ebidensiya o datos ba na sumusuporta sa mga prinsipyong ito?"
            ]
        },
        {   # TRL-2
            "level": 2,
            "title": "Nabuo ang Konsepto ng Teknolohiya",
            "checks": [
                "May tiyak na konsepto o aplikasyong teknolohikal na ba kaysa sa abstraktong ideya?",
                "Naipaliwanag ba ang mga benepisyo at posibleng gamit sa teknikal na wika?",
                "Nagawa na ba ang paunang feasibility analysis o simulation?",
                "Nakadokumento ba ang konsepto sa white-paper, preprint o katumbas?"
            ]
        },
        {   # TRL-3
            "level": 3,
            "title": "Eksperimental na Patunay ng Konsepto",
            "checks": [
                "Natukoy na ba ang mga kritikal na function o key performance parameters?",
                "May mga eksperimento bang laboratoryo na nagpatunay ng konsepto para kahit isang function?",
                "Naitala at na-benchmark ba ang performance metrics laban sa target?",
                "Natukoy na ba ang mga usaping pangkaligtasan, etikal o regulasyon sa yugtong ito?"
            ]
        },
        {   # TRL-4
            "level": 4,
            "title": "Na-validate ang Teknolohiya sa Laboratoryo",
            "checks": [
                "May breadboard o prototype subsystem ba na na-integrate para sa testing sa laboratoryo?",
                "Tugma ba ang nasukat na performance sa inaasahan ayon sa modelo?",
                "Nadokumento at na-peer-review ba ang test procedures o na-replicate nang independiyente?",
                "May paunang talaan ba ng panganib para sa na-validate na subsystem?"
            ]
        },
        {   # TRL-5
            "level": 5,
            "title": "Na-validate sa Kaugnay na Kapaligiran",
            "checks": [
                "Na-upgrade ba ang breadboard para gumana sa kaugnay (pero di pa operasyonal) na kapaligiran?",
                "Saklaw ba ng environmental tests ang temperatura, vibration o iba pang stress na may kaugnayan sa domain?",
                "Nagsagawa ba ng assessment sa pagsunod sa mga pamantayan ng industriya o regulasyon?",
                "Na-update ba ang risk mitigation plan batay sa resulta ng tests?"
            ]
        },
        {   # TRL-6
            "level": 6,
            "title": "Prototype na Naipakita sa Kaugnay na Kapaligiran",
            "checks": [
                "Kumpleto ba ang system o subsystem model/prototype para maghatid ng batayang functionality?",
                "Naipakita ba end-to-end ang prototype sa kaugnay na kapaligiran?",
                "Ipinapakita ba ng data na naabot ng prototype ang kritikal na performance metrics sa tunay na limitasyon?",
                "May verification at validation report ba para sa prototype?"
            ]
        },
        {   # TRL-7
            "level": 7,
            "title": "Prototype ng Sistema sa Operasyonal na Kapaligiran",
            "checks": [
                "Na-install o na-subok ba ang prototype sa inaasahang operasyonal na setting?",
                "Pinatutunayan ba ng operasyonal na datos ang functionality sa aktwal na duty-cycle?",
                "Na-analyse ba ang failure modes at nadokumento ang corrective actions?",
                "Natukoy na ba ang supply-chain o ruta ng pagmamanupaktura para sa mahahalagang bahagi?"
            ]
        },
        {   # TRL-8
            "level": 8,
            "title": "Kumpleto at Na-qualify ang Sistema",
            "checks": [
                "Isang integrado at handa-komersiyal o mission-ready na sistema na ba ang teknolohiya?",
                "Naipasa ba nito ang kumpletong acceptance tests, certifications, o approvals?",
                "May opisyal na user manuals, maintenance plans at training materials na ba?",
                "May pilot customers o early adopters ba na nag-sign-off sa performance KPIs?"
            ]
        },
        {   # TRL-9
            "level": 9,
            "title": "Aktwal na Sistemang Napatunayan sa Operasyon",
            "checks": [
                "Na-deploy na ba ang teknolohiya sa final form sa regular na operasyon?",
                "Pinatutunayan ba ng pangmatagalang datos ang tuloy-tuloy na performance at reliability?",
                "Gumagana ba ang service-level agreements at QA processes nang buo?",
                "May framework ba para sa continual improvement o derivative products?"
            ]
        }
    ]
}

# Complete IRL Questions Database (1-6 with multiple checks per level)
IRL_QUESTIONS = {
    "english": [
        {   # IRL-1: Initial Concept
            "level": 1,
            "title": "Initial Concept",
            "checks": [
                "Is there a clear business idea or concept documented?",
                "Has a basic business model canvas been completed?",
                "Are the founders aware of the specific market need or problem being addressed?",
                "Is there any documentation of the idea or initial research conducted?",
                "Have you identified the core value proposition of your technology?"
            ]
        },
        {   # IRL-2: Market & Competitive Analysis
            "level": 2,
            "title": "Market & Competitive Analysis",
            "checks": [
                "Has the value proposition been clearly defined and summarized?",
                "Is there an initial analysis of the target market size and growth potential?",
                "Has a basic competitive landscape been mapped and analyzed?",
                "Have you identified potential barriers to entry or regulatory considerations?",
                "Are key market trends and opportunities documented?"
            ]
        },
        {   # IRL-3: Problem/Solution Validation
            "level": 3,
            "title": "Problem/Solution Validation",
            "checks": [
                "Has the problem-solution fit been validated with potential customers through interviews or surveys?",
                "Is there evidence that the proposed solution addresses a real and significant market need?",
                "Have customer segments and their specific needs been clearly identified?",
                "Is there documented feedback from early users or market experts?",
                "Have you validated key assumptions about customer pain points?"
            ]
        },
        {   # IRL-4: Prototype/Minimum Viable Product (MVP)
            "level": 4,
            "title": "Prototype/Minimum Viable Product (MVP)",
            "checks": [
                "Has a low-fidelity prototype or MVP been developed and tested?",
                "Has the MVP been tested internally or with a small group of target users?",
                "Are there initial performance metrics or user feedback data collected?",
                "Is there a documented plan for further product development and iteration?",
                "Have you established success criteria and KPIs for the MVP?"
            ]
        },
        {   # IRL-5: Product/Market Fit Validation
            "level": 5,
            "title": "Product/Market Fit Validation",
            "checks": [
                "Has the product been tested in the market with real users in actual conditions?",
                "Is there evidence of product/market fit such as repeat usage or positive feedback?",
                "Have key performance indicators (KPIs) been defined, tracked, and analyzed?",
                "Are there initial sales, signed letters of intent, or committed customers?",
                "Have you demonstrated customer retention and engagement metrics?"
            ]
        },
        {   # IRL-6: Business Model Validation
            "level": 6,
            "title": "Business Model Validation",
            "checks": [
                "Has the business model been tested and validated in real market conditions?",
                "Is there evidence of sustainable revenue generation or proven monetization strategy?",
                "Have operational processes been established, tested, and optimized?",
                "Are there validated assumptions about customer acquisition costs and lifetime value?",
                "Have you demonstrated scalability of the business model with growth projections?"
            ]
        }
    ],
    "filipino": [
        {   # IRL-1: Initial Concept
            "level": 1,
            "title": "Pangunahing Konsepto",
            "checks": [
                "May malinaw at nakadokumentong business idea o konsepto ba?",
                "Nakumpleto na ba ang basic business model canvas?",
                "Alam ba ng mga founder ang tiyak na market need o problemang aayusin?",
                "May dokumentasyon ba ng ideya o paunang pananaliksik na ginawa?",
                "Natukoy na ba ang core value proposition ng inyong teknolohiya?"
            ]
        },
        {   # IRL-2: Market & Competitive Analysis
            "level": 2,
            "title": "Market at Competitive Analysis",
            "checks": [
                "Malinaw na ba ang pagkakadefine at nabuod ang value proposition?",
                "May paunang pagsusuri ba ng target market size at growth potential?",
                "Nagawa na ba ang basic competitive landscape mapping at analysis?",
                "Natukoy na ba ang mga potential barriers to entry o regulatory considerations?",
                "Nakadokumento ba ang mga key market trends at opportunities?"
            ]
        },
        {   # IRL-3: Problem/Solution Validation
            "level": 3,
            "title": "Problem/Solution Validation",
            "checks": [
                "Na-validate na ba ang problem-solution fit sa pamamagitan ng interviews o surveys sa potential customers?",
                "May ebidensya ba na ang proposed solution ay tumutugunan sa tunay at malaking market need?",
                "Malinaw na ba ang pagkakakilala sa customer segments at kanilang specific needs?",
                "May nakadokumentong feedback ba mula sa early users o market experts?",
                "Na-validate na ba ang mga key assumptions tungkol sa customer pain points?"
            ]
        },
        {   # IRL-4: Prototype/Minimum Viable Product (MVP)
            "level": 4,
            "title": "Prototype/Minimum Viable Product (MVP)",
            "checks": [
                "Nakabuo at nasubukan na ba ang low-fidelity prototype o MVP?",
                "Nasubukan na ba ang MVP internally o sa maliit na grupo ng target users?",
                "May nakolektang initial performance metrics o user feedback data ba?",
                "May nakadokumentong plano ba para sa karagdagang product development at iteration?",
                "Naitakda na ba ang success criteria at KPIs para sa MVP?"
            ]
        },
        {   # IRL-5: Product/Market Fit Validation
            "level": 5,
            "title": "Product/Market Fit Validation",
            "checks": [
                "Nasubukan na ba ang produkto sa market kasama ang tunay na users sa aktwal na kondisyon?",
                "May ebidensya ba ng product/market fit tulad ng repeat usage o positive feedback?",
                "Naitakda, sinubaybayan, at na-analyze na ba ang key performance indicators (KPIs)?",
                "May initial sales, signed letters of intent, o committed customers na ba?",
                "Naipakita na ba ang customer retention at engagement metrics?"
            ]
        },
        {   # IRL-6: Business Model Validation
            "level": 6,
            "title": "Business Model Validation",
            "checks": [
                "Nasubukan at na-validate na ba ang business model sa tunay na market conditions?",
                "May ebidensya ba ng sustainable revenue generation o napatunayang monetization strategy?",
                "Naitatag, nasubukan, at na-optimize na ba ang operational processes?",
                "May na-validate na assumptions ba tungkol sa customer acquisition costs at lifetime value?",
                "Naipakita na ba ang scalability ng business model kasama ang growth projections?"
            ]
        }
    ]
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/questions/<mode>/<language>")
def get_questions(mode, language):
    if mode.upper() == "TRL":
        return jsonify(TRL_QUESTIONS.get(language.lower(), TRL_QUESTIONS["english"]))
    return jsonify(IRL_QUESTIONS.get(language.lower(), IRL_QUESTIONS["english"]))

@app.route("/api/assess", methods=["POST"])
def assess_technology():
    data = request.json
    mode = data["mode"]
    language = data["language"]
    answers = data["answers"]

    questions = (
        TRL_QUESTIONS if mode.upper() == "TRL" else IRL_QUESTIONS
    )[language.lower()]

    level_achieved = -1
    for idx, lvl in enumerate(questions):
        if idx >= len(answers) or not all(answers[idx]):
            break
        level_achieved = lvl["level"]

    result = {
        "mode": mode,
        "mode_full": ("Technology Readiness Level" if mode.upper()=="TRL" else "Investment Readiness Level"),
        "level": max(0, level_achieved),
        "technology_title": data["technology_title"],
        "description": data["description"],
        "explanation": generate_explanation(level_achieved, mode, language, questions),
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(result)

def generate_explanation(lvl, mode, lang, qset):
    if lang == "filipino":
        if lvl < 0:
            text = f"Hindi pa naaabot ng inyong teknolohiya ang antas 1 ng {mode}. Mangyaring kumpletuhin muna ang mga pangunahing requirements."
        else:
            text = f"Naabot ng inyong teknolohiya ang {mode} antas {lvl}. {qset[lvl]['title']} ang pinakahuling yugto na natugunan nang buo."
        
        if lvl + 1 < len(qset):
            nxt = qset[lvl + 1]
            text += f" Para umusad sa susunod na antas ({nxt['level']}), kinakailangan: {nxt['title']}."
        
        if mode == "IRL":
            if lvl < 3:
                text += " Mag-focus sa market research at validation ng inyong business concept."
            elif lvl < 5:
                text += " Patuloy na i-develop ang inyong produkto at maghanap ng early customers."
            else:
                text += " Mag-focus sa scaling at revenue generation para sa sustainable growth."
        
        return text
    
    # English
    if lvl < 0:
        text = f"Your technology has not yet satisfied the basic requirements for {mode} level 1."
    else:
        text = f"Your technology has achieved {mode} level {lvl} — {qset[lvl]['title']} requirements are fully met."
    
    if lvl + 1 < len(qset):
        nxt = qset[lvl + 1]
        text += f" To advance to level {nxt['level']}, you must complete: {nxt['title']}."
    
    if mode == "IRL":
        if lvl < 3:
            text += " Focus on market research and validating your business concept with potential customers."
        elif lvl < 5:
            text += " Continue developing your product and securing early customer commitments."
        else:
            text += " Focus on scaling operations and demonstrating sustainable revenue growth."
    
    return text

@app.route("/api/generate_pdf", methods=["POST"])
def generate_pdf():
    data = request.json
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    sty = getSampleStyleSheet()
    head = ParagraphStyle("H1", parent=sty["Heading1"], textColor=colors.darkgreen)
    
    doc_elements = [
        Paragraph(f"{data['mode_full']} Assessment Report", head),
        Spacer(1, 12),
        Paragraph(f"<b>Technology Title:</b> {data['technology_title']}", sty["Normal"]),
        Paragraph(f"<b>Description:</b> {data['description']}", sty["Normal"]),
        Paragraph(f"<b>Date:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", sty["Normal"]),
        Spacer(1, 12),
        Paragraph(f"<b>Assessment Result:</b> {data['mode']} Level {data['level']}", sty["Heading2"]),
        Spacer(1, 8),
        Paragraph(f"<b>Explanation:</b>", sty["Heading3"]),
        Paragraph(data["explanation"], sty["Normal"])
    ]
    
    doc.build(doc_elements)
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True,
                     download_name=f"{data['technology_title']}_{data['mode']}_Assessment.pdf")

if __name__ == "__main__":
    app.run(debug=True)
