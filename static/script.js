class AssessmentApp {
    constructor() {
        this.lang = "";
        this.mode = "";
        this.questions = [];
        this.answers = [];
        this.lix = 0; // current level index
        this.cix = 0; // current check index

        this.i18n = {
            english: {
                choose_lang: "Choose Your Language",
                select_mode: "Select Assessment Mode",
                trl_desc: "Technology Readiness Level",
                irl_desc: "Investment Readiness Level",
                tech_info: "Technology Information",
                title_lbl: "Technology Title:",
                desc_lbl: "Short Description:",
                start: "Start Assessment",
                q_title: "Assessment Questions",
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
                tech_info: "Impormasyon ng Teknolohiya",
                title_lbl: "Pamagat ng Teknolohiya:",
                desc_lbl: "Maikling Paglalarawan:",
                start: "Simulan ang Assessment",
                q_title: "Mga Tanong sa Assessment",
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
            this.present();
        }
    }

    respond(ans) {
        this.record(ans);
    }

    reset() {
        location.reload();
    }

    download() {
        this.downloadPDF();
    }

    translate() {
        const t = this.i18n[this.lang];
        this.setText("mode-title", t.select_mode);
        this.setText("trl-description", t.trl_desc);
        this.setText("irl-description", t.irl_desc);
        this.setText("tech-info-title", t.tech_info);
        this.setText("title-label", t.title_lbl);
        this.setText("description-label", t.desc_lbl);
        this.setText("start-btn", t.start);
        this.setText("questions-title", t.q_title);
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
            this.questions = await res.json();
        } catch (error) {
            console.error('Error loading questions:', error);
        }
    }

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

            this.showStep("results");
        } catch (error) {
            console.error('Error completing assessment:', error);
        }
    }

    async downloadPDF() {
        try {
            const res = await fetch("/api/generate_pdf", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(this.result)
            });
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `MMSU_${this.result.technology_title}_${this.result.mode}_Assessment.pdf`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error downloading PDF:', error);
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
function answerQuestion(b) { APP.respond(b); }
function downloadPDF() { APP.download(); }
function resetAssessment() { APP.reset(); }
