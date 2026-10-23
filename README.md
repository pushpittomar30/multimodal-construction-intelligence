# Multimodal Construction Intelligence Platform (BuildWise)

A Streamlit capstone prototype for construction-site safety screening, visible crack observations, planning estimates, and weather-aware site guidance.

## Features
- PPE/site hazard review from uploaded JPG/PNG images
- Visible surface-defect observations with uncertainty-aware guidance
- Indicative cost, asset value, steel and cement estimates
- Weather-aware daily checklist and construction assistant chat
- JSON report downloads
- Demo mode when no Gemini API key is configured
- No external database

## Run locally
Requires Python 3.9+ (Python 3.10–3.12 recommended).

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit, usually `http://localhost:8501`.

## Enable Gemini image analysis
1. Obtain an API key from Google AI Studio.
2. Run the app and paste the key into the password field in the sidebar.
3. The app uses the Gemini API for image analysis and chat. The key is held in Streamlit session state and is not written to a project file.

For deployment, configure a secret named `GEMINI_API_KEY` only after adapting the app to read `st.secrets`; never commit keys to GitHub. The current app deliberately uses the sidebar field so a demo can be run without deployment secrets.

## Deploy on Streamlit Community Cloud
1. Push `app.py`, `requirements.txt`, and `README.md` to a GitHub repository.
2. In Streamlit Community Cloud, create an app pointing to `app.py`.
3. Deploy. The app starts in demo mode until a Gemini key is entered.
4. Test each tab with non-sensitive sample images.

## Estimate assumptions
The construction rate, steel/cement quantities and valuation are rough illustrative assumptions embedded in the app. Replace them with a documented local rate card and professionally reviewed calculation model before presenting as a real estimate.

## Safety and engineering disclaimer
This application is a student/capstone decision-support prototype, not a certified safety audit, structural diagnosis, quantity survey, property appraisal or engineering design. Image models may miss hazards or hallucinate details. OSHA requirements and Indian standards are context-specific; IS 456 is a concrete design code, not a PPE standard. Use qualified site safety professionals, structural engineers, quantity surveyors and local code requirements for real decisions.
