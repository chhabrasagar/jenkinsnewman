import json
import os
import subprocess
import sys
import requests

# Your Postman details here
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
    print("Collection downloaded and saved as collection.json")

def download_postman_environment():
    print("⬇️  Downloading Postman environment...")
    url = f"https://api.getpostman.com/environments/{ENV_UID}"
    headers = {"X-Api-Key": POSTMAN_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    env_data = response.json()
    with open("environment.json", "w") as f:
        json.dump(env_data, f)
    print("Environment downloaded and saved as environment.json")

def run_newman_test(company_name, failure_summary):
    print(f"🚀 Running test for: {company_name}")

    # Use --env-var to pass the company name as a variable to your Postman collection if needed
    # Adjust this as per your collection's variable usage
    command = [
        "newman", "run", "collection.json",
        "-e", "environment.json",
        "--env-var", f"companyName={company_name}",
        "--reporters", "json",
        "--reporter-json-export", f"result_{company_name.replace(' ', '_').replace('&','')}.json"
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✅ Newman test passed for {company_name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Newman failed for {company_name}")
        # Read the result JSON if available and extract errors, else add a generic failure
        result_file = f"result_{company_name.replace(' ', '_').replace('&','')}.json"
        if os.path.exists(result_file):
            with open(result_file) as f:
                result_data = json.load(f)
            # Extract failed test details from the newman json output if possible
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
                "error": "Newman run failed but no result file found."
            })

def main():
    try:
        download_postman_collection()
        download_postman_environment()
    except requests.HTTPError as e:
        print(f"Error downloading collection or environment: {e}")
        sys.exit(1)

    with open("companies.json") as f:
        companies = json.load(f)

    print(f"📦 Total companies to process: {len(companies)}")

    failure_summary = []

    for company in companies:
        company_name = company["companyName"]
        run_newman_test(company_name, failure_summary)

    if failure_summary:
        with open("failed_tests_summary.json", "w") as f:
            json.dump(failure_summary, f, indent=2)
        print(f"📋 Failure summary: {len(failure_summary)} failed tests written to failed_tests_summary.json")
    else:
        print("✅ All tests completed successfully.")

if __name__ == "__main__":
    main()
