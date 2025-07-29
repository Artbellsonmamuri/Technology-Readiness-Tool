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

# COMPLETE QUESTION DATABASES
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

MRL_QUESTIONS = {
    "english": [
        {
            "level": 1,
            "title": "Market Need Identification",
            "checks": [
                "Has a specific market problem or unmet need been clearly identified?",
                "Is there preliminary evidence that the identified need is significant and widespread?",
                "Have initial market pain points been documented through observations or informal discussions?",
                "Is there awareness of existing solutions and their limitations in addressing the identified need?"
            ]
        },
        {
            "level": 2,
            "title": "Market Research and Analysis",
            "checks": [
                "Has formal market research been conducted to validate the identified market need?",
                "Is there documented analysis of market size, growth trends, and dynamics?",
                "Have target customer segments been preliminarily identified and characterized?",
                "Is there understanding of market drivers, barriers, and key success factors?",
                "Have relevant industry reports, studies, or expert opinions been gathered and analyzed?"
            ]
        },
        {
            "level": 3,
            "title": "Customer Discovery and Validation",
            "checks": [
                "Have direct interviews or surveys been conducted with potential customers?",
                "Is there validated evidence that customers experience the identified problem?",
                "Have customer personas and use cases been developed based on real feedback?",
                "Is there documented willingness from customers to consider alternative solutions?",
                "Have customer requirements and decision-making criteria been identified?"
            ]
        },
        {
            "level": 4,
            "title": "Market Segmentation and Sizing",
            "checks": [
                "Have distinct market segments been identified and prioritized based on data?",
                "Is there quantitative analysis of Total Addressable Market (TAM) and Serviceable Available Market (SAM)?",
                "Have early adopter segments been identified with specific characteristics?",
                "Is there analysis of market penetration potential and adoption barriers?"
            ]
        },
        {
            "level": 5,
            "title": "Competitive Analysis and Positioning",
            "checks": [
                "Has a comprehensive competitive landscape analysis been completed?",
                "Are direct and indirect competitors identified with their strengths and weaknesses?",
                "Is there clear differentiation and unique value proposition compared to existing solutions?",
                "Have competitive pricing models and market positioning strategies been analyzed?",
                "Is there understanding of competitive response scenarios?"
            ]
        },
        {
            "level": 6,
            "title": "Go-to-Market Strategy Development",
            "checks": [
                "Has a comprehensive go-to-market strategy been developed and documented?",
                "Are distribution channels and sales strategies clearly defined?",
                "Is there a marketing and customer acquisition plan with defined tactics?",
                "Have partnerships and strategic alliances been identified and approached?",
                "Is there a pricing strategy based on market research and competitive analysis?"
            ]
        },
        {
            "level": 7,
            "title": "Market Testing and Pilot Programs",
            "checks": [
                "Have pilot programs or market tests been conducted with real customers?",
                "Is there validated customer adoption and usage data from controlled market tests?",
                "Have key performance indicators for market success been defined and measured?",
                "Is there evidence of customer satisfaction and willingness to pay?",
                "Have market test results been used to refine the value proposition and strategy?"
            ]
        },
        {
            "level": 8,
            "title": "Market Launch Preparation",
            "checks": [
                "Are all market launch preparations completed including sales materials and training?",
                "Have launch partnerships and distribution agreements been secured?",
                "Is there established customer support and service infrastructure?",
                "Are marketing campaigns and launch activities planned and ready for execution?",
                "Have success metrics and monitoring systems been established for market launch?"
            ]
        },
        {
            "level": 9,
            "title": "Market Adoption and Scale",
            "checks": [
                "Has the technology achieved measurable market adoption with growing customer base?",
                "Are there established market channels generating consistent demand?",
                "Is there evidence of market acceptance and positive customer testimonials?",
                "Have expansion opportunities into adjacent markets been identified and planned?",
                "Is there a track record of successful market performance and growth?"
            ]
        }
    ],
    "filipino": [
        {
            "level": 1,
            "title": "Pagkilala sa Pangangailangan ng Market",
            "checks": [
                "Malinaw bang natukoy ang specific na problema o hindi natutugunang pangangailangan sa market?",
                "May paunang ebidensya ba na ang natukoyang pangangailangan ay malaki at malawakang naranasan?",
                "Nadokumento na ba ang initial market pain points sa pamamagitan ng obserbasyon o informal na diskusyon?",
                "May kamalayan ba sa existing solutions at ang kanilang mga limitasyon sa pagtugunan ng natukoyang pangangailangan?"
            ]
        },
        {
            "level": 2,
            "title": "Market Research at Analysis",
            "checks": [
                "Nagsagawa na ba ng formal market research upang ma-validate ang natukoyang market need?",
                "May nakadokumentong analysis ba ng market size, growth trends, at dynamics?",
                "Paunang natukoy at na-characterize na ba ang target customer segments?",
                "May pag-unawa ba sa market drivers, barriers, at key success factors?",
                "Nakolekta at na-analyze na ba ang relevant industry reports, studies, o expert opinions?"
            ]
        },
        {
            "level": 3,
            "title": "Customer Discovery at Validation",
            "checks": [
                "Nagsagawa na ba ng direct interviews o surveys sa mga potential customers?",
                "May na-validate na ebidensya ba na naranasan ng customers ang natukoyang problema?",
                "Nabuo na ba ang customer personas at use cases batay sa tunay na feedback?",
                "May nakadokumentong willingness ba mula sa customers na isaalang-alang ang alternative solutions?",
                "Natukoy na ba ang customer requirements at decision-making criteria?"
            ]
        },
        {
            "level": 4,
            "title": "Market Segmentation at Sizing",
            "checks": [
                "Natukoy at na-prioritize na ba ang distinct market segments batay sa datos?",
                "May quantitative analysis ba ng Total Addressable Market (TAM) at Serviceable Available Market (SAM)?",
                "Natukoy na ba ang early adopter segments na may specific na karakteristika?",
                "May analysis ba ng market penetration potential at adoption barriers?"
            ]
        },
        {
            "level": 5,
            "title": "Competitive Analysis at Positioning",
            "checks": [
                "Nakumpleto na ba ang comprehensive competitive landscape analysis?",
                "Natukoy na ba ang direct at indirect competitors kasama ang kanilang mga strengths at weaknesses?",
                "May malinaw na differentiation at unique value proposition ba kumpara sa existing solutions?",
                "Na-analyze na ba ang competitive pricing models at market positioning strategies?",
                "May pag-unawa ba sa competitive response scenarios?"
            ]
        },
        {
            "level": 6,
            "title": "Go-to-Market Strategy Development",
            "checks": [
                "Nabuo at nadokumento na ba ang comprehensive go-to-market strategy?",
                "Malinaw bang natukoy ang distribution channels at sales strategies?",
                "May marketing at customer acquisition plan ba na may defined tactics?",
                "Natukoy at na-approach na ba ang partnerships at strategic alliances?",
                "May pricing strategy ba batay sa market research at competitive analysis?"
            ]
        },
        {
            "level": 7,
            "title": "Market Testing at Pilot Programs",
            "checks": [
                "Nagsagawa na ba ng pilot programs o market tests kasama ang tunay na customers?",
                "May na-validate na customer adoption at usage data ba mula sa controlled market tests?",
                "Natukoy at nasukat na ba ang key performance indicators para sa market success?",
                "May ebidensya ba ng customer satisfaction at willingness to pay?",
                "Ginamit na ba ang market test results upang i-refine ang value proposition at strategy?"
            ]
        },
        {
            "level": 8,
            "title": "Market Launch Preparation",
            "checks": [
                "Nakumpleto na ba ang lahat ng market launch preparations kasama ang sales materials at training?",
                "Na-secure na ba ang launch partnerships at distribution agreements?",
                "May naitatag na customer support at service infrastructure ba?",
                "Naplano at handa na ba ang marketing campaigns at launch activities para sa execution?",
                "Naitatag na ba ang success metrics at monitoring systems para sa market launch?"
            ]
        },
        {
            "level": 9,
            "title": "Market Adoption at Scale",
            "checks": [
                "Nakamit na ba ng teknolohiya ang measurable market adoption na may lumalaking customer base?",
                "May naitatagang market channels ba na gumagawa ng consistent demand?",
                "May ebidensya ba ng market acceptance at positive customer testimonials?",
                "Natukoy at naplano na ba ang expansion opportunities sa adjacent markets?",
                "May track record ba ng successful market performance at growth?"
            ]
        }
    ]
}

