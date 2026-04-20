import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv

# ---- Load env (local only) ----
load_dotenv()

# ---- Page Config ----
st.set_page_config(page_title="Service Desk AI Portal", page_icon="🤖", layout="wide")

# ---- OpenAI Client ----
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.error("🚨 OpenAI API key not found. Set it in .env or Streamlit secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

# ---- Styles ----
st.markdown("""
<style>
.hero {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
    padding: 32px;
    border-radius: 20px;
    margin-bottom: 24px;
}
</style>
""", unsafe_allow_html=True)

# ---- GPT Helper ----
def ask_gpt(question):

    system_prompt = """
You are an enterprise IT Service Desk assistant.

Analyze the issue and respond in this STRICT format:

1. Issue Category:
2. Department:
3. Step-by-Step Solution:
- Step 1:
  - Sub-step
- Step 2:
- Step 3:

4. Escalation:
If unresolved, escalate to:
Note:

Departments:
MOH_support (Main)
MT_support
NEFRMCAF_support
CHASMHL_support
CIDC_support
FSAE_support
HSMS_Alerts
MediClaims_Alerts
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
    )

    return response.output[0].content[0].text


# ---- Hero ----
st.markdown("""
<div class="hero">
    <h1>🤖 Service Desk AI Portal</h1>
    <p>Paste email or describe your issue for AI-powered support.</p>
</div>
""", unsafe_allow_html=True)


# ===============================
# 📧 EMAIL INPUT SECTION (NEW)
# ===============================
st.markdown("## 📧 Paste Email / Issue")

email_input = st.text_area(
    "Paste email content or describe issue (you can also upload screenshot below):",
    height=200
)

# 🆕 Add image in SAME section (acts like paste)
image_file = st.file_uploader(
    "📎 Paste/Upload screenshot of issue (optional)",
    type=["png", "jpg", "jpeg"],
    label_visibility="collapsed"
)

if st.button("Analyze Issue"):
    if email_input.strip() == "":
        st.warning("Please enter issue details.")
    else:
        with st.spinner("Analyzing issue..."):
            result = ask_gpt(email_input)

        st.markdown("## 🛠️ Solution")
        st.write(result)

        st.session_state["last_issue"] = email_input


# ===============================
# ⚡ QUICK ISSUE BUTTONS (OPTIONAL)
# ===============================
st.divider()
st.markdown("## ⚡ Quick Issues")

quick_issues = [
    "VPN not connecting",
    "Outlook not syncing",
    "Account locked",
    "Teams microphone not working"
]

cols = st.columns(4)

for col, issue in zip(cols, quick_issues):
    if col.button(issue):
        with st.spinner("Analyzing..."):
            result = ask_gpt(issue)

        st.markdown("## 🛠️ Solution")
        st.write(result)

        st.session_state["last_issue"] = issue


# ===============================
# 💬 FOLLOW-UP SECTION
# ===============================
if "last_issue" in st.session_state:

    st.divider()
    st.markdown("### 💬 Still not resolved? Ask more details")

    follow_up = st.text_input("Describe your issue further:")

    if st.button("Submit follow-up"):
        if follow_up.strip() == "":
            st.warning("Please enter more details.")
        else:
            combined_query = f"""
Original issue:
{st.session_state["last_issue"]}

Follow-up:
{follow_up}
"""
            with st.spinner("Analyzing further..."):
                answer = ask_gpt(combined_query)

            st.markdown("### 🤖 Additional Help")
            st.write(answer)


# ---- Footer ----
st.markdown("---")
st.caption("Enterprise Service Desk • AI-powered troubleshooting")