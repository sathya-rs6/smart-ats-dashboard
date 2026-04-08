"""
Resume Analyzer with RAG (Retrieval-Augmented Generation)
Combines the best features from both uploaded projects into a unified system.
"""

import os
import warnings
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Suppress warnings
warnings.filterwarnings('ignore')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import configuration
from config.settings import settings

# Set up logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import core dependencies
try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_huggingface.embeddings import HuggingFaceEmbeddings
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser

    # Vector stores
    if settings.vector_store_type == "weaviate":
        import weaviate
        from weaviate.classes.init import Auth
        from langchain_weaviate.vectorstores import WeaviateVectorStore
    elif settings.vector_store_type == "chroma":
        import chromadb
        try:
            from langchain_chroma import Chroma
        except ImportError:
            from langchain_community.vectorstores import Chroma
    elif settings.vector_store_type == "faiss":
        from langchain_community.vectorstores import FAISS

    # LLM providers
    if settings.default_llm_provider == "openai":
        from langchain_openai import ChatOpenAI
    elif settings.default_llm_provider == "groq":
        from langchain_groq import ChatGroq
    elif settings.default_llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
    elif settings.default_llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

except ImportError as e:
    logger.error(f"Failed to import required packages: {e}")
    logger.info("Please run: pip install -r requirements.txt")
    raise


class ResumeAnalyzer:
    """Main resume analyzer class with RAG capabilities"""

    _embeddings_cache = None

    def __init__(self):
        self.vector_store = None
        self.llm = None
        self.retriever = None
        self.chain = None
        self.docs = None  # Store processed documents

        # Initialize components (embeddings are lazy loaded)
        self._initialize_llm()
        self._initialize_vector_store()

    @property
    def embeddings(self):
        """Lazy loader for embeddings model"""
        if ResumeAnalyzer._embeddings_cache is None:
            self._initialize_embeddings()
        return ResumeAnalyzer._embeddings_cache

    def _initialize_embeddings(self):
        """Initialize the embedding model"""
        try:
            logger.info("Initializing embeddings model (this may take a moment)...")
            ResumeAnalyzer._embeddings_cache = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                cache_folder="models/hf_cache"
            )
            logger.info("Embeddings model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            raise

    def _initialize_llm(self):
        """Initialize the LLM based on configuration"""
        try:
            if settings.default_llm_provider == "openai":
                if not settings.openai_api_key:
                    raise ValueError("OpenAI API key not found")
                self.llm = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    temperature=settings.llm_temperature,
                    max_tokens=settings.max_tokens,
                    openai_api_key=settings.openai_api_key
                )
            elif settings.default_llm_provider == "groq":
                if not settings.groq_api_key:
                    raise ValueError("Groq API key not found")
                self.llm = ChatGroq(
                    model="llama-3.1-8b-instant",
                    temperature=settings.llm_temperature,
                    max_tokens=settings.max_tokens,
                    groq_api_key=settings.groq_api_key
                )
            elif settings.default_llm_provider == "google":
                if not settings.google_api_key:
                    raise ValueError("Google API key not found")
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-pro",
                    temperature=settings.llm_temperature,
                    max_tokens=settings.max_tokens,
                    google_api_key=settings.google_api_key
                )
            elif settings.default_llm_provider == "anthropic":
                if not settings.anthropic_api_key:
                    raise ValueError("Anthropic API key not found")
                self.llm = ChatAnthropic(
                    model="claude-3-sonnet-20240229",
                    temperature=settings.llm_temperature,
                    max_tokens=settings.max_tokens,
                    anthropic_api_key=settings.anthropic_api_key
                )

            logger.info(f"LLM ({settings.default_llm_provider}) initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

    def _initialize_vector_store(self):
        """Initialize the vector store based on configuration"""
        try:
            if settings.vector_store_type == "weaviate":
                if not settings.weaviate_url or not settings.weaviate_api_key:
                    raise ValueError("Weaviate credentials not found")

                client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=settings.weaviate_url,
                    auth_credentials=Auth.api_key(settings.weaviate_api_key)
                )

                if not client.is_ready():
                    raise ConnectionError("Weaviate client not ready")

                logger.info("Weaviate client connected successfully")

            elif settings.vector_store_type == "chroma":
                # Initialize ChromaDB
                persist_directory = Path(settings.chroma_persist_directory)
                persist_directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"ChromaDB directory: {persist_directory}")

            elif settings.vector_store_type == "faiss":
                logger.info("FAISS vector store selected")

            logger.info(f"Vector store ({settings.vector_store_type}) initialized")

        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise

    def load_and_process_resume(self, file_path: str) -> List[Any]:
        """Load and process a resume PDF file"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Resume file not found: {file_path}")

            # Load PDF
            logger.info(f"Loading resume from: {file_path}")
            loader = PyPDFLoader(file_path)
            pages = loader.load()

            if not pages:
                raise ValueError("No content found in resume")

            logger.info(f"Loaded {len(pages)} pages from resume")

            # Split into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap
            )

            docs = text_splitter.split_documents(pages)
            logger.info(f"Created {len(docs)} chunks from resume")

            # Store docs as instance variable
            self.docs = docs
            return docs

        except Exception as e:
            logger.error(f"Failed to load and process resume: {e}")
            raise

    def create_vector_store(self, docs: List[Any], collection_name: str = "resume_collection"):
        """Create vector store from resume chunks"""
        try:
            if settings.vector_store_type == "weaviate":
                # For demo purposes, we'll create an in-memory store
                # In production, this would use the Weaviate cloud instance
                from langchain_community.vectorstores import FAISS
                self.vector_store = FAISS.from_documents(docs, self.embeddings)

            elif settings.vector_store_type == "chroma":
                persist_directory = Path(settings.chroma_persist_directory)
                self.vector_store = Chroma.from_documents(
                    docs,
                    self.embeddings,
                    persist_directory=str(persist_directory),
                    collection_name=collection_name
                )

            elif settings.vector_store_type == "faiss":
                self.vector_store = FAISS.from_documents(docs, self.embeddings)

            # Create retriever
            self.retriever = self.vector_store.as_retriever(
                search_kwargs={"k": 4}
            )

            logger.info("Vector store and retriever created successfully")

        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            raise

    def create_qa_chain(self):
        """Create the question-answering chain"""
        try:
            # Create prompt template
            template = """You are an intelligent resume analyzer. Use the following pieces of resume context to answer questions accurately and comprehensively.

