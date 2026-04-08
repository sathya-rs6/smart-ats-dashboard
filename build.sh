#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm

# Pre-download Sentence Transformer model
echo "Downloading Sentence Transformer model..."
python -c "from langchain_huggingface.embeddings import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2')"

# Create necessary directories
mkdir -p models
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
