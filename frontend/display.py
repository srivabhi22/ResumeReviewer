import streamlit as st
import requests
import os



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

def calculate_ats_score(job_skills, missing_skills):
    # 🧠 Skill Match Score (85%)
    total_jd_skills = sum(len(job_skills.get(cat, [])) for cat in job_skills)
    total_missing_skills = sum(len(missing_skills.get(cat, [])) for cat in missing_skills)
    matched_skills = total_jd_skills - total_missing_skills

    if total_jd_skills > 0:
        skill_match_score = (matched_skills / total_jd_skills) * 50
    else:
        skill_match_score = 0

    # 🎓 Education Score (5%)
    total_jd_degrees = len(job_skills.get("academic_qualifications", []))
    missing_degrees = len(missing_skills.get("academic_qualifications", []))
    matched_degrees = total_jd_degrees - missing_degrees

    if total_jd_degrees > 0:
        education_score = (matched_degrees / total_jd_degrees) * 15
    else:
        education_score = 0

    # 📄 Formatting Score (10%)
    formatting_score = 10  # Assume formatting is clean for now

    # 🏁 Total ATS Score
    total_score = skill_match_score + education_score + formatting_score
    return round(total_score, 2)


def display_ats_score(ats_score):
    # Set color based on score
    if ats_score >= 80:
        color = "#4CAF50"  # Green
        rating = "✅ Excellent Fit"
    elif ats_score >= 60:
        color = "#FFC107"  # Amber
        rating = "⚠️ Good Fit"
    else:
        color = "#F44336"  # Red
        rating = "❗ Needs Improvement"

    # Display Circle Progress
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:center;margin:20px 0;">
      <div style="
        width: 200px;
        height: 200px;
        border-radius: 50%;
        border: 15px solid {color};
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.5rem;
        font-weight: bold;
        color: {color};
      ">
        {ats_score}%
      </div>
    </div>
    <h3 style="text-align:center;color:{color}">{rating}</h3>
    """, unsafe_allow_html=True)

def display_missing_skills(missing_skills):
    st.subheader("❗ Missing Skills")
    all_missing_technical_skills = missing_skills.get("technical_skills", [])
    all_missing_soft_skills = missing_skills.get("soft_skills", [])
    all_missing_academic_skills = missing_skills.get("academic_qualifications", [])

    
    if all_missing_technical_skills:
        st.markdown("**Technical Skills**")
        # Create a list of styled skill strings
        styled_skills = [
            f"<span style='background-color:#FF6961;color:white;padding:5px 10px;border-radius:20px;margin:3px;display:inline-block'>{skill}</span>"
            for skill in all_missing_technical_skills
        ]
        # Join them and display within a single markdown call for better grouping
        st.markdown(" ".join(styled_skills), unsafe_allow_html=True)
 

    
    if all_missing_soft_skills:
        st.markdown("**Soft Skills**")
        # Create a list of styled skill strings
        styled_skills = [
            f"<span style='background-color:#FF6961;color:white;padding:5px 10px;border-radius:20px;margin:3px;display:inline-block'>{skill}</span>"
            for skill in all_missing_soft_skills
        ]
        # Join them and display within a single markdown call for better grouping
        st.markdown(" ".join(styled_skills), unsafe_allow_html=True)
   


    if all_missing_academic_skills:
        st.markdown("**Academic Skills**")
        # Create a list of styled skill strings
        styled_skills = [
            f"<span style='background-color:#FF6961;color:white;padding:5px 10px;border-radius:20px;margin:3px;display:inline-block'>{skill}</span>"
            for skill in all_missing_academic_skills
        ]
        # Join them and display within a single markdown call for better grouping
        st.markdown(" ".join(styled_skills), unsafe_allow_html=True)
  

def display_work_experience(experiences):
    st.subheader("💼 Work Experience")

    for i, exp in enumerate(experiences):
        # Normalize technologies_used
        technologies = exp.get('technologies_used', [])
        if isinstance(technologies, str):
            technologies = [technologies]
        elif not isinstance(technologies, list):
            technologies = []
        # Fallback if technologies is empty
        tech_display = ', '.join(technologies) if technologies else "No technologies used"

        # Normalize responsibilities
        responsibilities = exp.get('responsibilities', [])
        if isinstance(responsibilities, str):
            responsibilities = [responsibilities]
        elif not isinstance(responsibilities, list):
            responsibilities = []

        with st.expander(f"**{exp.get('job_title', 'N/A')} at {exp.get('company_name', 'N/A')}** ({exp.get('employment_duration', 'N/A')})"):
            st.markdown(f"""
                <div style="background: #f8f8f8; color: #333; padding: 15px; border-radius: 10px;">
                    <strong>Responsibilities:</strong>
                    <ul>
                        {''.join([f"<li>{resp}</li>" for resp in responsibilities])}
                    </ul>
                    <strong>Technologies:</strong> {tech_display}
                </div>
            """, unsafe_allow_html=True)


def display_projects(projects):
    st.subheader("🚀 Key Projects")

    for i, proj in enumerate(projects):
        # Get outcomes and normalize
        outcomes = proj.get('outcomes', [])
        if isinstance(outcomes, str):
            outcomes = [outcomes]
        elif not isinstance(outcomes, list):
            outcomes = []
        # Fallback if outcomes is empty
        if not outcomes:
            outcomes = ["No outcomes specified."]

        # Get technologies and normalize
        technologies = proj.get('technologies_used', [])
        if isinstance(technologies, str):
            technologies = [technologies]
        elif not isinstance(technologies, list):
            technologies = []
        # Fallback if technologies is empty
        tech_display = ', '.join(technologies) if technologies else "N/A"

        with st.expander(f"**{proj.get('project_name', 'N/A')}**"):
            st.markdown(f"""
                <div style="background: #f8f8f8; color: #333; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <p><strong>Objective:</strong> <em>{proj.get('objective', 'N/A')}</em></p>
                    <p><strong>Outcome:</strong></p>
                    <ul>
                        {''.join([f"<li>{resp}</li>" for resp in outcomes])}
                    </ul>
                    <strong>Technologies:</strong> {tech_display}
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

import urllib.parse

def display_youtube_courses(youtube_links, skill_name):

    for link in youtube_links:
        # Extract video ID for thumbnail
        parsed_url = urllib.parse.urlparse(link)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        video_id = query_params.get("v", [""])[0]

        if video_id:
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/0.jpg"
        else:
            thumbnail_url = "https://via.placeholder.com/320x180.png?text=Video"

        # Display Card
        st.markdown(f"""
        <div style="display: flex; align-items: center; background-color: #f9f9f9; border-radius: 10px; padding: 10px; margin-bottom: 15px; border: 1px solid #ddd;">
            <img src="{thumbnail_url}" width="150" style="border-radius: 8px; margin-right: 15px;">
            <div>
                <h4 style="margin-bottom:5px;">{skill_name} Course</h4>
                <a href="{link}" target="_blank" style="text-decoration: none;">
                    <button style="background-color:#FF0000;color:white;padding:8px 16px;border:none;border-radius:5px;cursor:pointer;">
                        ▶️ Watch on YouTube
                    </button>
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)


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
