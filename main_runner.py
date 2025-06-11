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

# Validate required environment variables
required_env_vars = {
    "POSTMAN_API_KEY": POSTMAN_API_KEY,
    "COLLECTION_UID": COLLECTION_UID,
    "BASE_URL": BASE_URL,
    "WEB_TOKEN": WEB_TOKEN,
    "EMAIL": EMAIL
}
missing_vars = [k for k, v in required_env_vars.items() if not v]
if missing_vars:
    raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")

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

    with open("collection.json", "w") as f:
        json.dump(collection_data["collection"], f)
    
    print("Collection saved as collection.json")

def run_newman_for_each():
    print("Starting Newman runs...")

    with open("companies.json", "r") as f:
        companies = json.load(f)

    base_report_dir = "results/htmlextra-reports"
    os.makedirs(base_report_dir, exist_ok=True)

    for item in companies:
        company = item["companyName"]
        module = item["module"]
        safe_company_name = company.replace(" ", "_").replace("&", "").replace("/", "_")
        safe_module_name = module.replace(" ", "_").replace("&", "").replace("/", "_")

        company_report_dir = os.path.join(base_report_dir, safe_company_name)
        os.makedirs(company_report_dir, exist_ok=True)

        # Prepare iteration data
        data_entry = {
            **item,
            "base_url": BASE_URL,
            "Auth-Token": auth_token_str
        }

        temp_data_file = f"temp_data_{safe_company_name}_{safe_module_name}.json"
        with open(temp_data_file, "w") as f:
            json.dump([data_entry], f)

        result_file = f"results/result_{safe_company_name}_{safe_module_name}.json"
        html_report = os.path.join(company_report_dir, f"{safe_module_name}.html")

        command = [
            "newman", "run", "collection.json",
            "--env-var", f"base_url={BASE_URL}",
            "--env-var", f"Auth-Token={auth_token_str}",
            "--iteration-data", temp_data_file,
            "--reporters", "json,htmlextra",
            "--reporter-json-export", result_file,
            "--reporter-htmlextra-export", html_report,
            "--reporter-htmlextra-title", f"{company} - {module}",
            "--reporter-htmlextra-darkTheme", "true"
        ]

        print(f"\n Running Newman for: {company} ({module})")
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"PASSED: {company} - {module}")
        else:
            print(f"FAILED: {company} - {module}")
            print("---- STDOUT ----")
            print(result.stdout)
            print("---- STDERR ----")
            print(result.stderr)

        os.remove(temp_data_file)

if __name__ == "__main__":
    download_postman_collection()
    run_newman_for_each()
