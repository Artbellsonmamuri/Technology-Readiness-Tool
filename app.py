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

# Complete TRL Questions Database (0-9) - keeping as is since they work well
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

# Complete IRL Questions Database (1-9) - keeping as is
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

# Market Readiness Level (MRL) Questions Database (1-9) - keeping as is
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

# IMPROVED TCP Questions Database - Fixed to make sense with Low/Medium/High ratings
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
                    "How significant are the regulatory hurdles for your technology?",
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
                "criteria": ["High technology readiness", "Strong internal resources", "Established market channels"],
                "best_for": "Organizations with strong internal capabilities and established market presence",
                "timeline": "12-24 months to market",
                "investment_required": "Medium to High",
                "risk_level": "Medium"
            },
            {
                "name": "Licensing",
                "description": "Licensing the technology to other companies for commercialization",
                "criteria": ["Strong IP protection", "Market demand", "Limited internal resources"],
                "best_for": "Technologies with strong IP and limited internal commercialization resources",
                "timeline": "6-18 months to licensing deal",
                "investment_required": "Low to Medium",
                "risk_level": "Low to Medium"
            },
            {
                "name": "Startup/Spin-out",
                "description": "Creating a new company to commercialize the technology",
                "criteria": ["High innovation potential", "Entrepreneurial team", "Growth market"],
                "best_for": "Breakthrough technologies with dedicated entrepreneurial teams",
                "timeline": "18-36 months to market",
                "investment_required": "High",
                "risk_level": "High"
            },
            {
                "name": "Assignment",
                "description": "Selling or transferring technology rights to another organization",
                "criteria": ["Valuable IP", "Low internal interest", "Better suited for others"],
                "best_for": "Technologies outside core mission with clear value to others",
                "timeline": "3-12 months to transaction",
                "investment_required": "Low",
                "risk_level": "Low"
            },
            {
                "name": "Research Collaboration",
                "description": "Partnering with other organizations for further development",
                "criteria": ["Early-stage technology", "Need for development", "Research partnerships"],
                "best_for": "Early-stage technologies requiring additional development resources",
                "timeline": "12-36 months to commercial readiness",
                "investment_required": "Medium",
                "risk_level": "Medium"
            },
            {
                "name": "Open Source",
                "description": "Releasing technology as open source for broad adoption",
                "criteria": ["Broad adoption potential", "Service-based value", "Community building"],
                "best_for": "Platform technologies that benefit from community development",
                "timeline": "6-12 months to community adoption",
                "investment_required": "Low to Medium",
                "risk_level": "Low"
            },
            {
                "name": "Government Procurement",
                "description": "Targeting government agencies as primary customers",
                "criteria": ["Public sector relevance", "Regulatory compliance", "Government needs"],
                "best_for": "Technologies addressing government or public sector needs",
                "timeline": "12-36 months to procurement",
                "investment_required": "Medium",
                "risk_level": "Medium"
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
                    "Gaano ka-significant ang mga regulatory hurdles para sa inyong teknolohiya?",
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
                "criteria": ["Mataas na technology readiness", "Malakas na internal resources", "Established market channels"],
                "best_for": "Mga organisasyon na may malakas na internal capabilities at established market presence",
                "timeline": "12-24 buwan papunta sa market",
                "investment_required": "Medium hanggang High",
                "risk_level": "Medium"
            },
            {
                "name": "Licensing",
                "description": "Pag-license ng teknolohiya sa ibang companies para sa commercialization",
                "criteria": ["Malakas na IP protection", "Market demand", "Limited internal resources"],
                "best_for": "Mga teknolohiya na may malakas na IP at limited internal commercialization resources",
                "timeline": "6-18 buwan para sa licensing deal",
                "investment_required": "Low hanggang Medium",
                "risk_level": "Low hanggang Medium"
            },
            {
                "name": "Startup/Spin-out",
                "description": "Paggawa ng bagong company para i-commercialize ang teknolohiya",
                "criteria": ["Mataas na innovation potential", "Entrepreneurial team", "Growth market"],
                "best_for": "Breakthrough technologies na may dedicated entrepreneurial teams",
                "timeline": "18-36 buwan papunta sa market",
                "investment_required": "High",
                "risk_level": "High"
            },
            {
                "name": "Assignment",
                "description": "Pagbenta o paglilipat ng technology rights sa ibang organisasyon",
                "criteria": ["Valuable IP", "Mababang internal interest", "Mas bagay sa iba"],
                "best_for": "Mga teknolohiya na hindi core mission na may clear value sa iba",
                "timeline": "3-12 buwan para sa transaction",
                "investment_required": "Low",
                "risk_level": "Low"
            },
            {
                "name": "Research Collaboration",
                "description": "Pakikipag-partner sa ibang organisasyon para sa further development",
                "criteria": ["Early-stage technology", "Pangangailangan ng development", "Research partnerships"],
                "best_for": "Early-stage technologies na nangangailangan ng additional development resources",
                "timeline": "12-36 buwan para sa commercial readiness",
                "investment_required": "Medium",
                "risk_level": "Medium"
            },
            {
                "name": "Open Source",
                "description": "Pag-release ng teknolohiya bilang open source para sa broad adoption",
                "criteria": ["Broad adoption potential", "Service-based value", "Community building"],
                "best_for": "Platform technologies na nakikinabang sa community development",
                "timeline": "6-12 buwan para sa community adoption",
                "investment_required": "Low hanggang Medium",
                "risk_level": "Low"
            },
            {
                "name": "Government Procurement",
                "description": "Pag-target sa government agencies bilang primary customers",
                "criteria": ["Public sector relevance", "Regulatory compliance", "Government needs"],
                "best_for": "Mga teknolohiya na tumutugon sa government o public sector needs",
                "timeline": "12-36 buwan para sa procurement",
                "investment_required": "Medium",
                "risk_level": "Medium"
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
            msg['Subject'] = f"📊 Enhanced Assessment Report: {filename}"
            
            body = f"""
📊 ENHANCED TECHNOLOGY ASSESSMENT REPORT

📋 Assessment Details:
• Technology: {assessment_data.get('technology_title', 'N/A')}
• Assessment Type: {assessment_data.get('mode', 'N/A')}
• Language: {assessment_data.get('language', 'N/A')}
• Result: {assessment_data.get('level', assessment_data.get('recommended_pathway', 'N/A'))}
• Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Enhanced with: Comprehensive analysis and recommendations

📎 The complete enhanced assessment report is attached.

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

# Helper functions (keeping existing ones)
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
                # Save standard assessment answers
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

# ALL ROUTES
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
        empty_stats = {
            'total_assessments': 0,
            'assessments_by_type': [],
            'completion_rate': 0
        }
        return render_template("overview.html", stats=empty_stats)

@app.route("/admin/statistics")
def admin_statistics():
    try:
        stats = get_statistics()
        return render_template("admin_statistics.html", stats=stats)
    except Exception as e:
        print(f"Error in admin_statistics route: {e}")
        empty_stats = {
            'total_assessments': 0,
            'assessments_by_type': [],
            'completion_rate': 0
        }
        return render_template("admin_statistics.html", stats=empty_stats)

@app.route("/admin/pdfs")
def admin_pdfs():
    """Admin page to view all collected PDFs"""
    try:
        pdfs = get_all_pdfs()
        admin_email = os.getenv('ADMIN_EMAIL')
        return render_template("admin_pdfs.html", pdfs=pdfs, admin_email=admin_email)
    except Exception as e:
        print(f"Error in admin_pdfs route: {e}")
        return render_template("admin_pdfs.html", pdfs=[], admin_email=None)

@app.route("/admin/pdf/<int:assessment_id>")
def download_pdf(assessment_id):
    """Download specific PDF by assessment ID"""
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

    # Generate enhanced detailed analysis
    detailed_analysis = generate_standard_detailed_analysis(answers, questions, level_achieved, mode, language)

    result = {
        "mode": mode,
        "mode_full": get_mode_full_name(mode),
        "level": max(0 if mode.upper() == "TRL" else 1, level_achieved),
        "technology_title": data["technology_title"],
        "description": data["description"],
        "answers": answers,
        "questions": questions,
        "explanation": generate_enhanced_explanation(level_achieved, mode, language, questions),
        "detailed_analysis": detailed_analysis,
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(result)

def get_mode_full_name(mode):
    mode_names = {
        "TRL": "Technology Readiness Level",
        "IRL": "Investment Readiness Level", 
        "MRL": "Market Readiness Level",
        "TCP": "Technology Commercialization Pathway"
    }
    return mode_names.get(mode.upper(), mode)

def generate_standard_detailed_analysis(answers, questions, level_achieved, mode, language):
    """Generate detailed analysis for standard assessments (TRL/IRL/MRL)"""
    analysis = {
        "input_summary": generate_standard_input_summary(answers, questions),
        "level_breakdown": generate_level_breakdown(answers, questions),
        "strengths": [],
        "areas_for_improvement": [],
        "next_steps": [],
        "recommendations": generate_mode_specific_recommendations(level_achieved, mode, language),
        "success_factors": generate_success_factors(mode, language),
        "timeline_estimate": generate_timeline_estimate(level_achieved, mode),
        "risk_assessment": generate_standard_risk_assessment(level_achieved, mode, language)
    }
    
    # Identify strengths and areas for improvement
    for idx, level in enumerate(questions):
        if idx < len(answers):
            level_answers = answers[idx]
            completed_count = sum(1 for ans in level_answers if ans)
            total_count = len(level_answers)
            completion_rate = completed_count / total_count if total_count > 0 else 0
            
            if completion_rate >= 0.8:
                analysis["strengths"].append(level["title"])
            elif completion_rate < 0.5:
                analysis["areas_for_improvement"].append(level["title"])
    
    # Generate next steps
    analysis["next_steps"] = generate_next_steps(level_achieved, mode, questions, language)
    
    return analysis

def generate_standard_input_summary(answers, questions):
    """Generate input summary for standard assessments"""
    total_questions = sum(len(level_answers) for level_answers in answers)
    total_yes = sum(sum(level_answers) for level_answers in answers)
    
    level_summaries = []
    for idx, (level_answers, question_level) in enumerate(zip(answers, questions)):
        yes_count = sum(level_answers)
        total_count = len(level_answers)
        completion_rate = (yes_count / total_count * 100) if total_count > 0 else 0
        
        level_summaries.append({
            "level": question_level["level"],
            "title": question_level["title"],
            "completed": yes_count,
            "total": total_count,
            "percentage": round(completion_rate, 1),
            "status": "Complete" if completion_rate == 100 else "Partial" if completion_rate > 0 else "Not Started"
        })
    
    return {
        "total_questions": total_questions,
        "total_completed": total_yes,
        "overall_completion_rate": round((total_yes / total_questions * 100) if total_questions > 0 else 0, 1),
        "level_summaries": level_summaries
    }

def generate_level_breakdown(answers, questions):
    """Generate detailed breakdown by level"""
    breakdown = []
    
    for idx, (level_answers, question_level) in enumerate(zip(answers, questions)):
        yes_count = sum(level_answers)
        total_count = len(level_answers)
        completion_rate = (yes_count / total_count * 100) if total_count > 0 else 0
        
        question_details = []
        for q_idx, (answer, question_text) in enumerate(zip(level_answers, question_level["checks"])):
            question_details.append({
                "question": question_text,
                "answer": "Yes" if answer else "No",
                "status": "✅" if answer else "❌"
            })
        
        breakdown.append({
            "level": question_level["level"],
            "title": question_level["title"],
            "completion_rate": round(completion_rate, 1),
            "status": "Complete" if completion_rate == 100 else "Partial" if completion_rate > 0 else "Not Started",
            "questions": question_details
        })
    
    return breakdown

def generate_mode_specific_recommendations(level_achieved, mode, language):
    """Generate specific recommendations based on mode and level"""
    recommendations = []
    
    if language == "filipino":
        if mode == "TRL":
            if level_achieved < 3:
                recommendations = [
                    "Mag-focus sa fundamental research at proof-of-concept development",
                    "Mag-establish ng clear technical requirements at specifications", 
                    "Mag-conduct ng literature review at prior art analysis",
                    "Mag-develop ng theoretical models at simulations"
                ]
            elif level_achieved < 6:
                recommendations = [
                    "Mag-build ng prototypes para sa laboratory testing",
                    "Mag-validate ng performance metrics at benchmarks",
                    "Mag-conduct ng environmental testing",
                    "Mag-prepare para sa relevant environment validation"
                ]
            else:
                recommendations = [
                    "Mag-prepare para sa operational environment deployment",
                    "Mag-develop ng manufacturing at scaling plans",
                    "Mag-establish ng quality assurance systems",
                    "Mag-prepare para sa commercial launch"
                ]
        elif mode == "IRL":
            if level_achieved < 3:
                recommendations = [
                    "Mag-develop ng comprehensive business plan",
                    "Mag-conduct ng market research at validation",
                    "Mag-establish ng founding team",
                    "Mag-secure ng initial funding sources"
                ]
            elif level_achieved < 6:
                recommendations = [
                    "Mag-build ng MVP at mag-test sa market",
                    "Mag-establish ng customer acquisition strategies",
                    "Mag-develop ng revenue models",
                    "Mag-secure ng growth funding"
                ]
            else:
                recommendations = [
                    "Mag-focus sa scaling operations",
                    "Mag-establish ng strategic partnerships",
                    "Mag-expand sa new markets",
                    "Mag-prepare para sa exit strategies"
                ]
        elif mode == "MRL":
            if level_achieved < 3:
                recommendations = [
                    "Mag-conduct ng comprehensive market research",
                    "Mag-identify ng target customer segments",
                    "Mag-validate ng market demand",
                    "Mag-analyze ng competitive landscape"
                ]
            elif level_achieved < 6:
                recommendations = [
                    "Mag-develop ng go-to-market strategy",
                    "Mag-establish ng distribution channels",
                    "Mag-build ng marketing capabilities",
                    "Mag-test ng pricing strategies"
                ]
            else:
                recommendations = [
                    "Mag-execute ng market launch plan",
                    "Mag-monitor ng market performance",
                    "Mag-optimize ng customer acquisition",
                    "Mag-scale ng market operations"
                ]
    else:
        if mode == "TRL":
            if level_achieved < 3:
                recommendations = [
                    "Focus on fundamental research and proof-of-concept development",
                    "Establish clear technical requirements and specifications",
                    "Conduct comprehensive literature review and prior art analysis",
                    "Develop theoretical models and simulations"
                ]
            elif level_achieved < 6:
                recommendations = [
                    "Build prototypes for rigorous laboratory testing",
                    "Validate performance metrics against established benchmarks",
                    "Conduct environmental testing under relevant conditions",
                    "Prepare for relevant environment validation"
                ]
            else:
                recommendations = [
                    "Prepare for operational environment deployment",
                    "Develop manufacturing and scaling plans",
                    "Establish quality assurance and control systems",
                    "Prepare for commercial launch and market entry"
                ]
        elif mode == "IRL":
            if level_achieved < 3:
                recommendations = [
                    "Develop comprehensive business plan with financial projections",
                    "Conduct thorough market research and validation",
                    "Establish experienced founding team with complementary skills",
                    "Secure initial funding sources and investor relationships"
                ]
            elif level_achieved < 6:
                recommendations = [
                    "Build and test minimum viable product (MVP) with target customers",
                    "Establish proven customer acquisition and retention strategies",
                    "Develop sustainable revenue models and pricing strategies",
                    "Secure growth funding for scaling operations"
                ]
            else:
                recommendations = [
                    "Focus on scaling operations and expanding market reach",
                    "Establish strategic partnerships and alliances",
                    "Expand into new markets and customer segments",
                    "Prepare for potential exit strategies or IPO"
                ]
        elif mode == "MRL":
            if level_achieved < 3:
                recommendations = [
                    "Conduct comprehensive market research and analysis",
                    "Identify and characterize target customer segments",
                    "Validate market demand through customer discovery",
                    "Analyze competitive landscape and positioning opportunities"
                ]
            elif level_achieved < 6:
                recommendations = [
                    "Develop comprehensive go-to-market strategy",
                    "Establish distribution channels and sales partnerships",
                    "Build marketing capabilities and brand awareness",
                    "Test and optimize pricing strategies"
                ]
            else:
                recommendations = [
                    "Execute market launch plan with defined milestones",
                    "Monitor market performance and customer feedback",
                    "Optimize customer acquisition and retention processes",
                    "Scale market operations for sustainable growth"
                ]
    
    return recommendations

def generate_success_factors(mode, language):
    """Generate critical success factors for each mode"""
    success_factors = []
    
    if language == "filipino":
        if mode == "TRL":
            success_factors = [
                "Malakas na technical expertise at research capabilities",
                "Adequate funding para sa R&D activities",
                "Access sa specialized equipment at facilities",
                "Collaboration sa academic at industry partners",
                "Clear technical milestones at success metrics"
            ]
        elif mode == "IRL":
            success_factors = [
                "Experienced management team na may business acumen",
                "Clear market opportunity at customer validation",
                "Sustainable business model at revenue streams",
                "Access sa funding at investment opportunities",
                "Strong execution capabilities at operational excellence"
            ]
        elif mode == "MRL":
            success_factors = [
                "Deep understanding ng target market at customers",
                "Strong competitive positioning at differentiation",
                "Effective marketing at sales capabilities",
                "Established distribution channels at partnerships",
                "Continuous market monitoring at adaptation"
            ]
    else:
        if mode == "TRL":
            success_factors = [
                "Strong technical expertise and research capabilities",
                "Adequate funding for sustained R&D activities",
                "Access to specialized equipment and testing facilities",
                "Collaboration with academic and industry partners",
                "Clear technical milestones and success metrics"
            ]
        elif mode == "IRL":
            success_factors = [
                "Experienced management team with proven business acumen",
                "Clear market opportunity with validated customer demand",
                "Sustainable business model with multiple revenue streams",
                "Access to funding and investment opportunities",
                "Strong execution capabilities and operational excellence"
            ]
        elif mode == "MRL":
            success_factors = [
                "Deep understanding of target market and customer needs",
                "Strong competitive positioning and clear differentiation",
                "Effective marketing and sales capabilities",
                "Established distribution channels and strategic partnerships",
                "Continuous market monitoring and adaptive strategy"
            ]
    
    return success_factors

def generate_timeline_estimate(level_achieved, mode):
    """Generate realistic timeline estimates based on current level"""
    timelines = {}
    
    if mode == "TRL":
        if level_achieved < 3:
            timelines = {
                "next_level": "6-12 months",
                "commercial_readiness": "3-5 years",
                "full_deployment": "5-7 years"
            }
        elif level_achieved < 6:
            timelines = {
                "next_level": "12-18 months", 
                "commercial_readiness": "2-3 years",
                "full_deployment": "3-4 years"
            }
        else:
            timelines = {
                "next_level": "6-12 months",
                "commercial_readiness": "12-18 months",
                "full_deployment": "18-24 months"
            }
    elif mode == "IRL":
        if level_achieved < 3:
            timelines = {
                "next_level": "3-6 months",
                "investment_ready": "12-18 months",
                "commercial_launch": "18-24 months"
            }
        elif level_achieved < 6:
            timelines = {
                "next_level": "6-12 months",
                "investment_ready": "12-18 months", 
                "commercial_launch": "18-24 months"
            }
        else:
            timelines = {
                "next_level": "6-9 months",
                "investment_ready": "Already achieved",
                "scaling_phase": "12-18 months"
            }
    elif mode == "MRL":
        if level_achieved < 3:
            timelines = {
                "next_level": "3-6 months",
                "market_ready": "12-18 months",
                "full_adoption": "24-36 months"
            }
        elif level_achieved < 6:
            timelines = {
                "next_level": "6-9 months",
                "market_ready": "12-15 months",
                "full_adoption": "18-24 months"
            }
        else:
            timelines = {
                "next_level": "3-6 months",
                "market_ready": "6-9 months",
                "full_adoption": "12-18 months"
            }
    
    return timelines

def generate_standard_risk_assessment(level_achieved, mode, language):
    """Generate risk assessment for standard modes"""
    risks = {
        "high_risks": [],
        "medium_risks": [],
        "low_risks": [],
        "mitigation_strategies": []
    }
    
    if language == "filipino":
        if mode == "TRL":
            if level_achieved < 3:
                risks["high_risks"] = ["Technical feasibility hindi pa proven", "Limited funding para sa R&D"]
                risks["medium_risks"] = ["Competition sa research area", "IP protection challenges"]
                risks["mitigation_strategies"] = [
                    "Mag-conduct ng systematic technical validation",
                    "Mag-secure ng multiple funding sources",
                    "Mag-establish ng IP protection strategy"
                ]
            elif level_achieved < 6:
                risks["high_risks"] = ["Scaling challenges", "Manufacturing feasibility"]
                risks["medium_risks"] = ["Market acceptance", "Regulatory approvals"]
                risks["mitigation_strategies"] = [
                    "Mag-develop ng detailed scaling plan",
                    "Mag-engage sa early customer validation",
                    "Mag-work closely sa regulatory bodies"
                ]
            else:
                risks["high_risks"] = ["Market competition", "Commercial viability"]
                risks["medium_risks"] = ["Technology adoption rate", "Supply chain risks"]
                risks["mitigation_strategies"] = [
                    "Mag-establish ng strong market position",
                    "Mag-develop ng robust supply chain",
                    "Mag-monitor ng technology trends"
                ]
    else:
        if mode == "TRL":
            if level_achieved < 3:
                risks["high_risks"] = ["Technical feasibility not yet proven", "Limited funding for sustained R&D"]
                risks["medium_risks"] = ["Competition in research area", "IP protection challenges"]
                risks["mitigation_strategies"] = [
                    "Conduct systematic technical validation studies",
                    "Secure multiple funding sources and partnerships",
                    "Establish comprehensive IP protection strategy"
                ]
            elif level_achieved < 6:
                risks["high_risks"] = ["Technology scaling challenges", "Manufacturing feasibility concerns"]
                risks["medium_risks"] = ["Market acceptance uncertainty", "Regulatory approval delays"]
                risks["mitigation_strategies"] = [
                    "Develop detailed scaling and manufacturing plan",
                    "Engage in early customer validation activities",
                    "Work closely with regulatory bodies for compliance"
                ]
            else:
                risks["high_risks"] = ["Intense market competition", "Commercial viability pressures"]
                risks["medium_risks"] = ["Technology adoption rate", "Supply chain disruptions"]
                risks["mitigation_strategies"] = [
                    "Establish strong competitive market position", 
                    "Develop robust and diversified supply chain",
                    "Continuously monitor technology and market trends"
                ]
        elif mode == "IRL":
            if level_achieved < 3:
                risks["high_risks"] = ["Market validation uncertainty", "Team capability gaps"]
                risks["medium_risks"] = ["Funding accessibility", "Business model viability"]
                risks["mitigation_strategies"] = [
                    "Conduct thorough market research and validation",
                    "Build experienced team with complementary skills",
                    "Develop multiple revenue stream opportunities"
                ]
            elif level_achieved < 6:
                risks["high_risks"] = ["Customer acquisition challenges", "Competitive pressure"]
                risks["medium_risks"] = ["Scaling operational complexity", "Cash flow management"]
                risks["mitigation_strategies"] = [
                    "Implement proven customer acquisition strategies",
                    "Establish strong competitive differentiation",
                    "Maintain adequate cash flow and working capital"
                ]
            else:
                risks["high_risks"] = ["Market saturation", "Scaling execution risks"]
                risks["medium_risks"] = ["Technology disruption", "Talent acquisition"]
                risks["mitigation_strategies"] = [
                    "Diversify into new markets and customer segments",
                    "Invest in continuous innovation and R&D",
                    "Build strong organizational capabilities"
                ]
        elif mode == "MRL":
            if level_achieved < 3:
                risks["high_risks"] = ["Market need not validated", "Customer segment unclear"]
                risks["medium_risks"] = ["Competitive landscape uncertainty", "Pricing strategy risks"]
                risks["mitigation_strategies"] = [
                    "Conduct extensive customer discovery and validation",
                    "Perform comprehensive competitive analysis",
                    "Test multiple pricing and positioning strategies"
                ]
            elif level_achieved < 6:
                risks["high_risks"] = ["Go-to-market execution challenges", "Channel partnership risks"]
                risks["medium_risks"] = ["Brand recognition barriers", "Customer acquisition costs"]
                risks["mitigation_strategies"] = [
                    "Develop comprehensive go-to-market plan with milestones",
                    "Establish strategic channel partnerships",
                    "Invest in brand building and marketing capabilities"
                ]
            else:
                risks["high_risks"] = ["Market penetration limitations", "Competitive response"]
                risks["medium_risks"] = ["Customer retention challenges", "Market evolution"]
                risks["mitigation_strategies"] = [
                    "Implement customer retention and loyalty programs",
                    "Continuously monitor and adapt to market changes",
                    "Build sustainable competitive advantages"
                ]
    
    return risks

def generate_next_steps(level_achieved, mode, questions, language):
    """Generate specific next steps based on current level"""
    next_steps = []
    
    # Find the next level to work on
    next_level_idx = None
    for idx, level in enumerate(questions):
        if level["level"] > level_achieved:
            next_level_idx = idx
            break
    
    if next_level_idx is not None:
        next_level = questions[next_level_idx]
        
        if language == "filipino":
            next_steps = [
                f"Mag-focus sa {next_level['title']} (Level {next_level['level']})",
                "Mag-address ng mga requirements sa susunod na level:",
            ]
            
            # Add specific requirements from next level
            for requirement in next_level["checks"][:3]:  # Limit to first 3
                next_steps.append(f"• {requirement}")
                
        else:
            next_steps = [
                f"Focus on achieving {next_level['title']} (Level {next_level['level']})",
                "Address the following requirements for the next level:",
            ]
            
            # Add specific requirements from next level
            for requirement in next_level["checks"][:3]:  # Limit to first 3
                next_steps.append(f"• {requirement}")
    else:
        if language == "filipino":
            next_steps = [
                "Nakamit na ang pinakamataas na level!",
                "Mag-focus sa continuous improvement at maintenance",
                "Mag-monitor ng emerging technologies at market changes"
            ]
        else:
            next_steps = [
                "Highest level achieved! Focus on continuous improvement and maintenance",
                "Monitor emerging technologies and market changes",
                "Consider expansion into new applications or markets"
            ]
    
    return next_steps

def generate_enhanced_explanation(level_achieved, mode, language, questions):
    """Generate enhanced explanation with more detail"""
    if language == "filipino":
        if level_achieved < (0 if mode == "TRL" else 1):
            start_level = 0 if mode == "TRL" else 1
            text = f"🔍 **Assessment Result**: Hindi pa naaabot ng inyong teknolohiya ang antas {start_level} ng {mode}.\n\n"
            text += f"**Kahulugan**: Ang teknolohiya ay nasa napakaunang yugto pa lamang at kailangan ng malawakang development bago maabot ang basic requirements.\n\n"
            text += f"**Mga Hakbang**: Mag-focus sa fundamental research, proof-of-concept development, at basic validation activities."
        else:
            current_level = next((q for q in questions if q["level"] == level_achieved), None)
            if current_level:
                text = f"🎯 **Assessment Result**: Naabot ng inyong teknolohiya ang {mode} antas {level_achieved} - {current_level['title']}.\n\n"
                text += f"**Kahulugan**: Ang teknolohiya ay successfully na-complete ang mga requirements para sa level na ito, na nagpapakita ng {current_level['title'].lower()}.\n\n"
                
                # Find next level
                next_level = next((q for q in questions if q["level"] > level_achieved), None)
                if next_level:
                    text += f"**Susunod na Target**: Para umusad sa Level {next_level['level']} ({next_level['title']}), kailangan ninyo ng mga sumusunod:\n"
                    for req in next_level['checks'][:3]:
                        text += f"• {req}\n"
                else:
                    text += f"**Congratulations**: Nakamit ninyo na ang pinakamataas na level! Focus na lang sa continuous improvement at innovation."
            else:
                text = f"Naabot ng inyong teknolohiya ang {mode} level {level_achieved}."
        
        return text
    else:
        start_level = 0 if mode == "TRL" else 1
        if level_achieved < start_level:
            text = f"🔍 **Assessment Result**: Your technology has not yet satisfied the basic requirements for {mode} level {start_level}.\n\n"
            text += f"**Interpretation**: The technology is in very early stages and requires substantial development before meeting basic requirements.\n\n"
            text += f"**Immediate Actions**: Focus on fundamental research, proof-of-concept development, and basic validation activities."
        else:
            current_level = next((q for q in questions if q["level"] == level_achieved), None)
            if current_level:
                text = f"🎯 **Assessment Result**: Your technology has achieved {mode} Level {level_achieved} - {current_level['title']}.\n\n"
                text += f"**Interpretation**: The technology has successfully completed the requirements for this level, demonstrating {current_level['title'].lower()}.\n\n"
                
                # Find next level
                next_level = next((q for q in questions if q["level"] > level_achieved), None)
                if next_level:
                    text += f"**Next Target**: To advance to Level {next_level['level']} ({next_level['title']}), you need to address:\n"
                    for req in next_level['checks'][:3]:
                        text += f"• {req}\n"
                else:
                    text += f"**Congratulations**: You have achieved the highest level! Focus on continuous improvement and innovation."
            else:
                text = f"Your technology has achieved {mode} level {level_achieved}."
        
        return text

# Enhanced TCP Assessment Function (No AI Dependencies)
def assess_tcp_enhanced(data):
    """Enhanced TCP assessment with comprehensive analysis (No AI)"""
    print("📊 Starting Enhanced TCP Analysis...")
    
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
    
    # Generate comprehensive analysis (No AI)
    detailed_analysis = generate_comprehensive_tcp_analysis(
        answers, tcp_data, pathway_scores, recommended_pathway,
        technology_title, technology_description, language
    )
    
    result = {
        "mode": "TCP",
        "mode_full": "Technology Commercialization Pathway (Enhanced)",
        "technology_title": technology_title,
        "description": technology_description,
        "answers": answers,
        "tcp_data": tcp_data,
        "pathway_scores": pathway_scores,
        "recommended_pathway": recommended_pathway,
        "explanation": generate_tcp_enhanced_explanation(pathway_scores, recommended_pathway, detailed_analysis, language),
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
    
    # Enhanced scoring logic
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
    """Generate comprehensive analysis (No AI Dependencies)"""
    print("📊 Generating comprehensive TCP analysis...")
    
    # Basic analysis components
    input_summary = generate_tcp_input_summary(answers, tcp_data)
    dimension_scores = generate_tcp_dimension_scores(answers, tcp_data)
    sorted_pathways = sorted(pathway_scores.items(), key=lambda x: x[1], reverse=True)
    top_pathways = sorted_pathways[:3]
    second_alternative = sorted_pathways[1] if len(sorted_pathways) > 1 else None
    
    # Enhanced analysis components
    strengths_weaknesses = analyze_strengths_weaknesses(dimension_scores, language)
    success_strategies = generate_tcp_success_strategies(dimension_scores, recommended_pathway, language)
    risk_assessment = generate_tcp_risk_assessment(dimension_scores, recommended_pathway, language)
    implementation_plan = generate_tcp_implementation_plan(recommended_pathway, dimension_scores, language)
    financial_considerations = generate_tcp_financial_analysis(recommended_pathway, dimension_scores, language)
    partnership_recommendations = generate_tcp_partnership_recommendations(recommended_pathway, dimension_scores, language)
    
    analysis = {
        # Basic analysis
        "input_summary": input_summary,
        "dimension_scores": dimension_scores,
        "top_pathways": top_pathways,
        "recommended_pathway": recommended_pathway,
        "second_alternative": second_alternative,
        "overall_readiness": calculate_tcp_overall_readiness(dimension_scores),
        "confidence_score": calculate_tcp_confidence_score(pathway_scores, dimension_scores),
        
        # Enhanced analysis
        "strengths_weaknesses": strengths_weaknesses,
        "success_strategies": success_strategies,
        "risk_assessment": risk_assessment,
        "implementation_plan": implementation_plan,
        "financial_considerations": financial_considerations,
        "partnership_recommendations": partnership_recommendations,
        "detailed_pathway_analysis": generate_detailed_pathway_analysis(tcp_data, recommended_pathway, language),
        
        # Metadata
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "enhanced": True,
        "methodology": "Comprehensive Multi-Dimensional Analysis"
    }
    
    return analysis

def generate_tcp_input_summary(answers, tcp_data):
    """Generate comprehensive input summary for TCP"""
    total_questions = len(answers)
    average_score = sum(answers) / len(answers) if answers else 0
    
    dimension_breakdown = []
    answer_idx = 0
    
    for dimension in tcp_data["dimensions"]:
        dim_answers = answers[answer_idx:answer_idx + len(dimension["questions"])]
        dim_avg = sum(dim_answers) / len(dim_answers) if dim_answers else 0
        dim_total = sum(dim_answers)
        dim_max = len(dim_answers) * 3
        
        strength_level = "High" if dim_avg >= 2.5 else "Medium" if dim_avg >= 2.0 else "Low"
        
        dimension_breakdown.append({
            "dimension": dimension["name"],
            "average_score": round(dim_avg, 2),
            "total_score": dim_total,
            "max_score": dim_max,
            "percentage": round((dim_total / dim_max * 100), 1),
            "strength_level": strength_level,
            "individual_scores": dim_answers
        })
        answer_idx += len(dimension["questions"])
    
    return {
        "total_questions": total_questions,
        "average_score": round(average_score, 2),
        "total_possible": total_questions * 3,
        "overall_percentage": round((sum(answers) / (total_questions * 3) * 100), 1),
        "dimension_breakdown": dimension_breakdown,
        "assessment_completeness": "Complete"
    }

def generate_tcp_dimension_scores(answers, tcp_data):
    """Generate detailed dimension score analysis"""
    dimension_scores = {}
    answer_idx = 0
    
    for dimension in tcp_data["dimensions"]:
        dim_answers = answers[answer_idx:answer_idx + len(dimension["questions"])]
        dim_score = sum(dim_answers)
        max_score = len(dimension["questions"]) * 3
        percentage = (dim_score / max_score) * 100
        
        # Detailed analysis
        question_analysis = []
        for i, (answer, question) in enumerate(zip(dim_answers, dimension["questions"])):
            question_analysis.append({
                "question": question,
                "score": answer,
                "rating": "High" if answer == 3 else "Medium" if answer == 2 else "Low"
            })
        
        dimension_scores[dimension["name"]] = {
            "score": dim_score,
            "max_score": max_score,
            "percentage": round(percentage, 1),
            "level": "High" if percentage >= 75 else "Medium" if percentage >= 50 else "Low",
            "individual_answers": dim_answers,
            "question_analysis": question_analysis,
            "improvement_potential": max_score - dim_score
        }
        answer_idx += len(dimension["questions"])
    
    return dimension_scores

def analyze_strengths_weaknesses(dimension_scores, language):
    """Analyze strengths and weaknesses from dimension scores"""
    strengths = []
    weaknesses = []
    opportunities = []
    
    for dim_name, dim_data in dimension_scores.items():
        percentage = dim_data["percentage"]
        
        if percentage >= 75:
            strengths.append({
                "dimension": dim_name,
                "score": percentage,
                "note": "Excellent capability in this area"
            })
        elif percentage < 50:
            weaknesses.append({
                "dimension": dim_name,
                "score": percentage,
                "improvement_needed": dim_data["improvement_potential"],
                "priority": "High" if percentage < 30 else "Medium"
            })
        elif percentage >= 50 and percentage < 75:
            opportunities.append({
                "dimension": dim_name,
                "score": percentage,
                "potential": dim_data["improvement_potential"],
                "note": "Good foundation with room for improvement"
            })
    
    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "opportunities": opportunities,
        "overall_assessment": generate_overall_swot_assessment(strengths, weaknesses, opportunities, language)
    }

def generate_overall_swot_assessment(strengths, weaknesses, opportunities, language):
    """Generate overall SWOT assessment"""
    if language == "filipino":
        if len(strengths) >= 3:
            return "Malakas na overall readiness na may mga established capabilities"
        elif len(weaknesses) >= 3:
            return "Kailangan ng significant improvement sa maraming areas"
        elif len(opportunities) >= 2:
            return "Magandang foundation na may malaking potential para sa improvement"
        else:
            return "Balanced na readiness na may specific areas para sa enhancement"
    else:
        if len(strengths) >= 3:
            return "Strong overall readiness with established capabilities across multiple dimensions"
        elif len(weaknesses) >= 3:
            return "Requires significant improvement across multiple areas before commercialization"
        elif len(opportunities) >= 2:
            return "Good foundation with substantial potential for improvement"
        else:
            return "Balanced readiness with specific areas identified for enhancement"

def generate_tcp_success_strategies(dimension_scores, recommended_pathway, language):
    """Generate comprehensive success strategies"""
    strategies = {
        "immediate_actions": [],
        "short_term_strategies": [],
        "long_term_strategies": [],
        "pathway_specific": [],
        "capability_building": []
    }
    
    # Get pathway details
    pathway_info = next((p for p in TCP_QUESTIONS["english"]["pathways"] if p["name"] == recommended_pathway), None)
    
    if language == "filipino":
        # Immediate actions based on weaknesses
        weak_dimensions = [dim for dim, data in dimension_scores.items() if data["percentage"] < 50]
        for dim in weak_dimensions[:2]:  # Focus on top 2 weakest
            if "Technology" in dim:
                strategies["immediate_actions"].append(f"Palakasin ang technology development at validation para sa {dim}")
            elif "Market" in dim:
                strategies["immediate_actions"].append(f"Mag-conduct ng comprehensive market research para sa {dim}")
            elif "Business" in dim:
                strategies["immediate_actions"].append(f"Mag-develop ng business capabilities para sa {dim}")
            elif "Team" in dim:
                strategies["immediate_actions"].append(f"Mag-strengthen ng team expertise para sa {dim}")
        
        # Pathway-specific strategies
        if recommended_pathway == "Direct Sale":
            strategies["pathway_specific"] = [
                "Mag-build ng direct sales team na may industry experience",
                "Mag-establish ng customer support at service infrastructure",
                "Mag-develop ng competitive pricing strategy",
                "Mag-create ng comprehensive marketing materials"
            ]
        elif recommended_pathway == "Licensing":
            strategies["pathway_specific"] = [
                "Mag-strengthen ng IP portfolio at protection strategy",
                "Mag-identify ng potential licensing partners sa target industry",
                "Mag-prepare ng comprehensive technology packages",
                "Mag-develop ng licensing terms at negotiation strategy"
            ]
        elif recommended_pathway == "Startup/Spin-out":
            strategies["pathway_specific"] = [
                "Mag-assemble ng experienced founding team",
                "Mag-develop ng detailed business plan at financial projections",
                "Mag-secure ng initial seed funding",
                "Mag-establish ng legal structure at governance"
            ]
        
        # Long-term strategies
        strategies["long_term_strategies"] = [
            "Mag-establish ng sustainable competitive advantage",
            "Mag-build ng strong brand recognition sa target market",
            "Mag-develop ng strategic partnerships para sa growth",
            "Mag-create ng innovation pipeline para sa future products"
        ]
    else:
        # Immediate actions based on weaknesses
        weak_dimensions = [dim for dim, data in dimension_scores.items() if data["percentage"] < 50]
        for dim in weak_dimensions[:2]:  # Focus on top 2 weakest
            if "Technology" in dim:
                strategies["immediate_actions"].append(f"Strengthen technology development and validation capabilities in {dim}")
            elif "Market" in dim:
                strategies["immediate_actions"].append(f"Conduct comprehensive market research and validation for {dim}")
            elif "Business" in dim:
                strategies["immediate_actions"].append(f"Develop business capabilities and resources for {dim}")
            elif "Team" in dim:
                strategies["immediate_actions"].append(f"Strengthen team expertise and experience in {dim}")
        
        # Short-term strategies (3-12 months)
        strategies["short_term_strategies"] = [
            "Establish key performance indicators and monitoring systems",
            "Build strategic partnerships and alliances",
            "Develop pilot programs or proof-of-concept demonstrations",
            "Secure necessary funding and resource commitments"
        ]
        
        # Pathway-specific strategies
        if pathway_info:
            if recommended_pathway == "Direct Sale":
                strategies["pathway_specific"] = [
                    "Build direct sales team with industry experience and networks",
                    "Establish customer support and service infrastructure",
                    "Develop competitive pricing strategy based on market analysis", 
                    "Create comprehensive marketing materials and sales tools"
                ]
            elif recommended_pathway == "Licensing":
                strategies["pathway_specific"] = [
                    "Strengthen IP portfolio and protection strategy",
                    "Identify and approach potential licensing partners in target industries",
                    "Prepare comprehensive technology packages and documentation",
                    "Develop licensing terms and negotiation strategy"
                ]
            elif recommended_pathway == "Startup/Spin-out":
                strategies["pathway_specific"] = [
                    "Assemble experienced founding team with complementary skills",
                    "Develop detailed business plan with financial projections",
                    "Secure initial seed funding through grants, angels, or VCs",
                    "Establish legal structure and corporate governance"
                ]
            elif recommended_pathway == "Government Procurement":
                strategies["pathway_specific"] = [
                    "Understand government procurement processes and requirements",
                    "Ensure compliance with all relevant regulations and standards",
                    "Build relationships with key government stakeholders",
                    "Prepare for lengthy procurement cycles and processes"
                ]
        
        # Long-term strategies (1-3 years)
        strategies["long_term_strategies"] = [
            "Establish sustainable competitive advantage through continuous innovation",
            "Build strong brand recognition and market presence",
            "Develop strategic partnerships for growth and expansion",
            "Create innovation pipeline for future products and services"
        ]
        
        # Capability building recommendations
        strategies["capability_building"] = [
            "Invest in team development and skill enhancement",
            "Build organizational processes and systems for scaling",
            "Establish quality assurance and continuous improvement programs",
            "Develop crisis management and risk mitigation capabilities"
        ]
    
    return strategies

def generate_tcp_risk_assessment(dimension_scores, recommended_pathway, language):
    """Generate comprehensive risk assessment"""
    risks = {
        "high_risks": [],
        "medium_risks": [],
        "low_risks": [],
        "mitigation_strategies": [],
        "contingency_plans": []
    }
    
    # Identify risks based on dimension weaknesses
    for dim_name, dim_data in dimension_scores.items():
        percentage = dim_data["percentage"]
        
        if percentage < 30:
            if language == "filipino":
                risks["high_risks"].append({
                    "area": dim_name,
                    "risk": f"Napakababang capability sa {dim_name} ay maaaring mag-cause ng project failure",
                    "impact": "Critical",
                    "probability": "High"
                })
            else:
                risks["high_risks"].append({
                    "area": dim_name,
                    "risk": f"Very low capability in {dim_name} may cause project failure",
                    "impact": "Critical", 
                    "probability": "High"
                })
        elif percentage < 50:
            if language == "filipino":
                risks["medium_risks"].append({
                    "area": dim_name,
                    "risk": f"Limited capability sa {dim_name} ay maaaring mag-delay ng commercialization",
                    "impact": "Moderate",
                    "probability": "Medium"
                })
            else:
                risks["medium_risks"].append({
                    "area": dim_name,
                    "risk": f"Limited capability in {dim_name} may delay commercialization",
                    "impact": "Moderate",
                    "probability": "Medium"
                })
    
    # Pathway-specific risks
    if language == "filipino":
        if recommended_pathway == "Direct Sale":
            risks["medium_risks"].append({
                "area": "Market Execution",
                "risk": "Direct sales ay nangangailangan ng malaking investment sa marketing at sales",
                "impact": "High",
                "probability": "Medium"
            })
        elif recommended_pathway == "Licensing":
            risks["medium_risks"].append({
                "area": "Partner Dependency", 
                "risk": "Success ay dependent sa performance ng licensing partners",
                "impact": "Medium",
                "probability": "Medium"
            })
        elif recommended_pathway == "Startup/Spin-out":
            risks["high_risks"].append({
                "area": "Entrepreneurial Risk",
                "risk": "Startup approach ay may mataas na failure rate at resource requirements",
                "impact": "Critical",
                "probability": "High"
            })
        
        # General mitigation strategies
        risks["mitigation_strategies"] = [
            "Mag-develop ng comprehensive risk monitoring system",
            "Mag-establish ng emergency contingency plans",
            "Mag-build ng diverse partnerships para sa risk distribution",
            "Mag-maintain ng adequate financial reserves"
        ]
        
        risks["contingency_plans"] = [
            f"Kung hindi successful ang {recommended_pathway}, consider ang second-best pathway",
            "Mag-establish ng alternative funding sources",
            "Mag-develop ng pivot strategies kung mag-change ang market conditions"
        ]
    else:
        if recommended_pathway == "Direct Sale":
            risks["medium_risks"].append({
                "area": "Market Execution",
                "risk": "Direct sales requires significant investment in marketing and sales infrastructure",
                "impact": "High",
                "probability": "Medium"
            })
        elif recommended_pathway == "Licensing":
            risks["medium_risks"].append({
                "area": "Partner Dependency",
                "risk": "Success depends heavily on licensing partner performance and commitment",
                "impact": "Medium", 
                "probability": "Medium"
            })
        elif recommended_pathway == "Startup/Spin-out":
            risks["high_risks"].append({
                "area": "Entrepreneurial Risk",
                "risk": "Startup approach has high failure rate and significant resource requirements",
                "impact": "Critical",
                "probability": "High"
            })
        
        # General mitigation strategies
        risks["mitigation_strategies"] = [
            "Develop comprehensive risk monitoring and early warning systems",
            "Establish emergency contingency plans and crisis management protocols",
            "Build diverse partnerships and alliances for risk distribution",
            "Maintain adequate financial reserves and backup funding options"
        ]
        
        risks["contingency_plans"] = [
            f"If {recommended_pathway} is not successful, pivot to second-best pathway option",
            "Establish alternative funding sources and financial backup plans",
            "Develop pivot strategies for changing market conditions or technology disruption"
        ]
    
    return risks

def generate_tcp_implementation_plan(recommended_pathway, dimension_scores, language):
    """Generate detailed implementation plan"""
    plan = {
        "phase_1": {"timeframe": "0-6 months", "activities": [], "milestones": []},
        "phase_2": {"timeframe": "6-18 months", "activities": [], "milestones": []},
        "phase_3": {"timeframe": "18-36 months", "activities": [], "milestones": []},
        "success_metrics": [],
        "resource_requirements": []
    }
    
    if language == "filipino":
        # Phase 1: Foundation
        plan["phase_1"]["activities"] = [
            "Mag-address ng identified weaknesses sa dimension scores",
            "Mag-establish ng core team at organizational structure",
            "Mag-develop ng detailed commercialization strategy"
        ]
        plan["phase_1"]["milestones"] = [
            "Nakumpleto ang team formation",
            "Na-finalize ang commercialization strategy",
            "Na-secure ang initial funding o resources"
        ]
        
        # Phase 2: Development
        plan["phase_2"]["activities"] = [
            "Mag-implement ng pathway-specific strategies",
            "Mag-build ng necessary capabilities at infrastructure", 
            "Mag-establish ng key partnerships"
        ]
        plan["phase_2"]["milestones"] = [
            "Na-establish ang key partnerships",
            "Natapos ang capability building programs",
            "Na-launch ang pilot programs o prototypes"
        ]
        
        # Phase 3: Launch
        plan["phase_3"]["activities"] = [
            "Mag-execute ng full commercialization plan",
            "Mag-monitor at mag-optimize ng performance",
            "Mag-scale operations based sa results"
        ]
        plan["phase_3"]["milestones"] = [
            "Successful commercial launch",
            "Na-achieve ang target performance metrics",
            "Na-establish ang sustainable operations"
        ]
        
        # Success metrics
        plan["success_metrics"] = [
            "Technology readiness improvement scores",
            "Market penetration rates",
            "Revenue generation milestones",
            "Partnership establishment success"
        ]
    else:
        # Phase 1: Foundation (0-6 months)
        plan["phase_1"]["activities"] = [
            "Address identified weaknesses in dimension scores through targeted improvements",
            "Establish core team and organizational structure for commercialization",
            "Develop detailed commercialization strategy and execution plan"
        ]
        plan["phase_1"]["milestones"] = [
            "Complete team formation with all key roles filled",
            "Finalize comprehensive commercialization strategy",
            "Secure initial funding or resource commitments"
        ]
        
        # Phase 2: Development (6-18 months)
        plan["phase_2"]["activities"] = [
            "Implement pathway-specific strategies and action plans",
            "Build necessary capabilities and infrastructure",
            "Establish key partnerships and strategic alliances"
        ]
        plan["phase_2"]["milestones"] = [
            "Establish all critical partnerships and alliances",
            "Complete capability building and infrastructure development",
            "Launch pilot programs or prototype demonstrations"
        ]
        
        # Phase 3: Launch and Scale (18-36 months)
        plan["phase_3"]["activities"] = [
            "Execute full commercialization plan with market launch",
            "Monitor performance and optimize operations continuously",
            "Scale operations based on market response and results"
        ]
        plan["phase_3"]["milestones"] = [
            "Achieve successful commercial launch",
            "Meet target performance metrics and KPIs",
            "Establish sustainable and scalable operations"
        ]
        
        # Success metrics
        plan["success_metrics"] = [
            "Technology readiness level improvements across all dimensions",
            "Market penetration rates and customer acquisition metrics",
            "Revenue generation and financial performance milestones",
            "Partnership establishment and collaboration success rates"
        ]
        
        # Resource requirements
        plan["resource_requirements"] = [
            f"Estimated investment: {get_pathway_investment_estimate(recommended_pathway)}",
            f"Timeline to market: {get_pathway_timeline_estimate(recommended_pathway)}",
            f"Key personnel needed: {get_pathway_personnel_requirements(recommended_pathway)}",
            f"Infrastructure requirements: {get_pathway_infrastructure_needs(recommended_pathway)}"
        ]
    
    return plan

def get_pathway_investment_estimate(pathway):
    """Get investment estimate for pathway"""
    estimates = {
        "Direct Sale": "Medium to High ($100K-$1M+)",
        "Licensing": "Low to Medium ($10K-$100K)",
        "Startup/Spin-out": "High ($500K-$5M+)",
        "Assignment": "Low ($5K-$50K)",
        "Research Collaboration": "Medium ($50K-$500K)",
        "Open Source": "Low to Medium ($10K-$100K)",
        "Government Procurement": "Medium ($100K-$1M)"
    }
    return estimates.get(pathway, "Medium ($50K-$500K)")

def get_pathway_timeline_estimate(pathway):
    """Get timeline estimate for pathway"""
    timelines = {
        "Direct Sale": "12-24 months",
        "Licensing": "6-18 months",
        "Startup/Spin-out": "18-36 months",
        "Assignment": "3-12 months",
        "Research Collaboration": "12-36 months",
        "Open Source": "6-12 months",
        "Government Procurement": "12-36 months"
    }
    return timelines.get(pathway, "12-24 months")

def get_pathway_personnel_requirements(pathway):
    """Get personnel requirements for pathway"""
    requirements = {
        "Direct Sale": "Sales team, marketing specialists, customer support",
        "Licensing": "IP specialists, business development, legal support",
        "Startup/Spin-out": "Founding team, technical leads, business developers",
        "Assignment": "Legal support, technology transfer specialists",
        "Research Collaboration": "Research team, project managers, partnerships lead",
        "Open Source": "Community managers, technical evangelists, developers",
        "Government Procurement": "Regulatory specialists, government relations, compliance"
    }
    return requirements.get(pathway, "General business and technical team")

def get_pathway_infrastructure_needs(pathway):
    """Get infrastructure needs for pathway"""
    needs = {
        "Direct Sale": "Sales infrastructure, customer support systems, distribution",
        "Licensing": "IP management systems, partner portals, technology packages",
        "Startup/Spin-out": "Complete business infrastructure, office space, systems",
        "Assignment": "Legal documentation, technology transfer processes",
        "Research Collaboration": "Research facilities, collaboration platforms, data sharing",
        "Open Source": "Development platforms, community tools, documentation",
        "Government Procurement": "Compliance systems, security infrastructure, certifications"
    }
    return needs.get(pathway, "Basic business and technical infrastructure")

def generate_tcp_financial_analysis(recommended_pathway, dimension_scores, language):
    """Generate financial analysis and projections"""
    analysis = {
        "investment_requirements": {},
        "revenue_projections": {},
        "break_even_analysis": {},
        "funding_recommendations": []
    }
    
    # Get pathway info
    pathway_info = next((p for p in TCP_QUESTIONS["english"]["pathways"] if p["name"] == recommended_pathway), None)
    
    if language == "filipino":
        analysis["investment_requirements"] = {
            "initial_investment": get_pathway_investment_estimate(recommended_pathway),
            "ongoing_costs": "Monthly operational costs na mag-vary depende sa scale",
            "risk_level": pathway_info["risk_level"] if pathway_info else "Medium"
        }
        
        analysis["revenue_projections"] = {
            "timeline_to_revenue": get_pathway_timeline_estimate(recommended_pathway),
            "revenue_model": get_pathway_revenue_model(recommended_pathway, language),
            "growth_potential": "Dependent sa market size at adoption rate"
        }
        
        analysis["funding_recommendations"] = [
            "Mag-explore ng government grants para sa R&D activities",
            "Consider ang angel investors o VCs para sa high-growth potential",
            "Mag-apply sa innovation competitions at startup programs",
            "Mag-look into strategic partnerships na may funding component"
        ]
    else:
        analysis["investment_requirements"] = {
            "initial_investment": get_pathway_investment_estimate(recommended_pathway),
            "ongoing_costs": "Monthly operational costs varying by scale and complexity",
            "risk_level": pathway_info["risk_level"] if pathway_info else "Medium",
            "roi_timeline": "Typically 2-5 years depending on market conditions"
        }
        
        analysis["revenue_projections"] = {
            "timeline_to_revenue": get_pathway_timeline_estimate(recommended_pathway),
            "revenue_model": get_pathway_revenue_model(recommended_pathway, language),
            "growth_potential": "Dependent on market size, adoption rate, and competitive positioning"
        }
        
        analysis["break_even_analysis"] = {
            "estimated_timeline": "18-36 months for most pathways",
            "key_factors": "Customer acquisition costs, pricing strategy, operational efficiency",
            "sensitivity": "High sensitivity to market adoption and competitive response"
        }
        
        analysis["funding_recommendations"] = [
            "Explore government grants and R&D tax incentives",
            "Consider angel investors or VCs for high-growth potential technologies",
            "Apply to innovation competitions and startup accelerator programs",
            "Investigate strategic partnerships with established companies",
            "Consider crowdfunding for consumer-oriented technologies"
        ]
    
    return analysis

def get_pathway_revenue_model(pathway, language):
    """Get revenue model description for pathway"""
    if language == "filipino":
        models = {
            "Direct Sale": "Direct revenue from product sales sa customers",
            "Licensing": "Licensing fees, royalties, at milestone payments",
            "Startup/Spin-out": "Product sales, services, at potential equity value",
            "Assignment": "One-time payment para sa technology rights",
            "Research Collaboration": "Shared IP value at research funding",
            "Open Source": "Service-based revenue at support contracts",
            "Government Procurement": "Contract-based revenue from government agencies"
        }
    else:
        models = {
            "Direct Sale": "Direct revenue from product sales to end customers",
            "Licensing": "Licensing fees, royalties, and milestone payments from partners",
            "Startup/Spin-out": "Product sales, services revenue, and potential equity value",
            "Assignment": "One-time payment for technology rights transfer",
            "Research Collaboration": "Shared intellectual property value and research funding",
            "Open Source": "Service-based revenue, support contracts, and consulting",
            "Government Procurement": "Contract-based revenue from government agencies and public sector"
        }
    
    return models.get(pathway, "Mixed revenue streams depending on implementation")

def generate_tcp_partnership_recommendations(recommended_pathway, dimension_scores, language):
    """Generate partnership recommendations"""
    recommendations = {
        "strategic_partners": [],
        "technology_partners": [],
        "distribution_partners": [],
        "funding_partners": [],
        "partnership_strategy": []
    }
    
    if language == "filipino":
        # Strategic partners based on pathway
        if recommended_pathway == "Direct Sale":
            recommendations["strategic_partners"] = [
                "Industry leaders na may established customer base",
                "Technology integrators na pwedeng mag-incorporate ng solution",
                "Channel partners na may distribution networks"
            ]
        elif recommended_pathway == "Licensing":
            recommendations["strategic_partners"] = [
                "Large corporations na may complementary products",
                "International companies na nag-hahanap ng innovation",
                "Industry consortiums para sa standard setting"
            ]
        elif recommended_pathway == "Startup/Spin-out":
            recommendations["strategic_partners"] = [
                "Accelerators at incubators na specialized sa technology",
                "Angel investors at VCs na may sector expertise",
                "Industry mentors na may successful track record"
            ]
        
        recommendations["partnership_strategy"] = [
            "Mag-identify ng partners na may complementary strengths",
            "Mag-establish ng clear partnership agreements at expectations",
            "Mag-maintain ng regular communication at collaboration",
            "Mag-measure ng partnership success through defined metrics"
        ]
    else:
        # Strategic partners based on pathway
        if recommended_pathway == "Direct Sale":
            recommendations["strategic_partners"] = [
                "Industry leaders with established customer relationships",
                "Technology integrators who can incorporate solution into offerings",
                "Channel partners with distribution networks and market access"
            ]
        elif recommended_pathway == "Licensing":
            recommendations["strategic_partners"] = [
                "Large corporations with complementary product portfolios",
                "International companies seeking innovative technologies",
                "Industry consortiums and standard-setting organizations"
            ]
        elif recommended_pathway == "Startup/Spin-out":
            recommendations["strategic_partners"] = [
                "Technology-focused accelerators and incubators",
                "Angel investors and VCs with relevant sector expertise",
                "Industry mentors with successful commercialization experience"
            ]
        elif recommended_pathway == "Government Procurement":
            recommendations["strategic_partners"] = [
                "Established government contractors and system integrators",
                "Public sector consulting firms with agency relationships",
                "Compliance and regulatory specialists"
            ]
        
        # Technology partners
        recommendations["technology_partners"] = [
            "Research institutions with complementary capabilities",
            "Technology suppliers for critical components",
            "Software/platform providers for integration needs"
        ]
        
        # Distribution partners
        recommendations["distribution_partners"] = [
            "Regional distributors with market knowledge",
            "Online platforms for digital distribution",
            "Retail partners for direct customer access"
        ]
        
        # Funding partners
        recommendations["funding_partners"] = [
            "Government innovation programs and grants",
            "Industry-specific VCs and strategic investors",
            "Crowdfunding platforms for consumer technologies"
        ]
        
        recommendations["partnership_strategy"] = [
            "Identify partners with complementary strengths and capabilities",
            "Establish clear partnership agreements with defined roles and expectations",
            "Maintain regular communication and collaborative working relationships",
            "Measure partnership success through defined metrics and KPIs",
            "Build long-term strategic relationships rather than transactional arrangements"
        ]
    
    return recommendations

def generate_detailed_pathway_analysis(tcp_data, recommended_pathway, language):
    """Generate detailed analysis of the recommended pathway"""
    pathway_info = next((p for p in tcp_data["pathways"] if p["name"] == recommended_pathway), None)
    
    if not pathway_info:
        return {}
    
    analysis = {
        "pathway_name": pathway_info["name"],
        "description": pathway_info["description"],
        "best_for": pathway_info.get("best_for", ""),
        "timeline": pathway_info.get("timeline", ""),
        "investment_required": pathway_info.get("investment_required", ""),
        "risk_level": pathway_info.get("risk_level", ""),
        "success_factors": pathway_info.get("criteria", []),
        "advantages": [],
        "challenges": [],
        "success_examples": []
    }
    
    # Add pathway-specific advantages and challenges
    if language == "filipino":
        pathway_details = {
            "Direct Sale": {
                "advantages": [
                    "Full control sa customer relationship at brand",
                    "Higher profit margins through direct sales",
                    "Direct feedback from customers para sa improvement"
                ],
                "challenges": [
                    "Kailangan ng malaking investment sa sales at marketing",
                    "Need ng comprehensive customer support infrastructure",
                    "High competition sa direct market"
                ]
            },
            "Licensing": {
                "advantages": [
                    "Lower investment requirements para sa commercialization",
                    "Access sa established distribution networks ng partners",
                    "Reduced operational complexity"
                ],
                "challenges": [
                    "Limited control sa market execution",
                    "Dependency sa performance ng licensing partners",
                    "Potential conflicts over strategy at priorities"
                ]
            },
            "Startup/Spin-out": {
                "advantages": [
                    "Maximum potential returns from successful commercialization",
                    "Complete control over strategy at execution",
                    "Ability to attract top talent through equity"
                ],
                "challenges": [
                    "High risk of failure at significant resource requirements",
                    "Need for entrepreneurial skills at experience",
                    "Intense competition for funding at market share"
                ]
            }
        }
    else:
        pathway_details = {
            "Direct Sale": {
                "advantages": [
                    "Full control over customer relationships and brand positioning",
                    "Higher profit margins through direct customer sales",
                    "Direct customer feedback for continuous improvement"
                ],
                "challenges": [
                    "Requires significant investment in sales and marketing infrastructure",
                    "Need for comprehensive customer support and service capabilities",
                    "High competition in direct-to-customer markets"
                ]
            },
            "Licensing": {
                "advantages": [
                    "Lower investment requirements for commercialization",
                    "Access to established distribution networks and customer relationships",
                    "Reduced operational complexity and resource requirements"
                ],
                "challenges": [
                    "Limited control over market execution and customer experience",
                    "Dependency on licensing partner performance and commitment",
                    "Potential conflicts over strategic direction and priorities"
                ]
            },
            "Startup/Spin-out": {
                "advantages": [
                    "Maximum potential returns from successful commercialization",
                    "Complete control over strategic direction and execution",
                    "Ability to attract top talent through equity participation"
                ],
                "challenges": [
                    "High risk of failure with significant resource requirements",
                    "Need for entrepreneurial skills and startup experience",
                    "Intense competition for funding and market share"
                ]
            },
            "Government Procurement": {
                "advantages": [
                    "Large contract values and stable, long-term relationships",
                    "Less price sensitivity for innovative solutions",
                    "Opportunity to shape public sector standards"
                ],
                "challenges": [
                    "Complex procurement processes with lengthy timelines",
                    "Strict compliance and regulatory requirements",
                    "Political and budgetary uncertainties"
                ]
            }
        }
    
    # Get pathway-specific details
    details = pathway_details.get(recommended_pathway, {})
    analysis["advantages"] = details.get("advantages", [])
    analysis["challenges"] = details.get("challenges", [])
    
    return analysis

def calculate_tcp_overall_readiness(dimension_scores):
    """Calculate overall TCP readiness score"""
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

def calculate_tcp_confidence_score(pathway_scores, dimension_scores):
    """Calculate confidence score for TCP recommendation"""
    # Basic confidence from pathway scores
    max_score = max(pathway_scores.values()) if pathway_scores else 0
    second_score = sorted(pathway_scores.values(), reverse=True)[1] if len(pathway_scores) > 1 else 0
    score_gap = max_score - second_score
    
    # Average dimension readiness
    avg_dimension_score = sum(dim["percentage"] for dim in dimension_scores.values()) / len(dimension_scores) if dimension_scores else 0
    
    # Calculate confidence (0-100)
    confidence = min(100, (score_gap * 10) + (avg_dimension_score * 0.5))
    
    return round(confidence, 1)

def generate_tcp_enhanced_explanation(pathway_scores, recommended_pathway, detailed_analysis, language):
    """Generate enhanced explanation for TCP results"""
    confidence = detailed_analysis.get("confidence_score", 0)
    second_alt = detailed_analysis.get("second_alternative")
    overall_readiness = detaile