If you don't know the answer based on the context, say "I don't have enough information to answer this question" rather than making up information.

Provide detailed, specific answers based only on the resume content provided.

Question: {question}
Context: {context}

Answer:"""

            prompt = ChatPromptTemplate.from_template(template)

            # Create the chain
            self.chain = (
                {"context": self.retriever, "question": RunnablePassthrough()}
                | prompt
                | self.llm
                | StrOutputParser()
            )

            logger.info("QA chain created successfully")

        except Exception as e:
            logger.error(f"Failed to create QA chain: {e}")
            raise

    def ask_question(self, question: str) -> str:
        """Ask a question about the resume"""
        try:
            if not self.chain:
                raise ValueError("QA chain not initialized. Call create_qa_chain() first.")

            logger.info(f"Processing question: {question}")
            result = self.chain.invoke(question)

            return result

        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            return f"Error processing question: {str(e)}"

    def analyze_resume_comprehensive(self, resume_path: str) -> Dict[str, Any]:
        """Comprehensive resume analysis with scoring"""
        import json
        try:
            # Load and process resume
            docs = self.load_and_process_resume(resume_path)

            # Create vector store
            self.create_vector_store(docs)

            # Create QA chain
            self.create_qa_chain()

            # Perform comprehensive analysis in a single LLM call for speed
            logger.info("Executing single batch prompt for comprehensive analysis...")
            
            # The prompt requires returning a JSON object with the keys the UI expects
            batch_question = (
                "Extract and summarize the following information from the resume. "
                "You MUST return the output ONLY as a valid JSON object with the exact keys below. "
                "Do not include markdown blocks, just the raw JSON.\n\n"
                "Keys to include:\n"
                "- 'Extract all personal information including name, contact details, and location': (string value)\n"
                "- 'What is the candidate\\'s educational background?': (string value)\n"
                "- 'List all work experience with company names, positions, and dates': (string value)\n"
                "- 'What technical skills does the candidate have?': (string value)\n"
                "- 'List all projects the candidate has worked on': (string value)\n"
                "- 'What certifications does the candidate hold?': (string value)\n"
                "- 'Summarize the candidate\\'s professional summary or objective': (string value)\n"
                "- 'Rate this resume on a scale of 1-100 based on clarity, completeness, and professional presentation': (string value)"
            )
            
            answer = self.ask_question(batch_question)
            
            # Try to safely parse the JSON output
            try:
                # Clean up any potential markdown formatting the LLM might have added
                cleaned_answer = answer.strip()
                if cleaned_answer.startswith("```json"):
                    cleaned_answer = cleaned_answer[7:]
                elif cleaned_answer.startswith("```"):
                    cleaned_answer = cleaned_answer[3:]
                if cleaned_answer.endswith("```"):
                    cleaned_answer = cleaned_answer[:-3]
                    
                analysis = json.loads(cleaned_answer.strip())
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM JSON response: {e}. Falling back to raw text.")
                # Fallback to just providing the raw text if parsing fails
                analysis = {
                    "Raw Analysis Result": answer,
                    "Error": "The model failed to return structured JSON. Showing raw output."
                }

            return analysis

        except Exception as e:
            logger.error(f"Failed to perform comprehensive analysis: {e}")
            return {"error": str(e)}

    def analyze_job_description(self, jd_text: str) -> Dict[str, Any]:
        """Extract structured requirements from a job description text using LLM"""
        import json
        try:
            logger.info("Extracting structured requirements from job description...")
            
            prompt_template = """You are an expert HR recruiter assistant. Extract structured requirements from the following job description.
            
            Return the result ONLY as a valid JSON object with the following keys.
            Do not include markdown blocks, just the raw JSON.
            
            Keys:
            - 'title': (string)
            - 'required_skills': (list of strings)
            - 'preferred_skills': (list of strings)
            - 'required_experience': (float value in years)
            - 'required_education': (list of strings like 'Bachelor', 'Master', etc.)
            - 'required_certifications': (list of strings)
            - 'key_responsibilities': (list of strings)
            
            Job Description:
            {jd_text}
            """
            
            prompt = prompt_template.format(jd_text=jd_text)
            
            # Using the existing LLM instance
            if not self.llm:
                self._initialize_llm()
            
            response = self.llm.invoke(prompt)
            content = response.content
            
            # Clean up and parse JSON
            cleaned_content = content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            elif cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
                
            try:
                structured_jd = json.loads(cleaned_content.strip())
                return structured_jd
            except json.JSONDecodeError:
                logger.error("Failed to parse JD extraction JSON. Returning raw content.")
                return {"error": "Failed to parse JSON", "raw": content}

        except Exception as e:
            logger.error(f"Error analyzing job description: {e}")
            return {"error": str(e)}


def main():
    """Main function for command-line usage"""
    print("🚀 Resume Analyzer RAG System")
    print("=" * 50)

    # Get resume file path
    resume_path = input("Enter the path to the resume PDF file: ").strip()

    if not os.path.exists(resume_path):
        print(f"❌ Error: Resume file not found at {resume_path}")
        return

    # Initialize analyzer
    try:
        analyzer = ResumeAnalyzer()
        print("✅ Analyzer initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize analyzer: {e}")
        return

    # Analyze resume
    print(f"\n📄 Analyzing resume: {resume_path}")
    analysis = analyzer.analyze_resume_comprehensive(resume_path)

    if "error" in analysis:
        print(f"❌ Analysis failed: {analysis['error']}")
        return

    # Display results
    print("\n🎯 Analysis Results:")
    print("=" * 50)

    for question, answer in analysis.items():
        print(f"\n❓ {question}")
        print(f"💡 {answer[:200]}{'...' if len(answer) > 200 else ''}")

    print("\n✅ Analysis completed successfully!")


if __name__ == "__main__":
    main()
