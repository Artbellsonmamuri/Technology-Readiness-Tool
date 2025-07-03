from flask import Flask, render_template, request, jsonify, send_file
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import io

app = Flask(__name__)

# Complete TRL Questions Database (0-9)
TRL_QUESTIONS = {
    "english": [
        {
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
        {
            "level": 1,
            "title": "Basic Principles Observed",
            "checks": [
                "Have the fundamental scientific principles underpinning the technology been identified?",
                "Is at least one peer-reviewed source or equivalent documentation available?",
                "Have theoretical or mathematical models been drafted to explain feasibility?",
                "Is there preliminary evidence or data supporting the stated principles?"
            ]
        },
        {
            "level": 2,
            "title": "Technology Concept Formulated",
            "checks": [
                "Is a specific technology concept or application now defined rather than an abstract idea?",
                "Are the advantages and potential use-cases described in technical language?",
                "Have initial feasibility analyses or simulations been completed?",
                "Is the concept documented in a white-paper, preprint or equivalent outlet?"
            ]
        },
        {
            "level": 3,
            "title": "Experimental Proof of Concept",
            "checks": [
                "Have critical functions or key performance parameters been identified?",
                "Have laboratory experiments demonstrated proof-of-concept for at least one function?",
                "Are performance metrics recorded and benchmarked against targets?",
                "Have safety, ethical or regulatory constraints been identified at this stage?"
            ]
        },
        {
            "level": 4,
            "title": "Technology Validated in Laboratory",
            "checks": [
                "Has a breadboard or prototype subsystem been integrated for laboratory testing?",
                "Do measured performances meet or surpass model predictions within tolerances?",
                "Are test procedures documented and peer-reviewed or independently replicated?",
                "Is a preliminary risk register available for the validated subsystem?"
            ]
        },
        {
            "level": 5,
            "title": "Technology Validated in Relevant Environment",
            "checks": [
                "Has the breadboard been upgraded for operation in a relevant (not yet operational) environment?",
                "Do environmental tests include temperature, vibration or other domain-specific stresses?",
                "Has compliance with domain standards been assessed by an external body or advisory board?",
                "Is an updated risk mitigation plan in place reflecting test outcomes?"
            ]
        },
        {
            "level": 6,
            "title": "Prototype Demonstrated in Relevant Environment",
            "checks": [
                "Is a system/sub-system model or prototype complete enough to deliver baseline functionality?",
                "Has the prototype been demonstrated end-to-end in a relevant environment?",
                "Do data show the prototype meeting critical performance metrics under realistic constraints?",
                "Is a V&V (verification & validation) report available for this prototype?"
            ]
        },
        {
            "level": 7,
            "title": "System Prototype Demonstrated in Operational Environment",
            "checks": [
                "Has the prototype been installed or trialed within the intended operational setting?",
                "Do operational data confirm functionality under real-world duty-cycles?",
                "Are failure modes analysed with corrective actions documented?",
                "Is the supply-chain or manufacturing route for key components identified?"
            ]
        },
        {
            "level": 8,
            "title": "System Complete and Qualified",
            "checks": [
                "Is the technology an integrated commercial or mission-ready system?",
                "Has the system passed full acceptance tests, certifications, or regulatory approvals?",
                "Are formal user manuals, maintenance plans and training materials available?",
                "Have pilot customers or early adopters signed off on performance KPIs?"
            ]
        },
        {
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
        {
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
        {
            "level": 1,
            "title": "Pangunahing Prinsipyo na-obserbahan",
            "checks": [
                "Natukoy na ba ang mga batayang prinsipyong siyentipiko ng teknolohiya?",
                "Mayroon bang kahit isang peer-reviewed na sanggunian o katumbas na dokumentasyon?",
                "Nabuo na ba ang teoretikal o matematikal na modelo upang patunayan ang posibilidad?",
                "May paunang ebidensiya o datos ba na sumusuporta sa mga prinsipyong ito?"
            ]
        },
        {
            "level": 2,
            "title": "Nabuo ang Konsepto ng Teknolohiya",
            "checks": [
                "May tiyak na konsepto o aplikasyong teknolohikal na ba kaysa sa abstraktong ideya?",
                "Naipaliwanag ba ang mga benepisyo at posibleng gamit sa teknikal na wika?",
                "Nagawa na ba ang paunang feasibility analysis o simulation?",
                "Nakadokumento ba ang konsepto sa white-paper, preprint o katumbas?"
            ]
        },
        {
            "level": 3,
            "title": "Eksperimental na Patunay ng Konsepto",
            "checks": [
                "Natukoy na ba ang mga kritikal na function o key performance parameters?",
                "May mga eksperimento bang laboratoryo na nagpatunay ng konsepto para kahit isang function?",
                "Naitala at na-benchmark ba ang performance metrics laban sa target?",
                "Natukoy na ba ang mga usaping pangkaligtasan, etikal o regulasyon sa yugtong ito?"
            ]
        },
        {
            "level": 4,
            "title": "Na-validate ang Teknolohiya sa Laboratoryo",
            "checks": [
                "May breadboard o prototype subsystem ba na na-integrate para sa testing sa laboratoryo?",
                "Tugma ba ang nasukat na performance sa inaasahan ayon sa modelo?",
                "Nadokumento at na-peer-review ba ang test procedures o na-replicate nang independiyente?",
                "May paunang talaan ba ng panganib para sa na-validate na subsystem?"
            ]
        },
        {
            "level": 5,
            "title": "Na-validate sa Kaugnay na Kapaligiran",
            "checks": [
                "Na-upgrade ba ang breadboard para gumana sa kaugnay (pero di pa operasyonal) na kapaligiran?",
                "Saklaw ba ng environmental tests ang temperatura, vibration o iba pang stress na may kaugnayan sa domain?",
                "Nagsagawa ba ng assessment sa pagsunod sa mga pamantayan ng industriya o regulasyon?",
                "Na-update ba ang risk mitigation plan batay sa resulta ng tests?"
            ]
        },
        {
            "level": 6,
            "title": "Prototype na Naipakita sa Kaugnay na Kapaligiran",
            "checks": [
                "Kumpleto ba ang system o subsystem model/prototype para maghatid ng batayang functionality?",
                "Naipakita ba end-to-end ang prototype sa kaugnay na kapaligiran?",
                "Ipinapakita ba ng data na naabot ng prototype ang kritikal na performance metrics sa tunay na limitasyon?",
                "May verification at validation report ba para sa prototype?"
            ]
        },
        {
            "level": 7,
            "title": "Prototype ng Sistema sa Operasyonal na Kapaligiran",
            "checks": [
                "Na-install o na-subok ba ang prototype sa inaasahang operasyonal na setting?",
                "Pinatutunayan ba ng operasyonal na datos ang functionality sa aktwal na duty-cycle?",
                "Na-analyse ba ang failure modes at nadokumento ang corrective actions?",
                "Natukoy na ba ang supply-chain o ruta ng pagmamanupaktura para sa mahahalagang bahagi?"
            ]
        },
        {
            "level": 8,
            "title": "Kumpleto at Na-qualify ang Sistema",
            "checks": [
                "Isang integrado at handa-komersiyal o mission-ready na sistema na ba ang teknolohiya?",
                "Naipasa ba nito ang kumpletong acceptance tests, certifications, o approvals?",
                "May opisyal na user manuals, maintenance plans at training materials na ba?",
                "May pilot customers o early adopters ba na nag-sign-off sa performance KPIs?"
            ]
        },
        {
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

# Complete IRL Questions Database (1-9)
IRL_QUESTIONS = {
    "english": [
        {
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
        {
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
        {
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
        {
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
        {
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
        {
            "level": 6,
            "title": "Business Model Validation",
            "checks": [
                "Has the business model been tested and validated in real market conditions?",
                "Is there evidence of sustainable revenue generation or proven monetization strategy?",
                "Have operational processes been established, tested, and optimized?",
                "Are there validated assumptions about customer acquisition costs and lifetime value?",
                "Have you demonstrated scalability of the business model with growth projections?"
            ]
        },
        {
            "level": 7,
            "title": "Investment Ready / Early Commercial",
            "checks": [
                "Has a comprehensive business plan been developed with detailed financial projections?",
                "Is there a complete management team with relevant industry experience?",
                "Have you secured initial funding, investment, or significant partnerships?",
                "Are intellectual property rights and legal structures properly established?",
                "Have you achieved initial commercial sales or revenue milestones?"
            ]
        },
        {
            "level": 8,
            "title": "Commercial Scaling",
            "checks": [
                "Is the business generating consistent and growing revenue streams?",
                "Have you established scalable operations and distribution channels?",
                "Are customer acquisition and retention processes optimized and repeatable?",
                "Have you achieved positive cash flow or clear path to profitability?",
                "Is there evidence of market traction and competitive positioning?"
            ]
        },
        {
            "level": 9,
            "title": "Market Leadership / Expansion",
            "checks": [
                "Has the business achieved sustainable profitability and market leadership?",
                "Are you expanding into new markets, products, or customer segments?",
                "Have you established strong brand recognition and customer loyalty?",
                "Are there strategic partnerships or acquisition opportunities being pursued?",
                "Is there a clear strategy for long-term growth and market expansion?"
            ]
        }
    ],
    "filipino": [
        {
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
        {
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
        {
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
        {
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
        {
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
        {
            "level": 6,
            "title": "Business Model Validation",
            "checks": [
                "Nasubukan at na-validate na ba ang business model sa tunay na market conditions?",
                "May ebidensya ba ng sustainable revenue generation o napatunayang monetization strategy?",
                "Naitatag, nasubukan, at na-optimize na ba ang operational processes?",
                "May na-validate na assumptions ba tungkol sa customer acquisition costs at lifetime value?",
                "Naipakita na ba ang scalability ng business model kasama ang growth projections?"
            ]
        },
        {
            "level": 7,
            "title": "Handa sa Investment / Early Commercial",
            "checks": [
                "Nabuo na ba ang comprehensive business plan na may detalyadong financial projections?",
                "May kumpletong management team ba na may kaugnay na industry experience?",
                "Nakakuha na ba ng initial funding, investment, o makabuluhang partnerships?",
                "Naitatag na ba nang maayos ang intellectual property rights at legal structures?",
                "Nakamit na ba ang initial commercial sales o revenue milestones?"
            ]
        },
        {
            "level": 8,
            "title": "Commercial Scaling",
            "checks": [
                "Gumagawa ba ang business ng consistent at lumalaking revenue streams?",
                "Naitatag na ba ang scalable operations at distribution channels?",
                "Na-optimize na ba at nauulit ang customer acquisition at retention processes?",
                "Nakamit na ba ang positive cash flow o malinaw na daan patungo sa profitability?",
                "May ebidensya ba ng market traction at competitive positioning?"
            ]
        },
        {
            "level": 9,
            "title": "Market Leadership / Expansion",
            "checks": [
                "Nakamit na ba ng business ang sustainable profitability at market leadership?",
                "Nag-eexpand ba kayo sa bagong markets, products, o customer segments?",
                "Naitatag na ba ang malakas na brand recognition at customer loyalty?",
                "May strategic partnerships o acquisition opportunities ba na sinusubaybayan?",
                "May malinaw na estratehiya ba para sa long-term growth at market expansion?"
            ]
        }
    ]
}

# TCP Questions Database
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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/questions/<mode>/<language>")
def get_questions(mode, language):
    if mode.upper() == "TRL":
        return jsonify(TRL_QUESTIONS.get(language.lower(), TRL_QUESTIONS["english"]))
    elif mode.upper() == "IRL":
        return jsonify(IRL_QUESTIONS.get(language.lower(), IRL_QUESTIONS["english"]))
    elif mode.upper() == "TCP":
        return jsonify(TCP_QUESTIONS.get(language.lower(), TCP_QUESTIONS["english"]))
    return jsonify([])

@app.route("/api/assess", methods=["POST"])
def assess_technology():
    data = request.json
    mode = data["mode"]
    
    if mode.upper() == "TCP":
        return assess_tcp(data)
    else:
        return assess_trl_irl(data)

def assess_trl_irl(data):
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
        "answers": answers,
        "questions": questions,
        "explanation": generate_explanation(level_achieved, mode, language, questions),
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(result)

def assess_tcp(data):
    language = data["language"]
    answers = data["answers"]
    tcp_data = TCP_QUESTIONS[language.lower()]
    
    pathway_scores = calculate_pathway_scores(answers, tcp_data)
    recommended_pathway = max(pathway_scores, key=pathway_scores.get)
    
    result = {
        "mode": "TCP",
        "mode_full": "Technology Commercialization Pathway",
        "technology_title": data["technology_title"],
        "description": data["description"],
        "answers": answers,
        "tcp_data": tcp_data,
        "pathway_scores": pathway_scores,
        "recommended_pathway": recommended_pathway,
        "explanation": generate_tcp_explanation(pathway_scores, recommended_pathway, language),
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(result)

def calculate_pathway_scores(answers, tcp_data):
    pathways = {pathway["name"]: 0 for pathway in tcp_data["pathways"]}
    
    # Ensure we have enough answers
    if len(answers) < 15:
        # Pad with zeros if not enough answers
        answers = answers + [0] * (15 - len(answers))
    
    tech_score = sum(answers[0:3])
    market_score = sum(answers[3:6])
    business_score = sum(answers[6:9])
    regulatory_score = sum(answers[9:11])
    team_score = sum(answers[11:13])
    strategic_score = sum(answers[13:15])
    
    pathways["Direct Sale"] = tech_score + business_score + market_score
    pathways["Licensing"] = tech_score + market_score + (9 - business_score)
    pathways["Startup/Spin-out"] = tech_score + team_score + market_score
    pathways["Assignment"] = tech_score + (9 - strategic_score)
    pathways["Research Collaboration"] = (9 - tech_score) + team_score + strategic_score
    pathways["Open Source"] = strategic_score + market_score + (9 - regulatory_score)
    pathways["Government Procurement"] = tech_score + regulatory_score + market_score
    
    return pathways

def generate_tcp_explanation(pathway_scores, recommended_pathway, language):
    if language == "filipino":
        text = f"Batay sa assessment, ang pinakarekomendadong commercialization pathway para sa inyong teknolohiya ay ang {recommended_pathway}. "
        text += f"Ang pathway na ito ay nakakuha ng pinakamataas na score sa evaluation. "
        text += "Dapat isaalang-alang ang mga strengths at weaknesses ng inyong teknolohiya sa pagpili ng final strategy."
    else:
        text = f"Based on the assessment, the most recommended commercialization pathway for your technology is {recommended_pathway}. "
        text += f"This pathway scored highest in the evaluation criteria. "
        text += "Consider your technology's specific strengths and organizational capabilities when finalizing your commercialization strategy."
    
    return text

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
            elif lvl < 6:
                text += " Patuloy na i-develop ang inyong produkto at maghanap ng early customers."
            else:
                text += " Mag-focus sa scaling at revenue generation para sa sustainable growth."
        
        return text
    
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
        elif lvl < 6:
            text += " Continue developing your product and securing early customer commitments."
        else:
            text += " Focus on scaling operations and demonstrating sustainable revenue growth."
    
    return text

@app.route("/api/generate_pdf", methods=["POST"])
def generate_pdf():
    try:
        data = request.json
        
        # Validate required fields
        if not data or 'mode' not in data:
            return jsonify({"error": "Invalid data provided"}), 400
            
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=0.5*inch)
        sty = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle("Title", parent=sty["Heading1"], 
                                   fontSize=16, textColor=colors.darkgreen, 
                                   alignment=1, spaceAfter=6)
        subtitle_style = ParagraphStyle("Subtitle", parent=sty["Normal"], 
                                       fontSize=10, textColor=colors.darkblue, 
                                       alignment=1, spaceAfter=12)
        heading_style = ParagraphStyle("Heading", parent=sty["Heading2"], 
                                      fontSize=12, textColor=colors.darkgreen)
        
        doc_elements = []

        # Header
        doc_elements.append(Paragraph("MARANO MARCOS STATE UNIVERSITY", title_style))
        doc_elements.append(Paragraph("Innovation and Technology Support Office", subtitle_style))
        doc_elements.append(Paragraph("Technology Assessment Tool", subtitle_style))
        doc_elements.append(Spacer(1, 18))

        doc_elements.append(Paragraph(f"{data.get('mode_full', data['mode'])} Assessment Report", heading_style))
        doc_elements.append(Spacer(1, 10))

        # Technology Information
        tech_info = [
            ["Technology Title:", data.get('technology_title', 'N/A')],
            ["Description:", data.get('description', 'N/A')],
            ["Assessment Date:", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')]
        ]
        
        if data['mode'] == 'TCP':
            tech_info.append(["Recommended Pathway:", data.get('recommended_pathway', 'N/A')])
        else:
            tech_info.append(["Assessment Result:", f"{data['mode']} Level {data.get('level', 'N/A')}"])

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

        # Assessment Summary
        doc_elements.append(Paragraph("Assessment Summary", heading_style))
        doc_elements.append(Paragraph(data.get("explanation", "No explanation available."), sty["Normal"]))
        doc_elements.append(Spacer(1, 14))

        # Mode-specific content
        if data["mode"] == "TCP":
            generate_tcp_pdf_content(doc_elements, data, sty, heading_style)
        else:
            generate_trl_irl_pdf_content(doc_elements, data, sty, heading_style)

        # Footer
        doc_elements.append(Spacer(1, 14))
        footer_style = ParagraphStyle("Footer", parent=sty["Normal"], 
                                     fontSize=8, textColor=colors.grey, 
                                     alignment=1)
        doc_elements.append(Paragraph("Generated by MMSU Innovation and Technology Support Office", footer_style))
        doc_elements.append(Paragraph("Technology Assessment Tool", footer_style))

        doc.build(doc_elements)
        buf.seek(0)
        
        filename = f"MMSU_{data.get('technology_title', 'Assessment')}_{data['mode']}_Assessment.pdf"
        # Clean filename
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ").strip()
        
        return send_file(
            buf, 
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"PDF Generation Error: {str(e)}")
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500

def generate_tcp_pdf_content(doc_elements, data, sty, heading_style):
    """Generate TCP-specific PDF content"""
    
    # Pathway Scores
    doc_elements.append(Paragraph("Commercialization Pathway Scores", heading_style))
    doc_elements.append(Spacer(1, 8))

    pathway_scores = data.get('pathway_scores', {})
    if pathway_scores:
        score_data = [["Pathway", "Score", "Ranking"]]
        sorted_pathways = sorted(pathway_scores.items(), key=lambda x: x[1], reverse=True)
        for rank, (pathway, score) in enumerate(sorted_pathways, 1):
            score_data.append([pathway, str(score), f"#{rank}"])

        score_table = Table(score_data, colWidths=[2.5*inch, 0.8*inch, 0.7*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER')
        ]))
        doc_elements.append(score_table)
    else:
        doc_elements.append(Paragraph("No pathway scores available.", sty["Normal"]))
    
    doc_elements.append(Spacer(1, 12))

    # Detailed Responses
    doc_elements.append(Paragraph("Detailed Assessment Responses", heading_style))
    doc_elements.append(Spacer(1, 8))
    
    tcp_data = data.get('tcp_data', {})
    answers = data.get('answers', [])
    
    if tcp_data and answers:
        answer_idx = 0
        for dimension in tcp_data.get('dimensions', []):
            doc_elements.append(Paragraph(dimension['name'], sty["Heading3"]))
            
            for question in dimension['questions']:
                if answer_idx < len(answers):
                    score = answers[answer_idx]
                    if score == 1:
                        score_text = "Low (1)"
                    elif score == 2:
                        score_text = "Medium (2)"
                    elif score == 3:
                        score_text = "High (3)"
                    else:
                        score_text = "Not answered"
                else:
                    score_text = "Not answered"
                
                doc_elements.append(Paragraph(f"Q{answer_idx+1}. {question}", sty["Normal"]))
                doc_elements.append(Paragraph(f"Response: {score_text}", sty["Normal"]))
                doc_elements.append(Spacer(1, 6))
                answer_idx += 1
            doc_elements.append(Spacer(1, 8))
    else:
        doc_elements.append(Paragraph("No detailed responses available.", sty["Normal"]))

    # Strategic Recommendations
    doc_elements.append(Paragraph("Strategic Recommendations", heading_style))
    recommended_pathway = data.get('recommended_pathway', '')
    recommendations = get_pathway_recommendations(recommended_pathway)
    doc_elements.append(Paragraph(recommendations, sty["Normal"]))

def generate_trl_irl_pdf_content(doc_elements, data, sty, heading_style):
    """Generate TRL/IRL-specific PDF content"""
    doc_elements.append(Paragraph("Detailed Assessment Results", heading_style))
    doc_elements.append(Spacer(1, 10))
    
    questions = data.get('questions', [])
    answers = data.get('answers', [])
    
    if questions and answers:
        for idx, level in enumerate(questions):
            level_title = f"{data['mode']} Level {level['level']}: {level['title']}"
            doc_elements.append(Paragraph(level_title, sty["Heading3"]))
            
            if idx < len(answers):
                level_answers = answers[idx]
                for q_idx, question in enumerate(level['checks']):
                    if q_idx < len(level_answers):
                        answer = "Yes" if level_answers[q_idx] else "No"
                    else:
                        answer = "Not answered"
                    
                    doc_elements.append(Paragraph(f"Q{q_idx+1}. {question}", sty["Normal"]))
                    doc_elements.append(Paragraph(f"Answer: {answer}", sty["Normal"]))
                    doc_elements.append(Spacer(1, 4))
            doc_elements.append(Spacer(1, 8))
    else:
        doc_elements.append(Paragraph("No detailed assessment results available.", sty["Normal"]))

def get_pathway_recommendations(pathway):
    """Get recommendations for a specific pathway"""
    recommendations = {
        "Direct Sale": "Focus on developing comprehensive go-to-market strategy, establishing direct sales channels, investing in marketing and brand development, ensuring manufacturing capabilities, and securing pilot customers. Build strong customer relationships and ensure product quality meets market expectations.",
        
        "Licensing": "Strengthen intellectual property protection through patents and trademarks. Identify potential licensees with established market presence and complementary capabilities. Develop comprehensive licensing packages that include technical documentation, training materials, and ongoing support. Negotiate favorable terms that balance upfront payments, royalties, and milestone-based compensation.",
        
        "Startup/Spin-out": "Assemble an experienced management team with relevant industry expertise and entrepreneurial experience. Develop a comprehensive business plan with detailed market analysis, financial projections, and growth strategies. Secure initial funding through angel investors, venture capital, or government grants. Establish proper legal structure and intellectual property ownership arrangements.",
        
        "Assignment": "Conduct thorough technology valuation using multiple methodologies including cost, market, and income approaches. Identify potential acquirers with strategic interest and complementary capabilities. Prepare comprehensive technology transfer packages including all documentation, know-how, and training materials. Negotiate favorable terms that maximize value while ensuring successful technology transfer.",
        
        "Research Collaboration": "Identify research partners with complementary expertise, resources, and strategic objectives. Develop joint research proposals that clearly define objectives, responsibilities, and intellectual property arrangements. Secure funding through collaborative grants and partnership agreements. Establish governance structures for project management and decision-making. Plan eventual commercialization pathways.",
        
        "Open Source": "Develop open source licensing strategy that balances community building with commercial opportunities. Create comprehensive documentation, tutorials, and developer resources to encourage adoption. Build community engagement through forums, conferences, and collaborative development platforms. Identify service revenue opportunities including consulting, training, and premium support.",
        
        "Government Procurement": "Understand government procurement processes, requirements, and evaluation criteria. Ensure full compliance with relevant regulations, security standards, and certification requirements. Develop relationships with government agencies, prime contractors, and system integrators. Prepare for extended procurement timelines and bureaucratic processes. Consider government funding opportunities such as SBIR/STTR programs."
    }
    
    return recommendations.get(pathway, "Develop a customized commercialization strategy based on your technology's unique characteristics, market conditions, and organizational capabilities. Consider consulting with technology transfer professionals and industry experts to optimize your approach.")

if __name__ == "__main__":
    app.run(debug=True)
