#!/usr/bin/env bash
# exit on error
set -o errexit

# Force HuggingFace cache to be in the project directory for persistence between build and runtime
export HF_HOME=models/hf_cache
export SENTENCE_TRANSFORMERS_HOME=models/hf_cache

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm

# Download NLTK data
echo "Downloading NLTK data..."
python -m nltk.downloader punkt stopwords averaged_perceptron_tagger

# Pre-download Sentence Transformer model (smaller version for 512MB RAM)
echo "Downloading Sentence Transformer model (all-MiniLM-L6-v2)..."
python -c "from langchain_huggingface.embeddings import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', cache_folder='models/hf_cache')"

# Create necessary directories
mkdir -p models/hf_cache
mkdir -p uploads/resumes
mkdir -p logs
mkdir -p vector_stores/chroma_db

# Ensure the app can write to its log file
touch logs/app.log
chmod -R 777 logs
chmod -R 777 uploads
chmod -R 777 models
chmod -R 777 vector_stores

echo "Build pipeline complete."
