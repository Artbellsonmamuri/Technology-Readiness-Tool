class TRLIRLAssessment {
    constructor() {
        this.currentLanguage = '';
        this.currentMode = '';
        this.questions = [];
        this.currentQuestionIndex = 0;
        this.answers = [];
        this.technologyTitle = '';
        this.technologyDescription = '';
        this.translations = {
            english: {
                mode_title: "Select Assessment Mode",
                trl_description: "Technology Readiness Level",
                irl_description: "Investment Readiness Level",
                tech_info_title: "Technology Information",
                title_label: "Technology Title:",
                description_label: "Short Description:",
                start_btn: "Start Assessment",
                questions_title: "Assessment Questions",
                yes_btn: "Yes",
                no_btn: "No",
                results_title: "Assessment Results",
                download_btn: "Download PDF Report",
                restart_btn: "Start New Assessment"
            },
            filipino: {
                mode_title: "Pumili ng Uri ng Assessment",
                trl_description: "Technology Readiness Level",
                irl_description: "Investment Readiness Level",
                tech_info_title: "Impormasyon ng Teknolohiya",
                title_label: "Pamagat ng Teknolohiya:",
                description_label: "Maikling Paglalarawan:",
                start_btn: "Simulan ang Assessment",
                questions_title: "Mga Tanong sa Assessment",
                yes_btn: "Oo",
                no_btn: "Hindi",
                results_title: "Mga Resulta ng Assessment",
                download_btn: "I-download ang PDF Report",
                restart_btn: "Magsimula ng Bagong Assessment"
            }
        };
    }

    selectLanguage(language) {
        this.currentLanguage = language;
        this.updateLanguage();
        this.showStep('mode-selection');
    }

    updateLanguage() {
        const t = this.translations[this.currentLanguage];
        document.getElementById('mode-title').textContent = t.mode_title;
        document.getElementById('trl-description').textContent = t.trl_description;
        document.getElementById('irl-description').textContent = t.irl_description;
        document.getElementById('tech-info-title').textContent = t.tech_info_title;
        document.getElementById('title-label').textContent = t.title_label;
        document.getElementById('description-label').textContent = t.description_label;
        document.getElementById('start-btn').textContent = t.start_btn;
        document.getElementById('questions-title').textContent = t.questions_title;
        document.getElementById('yes-btn').textContent = t.yes_btn;
        document.getElementById('no-btn').textContent = t.no_btn;
        document.getElementById('results-title').textContent = t.results_title;
        document.getElementById('download-btn').textContent = t.download_btn;
        document.getElementById('restart-btn').textContent = t.restart_btn;
    }

    selectMode(mode) {
        this.currentMode = mode;
        this.showStep('tech-info');
    }

    showStep(stepId) {
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active');
        });
        document.getElementById(stepId).classList.add('active');
    }

    async startAssessment() {
        this.technologyTitle = document.getElementById('tech-title').value;
        this.technologyDescription = document.getElementById('tech-description').value;
        
        if (!this.technologyTitle || !this.technologyDescription) {
            alert(this.currentLanguage === 'english' ? 
                'Please fill in all fields' : 
                'Pakipunan ang lahat ng field');
            return;
        }

        await this.loadQuestions();
        this.currentQuestionIndex = 0;
        this.answers = [];
        this.showQuestion();
        this.showStep('questions');
    }

    async loadQuestions() {
        try {
            const response = await fetch(`/api/questions/${this.currentMode}/${this.currentLanguage}`);
            this.questions = await response.json();
        } catch (error) {
            console.error('Error loading questions:', error);
        }
    }

    showQuestion() {
        if (this.currentQuestionIndex < this.questions.length) {
            const question = this.questions[this.currentQuestionIndex];
            document.getElementById('question-text').textContent = question.question;
            document.getElementById('question-description').textContent = question.description;
            
            const progress = ((this.currentQuestionIndex + 1) / this.questions.length) * 100;
            document.getElementById('progress').style.width = progress + '%';
            document.getElementById('progress-text').textContent = 
                `${this.currentLanguage === 'english' ? 'Question' : 'Tanong'} ${this.currentQuestionIndex + 1} ${this.currentLanguage === 'english' ? 'of' : 'ng'} ${this.questions.length}`;
        }
    }

    answerQuestion(answer) {
        this.answers.push(answer);
        
        if (!answer || this.currentQuestionIndex === this.questions.length - 1) {
            this.completeAssessment();
        } else {
            this.currentQuestionIndex++;
            this.showQuestion();
        }
    }

    async completeAssessment() {
        const assessmentData = {
            mode: this.currentMode,
            language: this.currentLanguage,
            technology_title: this.technologyTitle,
            description: this.technologyDescription,
            answers: this.answers
        };

        try {
            const response = await fetch('/api/assess', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(assessmentData)
            });

            this.result = await response.json();
            this.showResults();
        } catch (error) {
            console.error('Error completing assessment:', error);
        }
    }

    showResults() {
        document.getElementById('result-level').textContent = 
            `${this.result.mode} ${this.currentLanguage === 'english' ? 'Level' : 'Antas'} ${this.result.level}`;
        
        document.getElementById('tech-title-display').textContent = this.result.technology_title;
        document.getElementById('result-explanation').textContent = this.result.explanation;
        
        // Set badge color based on level
        const badge = document.getElementById('result-badge');
        badge.textContent = `${this.currentLanguage === 'english' ? 'Level' : 'Antas'} ${this.result.level}`;
        
        if (this.result.level <= 3) {
            badge.style.background = '#fed7d7';
            badge.style.color = '#c53030';
        } else if (this.result.level <= 6) {
            badge.style.background = '#fef2de';
            badge.style.color = '#dd6b20';
        } else {
            badge.style.background = '#c6f6d5';
            badge.style.color = '#2f855a';
        }
        
        this.showStep('results');
    }

    async downloadPDF() {
        try {
            const response = await fetch('/api/generate_pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.result)
            });

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `${this.result.technology_title}_${this.result.mode}_Assessment.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error downloading PDF:', error);
        }
    }

    resetAssessment() {
        this.currentLanguage = '';
        this.currentMode = '';
        this.questions = [];
        this.currentQuestionIndex = 0;
        this.answers = [];
        this.technologyTitle = '';
        this.technologyDescription = '';
        document.getElementById('tech-title').value = '';
        document.getElementById('tech-description').value = '';
        this.showStep('language-selection');
    }
}

// Global instance
const assessment = new TRLIRLAssessment();

// Global functions for HTML onclick events
function selectLanguage(language) {
    assessment.selectLanguage(language);
}

function selectMode(mode) {
    assessment.selectMode(mode);
}

function startAssessment() {
    assessment.startAssessment();
}

function answerQuestion(answer) {
    assessment.answerQuestion(answer);
}

function downloadPDF() {
    assessment.downloadPDF();
}

function resetAssessment() {
    assessment.resetAssessment();
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', function() {
    assessment.showStep('language-selection');
});
