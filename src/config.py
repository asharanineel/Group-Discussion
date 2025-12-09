
# config.py
import os
from dotenv import load_dotenv
import sys # For critical error output

# Determine the path to the project root's .env file
# Assuming config.py is in 'src/' and .env is in the parent directory
project_root = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(project_root, '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- API Keys ---
# Values from your .env. If empty in .env, these will be None/""
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CLOUD_API_KEY = os.getenv("GOOGLE_CLOUD_API_KEY")
QWEN_API_KEY = os.getenv("QWEN_API_KEY")

# --- MongoDB Configuration ---
# Value from your .env.
MONGO_URI = os.getenv("MONGO_URI")
# These are NOT in your .env snippet, so provide sensible defaults
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "Group_discussion_report_db")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "group_discussions")

# --- MySQL Configuration ---
# Values from your .env snippet.
MYSQL_HOST = os.getenv("MYSQL_HOST")
# Convert port to int, provide default if not in .env
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
# This is NOT in your .env snippet, so provide a sensible default
MYSQL_USER_DB_NAME = os.getenv("MYSQL_USER_DB_NAME", "Interviewer_database")

# --- Mail Configuration ---
# Values from your .env snippet, using exact names provided
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
SMTP_SERVER = os.getenv("MAIL_SERVER") # Using MAIL_SERVER from your .env
# Convert port to int, provide default if not in .env
SMTP_PORT = int(os.getenv("MAIL_PORT", 587)) # Using MAIL_PORT from your .env

# --- Group Discussion Settings (NOT in your .env, provide defaults) ---
GD_TIME_LIMIT_SECONDS = int(os.getenv("GD_TIME_LIMIT_SECONDS", 500)) # Default to 4 minutes

# --- LLM Evaluation Configuration (NOT in your .env, provide defaults) ---
LLM_EVALUATION_MAX_TOKENS = int(os.getenv("LLM_EVALUATION_MAX_TOKENS", 800))
LLM_TOKENS_PER_RESPONSE_EVALUATION = int(os.getenv("LLM_TOKENS_PER_RESPONSE_EVALUATION", 150))

# --- Google Cloud Text-to-Speech (GCS TTS) Configuration (NOT in your .env, provide defaults) ---
GCS_TTS_DEFAULT_VOICE = os.getenv("GCS_TTS_DEFAULT_VOICE", "en-IN-Chirp3-HD-Puck")
GCS_TTS_FALLBACK_VOICE = os.getenv("GCS_TTS_FALLBACK_VOICE", "en-IN-Standard-B")
GCS_TTS_LANGUAGE_CODE = os.getenv("GCS_TTS_LANGUAGE_CODE", "en-IN")
GCS_TTS_AUDIO_ENCODING = os.getenv("GCS_TTS_AUDIO_ENCODING", "MP3")
GCS_TTS_PITCH = float(os.getenv("GCS_TTS_PITCH", -0.5))
GCS_TTS_SPEAKING_RATE = float(os.getenv("GCS_TTS_SPEAKING_RATE", 0.95))
GCS_TTS_MIMETYPE = os.getenv("GCS_TTS_MIMETYPE", "audio/mpeg")

# Optional: Basic check for critical missing environment variables at load time
# The main.py will also handle errors if these are None or empty
# (using sys for direct stderr output)
_critical_vars = {
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "GOOGLE_CLOUD_API_KEY": GOOGLE_CLOUD_API_KEY,
    "QWEN_API_KEY": QWEN_API_KEY,
    "MONGO_URI": MONGO_URI,
    "MYSQL_HOST": MYSQL_HOST,
    "MYSQL_USER": MYSQL_USER,
    "MYSQL_PASSWORD": MYSQL_PASSWORD,
    "MAIL_USERNAME": MAIL_USERNAME,
    "MAIL_PASSWORD": MAIL_PASSWORD,
    "MAIL_SERVER": SMTP_SERVER, # Renamed to SMTP_SERVER for consistency, but loads from MAIL_SERVER
}

for var_name, value in _critical_vars.items():
    if value is None or (isinstance(value, str) and value.strip() == ""):
        print(f"WARNING: Critical environment variable '{var_name}' is missing or empty. "
              "Application may not function correctly. Please check your .env file.", file=sys.stderr)

