import json
import os
import subprocess
import sys
import requests

# Postman API details
POSTMAN_API_KEY = 'PMAK-684680352c35f10001b70943-ef03e4f308962aca5b3a25d2e17cb100ea'
COLLECTION_UID = '43612186-ee747e79-3b13-4b5d-a0fb-0ab65e5eb73c'
ENV_UID = '43612186-c1b130eb-94b4-4aab-bf36-53c2f914e946'

def download_postman_collection():
    print("⬇️  Downloading Postman collection...")
    url = f"https://api.getpostman.com/collections/{COLLECTION_UID}"
    headers = {"X-Api-Key": POSTMAN_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    with open("collection.json", "w") as f:
        json.dump(response.json(), f)
    print("Collection downloaded and saved as collection.json")

def download_postman_environment():
    print("⬇️  Downloading Postman environment...")
    url = f"https://api.getpostman.com/environments/{ENV_UID}"
    headers = {"X-Api-Key": POSTMAN_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    with open("environment.json", "w") as f:
        json.dump(response.json(), f)
    print("Environment downloaded and saved as environment.json")

def run_newman_test(company_name, failure_summary):
    print(f"🚀 Running test for: {company_name}")
    safe_name = company_name.replace(" ", "_").replace("&", "")
    result_file = f"result_{safe_name}.json"
    allure_dir = f"results/allure-results/{safe_name}"
    os.makedirs(allure_dir, exist_ok=True)

    command = [
        "newman", "run", "collection.json",
        "-e", "environment.json",
        "--global-var", f"companyName={company_name}",
        "--reporters", "json,allure",
        "--reporter-json-export", result_file,
        "--reporter-allure-export", allure_dir
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f"❌ Newman failed for {company_name}")
        if os.path.exists(result_file):
            with open(result_file) as f:
                result_data = json.load(f)
            failures = result_data.get("run", {}).get("failures", [])
            for fail in failures:
                failure_summary.append({
                    "file": result_file,
                    "request": fail.get("source", {}).get("name", "Unknown request"),
                    "error": fail.get("error", {}).get("message", "Unknown error")
                })
        else:
            failure_summary.append({
                "file": result_file,
                "request": company_name,
                "error": "Newman run failed and no result file was generated."
            })

def main():
    try:
        download_postman_collection()
        download_postman_environment()
    except requests.HTTPError as e:
        print(f"❌ Failed to download collection or environment: {e}")
        sys.exit(1)

    if not os.path.exists("companies.json"):
        print("❌ companies.json not found.")
        sys.exit(1)

    with open("companies.json") as f:
        companies = json.load(f)

    print(f"📦 Total companies to process: {len(companies)}")

    os.makedirs("results/allure-results", exist_ok=True)
    failure_summary = []

    for company in companies:
        run_newman_test(company["companyName"], failure_summary)

    if failure_summary:
        with open("failed_tests_summary.json", "w") as f:
            json.dump(failure_summary, f, indent=2)
        print(f"📋 Failure summary: {len(failure_summary)} failed tests written to failed_tests_summary.json")
    else:
        print("✅ All Newman tests completed successfully.")

if __name__ == "__main__":
    print("+ python3 main_runner.py")
    main()
