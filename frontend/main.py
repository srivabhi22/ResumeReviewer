import streamlit as st
import requests
import os

# API Base URL
API_BASE_URL = "http://localhost:8000"

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

# --- AUTH FUNCTIONS ---
def register_user(username, email, password):
    try:
        resp = requests.post(f"{API_BASE_URL}/register", params={
            "username": username, "email": email, "password": password
        })
        if resp.status_code == 200:
            st.success("✅ Registration successful! Please login.")
        else:
            st.error(resp.json().get("detail", "Registration failed."))
    except Exception as e:
        st.error(f"Error: {e}")

def login_user(username, password):
    try:
        resp = requests.post(f"{API_BASE_URL}/login", data={
            "username": username, "password": password
        })
        if resp.status_code == 200:
            st.session_state.auth_token = resp.json()["access_token"]
            st.session_state.page = "session_select"
            st.rerun()
        else:
            st.error(resp.json().get("detail", "Login failed."))
    except Exception as e:
        st.error(f"Error: {e}")

def fetch_session_data(session_id):
    headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
    resp = requests.get(f"{API_BASE_URL}/load_session", params={"session_id": session_id}, headers=headers)
    if resp.status_code == 200:
        st.session_state.session_data = resp.json()
    else:
        st.error("❌ Failed to load session data.")
        st.session_state.session_data = {
            "resume_analysis": {},
            "skill_recommendation": {},
            "ats_bullets": {}
        }


def display_resume_summary(summary):
    st.subheader("👤 Personal Info & Education")
    info = summary.get("personal_info_and_education", {})
    st.markdown(f"**Name:** {info.get('name', 'N/A')}")
    st.markdown(f"**Email:** {info.get('email', 'N/A')}")
    st.markdown(f"**Phone:** {info.get('phone', 'N/A')}")
    st.markdown("**Profiles:**")
    for link in info.get("profiles", []):
        st.markdown(f"- [{link}]({link})")

    st.markdown("### 🎓 Education")
    for edu in info.get("education", []):
        st.markdown(f"**{edu.get('degree', '')}**, {edu.get('institution', '')} ({edu.get('graduation_year', '')})")
        for ach in edu.get("achievements", []):
            st.markdown(f"- {ach}")

    st.markdown("---")

    st.subheader("💼 Work Experience")
    for exp in summary.get("work_experience", []):
        st.markdown(f"**{exp.get('job_title', '')}**, {exp.get('company_name', '')} ({exp.get('employment_duration', '')})")
        st.markdown("**Responsibilities:**")
        for resp in exp.get("responsibilities", []):
            st.markdown(f"- {resp}")
        st.markdown("**Technologies Used:**")
        st.markdown(", ".join(exp.get("technologies_used", [])))
        st.markdown("")

    st.markdown("---")

    st.subheader("🛠️ Key Projects")
    for proj in summary.get("key_projects", []):
        st.markdown(f"**{proj.get('project_name', '')}**")
        st.markdown(f"*Objective:* {proj.get('objective', '')}")
        st.markdown("**Technologies Used:**")
        st.markdown(", ".join(proj.get("technologies_used", [])))
        st.markdown("**Description:**")
        st.markdown(", ".join(proj.get("outcomes", [])))
        st.markdown("")

    st.markdown("---")

    st.subheader("🌟 Extracurricular Activities")
    for activity in summary.get("extracurricular_and_soft_skills", {}).get("activities", []):
        st.markdown(f"-{activity}")
    
    st.subheader("🤝 Soft Skills")
    soft_skills = summary.get("extracurricular_and_soft_skills", {}).get("soft_skills", [])
    if soft_skills:
        st.markdown("**Soft Skills:** " + ", ".join(soft_skills))

def display_skills(title, skills):
    st.subheader(title)
    st.markdown("### 🔧 Technical Skills")
    st.markdown(", ".join(skills.get("technical_skills", [])) or "_None_")

    st.markdown("### 🤝 Soft Skills")
    st.markdown(", ".join(skills.get("soft_skills", [])) or "_None_")

    st.markdown("### 🎓 Academic Qualifications")
    st.markdown(", ".join(skills.get("academic_qualifications", [])) or "_None_")

