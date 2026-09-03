<div align="center">

# 🤖 Ultimate AI Sales Copilot (Call Center Agent)

### مساعد المبيعات الذكي بالذكاء الاصطناعي لمراكز الاتصال والوساطة المالية

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com)
[![WebSockets](https://img.shields.io/badge/WebSockets-Real--Time-blueviolet.svg)](https://websockets.readthedocs.io/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-2.0%20Flash-orange.svg)](https://ai.google.dev/)
[![Language Support](https://img.shields.io/badge/Language-Arabic%20RTL%20%7C%20Dialects-gold.svg)](#)

*An enterprise-grade, real-time AI copilot designed for financial brokerage and fintech call center sales agents, specialized in the Arab and MENA markets.*

[Overview](#-overview) • [Key Features](#-key-features) • [Architecture](#-system-architecture) • [Quick Start](#-quick-start) • [Installation](#-installation-guide) • [Usage Guide](#-detailed-usage-walkthrough) • [API Reference](#-api-reference)

---

</div>

## 🌟 Overview

In the high-stakes world of financial brokerage sales (CFDs, Forex, Global Equities, and Crypto), conversion rates depend on split-second decisions. Sales agents must handle complex customer psychology, answer nuanced regulatory and Sharia-compliance questions, counter competitor comparisons, and avoid legal compliance violations — all in real time.

**Ultimate AI Sales Copilot** acts as an invisible, sub-second AI assistant during live phone calls. It transcribes audio, analyzes caller personality, detects customer objections, calculates real-time profit potential using the **3M Model**, and suggests copy-ready Arabic replies strictly grounded in your company's training documents.

> 📖 **Architectural Whitepaper**: For a complete scientific and psychological study of this system, see [`دراسة بناء نموذج تداول واستثمار.md`](دراسة%20بناء%20نموذج%20تداول%20واستثمار.md).

---

## ⚡ Key Features

### 🎙️ 1. Live Speech-to-Text & Sub-Second Latency
- Native browser **Web Speech API** integration with live audio level visualization.
- Bidirectional **WebSocket streaming** (`/ws/call/{agent_id}`) for instantaneous analysis with minimal latency (<200ms).

### 🧠 2. Real-Time Client Personality Classification
Automatically scores customer intent, dialect patterns, and sentiment within the first 60 seconds of a call into 4 core psychological profiles:
- **Emotional (عاطفي)**: Reassurance, real-life success stories, Islamic account emphasis, and gentle closing.
- **Analyst (محلل)**: Exact spread numbers, zero-fee details, competitive comparisons, and license disclosures.
- **Leader (قائد)**: Acknowledging expertise, exclusive high-tier accounts, and smart urgency.
- **Nice / Hesitant (لطيف)**: Micro-commitments, trial accounts, and decisive time frames.

### ⚔️ 3. Instant Objection Battle Cards
Pre-configured battle cards pop up instantly when specific Arabic triggers are uttered:
- **Sharia & Islamic Accounts (اعتراض الشرعية)**: Zero overnight fees (Swap-free), legitimate spot trading, Halal Saudi/Aramco stock availability.
- **Scam & Trust Concerns (الخوف من النصب)**: Global regulatory tier licenses (FSC, FSCA, VFSC), segregated client bank accounts, OTP & SSL security.
- **Fear of Financial Loss (الخوف من الخسارة)**: Risk mitigation tools (Stop Loss / Take Profit), educational academy.
- **High Commissions & Spreads (العمولات والسبريد)**: Raw spread transparency starting from 0.0 pips.
- **Competitor Comparisons (المنافسين)**: Instant battle cards against brokers like Exness, XTB, IC Markets, and Pepperstone.

### 📊 4. 3M Market Opportunity Engine (*Mover → Market → Movement*)
- Dynamically links real-time financial market movements (Gold, Oil, NASDAQ, Bitcoin, Aramco) to the client's conversation.
- Instantly calculates expected profit scenarios based on deposit size and leverage (e.g., "$1,000 deposit on Gold movement = $3,000 potential profit").

### 🛡️ 5. Real-Time Regulatory Compliance Guardrail
Actively protects your brokerage from financial regulatory fines:
- ⛔ **Guaranteed Profit Claims**: Detects and penalizes phrases like *"أضمن لك"* or *"بدون خسارة"*.
- ⛔ **False Identity / Impersonation**: Flags unauthorized titles like *"أنا المدير العام"*.
- ⚠️ **Inappropriate Religious Oaths**: Flags inappropriate swearing like *"والله العظيم أضمن لك"*.
- ⚠️ **High-Pressure Tactics**: Flags unethical coercion.
- Live **Compliance Score Meter (0-100%)** displayed on the agent's screen.

### 🏆 6. Live Agent Performance Scorer
Scores the agent dynamically during the call across 10 best-practice sales standards:
- Greeting & using client's name.
- Asking open-ended discovery questions.
- Explaining risk management (Stop Loss).
- Using social proof.
- Attempting structured closing techniques.

### ✨ 7. Grounded Gemini AI Suggestions (Anti-Hallucination)
- Powered by **Google Gemini 2.0 Flash** via the `google-genai` SDK.
- Prompt-engineered to **strictly answer only from ingested training files and company RAG context**.
- Prevents fabricated numbers, hallucinations, or unverified claims.

### 📁 8. Dynamic RAG Knowledge Base & Document Processor
- Ingests **PDF, DOCX, TXT, and JSON** files.
- Automatically chunks and indexes documents with TF-IDF vectorization and cosine similarity.
- Built-in semantic caching for high-frequency queries (<20ms response time).

### 🎬 9. Multi-Turn Interactive Call Simulator
- Test and train agents offline using pre-scripted multi-turn Arabic call scenarios:
  - Ahmed Al-Khalidi (Emotional Caller)
  - Mohammed Al-Ali (Analyst Caller)
  - Khaled Al-Mansoor (Leader Caller)
  - Sarah Al-Omari (Nice / Hesitant Caller)
- Adjustable playback speed (0.5x to 2x).

### 🎙️ 10. Post-Call Audio Recording Analyzer
- Upload completed call audio files (`.mp3`, `.wav`, `.m4a`, `.ogg`, `.webm`, `.flac`).
- Utilizes Gemini's multimodal audio engine to transcribe speaker diarization (Agent vs. Client).
- Produces a comprehensive audit: Executive Summary, Agent Strengths, Critical Weaknesses, Objection Effectiveness, and Better Alternatives.

---

## 🏛️ System Architecture

```
                                  ┌────────────────────────┐
                                  │      Sales Agent       │
                                  │ (Microphone / Browser) │
                                  └───────────┬────────────┘
                                              │ WebSockets (Audio STT / Text)
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                FastAPI Server (main.py)                                     │
│                                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │    Client Classifier    │  │    Objection Handler    │  │      Compliance Monitor     │  │
│  │  (client_classifier.py) │  │  (objection_handler.py) │  │   (compliance_monitor.py)   │  │
│  └─────────────────────────┘  └─────────────────────────┘  └─────────────────────────────┘  │
│                                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │    Market 3M Engine     │  │   Competitor Engine     │  │     Agent Performance       │  │
│  │   (market_engine.py)    │  │ (competitor_engine.py)  │  │   Scorer (agent_scorer.py)  │  │
│  └─────────────────────────┘  └─────────────────────────┘  └─────────────────────────────┘  │
│                                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                       Smart Suggestion Engine (suggestion_engine.py)                  │  │
│  └───────────────────────────┬───────────────────────────────────────────┬───────────────┘  │
│                              │                                           │                  │
│                              ▼                                           ▼                  │
│               ┌─────────────────────────────┐             ┌──────────────────────────────┐  │
│               │      Local RAG Engine       │             │       Gemini AI Engine       │  │
│               │       (rag_engine.py)       │             │      (gemini_engine.py)      │  │
│               └──────────────┬──────────────┘             └──────────────┬───────────────┘  │
└──────────────────────────────┼───────────────────────────────────────────┼──────────────────┘
                               ▼                                           ▼
                 ┌───────────────────────────┐               ┌───────────────────────────┐
                 │ Local Knowledge & Uploads │               │      Google Gemini API    │
                 │  (data/knowledge_base)    │               │     (gemini-2.0-flash)    │
                 └───────────────────────────┘               └───────────────────────────┘
```

---

## 🚀 Quick Start

Launch the entire application with one command using the automated quick start script:

```bash
git clone https://github.com/gmudz/UltimateCallCenterAgent.git
cd UltimateCallCenterAgent
chmod +x quickstart.sh
./quickstart.sh
```

The script will automatically:
1. Check for Python 3.10+.
2. Set up a dedicated virtual environment in `./venv`.
3. Install all required dependencies.
4. Create your `.env` configuration.
5. Initialize the SQLite user database.
6. Launch the server on `http://localhost:8000`.

---

## 📦 Installation Guide

### Prerequisites
- **Python 3.10, 3.11, or 3.12** installed on your system.
- **Google Gemini API Key** (Free from [Google AI Studio](https://aistudio.google.com/)).

### Step-by-Step Manual Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/gmudz/UltimateCallCenterAgent.git
cd UltimateCallCenterAgent
```

#### 2. Create and Activate a Virtual Environment
```bash
# On Linux / macOS
python3 -m venv venv
source venv/bin/activate

# On Windows (cmd/PowerShell)
python -m venv venv
.\venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure Environment Variables
Copy the template configuration:
```bash
cp .env.example .env
```

Edit `.env` and add your Google Gemini API key:
```ini
GEMINI_API_KEY=AIzaSy...your_gemini_api_key...
PORT=8000
```
*(Note: You can also set the Gemini API key directly from the web Admin portal).*

#### 5. Start the Application
```bash
python main.py
# Or with uvicorn directly:
uvicorn main.py:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser and navigate to: **`http://localhost:8000`**

---

## 🔑 Default Accounts & Access

When started on a clean database, the system automatically initializes the default administrator:

| Username | Password | Role | Permissions |
| :--- | :--- | :--- | :--- |
| **`admin`** | **`admin123`** | `admin` | Full Access (Dashboard, Admin Portal, Uploads, Users, Analytics, Training) |
| *(Agent accounts)* | *(Set by admin)* | `agent` | Sales Dashboard, Training Center, Analytics |

> 🔒 **Security Notice**: Change the default admin password immediately in a production environment via `/users`.

---

## 🖥️ Detailed Usage Walkthrough

### 1. Live Agent Dashboard (`/`)
- **Microphone Listening**: Click **"تشغيل الميكروفون"** to capture live speech via the browser's speech recognition.
- **Manual Input**: Type sentences into the text bar and toggle the speaker between **👤 عميل (Client)** and **🎧 موظف (Agent)** to test real-time detections.
- **Battle Cards & Nudges**: As soon as a client mentions an objection (e.g. *"هل تداولكم حلال؟"* or *"أخاف من النصب"*), the relevant card expands with bullet points.
- **3M Opportunities**: When commodities or indices are mentioned, the 3M card calculates estimated profits dynamically.
- **Live Compliance Score**: Watches the agent's statements and displays a color-coded compliance rating (Green = Excellent, Yellow = Warning, Red = Critical violation).

### 2. Interactive Simulator
- Click **"وضع التجريب"** on the top toolbar.
- Choose one of the 4 built-in realistic Arabic scenarios.
- Set playback speed (1x, 1.5x, 2x) and click **"▶ بدء المحاكاة"**.
- Watch the copilot dynamically categorize the caller, display battle cards, trigger compliance checks, and formulate Gemini answers in real-time.

### 3. Admin & Document Knowledge Ingestion (`/admin`)
- Upload official sales presentations, commission sheets, and training manuals in **PDF, DOCX, TXT, or JSON**.
- The file processor extracts text, breaks it into chunks, and embeds it directly into the RAG knowledge base.
- Configure or update your **Google Gemini API Key** securely.

### 4. Post-Call Audio Analyzer (`/admin`)
- Upload audio recordings of completed calls (`.mp3`, `.wav`, `.m4a`, etc.).
- The system transcribes the entire conversation and provides an automated coaching report with:
  - Call Summary
  - Agent Strengths & Weaknesses
  - Effectiveness of objection handling
  - Suggested alternative phrasing

### 5. Sales Training Center (`/training`)
- Interactive portal for onboarding junior agents.
- Provides practical exercises on handling tough objections, building trust, and applying the 3M framework.

### 6. Analytics & Reports (`/analytics`)
- Aggregated metrics across calls: Total Calls, Average Compliance Score, Conversion Rate, Personality Type Distribution, and Most Common Objections.

### 7. User Management (`/users`)
- Administrators can invite new sales agents, create passwords, toggle active status, and assign roles (`admin` vs `agent`).

---

## 📡 API Reference

### REST Endpoints

| Method | Route | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/login` | Public | Authenticates user and sets HTTP-only session cookie |
| `POST` | `/api/logout` | Public | Clears session cookie |
| `GET` | `/api/me` | Authenticated | Returns current authenticated user profile |
| `GET` | `/api/health` | Public | Engine health check and RAG stats |
| `GET` | `/api/market-data` | Authenticated | Real-time simulated market instruments and trending assets |
| `GET` | `/api/3m/{symbol}` | Authenticated | Calculates 3M opportunity based on symbol, investment, leverage |
| `GET` | `/api/knowledge` | Authenticated | Query RAG knowledge base (`?q=search_query`) |
| `GET` | `/api/battle-cards`| Authenticated | Returns all pre-configured objection battle cards |
| `GET` | `/api/scenarios` | Authenticated | Lists available simulation scenarios |
| `GET` | `/api/analytics` | Authenticated | Aggregated call statistics and KPIs |
| `POST` | `/api/upload` | Admin | Upload training documents (PDF, DOCX, TXT, JSON) |
| `GET` | `/api/documents` | Admin | List all uploaded training documents |
| `DELETE`| `/api/documents/{id}`| Admin | Delete document and prune its RAG vectors |
| `POST` | `/api/upload-recording` | Admin | Upload call audio for Gemini transcription and analysis |
| `GET` | `/api/recordings` | Admin | List analyzed call recordings |
| `POST` | `/api/gemini-key` | Admin | Save Gemini API key |
| `GET` | `/api/users` | Admin | List all users |
| `POST` | `/api/users` | Admin | Create a new user account |
| `POST` | `/api/users/{id}/toggle` | Admin | Enable/disable user account |

### WebSocket Endpoint

```
ws://localhost:8000/ws/call/{agent_id}
```

#### Client Messages (Send to WebSocket):
```json
// Start a simulated call scenario
{"action": "start_demo", "scenario_id": "emotional_client", "speed": 1.0}

// Send live spoken or typed text
{"action": "process_text", "speaker": "client", "text": "أنا خايف من الخسارة"}

// Search knowledge base
{"action": "search_knowledge", "query": "حساب إسلامي"}
```

#### Server Analysis Response (Received from WebSocket):
```json
{
  "type": "analysis",
  "speaker": "client",
  "text": "أنا خايف من الخسارة",
  "classification": {
    "type": "emotional",
    "name_ar": "عاطفي",
    "confidence": 0.85
  },
  "objections": [
    {
      "card": {
        "id": "loss",
        "title_ar": "اعتراض الخوف من الخسارة"
      }
    }
  ],
  "compliance_score": { "score": 100, "status": "ممتاز" },
  "suggestions": {
    "recommended_response": "أفهم خوفك تماماً، وهذا شعور طبيعي لكل مستثمر...",
    "stage": { "id": "objection_handling", "name": "معالجة اعتراض" }
  }
}
```

---

## 📂 Project Directory Structure

```
UltimateCallCenterAgent/
├── main.py                     # FastAPI server, WebSocket hub, routing & auth
├── requirements.txt            # Python dependencies
├── quickstart.sh               # Automated one-click setup script
├── .env.example                # Configuration template
├── .gitignore                  # Git exclusions for secrets, venv, and uploads
├── README.md                   # Complete documentation
├── دراسة بناء نموذج تداول واستثمار.md  # Architectural and scientific whitepaper
│
├── engine/                     # Core Python Intelligence Engines
│   ├── client_classifier.py    # Arabic client personality classifier
│   ├── objection_handler.py    # Battle cards for sales objections
│   ├── market_engine.py        # 3M Model & financial opportunity calculator
│   ├── compliance_monitor.py   # Real-time regulatory violation detector
│   ├── suggestion_engine.py    # Smart coaching suggestions from best scripts
│   ├── agent_scorer.py         # Live sales performance scoring
│   ├── competitor_engine.py    # Competitor intelligence & follow-up messages
│   ├── gemini_engine.py        # Google Gemini API integration (anti-hallucination)
│   ├── rag_engine.py           # In-memory TF-IDF vectorizer & semantic cache
│   ├── file_processor.py       # PDF/DOCX/TXT/JSON parser & chunker
│   ├── call_analyzer.py        # Multimodal Gemini audio transcription & audit
│   ├── call_simulator.py       # Multi-turn demo call scenario streamer
│   └── auth.py                 # SQLite, bcrypt & JWT authentication
│
├── data/                       # Structured Knowledge & Storage
│   ├── knowledge_base.json     # Seed knowledge base (company, terms, features)
│   ├── best_employee_scripts.json # Top-performing employee sales scripts
│   ├── competitor_intelligence.json # Competitor comparisons & messaging templates
│   ├── demo_scenarios.json     # Pre-scripted Arabic simulation calls
│   ├── gemini_config.json.example # Template for Gemini config
│   ├── uploads/                # Directory for uploaded training documents
│   └── recordings/             # Directory for uploaded audio recordings
│
└── static/                     # Frontend Interface (HTML5/CSS3/Vanilla JS)
    ├── index.html              # Main Live Agent Dashboard
    ├── admin.html              # Document Ingestion & Settings Portal
    ├── analytics.html          # Performance & Analytics KPI Dashboard
    ├── training.html           # Agent Training Portal
    ├── users.html              # User Management Portal
    ├── login.html              # User Authentication Page
    ├── css/
    │   └── style.css           # Modern RTL Dark Glassmorphism Stylesheet
    └── js/
        └── app.js              # WebSocket client, Web Speech API & UI manager
```

---

## 🔒 Security & Best Practices

- **Never commit `.env` or `data/gemini_config.json`**: These contain API keys and are excluded via `.gitignore`.
- **JWT Authentication**: User sessions are protected with HTTP-only, SameSite cookies.
- **Local RAG Grounding**: The Gemini prompt strictly forbids answering beyond provided training documents to ensure regulatory safety.
- **Segregated Storage**: Uploaded audio recordings and training files are stored in distinct directories with input validation.

---

## 🤝 Contributing

Contributions are welcome! Whether it's adding new Arabic dialect patterns, supporting additional CRM integrations (Salesforce, HubSpot, Panda CRM), or improving STT latency:

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License

This project is open-source software licensed under the [Apache 2.0 License](LICENSE).

---

<div align="center">
  <sub>Built with ❤️ for high-performance financial sales teams across the Arab world.</sub>
</div>
