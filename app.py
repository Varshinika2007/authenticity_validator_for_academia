import streamlit as st
import hashlib
import os
import difflib
from fpdf import FPDF
import PyPDF2
import sqlite3
import pandas as pd
from datetime import datetime

# --- Page Setup ---
st.set_page_config(page_title="Ava - Academic Validator", page_icon="🛡️", layout="wide")

# --- CSS Styling ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    .stApp { background: linear-gradient(135deg, #f0f2f6 0%, #d1d8e0 100%); }
    .login-card { background: #ffffff; padding: 2rem; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: 50px auto; max-width: 450px; text-align: center; }
    .dashboard-bg { background: #ffffff; padding: 30px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    div.stButton > button { background-color: #008080 !important; color: white !important; border-radius: 5px; width: 100%; }
    .guide-box { background-color: #e8f4f4; padding: 20px; border-left: 5px solid #008080; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- Database & Helper Functions ---
def init_db():
    conn = sqlite3.connect('submissions.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS history (username text, file_hash text, score real, date text)')
    conn.commit()
    conn.close()

init_db()

def extract_text(file):
    if file.name.endswith('.pdf'):
        reader = PyPDF2.PdfReader(file)
        return "".join([p.extract_text() or "" for p in reader.pages])
    return file.read().decode(errors='ignore')

def generate_report(file_hash, similarity):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Ava - Authenticity Report", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Hash: {file_hash[:20]}...", ln=True)
    pdf.cell(200, 10, txt=f"Similarity: {similarity:.2f}%", ln=True)
    report_filename = "report.pdf"
    pdf.output(report_filename)
    return report_filename

def check_plagiarism(content):
    ref_folder = "reference_docs"
    if not os.path.exists(ref_folder): os.makedirs(ref_folder)
    files = [f for f in os.listdir(ref_folder) if f.endswith(('.txt', '.pdf'))]
    if not files: return 0.0
    max_sim = 0
    for f_name in files:
        with open(os.path.join(ref_folder, f_name), 'r', encoding='utf-8', errors='ignore') as f:
            ref_content = f.read()
        sim = difflib.SequenceMatcher(None, content, ref_content).ratio()
        if sim > max_sim: max_sim = sim
    return max_sim * 100

# --- App Logic ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'show_guide' not in st.session_state: st.session_state.show_guide = False

if not st.session_state.logged_in:
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.title("Ava 🛡️")
    st.subheader("Academic Authenticity Portal")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == "admin" and pwd == "password123":
            st.session_state.logged_in = True
            st.rerun()
        else: st.error("Invalid Credentials!")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    with st.sidebar:
        st.subheader("⚙️ Navigation")
        if st.button("📖 User Guide"): st.session_state.show_guide = True
        if st.button("🏠 Dashboard"): st.session_state.show_guide = False
        if st.button("📊 View History"):
            conn = sqlite3.connect('submissions.db')
            st.dataframe(pd.read_sql_query("SELECT * FROM history", conn))
            conn.close()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown('<div class="dashboard-bg">', unsafe_allow_html=True)
    if st.session_state.show_guide:
        st.header("📖 User Guide")
        st.markdown('<div class="guide-box">1. Upload your document.\n2. Click "Analyze".\n3. Download your report.</div>', unsafe_allow_html=True)
    else:
        st.header("Ava Dashboard")
        uploaded_file = st.file_uploader("Upload Document (.txt or .pdf)", type=['txt', 'pdf'])
        if uploaded_file and st.button("Analyze Document"):
            with st.spinner('Analyzing...'):
                text = extract_text(uploaded_file)
                hash_val = hashlib.sha256(text.encode()).hexdigest()
                score = check_plagiarism(text)
                
                conn = sqlite3.connect('submissions.db')
                c = conn.cursor()
                c.execute("INSERT INTO history VALUES (?, ?, ?, ?)", ("admin", hash_val, score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                
                st.metric("Similarity Score", f"{score:.2f}%")
                st.progress(score / 100)
                report_path = generate_report(hash_val, score)
                with open(report_path, "rb") as f:
                    st.download_button("📥 Download PDF", f, file_name="report.pdf")
    st.markdown('</div>', unsafe_allow_html=True)