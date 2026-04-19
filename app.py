import streamlit as st
import requests
import pandas as pd
import openai
import msal
import uuid
import base64
from pdf2image import convert_from_bytes
from PIL import Image
import io

# ---------------- CONFIG ----------------
st.title("📧 Service Desk Research Tool (Emails + Screenshots + PDFs)")

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
    url = "https://graph.microsoft.com/v1.0/me/messages?$top=10"
    response = requests.get(url, headers=headers)
    return response.json().get("value", [])

# ---------------- TEXT ANALYSIS ----------------
def analyze_email(subject, body):
    prompt = f"""
You are an IT Service Desk analyst.

Subject: {subject}
Email Body: {body}

Tasks:
1. Identify application/system (if any)
2. Classify issue type
3. Summarize problem
4. Identify root cause
5. Provide resolution steps
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content

# ---------------- IMAGE ANALYSIS ----------------
def analyze_image(file_bytes):
    base64_image = base64.b64encode(file_bytes).decode("utf-8")

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
You are an IT Service Desk expert.

From this screenshot:
1. Identify the application/website
2. Extract any visible URL
3. Describe the issue
4. Suggest root cause
5. Provide resolution steps
6. Suggest help/documentation links
"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=800
    )

    return response.choices[0].message.content

# ---------------- PDF → IMAGE ----------------
def pdf_to_images(pdf_file):
    images = convert_from_bytes(pdf_file.read())
    image_bytes_list = []

    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        image_bytes_list.append(buf.getvalue())

    return image_bytes_list

# ---------------- UI ----------------

st.header("📊 Analyze Outlook Emails")

if st.button("Analyze Emails"):
    token = st.session_state.token["access_token"]
    emails = fetch_emails(token)

    rows = []
    for e in emails:
        subject = e.get("subject", "")
        body = e.get("body", {}).get("content", "")

        analysis = analyze_email(subject, body)

        rows.append({
            "Type": "Email",
            "Subject/File": subject,
            "Analysis": analysis
        })

    df = pd.DataFrame(rows)
    st.dataframe(df)

    st.download_button(
        "⬇ Download Email Analysis",
        df.to_csv(index=False),
        "email_analysis.csv"
    )

# ---------------- FILE UPLOAD ----------------

st.header("🖼️ Analyze Screenshot / PDF")

uploaded_file = st.file_uploader(
    "Upload Screenshot or PDF",
    type=["png", "jpg", "jpeg", "pdf"]
)

if uploaded_file:
    results = []

    if uploaded_file.type == "application/pdf":
        st.info("Processing PDF...")
        images = pdf_to_images(uploaded_file)

        for i, img_bytes in enumerate(images):
            st.write(f"Analyzing page {i+1}...")
            result = analyze_image(img_bytes)

            results.append({
                "Type": "PDF Page",
                "Subject/File": f"{uploaded_file.name} - Page {i+1}",
                "Analysis": result
            })

    else:
        st.info("Processing Image...")
        file_bytes = uploaded_file.read()
        result = analyze_image(file_bytes)

        results.append({
            "Type": "Image",
            "Subject/File": uploaded_file.name,
            "Analysis": result
        })

    df = pd.DataFrame(results)
    st.dataframe(df)

    st.download_button(
        "⬇ Download Analysis",
        df.to_csv(index=False),
        "image_pdf_analysis.csv"
    )
