import json
import os
import subprocess
import sys
import requests

# Postman API details
POSTMAN_API_KEY = os.getenv('POSTMAN_API_KEY')
COLLECTION_UID = os.getenv('COLLECTION_UID')
BASE_URL = os.getenv('BASE_URL')
WEB_TOKEN = os.getenv('WEB_TOKEN')
EMAIL = os.getenv('EMAIL')

AUTH_TOKEN = {
    "email": EMAIL,
    "webToken": WEB_TOKEN
}
auth_token_str = json.dumps(AUTH_TOKEN)

COLLECTION_FILE = "collection.json"
ENV_FILE = "environment.json"
REPORT_DIR = "./reports"
HTML_REPORT = os.path.join(REPORT_DIR, "htmlreport.html")
JSON_REPORT = os.path.join(REPORT_DIR, "report.json")

# Determine DATA_FILE
DATA_FILE = "companies.json"  # default fallback

def determine_data_file():
    global DATA_FILE

    # 1. Check if uploaded file exists (via Jenkins file param)
    uploaded_file = "CUSTOM_JSON_FILE"
    if os.path.exists(uploaded_file):
        DATA_FILE = uploaded_file
        print(f"Using uploaded JSON file: {DATA_FILE}")
        return

    # 2. Check if JSON text is passed as CLI argument
    if len(sys.argv) > 1:
        try:
            input_data = json.loads(sys.argv[1])
            with open("file.json", "w") as f:
                json.dump(input_data, f, indent=2)
            DATA_FILE = "file.json"
            print("JSON data received via CLI and saved to file.json")
        except json.JSONDecodeError:
            print("Invalid JSON passed via CLI. Falling back to default companies.json")
    else:
        print("No custom input provided. Using default companies.json")

def download_postman_collection():
    print("Downloading Postman collection...")
    url = f"https://api.getpostman.com/collections/{COLLECTION_UID}"
    headers = {"X-Api-Key": POSTMAN_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    collection_data = response.json()["collection"]
    with open(COLLECTION_FILE, "w") as f:
        json.dump(collection_data, f, indent=2)
    print(f"Collection saved as {COLLECTION_FILE}")

def run_newman():
    print(f"Running Newman with data file: {DATA_FILE}")
    os.makedirs(REPORT_DIR, exist_ok=True)
    command = [
        "newman", "run", COLLECTION_FILE,
        "--env-var", f"base_url={BASE_URL}",
        "--env-var", f"Auth-Token={auth_token_str}",
        "-d", DATA_FILE,
        "-r", "htmlextra,json",
        "--reporter-htmlextra-export", HTML_REPORT,
        "--reporter-json-export", JSON_REPORT
    ]
    try:
        subprocess.run(command, check=True)
        print("Newman run complete. Reports generated.")
    except subprocess.CalledProcessError as e:
        print(f"Newman run failed: {e}")
        exit(1)

if __name__ == "__main__":
    determine_data_file()
    download_postman_collection()
    run_newman()
