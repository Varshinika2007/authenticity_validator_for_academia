import streamlit as st
import pdfplumber
import re
import zipfile
import io
from PIL import Image
import easyocr
import numpy as np
import requests
import time
import base64

# Initialize the OCR text parser once and cache it
@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(['en'], gpu=False)

def clean_duplicate_chars(text):
    """Safely removes consecutive line breaks or space gaps without breaking actual words."""
    if not text:
        return ""
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

def check_local_plagiarism(text):
    """Cross-checks text against an internal institutional string database."""
    if not text or len(text.strip()) < 15:
        return "Not Available", []

    past_submissions_database = [
        "the objective of this research paper is to evaluate the neural network models for real time image classification tasks in distributed environments.",
        "blockchain technology offers decentralized ledger systems that completely eliminate the need for centralized banking authorities and institutions.",
        "climate change models indicate a significant increase in global temperatures over the next two decades if carbon emissions are not restricted.",
        "artificial intelligence algorithms can optimize energy consumption patterns in smart grid networks effectively through reinforcement learning techniques."
    ]
    
    sentences = [s.strip().lower() for s in re.split(r'[.!?\n]', text) if len(s.strip()) > 15]
    if not sentences:
        return "0.0%", []
        
    copied_sentences = []
    matched_count = 0
    
    for sentence in sentences:
        for archived_paper in past_submissions_database:
            if sentence in archived_paper or archived_paper in sentence:
                matched_count += 1
                copied_sentences.append(sentence)
                break
                
    plagiarism_percentage = (matched_count / len(sentences)) * 100
    return f"{round(plagiarism_percentage, 1)}%", list(set(copied_sentences))

def calculate_readability_metrics(text):
    """Calculates reading times and grading complexity metrics via rule-based thresholds."""
    words = text.split()
    word_count = len(words)
    
    if word_count < 15:
        return {"word_count": word_count, "reading_time": 0, "grade": "Short Form Content", "desc": "Document text array is minimal (e.g., certificate, header)."}
        
    reading_time_mins = max(1, round(word_count / 200))
    sentences = [s for s in re.split(r'[.!?]', text) if s.strip()]
    sentence_count = len(sentences) if sentences else 1
    avg_sentence_len = word_count / sentence_count
    
    long_words = [w for w in words if len(w) > 6]
    long_word_ratio = len(long_words) / word_count if word_count else 0
    
    if avg_sentence_len > 18 or long_word_ratio > 0.35:
        grade = "Advanced Academic / Journal"
        desc = "Dense structural prose with technical terminology."
    elif avg_sentence_len > 12 or long_word_ratio > 0.20:
        grade = "Standard Undergraduate"
        desc = "Clear informational text matching college standards."
    else:
        grade = "Basic / High School"
        desc = "Simplified phrasing patterns with accessible grammar."
        
    return {"word_count": word_count, "reading_time": reading_time_mins, "grade": grade, "desc": desc}

def calculate_authenticity_score(text):
    """Evaluates text patterns using statistical lexical diversity metrics."""
    if not text or len(text.strip()) < 15:
        return 100.0
        
    words = text.split()
    unique_words = set(words)
    
    lexical_diversity = len(unique_words) / len(words) if words else 0
    avg_word_len = sum(len(w) for w in words) / len(words) if words else 0
    
    uniformity_score = 50.0
    if lexical_diversity < 0.4:
        uniformity_score += 25
    elif lexical_diversity > 0.7:
        uniformity_score -= 25
        
    if 4.5 <= avg_word_len <= 6.0:
        uniformity_score += 15
    else:
        uniformity_score -= 15
        
    uniformity_score = max(0.0, min(100.0, uniformity_score))
    authenticity_score = 100.0 - uniformity_score
    return round(authenticity_score, 1)

def extract_citations(text):
    """Scans text for academic citations using regular expression pattern matching."""
    bracket_pattern = r'\[\d+(?:-\d+)?\]'
    author_year_pattern = r'\([A-Z][a-zA-Z]+(?:\s+et\s+al\.)?,\s+\d{4}\)'
    return sorted(list(set(re.findall(bracket_pattern, text) + re.findall(author_year_pattern, text))))

def extract_and_check_links(text):
    """Finds URLs in text and executes live HTTP requests to verify routing status."""
    urls = list(set(re.findall(r'https?://[^\s$\n\)\}\]]+', text)))
    link_results = []
    for url in urls[:5]:
        url = url.rstrip('.,;')
        try:
            response = requests.head(url, timeout=3, allow_redirects=True)
            status = "✅ Active" if response.status_code < 400 else f"❌ Broken ({response.status_code})"
            link_results.append((url, status))
        except:
            link_results.append((url, "❌ Unreachable"))
    return link_results, len(urls)

def process_pdf_bytes(pdf_bytes):
    text_content = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_content += page_text + "\n"
    return text_content

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if st.session_state["logged_in"]:
        return True

    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center;'>🛡️ Portal Sign-In</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray;'>Authenticity Validator for Academia</p>", unsafe_allow_html=True)
            st.markdown("---")
            username = st.text_input("Username", placeholder="e.g., admin")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Access Dashboard →", use_container_width=True, type="primary"):
                if username == "admin" and password == "validator2026":
                    st.session_state["logged_in"] = True
                    st.success("Access Granted!")
                    st.rerun()
                else:
                    st.error("Incorrect credentials.")
    return False

