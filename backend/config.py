import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'

DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/arogya_grid.db')

GOOGLE_API_KEY     = os.getenv('GOOGLE_API_KEY', '')
GOOGLE_PROJECT_ID  = os.getenv('GOOGLE_PROJECT_ID', '')
GOOGLE_REGION      = os.getenv('GOOGLE_REGION', 'us-central1')

USE_REAL_GCP       = os.getenv('USE_REAL_GCP',       'false').lower() == 'true'
USE_REAL_GEMINI    = os.getenv('USE_REAL_GEMINI',    'true').lower()  == 'true'
USE_REAL_FORECAST  = os.getenv('USE_REAL_FORECAST',  'false').lower() == 'true'
USE_REAL_OCR       = os.getenv('USE_REAL_OCR',       'false').lower() == 'true'
USE_REAL_IMAGEN    = os.getenv('USE_REAL_IMAGEN',    'false').lower() == 'true'
USE_REAL_TRANSLATE = os.getenv('USE_REAL_TRANSLATE', 'false').lower() == 'true'

DEMO_STATES        = ['Maharashtra', 'Rajasthan']
DEMO_LANGUAGE      = os.getenv('DEMO_LANGUAGE', 'hi')
STOCKOUT_LEAD_DAYS = int(os.getenv('STOCKOUT_LEAD_DAYS', '14'))
SAFETY_STOCK_DAYS  = int(os.getenv('SAFETY_STOCK_DAYS',  '7'))

GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')

ALLOWED_ORIGINS = os.getenv(
    'ALLOWED_ORIGINS',
    'http://localhost:3000,http://localhost:3001'
).split(',')