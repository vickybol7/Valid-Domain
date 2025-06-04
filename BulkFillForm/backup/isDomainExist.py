import os
import socket
import requests
import csv
from urllib.parse import urlparse

def check_domain(domain, timeout=5):
    domain = domain.strip().lower()
    if not domain:
        return None

    try:
        ip = socket.gethostbyname(domain)
        print(f"Resolved {domain} to {ip}")
    except socket.gaierror:
        print(f"{domain} - ❌ DNS resolution failed")
        return None

    urls_to_try = [f"https://{domain}", f"http://{domain}"]
    for url in urls_to_try:
        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            final_netloc = urlparse(response.url).netloc.lower().replace('www.', '')
            original_domain = domain.replace('www.', '')

            if original_domain in final_netloc and not any(sales in final_netloc for sales in ["godaddy", "sedoparking", "afternic", "dan.com"]):
                print(f"{domain} - ✅ Active and not redirected to marketplace")
                return domain
            else:
                print(f"{domain} - ⚠️ Redirected to {final_netloc}, skipping")
                return None
        except requests.exceptions.RequestException as e:
            print(f"{domain} - ❌ Request failed - {e}")
    return None

def append_to_csv(filename, domain):
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([domain])

# File paths
input_path = os.path.join("Indian Domains", "Indian Domain_1.txt")
output_csv = "existDomain.csv"

# Create CSV with header if not exists
if not os.path.exists(output_csv):
    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Domain"])

# Process domains
if os.path.exists(input_path):
    with open(input_path, 'r') as file:
        for line in file:
            result = check_domain(line)
            if result:
                append_to_csv(output_csv, result)
else:
    print(f"❌ File not found: {input_path}")
