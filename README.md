# 🌞 SolarSense AI

> **Point. Scan. Power Your Home.**

AI-powered rooftop solar planning tool for Indian homeowners. Upload a photo of your rooftop and get an instant solar panel layout, energy yield prediction, and financial savings report.

Built for **AMD Slingshot Hackathon 2026** | Domain: Sustainable AI & Green Tech

---

## ✨ Features

| Feature | Description |
|---|---|
| 📸 Smart Upload | Drag-drop rooftop photo with auto-validation (blur, brightness, resolution) |
| 🧠 Depth Estimation | Depth Anything V2 model for 3D roof structure analysis |
| ☀️ Shadow Simulation | Annual sun-path ray tracing with irradiance heatmap |
| 📐 Panel Placement | Greedy optimizer for maximum energy yield with maintenance gaps |
| 💰 Financial Engine | 25-year ROI, PM Surya Ghar subsidy, EMI calculator |
| 📝 AI Report | LLM-generated personalized summary (Anthropic Claude + fallback) |
| 🎯 Demo Mode | Pre-computed results for reliable live demos |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) AMD ROCm / NVIDIA CUDA for GPU acceleration

### 1. Clone & Setup
```bash
git clone <repo-url>
cd Solarsense
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY (optional)
```

### 2. Backend
```bash
cd backend
pip install -r requirements.txt
python validate_env.py          # Check everything is ready
uvicorn main:app --port 8000    # Start API server
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev                     # Start dev server at localhost:5173
```

### 4. Open Browser
Navigate to **http://localhost:5173** and upload a rooftop photo!

---

## 🐳 Docker (Alternative)
```bash
docker-compose up --build
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000/docs
```

---

## 🏗️ Architecture

```
Solarsense/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── routers/
│   │   ├── scan.py             # POST /api/scan/upload, GET /api/scan/{id}/...
│   │   └── financial.py        # GET /api/financial/estimate
│   ├── services/
│   │   ├── depth_estimator.py  # Depth Anything V2
│   │   ├── shadow_simulator.py # Sun-path ray tracing
│   │   ├── panel_optimizer.py  # Greedy panel placement
│   │   ├── financial_engine.py # 25-year ROI calculator
│   │   ├── energy_calculator.py# Energy yield calculator
│   │   └── report_generator.py # LLM summary + fallback
│   ├── utils/
│   │   ├── gpu_manager.py      # AMD ROCm / CUDA / CPU
│   │   ├── image_preprocessor.py
│   │   └── pvgis_client.py     # Solar irradiance data
│   └── data/                   # Static JSON (costs, subsidies, specs)
├── frontend/
│   └── src/
│       ├── App.tsx             # Main app shell
│       ├── components/         # RoofUploader, HeatmapOverlay, etc.
│       └── hooks/              # useScan, useFinancial
├── benchmark.py                # Pipeline benchmark
├── docker-compose.yml
└── README.md
```

---

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | No | — | Enables AI-generated report summaries |
| `PVGIS_OFFLINE_MODE` | No | `true` | Use offline irradiance data |
| `BACKEND_HOST` | No | `0.0.0.0` | Backend bind address |
| `BACKEND_PORT` | No | `8000` | Backend port |

---

## 🧪 Testing

```bash
cd backend

# Environment validation
python validate_env.py

# Unit tests
python -m pytest tests/ -v

# Pipeline benchmark
cd ..
python benchmark.py
```

---

## 🎯 Demo Mode

Append `?demo=true` to the frontend URL or use the **"Load Demo Image"** button for instant results with pre-computed analysis.

---

## 🏆 AMD Slingshot Hackathon 2026

**Team:** SolarSense AI  
**Track:** Sustainable AI & Green Tech  
**Hardware:** AMD ROCm (auto-fallback to CUDA/CPU)

---

*Built with ❤️ for a sustainable future*
