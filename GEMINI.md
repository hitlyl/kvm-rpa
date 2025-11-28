# GEMINI.md - AI Context & Instructions

## Project: KVM RPA System

This file provides context and instructions for AI agents interacting with this codebase.

### 1. Project Overview
The **KVM RPA (Robotic Process Automation) System** is a full-stack application designed to automate tasks on a remote machine via KVM (Keyboard, Video, Mouse) interface. It captures video from an RTSP stream, analyzes it using Computer Vision (YOLOv8 for object detection, PaddleOCR for text recognition), and sends keyboard/mouse commands to control the target machine based on defined logic flows.

**Key Technologies:**
*   **Backend:** Python 3.9+, FastAPI (API & WebSocket), OpenCV (Video), Ultralytics YOLOv8, PaddleOCR.
*   **Frontend:** Vue 3, Vite, TypeScript, Element Plus, Pinia, LogicFlow.
*   **Hardware Target:** Sophon TPU (optional/production), Standard CPU/GPU (development).
*   **Protocol:** RTSP (Video), HTTP/WebSocket (Control & Feedback).

### 2. Project Structure

```text
/
├── backend/                # Python Backend Service
│   ├── src/                # Source code
│   │   ├── api/            # FastAPI routes & WebSocket
│   │   ├── capture/        # RTSP Video capture
│   │   ├── detection/      # YOLOv8 inference
│   │   ├── ocr/            # PaddleOCR inference
│   │   ├── engine/         # Rule & Flow execution engine
│   │   ├── kvm_api/        # KVM control adapter (Mouse/Keyboard)
│   │   └── models/         # Pydantic models
│   ├── config/             # Configuration files (default.yaml)
│   ├── flows/              # JSON/YAML flow definitions
│   ├── models/             # ML Model weights (YOLO *.pt)
│   └── main.py             # Entry point
├── frontend/               # Vue 3 Frontend Application
│   ├── src/                # Vue source
│   └── package.json        # Dependencies
├── deploy/                 # Deployment scripts (Docker, Shell)
├── docs/                   # Documentation (ARCHITECTURE.md)
└── .cursor/rules/          # AI behavior rules (RIPER workflow)
```

### 3. Setup & Execution Commands

**Backend:**
*   **Directory:** `backend/`
*   **Install:** `pip install -r requirements.txt`
*   **Run:** `python main.py`
*   **Config:** `backend/config/default.yaml` (Supports hot-reloading)
*   **Mock Mode:** Can run without actual KVM hardware by using mock adapters (see `src/kvm_api/keystroke_adapter.py`).

**Frontend:**
*   **Directory:** `frontend/`
*   **Install:** `npm install`
*   **Run (Dev):** `npm run dev` (Default port: 5000)
*   **Build:** `npm run build`

**Deployment:**
*   **Script:** `./deploy.sh` (Root directory)

### 4. Key Architectural Patterns

*   **Event Loop:** The backend runs a main loop capturing video frames -> processing (YOLO/OCR) -> evaluating rules -> executing actions.
*   **Flow Engine:** Logic is defined in JSON/YAML "Flows" which describe a state machine or sequence of actions based on visual triggers.
*   **WebSockets:** Used heavily for streaming the processed video feed (`/ws/frame`) and inference results (`/ws/inference`) to the frontend in real-time.
*   **Modularity:** Detection, OCR, and Execution are decoupled. The system can run inference without executing actions (Observation mode).

### 5. AI Development Guidelines

*   **Conventions:** Follow existing Python (PEP 8) and TypeScript styles.
*   **RIPER Workflow:** This project adopts the RIPER (Research, Innovate, Plan, Execute, Review) workflow for complex tasks. See `.cursor/rules/riper-workflow.mdc` for details. When performing complex refactoring or feature additions, consider adopting this structured approach.
*   **Configuration:** Always check `backend/config/default.yaml` before hardcoding values. Use the configuration system.
*   **Mocking:** When writing tests or running locally without hardware, ensure the system gracefully falls back to mock implementations for RTSP and KVM control.
