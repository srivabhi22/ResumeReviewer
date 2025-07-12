import os

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def create_file(path, content=""):
    if not os.path.exists(path):
        with open(path, "w") as file:
            file.write(content)
        print(f"Created file: {path}")
    else:
        print(f"File already exists: {path}")

def main():
    # Base directory
    base_dir = r"C:\Users\HP\OneDrive - IIT Kanpur\Documents\Desktop\ResumeReviewer"
    create_directory(base_dir)

    # Subdirectories
    subdirs = [
        "backend", "frontend", "models", "utils", "data", "tests", "config"
    ]
    for subdir in subdirs:
        create_directory(os.path.join(base_dir, subdir))

    # Essential files
    files_content = {
        "README.md": "# Resume Review Tool\n\nA tool to extract, summarize, and match resumes with job descriptions.",
        "requirements.txt": "streamlit\nfastapi\nuvicorn\nPyPDF2\npdfminer.six\ntransformers\nscikit-learn\nnltk\nspacy\npandas\n",
        "backend/main.py": "# Entry point for the backend\n\nfrom fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef home():\n    return {'message': 'Resume Review Tool Backend'}\n",
        "frontend/app.py": "# Entry point for the frontend\n\nimport streamlit as st\n\nst.title('Resume Review Tool')\nst.write('Upload your resume and job description to get started.')\n",
        "tests/test_basic.py": "# Basic test file\n\ndef test_sample():\n    assert 1 + 1 == 2\n",
        "config/config.yaml": "# Configuration settings\n\nsettings:\n  debug: true\n",
    }

    for file, content in files_content.items():
        create_file(os.path.join(base_dir, file), content)

    print("\nProject structure created successfully!")

if __name__ == "__main__":
    main()
