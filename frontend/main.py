import sys
import os
import streamlit as st
import requests

# Get the root directory and add it to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)


from frontend.display import (
    display_personal_info,
    display_skill_match,
    display_missing_skills,
    calculate_ats_score,
    display_ats_score,
    display_work_experience,
    display_projects,
    display_youtube_courses,
    display_ats_content
)

from frontend.credentials import register_user, login_user, fetch_session_data

# API Base URL
# API_BASE_URL = "http://localhost:8000"
API_BASE_URL = "http://backend:8000" #use if running in docker-compose

# --- SESSION STATE ---
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "page" not in st.session_state:
    st.session_state.page = "login"  # Default page
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "session_data" not in st.session_state:
    st.session_state.session_data = {
        "resume_analysis": {},
        "skill_recommendation": {},
        "ats_bullets": {}
    }



# --- LOGIN PAGE ---
if st.session_state.page == "login":
    st.title("🔐 Resume Reviewer - Login or Register")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            login_user(username, password)

    with tab2:
        st.subheader("Register")
        new_username = st.text_input("New Username", key="signup_username")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Sign Up"):
            register_user(new_username, new_email, new_password)

# --- SESSION SELECTOR PAGE ---
elif st.session_state.page == "session_select":
    st.title("📂 Select or Create a Session")
    headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
    resp = requests.get(f"{API_BASE_URL}/my_sessions", headers=headers)

    if resp.status_code == 200:
        sessions = resp.json()
        session_names = [s["name"] for s in sessions] + ["➕ Create New Session"]
        choice = st.selectbox("Choose Session", session_names)

        if choice == "➕ Create New Session":
            new_session_name = st.text_input("Enter New Session Name")
            if st.button("Create Session") and new_session_name:
                create_resp = requests.post(
                    f"{API_BASE_URL}/start_session",
                    params={"session_name": new_session_name},
                    headers=headers
                )
                if create_resp.status_code == 200:
                    st.session_state.session_id = create_resp.json()["session_id"]
                    fetch_session_data(st.session_state.session_id)
                    st.session_state.page = "main"
                    st.rerun()
                else:
                    st.error("❌ Failed to create session.")
        else:
            if st.button("Load Selected Session"):
                selected_session = next(s for s in sessions if s["name"] == choice)
                st.session_state.session_id = selected_session["id"]
                fetch_session_data(st.session_state.session_id)
                st.session_state.page = "main"
                st.rerun()
    else:
        st.error("❌ Unable to fetch sessions.")

