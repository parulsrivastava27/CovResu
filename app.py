# app.py
import streamlit as st
import requests
import json
import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime
import io

# New imports for LinkedIn features
from bs4 import BeautifulSoup
import validators
import zipfile
import pandas as pd

# ---- Ollama config (adjust if needed) ----
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:1b")
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/api/generate")

# ---- Helper: query Ollama ----
def query_ollama(prompt):
    """
    Sends a prompt to local Ollama and returns the text response.
    """
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7
            }
        }
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Ollama. Make sure Ollama is running."
    except Exception as e:
        return f"Error: {str(e)}"

# ---- AI GENERATION FUNCTIONS (your originals) ----
def generate_cover_letter(user_data, job_description):
    prompt = f"""
    You are a professional resume writer. Write a cover letter.

    Candidate Name: {user_data.get('name','')}
    Current Role: {user_data.get('current_role','Not specified')}
    Skills: {', '.join(user_data.get('skills', []))}

    Target Job Description:
    {job_description}

    Instructions:
    1. Tone: Professional, confident, and enthusiastic.
    2. Structure: Introduction (why I'm applying), Body (matching my skills to the JD), Conclusion (call to action).
    3. Do NOT include placeholders like [Insert Date]. Use today's date.
    4. Keep it under 500 words.
    """
    return query_ollama(prompt)

def tailor_resume_experience(experience_list, job_description):
    """
    Uses Local LLM to rewrite experience bullet points.
    """
    experience_str = json.dumps(experience_list)
    prompt = f"""
    Act as an Expert Resume Writer.
    Task: Rewrite the 'description' field of the work experience JSON below to match the Job Description.

    Job Description Keywords:
    {job_description}

    Original Experience JSON:
    {experience_str}

    RULES:
    1. Output ONLY valid JSON.
    2. Return a LIST of dictionaries.
    3. Keep the exact same keys (title, company, duration), only change 'description'.
    4. Do not add conversational filler like "Here is the JSON".
    5. Ensure all quotes are escaped correctly.
    """
    response_text = query_ollama(prompt)

    # Improved JSON extraction
    try:
        match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            clean_text = response_text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_text)
    except json.JSONDecodeError as e:
        st.error(f"AI Error: The model returned invalid JSON. (Error: {str(e)})")
        st.warning("Raw Model Output (for debugging):")
        st.code(response_text)
        return experience_list

# ---- PDF GENERATION FUNCTIONS (your originals) ----
def create_resume_pdf(user_data, use_tailored=False):
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        story = []

        # Styles
        name_style = ParagraphStyle('Name', parent=styles['Heading1'], fontSize=22, spaceAfter=5, alignment=TA_CENTER)
        contact_style = ParagraphStyle('Contact', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.darkgrey)
        section_header = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=12, spaceBefore=15, spaceAfter=6, textTransform='uppercase')
        role_style = ParagraphStyle('Role', parent=styles['Heading3'], fontSize=11, spaceBefore=8, spaceAfter=2)
        company_style = ParagraphStyle('Company', parent=styles['Normal'], fontSize=11, textColor=colors.black, spaceAfter=2)
        desc_style = ParagraphStyle('Desc', parent=styles['Normal'], fontSize=10, leading=14)

        # Header
        story.append(Paragraph(user_data.get('name', 'Name'), name_style))
        contact_info = f"{user_data.get('email', '')} | {user_data.get('phone', '')} | {user_data.get('current_role', '')}"
        story.append(Paragraph(contact_info, contact_style))
        story.append(Spacer(1, 20))

        # Summary
        if user_data.get('summary'):
            story.append(Paragraph('Professional Summary', section_header))
            story.append(Paragraph(user_data['summary'], desc_style))
            story.append(Spacer(1, 10))

        # Education
        if user_data.get('education'):
            story.append(Paragraph('Education', section_header))
            for edu in user_data['education']:
                edu_text = f"<b>{edu.get('degree', '')}</b> - {edu.get('institution', '')} ({edu.get('year', '')})"
                story.append(Paragraph(edu_text, desc_style))

        # Experience
        experience_source = user_data.get('tailored_experience') if use_tailored and user_data.get('tailored_experience') else user_data.get('experience', [])

        if experience_source:
            story.append(Paragraph('Experience', section_header))
            for exp in experience_source:
                story.append(Paragraph(f"<b>{exp.get('title', '')}</b>", role_style))
                comp_dur = f"{exp.get('company', '')} | <i>{exp.get('duration', '')}</i>"
                story.append(Paragraph(comp_dur, company_style))
                story.append(Paragraph(exp.get('description', ''), desc_style))
                story.append(Spacer(1, 10))

        # Skills
        if user_data.get('skills'):
            story.append(Paragraph('Technical Skills', section_header))
            story.append(Paragraph(", ".join(user_data['skills']), desc_style))
            story.append(Spacer(1, 10))

        # Projects
        if user_data.get('projects'):
            story.append(Paragraph('Projects', section_header))
            for proj in user_data['projects']:
                story.append(Paragraph(f"<b>{proj.get('title', '')}</b>", role_style))
                if proj.get('tech'):
                    story.append(Paragraph(f"<i>Tech: {proj['tech']}</i>", desc_style))
                story.append(Paragraph(proj.get('description', ''), desc_style))
                story.append(Spacer(1, 8))

        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"PDF Error: {e}")
        return None

