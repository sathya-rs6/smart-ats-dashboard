# Smart ATS Dashboard

An intelligent, AI-powered Applicant Tracking System (ATS) and recruiter dashboard that automatically analyzes, scores, and ranks resumes against job descriptions using Retrieval-Augmented Generation (RAG).

## 🚀 Key Features
- **Modern Recruiter Dashboard**: A rich, interactive React + Vite frontend (`frontend_v2`) designed for HR professionals, featuring analytics, split-screen candidate review, and global rankings.
- **Automatic Background Analysis**: Upload bulk resumes, and the background AI pipeline will automatically score them against all active job descriptions asynchronously.
- **RAG-Powered Extraction & Q&A**: Uses vector embeddings to securely extract candidate data. Includes a built-in AI assistant to query specific candidate experiences ("Did this candidate work with microservices?").
- **Detailed Scoring Matrix**: Grades candidates autonomously across skills, experience, education, and keyword matching.
- **Integrated Email Actions**: Seamlessly send automated interview shortlisting invitations directly from the web interface using SMTP.

---

## 📁 Project Structure
```text
smart_ats_dashboard/
├── backend/            # FastAPI Backend & LLM Logic
│   ├── config/         # App settings (.env bindings)
│   ├── core/           # Parser, Scorer, email services, RAG engine
│   ├── models/         # SQLite Database models & schemas
│   ├── routers/        # JWT Authentication routes
│   └── main.py         # Entry point for backend & background tasks
│
├── frontend_v2/        # Modern React Application
│   ├── src/            # React components (Dashboard, Modals, Rankings)
│   ├── dist/           # Production builds served statically by FastAPI
│   └── vite.config.js  # Vite build configuration
│
├── .env                # App Secrets & API Keys
├── run.bat             # Robust startup macro (Windows)
└── requirements.txt    # Python dependencies
```

---

## 🚀 Getting Started

### 1. Install Backend Dependencies
Make sure you have Python installed, then install the required core packages via pip:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Create a `.env` file in the root directory. Add your LLM provider API keys and optional SMTP details for email capabilities. 
```env
# AI Models
GROQ_API_KEY=your_groq_api_key_here
DEFAULT_LLM_PROVIDER=groq

# Security
SECRET_KEY=your_jwt_secret_key

# Email Sending (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_gmail@gmail.com
SMTP_PASSWORD=your_google_app_password
```

### 3. Build the Frontend (If modifying UI)
The backend natively serves the compiled React app from `frontend_v2/dist`. If you modify React code, rebuild it:
```bash
cd frontend_v2
npm install
npm run build
cd ..
```

### 4. Run the Application
Start the FastAPI server directly from the root directory using the provided macro, which launches backend services and automatically opens the dashboard:
```bash
run.bat
```
*(On Mac/Linux, run `source venv/bin/activate && python backend/main.py`)*

*The application will be universally available at `http://localhost:8000`.*

---

## 🛠️ Usage Workflow
1. **Create Jobs**: Once logged in, click "Create Job" in the dashboard. Define title and requirements (or let the AI extrapolate them).
2. **Bulk Upload Candidates**: Drag and drop PDF or DOCX files.
3. **Passive Rankings**: Behind the scenes, the FastAPI background tasks will extract and structurally score all resumes against existing jobs.
4. **Dashboard Review**: Switch jobs from the upper right to instantly filter the Ranking tables. Select a candidate to open the split-screen UI (original PDF on left, Matrix scores on right).
5. **Shortlist**: Click the "Shortlist" button to magically distribute an invitation email to their parsed email address!

---

## ⚙️ Tech Stack
- **Backend Core**: Python, FastAPI, SQLAlchemy (SQLite)
- **AI/LLM Architecture**: LangChain, HuggingFace Embeddings, Groq/OpenAI, FAISS
- **Document Extractors**: PyMuPDF, pdfplumber
- **Frontend Core**: React 18, Vite, Tailwind CSS, Recharts, Lucide Icons
