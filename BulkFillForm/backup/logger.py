import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os
import re
import csv
from datetime import datetime
import deathbycaptcha

# === DEATHBYCAPTCHA CREDENTIALS ===
DBC_USERNAME = 'bol7'  # Replace with your actual username
DBC_PASSWORD = 'Qwerty!23456'  # Replace with your actual password

FORM_DATA = {}

# === LOGGING TO CSV ===
def log_result(url, status, contact_url=None):
    filename = "submission_report.csv"
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Timestamp', 'URL', 'Contact Page', 'Status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'URL': url,
            'Contact Page': contact_url or 'N/A',
            'Status': status
        })

# === CAPTCHA SOLVER ===
def solve_recaptcha_v2(driver, site_url, site_key):
    print("🔐 Solving reCAPTCHA via DeathByCaptcha...")
    client = deathbycaptcha.SocketClient(DBC_USERNAME, DBC_PASSWORD)
    captcha_data = {
        'googlekey': site_key,
        'pageurl': site_url,
        'type': 4
    }
    try:
        captcha = client.decode(type=4, token_params=captcha_data)
        if 'text' in captcha and captcha['text']:
            print("✅ CAPTCHA solved.")
            return captcha['text']
        else:
            print("❌ CAPTCHA solve failed or returned empty text.")
            return None
    except Exception as e:
        print(f"❌ Error solving reCAPTCHA: {e}")
        return None

# === SELENIUM SETUP ===
def launch_browser():
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # Enable headless if needed
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(service=Service(), options=chrome_options)

def is_contact_link(text):
    keywords = ['contact', 'get in touch', 'support', 'reach us', 'help']
    return any(k in text.lower() for k in keywords)

def find_contact_page(driver, base_url):
    try:
        driver.set_page_load_timeout(25)
        driver.get(base_url)
        time.sleep(3)
        links = driver.find_elements(By.TAG_NAME, 'a')
        for link in links:
            text = link.text.strip()
            href = link.get_attribute('href')
            if href and is_contact_link(text):
                return href
    except Exception as e:
        print(f"❌ Failed to load site: {base_url} — {str(e)}")
    return None

# === FORM FILLING ===
def fill_contact_form(driver):
    try:
        forms = driver.find_elements(By.TAG_NAME, 'form')
        if not forms:
            print("⚠️ No forms found.")
            return False

        for form in forms:
            inputs = form.find_elements(By.TAG_NAME, 'input')
            textareas = form.find_elements(By.TAG_NAME, 'textarea')
            all_fields = inputs + textareas
            filled = False

            for field in all_fields:
                try:
                    field_type = field.get_attribute("type") or ""
                    name_attr = field.get_attribute("name") or ""
                    placeholder = field.get_attribute("placeholder") or ""
                    id_attr = field.get_attribute("id") or ""
                    label_text = f"{name_attr} {placeholder} {id_attr}".lower()

                    value = None
                    if any(k in label_text for k in ['name', 'full name', 'yourname', 'contact name']):
                        value = FORM_DATA['name']
                    elif any(k in label_text for k in ['email', 'e-mail', 'your email', 'email address']):
                        value = FORM_DATA['email']
                    elif any(k in label_text for k in ['message', 'comment', 'inquiry', 'details', 'your message']):
                        value = FORM_DATA['message']
                    elif any(k in label_text for k in ['phone', 'mobile', 'contact number']):
                        value = "15557008052"
                    elif any(k in label_text for k in ['subject']):
                        value = "Need WhatsApp Business API?"
                    elif field_type in ['submit', 'button', 'reset', 'hidden']:
                        continue
                    else:
                        value = "www.bol7.com/whatsapp"

                    if value:
                        field.clear()
                        field.send_keys(value)
                        filled = True
                except Exception as e:
                    print(f"⚠️ Could not fill a field: {e}")
                    continue

            if "recaptcha" in driver.page_source.lower():
                print("⚠️ reCAPTCHA detected — attempting to solve.")
                match = re.search(r'data-sitekey="(.*?)"', driver.page_source)
                if match:
                    site_key = match.group(1)
                    token = solve_recaptcha_v2(driver, driver.current_url, site_key)
                    if token:
                        driver.execute_script("""
                            let responseField = document.getElementById("g-recaptcha-response");
                            if (!responseField) {
                                responseField = document.createElement("textarea");
                                responseField.id = "g-recaptcha-response";
                                responseField.name = "g-recaptcha-response";
                                responseField.style.display = "none";
                                document.body.appendChild(responseField);
                            }
                            responseField.value = arguments[0];
                        """, token)
                        time.sleep(2)
                        print("✅ CAPTCHA token injected.")
                    else:
                        print("❌ CAPTCHA solve failed.")
                        return False

            if filled:
                submit_buttons = form.find_elements(By.XPATH, ".//button[@type='submit']") or \
                                 form.find_elements(By.XPATH, ".//input[@type='submit']")
                if submit_buttons:
                    try:
                        driver.execute_script("arguments[0].click();", submit_buttons[0])
                        print("✅ Form submitted via JS.")
                        return True
                    except Exception as e:
                        print(f"⚠️ JavaScript submit failed: {e}")
                        return False
        print("⚠️ Could not detect a valid form to submit.")
        return False
    except Exception as e:
        print(f"❌ Error in form handling: {e}")
        return False