def create_cover_letter_pdf(text, user_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []

    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=11, leading=16)

    story.append(Paragraph(user_data.get('name', ''), styles['Heading2']))
    story.append(Paragraph(user_data.get('email', ''), normal_style))
    story.append(Paragraph(user_data.get('phone', ''), normal_style))
    story.append(Spacer(1, 20))

    story.append(Paragraph(datetime.now().strftime("%B %d, %Y"), normal_style))
    story.append(Spacer(1, 20))

    for para in text.split('\n\n'):
        story.append(Paragraph(para, normal_style))
        story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ---- LinkedIn helpers ----

def parse_linkedin_export(uploaded_file):
    """
    Accepts an uploaded file-like object (ZIP or CSV/JSON).
    Tries to parse LinkedIn exported profile data into CovRes user_data format.
    Returns a dict with parsed fields.
    """
    parsed = {
        'name': '',
        'email': '',
        'phone': '',
        'current_role': '',
        'summary': '',
        'skills': [],
        'experience': [],
        'projects': [],
        'education': []
    }

    try:
        # If zip file: inspect files inside
        if uploaded_file.name.lower().endswith('.zip'):
            z = zipfile.ZipFile(uploaded_file)
            namelist = z.namelist()
            # look for profile JSON first
            profile_json_files = [n for n in namelist if n.lower().endswith('.json') and ('profile' in n.lower() or 'member' in n.lower())]
            csv_files = [n for n in namelist if n.lower().endswith('.csv')]

            if profile_json_files:
                raw = z.read(profile_json_files[0]).decode('utf-8')
                data = json.loads(raw)
                # best-effort mapping
                fn = data.get('firstName') or data.get('localizedFirstName') or ''
                ln = data.get('lastName') or data.get('localizedLastName') or ''
                parsed['name'] = (fn + ' ' + ln).strip() or data.get('fullName') or parsed['name']
                parsed['summary'] = data.get('summary', parsed['summary'])

            # CSV parsing
            for f in csv_files:
                fname = f.lower()
                content = z.read(f).decode('utf-8')
                try:
                    df = pd.read_csv(io.StringIO(content))
                except Exception:
                    continue

                if any(c.lower() in ['full name', 'email address', 'headline'] for c in df.columns):
                    row = df.iloc[0]
                    if 'Full Name' in df.columns:
                        parsed['name'] = row.get('Full Name', parsed['name'])
                    for email_col in ['Email Address', 'Email', 'email address', 'email']:
                        if email_col in df.columns:
                            parsed['email'] = row.get(email_col, parsed['email'])
                    if 'Headline' in df.columns:
                        parsed['current_role'] = row.get('Headline', parsed['current_role'])

                if any(k in fname for k in ['position', 'positions', 'experience']):
                    for _, r in df.iterrows():
                        title = r.get('Title') or r.get('Position') or r.get('Job Title') or ''
                        company = r.get('Company') or r.get('Organization') or ''
                        start = r.get('Start Date') or r.get('Start') or ''
                        end = r.get('End Date') or r.get('End') or ''
                        desc = r.get('Description') or r.get('Summary') or ''
                        duration = f"{start} - {end}".strip(' -')
                        parsed['experience'].append({
                            'title': title,
                            'company': company,
                            'duration': duration,
                            'description': desc
                        })
                if 'education' in fname:
                    for _, r in df.iterrows():
                        parsed['education'].append({
                            'degree': r.get('Degree') or r.get('Title') or '',
                            'institution': r.get('School') or r.get('Institution') or r.get('Organization') or '',
                            'year': r.get('End Date') or r.get('Year') or ''
                        })

            # fallback: try to find email in any CSV
            if not parsed['email']:
                for f in csv_files:
                    content = z.read(f).decode('utf-8')
                    try:
                        df = pd.read_csv(io.StringIO(content))
                    except Exception:
                        continue
                    for c in df.columns:
                        if 'email' in c.lower():
                            parsed['email'] = df.iloc[0].get(c, parsed['email'])
                            break

        else:
            # Not a zip — maybe they uploaded JSON/CSV directly
            name = uploaded_file.name.lower()
            raw = uploaded_file.getvalue().decode('utf-8')
            if name.endswith('.json'):
                data = json.loads(raw)
                parsed['name'] = data.get('fullName') or data.get('name') or parsed['name']
                parsed['summary'] = data.get('summary', parsed['summary'])
            elif name.endswith('.csv'):
                df = pd.read_csv(io.StringIO(raw))
                if 'Full Name' in df.columns:
                    parsed['name'] = df.iloc[0].get('Full Name', parsed['name'])
                if 'Title' in df.columns and 'Company' in df.columns:
                    for _, r in df.iterrows():
                        parsed['experience'].append({
                            'title': r.get('Title',''),
                            'company': r.get('Company',''),
                            'duration': r.get('Date Range',''),
                            'description': r.get('Description','')
                        })
    except Exception as e:
        st.warning(f"Could not fully parse LinkedIn export: {e}")

    # Try to infer skills from summary or positions (very basic)
    if not parsed['skills'] and parsed.get('summary'):
        parsed['skills'] = [s.strip() for s in re.split(r'[,\n;]', parsed['summary']) if len(s.strip()) < 40][:12]

    return parsed

