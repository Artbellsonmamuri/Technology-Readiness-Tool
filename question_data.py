# All Question Databases

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
                "May estratehiya na ba ukol sa proteksyon ng intelektuwal na ari-arian?"
            ]
        },
        # Add other Filipino TRL levels here (same as before)
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
        # Add other IRL levels here (same as before)
    ],
    "filipino": [
        # Add Filipino IRL questions here
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
        # Add other MRL levels here (same as before)
    ],
    "filipino": [
        # Add Filipino MRL questions here
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
            # Add other Filipino TCP dimensions here
        ],
        "pathways": [
            {
                "name": "Direct Sale",
                "description": "Direktang pagbenta ng teknolohiya sa end users o customers",
                "criteria": ["Mataas na technology readiness", "Malakas na internal resources", "Established market channels"]
            },
            # Add other Filipino TCP pathways here
        ]
    }
}
