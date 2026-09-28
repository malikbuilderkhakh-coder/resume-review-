import streamlit as st

from resume_parser import clean_text, extract_resume_text, limit_text

# This must be the first Streamlit command in the file.
st.set_page_config(page_title="AI Resume Reviewer", page_icon="📄", layout="wide")

# Import the AI part safely, so a library problem shows a friendly message.
try:
    from resume_reviewer import friendly_error_message, review_resume
except Exception as import_error:
    st.title("AI Resume Reviewer")
    st.error(
        "The app could not start because a required library failed to load. "
        "Please check requirements.txt and the deployment logs."
    )
    with st.expander("Technical details (for developers)"):
        st.code(str(import_error))
    st.stop()

# ---------- Settings ----------
MAX_FILE_MB = 5
MAX_RESUME_CHARS = 6000
MAX_JOB_CHARS = 3000
DEFAULT_MODEL = "openai/gpt-oss-120b"


def read_secret(name, default=""):
    """Read a value from Streamlit Secrets. Returns default if it is missing."""
    try:
        return str(st.secrets[name]).strip()
    except Exception:
        return default


# ---------- Page header ----------
st.title("📄 AI Resume Reviewer")
st.write("Analyze your resume and get practical AI-powered improvement suggestions.")

with st.expander("How to use this app", expanded=False):
    st.markdown(
        """
1. Upload your resume (PDF or DOCX).
2. *(Optional)* Paste a job description to see how well your resume matches it.
3. Click **Review Resume** and wait about 20-60 seconds.

**Privacy:** your file is processed only for this review and is not saved by this app.
The extracted text is sent to the Groq AI service to generate the review.
"""
    )

# ---------- Inputs ----------
uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx"])

job_description = st.text_area(
    "Job description (optional)",
    height=200,
    placeholder="Paste the job description here to compare it with your resume...",
)

review_clicked = st.button("Review Resume", type="primary")

# ---------- Main logic ----------
if review_clicked:
    # Check the simple things first.
    if uploaded_file is None:
        st.warning("Please upload your resume first.")
        st.stop()

    api_key = read_secret("GROQ_API_KEY")
    if not api_key:
        st.error(
            "The Groq API key is not configured. "
            "Add GROQ_API_KEY in your Streamlit Secrets and try again."
        )
        st.stop()

    model_name = read_secret("GROQ_MODEL", DEFAULT_MODEL)

    file_bytes = uploaded_file.getvalue()
    if len(file_bytes) > MAX_FILE_MB * 1024 * 1024:
        st.error(f"This file is too large. Please upload a file smaller than {MAX_FILE_MB} MB.")
        st.stop()

    review_text = ""
    error_message = ""
    technical_details = ""
    notices = []
    stage = "reading"  # tells us where an error happened

    with st.status("Reviewing your resume...", expanded=True) as status:
        try:
            st.write("Step 1 of 3: Reading your resume file...")
            raw_text = extract_resume_text(uploaded_file.name, file_bytes)
            resume_text = clean_text(raw_text)

            if len(resume_text) < 50:
                raise ValueError(
                    "Very little text was found in this file. If your resume is a scanned "
                    "image, please upload a text-based PDF or a DOCX file instead."
                )

            resume_text, resume_shortened = limit_text(resume_text, MAX_RESUME_CHARS)
            if resume_shortened:
                notices.append(
                    "Your resume is long, so the middle part was shortened before analysis. "
                    "The beginning and end were kept."
                )

            job_text = clean_text(job_description or "")
            job_text, job_shortened = limit_text(job_text, MAX_JOB_CHARS)
            if job_shortened:
                notices.append("The job description was long, so part of it was shortened.")

            stage = "ai"
            st.write("Step 2 of 3: The AI agent is analyzing your resume...")
            review_text = review_resume(resume_text, job_text, api_key, model_name)

            st.write("Step 3 of 3: Preparing your results...")
            status.update(label="Review complete!", state="complete", expanded=False)

        except ValueError as problem:
            if stage == "reading":
                # These messages are written for users, so show them as they are.
                error_message = str(problem)
            else:
                error_message = friendly_error_message(problem)
                technical_details = str(problem)
            status.update(label="Something went wrong", state="error", expanded=False)

        except Exception as problem:
            error_message = friendly_error_message(problem)
            technical_details = f"{type(problem).__name__}: {problem}"
            status.update(label="Something went wrong", state="error", expanded=False)

    # ---------- Show results or errors ----------
    if error_message:
        st.error(error_message)
        if technical_details:
            # Make sure the key can never appear on screen.
            safe_details = technical_details.replace(api_key, "***")
            with st.expander("Technical details (for developers)"):
                st.code(safe_details[:1500])
    else:
        for notice in notices:
            st.info(notice)
        st.success("Your resume review is ready.")
        st.caption(
            "This review and any ratings are approximate AI assessments, not objective facts. "
            "Use them as suggestions, not guarantees."
        )
        st.markdown(review_text)
