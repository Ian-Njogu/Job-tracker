import sqlite3
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random
import matplotlib.pyplot as plt

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect("job_tracker.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY,
            company TEXT,
            role TEXT,
            status TEXT,
            applied_date TEXT,
            last_update TEXT,
            notes TEXT,
            source TEXT DEFAULT 'Manual'
        )
    """)
    conn.commit()
    conn.close()

#  Add/Edit Applications
def add_application(company, role, status="Applied", notes="", source="Manual"):
    if not company.strip() or not role.strip(): # Validate input
        print("❌ Company and Role fields cannot be empty.")
        return
    conn = sqlite3.connect("job_tracker.db")
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO applications (company, role, status, applied_date, last_update, notes, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (company, role, status, today, today, notes, source))
    conn.commit()
    conn.close()
    print(f"✅ Added: {role} at {company}")

# Indeed does not allow scraping:( have to switch to an API.
# # --- Web Scraper (Indeed) ---
# def scrape_indeed(job_title, location="Remote", max_pages=1):
#     base_url = "https://www.indeed.com"
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
#     }
#     jobs = []

#     for page in range(max_pages):
#         url = f"{base_url}/jobs?q={job_title.replace(' ', '+')}&l={location}&start={page * 10}"
#         try:
#             response = requests.get(url, headers=headers)
#             soup = BeautifulSoup(response.text, "html.parser")
            
#             for job_card in soup.find_all("div", class_="job_seen_beacon"):
#                 title = job_card.find("h2", class_="jobTitle").text.strip()
#                 company = job_card.find("span", class_="companyName").text.strip()
#                 salary = job_card.find("div", class_="salary-snippet")
#                 salary = salary.text.strip() if salary else "Not specified"
                
#                 jobs.append({
#                     "Title": title,
#                     "Company": company,
#                     "Salary": salary,
#                     "Source": "Indeed"
#                 })
            
#             time.sleep(random.uniform(1, 3))  # Avoid rate-limiting
        
#         except Exception as e:
#             print(f"⚠️ Error scraping page {page + 1}: {e}")
#     return pd.DataFrame(jobs)

def scrape_jsearch(job_title, max_results=10):
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": "d8b1beb0ebmsh41fec65ae23bb00p1c815djsn552f6b8f3b53",
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    params = {"query": job_title, "num_pages": 1}
    response = requests.get(url, headers=headers, params=params)
    print(response.status_code)
    print(response.json())

   
    response.raise_for_status()
    data = response.json()

    jobs = []
    for job in data.get("data", [])[:max_results]:
        jobs.append({
            "Title": job.get("job_title", "N/A"),
            "Company": job.get("company_name", "N/A"),
            "Salary": job.get("salary", "Not specified"),
            "Source": "JSearch"
        })

    return pd.DataFrame(jobs)

# --- Analytics ---
def show_analytics():
    conn = sqlite3.connect("job_tracker.db")
    df = pd.read_sql_query("SELECT * FROM applications", conn)
    
    if df.empty:
        print("No applications found.")
        return
    
    # Success rates
    total = len(df)
    interviews = len(df[df["status"].str.contains("Interview")])
    offers = len(df[df["status"] == "Offer"])
    
    print("\n=== Application Analytics ===")
    print(f"Total Applications: {total}")
    print(f"Interview Rate: {interviews/total:.1%}")
    print(f"Offer Rate: {offers/interviews:.1%}" if interviews else "N/A")
    
    # Salary analysis (if scraped data exists)
    if "Indeed" in df["source"].values:
        salary_data = df[df["source"] == "Indeed"]["notes"].str.extract(r'Salary: (.*)')[0]
        print("\n=== Salary Insights ===")
        print(salary_data.value_counts())

# --- Plotting ---
def plot_status_distribution():
    conn = sqlite3.connect("job_tracker.db")
    df = pd.read_sql_query("SELECT status FROM applications", conn)
    status_counts = df["status"].value_counts()
    
    status_counts.plot(kind="bar", color="skyblue")
    plt.title("Application Status Distribution")
    plt.xlabel("Status")
    plt.ylabel("Count")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# --- CLI Menu ---
def main():
    init_db()
    while True:
        print("\n==== JOB APPLICATION TRACKER ====")
        print("1. Add Manual Entry")
        print("2. Scrape Job Postings (Indeed)")
        print("3. View Analytics")
        print("4. Plot Status Distribution")
        print("5. Exit")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            company = input("Company: ")
            role = input("Role: ")
            add_application(company, role)
        
        elif choice == "2":
            job_title = input("Job title to search: ")
            jobs_df = scrape_jsearch(job_title)

            if not jobs_df.empty:
                print("\n--- Scraped Jobs ---")
                print(jobs_df[["Title", "Company", "Salary"]].head())

                if input("\nSave these jobs? (y/n): ").strip().lower() == "y":
                    for _, row in jobs_df.iterrows():
                        add_application(
                            company=row["Company"],
                            role=row["Title"],
                            notes=f"Salary: {row['Salary']}",
                            source="JSearch"
                        )
                else:
                    print("❌ Jobs not saved.")

                if input("\nReturn to menu (m) or exit (e)? ").strip().lower() == "e":
                    print("Exiting...")
                    break
            else:
                print("❌ No jobs found.")


        elif choice == "3":
            show_analytics()
        
        elif choice == "4":
            plot_status_distribution()
        
        elif choice == "5":
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Try again.")
        time.sleep(1)

if __name__ == "__main__":
    main()