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

# --- Add/Edit Applications ---
def add_application(company, role, status="Applied", notes="", source="Manual"):
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

# --- Web Scraper (Indeed) ---
def scrape_indeed(job_title, location="Remote", max_pages=1):
    base_url = "https://www.indeed.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    jobs = []

    for page in range(max_pages):
        url = f"{base_url}/jobs?q={job_title.replace(' ', '+')}&l={location}&start={page * 10}"
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            
            for job_card in soup.find_all("div", class_="job_seen_beacon"):
                title = job_card.find("h2", class_="jobTitle").text.strip()
                company = job_card.find("span", class_="companyName").text.strip()
                salary = job_card.find("div", class_="salary-snippet")
                salary = salary.text.strip() if salary else "Not specified"
                
                jobs.append({
                    "Title": title,
                    "Company": company,
                    "Salary": salary,
                    "Source": "Indeed"
                })
            
            time.sleep(random.uniform(1, 3))  # Avoid rate-limiting
        
        except Exception as e:
            print(f"⚠️ Error scraping page {page + 1}: {e}")
    
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
            job_title = input("Job title to scrape: ")
            location = input("Location (e.g., 'Remote'): ") or "Remote"
            jobs_df = scrape_indeed(job_title, location)

            if not jobs_df.empty:
                print("\n--- Scraped Jobs ---")
                try:
                    # Display the first 5 jobs cleanly
                    print(jobs_df[["Title", "Company", "Salary"]].head())
                except KeyError as e:
                    print("⚠️ Unexpected data format:", e)
                    print(jobs_df.head())

                confirm = input("\nSave these jobs to the database? (y/n): ").strip().lower()
                if confirm == "y":
                    for _, row in jobs_df.iterrows():
                        add_application(
                            company=row.get("Company", "Unknown"),
                            role=row.get("Title", "Unknown"),
                            notes=f"Salary: {row.get('Salary', 'N/A')}",
                            source="Indeed"
                        )
                else:
                    print("❌ Jobs not saved.")

                next_action = input("\nType 'm' to return to the menu or 'e' to exit: ").strip().lower()
                if next_action == "e":
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

if __name__ == "__main__":
    main()