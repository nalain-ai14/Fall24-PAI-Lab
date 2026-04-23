# Wakeel AI — Pakistan Legal Aid Bot
### GenAI + Flask | BSAI 4th Semester Final Project

---

## What This Does

Wakeel AI is a free AI-powered legal aid assistant for Pakistani citizens. Users describe their legal problem in English or Roman Urdu, and the app:

- Identifies the legal category (Tenant Rights, Labour Law, Family Law, etc.)
- Explains relevant Pakistan laws with section numbers
- Shows a **Case Strength Meter** (0–100%)
- Lists user's rights in simple language
- Suggests next steps + which authority to contact
- Drafts legal notices, complaint letters, and FIR applications

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + Flask |
| AI Engine | Grok API — `grok-3-latest` (xAI) |
| Frontend | HTML + CSS + Vanilla JS |
| Session | Flask Sessions |
| Fonts | Google Fonts (Playfair Display + DM Sans) |

---

## Project Structure

```
Legal_Aid_Bot/
│
├── app.py                  ← Main Flask application (Grok API)
├── requirements.txt        ← Python dependencies
├── .env.example            ← Environment variables template
├── .env                    ← Your actual keys (DO NOT share!)
│
├── templates/
│   └── index.html          ← Complete frontend UI
│
├── static/
│   └── style/              ← (reserved for future CSS files)
│
├── .vscode/
│   └── settings.json       ← VS Code workspace settings
│
└── README.md               ← This file
```

---

## Setup Instructions

### Step 1: Clone / Download the project
```bash
cd Desktop
# Place the Legal_Aid_Bot folder here
```

### Step 2: Create virtual environment
```bash
cd Legal_Aid_Bot
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set your API Key
```bash
# Copy the example file
cp .env.example .env

# Open .env and add your xAI (Grok) API key:
# XAI_API_KEY=xai-your-key-here
```

Get your Grok API key at: https://console.x.ai

### Step 5: Run the app
```bash
python app.py
```

### Step 6: Open in browser
```
http://localhost:5000
```

---

##  API Configuration (Grok / xAI)

This project uses the **Groq API**, accessed via the OpenAI-compatible SDK:

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("XAI_API_KEY"),
    base_url="https://api.x.ai/v1",
)

response = client.chat.completions.create(
    model="grok-3-latest",
    max_tokens=1500,
    messages=[...]
)
```

> No special SDK needed — the standard `openai` Python package works with Grok's OpenAI-compatible endpoint.

---

##  Key Features

### 1. Smart Legal Analysis
- Auto-categorizes legal issues
- References real Pakistan laws (PPC, CrPC, PECA 2016, etc.)
- Bilingual support (English + Roman Urdu)

### 2. Case Strength Meter
- Visual 0-100% strength indicator
- Color coded: Green (strong) → Amber (moderate) → Red (weak)

### 3. Document Drafting
- Legal Notice
- Complaint Letter  
- FIR Application
- One-click copy to clipboard

### 4. Quick Topics Sidebar
- 8 pre-built common scenarios
- Click to instantly ask about that topic

---

##  API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Main chat interface |
| `/api/legal-query` | POST | Send legal question, get structured analysis |
| `/api/draft-document` | POST | Generate legal document draft |
| `/api/clear-session` | POST | Clear conversation history |

---

##  Demo Script (For Presentation)

1. Open app → Show clean UI
2. Type: *"Mera landlord mujhe ghar se nikal raha hai bina notice ke"*
3. Show: Category detected → Laws cited → Rights listed → Case strength 78%
4. Click "Draft Legal Notice" → Show generated document
5. Try another: *"My employer fired me without notice"*
6. Show multi-turn conversation memory

---

##  Disclaimer

This app provides general legal information based on Pakistani law. It is NOT a substitute for professional legal advice. Users should consult a licensed Pakistani lawyer for their specific cases.

---

##  Built By

**Nalain** | BSAI 4th Semester | Programming for AI Final Project
```
GenAI + Flask | Groq API | 2026
```
