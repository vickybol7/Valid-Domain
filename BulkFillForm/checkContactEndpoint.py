import time
import csv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Function to detect if link text or href likely points to a contact page
def is_contact_link(text):
    keywords = ['contact', 'get in touch', 'reach us']
    return any(keyword.lower() in text.lower() for keyword in keywords)

# Function to find contact page
def find_contact_page(driver, base_url):
    try:
        driver.set_page_load_timeout(25)
        driver.get(base_url)
        time.sleep(3)
        links = driver.find_elements(By.TAG_NAME, 'a')
        for link in links:
            text = link.text.strip()
            href = link.get_attribute('href')
            if href and is_contact_link(text + ' ' + href):
                return href
    except Exception as e:
        print(f"❌ Failed to load site: {base_url} — {str(e)}")
    return None

# Load domains from CSV
input_csv = "checkContactEndpoint.csv"
domains = []
if os.path.exists(input_csv):
    with open(input_csv, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:  # Skip empty rows
                domain = row[0].strip()
                if not domain.startswith("http"):
                    domain = "https://" + domain
                domains.append(domain)
else:
    print(f"❌ File not found: {input_csv}")
    exit(1)

# Set up Selenium with headless Chrome
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(), options=options)

# Output CSV
output_csv = "domains_with_contact_page.csv"
with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=['contact_page'])
    writer.writeheader()

    for domain in domains:
        contact_page = find_contact_page(driver, domain)
        if contact_page:
            print(f"✅ Found contact page: {domain} -> {contact_page}")
            writer.writerow({'contact_page': contact_page})
        else:
            print(f"❌ No contact page found: {domain}")

driver.quit()
print(f"\n✅ Done. Results written to {output_csv}")

