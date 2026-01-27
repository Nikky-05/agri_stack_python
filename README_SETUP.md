# AgriStack Chatbot Setup Instructions

This guide explains how to set up the AgriStack Chatbot project on a new machine.

## Prerequisites

1. **Python 3.8+**: Ensure Python is installed and added to your system PATH.
2. **PostgreSQL**: Ensure PostgreSQL is installed and running on port 5432 (default).
   - You should have a superuser role (default: `postgres`) capable of creating databases.
3. **Ollama (Optional)**: For using the LLM features locally.
   - Install Ollama and pull the model: `ollama pull gpt-oss-120b` (or update `.env` to point to a different model).

## Automatic Setup

We have provided a single setup script that handles dependency installation, environment configuration, and database initialization.

1. Open a terminal in the project root directory.
2. Run the setup script:
   ```bash
   python setup_project.py
   ```
3. Follow the interactive prompts:
   - Provide your PostgreSQL headers (User, Password, Host, Port).
   - Confirm the target database name (default: `exam_db`).
   - The script will create a `.env` file with your configuration.
   - The script will automatically install required Python packages from `requirements.txt`.
   - The script will initialize the database schema and import sample data.

## Manual Setup (If script fails)

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   - Create a `.env` file in the root directory.
   - Add the following variables:
     ```env
     DB_HOST=localhost
     DB_PORT=5432
     DB_USER=postgres
     DB_PASSWORD=your_password
     DB_NAME=exam_db
     DEFAULT_DB=postgres
     LLM_API_URL=http://localhost:11434/api/generate
     ```

3. **Initialize Database**:
   ```bash
   python setup_db.py
   ```

## Running the Application

To start the backend server:

```bash
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`.
Documentation is available at `http://localhost:8000/docs`.
