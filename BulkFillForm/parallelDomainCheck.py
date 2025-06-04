import os
import socket
import requests
import csv
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
from threading import Lock, Thread
import urllib3
import time
from queue import Queue

# === Configurations ===
FOLDER_PATH = "Indian Domains"
OUTPUT_CSV = "existDomain.csv"
TIMEOUT = 5
BLOCKED_HOSTS = ["godaddy", "sedoparking", "afternic", "dan.com"]
THREADS = multiprocessing.cpu_count() * 2

# === Disable SSL warnings (optional but safe for this use case) ===
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === Thread lock for safe CSV writing ===
write_lock = Lock()

# === Queue for collecting domain results ===
results_queue = Queue()

# === Function to check and validate domain ===
def check_domain(domain):
    domain = domain.strip().lower()
    if not domain:
        return None

    try:
        ip = socket.gethostbyname(domain)
        print(f"Resolved {domain} to {ip}")
    except socket.gaierror:
        print(f"{domain} - ❌ DNS resolution failed")
        return None

    for scheme in ['https', 'http']:
        url = f"{scheme}://{domain}"
        try:
            response = requests.get(url, timeout=TIMEOUT, allow_redirects=True, verify=False)
            final_domain = urlparse(response.url).netloc.lower().replace('www.', '')
            original_domain = domain.replace('www.', '')

            if original_domain in final_domain and not any(b in final_domain for b in BLOCKED_HOSTS):
                print(f"{domain} - ✅ Active and not redirected to marketplace")
                return domain
            else:
                print(f"{domain} - ⚠️ Redirected to {final_domain}, skipping")
                return None
        except requests.exceptions.RequestException as e:
            print(f"{domain} - ❌ Request failed - {e}")
    return None

# === Function to write results from queue to CSV ===
def write_to_csv():
    with open(OUTPUT_CSV, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        while True:
            domain = results_queue.get()
            if domain == "DONE":
                break
            writer.writerow([domain])
            csvfile.flush()

# === Main process ===
def main():
    # Create CSV with header if not present
    if not os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, 'a', newline='') as f:
            csv.writer(f).writerow(["Domain"])

    # Start a background thread for writing to CSV
    writer_thread = Thread(target=write_to_csv)
    writer_thread.start()

    # Read all .txt files from folder
    all_domains = []
    for fname in os.listdir(FOLDER_PATH):
        if fname.endswith(".txt"):
            fpath = os.path.join(FOLDER_PATH, fname)
            with open(fpath, 'r') as f:
                all_domains.extend(f.readlines())

    # Check domains in parallel
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(check_domain, d): d for d in all_domains}
        for future in as_completed(futures):
            result = future.result()
            if result:
                results_queue.put(result)

    # Indicate that all tasks are done by putting "DONE" in the queue
    results_queue.put("DONE")

    # Wait for the writer thread to finish
    writer_thread.join()

    print(f"\n✅ Done. Valid domains have been saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
