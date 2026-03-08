# ⚖️ LegalLease — Live AI Legal Partner

> **Gemini Live Agent Challenge** — Redefining legal contract creation through real-time voice conversation.

LegalLease is a **voice-to-voice AI legal assistant** that helps users create professionally drafted legal contracts through natural conversation. Instead of filling out forms or reading legal jargon, users simply _talk_ to LegalLease — and it listens, asks clarifying questions, and generates comprehensive contracts in real-time.

[![Built with Gemini](https://img.shields.io/badge/Built%20with-Gemini%20Live%20API-blue?style=for-the-badge&logo=google)](https://ai.google.dev/)
[![Hackathon](https://img.shields.io/badge/Hackathon-Gemini%20Live%20Agent%20Challenge-gold?style=for-the-badge)](https://geminiliveagentchallenge.devpost.com/)

---

## 🎯 Problem

Creating legal contracts is **expensive, intimidating, and inaccessible** for most people:

- Lawyers charge $200-500/hr for basic contract drafting
- Legal templates are confusing and filled with jargon
- Online form-based generators feel impersonal and miss nuance
- Most people don't know what clauses they need

## 💡 Solution

LegalLease uses **Gemini's Live API** to create a conversational legal partner that:

- 🗣️ **Talks naturally** — speak your needs, get spoken responses back
- 📋 **Covers 40+ contract types** across 5 jurisdictions
- 📝 **Generates comprehensive contracts** with 16+ standard legal sections
- 🔄 **Real-time** — bidirectional audio streaming, not turn-based chat
- 📄 **Instant download** — save your contract as PDF immediately

## 🏗️ Architecture

```
┌─────────────────────┐                    ┌──────────────────────────┐
│   Next.js Frontend  │                    │  Google Cloud Run        │
│                     │                    │                          │
│  AudioWorklet       │◄── WebSocket ────►│  FastAPI + ADK Runner    │
│  (PCM 16kHz capture)│    (bidirectional) │         │                │
│                     │                    │         ▼                │
│  Web Audio API      │                    │  Gemini Live API         │
│  (24kHz playback)   │                    │  (2.5 Flash Native Audio)│
│                     │                    │                          │
│  Contract Preview   │                    │  Firebase (Auth/Data)    │
│  + PDF Download     │                    │                          │
└─────────────────────┘                    └──────────────────────────┘
```

### Tech Stack

| Component       | Technology                                                     |
| --------------- | -------------------------------------------------------------- |
| **Frontend**    | Next.js 15, TypeScript, Web Audio API, AudioWorklet            |
| **Backend**     | Python 3.11, FastAPI, WebSockets                               |
| **Agent**       | Google ADK (Agent Development Kit)                             |
| **LLM**         | Gemini 2.5 Flash Native Audio (Live API / bidiGenerateContent) |
| **Auth & Data** | Firebase Admin SDK                                             |
| **Cloud**       | Google Cloud Run                                               |
| **Audio**       | PCM 16-bit, 16kHz capture / 24kHz playback                     |

## 🚀 Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Google AI Studio API key](https://aistudio.google.com/apikey)

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/legallease-live-agent.git
cd legallease-live-agent
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set your GOOGLE_API_KEY

# Start the server
bash start-minimal.sh
```

The backend will be running at `http://localhost:8000`.

### 3. Frontend Setup
Download The Frontend Repo at [Legal-GoogleADK-Frontend](https://github.com/Clarionxk/Legal-GoogleADK-Frontend)

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend will be running at `http://localhost:3000`.

### 4. Use the App

1. Open `http://localhost:3000` in Chrome
2. Click the **microphone button** 🎤
3. Allow microphone access when prompted
4. Start talking! Say something like _"I need a sales contract"_
5. The agent will ask you clarifying questions
6. Once confirmed, it generates the contract and displays it in the preview panel
7. Click **Download** to save as PDF

## 🧪 Reproducible Testing (For Judges)

Once both backend and frontend are running, follow these steps to verify the project works:

### Step 1: Verify Backend Health

```bash
curl http://localhost:8000/health
```

**Expected:** `{"status":"healthy","app":"LegalLease Live Agent","version":"2.0.0","environment":"development"}`

### Step 2: Test Contract Creation (Voice Agent)

1. Open [http://localhost:3000/create](http://localhost:3000/create)
2. Click the **microphone button** to start a voice session
3. **Allow microphone access** when prompted by your browser
4. Speak to the agent. Example prompt:
   > _"I need a sales agreement under California law. The seller is John Smith, the buyer is Sarah Johnson. It's for a 2020 Honda Civic, $15,000 paid in full on delivery, effective March 15th 2026."_
5. The agent will confirm details and ask for approval
6. Say **"Yes, that looks correct"** to confirm
7. **Expected:** A full contract appears in the right panel within 10-15 seconds
8. The contract auto-saves to Cloud Firestore

### Step 3: Test Contract Analysis (Vision)

1. Navigate to [http://localhost:3000/analyze](http://localhost:3000/analyze)
2. Upload any **PDF or image** of a contract (you can screenshot the contract from Step 2, or use any contract PDF)
3. Optionally type context like: _"I'm the buyer — what should I watch out for?"_
4. Click **"🔍 Analyze Contract"**
5. **Expected:** An 8-section structured analysis appears within 15-20 seconds, covering:
   - Contract overview
   - Key terms & definitions
   - Obligations of each party
   - Important clauses
   - Potential risks & red flags
   - Missing elements
   - Plain language summary
   - Recommendations

### Step 4: Test API Endpoints Directly (Optional)

```bash
# List all saved contracts
curl http://localhost:8000/api/contracts

# Upload a contract for analysis via CLI
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@/path/to/contract.pdf" \
  -F "context=I am the tenant"
```

### Live Deployment

The backend is also deployed on Google Cloud Run:

- **Health:** [https://legallease-backend-1020043848119.us-central1.run.app/health](https://legallease-backend-1020043848119.us-central1.run.app/health)
- **API Docs:** [https://legallease-backend-1020043848119.us-central1.run.app/docs](https://legallease-backend-1020043848119.us-central1.run.app/docs)

---

## ☁️ Deploy to Google Cloud Run

### Prerequisites

- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) installed
- A GCP project with billing enabled

### Deploy

```bash
cd backend

# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# Set your API key and deploy
export GOOGLE_API_KEY=your-key-here
bash deploy-cloudrun.sh
```

The deployment script will output your Cloud Run URL. Update the frontend's `NEXT_PUBLIC_BACKEND_URL` environment variable to point to it:

```bash
# In the frontend directory
echo "NEXT_PUBLIC_BACKEND_URL=wss://your-service-url.run.app" > .env.local
```

## 📂 Project Structure

```
legallease-live-agent/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Pydantic settings
│   │   ├── api/routes/
│   │   │   ├── live_agent.py    # WebSocket endpoint (ADK ↔ browser)
│   │   │   ├── auth.py          # Firebase auth routes
│   │   │   └── contracts.py     # Contract CRUD (Firestore)
│   │   ├── services/
│   │   │   ├── agent.py         # ADK Agent definition + instructions
│   │   │   └── contract_tools.py # Contract types & categories
│   │   └── utils/
│   │       └── security.py      # Firebase token verification
│   ├── Dockerfile               # Cloud Run container
│   ├── deploy-cloudrun.sh       # One-click deployment script
│   ├── requirements.txt
│   └── start-minimal.sh         # Local dev startup
├── frontend/
│   ├── app/
│   │   ├── hooks/
│   │   │   └── useLiveAgent.ts  # React hook (WebSocket + audio)
│   │   ├── components/
│   │   │   ├── LiveLegalPartner.tsx      # Main UI component
│   │   │   └── LiveLegalPartner.module.css
│   │   ├── globals.css          # Design system
│   │   ├── layout.tsx
│   │   └── page.tsx
│   └── public/
│       └── pcm-capture-processor.js  # AudioWorklet for mic capture
└── README.md
```


## 📜 Available Contract Types

**Business:** Sales Agreement, Service Agreement, NDA, Partnership, Joint Venture, Franchise, Distribution, Supply, License, Employment, Consulting, Non-Compete, Independent Contractor, Manufacturing

**Real Estate:** Lease, Purchase, Mortgage, Tenancy, Property Management, Commercial Lease

**Financial:** Loan Agreement, Investment Agreement, Promissory Note, Guaranty, Credit

**Employment:** Offer Letter, Employee Handbook, Severance, Termination

**IP:** Copyright Assignment, Patent License, Trademark License, Confidentiality

**Personal:** Prenuptial, Postnuptial, Separation, Settlement, Child Custody, Power of Attorney, Living Will

**Technology:** Software License, IT Services, Website Development

## ⚠️ Disclaimer

LegalLease generates **template contracts** for educational and informational purposes. All generated documents should be reviewed by a qualified attorney before signing. This tool does not constitute legal advice.

## 📄 License

MIT
