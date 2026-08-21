# Quickstart & Local Setup Guide

## Prerequisites
- Operating System: Windows / Linux / macOS
- Python: 3.10+ (Python 3.14 compatible)
- PowerShell or Terminal

## Setup Steps

### 1. Clone Repository & Set Location
```bash
git clone https://github.com/your-org/armor-iq-scholarship-agent.git
cd D:\armor-iq-scholarship-agent
```

### 2. Create Virtual Environment & Set Temp Directory
```powershell
# Set temporary directory to Drive D to avoid drive space limitations
$env:TEMP='D:\tmp'; $env:TMP='D:\tmp'

python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Setup Environment Variables
```powershell
Copy-Item .env.example .env
```

### 5. Run Mock Portal API
```powershell
$env:PYTHONPATH='D:\armor-iq-scholarship-agent'
.venv\Scripts\python.exe -m uvicorn mock_portal.main:app --host 127.0.0.1 --port 8001
```

### 6. Run Agent Backend API
```powershell
$env:PYTHONPATH='D:\armor-iq-scholarship-agent'
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 7. Run Test Suite
```powershell
$env:PYTHONPATH='D:\armor-iq-scholarship-agent'
.venv\Scripts\pytest.exe -v
```