TCP_QUESTIONS = {
    "english": {
        "dimensions": [
            {
                "name": "Technology & Product Readiness",
                "questions": [
                    "How complete is your technology development status?",
                    "How strong is your technology's value proposition compared to existing solutions?",
                    "How robust is your intellectual property protection strategy?"
                ]
            },
            {
                "name": "Market & Customer",
                "questions": [
                    "How well-defined is your target market with demonstrated demand?",
                    "How strong is your competitive advantage in the market?",
                    "How adequate is the market size for your commercialization pathway?"
                ]
            },
            {
                "name": "Business & Financial",
                "questions": [
                    "How capable is your organization to manufacture, market, and sell directly?",
                    "How accessible is the external investment you require?",
                    "How established are your channels for reaching customers?"
                ]
            },
            {
                "name": "Regulatory & Policy",
                "questions": [
                    "How manageable are the regulatory hurdles for your technology?",
                    "How supportive is the policy environment for your commercialization?"
                ]
            },
            {
                "name": "Organizational & Team",
                "questions": [
                    "How experienced is your team in product development, sales, and scaling?",
                    "How strong is your organization's capacity to form or support a new company?"
                ]
            },
            {
                "name": "Strategic Fit",
                "questions": [
                    "How aligned is this technology with your organization's core mission?",
                    "How valuable would open-source release be for accelerating adoption?"
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
                    "Gaano na ka-kompleto ang development status ng inyong teknolohiya?",
                    "Gaano kalakas ang value proposition ng inyong teknolohiya kumpara sa existing solutions?",
                    "Gaano ka-robust ang inyong intellectual property protection strategy?"
                ]
            },
            {
                "name": "Market at Customer",
                "questions": [
                    "Gaano ka-well-defined ang inyong target market na may demonstrated demand?",
                    "Gaano kalakas ang inyong competitive advantage sa market?",
                    "Gaano ka-adequate ang market size para sa inyong commercialization pathway?"
                ]
            },
            {
                "name": "Business at Financial",
                "questions": [
                    "Gaano ka-capable ang inyong organisasyon na mag-manufacture, mag-market, at mag-sell directly?",
                    "Gaano ka-accessible ang external investment na kailangan ninyo?",
                    "Gaano ka-established ang inyong channels para maabot ang customers?"
                ]
            },
            {
                "name": "Regulatory at Policy",
                "questions": [
                    "Gaano ka-manageable ang mga regulatory hurdles para sa inyong teknolohiya?",
                    "Gaano ka-supportive ang policy environment para sa inyong commercialization?"
                ]
            },
            {
                "name": "Organizational at Team",
                "questions": [
                    "Gaano ka-experienced ang inyong team sa product development, sales, at scaling?",
                    "Gaano kalakas ang capacity ng inyong organisasyon na bumuo o suportahan ang bagong company?"
                ]
            },
            {
                "name": "Strategic Fit",
                "questions": [
                    "Gaano ka-aligned ang teknolohiyang ito sa core mission ng inyong organisasyon?",
                    "Gaano ka-valuable ang open-source release para sa pag-accelerate ng adoption?"
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

# DATABASE FUNCTIONS
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
            print(f"💾 PDF saved: {filename}")
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

# EMAIL MANAGER
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
            msg['Subject'] = f"📊 Assessment Report: {filename}"
            
            body = f"""
📊 TECHNOLOGY ASSESSMENT REPORT

📋 Assessment Details:
• Technology: {assessment_data.get('technology_title', 'N/A')}
• Assessment Type: {assessment_data.get('mode', 'N/A')}
• Language: {assessment_data.get('language', 'N/A')}
• Result: {assessment_data.get('level', assessment_data.get('recommended_pathway', 'N/A'))}
• Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📎 The complete assessment report is attached.

---
🏫 MMSU Technology Assessment Tool
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
            
            print(f"✅ Email sent successfully to {self.admin_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False

# HELPER FUNCTIONS
def get_client_ip_address():
    try:
        x_forwarded_for = request.environ.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.environ.get('REMOTE_ADDR')
    except Exception as e:
        return None

def get_mode_full_name(mode):
    mode_names = {
        "TRL": "Technology Readiness Level",
        "IRL": "Investment Readiness Level", 
        "MRL": "Market Readiness Level",
        "TCP": "Technology Commercialization Pathway"
    }
    return mode_names.get(mode.upper(), mode)

# ASSESSMENT FUNCTIONS
def assess_standard(data):
    mode = data["mode"]
    language = data["language"]
    answers = data["answers"]

    if mode.upper() == "TRL":
        questions = TRL_QUESTIONS[language.lower()]
    elif mode.upper() == "IRL":
        questions = IRL_QUESTIONS[language.lower()]
    elif mode.upper() == "MRL":
        questions = MRL_QUESTIONS[language.lower()]
    else:  
        return jsonify({"error": "Invalid assessment mode"}), 400

    level_achieved = -1
    for idx, lvl in enumerate(questions):
        if idx >= len(answers) or not all(answers[idx]):
            break
        level_achieved = lvl["level"]

    result = {
        "mode": mode,
        "mode_full": get_mode_full_name(mode),
        "level": max(0 if mode.upper() == "TRL" else 1, level_achieved),
        "technology_title": data["technology_title"],
        "description": data["description"],
        "answers": answers,
        "questions": questions,
        "explanation": generate_enhanced_explanation(level_achieved, mode, language, questions),
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(result)

def assess_tcp_enhanced(data):
    """Enhanced TCP assessment"""
    print("📊 Starting TCP Analysis...")
    
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
    
    # Generate detailed analysis
    detailed_analysis = generate_tcp_analysis(answers, tcp_data, pathway_scores, recommended_pathway, language)
    
    result = {
        "mode": "TCP",
        "mode_full": "Technology Commercialization Pathway (Enhanced)",
        "technology_title": technology_title,
        "description": technology_description,
        "answers": answers,
        "tcp_data": tcp_data,
        "pathway_scores": pathway_scores,
        "recommended_pathway": recommended_pathway,
        "explanation": generate_tcp_explanation(pathway_scores, recommended_pathway, detailed_analysis, language),
        "detailed_analysis": detailed_analysis,
        "timestamp": datetime.utcnow().isoformat(),
        "level": None,
        "questions": None,
        "enhanced": True
    }
    
    print("✅ TCP analysis completed!")
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

def generate_tcp_analysis(answers, tcp_data, pathway_scores, recommended_pathway, language):
    """Generate comprehensive TCP analysis"""
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
            "percentage": round(percentage, 1),
            "level": "High" if percentage >= 75 else "Medium" if percentage >= 50 else "Low"
        }
        answer_idx += len(dimension["questions"])
    
    # Generate comprehensive recommendations
    recommendations = generate_tcp_recommendations(dimension_scores, recommended_pathway, language)
    
    return {
        "dimension_scores": dimension_scores,
        "recommendations": recommendations,
        "overall_readiness": calculate_overall_readiness(dimension_scores),
        "confidence_score": calculate_confidence_score(pathway_scores, dimension_scores)
    }

def generate_tcp_recommendations(dimension_scores, recommended_pathway, language):
    """Generate detailed recommendations based on analysis"""
    recommendations = {
        "immediate_actions": [],
        "strategic_priorities": [],
        "success_factors": [],
        "risk_mitigation": []
    }
    
    weak_dimensions = [dim for dim, data in dimension_scores.items() if data["percentage"] < 50]
    strong_dimensions = [dim for dim, data in dimension_scores.items() if data["percentage"] >= 75]
    
    if language == "filipino":
        # Immediate actions for weak areas
        for dim in weak_dimensions[:2]:
            if "Technology" in dim:
                recommendations["immediate_actions"].append(f"🔧 Palakasin ang technology development para sa {dim}")
            elif "Market" in dim:
                recommendations["immediate_actions"].append(f"📊 Mag-conduct ng market research para sa {dim}")
            elif "Business" in dim:
                recommendations["immediate_actions"].append(f"💼 Mag-develop ng business capabilities para sa {dim}")
        
        # Strategic priorities
        recommendations["strategic_priorities"] = [
            f"🎯 Focus sa {recommended_pathway} pathway implementation",
            "📈 Build comprehensive commercialization strategy",
            "🤝 Establish key strategic partnerships",
            "💰 Secure adequate funding and resources"
        ]
        
        # Success factors
        recommendations["success_factors"] = [
            "💪 Strong team with complementary skills",
            "📊 Clear understanding ng market needs",
            "🔧 Robust technology development process",
            "💰 Adequate financial resources"
        ]
        
        # Risk mitigation
        recommendations["risk_mitigation"] = [
            "⚠️ Monitor market changes at competitive threats",
            "🛡️ Develop contingency plans para sa key risks",
            "📊 Establish performance monitoring systems",
            "🔄 Regular strategy review at adjustment"
        ]
    else:
        # Immediate actions for weak areas
        for dim in weak_dimensions[:2]:
            if "Technology" in dim:
                recommendations["immediate_actions"].append(f"🔧 Strengthen technology development capabilities in {dim}")
            elif "Market" in dim:
                recommendations["immediate_actions"].append(f"📊 Conduct comprehensive market research for {dim}")
            elif "Business" in dim:
                recommendations["immediate_actions"].append(f"💼 Develop business capabilities for {dim}")
        
        # Strategic priorities
        recommendations["strategic_priorities"] = [
            f"🎯 Focus on {recommended_pathway} pathway implementation",
            "📈 Build comprehensive commercialization strategy",
            "🤝 Establish key strategic partnerships and alliances",
            "💰 Secure adequate funding and resource commitments"
        ]
        
        # Success factors
        recommendations["success_factors"] = [
            "💪 Strong, experienced team with complementary skills",
            "📊 Clear understanding of market needs and customer requirements",
            "🔧 Robust technology development and validation process",
            "💰 Adequate financial resources and funding access"
        ]
        
        # Risk mitigation
        recommendations["risk_mitigation"] = [
            "⚠️ Monitor market changes and competitive threats continuously",
            "🛡️ Develop comprehensive contingency plans for key risks",
            "📊 Establish performance monitoring and tracking systems",
            "🔄 Regular strategy review and adjustment processes"
        ]
    
    return recommendations

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

def calculate_confidence_score(pathway_scores, dimension_scores):
    """Calculate confidence score for recommendation"""
    max_score = max(pathway_scores.values()) if pathway_scores else 0
    second_score = sorted(pathway_scores.values(), reverse=True)[1] if len(pathway_scores) > 1 else 0
    score_gap = max_score - second_score
    
    avg_dimension_score = sum(dim["percentage"] for dim in dimension_scores.values()) / len(dimension_scores) if dimension_scores else 0
    
    confidence = min(100, (score_gap * 10) + (avg_dimension_score * 0.5))
    return round(confidence, 1)

def generate_enhanced_explanation(level_achieved, mode, language, questions):
    """Generate enhanced explanation with detailed insights"""
    if language == "filipino":
        if level_achieved < (0 if mode == "TRL" else 1):
            start_level = 0 if mode == "TRL" else 1
            text = f"🔍 **Assessment Result**: Hindi pa naaabot ng inyong teknolohiya ang antas {start_level} ng {mode}.\n\n"
            text += f"**📊 Interpretation**: Ang teknolohiya ay nasa napakaunang yugto pa at kailangan ng substantial development.\n\n"
            text += f"**🚀 Next Steps**: Mag-focus sa fundamental research at basic validation activities."
        else:
            current_level = next((q for q in questions if q["level"] == level_achieved), None)
            if current_level:
                text = f"🎯 **Assessment Result**: Naabot ng inyong teknolohiya ang {mode} Level {level_achieved} - {current_level['title']}.\n\n"
                text += f"**📊 Interpretation**: Successfully na-complete ang requirements para sa level na ito.\n\n"
                
                # Find next level
                next_level = next((q for q in questions if q["level"] > level_achieved), None)
                if next_level:
                    text += f"**🎯 Next Target**: Para umusad sa Level {next_level['level']} ({next_level['title']}), focus sa:\n"
                    for req in next_level['checks'][:3]:
                        text += f"• {req}\n"
                else:
                    text += f"**🏆 Congratulations**: Nakamit na ang highest level! Focus sa continuous improvement."
            else:
                text = f"Naabot ng teknolohiya ang {mode} level {level_achieved}."
        
        return text
    else:
        start_level = 0 if mode == "TRL" else 1
        if level_achieved < start_level:
            text = f"🔍 **Assessment Result**: Your technology has not yet satisfied the basic requirements for {mode} level {start_level}.\n\n"
            text += f"**📊 Interpretation**: The technology is in very early stages requiring substantial development.\n\n"
            text += f"**🚀 Next Steps**: Focus on fundamental research and basic validation activities."
        else:
            current_level = next((q for q in questions if q["level"] == level_achieved), None)
            if current_level:
                text = f"🎯 **Assessment Result**: Your technology has achieved {mode} Level {level_achieved} - {current_level['title']}.\n\n"
                text += f"**📊 Interpretation**: Successfully completed requirements for this level.\n\n"
                
                # Find next level
                next_level = next((q for q in questions if q["level"] > level_achieved), None)
                if next_level:
                    text += f"**🎯 Next Target**: To advance to Level {next_level['level']} ({next_level['title']}), focus on:\n"
                    for req in next_level['checks'][:3]:
                        text += f"• {req}\n"
                else:
                    text += f"**🏆 Congratulations**: Achieved the highest level! Focus on continuous improvement."
            else:
                text = f"Your technology has achieved {mode} level {level_achieved}."
        
        return text

def generate_tcp_explanation(pathway_scores, recommended_pathway, detailed_analysis, language):
    """Generate enhanced TCP explanation"""
    confidence = detailed_analysis.get("confidence_score", 0)
    overall_readiness = detailed_analysis.get("overall_readiness", "Good")
    
    if language == "filipino":
        text = f"📊 **Enhanced Technology Commercialization Analysis**\n\n"
        text += f"Batay sa comprehensive assessment, ang **pinakarekomendadong pathway** para sa inyong teknolohiya ay ang **{recommended_pathway}** (confidence: {confidence}%).\n\n"
        text += f"**Overall Readiness:** {overall_readiness}\n\n"
        text += f"Ang analysis na ito ay nag-evaluate ng inyong teknolohiya sa six critical dimensions upang magbigay ng data-driven recommendation."
    else:
        text = f"📊 **Enhanced Technology Commercialization Analysis**\n\n"
        text += f"Based on comprehensive multi-dimensional assessment, the **most recommended commercialization pathway** for your technology is **{recommended_pathway}** (confidence: {confidence}%).\n\n"
        text += f"**Overall Readiness:** {overall_readiness}\n\n"
        text += f"This analysis evaluates your technology across six critical dimensions to provide data-driven recommendations for successful commercialization."
    
    return text

# PDF GENERATION
def create_enhanced_pdf(data):
    """Create enhanced PDF report"""
    buf = io.BytesIO()
    doc = SimpleDocumentTemplate(buf, pagesize=A4, topMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=16, textColor=colors.darkgreen, alignment=1, spaceAfter=6)
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=10, textColor=colors.darkblue, alignment=1, spaceAfter=12)
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], fontSize=12, textColor=colors.darkgreen)
    
    elements = []
    
    # Header
    elements.append(Paragraph("MARANO MARCOS STATE UNIVERSITY", title_style))
    elements.append(Paragraph("Innovation and Technology Support Office", subtitle_style))
    elements.append(Paragraph("📊 Enhanced Technology Assessment Tool", subtitle_style))
    elements.append(Spacer(1, 18))
    
    elements.append(Paragraph(f"📋 {data.get('mode_full', data['mode'])} Assessment Report", heading_style))
    elements.append(Spacer(1, 10))
    
    # Technology Information
    tech_info = [
        ["Technology Title:", data.get('technology_title', 'N/A')],
        ["Description:", data.get('description', 'N/A')],
        ["Assessment Date:", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')],
        ["Enhancement Level:", "📊 Comprehensive Analysis with Smart Recommendations"]
    ]
    
    if data['mode'] == 'TCP':
        tech_info.append(["Recommended Pathway:", data.get('recommended_pathway', 'N/A')])
        detailed_analysis = data.get('detailed_analysis', {})
        confidence = detailed_analysis.get('confidence_score', 0)
        tech_info.append(["Confidence Level:", f"{confidence}%"])
    else:
        tech_info.append(["Level Achieved:", str(data.get('level', 'N/A'))])
    
    tech_table = Table(tech_info, colWidths=[2*inch, 4*inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(tech_table)
    elements.append(Spacer(1, 16))
    
    # Assessment Summary
    elements.append(Paragraph("📊 Assessment Summary", heading_style))
    elements.append(Paragraph(data.get("explanation", "No explanation available."), styles["Normal"]))
    elements.append(Spacer(1, 14))
    
    # Enhanced Analysis Section
    if data.get('detailed_analysis'):
        analysis = data['detailed_analysis']
        
        elements.append(Paragraph("🔍 Detailed Analysis", heading_style))
        
        if 'dimension_scores' in analysis:
            elements.append(Paragraph("📋 Dimension Analysis:", styles["Heading3"]))
            for dim_name, dim_data in analysis['dimension_scores'].items():
                dim_text = f"• {dim_name}: {dim_data['percentage']}% ({dim_data['level']})"
                elements.append(Paragraph(dim_text, styles["Normal"]))
            elements.append(Spacer(1, 10))
        
        if 'recommendations' in analysis:
            recommendations = analysis['recommendations']
            elements.append(Paragraph("💡 Key Recommendations:", styles["Heading3"]))
            
            if 'immediate_actions' in recommendations:
                for action in recommendations['immediate_actions'][:3]:
                    elements.append(Paragraph(f"• {action}", styles["Normal"]))
            elements.append(Spacer(1, 10))
    
    # Footer
    elements.append(Spacer(1, 14))
    footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=1)
    elements.append(Paragraph("📊 Generated by MMSU Enhanced Technology Assessment Tool", footer_style))
    elements.append(Paragraph("Innovation and Technology Support Office • Comprehensive Analysis Report", footer_style))
    
    doc.build(elements)
    return buf

# Initialize components
init_database()
email_manager = EmailManager()

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
        print(f"📄 PDF Generation - Mode: {data.get('mode', 'Unknown')}")
        
        if not data or 'mode' not in data:
            return jsonify({"error": "Invalid data provided"}), 400
        
        # Generate PDF
        buf = create_enhanced_pdf(data)
        
        # Generate filename
        now = datetime.now()
        date_str = now.strftime('%m%d%y')
        tech_title = data.get('technology_title', 'Assessment').replace(' ', '_').replace('/', '_')
        filename = f"{date_str}_{tech_title}_Report.pdf"
        
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
        
        # Send email
        buf_for_email = io.BytesIO(buf.getvalue())
        email_manager.send_pdf_email(buf_for_email, filename, assessment_data)
        
        buf.seek(0)
        return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"❌ PDF Generation Error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"PDF generation failed: {e}"}), 500

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
