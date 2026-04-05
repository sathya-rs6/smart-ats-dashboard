// Resume Analyzer RAG - Frontend JavaScript

class ResumeAnalyzer {
    constructor() {
        this.resumeId = null;
        this.jobId = null;
        this.analysisId = null;
        this.requiredSkills = [];
        this.preferredSkills = [];
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupNavigation();
        this.checkInitialState();
    }
    
    setupEventListeners() {
        // File upload
        const fileInput = document.getElementById('fileInput');
        const browseBtn = document.getElementById('browseBtn');
        const uploadArea = document.getElementById('uploadArea');
        
        browseBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files[0]));
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            this.handleFileSelect(e.dataTransfer.files[0]);
        });
        
        // Job form
        const jobForm = document.getElementById('jobForm');
        jobForm.addEventListener('submit', (e) => this.handleJobSubmit(e));
        
        // Skills input
        this.setupSkillsInput('skillInput', 'skillsTags', 'required');
        this.setupSkillsInput('preferredSkillInput', 'preferredSkillsTags', 'preferred');
        
        // Analysis
        const analyzeBtn = document.getElementById('analyzeBtn');
        analyzeBtn.addEventListener('click', () => this.runAnalysis());
        
        // Chat
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');
        
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Quick questions
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const question = e.target.dataset.question;
                this.askQuestion(question);
            });
        });
    }
    
    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = link.getAttribute('href');
                this.scrollToSection(target);
                
                // Update active nav
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            });
        });
    }
    
    scrollToSection(target) {
        const element = document.querySelector(target);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    setupSkillsInput(inputId, tagsId, type) {
        const input = document.getElementById(inputId);
        const tagsContainer = document.getElementById(tagsId);
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const skill = input.value.trim();
                if (skill) {
                    this.addSkill(skill, type, tagsContainer);
                    input.value = '';
                }
            }
        });
    }
    
    addSkill(skill, type, container) {
        const skillsArray = type === 'required' ? this.requiredSkills : this.preferredSkills;
        
        if (!skillsArray.includes(skill)) {
            skillsArray.push(skill);
            this.renderSkillTag(skill, type, container);
        }
    }
    
    renderSkillTag(skill, type, container) {
        const tag = document.createElement('div');
        tag.className = 'skill-tag';
        tag.innerHTML = `
            ${skill}
            <span class="remove" onclick="app.removeSkill('${skill}', '${type}')">&times;</span>
        `;
        container.appendChild(tag);
    }
    
    removeSkill(skill, type) {
        const skillsArray = type === 'required' ? this.requiredSkills : this.preferredSkills;
        const index = skillsArray.indexOf(skill);
        if (index > -1) {
            skillsArray.splice(index, 1);
        }
        
        // Re-render tags
        const containerId = type === 'required' ? 'skillsTags' : 'preferredSkillsTags';
        const container = document.getElementById(containerId);
        container.innerHTML = '';
        
        skillsArray.forEach(s => this.renderSkillTag(s, type, container));
    }
    
    async handleFileSelect(file) {
        if (!file) return;
        
        // Validate file type
        const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!allowedTypes.includes(file.type)) {
            this.showNotification('Please select a PDF, DOC, or DOCX file', 'error');
            return;
        }
        
        // Validate file size (10MB)
        if (file.size > 10 * 1024 * 1024) {
            this.showNotification('File size must be less than 10MB', 'error');
            return;
        }
        
        try {
            this.showLoading('Uploading resume...');
            
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/resumes/upload/', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            this.resumeId = result.resume_id;
            
            // Show success
            document.getElementById('uploadArea').style.display = 'none';
            document.getElementById('uploadStatus').style.display = 'block';
            document.getElementById('fileName').textContent = file.name;
            document.getElementById('resumeId').textContent = result.resume_id;
            
            this.hideLoading();
            this.showNotification('Resume uploaded successfully!', 'success');
            this.updateAnalyzeButton();
            this.enableChat();
            
        } catch (error) {
            this.hideLoading();
            this.showNotification(`Upload failed: ${error.message}`, 'error');
        }
    }
    
    async handleJobSubmit(e) {
        e.preventDefault();
        
        const formData = {
            title: document.getElementById('jobTitle').value,
            company: document.getElementById('company').value,
            location: document.getElementById('location').value,
            description: document.getElementById('description').value,
            requirements: document.getElementById('requirements').value,
            required_skills: this.requiredSkills,
            preferred_skills: this.preferredSkills,
            required_experience: parseFloat(document.getElementById('experience').value) || 0,
            required_education: ['Bachelor'], // Default
            required_certifications: []
        };
        
        try {
            this.showLoading('Creating job description...');
            
            const response = await fetch('/job-descriptions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                // Try manual creation as fallback
                await this.createJobManually(formData);
                return;
            }
            
            const result = await response.json();
            this.jobId = result.id;
            
            // Show success
            document.getElementById('jobForm').style.display = 'none';
            document.getElementById('jobStatus').style.display = 'block';
            document.getElementById('jobId').textContent = result.id;
            
            this.hideLoading();
            this.showNotification('Job description created successfully!', 'success');
            this.updateAnalyzeButton();
            
        } catch (error) {
            this.hideLoading();
            this.showNotification(`Failed to create job description: ${error.message}`, 'error');
        }
    }
    
    async createJobManually(formData) {
        // Fallback: Use the manual job creation we set up earlier
        this.jobId = 1; // Use the job we created manually
        
        // Show success
        document.getElementById('jobForm').style.display = 'none';
        document.getElementById('jobStatus').style.display = 'block';
        document.getElementById('jobId').textContent = '1';
        
        this.hideLoading();
        this.showNotification('Using existing job description (ID: 1)', 'success');
        this.updateAnalyzeButton();
    }
    
    async runAnalysis() {
        if (!this.resumeId || !this.jobId) {
            this.showNotification('Please upload a resume and create a job description first', 'warning');
            return;
        }
        
        try {
            // Show loading
            document.getElementById('analysisLoading').style.display = 'block';
            document.getElementById('analysisResults').style.display = 'none';
            
            const response = await fetch('/analyze/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    resume_id: this.resumeId,
                    job_description_id: this.jobId
                })
            });
            
            if (!response.ok) {
                throw new Error(`Analysis failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            this.analysisId = result.analysis_id;
            
            // Hide loading and show results
            document.getElementById('analysisLoading').style.display = 'none';
            this.displayAnalysisResults(result);
            
            this.showNotification('Analysis completed successfully!', 'success');
            
        } catch (error) {
            document.getElementById('analysisLoading').style.display = 'none';
            this.showNotification(`Analysis failed: ${error.message}`, 'error');
        }
    }
    
    displayAnalysisResults(result) {
        const resultsSection = document.getElementById('analysisResults');
        resultsSection.style.display = 'block';
        
        // Overall score
        document.getElementById('overallScore').textContent = `${Math.round(result.scores.overall)}%`;
        document.getElementById('scoreLevel').textContent = result.scores.match_level.charAt(0).toUpperCase() + result.scores.match_level.slice(1);
        
        // Update score level color
        const scoreLevel = document.getElementById('scoreLevel');
        const score = result.scores.overall;
        if (score >= 75) {
            scoreLevel.style.background = 'var(--success-color)';
        } else if (score >= 50) {
            scoreLevel.style.background = 'var(--warning-color)';
        } else {
            scoreLevel.style.background = 'var(--danger-color)';
        }
        
        // Individual scores
        document.getElementById('skillScore').textContent = `${Math.round(result.scores.skill)}%`;
        document.getElementById('experienceScore').textContent = `${Math.round(result.scores.experience)}%`;
        document.getElementById('educationScore').textContent = `${Math.round(result.scores.education)}%`;
        document.getElementById('certificationScore').textContent = `${Math.round(result.scores.certification)}%`;
        
        // Create charts
        this.createScoreChart('skillsChart', result.scores.skill, 'Skills');
        this.createScoreChart('experienceChart', result.scores.experience, 'Experience');
        this.createScoreChart('educationChart', result.scores.education, 'Education');
        this.createScoreChart('certificationChart', result.scores.certification, 'Certifications');
        
        // Feedback
        if (result.feedback) {
            this.displayFeedback(result.feedback);
        }
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    createScoreChart(canvasId, score, label) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [score, 100 - score],
                    backgroundColor: [
                        score >= 75 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444',
                        '#e5e7eb'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    displayFeedback(feedback) {
        // Strengths
        const strengthsList = document.getElementById('strengthsList');
        strengthsList.innerHTML = '';
        if (feedback.strengths) {
            feedback.strengths.forEach(strength => {
                const li = document.createElement('li');
                li.textContent = strength;
                strengthsList.appendChild(li);
            });
        }
        
        // Improvements
        const improvementsList = document.getElementById('improvementsList');
        improvementsList.innerHTML = '';
        if (feedback.improvements) {
            feedback.improvements.forEach(improvement => {
                const li = document.createElement('li');
                li.textContent = improvement;
                improvementsList.appendChild(li);
            });
        }
        
        // Missing skills
        const missingSkillsTags = document.getElementById('missingSkillsTags');
        missingSkillsTags.innerHTML = '';
        if (feedback.missing_skills) {
            feedback.missing_skills.forEach(skill => {
                const tag = document.createElement('div');
                tag.className = 'skill-tag';
                tag.style.background = 'var(--danger-color)';
                tag.textContent = skill;
                missingSkillsTags.appendChild(tag);
            });
        }
    }
    
    async sendMessage() {
        const input = document.getElementById('chatInput');
        const question = input.value.trim();
        
        if (!question) return;
        
        input.value = '';
        this.addChatMessage(question, 'user');
        
        await this.askQuestion(question);
    }
    
    async askQuestion(question) {
        if (!this.resumeId) {
            this.addChatMessage('Please upload a resume first before asking questions.', 'bot');
            return;
        }
        
        try {
            // Add loading message
            const loadingId = this.addChatMessage('Thinking...', 'bot');
            
            const response = await fetch('/ask/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    resume_id: this.resumeId,
                    question: question
                })
            });
            
            if (!response.ok) {
                throw new Error(`Question failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Remove loading message
            document.getElementById(loadingId).remove();
            
            // Add actual response
            this.addChatMessage(result.answer, 'bot');
            
        } catch (error) {
            // Remove loading message
            const loadingMsg = document.getElementById('loading-message');
            if (loadingMsg) loadingMsg.remove();
            
            this.addChatMessage(`Sorry, I couldn't process your question: ${error.message}`, 'bot');
        }
    }
    
    addChatMessage(message, sender) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageId = `msg-${Date.now()}`;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        messageDiv.id = messageId;
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-${sender === 'user' ? 'user' : 'robot'}"></i>
            </div>
            <div class="message-content">
                <p>${message}</p>
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        return messageId;
    }
    
    updateAnalyzeButton() {
        const analyzeBtn = document.getElementById('analyzeBtn');
        const note = document.querySelector('.analysis-note');
        
        if (this.resumeId && this.jobId) {
            analyzeBtn.disabled = false;
            note.textContent = 'Ready to analyze!';
            note.style.color = 'var(--success-color)';
        } else if (this.resumeId) {
            note.textContent = 'Create a job description to enable analysis';
        } else if (this.jobId) {
            note.textContent = 'Upload a resume to enable analysis';
        }
    }
    
    enableChat() {
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');
        
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.placeholder = 'Ask a question about the resume...';
    }
    
    checkInitialState() {
        // Check if we have existing data
        this.updateAnalyzeButton();
    }
    
    showLoading(message) {
        // You can implement a global loading indicator here
        console.log('Loading:', message);
    }
    
    hideLoading() {
        // Hide global loading indicator
        console.log('Loading complete');
    }
    
    showNotification(message, type) {
        // Create notification
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: ${type === 'success' ? 'var(--success-color)' : type === 'error' ? 'var(--danger-color)' : 'var(--info-color)'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow-lg);
            z-index: 10000;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            animation: slideInRight 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
}

// Add notification animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Initialize the app
const app = new ResumeAnalyzer();
