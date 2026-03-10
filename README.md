# Resume Analyzer RAG 

An intelligent web application that analyzes and scores resumes against job descriptions using Retrieval-Augmented Generation (RAG).

## Features
- **Traditional Frontend Pipeline**: Clean HTML/CSS/JS interface decoupled from the backend.
- **RAG Powered Extraction**: Uses vector embeddings and LLMs to seamlessly extract, format, and score resume information in a single, lightning-fast structured query.
- **Detailed Scoring Matrix**: Grades candidates across skills, experience, education, and keyword matching.

---

##  Project Structure
```text
resume_analyzer_rag/
├── backend/            # FastAPI Backend & RAG Logic
│   ├── config/         # App settings & LLM routing
│   ├── core/           # Parser, Scorer, embedding generation
│   ├── models/         # Database models
│   ├── utils/          # Helper scripts
│   └── main.py         # Entry point for backend
│
├── frontend/           # Vanilla Web Interface
│   ├── index.html      # Main UI
│   ├── styles.css      # Styling component
│   └── app.js          # API consumption
│
├── .env                # API Keys (Not tracked)
└── requirements.txt    # Python dependencies
```

---

##  Getting Started

### 1. Install Dependencies
Make sure you have Python installed, then install the required core packages:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Rename `.env.example` to `.env` (or create a new `.env` file) in the root directory. Add your provider API keys. For example, using Groq:
```env
GROQ_API_KEY=your_groq_api_key_here
DEFAULT_LLM_PROVIDER=groq
```

### 3. Run the Application
Start the FastAPI server directly from the root `resume_analyzer_rag` directory using the provided run script, which automatically activates your virtual environment:
```bash
run.bat
```
*(On Mac/Linux, run `source venv/bin/activate && python backend/main.py`)*

*The backend server will start at `http://localhost:8000` and serves the frontend automatically.*

---

## 🛠️ Usage
1. Navigate to [http://localhost:8000](http://localhost:8000) in your web browser.
2. Upload a candidate's Resume (PDF/DOCX).
3. Fill in the specific Job Description and Requirements.
4. Click **Analyze**. The RAG pipeline will parse the document, ask the LLM to extract all requested data points, compute a visual score breakdown, and present actionable feedback.

---

## ⚙️ Tech Stack
- **Backend**: FastAPI, SQLAlchemy, Uvicorn
- **AI/LLM Core**: LangChain, HuggingFace Embeddings, Groq (or OpenAI/Anthropic/Google variants)
- **Document Extractors**: PyMuPDF, pdfplumber
- **Frontend**: HTML5, Vanilla CSS / JS
