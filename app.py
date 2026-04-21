import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
import base64

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
def ask_gpt(question, image_file=None):

    system_prompt = """
You are an enterprise IT Service Desk assistant.

IMPORTANT:
- Use ONLY the user's email + screenshot (if provided)
- Do NOT give generic answers
- Identify system, issue, and give SPECIFIC Quick Fix

Respond in this STRICT format:

1. Application/Website:
2. Issue Category:
3. Department:

4. Quick Fix:
- Step 1:
- Step 2:
- Step 3:

5. Detailed Solution:
- Step 1:
- Step 2:
- Step 3:

6. Escalation:
If unresolved, escalate to:
Note:
"""

    content = [{"type": "input_text", "text": question}]

    if image_file:
        image_bytes = image_file.getvalue()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        content.append({
            "type": "input_image",
            "image_url": f"data:image/png;base64,{base64_image}"
        })

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": system_prompt},
                *content
            ],
        }],
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
# 📧 EMAIL INPUT
# ===============================
st.markdown("## 📧 Paste Email / Issue")

email_input = st.text_area(
    "Paste email content or describe issue (you can also upload screenshot below):",
    height=200
)

image_file = st.file_uploader(
    "📎 Drag & drop or upload screenshot of issue",
    type=["png", "jpg", "jpeg"]
)

if image_file:
    st.image(image_file, caption="Uploaded Screenshot", use_column_width=True)

# ===============================
# 🔍 ANALYZE BUTTON
# ===============================
if st.button("Analyze Issue"):

    if email_input.strip() == "" and not image_file:
        st.warning("Please enter issue details or upload screenshot.")

    else:
        combined_input = f"""
User Issue:
{email_input}

Context:
User may have uploaded a screenshot of a webpage or system error.
Use this to identify system and issue.

Instruction:
Provide a precise Quick Fix based ONLY on this issue.
"""

        with st.spinner("Analyzing issue..."):
            result = ask_gpt(combined_input, image_file)

        st.markdown("## 🛠️ Solution")
        st.write(result)

        st.session_state["last_issue"] = combined_input


# ===============================
# ⚡ QUICK ISSUES
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
# 💬 FOLLOW-UP
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