def display_skill_match(missing_skills_len, job_skills_len):
    st.subheader("🎯 Skill Match Overview")
    matched_skills_len = job_skills_len - missing_skills_len
    if job_skills_len == 0:
        match_percentage = 0
    else:
        match_percentage = int((matched_skills_len / job_skills_len) * 100)
    # Clamp to 100%
    match_percentage = min(match_percentage, 100)
    st.markdown(f"**Matched {matched_skills_len} out of {job_skills_len} required skills ({match_percentage}%)**")
    # Progress bar expects 0.0–1.0
    st.progress(match_percentage / 100.0)


def display_missing_skills(missing_skills):
    st.subheader("❗ Missing Skills")
    all_missing_skills = missing_skills.get("technical_skills", [])
    if all_missing_skills:
        # Create a list of styled skill strings
        styled_skills = [
            f"<span style='background-color:#FF6961;color:white;padding:5px 10px;border-radius:20px;margin:3px;display:inline-block'>{skill}</span>"
            for skill in all_missing_skills
        ]
        # Join them and display within a single markdown call for better grouping
        st.markdown(" ".join(styled_skills), unsafe_allow_html=True)
    else:
        st.write("No missing skills to display.")

def display_work_experience(experiences):
    st.subheader("💼 Work Experience")

    for i, exp in enumerate(experiences):
        # Create a unique key for each expander
        with st.expander(f"**{exp.get('job_title', 'N/A')} at {exp.get('company_name', 'N/A')}** ({exp.get('employment_duration', 'N/A')})"):
            st.markdown(f"""
                <div style="background: #f8f8f8; color: #333; padding: 15px; border-radius: 10px;">
                    <strong>Responsibilities:</strong>
                    <ul>
                        {''.join([f"<li>{resp}</li>" for resp in exp.get('responsibilities', [])])}
                    </ul>
                    <strong>Technologies:</strong> {', '.join(exp.get('technologies_used', []))}
                </div>
            """, unsafe_allow_html=True)


def display_projects(projects):
    st.subheader("🚀 Key Projects")

    for i, proj in enumerate(projects):
        # Each st.expander will be rendered on a new line
        with st.expander(f"**{proj.get('project_name', 'N/A')}**"):
            st.markdown(f"""
                <div style="background: #f8f8f8; color: #333; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <strong>Objective:</strong> <ul>
                    <p><em>{proj.get('objective', '')}</em></p>
                    <strong>Outcome:</strong> <ul>
                        {''.join([f"<li>{resp}</li>" for resp in proj.get('outcomes', [])])}
                    </ul>
                    <strong>Technologies:</strong> {', '.join(proj.get('technologies_used', []))}<br>
                </div>
            """, unsafe_allow_html=True)

# Example Usage:
# display_projects_expander_in_columns(projects_data)

def display_personal_info(info):
    st.subheader("👤 Personal Information")
    st.markdown(f"**Name:** {info.get('name', 'N/A')}")
    st.markdown(f"**Email:** {info.get('email', 'N/A')}")
    st.markdown(f"**Phone:** {info.get('phone', 'N/A')}")
    for profile in info.get('profiles', []):
        if("linkedin" in profile.lower()):
            st.markdown(f"🔗 [LinkedIn]({profile})")
        elif("github" in profile.lower()):
            st.markdown(f"🔗 [Github]({profile})")
        elif("kaggle" in profile.lower()):
            st.markdown(f"🔗 [Kaggle]({profile})")
        else:
            st.markdown(f"🔗 [Other Links]({profile})")

