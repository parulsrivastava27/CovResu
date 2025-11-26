# 🦙 CovRes - AI Resume and Cover Letter Generator

A powerful Streamlit application that uses local LLM models (via Ollama) to help you create professionally tailored resumes and cover letters with AI assistance.

## Features

✨ **AI-Powered Resume Tailoring**
- Automatically rewrite your professional summary to be more impactful
- Rewrite experience bullet points to match job descriptions
- Enhance project descriptions for maximum impact
- Side-by-side comparison of original vs. AI-tailored content
- Choose which version to include in your final PDF

📝 **Cover Letter Generation**
- AI-generated cover letters tailored to specific job descriptions
- Professional formatting with proper structure
- Export to PDF

📄 **Professional PDF Export**
- Clean, ATS-friendly resume formatting
- Professional cover letter layouts
- Customizable sections

🎯 **5-Step Guided Workflow**
1. Personal Information (Name, Email, Phone, Role, Summary)
2. Skills & Work Experience (Skills, Job History)
3. Projects & Certifications (Projects, Certifications)
4. Education & Job Description (Education, Target JD)
5. Generate & Download (Compare & Export PDFs)

🧭 **Easy Navigation**
- Sidebar navigation to jump between steps
- Back/Next buttons for sequential flow
- Progress tracking

## Prerequisites

- **Python**
- **Ollama** installed and running locally
  - Download from [ollama.ai](https://ollama.ai)
  - Run: `ollama run gemma2:9b` (or your preferred model)

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure Ollama is running

## Usage

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Open your browser to `http://localhost:8501`

3. Follow the 5-step wizard:
  - **Step 1**: Enter personal information and professional summary
  - **Step 2**: Add skills and work experience
  - **Step 3**: Add projects and certifications
  - **Step 4**: Add education and paste the target job description
  - **Step 5**: Generate and compare AI-tailored versions, then download PDFs

## Configuration

Edit the Ollama model in [app.py](app.py):

```python
OLLAMA_MODEL = "llama3.1"  # Change to your desired model
OLLAMA_API_URL = "http://localhost:11434/api/generate"
```

**Supported Models:**
- `gemma2:9b` (recommended - good balance)
- `llama2:7b`
- `llama3.1`
- `mistral`

## How It Works

### Resume Tailoring
The app uses three AI functions to enhance your resume:

1. **Professional Summary** - Rewrites your summary to be concise and impactful (max 3 sentences)
2. **Work Experience** - Rewrites bullet points to match keywords from the job description
3. **Projects** - Enhances project descriptions to highlight impact and technology

All tailoring happens locally on your machine via Ollama—your data never leaves your computer.

### Cover Letter Generation
AI generates a personalized cover letter that:
- Introduces you with enthusiasm and confidence
- Maps your skills to job requirements
- Includes a strong call to action
- Stays under 500 words

### PDF Generation
Uses ReportLab to create professionally formatted documents with:
- Clean typography
- Proper spacing and alignment
- All your sections (summary, skills, experience, projects, education)

## File Structure

```
.
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Key Functions

- `query_ollama()` | Sends prompts to local Ollama API |
- `tailor_resume_summary()` | AI-rewrites professional summary |
- `tailor_resume_experience()` | AI-rewrites experience bullet points |
- `tailor_resume_projects()` | AI-enhances project descriptions |
- `generate_cover_letter()` | AI generates cover letter |
- `create_resume_pdf()` | Generates resume PDF with optional tailored content |
- `create_cover_letter_pdf()` | Generates cover letter PDF |

## Dependencies

- **streamlit** - Web application framework
- **reportlab** - PDF generation
- **requests** - HTTP client for Ollama API
- **json** - JSON parsing for AI responses
- **re** - Regex for improved JSON extraction

## Troubleshooting

**"Could not connect to Ollama"**
- Ensure Ollama is running: `ollama serve`
- Check that `OLLAMA_API_URL` is correct (default: `http://localhost:11434/api/generate`)

**"Invalid JSON from model"**
- The app will show the raw output for debugging
- Try a different model or adjust the temperature setting
- Some models are better at structured output

**PDF Generation Errors**
- Ensure all text fields are properly filled
- Check for special characters that might break PDF generation

## Tips for Best Results

✅ **Professional Summary**
- Keep it concise (2-3 sentences)
- Highlight key achievements and skills
- Mention years of experience

✅ **Work Experience**
- Use detailed job descriptions (3-5 sentences)
- Include specific metrics and achievements
- Use relevant industry keywords

✅ **Job Description**
- Paste the complete job posting
- Include job requirements and responsibilities
- Use actual JD from job posting (not your own words)

✅ **Cover Letter**
- AI works best with complete job descriptions
- Highlight role-specific keywords in your experience
- Review generated content for accuracy before download

## Future Enhancements

- [ ] Multiple resume templates
- [ ] LinkedIn profile import
- [ ] Resume scoring against job descriptions
- [ ] Multiple language support
- [ ] Custom styling options
- [ ] Batch processing for multiple job applications
- [ ] Resume version history/comparison

## Limitations

- Requires local Ollama installation (no cloud AI)
- LLM quality depends on chosen model
- Large job descriptions may take longer to process
- AI output requires human review before submission

## Privacy

✅ **Your data stays on your machine**
- No cloud uploads
- No external AI services (uses local Ollama)
- All processing happens locally

Made with ❤️ using Streamlit & Ollama