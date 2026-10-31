# OmniStore AI — Agentic Local Intelligence & Micro-Commerce Engine

**Hackathon:** Meta Global AI Developer Hackathon (Oct 26 – Nov 4, 2026)  
**Track:** Build for Your World  
**Team / Creator:** Joseph John Bassey  
**Architecture:** Decoupled Next.js 14+ (App Router) + Python FastAPI Engine  
**Core Pipeline:** Meta SAM 3.1 (Eyes) → Muse Spark 1.3 (Brain) → Muse Code (Hands)

---

## 🌍 The "Build for Your World" Mission

In emerging markets across Sub-Saharan Africa, Latin America, and Southeast Asia, hundreds of millions of micro-entrepreneurs, kiosk vendors, and local market stall operators power the real economy. 

However, they are almost entirely excluded from digital commerce:
1. **High Friction of Traditional E-Commerce:** Platforms like Shopify, WooCommerce, or Amazon require manual SKU entry, detailed text descriptions, barcode scanners, and desktop workflows that small traders cannot maintain.
2. **Language and Valuation Barriers:** Local prices are dynamic, subject to market bargaining, seasonal availability, and localized unit conventions (e.g., tuber bundles, paint-bucket measures of grains).
3. **The WhatsApp Reality:** In emerging economies, business already happens over WhatsApp, mobile money, and local calls — not complex checkout funnels or cart pages.

**OmniStore AI** transforms any physical kiosk, market stall, or grocery shelf into a complete digital storefront in seconds. By snapping a single photo or streaming video of physical inventory, our autonomous multi-model pipeline isolates products, reasons over local market value, and compiles a mobile-first web storefront featuring WhatsApp 1-click checkout and SQLite inventory tracking.

---

## ⚡ The 3-Model Autonomous Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PHYSICAL / USER INPUT                         │
│               (Video streams, shelf photos, physical goods)             │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      1. SAM 3.1 (VISUAL PERCEPTION)                     │
│                             "THE EYES"                                  │
│  • Precise object segmentation & spatial masking                        │
│  • Zero-shot video tracking & item extraction                           │
│  • Bounding box coordinate & visual feature output                      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Segmented Crops + Spatial Masks
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     2. MUSE SPARK (COGNITIVE REASONING)                 │
│                             "THE BRAIN"                                 │
│  • Cross-modal domain logic & anomaly evaluation                        │
│  • Context grounding & structured decision graphs                       │
│  • Local market pricing (NGN, KES, GHS, USD) & stock counts             │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Structured StorefrontSchema (JSON)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       3. MUSE CODE (AGENTIC SYNTHESIS)                  │
│                             "THE HANDS"                                 │
│  • Programmatic low-latency web app generation                          │
│  • Mobile-first Next.js 14 + Tailwind storefront synthesis              │
│  • WhatsApp 1-click checkout API & Prisma/SQLite data schema            │
└─────────────────────────────────────────────────────────────────────────┘
```

1. **SAM 3.1 (The Eyes):** 
   - Zero-shot spatial segmentation of physical goods on crowded shelves or market stalls.
   - Outputs normalized `[ymin, xmin, ymax, xmax]` bounding boxes, polygonal masks, and isolated visual crops.
2. **Muse Spark 1.3 (The Brain):**
   - Multimodal cognitive reasoning grounded in local commerce context.
   - Evaluates items (e.g., local yams, fresh produce baskets, sealed garri tubs, palm oil bottles), identifies quantities, infers competitive market pricing in the merchant's local currency (`NGN`, `KES`, `GHS`, etc.), and produces a typed `StorefrontSchema`.
3. **Muse Code (The Hands):**
   - Agentic software synthesis engine.
   - Programmatically writes mobile-first Next.js 14 App Router code (`app/page.tsx`), a WhatsApp checkout route handler (`app/api/checkout/route.ts`), and a database schema (`prisma/schema.prisma`).

---

## 🏛️ System Architecture

OmniStore AI is built with a decoupled monorepo architecture designed for low-latency edge deployment and resilient offline execution:

- **Frontend (`frontend/`):**
  - **Framework:** Next.js 14 App Router, React 18, TypeScript, Tailwind CSS.
  - **Pipeline Studio:** Interactive HTML5 canvas with real-time SAM 3.1 bounding box overlays, confidence badges, and crop inspectors.
  - **Reasoning Panel:** Cognitive breakdown of classified goods, stock valuation in local currency, and recommended merchant actions.
  - **Live Mobile Simulator:** Phone frame simulator previewing the synthesized storefront with live cart calculation and WhatsApp 1-click checkout.
  - **Code Inspector:** Live syntax view of the generated `app/page.tsx`, `checkout/route.ts`, and `schema.prisma`.
  - **AI Voice & Chat Advisor:** Real-time Server-Sent Events (SSE) streaming assistant drawer powered by Muse Spark.
- **Backend (`backend/`):**
  - **Framework:** Python FastAPI engine with Uvicorn ASGI server.
  - **Validation:** Pydantic v2 schemas (`MerchantContext`, `InventoryItem`, `StorefrontSchema`, `CodeGenerateResponse`, `PipelineResponse`).
  - **Meta Model Service:** Async HTTPX client with connection pooling, exponential backoff retries, and high-fidelity fallback generators for sandboxed/offline environments.
  - **Background Task Queue:** Asynchronous worker queue with webhook callbacks for batch shelf processing.
  - **Cross-Agent Memory:** SQLite + FTS5 full-text search indexing past store audits and inventory history.

---

## 🚀 API Specification (`/api/v1`)

### 1. End-to-End Storefront Scan (`POST /api/v1/scan` or `POST /api/v1/scan/json`)
Executes the unified 3-model pipeline in a single call (upload a photo or submit base64 data):

**Request Payload:**
```json
{
  "image_base64": "data:image/jpeg;base64,...",
  "store_name": "Mama Cass Market",
  "currency": "NGN",
  "location": "Akure Central Market, Ondo State, Nigeria",
  "whatsapp_number": "+2348012345678"
}
```

**Response Payload:**
```json
{
  "status": "completed",
  "store_schema": {
    "store_title": "Mama Cass Market - Digital Storefront",
    "currency": "NGN",
    "location": "Akure Central Market, Ondo State, Nigeria",
    "whatsapp_number": "+2348012345678",
    "category": "Local Market & Provisions",
    "inventory": [
      {
        "item_id": "item_001",
        "name": "Local Yams (Large)",
        "category": "Tubers & Roots",
        "suggested_price": 2500.0,
        "estimated_quantity": 4,
        "description": "Freshly harvested organic tubers, dense and starch-rich.",
        "image_segment_id": "seg_001"
      },
      {
        "item_id": "item_002",
        "name": "Fresh Produce Basket (Tomatoes & Peppers)",
        "category": "Vegetables & Produce",
        "suggested_price": 1800.0,
        "estimated_quantity": 6,
        "description": "Farm-fresh red bell tomatoes and hot scotch bonnet peppers.",
        "image_segment_id": "seg_002"
      }
    ]
  },
  "bounding_boxes": [
    {
      "box_id": "seg_001",
      "label": "Local Yams (Tubers)",
      "confidence": 0.94,
      "bbox": [0.15, 0.05, 0.48, 0.32],
      "area": 78000
    }
  ],
  "code_synthesis": {
    "status": "compiled",
    "model_used": "muse-code",
    "repository_files": {
      "app/page.tsx": "...",
      "app/api/checkout/route.ts": "...",
      "prisma/schema.prisma": "..."
    },
    "preview_url": "https://omnistore-demo.vercel.app/mama-cass-market",
    "deployment_ready": true,
    "files_generated": 4
  },
  "processing_time_ms": 320.5
}
```

---

### 2. SAM 3.1 Visual Segmentation (`POST /api/v1/segment`)
Extracts bounding boxes and visual crops from raw stall imagery:
```bash
curl -X POST http://localhost:8000/api/v1/segment \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "data:image/png;base64,...",
    "prompt": "Locate market stall products and produce",
    "confidence_threshold": 0.25,
    "generate_crops": true
  }'
