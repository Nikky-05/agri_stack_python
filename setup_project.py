
import os
import sys
import subprocess
import getpass

def install_dependencies():
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def setup_env_file():
    print("\nSetting up environment variables...")
    
    # Defaults
    default_db_host = "localhost"
    default_db_port = "5432"
    default_db_user = "postgres"
    default_db_pass = "postgres"
    default_db_name = "exam_db"

    # Prompt user
    db_host = input(f"Database Host [{default_db_host}]: ") or default_db_host
    db_port = input(f"Database Port [{default_db_port}]: ") or default_db_port
    db_user = input(f"Database User [{default_db_user}]: ") or default_db_user
    db_pass = getpass.getpass(f"Database Password [{default_db_pass}]: ") or default_db_pass
    db_name = input(f"Target Database Name [{default_db_name}]: ") or default_db_name
    
    # LLM Config (Ollama)
    default_llm_url = "http://localhost:11434/api/generate"
    llm_url = input(f"LLM API URL [{default_llm_url}]: ") or default_llm_url
    
    env_content = f"""
DB_HOST={db_host}
DB_PORT={db_port}
DB_USER={db_user}
DB_PASSWORD={db_pass}
DB_NAME={db_name}
DEFAULT_DB=postgres
LLM_API_URL={llm_url}
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print(".env file created.")

def run_db_setup():
    print("\nRunning database setup...")
    try:
        subprocess.check_call([sys.executable, "setup_db.py"])
        print("Database setup completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Database setup failed. Please check your credentials and ensure PostgreSQL is running. Error: {e}")
        sys.exit(1)

def main():
    print("=== AgriStack MIS Project Setup ===\n")
    
    # 1. Install Dependencies
    try:
        install_dependencies()
    except Exception as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)
        
    # 2. Setup .env
    if not os.path.exists(".env"):
        setup_env_file()
    else:
        print(".env file already exists. Skipping creation.")
        val = input("Do you want to overwrite it? (y/n): ")
        if val.lower() == 'y':
            setup_env_file()

    # 3. Run DB Setup
    run_db_setup()

    print("\n=== Setup Complete! ===")
    print("To run the application, use the following command:")
    print(f"    {sys.executable} -m uvicorn app:app --reload")

if __name__ == "__main__":
    main()