def fetch_public_linkedin(linkedin_url, timeout=8):
    """
    Try to fetch a public LinkedIn profile and extract basic fields.
    VERY best-effort: LinkedIn frequently changes HTML and may block requests.
    Returns a dict with possible keys: name, current_role, summary, skills, experience, education.
    """
    parsed = {
        'name': '',
        'email': '',
        'phone': '',
        'current_role': '',
        'summary': '',
        'skills': [],
        'experience': [],
        'education': []
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    }

    try:
        if not validators.url(linkedin_url):
            raise ValueError("Invalid URL")

        r = requests.get(linkedin_url, headers=headers, timeout=timeout)
        if r.status_code != 200:
            raise ValueError(f"Could not fetch page (status {r.status_code})")

        soup = BeautifulSoup(r.text, "lxml")

        # Heuristics for name/headline/summary/skills/experience/education
        name_tag = soup.select_one('h1') or soup.select_one('.text-heading-xlarge') or soup.select_one('.top-card-layout__title')
        if name_tag:
            parsed['name'] = name_tag.get_text(strip=True)

        headline = soup.select_one('div.text-body-medium') or soup.select_one('.text-body-medium') or soup.select_one('.top-card-layout__headline')
        if headline:
            parsed['current_role'] = headline.get_text(strip=True)

        about_sel = soup.select_one('#about') or soup.select_one('.pv-shared-text-with-see-more') or soup.find('section', {'id': 'about'})
        if about_sel:
            parsed['summary'] = about_sel.get_text(separator=' ', strip=True)

        skill_blocks = soup.select('.skill-pill') or soup.select('.pv-skill-category-entity__name-text') or soup.select('.skill-name')
        skills = []
        for s in skill_blocks[:20]:
            txt = s.get_text(strip=True)
            if txt:
                skills.append(txt)
        parsed['skills'] = skills

        exp_sections = soup.select('section#experience-section li') or soup.select('.experience__list-item') or soup.select('.pv-position-entity')
        experiences = []
        for ex in exp_sections[:10]:
            title = ex.select_one('h3') or ex.select_one('.t-16') or ex.select_one('.pv-entity__summary-info h3')
            company = ex.select_one('.pv-entity__secondary-title') or ex.select_one('.pv-entity__company-summary-info__company-name')
            date_range = ex.select_one('.pv-entity__date-range') or ex.select_one('.date-range')
            desc = ex.select_one('.pv-entity__description') or ex.select_one('.description')
            experiences.append({
                'title': title.get_text(strip=True) if title else '',
                'company': company.get_text(strip=True) if company else '',
                'duration': date_range.get_text(strip=True) if date_range else '',
                'description': desc.get_text(separator=' ', strip=True) if desc else ''
            })
        if experiences:
            parsed['experience'] = experiences

        edu_sections = soup.select('section#education-section li') or soup.select('.education__list-item') or soup.select('.pv-entity__school-summary-info')
        educations = []
        for ed in edu_sections[:10]:
            deg = ed.select_one('h3') or ed.select_one('.pv-entity__degree-name')
            school = ed.select_one('h4') or ed.select_one('.pv-entity__school-name')
            date = ed.select_one('.pv-entity__dates')
            educations.append({
                'degree': deg.get_text(strip=True) if deg else '',
                'institution': school.get_text(strip=True) if school else '',
                'year': date.get_text(strip=True) if date else ''
            })
        if educations:
            parsed['education'] = educations

        return parsed

    except Exception as e:
        return {'_error': str(e), **parsed}

