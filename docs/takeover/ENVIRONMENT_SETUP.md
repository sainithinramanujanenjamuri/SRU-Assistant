# Environment Setup Guide: SRU Assistant

## 1. Prerequisites
- **Python:** Python 3.10+ or Python 3.11+ (verified on Python 3.11.9)
- **Operating Systems:** Windows 10/11, macOS (Apple Silicon / Intel), Linux (Ubuntu 20.04+)
- **Architecture:** x86_64 or ARM64 (Apple M-series)
- **Hardware Requirements:** CPU-only operation supported out-of-the-box using lightweight FastHash embeddings (384-dimensional) and deterministic or local models. No dedicated GPU required for core functionality.
- **Optional Local LLM:** [Ollama](https://ollama.ai) (optional, for neural generation with models like `qwen2.5:0.5b` or `qwen3.5:0.8b`).

---

## 2. Step-by-Step Installation

### Step 2.1: Clone & Navigate to Repository
```bash
git clone <repository-url> SRU_Assistant_Capstone_Project
cd SRU_Assistant_Capstone_Project
```

### Step 2.2: Create and Activate Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS / Linux (bash/zsh):**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2.3: Upgrade Package Installer
```bash
python -m pip install --upgrade pip
```

### Step 2.4: Install Required Dependencies
Install the foundation and application dependencies from `requirements.txt`:
```bash
pip install -r requirements.txt
```
*Note: Key packages include `pydantic>=2.0.0`, `pydantic-settings>=2.0.0`, `fastapi>=0.110.0`, `uvicorn>=0.28.0`, `python-multipart>=0.0.9`, `pypdf>=4.0.0`, `python-docx>=1.1.0`, and `numpy>=1.24.0`.*

### Step 2.5: Configure Environment (.env)
Copy the provided `.env.example` to `.env`:
```powershell
# Windows
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```
Default parameters in `.env` default to deterministic CPU-friendly modes:
```ini
APP_ENV=development
APP_NAME="SRU Assistant"
DEBUG=true
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

LLM_PROVIDER=deterministic
LLM_MODEL=qwen3.5:0.8b
EMBEDDING_PROVIDER=fasthash
EMBEDDING_MODEL=fasthash-384
EMBEDDING_DIMENSION=384
VECTORSTORE_BACKEND=sqlite
```

---

## 3. Verifying the Installation

### Step 3.1: Run the Automated Verification Suite
```bash
pytest -v
```
All deterministic unit, integration, security, and API tests should pass cleanly.

### Step 3.2: Inspect Configuration Loading
```bash
python -c "from app.config.settings import get_settings; s = get_settings(); print(f'Ready: {s.app_name} (Mode: {s.llm_provider})')"
```

---

## 4. Running the Application

### Option A: Direct Python Execution
```bash
python app/main.py
```

### Option B: Uvicorn Server Command
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will be available at:
- **Interactive Student/Faculty Portal:** [http://localhost:8000](http://localhost:8000)
- **Capstone Viva Slides:** [http://localhost:8000/presentation](http://localhost:8000/presentation)
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Status:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 5. (Optional) Configuring Local Ollama Neural LLM
If you wish to run neural generation instead of the deterministic rule baseline:
1. Install Ollama from [https://ollama.ai](https://ollama.ai).
2. Start the Ollama background daemon:
   ```bash
   ollama serve
   ```
3. Pull the target model:
   ```bash
   ollama pull qwen2.5:0.5b
   ```
4. In `.env`, change:
   ```ini
   LLM_PROVIDER=ollama
   LLM_MODEL=qwen2.5:0.5b
   ```
5. Restart the server.