# === PROCESS EACH WEBSITE ===
def process_website(url):
    print(f"\n🔍 Processing: {url}")
    driver = launch_browser()
    try:
        contact_url = find_contact_page(driver, url)
        if contact_url:
            print(f"➡️ Found contact page: {contact_url}")
            try:
                driver.get(contact_url)
                time.sleep(2)
                submitted = fill_contact_form(driver)
                status = "Form Submitted" if submitted else "Form Not Submitted"
                log_result(url, status, contact_url)
            except Exception as e:
                print(f"❌ Failed to load contact page: {e}")
                log_result(url, "Contact Page Load Failed", contact_url)
        else:
            print("❌ Contact page not found.")
            log_result(url, "Contact Page Not Found")
    finally:
        driver.quit()

# === GUI: TKINTER ===
def start_bot():
    FORM_DATA['name'] = name_entry.get()
    FORM_DATA['email'] = email_entry.get()
    FORM_DATA['message'] = message_text.get("1.0", tk.END).strip()

    if not FORM_DATA['name'] or not FORM_DATA['email'] or not FORM_DATA['message']:
        messagebox.showerror("Input Error", "All fields are required.")
        return
    window.destroy()

# === LAUNCH GUI ===
window = tk.Tk()
window.title("Contact Form Autofill")

tk.Label(window, text="Name").grid(row=0, column=0)
name_entry = tk.Entry(window, width=40)
name_entry.insert(0, "Shashank Gupta")
name_entry.grid(row=0, column=1)

tk.Label(window, text="Email").grid(row=1, column=0)
email_entry = tk.Entry(window, width=40)
email_entry.insert(0, "shashank@bol7.com")
email_entry.grid(row=1, column=1)

tk.Label(window, text="Message").grid(row=2, column=0)
message_text = tk.Text(window, width=30, height=5)

message_text.insert("1.0", '''Need WhatsApp Business API?
Start with $6/Month* only.
Chat with Shashank Gupta from BOL7

WhatsApp: +1 555 700 8052
www.bol7.com/whatsapp''')

message_text.grid(row=2, column=1)
submit_btn = tk.Button(window, text="Start Automation", command=start_bot)
submit_btn.grid(row=3, column=0, columnspan=2, pady=10)

window.mainloop()

# === BULK PROCESSING ===
file_path = "Dubai Website_Login_Detector.txt"
if not os.path.exists(file_path):
    print(f"❌ '{file_path}' not found. Add a file with one URL per line.")
    exit()

with open(file_path, 'r') as f:
    websites = [line.strip() for line in f if line.strip()]

for site in websites:
    if not site.startswith('http'):
        site = 'https://' + site
    try:
        process_website(site)
    except Exception as e:
        print(f"❌ Skipping {site} due to unexpected error: {e}")
        log_result(site, "Unhandled Exception")
        continue
