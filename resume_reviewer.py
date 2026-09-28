import os

# Privacy: turn off CrewAI telemetry/tracing BEFORE importing crewai.
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

from crewai import LLM, Agent, Crew, Process, Task

# Groq offers an OpenAI-compatible API at this address.
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# NOTE: the text below uses {resume_text} and {job_section} as placeholders.
# CrewAI fills them in when we call crew.kickoff(inputs=...).
# Do not add any other curly braces to this text.
TASK_DESCRIPTION = """
Review the resume below and write a structured review in Markdown.

STRICT RULES:
- Only use facts that appear in the resume text. Never invent employers, dates, numbers, skills, or achievements.
- Before saying something is missing, check the resume text carefully. If it is present, do not list it as missing.
- If you rewrite a bullet point, keep its original meaning. Do not add fake numbers or results. If a number would help, write [add number if you have it].
- Never claim the resume will or will not pass an ATS. Give analysis and suggestions only.
- Never tell the user to add skills they do not have. For job description gaps say: "If you genuinely have this skill, consider making it more visible on your resume."
- Ratings are rough AI estimates, not objective facts.
- Be specific and concise. Use bullet points. If a section does not apply, write one short line saying so.

RESUME TEXT:
{resume_text}

{job_section}

Write the review using exactly these headings, in this order:

# Resume Review
## 1. Summary
(2-4 sentences on what the resume contains.)
## 2. Strengths
(Bullets: skills, education, experience, projects, certifications, achievements, clarity.)
## 3. Areas for Improvement
(Bullets.)
## 4. Missing Information
(Bullets. Only list things truly absent, such as contact details, LinkedIn/GitHub, measurable results, project descriptions.)
## 5. ATS Analysis
(Comment on keywords, job titles, skills, relevant experience, and section headings. Give suggestions.)
## 6. Skills Analysis
(Group into: Technical skills, Soft skills, Tools, Programming languages, Frameworks, Other.)
## 7. Experience Analysis
(Are responsibilities clear? Are achievements measurable? Are action verbs used? Is the experience relevant?)
## 8. Projects Analysis
(Descriptions, technologies, impact, clarity, relevance. If there are no projects, say so in one line.)
## 9. Education Analysis
(Review the education section.)
## 10. Job Description Match
(If a job description was provided: matching skills, missing skills, relevant experience, keywords, keyword gaps, ways to better match. If none was provided, write only: No job description was provided.)
## 11. Recommended Improvements
(A numbered list of practical steps the user can take.)
## 12. Example Improvements
(2-3 examples. Format each as Original: "..." then Suggested: "...". Keep the original meaning.)
## 13. Approximate AI Ratings (rough estimates out of 10)
(One line each: Content completeness, ATS readiness, Skills clarity, Experience clarity, Project quality. Add one sentence reminding the user these are approximate.)
"""

EXPECTED_OUTPUT = (
    "A complete Markdown resume review that follows the requested headings exactly, "
    "based only on facts found in the resume."
)


def build_llm(api_key, model_name):
    """Create the CrewAI LLM object that talks to Groq."""
    crew_model = model_name
    # CrewAI removes one leading "openai/" from the model name. Groq's model
    # names (such as openai/gpt-oss-120b) start with "openai/" themselves,
    # so we add one extra prefix to keep the real name intact.
    if model_name.startswith("openai/"):
        crew_model = "openai/" + model_name

    return LLM(
        model=crew_model,
        custom_openai=True,
        base_url=GROQ_BASE_URL,
        api_key=api_key,
        temperature=0.3,
        max_tokens=4000,
    )


def review_resume(resume_text, job_description, api_key, model_name):
    """Run the single-agent crew and return the review as Markdown text."""
    llm = build_llm(api_key, model_name)

    agent = Agent(
        role="Resume Review Specialist",
        goal="Give an honest, accurate, and practical review of a resume.",
        backstory=(
            "You are an experienced recruiter and career coach. You give specific, "
            "honest feedback and you never invent facts about a candidate."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )

    task = Task(
        description=TASK_DESCRIPTION,
        expected_output=EXPECTED_OUTPUT,
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    if job_description:
        job_section = "JOB DESCRIPTION:\n" + job_description
    else:
        job_section = "JOB DESCRIPTION: none provided."

    result = crew.kickoff(
        inputs={"resume_text": resume_text, "job_section": job_section}
    )

    review = str(getattr(result, "raw", result) or "").strip()
    if len(review) < 100:
        raise ValueError("The AI returned an empty or invalid response.")
    return review


def friendly_error_message(error):
    """Turn a technical error into a short, understandable message."""
    text = str(error).lower()

    if "401" in text or "invalid api key" in text or "authentication" in text:
        return "Unable to analyze the resume right now. Your Groq API key looks invalid. Please check GROQ_API_KEY in your secrets."
    if "429" in text or "rate limit" in text or "rate_limit" in text:
        return "The AI service is busy or your usage limit was reached. Please wait a minute and try again."
    if "413" in text or "request too large" in text or "context length" in text:
        return "The resume text is too large for the AI model. Please try a shorter resume."
    if "model" in text and (
        "not found" in text or "decommission" in text or "does not exist" in text or "deprecated" in text
    ):
        return "The selected AI model is not available. Set GROQ_MODEL in your secrets to another Groq model and try again."
    if "connection" in text or "timeout" in text or "timed out" in text or "network" in text:
        return "Could not reach the AI service. Please check your internet connection and try again."
    if "empty or invalid response" in text:
        return "The AI returned an invalid response. Please try again."
    return "Unable to analyze the resume right now. Please check your API configuration and try again."
