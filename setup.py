"""
Setup script for Resume Analyzer RAG
"""

import os
import sys
from pathlib import Path
import subprocess


def create_directories():
    """Create necessary directories"""
    directories = [
        "uploads/resumes",
        "vector_stores",
        "logs",
        "static"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")


def copy_env_file():
    """Copy .env.example to .env if it doesn't exist"""
    if not Path(".env").exists():
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("✓ Created .env file from .env.example")
            print("⚠️  Please edit .env file and add your API keys!")
        else:
            print("⚠️  .env.example not found. Please create .env manually.")
    else:
        print("✓ .env file already exists")


def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True


def download_spacy_model():
    """Download spaCy language model"""
    print("\n📥 Downloading spaCy language model...")
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        print("✓ spaCy model downloaded successfully")
    except subprocess.CalledProcessError:
        print("⚠️  Failed to download spaCy model. You can download it later with:")
        print("   python -m spacy download en_core_web_sm")


def initialize_database():
    """Initialize the database"""
    print("\n🗄️  Initializing database...")
    try:
        from models.database import init_database
        init_database()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Failed to initialize database: {e}")
        print("   You can initialize it later by running:")
        print("   python -c \"from models.database import init_database; init_database()\"")


def main():
    """Main setup function"""
    print("=" * 60)
    print("Resume Analyzer RAG - Setup Script")
    print("=" * 60)
    print()
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✓ Python version: {sys.version.split()[0]}")
    print()
    
    # Create directories
    print("📁 Creating directories...")
    create_directories()
    print()
    
    # Copy .env file
    print("⚙️  Setting up configuration...")
    copy_env_file()
    print()
    
    # Ask user if they want to install dependencies
    response = input("Do you want to install dependencies now? (y/n): ").lower()
    if response == 'y':
        if install_dependencies():
            # Download spaCy model
            response = input("\nDo you want to download spaCy model? (y/n): ").lower()
            if response == 'y':
                download_spacy_model()
            
            # Initialize database
            response = input("\nDo you want to initialize the database? (y/n): ").lower()
            if response == 'y':
                initialize_database()
    
    print()
    print("=" * 60)
    print("✅ Setup completed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Edit the .env file and add your API keys")
    print("2. Run the API server: uvicorn main:app --reload")
    print("3. Run the Streamlit app: streamlit run web/app.py")
    print()
    print("For more information, see README.md")


if __name__ == "__main__":
    main()
