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
    collection_data = response.json()
    with open("collection.json", "w") as f:
        json.dump(collection_data, f)
    print("📁 Collection downloaded and saved as collection.json")

def download_postman_environment():
    print("⬇️  Downloading Postman environment...")
    url = f"https://api.getpostman.com/environments/{ENV_UID}"
    headers = {"X-Api-Key": POSTMAN_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    env_data = response.json()
    with open("environment.json", "w") as f:
        json.dump(env_data, f)
    print("📁 Environment downloaded and saved as environment.json")

def run_newman_test(company_name, failure_summary):
    print(f"\n🚀 Running test for: {company_name}")

    # Clean filename
    safe_name = company_name.replace(" ", "_").replace("&", "")
    result_file = f"result_{safe_name}.json"
    allure_dir = f"results/allure-results/{safe_name}"

    os.makedirs(allure_dir, exist_ok=True)

    command = [
        "newman", "run", "collection.json",
        "-e", "environment.json",
        "--global-var", f"companyName={company_name}",
        "--reporters", "cli,json,allure",
        "--reporter-json-export", result_file,
        "--reporter-allure-export", allure_dir
    ]

    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"✅ Newman test passed for {company_name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Newman failed for {company_name}")
        print("🔻 STDOUT:\n", e.stdout)
        print("🔻 STDERR:\n", e.stderr)

        if os.path.exists(result_file):
            with open(result_file) as f:
                result_data = json.load(f)
            failures = []
            for run in result_data.get("run", {}).get("failures", []):
                failures.append({
                    "file": result_file,
                    "request": run.get("source", {}).get("name", "Unknown request"),
                    "error": run.get("error", {}).get("message", "Unknown error")
                })
            failure_summary.extend(failures)
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
        print(f"❌ Error downloading collection or environment: {e}")
        sys.exit(1)

    if not os.path.exists("companies.json"):
        print("❌ companies.json not found. Please provide the file with company names.")
        sys.exit(1)

    with open("companies.json") as f:
        companies = json.load(f)

    print(f"\n📦 Total companies to process: {len(companies)}")
    os.makedirs("results/allure-results", exist_ok=True)

    failure_summary = []

    for company in companies:
        company_name = company["companyName"]
        run_newman_test(company_name, failure_summary)

    if failure_summary:
        with open("failed_tests_summary.json", "w") as f:
            json.dump(failure_summary, f, indent=2)
        print(f"\n📋 Failure summary: {len(failure_summary)} failed tests written to failed_tests_summary.json")
    else:
        print("\n✅ All Newman tests completed successfully.")

if __name__ == "__main__":
    main()
