# AgriStack MIS Analytics - Professional Modular Platform

A high-performance, conversational analytics dashboard for the AgriStack ecosystem. This platform allows government officials to query agricultural data using natural language, visualizing results through interactive charts and premium KPI indicators.

## 🏗️ Modular Architecture

The project is structured following professional software engineering principles:

- **`app.py`**: The central FastAPI orchestrator. Handles routing and coordinates between logic handlers.
- **`config.py`**: Centralized configuration management (DB credentials, LGD mappings, system constants).
- **`nlp_handler.py`**: The intelligence layer. Responsible for **Intent Classification** (understanding what the user wants) and **Natural Language Generation** (narrating data results).
- **`db_handler.py`**: The SQL engine. Manages all interactions with the PostgreSQL database.
- **`csv_handler.py`**: The fallback/flat-file engine. Allows the system to run directly from local CSV files using Pandas for maximum flexibility.
- **`setup_db.py`**: Data migration utility. Imports raw CSV data into the structured PostgreSQL schema.

## 🚀 Deployment & Setup

### 1. Environment Configuration
Update the `.env` file or modify `config.py` with your database credentials and environment-specific settings.

### 2. Database Migration
To import the raw agricultural data into your PostgreSQL instance:
```bash
python setup_db.py
```

### 3. Running the Platform
Launch the backend server:
```bash
python app.py
```
The API will be available at `http://localhost:8001`.

### 4. Frontend Access
Open `frontend/index.html` in any modern browser to access the interactive dashboard.

## 📊 Feature Highlights
- **Smart Data Toggle**: Switch between Database and CSV mode instantly in `app.py`.
- **LGD-Based Authorization**: Built-in security to ensure users only access data within their permitted LGD scope.
- **Interactive Visuals**: Real-time generation of Bar, Pie, and Line charts using Chart.js.
- **Premium UX**: Responsive layout with glassmorphism and state-of-the-art animations.




✻ Conversation compacted (ctrl+o for history)

  ⎿  Read requirements.txt (24 lines)
  ⎿  Read nlp_handler.py (435 lines)
  ⎿  Read config.py (282 lines)
  ⎿  Referenced file frontend\style.css
  ⎿  Referenced file frontend\script.js

● Looking at your code, the Ollama integration is correctly set up. Let me verify the key components:

  Ollama Integration in nlp_handler.py:                                                                                        - ✅ Connects to http://localhost:11434/api/generate
  - ✅ Default model: llama3:latest                                                                                          
  - ✅ Model verification via /api/tags endpoint
  - ✅ Timeout handling (15-20 seconds)
  - ✅ Fallback to template narration if LLM fails

  Dependencies Check:
  The requests library is included in requirements.txt for HTTP calls to Ollama.

  To ensure Ollama works properly, you need:

  1. Ollama installed and running - Start it with:
  ollama serve
  2. llama3 model downloaded - If not already:
  ollama pull llama3
  3. Verify it's running:
  curl http://localhost:11434/api/tags

  Your code handles Ollama gracefully:
  - If Ollama is not running → Falls back to template-based responses
  - If model doesn't exist → Tries llama3:latest as fallback
  - If LLM response is too short/long → Uses template narration

  Summary of your complete stack:
  ┌───────────────────────────┬───────────────────────────────────┐
  │         Component         │              Status               │
  ├───────────────────────────┼───────────────────────────────────┤
  │ FastAPI backend           │ ✅ Ready                          │
  ├───────────────────────────┼───────────────────────────────────┤
  │ NLP intent classification │ ✅ Fixed (cultivated vs surveyed) │
  ├───────────────────────────┼───────────────────────────────────┤
  │ CSV data processing       │ ✅ Working                        │
  ├───────────────────────────┼───────────────────────────────────┤
  │ PostgreSQL query format   │ ✅ Correct with is_view=true      │
  ├───────────────────────────┼───────────────────────────────────┤
  │ Ollama LLM narration      │ ✅ Configured (optional)          │
  ├───────────────────────────┼───────────────────────────────────┤
  │ Frontend UI               │ ✅ Cinematic 3D design            │
  ├───────────────────────────┼───────────────────────────────────┤
  │ requirements.txt          │ ✅ Updated                        │
  └───────────────────────────┴───────────────────────────────────┘
  Your application will work even without Ollama running - it will just use the template-based responses instead of
  LLM-generated narrations. Everything is good to go.