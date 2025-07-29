class AssessmentApp {
    constructor() {
        this.lang = "";
        this.mode = "";
        this.questions = [];
        this.answers = [];
        this.lix = 0;
        this.cix = 0;
        
        this.tcpQuestions = [];
        this.tcpCurrentQuestion = 0;
        this.tcpAnswers = [];
        this.result = null;

        this.i18n = {
            english: {
                choose_lang: "Choose Your Language",
                select_mode: "Select Assessment Mode",
                trl_desc: "Technology Readiness Level",
                irl_desc: "Investment Readiness Level",
                mrl_desc: "Market Readiness Level",
                tcp_desc: "Technology Commercialization Pathway",
                tech_info: "Technology Information",
                title_lbl: "Technology Title:",
                desc_lbl: "Short Description:",
                start: "Start Assessment",
                q_title: "Assessment Questions",
                tcp_q_title: "TCP Assessment Questions",
                yes: "Yes",
                no: "No",
                results: "Assessment Results",
                download: "Download PDF Report",
                restart: "Start New Assessment"
            },
            filipino: {
                choose_lang: "Pumili ng Wika",
                select_mode: "Pumili ng Uri ng Assessment",
                trl_desc: "Technology Readiness Level",
                irl_desc: "Investment Readiness Level",
                mrl_desc: "Market Readiness Level",
                tcp_desc: "Technology Commercialization Pathway",
                tech_info: "Impormasyon ng Teknolohiya",
                title_lbl: "Pamagat ng Teknolohiya:",
                desc_lbl: "Maikling Paglalarawan:",
                start: "Simulan ang Assessment",
                q_title: "Mga Tanong sa Assessment",
                tcp_q_title: "TCP Assessment na mga Tanong",
                yes: "Oo",
                no: "Hindi",
                results: "Mga Resulta",
                download: "I-download ang PDF",
                restart: "Magsimula Muli"
            }
        };
    }

    pickLanguage(code) {
        this.lang = code;
        this.translate();
        this.showStep("mode-selection");
    }

    pickMode(m) {
        this.mode = m;
        this.showStep("tech-info");
    }

    async begin() {
        if (this.collectInfo()) {
            await this.fetchQuestions();
            if (this.mode === "TCP") {
                this.presentTCP();
            } else {
                this.present();
            }
        }
    }

    translate() {
        const t = this.i18n[this.lang];
        this.setText("mode-title", t.select_mode);
        this.setText("trl-description", t.trl_desc);
        this.setText("irl-description", t.irl_desc);
        this.setText("mrl-description", t.mrl_desc);
        this.setText("tcp-description", t.tcp_desc);
        this.setText("tech-info-title", t.tech_info);
        this.setText("title-label", t.title_lbl);
        this.setText("description-label", t.desc_lbl);
        this.setText("start-btn", t.start);
        this.setText("questions-title", t.q_title);
        this.setText("tcp-questions-title", t.tcp_q_title);
        this.setText("yes-btn", t.yes);
        this.setText("no-btn", t.no);
        this.setText("results-title", t.results);
        this.setText("download-btn", t.download);
        this.setText("restart-btn", t.restart);
    }

    collectInfo() {
        this.title = this.getValue("tech-title");
        this.desc = this.getValue("tech-description");
        if (!this.title || !this.desc) {
            alert(this.lang === "english" ? "Fill in all fields" : "Pakipunan ang lahat ng field");
            return false;
        }
        return true;
    }

    async fetchQuestions() {
        try {
            const res = await fetch(`/api/questions/${this.mode}/${this.lang}`);
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            if (this.mode === "TCP") {
                this.tcpQuestions = await res.json();
                console.log("TCP Questions loaded:", this.tcpQuestions);
            } else {
                this.questions = await res.json();
                console.log(`${this.mode} Questions loaded:`, this.questions);
            }
        } catch (error) {
            console.error('Error loading questions:', error);
            alert(this.lang === "english" ? 
                "Error loading questions. Please try again." : 
                "Error sa pag-load ng mga tanong. Subukan muli.");
        }
    }

    // TCP Assessment Methods
    presentTCP() {
        this.tcpCurrentQuestion = 0;
        this.tcpAnswers = [];
        this.showStep("tcp-questions");
        this.renderTCPQuestion();
    }

    renderTCPQuestion() {
        let questionIndex = 0;
        let currentDimension = "";
        let currentQuestion = "";

        for (const dimension of this.tcpQuestions.dimensions) {
            for (const question of dimension.questions) {
                if (questionIndex === this.tcpCurrentQuestion) {
                    currentDimension = dimension.name;
                    currentQuestion = question;
                    break;
                }
                questionIndex++;
            }
            if (currentQuestion) break;
        }

        this.setText("tcp-dimension-title", currentDimension);
        this.setText("tcp-question-text", currentQuestion);

        const totalQuestions = this.tcpQuestions.dimensions.reduce((sum, dim) => sum + dim.questions.length, 0);
        const progress = ((this.tcpCurrentQuestion + 1) / totalQuestions) * 100;
        
        const progressElement = document.getElementById("tcp-progress");
        if (progressElement) {
            progressElement.style.width = `${progress}%`;
        }

        this.setText("tcp-progress-text",
            `${this.lang === "english" ? "Question" : "Tanong"} ${this.tcpCurrentQuestion + 1} / ${totalQuestions}`);
    }

    recordTCP(score) {
        this.tcpAnswers.push(score);
        this.tcpCurrentQuestion++;

        const totalQuestions = this.tcpQuestions.dimensions.reduce((sum, dim) => sum + dim.questions.length, 0);
        
        if (this.tcpCurrentQuestion >= totalQuestions) {
            this.finishTCP();
        } else {
            this.renderTCPQuestion();
        }
    }

    async finishTCP() {
        const payload = {
            mode: this.mode,
            language: this.lang,
            technology_title: this.title,
            description: this.desc,
            answers: this.tcpAnswers
        };

        console.log("Finishing TCP assessment with payload:", payload);

        try {
            const res = await fetch("/api/assess", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            
            this.result = await res.json();
            console.log("TCP assessment result:", this.result);
            this.showTCPResults();
        } catch (error) {
            console.error('Error completing TCP assessment:', error);
            alert(this.lang === "english" ? 
                "Error completing assessment. Please try again." : 
                "Error sa pagkumpleto ng assessment. Subukan muli.");
        }
    }

    showTCPResults() {
        // Set main result display
        this.setText("result-level", `Recommended Pathway: ${this.result.recommended_pathway}`);
        this.setText("tech-title-display", this.result.technology_title);
        
        // Enhanced explanation with detailed analysis
        let explanation = this.result.explanation;
        const detailedAnalysis = this.result.detailed_analysis;
        
        if (detailedAnalysis) {
            const overall = detailedAnalysis.overall_readiness;
            explanation += `\n\nOverall Commercialization Readiness: ${overall}`;
            
            if (detailedAnalysis.strengths && detailedAnalysis.strengths.length > 0) {
                explanation += `\n\nKey Strengths: ${detailedAnalysis.strengths.join(", ")}`;
            }
            
            if (detailedAnalysis.weaknesses && detailedAnalysis.weaknesses.length > 0) {
                explanation += `\n\nAreas for Improvement: ${detailedAnalysis.weaknesses.join(", ")}`;
            }
        }
        
        this.setText("result-explanation", explanation);

        // Set badge
        const badge = document.getElementById("result-badge");
        if (badge) {
            badge.textContent = "TCP Assessment";
            badge.style.background = "#DCFCE7";
            badge.style.color = "#065F46";
        }

        // Show pathway scores with enhanced details
        const scoresContainer = document.getElementById("tcp-pathway-scores");
        const scoresList = document.getElementById("pathway-scores-list");
        if (scoresContainer && scoresList) {
            scoresContainer.style.display = "block";
            scoresList.innerHTML = "";
            
            const pathwayScores = this.result.pathway_scores;
            const sortedPathways = Object.entries(pathwayScores).sort((a, b) => b[1] - a[1]);
            
            // Add title with overall readiness
            if (detailedAnalysis && detailedAnalysis.overall_readiness) {
                const readinessTitle = document.createElement("div");
                readinessTitle.className = "pathway-score-item";
                readinessTitle.innerHTML = `<strong>Overall Readiness: ${detailedAnalysis.overall_readiness}</strong>`;
                readinessTitle.style.borderTop = "2px solid #065F46";
                readinessTitle.style.paddingTop = "12px";
                readinessTitle.style.marginTop = "8px";
                scoresList.appendChild(readinessTitle);
            }
            
            sortedPathways.forEach(([pathway, score], index) => {
                const scoreItem = document.createElement("div");
                scoreItem.className = "pathway-score-item";
                scoreItem.innerHTML = `<strong>#${index + 1} ${pathway}:</strong> ${score} points`;
                
                // Highlight recommended pathway
                if (pathway === this.result.recommended_pathway) {
                    scoreItem.style.backgroundColor = "#DCFCE7";
                    scoreItem.style.fontWeight = "bold";
                    scoreItem.style.borderLeft = "4px solid #065F46";
                    scoreItem.style.paddingLeft = "12px";
                }
                
                scoresList.appendChild(scoreItem);
            });
        }

        this.showStep("results");
    }

    // Regular Assessment Methods (TRL/IRL/MRL)
    present() {
        this.lix = 0;
        this.cix = 0;
        this.answers = [];
        this.showStep("questions");
        this.renderCheck();
    }

    renderCheck() {
        const lvl = this.questions[this.lix];
        const qtext = lvl.checks[this.cix];
        this.setText("question-text", qtext);

        const progressDesc = `${lvl.title} — ${this.lang==='english'?'Check':'Tanong'} ${this.cix + 1}/${lvl.checks.length}`;
        this.setText("question-description", progressDesc);

        const done = this.answers.flat().length;
        const total = this.questions.reduce((s, l) => s + l.checks.length, 0);

        const progressElement = document.getElementById("progress");
        if (progressElement) {
            progressElement.style.width = `${Math.round(done / total * 100)}%`;
        }

        this.setText("progress-text",
            `${this.lang === "english" ? "Check" : "Tanong"} ${done + 1} / ${total}`);
    }

    record(ans) {
        if (!this.answers[this.lix]) this.answers[this.lix] = [];
        this.answers[this.lix].push(ans);

        if (!ans) {
            return this.finish();
        }

        const lvl = this.questions[this.lix];
        if (this.cix + 1 < lvl.checks.length) {
            this.cix++;
        } else {
            this.lix++;
            this.cix = 0;
        }

        if (this.lix >= this.questions.length) {
            this.finish();
        } else {
            this.renderCheck();
        }
    }

    async finish() {
        const payload = {
            mode: this.mode,
            language: this.lang,
            technology_title: this.title,
            description: this.desc,
            answers: this.answers
        };

        try {
            const res = await fetch("/api/assess", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            
            this.result = await res.json();
            console.log(`${this.mode} assessment result:`, this.result);

            this.setText("result-level",
                `${this.result.mode} ${(this.lang === "english") ? "Level" : "Antas"} ${this.result.level}`);
            this.setText("tech-title-display", this.result.technology_title);
            
            // Enhanced explanation for MRL
            let explanation = this.result.explanation;
            if (this.mode === "MRL" && this.result.detailed_analysis) {
                const analysis = this.result.detailed_analysis;
                explanation += `\n\nMarket Readiness: ${analysis.market_readiness}`;
                explanation += `\nOverall Progress: ${analysis.overall_progress.toFixed(1)}%`;
                
                if (analysis.strengths && analysis.strengths.length > 0) {
                    explanation += `\n\nKey Strengths: ${analysis.strengths.join(", ")}`;
                }
                
                if (analysis.areas_for_improvement && analysis.areas_for_improvement.length > 0) {
                    explanation += `\n\nAreas for Improvement: ${analysis.areas_for_improvement.join(", ")}`;
                }
            }
            
            this.setText("result-explanation", explanation);

            const badge = document.getElementById("result-badge");
            if (badge) {
                badge.textContent = `${this.lang === "english" ? "Level" : "Antas"} ${this.result.level}`;
                if (this.result.level <= 3) {
                    badge.style.background = "#FEE2E2";
                    badge.style.color = "#991B1B";
                } else if (this.result.level <= 6) {
                    badge.style.background = "#FEF9C3";
                    badge.style.color = "#92400E";
                } else {
                    badge.style.background = "#DCFCE7";
                    badge.style.color = "#065F46";
                }
            }

            const scoresContainer = document.getElementById("tcp-pathway-scores");
            if (scoresContainer) {
                scoresContainer.style.display = "none";
            }

            this.showStep("results");
        } catch (error) {
            console.error('Error completing assessment:', error);
            alert(this.lang === "english" ? 
                "Error completing assessment. Please try again." : 
                "Error sa pagkumpleto ng assessment. Subukan muli.");
        }
    }

    async downloadPDF() {
        try {
            console.log("Starting PDF download...");
            console.log("Current result object:", this.result);
            
            // Validate result object
            if (!this.result || !this.result.mode) {
                alert(this.lang === "english" ? 
                    "No assessment results available. Please complete an assessment first." : 
                    "Walang available na resulta. Kumpletuhin muna ang assessment.");
                return;
            }

            console.log("Sending PDF request for mode:", this.result.mode);
            
            // Show loading indicator
            const downloadBtn = document.getElementById("download-btn");
            const originalText = downloadBtn.textContent;
            downloadBtn.textContent = this.lang === "english" ? "Generating PDF..." : "Ginagawa ang PDF...";
            downloadBtn.disabled = true;

            const res = await fetch("/api/generate_pdf", {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(this.result)
            });

            console.log("PDF response status:", res.status);

            if (!res.ok) {
                const errorText = await res.text();
                console.error("PDF generation failed:", errorText);
                throw new Error(`HTTP error! status: ${res.status} - ${errorText}`);
            }

            const blob = await res.blob();
            console.log("PDF blob size:", blob.size);
            
            if (blob.size === 0) {
                throw new Error("Received empty PDF file");
            }
            
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `MMSU_${this.result.technology_title}_${this.result.mode}_Assessment.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            console.log("PDF download completed successfully");
            
            // Reset button
            downloadBtn.textContent = originalText;
            downloadBtn.disabled = false;
            
        } catch (error) {
            console.error('Error downloading PDF:', error);
            
            // Reset button
            const downloadBtn = document.getElementById("download-btn");
            if (downloadBtn) {
                downloadBtn.textContent = this.lang === "english" ? "Download PDF Report" : "I-download ang PDF";
                downloadBtn.disabled = false;
            }
            
            alert(this.lang === "english" ? 
                `Error downloading PDF: ${error.message}. Please try again.` : 
                `Error sa pag-download ng PDF: ${error.message}. Subukan muli.`);
        }
    }

    showStep(stepId) {
        document.querySelectorAll(".step").forEach(e => e.classList.remove("active"));
        const targetElement = document.getElementById(stepId);
        if (targetElement) {
            targetElement.classList.add("active");
        }
    }

    setText(elementId, text) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
        }
    }

    getValue(elementId) {
        const element = document.getElementById(elementId);
        return element ? element.value.trim() : "";
    }
}

const APP = new AssessmentApp();

document.addEventListener("DOMContentLoaded", () => {
    APP.showStep("language-selection");
});

function selectLanguage(l) { APP.pickLanguage(l); }
function selectMode(m) { APP.pickMode(m); }
function startAssessment() { APP.begin(); }
function answerQuestion(b) { APP.record(b); }
function answerTCPQuestion(score) { APP.recordTCP(score); }
function downloadPDF() { APP.downloadPDF(); }
function resetAssessment() { location.reload(); }
