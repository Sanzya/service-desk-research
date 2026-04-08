import streamlit as st
import requests
import pandas as pd
import openai
import msal
import uuid


git add .
git commit -m "Initial commit: Service Desk Research Analyzer"
git push origin main


# ---------------- CONFIG ----------------
st.title("📧 Service Desk Email Research Tool")

CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
TENANT_ID = st.secrets["TENANT_ID"]
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["Mail.Read", "User.Read"]

openai.api_key = st.secrets["OPENAI_API_KEY"]

# ---------------- MSAL CLIENT ----------------
if "msal_app" not in st.session_state:
    st.session_state.msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )

# ---------------- AUTH FLOW ----------------
if "token" not in st.session_state:
    auth_url = st.session_state.msal_app.get_authorization_request_url(
        SCOPE,
        state=str(uuid.uuid4()),
        redirect_uri="http://localhost:8501"
    )
    st.markdown(f"### 🔐 [Sign in with Microsoft]({auth_url})")
    st.stop()

# ---------------- GRAPH CALL ----------------
def fetch_emails(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://graph.microsoft.com/v1.0/me/messages?$top=15"
    response = requests.get(url, headers=headers)
    return response.json().get("value", [])

# ---------------- OPENAI ANALYSIS ----------------
def analyze_email(subject, body):
    prompt = f"""
You are an IT Service Desk analyst.

Subject: {subject}
Email Body: {body}

Tasks:
1. Classify issue type
2. Summarize problem
3. Identify possible root cause
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content

# ---------------- UI ACTION ----------------
if st.button("📊 Analyze My Outlook Emails"):
    token = st.session_state.token["access_token"]
    emails = fetch_emails(token)

    rows = []
    for e in emails:
        subject = e.get("subject", "")
        body = e.get("body", {}).get("content", "")
        analysis = analyze_email(subject, body)

        rows.append({
            "Subject": subject,
            "AI Analysis": analysis
        })

    df = pd.DataFrame(rows)
    st.dataframe(df)

    st.download_button(
        "⬇ Download Research CSV",
        df.to_csv(index=False),
        "service_desk_research.csv"
    )
``