# --- MAIN APP WITH SIDEBAR NAVIGATION ---
elif st.session_state.page == "main":
    st.sidebar.title("📁 Navigation")

    tab = st.sidebar.radio("Go to", [
        "Resume Analysis", "Skill Recommendations", "ATS Resume Bullets"
    ])
    if st.sidebar.button("🚪 Logout"):
        st.session_state.auth_token = None
        st.session_state.page = "login"
        st.rerun()

    headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}

        # --- RESUME ANALYSIS PAGE ---
    if tab == "Resume Analysis":
        st.title("📄 Resume and Job Description Analyzer")
        analysis = st.session_state.session_data.get("resume_analysis", {})

        # If no analysis data yet
        if not analysis:
            uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
            job_description = st.text_area("Paste Job Description")
            if st.button("Analyze Resume"):
                if uploaded_file and job_description:
                    src_dir = os.path.join(os.path.dirname(__file__), "..", "src")
                    resume_path = os.path.join(src_dir, uploaded_file.name)
                    with open(resume_path, "wb") as f:
                        f.write(uploaded_file.read())
                    
                    # Send request to backend for resume analysis
                    resp = requests.post(
                        f"{API_BASE_URL}/parse_resume",
                        data={
                            "resume_filename": uploaded_file.name,
                            "job_description": job_description,
                            "session_id": st.session_state.session_id
                        },
                        headers=headers
                    )

                    if resp.status_code == 200:
                        result = resp.json()
                        st.session_state.session_data["resume_analysis"] = result
                        analysis = result
                        st.success("✅ Analysis complete!")
                        st.rerun()
                    else:
                        st.error(f"Error: {resp.text}")
                else:
                    st.warning("Please upload a resume and enter a job description.")

        if analysis:
            # 📊 Beautiful Report Heading
            st.markdown("""
            Get a personalized analysis of your resume, highlighting strengths, skill gaps, and career highlights.
            """, unsafe_allow_html=True)

            summary = analysis.get("summary", {})

            # 👤 Personal Info & Education
            display_personal_info(summary.get("personal_info_and_education", {}))

            # 🎯 Skill Match Progress Bars
            total_skills_len = len(analysis.get("job_skills", {}).get("technical_skills", []))
            missing_skills_len = len(analysis.get("missing_skills", {}).get("technical_skills", []))
            display_skill_match(missing_skills_len, total_skills_len)

            # ❗ Missing Skills as Chips
            display_missing_skills(analysis.get("missing_skills", {}))            

            # 📊 ATS Score Circle Progres
            ats_score = calculate_ats_score(
                analysis.get("job_skills", {}),
                analysis.get("missing_skills", {})
            )

            st.subheader("📈 ATS Score")
            display_ats_score(ats_score)

            # 💼 Work Experience as Flip Cards
            display_work_experience(summary.get("work_experience", []))

            # 🚀 Projects as Carousel Flashcards
            display_projects(summary.get("key_projects", []))

            # 🌟 Soft Skills Cloud
            st.subheader("🤝 Soft Skills")
            soft_skills = summary.get("extracurricular_and_soft_skills", {}).get("soft_skills", [])
            if soft_skills:
                st.markdown(" ".join([f"<span style='background:#2196F3;color:white;padding:5px 10px;border-radius:20px;margin:5px;display:inline-block'>{skill}</span>" for skill in soft_skills]), unsafe_allow_html=True)
            else:
                st.markdown("_No soft skills found._")

            # 🔄 Button to Reset Analysis
            if st.button("🔄 New Analysis"):
                st.session_state.session_data["resume_analysis"] = {}
                st.rerun()


    # --- SKILL RECOMMENDATIONS PAGE ---
    elif tab == "Skill Recommendations":
        st.title("📘 Skill Recommendations")
        missing_skills = st.session_state.session_data.get("resume_analysis", {}).get("missing_skills", {}).get("technical_skills", [])
        if missing_skills:
            skill = st.selectbox("Select a Missing Skill", missing_skills)
            if st.button("Get Recommendations"):
                resp = requests.get(f"{API_BASE_URL}/recommend_courses", params={"skill": skill})
                if resp.status_code == 200:
                    courses = resp.json().get("courses", [])
                    st.subheader(f"🎓 Recommended YouTube Courses for {skill}")
                    display_youtube_courses(courses, skill)
                    # for course in courses:
                        # st.write(course)
                else:
                    st.error("Failed to fetch recommendations.")
        else:
            st.info("No missing skills found. Analyze a resume first.")

    # --- ATS RESUME BULLETS PAGE ---
    elif tab == "ATS Resume Bullets":
        st.title("📑 ATS Optimized Resume Bullets")
        src_dir = os.path.join(os.path.dirname(__file__), "..", "src")
        ats_points_file_path = os.path.join(src_dir, "ats_optimized_bullets.txt")
        resp = requests.get(f"{API_BASE_URL}/ats_optimized_bullets", headers=headers, params={'file_path': ats_points_file_path})
        if resp.status_code == 200:
            content = resp.json()
            st.markdown("### Optimized Bullet Points")
            display_ats_content(content.get("ats_content", "No ATS content available."))
            # st.write(content.get("ats_content", "No ATS content available."))
        else:
            st.error("Failed to fetch ATS optimized bullets.")

    