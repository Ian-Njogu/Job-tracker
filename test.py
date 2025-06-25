import sqlite3
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd

def init_db():
    conn = sqlite3.connect("JobTracker.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            status TEXT NOT NULL,
            date_applied DATE NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_application(job_title, company, status="Applied", date_applied=None):
    if not job_title or not company:
        print("❌ Job title and company cannot be empty.")
        return
    if date_applied is None:
        date_applied = datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect("JobTracker.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO applications (job_title, company, status, date_applied)
        VALUES (?, ?, ?, ?)
    ''', (job_title, company, status, date_applied))
    conn.commit()
    conn.close()
    print(f"✅ Added: {job_title} at {company}")
    
def search_linkedin_jobs(keyword, page=1):
   
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
    'x-rapidapi-key': "d8b1beb0ebmsh41fec65ae23bb00p1c815djsn552f6b8f3b53",
    'x-rapidapi-host': "linkedin-job-search-api.p.rapidapi.com",
    'Content-Type': "application/json"
    }
    body = {
        "keywords": keyword,
        "geo_code": 92000000,
        "onsite_remotes": ["Remote", "Hybrid"],
        "date_posted": "past_week",
        "experience_levels": ["Entry level", "Mid senior"],
        "job_types": ["Full-time"],
        "start": (page - 1) * 25
    }
    
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    data = response.json()
    return data.get("data", [])
search_linkedin_jobs("Software Engineer", 1)