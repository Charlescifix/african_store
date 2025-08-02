from dotenv import load_dotenv
import os
import sys

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    def __init__(self):
        self.validate_config()
    
    def validate_config(self):
        if not self.DATABASE_URL:
            print("ERROR: DATABASE_URL environment variable is not set!")
            print("Please set DATABASE_URL in your environment or .env file")
            sys.exit(1)
        
        if not self.DATABASE_URL.startswith(('postgresql://', 'postgres://')):
            print("WARNING: DATABASE_URL should start with 'postgresql://' or 'postgres://'")

settings = Settings()
