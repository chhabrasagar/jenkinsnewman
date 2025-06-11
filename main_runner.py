import json
import os
import subprocess
import requests

# Load environment variables
POSTMAN_API_KEY = os.getenv('POSTMAN_API_KEY')
COLLECTION_UID = os.getenv('COLLECTION_UID')
BASE_URL = os.getenv('BASE_URL')
WEB_TOKEN = os.getenv('WEB_TOKEN')
EMAIL = os.getenv('EMAIL')

if not all([POSTMAN_API_KEY, COLLECTION_UID, BASE_URL, WEB_TOKEN, EMAIL]):
    raise Exception("Missing one or more required environment variables.")

AUTH_TOKEN = {
    "email": EMAIL,
    "webToken": WEB_TOKEN
}
auth_token_str = json.dumps(AUTH_TOKEN)

def download_postman_collection():
    print("Downloading Postman collection...")
    url = f"https://api.getpostman.com/collections/{COLLECTION_UID}"
    headers = {"X-Api-Key": POSTMAN_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    collection_data = response.json()

    # Save only the 'collection' object as expected by Newman
    with open("collection.json", "w") as f:
        json.dump(collection_data["collection"], f)
    
    print("Collection saved as collection.json")

def run_newman_for_each():
    print("Starting Newman runs...")
    
    with open("companies.json", "r") as f:
        companies = json.load(f)

    os.makedirs("results/htmlextra-reports", exist_ok=True)

    for item in companies:
        company = item["companyName"]
        module = item["module"]
        safe_name = f"{company}_{module}".replace(" ", "_").replace("&", "").replace("/", "_")

        # Add auth token and base_url to each data entry
        data_entry = {
            **item,
            "base_url": BASE_URL,
            "Auth-Token": auth_token_str
        }

        # Write individual iteration data
        temp_data_file = f"temp_data_{safe_name}.json"
        with open(temp_data_file, "w") as f:
            json.dump([data_entry], f)

        # Report paths
        result_file = f"results/result_{safe_name}.json"
        html_report = f"results/htmlextra-reports/{safe_name}.html"

        command = [
            "newman", "run", "collection.json",
            "--iteration-data", temp_data_file,
            "--reporters", "json,htmlextra",
            "--reporter-json-export", result_file,
            "--reporter-htmlextra-export", html_report,
            "--reporter-htmlextra-title", f"{company} - {module}",
            "--reporter-htmlextra-darkTheme", "true"
        ]

        print(f"Running Newman for {company} ({module})")
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"Passed: {company} - {module}")
        else:
            print(f"Failed: {company} - {module}")
            print(result.stdout)
            print(result.stderr)

        os.remove(temp_data_file)

if __name__ == "__main__":
    download_postman_collection()
    run_newman_for_each()