```

---

### 3. Muse Spark Multimodal Reasoning (`POST /api/v1/reason`)
Takes visual crops and merchant context to infer localized catalog pricing:
```bash
curl -X POST http://localhost:8000/api/v1/reason \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_context": {
      "store_name": "Mama Cass Market",
      "currency": "NGN",
      "location": "Akure, Nigeria",
      "whatsapp_number": "+2348012345678"
    },
    "model": "muse-spark-1.3",
    "structured_format": true
  }'
```

---

### 4. Muse Code Storefront Synthesis (`POST /api/v1/code/generate`)
Generates production-ready Next.js 14 and Tailwind storefront code with 1-click WhatsApp order integration:
```bash
curl -X POST http://localhost:8000/api/v1/code/generate \
  -H "Content-Type: application/json" \
  -d '{
    "target_framework": "nextjs14_tailwind",
    "store_schema": { ... }
  }'
```

---

### 5. Real-Time Streaming Agent Chat (`POST /api/v1/agent/chat`)
Streams token responses via Server-Sent Events (`text/event-stream`), compatible with browser native Web Streams:
```bash
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "How do I optimize my shelf layout?"}],
    "agent_role": "commander",
    "stream": true
  }'
```

---

## 🛠️ Local Setup & Quick Start

### Option 1: Docker Compose (One-Click Launch)

Start both the FastAPI backend and Next.js frontend in isolated production containers:

```bash
# 1. Clone repository
git clone https://github.com/Josephjbassey/jenna-hackathon.git
cd jenna-hackathon

# 2. Configure environment
cp .env.example .env

# 3. Launch via Docker Compose
sudo docker-compose up --build
```

- **Frontend Studio & Mobile Simulator:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

### Option 2: Local Development

#### 1. Backend Service
```bash
# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start FastAPI backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Application
```bash
cd frontend

# Install Node dependencies
npm install

# Run production build and start
npm run build
npm run start
```

#### 3. Run Backend Verification Tests
Verify the entire multi-model pipeline and API endpoints with zero syntax or import errors:
```bash
python3 backend/tests/test_api.py
```

---

## ⚙️ Environment Variables Reference

| Variable | Description | Default / Example |
|----------|-------------|-------------------|
| `META_MODEL_API_KEY` | Meta Model API Bearer token | `sk-meta-...` (Optional; built-in market simulation enabled) |
| `META_MODEL_API_BASE` | Base URL for Meta Model API | `https://api.meta.ai/v1` |
| `HOST` | Backend host binding | `0.0.0.0` |
| `PORT` | Backend port | `8000` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000,http://127.0.0.1:3000` |
| `DATABASE_URL` | Cross-agent memory SQLite path | `sqlite:///./memory/cross_agent.db` |
| `NEXT_PUBLIC_API_URL` | Frontend API connection string | `http://localhost:8000/api/v1` |

---

## 📄 License & Attribution

MIT License © 2026 Joseph John Bassey.  
Developed for the **Meta Global AI Developer Hackathon 2026** — *Build for Your World*.