def merge_parsed_into_user(parsed, ud):
    """
    Merge parsed fields into st.session_state['user_data'] without
    overwriting fields the user has already filled.
    """
    if parsed.get('name') and not ud.get('name'):
        ud['name'] = parsed['name']
    if parsed.get('email') and not ud.get('email'):
        ud['email'] = parsed['email']
    if parsed.get('phone') and not ud.get('phone'):
        ud['phone'] = parsed['phone']
    if parsed.get('current_role') and not ud.get('current_role'):
        ud['current_role'] = parsed['current_role']
    if parsed.get('summary') and not ud.get('summary'):
        ud['summary'] = parsed['summary']
    if parsed.get('skills') and not ud.get('skills'):
        ud['skills'] = parsed['skills']
    if parsed.get('experience') and (not ud.get('experience') or len(ud.get('experience')) == 0):
        ud['experience'] = parsed['experience']
    if parsed.get('education') and (not ud.get('education') or len(ud.get('education')) == 0):
        ud['education'] = parsed['education']

# ---- MAIN Streamlit UI (integrates the original workflow) ----
def main():
    st.set_page_config(page_title="Local AI Resume Builder", page_icon="🦙", layout="wide")

    st.sidebar.title("🦙 Local AI Resume")
    st.sidebar.markdown(f"Running Model: **{OLLAMA_MODEL}**")

    # Initialize Session State
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1

    if 'user_data' not in st.session_state:
        st.session_state.user_data = {
            'name': '', 'email': '', 'phone': '', 'current_role': '', 'summary': '',
            'skills': [], 'experience': [], 'projects': [], 'education': [],
            'job_description': '', 'tailored_experience': []
        }

    # Step 1: Personal Info + LinkedIn import options
    if st.session_state.current_step == 1:
        st.header("👤 Personal Information")
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.user_data['name'] = st.text_input("Name", st.session_state.user_data['name'])
            st.session_state.user_data['email'] = st.text_input("Email", st.session_state.user_data['email'])
        with c2:
            st.session_state.user_data['phone'] = st.text_input("Phone", st.session_state.user_data['phone'])
            st.session_state.user_data['current_role'] = st.text_input("Current Role", st.session_state.user_data['current_role'])

        st.session_state.user_data['summary'] = st.text_area("Professional Summary", st.session_state.user_data['summary'])

        st.markdown("### Import options (optional)")
        import_option = st.radio("Choose import method", (
            "Fill manually",
            "LinkedIn URL (public scrape — best effort)",
            "Upload LinkedIn export (recommended fallback)",
            "Connect via LinkedIn OAuth (recommended for production)"
        ), index=0)

        if import_option == "LinkedIn URL (public scrape — best effort)":
            linkedin_url = st.text_input("Paste public LinkedIn profile URL (e.g. https://www.linkedin.com/in/username)")
            if st.button("Import from LinkedIn URL"):
                if linkedin_url.strip() == "":
                    st.warning("Please paste a LinkedIn profile URL.")
                else:
                    with st.spinner("Fetching public LinkedIn profile (best effort)..."):
                        parsed = fetch_public_linkedin(linkedin_url)
                    if parsed.get('_error'):
                        st.error(f"Could not parse LinkedIn page: {parsed['_error']}")
                        st.info("Try the export upload or OAuth options if this fails.")
                    merge_parsed_into_user(parsed, st.session_state.user_data)
                    st.success("Imported (best-effort). Review fields above and edit as needed.")
                    st.experimental_rerun()

        elif import_option == "Upload LinkedIn export (recommended fallback)":
            uploaded = st.file_uploader("Upload LinkedIn export ZIP / CSV / JSON", type=['zip','csv','json'])
            if uploaded is not None:
                with st.spinner("Parsing LinkedIn export..."):
                    parsed = parse_linkedin_export(uploaded)
                merge_parsed_into_user(parsed, st.session_state.user_data)
                st.success("Imported from export — review and edit fields above as needed.")
                st.experimental_rerun()

        elif import_option == "Connect via LinkedIn OAuth (recommended for production)":
            st.info("This requires a small backend to handle OAuth (Flask example provided).")
            BACKEND = st.text_input("Backend base URL (e.g. http://localhost:5000)", "http://localhost:5000")
            if st.button("Start LinkedIn OAuth"):
                try:
                    r = requests.get(f"{BACKEND}/auth_url", timeout=8)
                    r.raise_for_status()
                    auth_url = r.json().get("auth_url")
                    if auth_url:
                        st.write("Opening LinkedIn auth in a new tab... authorize and then use backend to fetch profile.")
                        import webbrowser
                        webbrowser.open(auth_url)
                        st.success("After authorizing, the backend will have the profile. Use the 'Fetch LinkedIn profile' button below to import it.")
                except Exception as e:
                    st.error(f"Could not initiate OAuth: {e}")

            linkedin_id = st.text_input("LinkedIn ID (for demo fetch from backend)", "")
            if st.button("Fetch LinkedIn profile from backend"):
                if linkedin_id:
                    try:
                        r = requests.get(f"{BACKEND}/profile/{linkedin_id}", timeout=8)
                        r.raise_for_status()
                        profile = r.json()
                        if profile:
                            ud = st.session_state.user_data
                            ud['name'] = ud.get('name') or (" ".join([profile.get('first_name',''), profile.get('last_name','')]).strip())
                            ud['email'] = ud.get('email') or profile.get('email')
                            ud['current_role'] = ud.get('current_role') or profile.get('headline')
                            st.success("LinkedIn profile imported; review fields above.")
                            st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Failed to fetch profile: {e}")
                else:
                    st.info("Enter the LinkedIn ID printed by the backend callback response (for demo).")

        if st.button("Next: Skills & Experience ➡"):
            st.session_state.current_step = 2
            st.rerun()

    # Step 2
    elif st.session_state.current_step == 2:
        st.header("🛠 Skills & Experience")
        skills_txt = st.text_area("Skills (comma sep)", ", ".join(st.session_state.user_data['skills']))
        st.session_state.user_data['skills'] = [s.strip() for s in skills_txt.split(',') if s.strip()]

        st.subheader("Work Experience")
        for i, exp in enumerate(st.session_state.user_data['experience']):
            with st.expander(f"Job {i+1}", expanded=True):
                c1, c2 = st.columns(2)
                exp['title'] = c1.text_input(f"Title {i}", exp.get('title',''))
                exp['company'] = c2.text_input(f"Company {i}", exp.get('company',''))
                exp['duration'] = c1.text_input(f"Duration {i}", exp.get('duration',''))
                exp['description'] = st.text_area(f"Description {i}", exp.get('description',''))

        if st.button("➕ Add Job"):
            st.session_state.user_data['experience'].append({'title':'', 'company':'', 'duration':'', 'description':''})
            st.rerun()

        c1, c2 = st.columns([1, 1])
        if c1.button("⬅ Back"):
            st.session_state.current_step = 1
            st.rerun()
        if c2.button("Next: Projects & Education ➡"):
            st.session_state.current_step = 3
            st.rerun()

    # Step 3
    elif st.session_state.current_step == 3:
        st.header("🚀 Projects & Education")

        st.subheader("Projects")
        for i, proj in enumerate(st.session_state.user_data['projects']):
            with st.expander(f"Project {i+1}", expanded=True):
                proj['title'] = st.text_input(f"Project Name {i}", proj.get('title',''))
                proj['tech'] = st.text_input(f"Tech Stack {i}", proj.get('tech',''))
                proj['description'] = st.text_area(f"Project Desc {i}", proj.get('description',''))

        if st.button("➕ Add Project"):
            st.session_state.user_data['projects'].append({'title': '', 'tech': '', 'description': ''})
            st.rerun()

        st.divider()

        st.subheader("Education")
        for i, edu in enumerate(st.session_state.user_data['education']):
            with st.expander(f"Education {i+1}", expanded=True):
                edu['degree'] = st.text_input(f"Degree {i}", edu.get('degree',''))
                edu['institution'] = st.text_input(f"Institution {i}", edu.get('institution',''))
                edu['year'] = st.text_input(f"Year {i}", edu.get('year',''))

        if st.button("➕ Add Education"):
            st.session_state.user_data['education'].append({'degree': '', 'institution': '', 'year': ''})
            st.rerun()

        c1, c2 = st.columns([1, 1])
        if c1.button("⬅ Back"):
            st.session_state.current_step = 2
            st.rerun()
        if c2.button("Next: Target Job ➡"):
            st.session_state.current_step = 4
            st.rerun()

    # Step 4
    elif st.session_state.current_step == 4:
        st.header("🎯 Target Job Description")
        st.info("Paste the Job Description (JD) below.")
        st.session_state.user_data['job_description'] = st.text_area("Paste JD Here", st.session_state.user_data['job_description'], height=300)

        c1, c2 = st.columns([1, 1])
        if c1.button("⬅ Back"):
            st.session_state.current_step = 3
            st.rerun()
        if c2.button("Finalize & Generate ➡", type="primary"):
            st.session_state.current_step = 5
            st.rerun()

    # Step 5
    elif st.session_state.current_step == 5:
        st.header("✨ Generate Documents")
        tab1, tab2 = st.tabs(["📄 Resume", "✉️ Cover Letter"])

        with tab1:
            st.subheader("Resume Tailoring")
            if st.button("✨ Auto-Tailor Experience with AI"):
                with st.spinner(f"Rewriting bullets with {OLLAMA_MODEL}..."):
                    tailored = tailor_resume_experience(st.session_state.user_data['experience'], st.session_state.user_data['job_description'])
                    st.session_state.user_data['tailored_experience'] = tailored
                    if st.session_state.user_data.get('tailored_experience'):
                        st.success("Tailoring complete!")

            # Comparison View
            if st.session_state.user_data.get('tailored_experience'):
                use_tailored = st.checkbox("Use AI-Tailored Content in PDF", value=True)
                for i, orig in enumerate(st.session_state.user_data['experience']):
                    if i < len(st.session_state.user_data['tailored_experience']):
                        new = st.session_state.user_data['tailored_experience'][i]
                        with st.expander(f"Compare: {orig.get('title','')}"):
                            c1, c2 = st.columns(2)
                            c1.caption("Original")
                            c1.write(orig.get('description',''))
                            c2.caption("AI Version")
                            c2.write(new.get('description',''))
            else:
                use_tailored = False

            if st.button("📥 Download Resume PDF"):
                pdf = create_resume_pdf(st.session_state.user_data, use_tailored)
                if pdf:
                    st.download_button("Download Resume", pdf, "resume.pdf", "application/pdf")

        with tab2:
            st.subheader("Cover Letter")
            if st.button("📝 Write Cover Letter"):
                with st.spinner("Writing..."):
                    cl = generate_cover_letter(st.session_state.user_data, st.session_state.user_data['job_description'])
                    st.session_state.cl = cl

            if 'cl' in st.session_state:
                st.text_area("Result", st.session_state.cl, height=400)
                cl_pdf = create_cover_letter_pdf(st.session_state.cl, st.session_state.user_data)
                st.download_button("📥 Download Cover Letter PDF", cl_pdf, "cover_letter.pdf", "application/pdf")

        if st.button("🔄 Start Over"):
            st.session_state.clear()
            st.rerun()

if __name__ == '__main__':
    main()
