import os
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

REDIS_URL = os.getenv('REDIS_URL')
SENTRY_DSN = os.getenv('SENTRY_DSN')
API_HASH = os.getenv('API_HASH')
API_ID = os.getenv('API_ID')
SESSION_STRING = os.getenv('SESSION_STRING')
JWT_TOKEN = os.getenv('JWT_TOKEN')
