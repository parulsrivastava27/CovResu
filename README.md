# 🦙 CovRes - AI Resume and Cover Letter Generator

A powerful Streamlit application that uses local LLM models (via Ollama) to help you create professionally tailored resumes and cover letters with AI assistance.

## Features

✨ **AI-Powered Resume Tailoring**
- Automatically rewrite your experience bullet points to match job descriptions
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

🎯 **Multi-Step Workflow**
- Personal Information
- Skills & Work Experience
- Projects & Education
- Target Job Description
- Document Generation & Download

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
   - **Step 3**: Add projects and education
   - **Step 4**: Paste the target job description
   - **Step 5**: Generate and download your documents

## Configuration

Edit the Ollama model in [app.py](app.py):

```python
OLLAMA_MODEL = "gemma2:9b"  # Change to your desired model
OLLAMA_API_URL = "http://localhost:11434/api/generate"
```

**Supported Models:**
- `gemma2:9b` (recommended - good balance)
- `llama2:7b`
- `llama3.1`
- `mistral`

## How It Works

### Resume Tailoring
The app sends your work experience and the job description to your local LLM, which rewrites your bullet points to highlight relevant skills and keywords from the job posting.

### Cover Letter Generation
AI generates a personalized cover letter that:
- Explains why you're interested in the role
- Maps your skills to job requirements
- Includes a strong call to action

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

## Dependencies

- **streamlit** - Web application framework
- **reportlab** - PDF generation
- **requests** - HTTP client for Ollama API

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

## Tips

- Use detailed job descriptions for better AI tailoring
- Review AI-generated content before finalizing
- Keep your experience descriptions concise for better formatting
- Use specific skills and keywords in your profile

## Future Enhancements

- [ ] Multiple resume templates
- [ ] LinkedIn profile import
- [ ] Resume scoring against job descriptions
- [ ] Multiple language support
- [ ] Custom styling options

Made with ❤️ using Streamlit & Ollama