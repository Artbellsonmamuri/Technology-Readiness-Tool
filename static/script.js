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

        this.i18n = {
            english: {
                choose_lang: "Choose Your Language",
                select_mode: "Select Assessment Mode",
                trl_desc: "Technology Readiness Level",
                irl_desc: "Investment Readiness Level",
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
            if (this.mode === "TCP") {
                this.tcpQuestions = await res.json();
            } else {
                this.questions = await res.json();
            }
        } catch (error) {
            console.error('Error loading questions:', error);
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

        try {
            const res = await fetch("/api/assess", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            this.result = await res.json();
            this.showTCPResults();
        } catch (error) {
            console.error('Error completing TCP assessment:', error);
        }
    }

    showTCPResults() {
        this.setText("result-level", `Recommended Pathway: ${this.result.recommended_pathway}`);
        this.setText("tech-title-display", this.result.technology_title);
        this.setText("result-explanation", this.result.explanation);

        const badge = document.getElementById("result-badge");
        if (badge) {
            badge.textContent = "TCP Assessment";
            badge.style.background = "#DCFCE7";
            badge.style.color = "#065F46";
        }

        const scoresContainer = document.getElementById("tcp-pathway-scores");
        const scoresList = document.getElementById("pathway-scores-list");
        if (scoresContainer && scoresList) {
            scoresContainer.style.display = "block";
            scoresList.innerHTML = "";
            
            const pathwayScores = this.result.pathway_scores;
            const sortedPathways = Object.entries(pathwayScores).sort((a, b) => b[1] - a[1]);
            
            sortedPathways.forEach(([pathway, score], index) => {
                const scoreItem = document.createElement("div");
                scoreItem.className = "pathway-score-item";
                scoreItem.innerHTML = `<strong>#${index + 1} ${pathway}:</strong> ${score} points`;
                scoresList.appendChild(scoreItem);
            });
        }

        this.showStep("results");
    }

    // Regular TRL/IRL Assessment Methods
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
            this.result = await res.json();

            this.setText("result-level",
                `${this.result.mode} ${(this.lang === "english") ? "Level" : "Antas"} ${this.result.level}`);
            this.setText("tech-title-display", this.result.technology_title);
            this.setText("result-explanation", this.result.explanation);

            const badge = document.getElementById("result-badge");
            if (badge) {
                badge.textContent = `${this.lang === "english" ? "Level" : "Antas"} ${this.result.level}`;
                if (this.result.level <= 3) {
                    badge.style.background = "#F
