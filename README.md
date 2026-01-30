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