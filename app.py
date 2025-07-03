from flask import Flask, render_template, request, jsonify, send_file
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime
import io

app = Flask(__name__)

# --------------------------------------------------------------------------
# 0.  DATA SOURCE:  nested guide-questions for each level in both languages
# --------------------------------------------------------------------------
TRL_QUESTIONS = {
    "english": [
        {   # TRL-0  ── Pre-concept
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
        {   # TRL-1  ── Basic principles observed
            "level": 1,
            "title": "Basic Principles Observed",
            "checks": [
                "Have the fundamental scientific principles underpinning the technology been identified?",
                "Is at least one peer-reviewed source or equivalent documentation available?",
                "Have theoretical or mathematical models been drafted to explain feasibility?",
                "Is there preliminary evidence or data supporting the stated principles?"
            ]
        },
        {   # TRL-2  ── Concept formulated
            "level": 2,
            "title": "Technology Concept Formulated",
            "checks": [
                "Is a specific technology concept or application now defined rather than an abstract idea?",
                "Are the advantages and potential use-cases described in technical language?",
                "Have initial feasibility analyses or simulations been completed?",
                "Is the concept documented in a white-paper, preprint or equivalent outlet?"
            ]
        },
        {   # TRL-3  ── Proof of concept
            "level": 3,
            "title": "Experimental Proof of Concept",
            "checks": [
                "Have critical functions or key performance parameters been identified?",
                "Have laboratory experiments demonstrated proof-of-concept for at least one function?",
                "Are performance metrics recorded and benchmarked against targets?",
                "Have safety, ethical or regulatory constraints been identified at this stage?"
            ]
        },
        {   # TRL-4  ── Lab validation
            "level": 4,
            "title": "Technology Validated in Laboratory",
            "checks": [
                "Has a breadboard or prototype subsystem been integrated for laboratory testing?",
                "Do measured performances meet or surpass model predictions within tolerances?",
                "Are test procedures documented and peer-reviewed or independently replicated?",
                "Is a preliminary risk register available for the validated subsystem?"
            ]
        },
        {   # TRL-5  ── Relevant-environment validation
            "level": 5,
            "title": "Technology Validated in Relevant Environment",
            "checks": [
                "Has the breadboard been upgraded for operation in a relevant (not yet operational) environment?",
                "Do environmental tests include temperature, vibration or other domain-specific stresses?",
                "Has compliance with domain standards been assessed by an external body or advisory board?",
                "Is an updated risk mitigation plan in place reflecting test outcomes?"
            ]
        },
        {   # TRL-6  ── Prototype demonstrated
            "level": 6,
            "title": "Prototype Demonstrated in Relevant Environment",
            "checks": [
                "Is a system/sub-system model or prototype complete enough to deliver baseline functionality?",
                "Has the prototype been demonstrated end-to-end in a relevant environment?",
                "Do data show the prototype meeting critical performance metrics under realistic constraints?",
                "Is a V&V (verification & validation) report available for this prototype?"
            ]
        },
        {   # TRL-7  ── System prototype in operational environment
            "level": 7,
            "title": "System Prototype Demonstrated in Operational Environment",
            "checks": [
                "Has the prototype been installed or trialed within the intended operational setting?",
                "Do operational data confirm functionality under real-world duty-cycles?",
                "Are failure modes analysed with corrective actions documented?",
                "Is the supply-chain or manufacturing route for key components identified?"
            ]
        },
        {   # TRL-8  ── Qualified through test & demo
            "level": 8,
            "title": "System Complete and Qualified",
            "checks": [
                "Is the technology an integrated commercial or mission-ready system?",
                "Has the system passed full acceptance tests, certifications, or regulatory approvals?",
                "Are formal user manuals, maintenance plans and training materials available?",
                "Have pilot customers or early adopters signed off on performance KPIs?"
            ]
        },
        {   # TRL-9  ── Proven in mission operations
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

#  IRL remains structurally identical to the initial design but is now nested:
IRL_QUESTIONS = {
    lang: [
        {
            "level": q["level"],
            "title": (
                q["description"].split(" - ")[0] if " - " in q["description"] else q["description"]
            ),
            "checks": [q["question"]]  # each IRL level still has one canonical check
        }
        for q in raw
    ] for lang, raw in {
        "english": [
            {"level": 1, "question": "Is there a clear market opportunity identified for your technology?", "description": "Market opportunity identification - basic market research completed"},
            {"level": 2, "question": "Has a preliminary business model been developed?", "description": "Business model formulation - initial business concept developed"},
            {"level": 3, "question": "Has market validation been conducted with potential customers?", "description": "Market validation - customer feedback and market research conducted"},
            {"level": 4, "question": "Is there a detailed business plan with financial projections?", "description": "Business plan development - comprehensive business strategy formulated"},
            {"level": 5, "question": "Has the management team been assembled with relevant expertise?", "description": "Management team formation - key personnel and advisors identified"},
            {"level": 6, "question": "Are there initial customer commitments or letters of intent?", "description": "Customer commitment - early adopters and strategic partnerships established"},
            {"level": 7, "question": "Has pilot testing or beta trials been completed successfully?", "description": "Pilot validation - real-world testing with customers completed"},
            {"level": 8, "question": "Is there proven revenue generation and scalable business operations?", "description": "Revenue generation - sustainable business model demonstrated"},
            {"level": 9, "question": "Has the venture achieved profitability and market penetration?", "description": "Market success - profitable operations and significant market share achieved"}
        ],
        "filipino": [
            {"level": 1, "question": "May nakilalang malinaw na market opportunity ba para sa inyong teknolohiya?", "description": "Market opportunity identification - natapos ang basic market research"},
            {"level": 2, "question": "Nakabuo na ba ng preliminary business model?", "description": "Business model formulation - nabuo ang initial business concept"},
            {"level": 3, "question": "Naisagawa na ba ang market validation kasama ang mga potensyal na customer?", "description": "Market validation - nakuha ang customer feedback at naisagawa ang market research"},
            {"level": 4, "question": "May detalyadong business plan ba kasama ang financial projections?", "description": "Business plan development - nabuo ang comprehensive business strategy"},
            {"level": 5, "question": "Nabuo na ba ang management team na may kaukulang expertise?", "description": "Management team formation - nakilala ang mga key personnel at advisors"},
            {"level": 6, "question": "May mga initial customer commitments o letters of intent ba?", "description": "Customer commitment - naitatag ang early adopters at strategic partnerships"},
            {"level": 7, "question": "Natapos na ba nang matagumpay ang pilot testing o beta trials?", "description": "Pilot validation - natapos ang real-world testing kasama ang mga customers"},
            {"level": 8, "question": "May napatunayang revenue generation at scalable business operations ba?", "description": "Revenue generation - napatunayan ang sustainable business model"},
            {"level": 9, "question": "Nakamit na ba ng venture ang profitability at market penetration?", "description": "Market success - nakamit ang profitable operations at malaking market share"}
        ]
    }.items()
}

# --------------------------------------------------------------------------
# 1.  FLASK ROUTES (unchanged except for nested scoring)
# --------------------------------------------------------------------------
@app.route("/")
def index():                                         # Home page
    return render_template("index.html")


@app.route("/api/questions/<mode>/<language>")
def get_questions(mode, language):                   # Provide questions for front-end
    if mode.upper() == "TRL":
        return jsonify(TRL_QUESTIONS.get(language.lower(), TRL_QUESTIONS["english"]))
    return jsonify(IRL_QUESTIONS.get(language.lower(), IRL_QUESTIONS["english"]))


@app.route("/api/assess", methods=["POST"])
def assess_technology():                             # Receive nested answers, compute level
    data       = request.json
    mode       = data["mode"]
    language   = data["language"]
    answers    = data["answers"]                     # 2-D list: answers[level_index][check_index]

    questions  = (
        TRL_QUESTIONS if mode.upper() == "TRL" else IRL_QUESTIONS
    )[language.lower()]

    level_achieved = -1
    for idx, lvl in enumerate(questions):
        if idx >= len(answers) or not all(answers[idx]):
            break
        level_achieved = lvl["level"]

    result = {
        "mode"       : mode,
        "mode_full"  : ("Technology Readiness Level" if mode.upper()=="TRL" else "Investment Readiness Level"),
        "level"      : max(0, level_achieved),
        "technology_title": data["technology_title"],
        "description": data["description"],
        "explanation": generate_explanation(level_achieved, mode, language, questions),
        "timestamp"  : datetime.utcnow().isoformat()
    }
    return jsonify(result)


def generate_explanation(lvl, mode, lang, qset):     # Human-readable narrative
    if lang == "filipino":
        if lvl < 0:
            text = f"Hindi pa naaabot ng inyong teknolohiya ang antas 0 ng {mode}. Mangyaring kumpletuhin muna ang mga unang tanong."
        else:
            text = f"Naabot ng inyong teknolohiya ang {mode} antas {lvl}. {qset[lvl]['title']} ang pinakahuling yugto na natugunan."
        if lvl + 1 < len(qset):
            nxt = qset[lvl + 1]
            text += f"  Para umusad sa antas {nxt['level']}, kinakailangan: {nxt['title']}."
        return text
    # English
    if lvl < 0:
        text = f"Your technology has not yet satisfied any criteria for {mode} level 0."
    else:
        text = f"Your technology satisfies all checks up to {mode} level {lvl} — {qset[lvl]['title']}."
    if lvl + 1 < len(qset):
        nxt = qset[lvl + 1]
        text += f"  To advance to level {nxt['level']}, you must meet: {nxt['title']}."
    return text


@app.route("/api/generate_pdf", methods=["POST"])
def generate_pdf():                                  # Portable result report
    data = request.json
    buf  = io.BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=A4)
    sty  = getSampleStyleSheet()
    head = ParagraphStyle("H1", parent=sty["Heading1"], textColor=colors.darkgreen)
    doc_elements = [
        Paragraph(f"{data['mode_full']} Assessment Report", head),
        Spacer(1, 12),
        Paragraph(f"<b>Technology Title:</b> {data['technology_title']}", sty["Normal"]),
        Paragraph(f"<b>Description:</b> {data['description']}", sty["Normal"]),
        Paragraph(f"<b>Date:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", sty["Normal"]),
        Spacer(1, 12),
        Paragraph(f"<b>Result:</b> {data['mode']} Level {data['level']}", sty["Heading2"]),
        Spacer(1, 8),
        Paragraph(data["explanation"], sty["Normal"])
    ]
    doc.build(doc_elements)
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True,
                     download_name=f"{data['technology_title']}_{data['mode']}_Assessment.pdf")


if __name__ == "__main__":
    app.run(debug=True)
