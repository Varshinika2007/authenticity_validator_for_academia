# Authenticity Validator for Academia

An automated, real-time web application designed to safeguard academic integrity. This tool analyzes documents for potential AI-generated patterns, plagiarism, and reference validity.

## 🚀 Features

* **Multi-Format Support:** Processes PDFs, images, and archives.
* **Authenticity Scoring:** Uses lexical diversity metrics to evaluate text patterns.
* **Citation & Link Tracking:** Automatically extracts academic citations and validates URL routing status.
* **OCR Integration:** Powered by `easyocr` to extract text from images and scanned documents.
* **Secure Portal:** Includes a protected sign-in gate for administrators.

## 🛠️ Tech Stack

* **Framework:** Streamlit
* **OCR Engine:** EasyOCR
* **Data Processing:** pdfplumber, NumPy, Pillow
* **Web Services:** Requests (for URL verification)

## 📋 Installation

To run this project locally, ensure you have Python installed, then follow these steps:

1. **Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/authenticity-validator.git
cd authenticity-validator

```


2. **Install dependencies:**
```bash
pip install -r requirements.txt

```


3. **Run the application:**
```bash
python -m streamlit run app.py

```



## 🔐 Login Credentials

* **Username:** `admin`
* **Password:** `validator2026`

## 📊 How to Use

1. Access the application via the browser.
2. Sign in using your credentials.
3. Use the sidebar to upload a PDF or image.
4. View the dashboard metrics and download the validation report.

---

