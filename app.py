import json
import os
from datetime import datetime
from typing import Any, Dict

import streamlit as st
from PIL import Image

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

st.set_page_config(
    page_title="BuildWise | Construction Intelligence",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown("""
<style>
:root { --ink:#182230; --muted:#667085; --line:#e7ebf0; --accent:#e87932; }
.block-container { padding-top: 1.6rem; max-width: 1440px; }
[data-testid="stSidebar"] { background: #111827; }
[data-testid="stSidebar"] * { color: #f9fafb !important; }
.hero {
  padding: 1.6rem 1.8rem; border-radius: 20px;
  background: linear-gradient(120deg,#172033 0%,#263b59 60%,#375b75 100%);
  color: white; margin-bottom: 1.2rem;
}
.hero h1 { font-size: 2.15rem; margin: 0 0 .35rem 0; color: white; }
.hero p { color:#dce6f1; margin:0; font-size:1.02rem; }
.eyebrow { text-transform:uppercase; letter-spacing:.13em; font-size:.72rem; color:#f8b47c; font-weight:800; }
.metric-card {
  padding: 1rem 1.1rem; border:1px solid var(--line); border-radius:15px;
  background:#fff; box-shadow:0 4px 14px rgba(16,24,40,.04); min-height:105px;
}
.metric-label { color:#667085; font-size:.84rem; margin-bottom:.3rem; }
.metric-value { color:#172033; font-size:1.55rem; font-weight:800; }
.metric-note { color:#667085; font-size:.78rem; margin-top:.25rem; }
.section-title { font-size:1.22rem; font-weight:800; color:#172033; margin:.4rem 0 .2rem; }
.small-muted { color:#667085; font-size:.88rem; }
.status { display:inline-block; padding:.28rem .7rem; border-radius:999px; font-size:.8rem; font-weight:800; }
.status-good { background:#dcfce7; color:#166534; }
.status-warn { background:#fef3c7; color:#92400e; }
.status-bad { background:#fee2e2; color:#991b1b; }
div[data-testid="stTabs"] button { font-weight:700; }
div[data-testid="stButton"] button { border-radius:10px; font-weight:700; }
div[data-testid="stDownloadButton"] button { border-radius:10px; font-weight:700; }
.note-box { padding: .85rem 1rem; border-radius:12px; background:#f8fafc; border:1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
def metric_card(label: str, value: str, note: str = ""):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )

def json_download(data: Dict[str, Any], filename: str):
    st.download_button(
        "⬇️ Download JSON report",
        data=json.dumps(data, indent=2, ensure_ascii=False),
        file_name=filename,
        mime="application/json",
        use_container_width=False,
    )

def parse_json_response(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end+1]
    return json.loads(text)

def call_gemini(api_key: str, prompt: str, image: Image.Image = None) -> Dict[str, Any]:
    if not api_key or not GEMINI_AVAILABLE:
        raise RuntimeError("Gemini is not configured. Use demo mode or add a valid API key.")
    client = genai.Client(api_key=api_key)
    contents = [prompt]
    if image is not None:
        contents.append(image)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=contents,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return parse_json_response(response.text or "{}")

def run_analysis(api_key: str, prompt: str, image: Image.Image, demo_data: Dict[str, Any]) -> Dict[str, Any]:
    if api_key and GEMINI_AVAILABLE:
        try:
            return call_gemini(api_key, prompt, image)
        except Exception as exc:
            st.warning(f"AI request failed; showing clearly labelled demo output instead. Details: {exc}")
    else:
        st.info("Demo mode is active. Add a Gemini API key in the sidebar to request image-based AI analysis.")
    return {**demo_data, "mode": "DEMO — illustrative output, not a real image inspection"}

def make_report(module: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "platform": "Multimodal Construction Intelligence Platform",
        "module": module,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "payload": payload,
        "disclaimer": "AI outputs are preliminary decision support only. They are not a substitute for qualified safety officers, structural engineers, quantity surveyors, or local code review.",
    }

def money_inr(value: float) -> str:
    if value >= 1e7:
        return f"₹{value/1e7:.2f} Cr"
    if value >= 1e5:
        return f"₹{value/1e5:.2f} L"
    return f"₹{value:,.0f}"

def show_hazards(hazards):
    if not hazards:
        st.success("No hazards were returned in this report.")
        return
    for item in hazards:
        severity = str(item.get("severity", "Medium")).title()
        color = "status-bad" if severity in ("Critical", "High") else ("status-warn" if severity == "Medium" else "status-good")
        st.markdown(
            f'<div style="padding:.8rem 1rem;border:1px solid #e7ebf0;border-radius:12px;margin:.45rem 0;">'
            f'<span class="status {color}">{severity}</span> <b>{item.get("hazard","Unspecified hazard")}</b>'
            f'<div class="small-muted" style="margin-top:.35rem">{item.get("remedy","Have a competent person assess and correct.")}</div></div>',
            unsafe_allow_html=True
        )

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🏗️ BuildWise")
    st.caption("Multimodal Construction Intelligence")
    api_key = st.text_input("Gemini API key", type="password", help="Used only for this session. For deployment, prefer Streamlit secrets.")
    st.caption("🔐 Your key is not written to a local file by this app.")
    st.markdown("---")
    st.markdown("### Architecture")
    st.markdown("**UI:** Streamlit  \n**Vision & language:** Gemini  \n**Image handling:** Pillow  \n**Reports:** JSON download  \n**Storage:** No external database")
    st.markdown("---")
    st.markdown("### Modules")
    st.markdown("1. PPE & site safety  \n2. Crack diagnostics  \n3. Cost & valuation  \n4. Weather & site assistant")
    st.markdown("---")
    st.caption("BuildWise · Capstone Project 1")

# ---------- Header ----------
st.markdown("""
<div class="hero">
  <div class="eyebrow">Skill Wallet · Capstone Project 1</div>
  <h1>Multimodal Construction Intelligence Platform</h1>
  <p>Turn site observations into structured safety insights, preliminary diagnostics, project estimates and daily protocols.</p>
</div>
""", unsafe_allow_html=True)

st.warning("Important: This is a capstone decision-support prototype. Never use its output as the sole basis for worker safety, structural diagnosis, engineering design, or property transactions.")

tab_safety, tab_crack, tab_plan, tab_assistant = st.tabs([
    "🦺 Site Safety & PPE", "🧱 Crack Diagnostics", "📐 Planning & Valuation", "🌦️ Daily Site Assistant"
])

# ---------- Tab 1 ----------
with tab_safety:
    st.markdown('<div class="section-title">Site Safety & PPE Audit</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Upload a site image for a preliminary PPE checklist and visible hazard review.</div>', unsafe_allow_html=True)
    safety_file = st.file_uploader("Upload construction-site photo", type=["jpg", "jpeg", "png"], key="safety_image")
    if safety_file:
        image = Image.open(safety_file).convert("RGB")
        st.image(image, caption="Uploaded site photo", use_container_width=True)
    else:
        image = None

    if st.button("Run PPE audit", type="primary", key="run_safety"):
        demo = {
            "safety_score": 72,
            "overall_status": "Needs attention",
            "ppe_detection": {
                "helmet": {"status": "Partially visible", "notes": "Verify each worker individually."},
                "high_visibility_vest": {"status": "Unclear", "notes": "Image visibility may be insufficient."},
                "steel_toe_boots": {"status": "Not verifiable from this image", "notes": "Footwear cannot reliably be confirmed."},
                "safety_harness": {"status": "Not verifiable", "notes": "Check elevated-work tasks on site."}
            },
            "hazards": [
                {"hazard": "PPE compliance not fully verifiable", "severity": "High", "remedy": "Conduct a person-by-person check and stop unsafe work until required PPE is confirmed."},
                {"hazard": "Potential trip hazards in work area", "severity": "Medium", "remedy": "Keep access routes clear and secure loose materials."}
            ]
        }
        prompt = """Analyze this construction site photo for visible PPE and site hazards. Return ONLY valid JSON with this schema:
{"safety_score": integer 0-100, "overall_status": string, "ppe_detection": {"helmet":{"status":string,"notes":string},"high_visibility_vest":{"status":string,"notes":string},"steel_toe_boots":{"status":string,"notes":string},"safety_harness":{"status":string,"notes":string}}, "hazards":[{"hazard":string,"severity":"Low|Medium|High|Critical","remedy":string}]}.
Do not claim a PPE item is present if it cannot be seen clearly. Include uncertainty. Refer to applicable site rules and relevant OSHA guidance only at a high level; do not claim legal certification or compliance with IS 456, which is a concrete design code and not a PPE standard. This is preliminary visual screening, not an official safety audit."""
        if image is None:
            st.error("Upload a photo first.")
        else:
            with st.spinner("Reviewing site photo..."):
                result = run_analysis(api_key, prompt, image, demo)
            st.session_state["safety_result"] = result

    result = st.session_state.get("safety_result")
    if result:
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        score = result.get("safety_score", "—")
        metric_card("Safety screening score", f"{score}/100" if isinstance(score, (int, float)) else str(score), "Indicative only")
        with c2:
            status = result.get("overall_status", "Not assessed")
            metric_card("Overall status", str(status), "Review all flagged items")
        with c3:
            metric_card("Hazards identified", str(len(result.get("hazards", []))), "From returned report")
        st.markdown("#### PPE checklist")
        ppe = result.get("ppe_detection", {})
        if isinstance(ppe, dict):
            for key, val in ppe.items():
                if isinstance(val, dict):
                    with st.expander(key.replace("_", " ").title()):
                        st.write("**Status:**", val.get("status", "Not reported"))
                        st.write(val.get("notes", ""))
                else:
                    st.write(f"**{key}:** {val}")
        st.markdown("#### Site hazards & remedies")
        show_hazards(result.get("hazards", []))
        report = make_report("Site Safety & PPE Audit", result)
        json_download(report, "site_safety_report.json")
        with st.expander("View raw JSON"):
            st.json(result)

# ---------- Tab 2 ----------
with tab_crack:
    st.markdown('<div class="section-title">Crack Diagnostics & Structural Integrity</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Use close, well-lit images with a scale marker where possible. A photo alone cannot confirm structural integrity.</div>', unsafe_allow_html=True)
    crack_file = st.file_uploader("Upload concrete or wall surface photo", type=["jpg", "jpeg", "png"], key="crack_image")
    if crack_file:
        crack_image = Image.open(crack_file).convert("RGB")
        st.image(crack_image, caption="Uploaded surface photo", use_container_width=True)
    else:
        crack_image = None
    if st.button("Analyze visible defect", type="primary", key="run_crack"):
        demo = {
            "defect_type": "Hairline (tentative)",
            "estimated_width_mm": "Cannot reliably estimate from an unscaled image",
            "severity": "Unknown — engineer review recommended",
            "possible_causes": ["Drying shrinkage", "Thermal movement", "Settlement (requires site context)"],
            "recommended_actions": ["Photograph with a crack-width gauge and date label.", "Monitor for change and check for water ingress.", "Ask a qualified structural engineer to inspect if the crack is growing, diagonal, through-wall, or accompanied by deformation."],
            "urgency": "Routine documentation; escalate immediately if movement or instability is suspected."
        }
        prompt = """Assess the visible concrete/wall defect in this image. Return ONLY JSON:
{"defect_type":"Hairline|Settlement|Structural Shear|Thermal Expansion|Spalling|Other|Indeterminate","estimated_width_mm":number|string,"severity":string,"possible_causes":[string],"recommended_actions":[string],"urgency":string}.
Do not diagnose structural safety from an image. If there is no scale marker, say width cannot be reliably measured. Distinguish observations from hypotheses, state uncertainty, and recommend an in-person qualified structural-engineer inspection for potentially serious defects. Repair ideas must be conditional, not prescriptive; epoxy injection or re-grouting must only be specified after professional diagnosis."""
        if crack_image is None:
            st.error("Upload a surface photo first.")
        else:
            with st.spinner("Reviewing surface image..."):
                result = run_analysis(api_key, prompt, crack_image, demo)
            st.session_state["crack_result"] = result
    result = st.session_state.get("crack_result")
    if result:
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            metric_card("Tentative defect class", str(result.get("defect_type", "Indeterminate")), "Image-based observation")
        with c2:
            metric_card("Estimated width", str(result.get("estimated_width_mm", "Not provided")), "Requires scale marker for measurement")
        st.markdown("#### Possible causes")
        for cause in result.get("possible_causes", []):
            st.markdown(f"- {cause}")
        st.markdown("#### Recommended next actions")
        for action in result.get("recommended_actions", []):
            st.markdown(f"- {action}")
        st.info(f"Urgency: {result.get('urgency', 'Not specified')}")
        report = make_report("Crack Diagnostics", result)
        json_download(report, "crack_diagnostics_report.json")
        with st.expander("View raw JSON"):
            st.json(result)

# ---------- Tab 3 ----------
with tab_plan:
    st.markdown('<div class="section-title">Project Planning & Real Estate Valuation</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Transparent rule-of-thumb estimates for planning discussions. Replace defaults with local quotations and professional valuations.</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        structure = st.selectbox("Structure type", ["Residential house", "Apartment building", "Commercial building", "Warehouse", "Farmhouse"])
        area = st.number_input("Built-up area (sq ft)", min_value=100, max_value=1000000, value=1500, step=100)
        tier = st.selectbox("Indian city tier", ["Tier 1", "Tier 2", "Tier 3"])
        completion = st.slider("Construction completion", 0, 100, 35, 5)
    with col2:
        city = st.text_input("City / locality", value="Indore, Madhya Pradesh")
        finish = st.selectbox("Finish quality", ["Economy", "Standard", "Premium"])
        land_rate_sqft = st.number_input("Estimated local land rate (₹/sq ft)", min_value=0, value=2500, step=100)
        contingency_pct = st.slider("Contingency allowance (%)", 0, 25, 10, 1)

    base_rates = {"Tier 1": 2600, "Tier 2": 2100, "Tier 3": 1750}
    finish_mult = {"Economy": 0.85, "Standard": 1.0, "Premium": 1.35}
    structure_mult = {"Residential house": 1.0, "Apartment building": 1.08, "Commercial building": 1.25, "Warehouse": 0.75, "Farmhouse": 1.05}
    build_rate = base_rates[tier] * finish_mult[finish] * structure_mult[structure]
    base_budget = area * build_rate
    total_budget = base_budget * (1 + contingency_pct / 100)
    incurred = total_budget * completion / 100
    remaining = total_budget - incurred
    land_value = area * land_rate_sqft
    current_asset_value = land_value + incurred * 0.9
    # Approximate planning quantities, explicitly illustrative
    steel_kg = area * 4.0
    cement_bags = area * 0.4
    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    with m1: metric_card("Estimated project budget", money_inr(total_budget), f"₹{build_rate:,.0f}/sq ft base rate")
    with m2: metric_card("Budget consumed to date", money_inr(incurred), f"{completion}% completion assumption")
    with m3: metric_card("Estimated remaining budget", money_inr(remaining), "Excludes financing and major scope changes")
    m4, m5, m6 = st.columns(3)
    with m4: metric_card("Indicative asset value", money_inr(current_asset_value), f"Land + 90% of incurred cost in {city}")
    with m5: metric_card("Indicative steel quantity", f"{steel_kg/1000:.1f} tonnes", "Rule of thumb: 4 kg/sq ft; engineer must calculate")
    with m6: metric_card("Indicative cement quantity", f"{cement_bags:,.0f} bags", "Rule of thumb: 0.4 bags/sq ft; verify design")
    st.markdown("#### Milestone progress")
    st.progress(completion / 100, text=f"{completion}% complete · {100-completion}% remaining")
    st.caption("Cost rates and quantities are illustrative placeholders, not a bill of quantities or market appraisal. Actual requirements depend on design, soil, location, specifications, taxes and contractor quotes.")
    with st.expander("How these estimates are calculated"):
        st.write(f"Base construction estimate = area × ₹{build_rate:,.0f}/sq ft.")
        st.write(f"Total project budget = base estimate × (1 + {contingency_pct}% contingency).")
        st.write("Indicative asset value = entered land-rate estimate × area + 90% of assumed incurred construction cost. This is not a certified valuation.")
    if st.button("Generate conceptual architecture prompt"):
        prompt_text = f"Photorealistic conceptual architectural visualization of a {structure.lower()}, {area} sq ft built-up area, {finish.lower()} finish, in {city}, Indian climate context, practical materials, daylight, professional architectural render, no text, no watermark. Concept only, not a construction drawing."
        st.text_area("Prompt for an image-generation service", value=prompt_text, height=110)
        st.caption("This app prepares a prompt only; it does not call Pollinations/Flux or generate an image.")
    planning_payload = {
        "structure_type": structure, "area_sqft": area, "city": city, "city_tier": tier,
        "finish_quality": finish, "completion_percent": completion,
        "construction_rate_inr_per_sqft": round(build_rate, 2),
        "estimated_total_budget_inr": round(total_budget, 2),
        "estimated_cost_incurred_inr": round(incurred, 2),
        "estimated_remaining_budget_inr": round(remaining, 2),
        "estimated_asset_value_inr": round(current_asset_value, 2),
        "indicative_steel_kg": round(steel_kg, 2), "indicative_cement_bags": round(cement_bags, 2),
        "contingency_percent": contingency_pct
    }
    json_download(make_report("Planning & Valuation", planning_payload), "planning_valuation_report.json")

# ---------- Tab 4 ----------
with tab_assistant:
    st.markdown('<div class="section-title">Daily Site Assistant & Weather-Aware Advisory</div>', unsafe_allow_html=True)
    weather = st.selectbox("Today's weather / site condition", ["Normal", "High Wind", "Heavy Rain", "Extreme Heat"])
    advisories = {
        "Normal": [
            "Run the daily toolbox talk and verify PPE before work starts.",
            "Inspect access routes, scaffolds, lifting gear and temporary electrical systems.",
            "Follow the approved concrete placement and curing method statement."
        ],
        "High Wind": [
            "Pause crane and hoisting operations when wind exceeds equipment or lift-plan limits; secure suspended loads.",
            "Stop work at height if conditions exceed the site risk assessment; secure loose sheets and materials.",
            "Re-check temporary structures, scaffolds and edge protection before resuming."
        ],
        "Heavy Rain": [
            "Assess flooding, excavation collapse and slippery access routes; restrict entry to unsafe areas.",
            "Isolate and inspect electrical equipment in wet areas; only qualified personnel should restore power.",
            "Protect fresh concrete from washout and follow the approved mix, placement and curing plan."
        ],
        "Extreme Heat": [
            "Schedule heavy work during cooler periods where practical and provide shade, drinking water and rest breaks.",
            "Use a buddy system and monitor for heat illness; stop work and seek medical help for concerning symptoms.",
            "Follow the engineer-approved concrete temperature, placement and curing procedures."
        ]
    }
    st.markdown("#### Weather protocol")
    for advice in advisories[weather]:
        st.markdown(f"- {advice}")
    st.caption("Follow local forecasts, the site-specific safety plan, equipment limits and competent-person instructions. These generic alerts do not replace site procedures.")

    st.markdown("---")
    st.markdown("#### Construction engineering assistant")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    user_question = st.chat_input("Ask about planning, materials, site workflow or safety...")
    if user_question:
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)
        answer = None
        if api_key and GEMINI_AVAILABLE:
            try:
                client = genai.Client(api_key=api_key)
                history_text = "\n".join([f'{m["role"]}: {m["content"]}' for m in st.session_state.chat_history[-10:]])
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=("You are BuildWise, a cautious construction project assistant. Give practical general guidance, ask clarifying questions when needed, clearly state uncertainty, and never certify structural safety or replace a licensed engineer or site safety officer.\n\nConversation:\n" + history_text)
                )
                answer = response.text
            except Exception as exc:
                st.warning(f"AI chat unavailable; using the demo response. Details: {exc}")
        if not answer:
            answer = ("Demo assistant: I can help outline general planning steps, checklists and questions to ask your engineer. "
                      "For a specific answer, add a Gemini API key. For structural defects, lifting operations, electrical hazards or imminent danger, "
                      "pause the affected work and contact the qualified site lead.")
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
    if st.button("Clear chat history"):
        st.session_state.chat_history = []
        st.rerun()

st.markdown("---")
st.markdown('<div class="small-muted">BuildWise prototype · No external database · Reports are generated in-session · Validate all outputs before operational use.</div>', unsafe_allow_html=True)
