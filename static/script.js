class AssessmentApp {
    constructor() {
        this.lang      = "";
        this.mode      = "";
        this.questions = [];
        this.answers   = [];    // nested answers
        this.lix       = 0;     // current level index
        this.cix       = 0;     // current check index

        this.i18n = {
            english: {
                choose_lang: "Choose Your Language",
                select_mode: "Select Assessment Mode",
                trl_desc: "Technology Readiness Level",
                irl_desc: "Investment Readiness Level",
                tech_info: "Technology Information",
                title_lbl: "Technology Title:",
                desc_lbl : "Short Description:",
                start    : "Start Assessment",
                q_title  : "Assessment Questions",
                yes      : "Yes",
                no       : "No",
                results  : "Assessment Results",
                download : "Download PDF Report",
                restart  : "Start New Assessment"
            },
            filipino: {
                choose_lang: "Pumili ng Wika",
                select_mode: "Pumili ng Uri ng Assessment",
                trl_desc: "Technology Readiness Level",
                irl_desc: "Investment Readiness Level",
                tech_info: "Impormasyon ng Teknolohiya",
                title_lbl: "Pamagat ng Teknolohiya:",
                desc_lbl : "Maikling Paglalarawan:",
                start    : "Simulan ang Assessment",
                q_title  : "Mga Tanong sa Assessment",
                yes      : "Oo",
                no       : "Hindi",
                results  : "Mga Resulta",
                download : "I-download ang PDF",
                restart  : "Magsimula Muli"
            }
        };
    }

    // ---------------- PUBLIC ENTRY POINTS called from HTML ----------------
    pickLanguage(code)   { this.lang = code;  this.translate(); show("mode"); }
    pickMode(m)          { this.mode = m;     show("tech"); }
    async begin()        { if (this.collectInfo()) { await this.fetchQuestions(); this.present(); } }
    respond(ans)         { this.record(ans); }
    reset()              { location.reload(); }
    download()           { this.downloadPDF(); }

    // ---------------- INTERNAL WORKFLOW ----------------
    translate() {
        const t = this.i18n[this.lang];
        text("mode-title",  t.select_mode);
        text("trl-description", t.trl_desc);
        text("irl-description", t.irl_desc);
        text("tech-info-title", t.tech_info);
        text("title-label", t.title_lbl);
        text("description-label", t.desc_lbl);
        text("start-btn", t.start);
        text("questions-title", t.q_title);
        text("yes-btn", t.yes);
        text("no-btn",  t.no);
        text("results-title", t.results);
        text("download-btn", t.download);
        text("restart-btn",  t.restart);
    }

    collectInfo() {
        this.title = val("tech-title");
        this.desc  = val("tech-description");
        if (!this.title || !this.desc) {
            alert(this.lang==="english" ? "Fill in all fields" : "Pakipunan ang lahat ng field");
            return false;
        }
        return true;
    }

    async fetchQuestions() {
        const res = await fetch(`/api/questions/${this.mode}/${this.lang}`);
        this.questions = await res.json();
    }

    present() {
        this.lix = 0; this.cix = 0; this.answers = [];
        show("questions");
        this.renderCheck();
    }

    renderCheck() {
        const lvl   = this.questions[this.lix];
        const qtext = lvl.checks[this.cix];
        text("question-text", qtext);
        text("question-description", `${lvl.title} — ${this.cix + 1}/${lvl.checks.length}`);
        const done   = this.answers.flat().length;
        const total  = this.questions.reduce((s,l)=>s+l.checks.length,0);
        id("progress").style.width = `${Math.round(done / total * 100)}%`;
        text("progress-text",
             `${this.lang==="english"?"Check":"Tanong"} ${done+1} / ${total}`);
    }

    record(ans) {
        if (!this.answers[this.lix]) this.answers[this.lix]=[];
        this.answers[this.lix].push(ans);

        if (!ans) { return this.finish(); }

        const lvl = this.questions[this.lix];
        if (this.cix + 1 < lvl.checks.length) {
            this.cix++;
        } else {                   // level complete
            this.lix++; this.cix = 0;
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
        const res = await fetch("/api/assess", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        this.result = await res.json();
        text("result-level",
             `${this.result.mode} ${(this.lang==="english")?"Level":"Antas"} ${this.result.level}`);
        text("tech-title-display", this.result.technology_title);
        text("result-explanation", this.result.explanation);
        const badge = id("result-badge");
        badge.textContent = `${this.lang==="english"?"Level":"Antas"} ${this.result.level}`;
        badge.style.background = this.result.level<=3?"#FEE2E2":this.result.level<=6?"#FEF9C3":"#DCFCE7";
        badge.style.color      = this.result.level<=3?"#991B1B":this.result.level<=6?"#92400E":"#065F46";
        show("results");
    }

    async downloadPDF() {
        const res  = await fetch("/api/generate_pdf", {
            method:"POST", headers:{"Content-Type":"application/json"},
            body:JSON.stringify(this.result)
        });
        const blob = await res.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement("a");
        a.href = url; a.download = `${this.result.technology_title}_${this.result.mode}.pdf`;
        a.click(); URL.revokeObjectURL(url);
    }
}

// -------------- Helper DOM functions --------------
const id   = s=>document.getElementById(s);
const text = (s,v)=>{ id(s).textContent=v; };
const val  = s=>id(s).value.trim();
function show(step){
    document.querySelectorAll(".step").forEach(e=>e.classList.remove("active"));
    id(`${step}-selection`)?.classList.add("active")||
    id(step).classList.add("active");
}

// -------------- Bootstrap on load --------------
const APP = new AssessmentApp();
document.addEventListener("DOMContentLoaded",()=>show("language"));

function selectLanguage(l){APP.pickLanguage(l);}
function selectMode(m){APP.pickMode(m);}
function startAssessment(){APP.begin();}
function answerQuestion(b){APP.respond(b);}
function downloadPDF(){APP.download();}
function resetAssessment(){APP.reset();}
