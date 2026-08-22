# Quickstart & Local Setup Guide

## Prerequisites
- Operating System: Windows / Linux / macOS
- Python: 3.10+ (Python 3.14 compatible)
- PowerShell or Terminal

## Setup Steps

### 1. Clone Repository & Set Location
```bash
git clone https://github.com/your-org/armor-iq-scholarship-agent.git
cd armor-iq-scholarship-agent
```

### 2. Create Virtual Environment
```powershell
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\activate
```
```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
```powershell
# Windows
Copy-Item .env.example .env
```
```bash
# Linux / macOS
cp .env.example .env
```

The mock portal's SQLite database and any uploaded documents are stored
relative to the repo by default (`mock_portal/scholarship_portal.db` and
`mock_portal/uploads/`). To use a different location, set `SCHOLARSHIP_DB_PATH`
and/or `SCHOLARSHIP_UPLOAD_DIR` in your `.env` file — do not hardcode an
absolute drive path, since it won't work across operating systems.

### 5. Run Mock Portal API
```bash
# Run from the repo root so Python can resolve the app/ and mock_portal/ packages
python -m uvicorn mock_portal.main:app --host 127.0.0.1 --port 8001
```

### 6. Run Agent Backend API
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 7. Run Test Suite
```bash
pytest -v
```
