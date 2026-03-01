# SolarSense AI

**Rooftop solar planning, simplified.**

Upload a photo of your roof, place panels interactively, and get a full financial breakdown — cost, subsidy, savings, and payback period — in seconds.

Built for the **AMD Slingshot Hackathon 2026** | Sustainable AI & Green Tech

---

## How It Works

1. **Upload** — Drag-and-drop a rooftop photo (satellite or drone view).
2. **Analyze** — The backend runs depth estimation (Depth Anything V2) and sun-path shadow simulation to produce an irradiance heatmap.
3. **Place Panels** — An interactive editor lets you click to place, drag to reposition, rotate, or delete solar panels on your roof. The heatmap overlay guides placement toward the sunniest areas.
4. **Get Results** — A 25-year financial report is generated: installation cost, PM Surya Ghar subsidy, monthly generation, cumulative savings, payback period, and optional SBI loan EMI.

---

## Features

| Area | Details |
|---|---|
| Image Analysis | Depth Anything V2 for 3D roof structure; annual sun-path ray tracing with irradiance heatmap |
| Panel Placement | Interactive drag-and-drop editor with rotate/delete; PlacementNet U-Net CNN for neural-guided suggestions |
| Financial Engine | 25-year ROI projection, PM Surya Ghar central subsidy (up to 78,000 INR), SBI solar loan EMI calculator |
| AI Report | LLM-generated summary via Anthropic Claude (with template fallback) |
| Demo Mode | Built-in demo image for instant walkthrough without uploading |

---

## Quick Start

### Prerequisites

- Python 3.10 – 3.12
- Node.js 18+
- (Optional) AMD ROCm for GPU acceleration

### 1. Clone

```bash
git clone https://github.com/Siddesh-bype/SolarSense_AI.git
cd SolarSense_AI
cp .env.example .env        # Add ANTHROPIC_API_KEY if you have one
```

### 2. Backend

```bash
python -m venv venv
venv\Scripts\activate        # Windows — or: source venv/bin/activate
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

Open **http://localhost:5173**, upload a roof photo, and start placing panels.

---

## Project Structure

```
SolarSense_AI/
├── backend/
│   ├── main.py                  # FastAPI application
│   ├── routers/
│   │   ├── scan.py              # /api/scan/upload (Phase 1), /api/scan/calculate (Phase 2)
│   │   └── financial.py         # /api/financial/estimate
│   ├── services/
│   │   ├── depth_estimator.py   # Depth Anything V2
│   │   ├── shadow_simulator.py  # Sun-path ray tracing
│   │   ├── panel_optimizer.py   # Greedy panel layout
│   │   ├── placement_network.py # PlacementNet U-Net CNN
│   │   ├── financial_engine.py  # 25-year cost/savings calculator
│   │   ├── energy_calculator.py # Energy yield projection
│   │   └── report_generator.py  # LLM report + template fallback
│   ├── weights/
│   │   └── placement_net.pth    # Trained model weights
│   ├── utils/
│   │   ├── gpu_manager.py       # AMD ROCm / CPU detection
│   │   ├── image_preprocessor.py
│   │   └── pvgis_client.py      # Solar irradiance data (PVGIS API + offline)
│   └── data/                    # Static JSON (costs, subsidies, panel specs)
├── frontend/
│   └── src/
│       ├── App.tsx              # Shell, navigation, modals
│       ├── components/
│       │   ├── RoofUploader.tsx  # Photo upload + city/bill form
│       │   ├── ScanProgress.tsx  # Analysis progress indicator
│       │   ├── PanelEditor.tsx   # Interactive panel placement editor
│       │   ├── FinancialDashboard.tsx  # Charts, cost breakdown, EMI
│       │   └── ReportCard.tsx    # AI-generated summary
│       ├── hooks/
│       │   └── useScan.ts       # 2-phase upload/calculate flow
│       └── types.ts             # Shared TypeScript types
├── benchmark.py
├── docker-compose.yml
└── README.md
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | No | — | Enables AI-generated report summaries |
| `PVGIS_OFFLINE_MODE` | No | `true` | Use bundled irradiance data instead of PVGIS API |
| `BACKEND_PORT` | No | `8001` | Backend listen port |

---

## API Overview

| Endpoint | Method | Description |
|---|---|---|
| `/api/scan/upload` | POST | Upload roof image + city/bill. Returns heatmap, depth map, panel spec, roof area. |
| `/api/scan/calculate` | POST | Submit panel positions. Returns full financial report + AI summary. |
| `/api/financial/estimate` | GET | Standalone financial estimate by system size and city. |
| `/` | GET | Health check. |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, Recharts, Lucide Icons |
| Backend | Python, FastAPI, Uvicorn |
| ML Models | Depth Anything V2 (HuggingFace), PlacementNet U-Net CNN (custom) |
| Compute | AMD ROCm (HIP) or CPU (auto-detected) |
| Data | PVGIS solar irradiance, PM Surya Ghar subsidy rates |

---

## Team

**SolarSense AI** — AMD Slingshot Hackathon 2026

- Omee
- Siddesh Bype

[github.com/Siddesh-bype/SolarSense_AI](https://github.com/Siddesh-bype/SolarSense_AI)