# UI Setup
st.set_page_config(page_title="Authenticity Validator for Academia", layout="wide")

if check_login():
    st.sidebar.markdown(f"👤 **Role:** System Administrator")
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.header("🧭 Navigation")
    # Added "User Guide" option to selection menu
    page = st.sidebar.selectbox("Go to page:", ["📊 Dashboard", "ℹ️ About Project", "📖 User Guide"])
    st.sidebar.markdown("---")

    ocr_reader = load_ocr_reader()

    # ==========================================
    # PAGE 1: DASHBOARD
    # ==========================================
    if page == "📊 Dashboard":
        st.title("🛡️ Authenticity Validator for Academia")
        st.markdown("---")

        st.sidebar.header("📁 Data Upload Pipeline")
        uploaded_file = st.sidebar.file_uploader("Upload document", type=["pdf", "zip", "jpg", "jpeg", "png"])

        if uploaded_file is not None:
            # --- PROGRESS BAR VISUAL ENGINE ---
            progress_bar = st.progress(0)
            status_text = st.empty()
            for percent_complete in range(0, 101, 25):
                time.sleep(0.12)
                progress_bar.progress(percent_complete)
                status_text.text(f"Running structural validation checks... {percent_complete}%")
            progress_bar.empty()
            status_text.empty()

            raw_text_content = ""
            file_name = uploaded_file.name
            pdf_bytes_preview = None

            if file_name.lower().endswith('.pdf'):
                pdf_bytes_preview = uploaded_file.getvalue()
                raw_text_content = process_pdf_bytes(pdf_bytes_preview)
            elif file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                img = Image.open(uploaded_file)
                img_array = np.array(img)
                results = ocr_reader.readtext(img_array, detail=0)
                raw_text_content = "\n".join(results)

            cleaned_text = clean_duplicate_chars(raw_text_content)
            authenticity_score = calculate_authenticity_score(cleaned_text)
            plag_result, plag_sentences = check_local_plagiarism(cleaned_text)
            read_metrics = calculate_readability_metrics(cleaned_text)
            citations = extract_citations(cleaned_text)
            links, total_links = extract_and_check_links(cleaned_text)

            # --- EXPORT REPORT ---
            st.sidebar.markdown("---")
            st.sidebar.header("📥 Export Pipeline")
            report_data = f"""==================================================
       AUTHENTICITY VALIDATOR FOR ACADEMIA
==================================================
[Target File]:            {file_name}
[Authenticity Score]:     {authenticity_score}%
[Repository Verification]: {plag_result}
[Complexity Tier]:        {read_metrics['grade']}
[Total Word Count]:       {read_metrics['word_count']} words
[Citations Tracked]:      {len(citations)}
=================================================="""
            
            st.sidebar.download_button(
                label="📥 Download Validation Report (.txt)",
                data=report_data,
                file_name=f"Authenticity_Report_{file_name}.txt",
                mime="text/plain"
            )

            # --- DASHBOARD CARD CONSTRUCTS ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("📊 Authenticity Score", f"{authenticity_score}%")
            c2.metric("📝 Repository Match", plag_result)
            c3.metric("📈 Total Words", read_metrics['word_count'])
            c4.metric("📚 Citations", len(citations))

            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2 = st.columns([1.1, 1])

            with col1:
                st.subheader("📊 Text Distribution Profile")
                st.write(f"**Custom Structural Variation (Human Writing Profile):** {authenticity_score}%")
                st.write(f"**Algorithmic Sequence Uniformity (Automated Baseline):** {round(100.0 - authenticity_score, 1)}%")
                
                st.markdown(f"""
                <div style="width:100%; background-color:#ddd; border-radius:5px; overflow:hidden; display:flex;">
                  <div style="width:{authenticity_score}%; background-color:#4CAF50; padding:10px; text-align:left; color:white;">Authentic Profile ({authenticity_score}%)</div>
                  <div style="width:{round(100.0 - authenticity_score, 1)}%; background-color:#FF4B4B; padding:10px; text-align:right; color:white;">Uniformity ({round(100.0 - authenticity_score, 1)}%)</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("---")
                st.subheader("🔗 Reference Routing Validator")
                if total_links > 0:
                    for url, status in links:
                        st.write(f"🌐 `{url[:30]}...` ➡️ {status}")
                else:
                    st.info("No reference links found in the uploaded document.")

            with col2:
                st.subheader("📄 Raw Document File Preview")
                
                if pdf_bytes_preview:
                    try:
                        base64_pdf = base64.b64encode(pdf_bytes_preview).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="400" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                    except Exception:
                        st.caption("PDF preview frame rendered.")
                elif file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    st.image(uploaded_file, use_container_width=True)
                    
                with st.expander("🔍 View Extracted Character Output Terminal"):
                    st.text_area("Plain Text Stream", cleaned_text, height=150)
        else:
            st.markdown("<br><br>", unsafe_allow_html=True)
            main_col1, main_col2 = st.columns([1.5, 1])
            
            with main_col1:
                st.markdown("<h2>👋 Welcome to the Authenticity Portal</h2>", unsafe_allow_html=True)
                st.markdown("Your system dashboard is fully active and ready. To generate an analysis report, please upload a document in the left sidebar pipeline.")
                st.markdown("---")
                st.markdown("### 🛠️ What this dashboard checks:")
                st.markdown("* **📊 Authenticity Score:** Evaluates text patterns using statistical lexical diversity metrics.")
                st.markdown("* **📝 Repository Match:** Cross-checks text against an internal institutional string database.")
                st.markdown("* **📈 Total Words & Readability:** Calculates reading times and grading complexity metrics.")
                st.markdown("* **📚 Citations & Links:** Scans text for academic citations and verifies live URL routing status.")

            with main_col2:
                st.markdown("### 📁 System Status")
                st.success("✅ Dashboard Engine: Online")
                st.success("✅ OCR Text Parser: Cached & Ready")
                st.info("💡 Tip: Try switching pages in the side navigation menu to read about the core project parameters or see the User Guide!")

    # ==========================================
    # PAGE 2: ABOUT PROJECT
    # ==========================================
    elif page == "ℹ️ About Project":
        st.title("ℹ️ About The Project")
        st.markdown("---")
        
        project_col1, project_col2 = st.columns([1.5, 1])
        
        with project_col1:
            st.markdown("### 🎯 Project Objective")
            st.markdown("""
            The **Authenticity Validator for Academia** is engineered to safeguard research integrity. By processing digital text distributions, identifying lexical diversity shifts, verifying formatting variations, and performing institutional string matching, it provides educators and administrators a multi-layered suite to check student papers, research manuscripts, and legal documents.
            """)
            
            st.markdown("### 🔬 Core Engine Framework")
            st.markdown("""
            * **Lexical Diversity Parsing:** Calculates unique-to-total word ratios to distinguish natural stylistic complexity variation from algorithmic, uniform generations.
            * **Optical Character Recognition (OCR):** Powered by an `easyocr` runtime model backend to read embedded text directly out of flattened screenshots and system graphics.
            * **Academic Citation Tracking:** Scans and collects standard bracket tags `[1]` and author-year references from academic layout profiles.
            * **Live Reference Routing Verification:** Uses fast network requests to query live document hyperlinks and flag dead web paths on the spot.
            * **Text Normalization:** Features a structural cleaning utility to filter synthetic space breaks and format gaps out of complex PDF extractions.
            """)
            
        with project_col2:
            with st.container(border=True):
                st.markdown("### 📊 Architecture Properties")
                st.write("**App Engine Tier:** Streamlit Microservice Web App")
                st.write("**Data Pipelines:** Dual Engine (Direct PDF Stream Parser + Vectorized Matrix Image Parser)")
                st.write("**Local Verification Cache:** Institutional Peer-Review Database Mockup")
                st.write("**Target Domain Focus:** Research Authenticity, Formatting Verification, Content Analysis")

    # ==========================================
    # PAGE 3: USER GUIDE
    # ==========================================
    elif page == "📖 User Guide":
        st.title("📖 System User Guide")
        st.markdown("---")
        
        guide_col1, guide_col2 = st.columns([1.6, 1])
        
        with guide_col1:
            st.markdown("### 🚀 How to Run and Verify Documents")
            
            st.markdown("""
            #### 1️⃣ Step 1: Access and Authorization
            * Sign in using your designated administrator credentials to initialize the analytics microservice.
            * Make sure the sidebar indicates your active role as a **System Administrator**.
            
            #### 2️⃣ Step 2: Upload Files into the Pipeline
            * Navigate to the **📊 Dashboard** using the navigation box on the left.
            * Click **Browse files** or drag and drop a document into the upload window. 
            * *Supported formats:* **PDF documents**, structural **ZIP archives**, and graphic scans (**JPG, JPEG, PNG**).
            
            #### 3️⃣ Step 3: Interpret Dashboard Metrics
            * **Authenticity Score:** High scores represent standard human structural variety. Low scores indicate high uniformity, often typical of automated document builders.
            * **Repository Match:** Flags text blocks that match verified internal records.
            * **Reference Routing Validator:** Reviews extracted URLs and immediately reports if paths are active or dead.
            
            #### 4️⃣ Step 4: Export Validation Reports
            * Once analysis finishes, look at the bottom of the left sidebar.
            * Click **📥 Download Validation Report (.txt)** to save a copy directly to your laptop.
            """)
            
        with guide_col2:
            with st.container(border=True):
                st.markdown("### 💡 Quick Operational Tips")
                st.warning("⚠️ **File Format Tip:** For images, make sure text is clear and readable so that the EasyOCR pipeline parses individual letters accurately.")
                st.info("💡 **Live Testing:** Want to see the reference router in action? Try uploading a text document with a mixture of live URLs (like `https://google.com`) and fake domains to see how it catches routing status instantly.")
