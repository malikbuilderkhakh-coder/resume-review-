# AI Resume Reviewer

Analyze your resume and get practical AI-powered improvement suggestions.

Upload a PDF or DOCX resume, optionally paste a job description, and get a structured review.

## Features
- PDF and DOCX resume upload
- Summary, strengths, weaknesses, missing information
- ATS-focused analysis (suggestions only, no pass/fail claims)
- Skills, experience, projects, and education analysis
- Optional resume vs job description comparison
- Example bullet-point rewrites that never invent facts
- Approximate AI ratings (clearly labelled as estimates)
- Friendly error messages

## Technology Stack
Python, Streamlit, CrewAI (one agent), Groq API, pypdf, python-docx.

## Project Structure
```
AI-Resume-Reviewer/
├── app.py                        # Web page (Streamlit)
├── resume_parser.py              # Reads PDF/DOCX and cleans text
├── resume_reviewer.py            # CrewAI agent + Groq connection
├── requirements.txt              # Libraries to install
├── README.md                     # This file
├── .gitignore                    # Files Git must ignore
└── .streamlit/
    └── secrets.toml.example      # Example secrets file (no real key)
```

## Local Setup
1. Install Python 3.12 (CrewAI needs Python 3.10 to 3.13).
2. Open a terminal in the project folder.
3. Create a virtual environment:
   - Windows: `python -m venv venv` then `venv\Scripts\activate`
   - Mac/Linux: `python3 -m venv venv` then `source venv/bin/activate`
4. Install libraries: `pip install -r requirements.txt`

## Streamlit Secrets Setup (local)
1. Get a free API key at https://console.groq.com
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
3. Replace `your_groq_api_key_here` with your real key.
4. Never upload `secrets.toml` to GitHub (it is already in `.gitignore`).

## Run the App
```
streamlit run app.py
```
Your browser opens at http://localhost:8501

## Deploy with GitHub + Streamlit Community Cloud
1. Create a GitHub repository (Public or Private) named `AI-Resume-Reviewer`.
2. Upload all project files (do NOT upload `.streamlit/secrets.toml`).
3. Go to https://share.streamlit.io and sign in with GitHub.
4. Click **Create app**, pick your repository, branch `main`, main file `app.py`.
5. Open **Advanced settings**, choose **Python 3.12**, and paste your secrets:
   ```
   GROQ_API_KEY = "your real key here"
   ```
6. Click **Deploy** and wait a few minutes.

## Troubleshooting
- **"API key not configured"** - add `GROQ_API_KEY` in Secrets, then reboot the app.
- **"Model is not available"** - Groq changes its models often. Set `GROQ_MODEL` in Secrets to a current model from https://console.groq.com/docs/models
- **"Usage limit reached"** - wait a minute, or try `GROQ_MODEL = "openai/gpt-oss-20b"`.
- **"Very little text found"** - your PDF is probably a scanned image. Use a text-based PDF or DOCX.
- **Install fails on deploy** - make sure Python 3.12 is selected in Advanced settings.

## Security and Privacy Notes
- The API key is read from Streamlit Secrets and is never written in code.
- Uploaded resumes are processed in memory and are not saved by this app.
- Resume text is sent to Groq to generate the review.
- CrewAI telemetry is turned off.
- AI reviews can contain mistakes. Always double-check the suggestions.