def display_ats_content(ats_content_data):
    st.subheader("💡 Optimized Resume Bullet Points")
    # Check if data is available
  
    if not ats_content_data or "optimized_bullets" not in ats_content_data:
        st.info("No ATS optimized content available.")
        return

    # --- Custom CSS for Styling the Expanders ---
    # This CSS will make each expander look like a distinct card.
    st.markdown("""
        <style>
        /* Styles for the expander container (the card itself) */
        .ats-section-card .stExpander {
            border: 1px solid #e0e0e0; /* Light grey border */
            border-radius: 12px; /* Rounded corners */
            margin-bottom: 20px; /* Space between cards */
            box-shadow: 0 4px 12px rgba(0,0,0,0.08); /* Soft shadow for depth */
            background-color: #ffffff; /* White background for the card */
            overflow: hidden; /* Ensures content respects border-radius */
        }

        /* Styles for the expander header (the clickable part) */
        .ats-section-card .stExpander > button {
            font-size: 1.15em; /* Slightly larger font for title */
            font-weight: bold;
            color: #2c3e50; /* Darker text for readability */
            padding: 18px 20px; /* More padding */
            width: 100%; /* Full width button */
            text-align: left; /* Align text to the left */
            background-color: #f8f9fa; /* Light background for header */
            border-bottom: 1px solid #e0e0e0; /* Separator line */
            border-top-left-radius: 12px; /* Match card radius */
            border-top-right-radius: 12px;
            display: flex; /* Use flexbox for alignment */
            align-items: center; /* Vertically center icon and text */
            gap: 10px; /* Space between icon and text */
        }
        /* Style for the Streamlit expander icon (caret) */
        .ats-section-card .stExpander > button svg {
            color: #3498db; /* Blue color for expander icon */
            transition: transform 0.3s ease; /* Smooth rotation transition */
        }
        /* Rotate icon when expander is open */
        .ats-section-card .stExpander > button[aria-expanded="true"] svg {
            transform: rotate(90deg); /* Rotates the caret right when expanded */
        }

        /* Styles for the expanded content area */
        .ats-section-card .streamlit-expanderContent {
            background-color: #fdfdfd; /* Very light background for content */
            padding: 15px 20px; /* Padding for content */
            border-bottom-left-radius: 12px; /* Match card radius */
            border-bottom-right-radius: 12px;
        }

        /* Styling for the unordered list of bullets */
        .ats-section-card ul {
            list-style-type: disc; /* Standard disc bullets */
            padding-left: 25px; /* Indent bullets */
            margin-top: 10px; /* Space above the list */
            margin-bottom: 10px; /* Space below the list */
        }

        /* Styling for individual bullet points */
        .ats-section-card ul li {
            margin-bottom: 8px; /* Space between bullet points */
            line-height: 1.6; /* Better readability */
            color: #495057; /* Slightly darker text for content */
        }
        </style>
    """, unsafe_allow_html=True)

    # Loop through each section in the ATS content
    for item in ats_content_data["optimized_bullets"]:
        section_title = item.get("section", "Untitled Section")
        bullets = item.get("bullets", [])

        # Create a custom container for each expander to apply our CSS classes
        with st.container():
            st.markdown(f'<div class="ats-section-card">', unsafe_allow_html=True) # Start custom wrapper div
            
            # Use st.expander for interactive collapsing
            with st.expander(f"**{section_title}**", expanded=False): # 'expanded=False' makes them initially collapsed
                if bullets:
                    # Construct an HTML unordered list for the bullet points
                    bullets_html = "".join([f"<li>{bullet}</li>" for bullet in bullets])
                    st.markdown(f"<ul>{bullets_html}</ul>", unsafe_allow_html=True)

                    # Add a Streamlit button to copy all bullets for the section
                    section_bullets_text = "\n".join(bullets)
                    # Using hash() for key to ensure uniqueness even if section titles are identical
                    if st.button(f"📋 Copy Bullets", key=f"copy_btn_{section_title.replace(' ', '_').replace('|', '')}_{hash(section_title)}"):
                        st.code(section_bullets_text, language='text')
                        st.success("The bullet points are now in the code block above. Please copy them manually from there.")
                else:
                    st.info("No bullet points available for this section.")
            st.markdown('</div>', unsafe_allow_html=True) # End custom wrapper div

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

        # If analysis data exists (either previously or just uploaded)
        # if analysis:
        #     st.subheader("Resume Summary")
        #     st.write(analysis.get("summary", "No summary available."))

        #     st.subheader("Skills in Resume")
        #     st.write(analysis.get("credentials", []))

        #     st.subheader("Job Skills")
        #     st.write(analysis.get("job_skills", []))

        #     st.subheader("Missing Skills")
        #     st.write(analysis.get("missing_skills", []))

        #     if st.button("🔄 New Analysis"):
        #         st.session_state.session_data["resume_analysis"] = {}
        #         st.rerun()

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
                    st.subheader(f"Recommended Courses for '{skill}'")
                    for course in courses:
                        st.write(course)
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
            print(content)
            display_ats_content(content.get("ats_content", "No ATS content available."))
            # st.write(content.get("ats_content", "No ATS content available."))
        else:
            st.error("Failed to fetch ATS optimized bullets.")

    