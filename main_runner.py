import json
import os
import subprocess
import sys
import requests

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


def download_postman_collection():
    print("📥 Downloading Postman collection...")
    url = f"https://api.getpostman.com/collections/{COLLECTION_UID}"
    headers = {"X-Api-Key": POSTMAN_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    collection_data = response.json()
    with open("collection.json", "w") as f:
        json.dump(collection_data, f)
    print("✅ Collection saved as collection.json")


def run_newman_test(company_name, failure_summary):
    print(f"\n🚀 Running test for: {company_name}")

    safe_name = company_name.replace(" ", "_").replace("&", "").replace("/", "_")
    result_file = f"result_{safe_name}.json"
    html_dir = f"results/htmlextra-reports/{safe_name}"
    html_report = os.path.join(html_dir, "report.html")
    os.makedirs(html_dir, exist_ok=True)

    temp_data = [{"companyName": company_name}]
    with open("temp_company.json", "w") as f:
        json.dump(temp_data, f)

    command = [
        "newman", "run", "collection.json",
        "--env-var", f"base_url={BASE_URL}",
        "--env-var", f"Auth-Token={auth_token_str}",
        "--global-var", f"companyName={company_name}",
        "--reporters", "json,htmlextra",
        "--reporter-json-export", result_file,
        "--reporter-htmlextra-export", html_report,
        "--reporter-htmlextra-title", f"Report for {company_name}",
        "--reporter-htmlextra-darkTheme", "true"
    ]

    stdout_log = f"{safe_name}_stdout.log"
    stderr_log = f"{safe_name}_stderr.log"

    with open(stdout_log, "w") as out, open(stderr_log, "w") as err:
        try:
            subprocess.run(command, check=True, stdout=out, stderr=err, text=True)
            print(f"✅ Newman test passed for {company_name}")
        except subprocess.CalledProcessError:
            print(f"❌ Newman test failed for {company_name}")
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
    except requests.HTTPError as e:
        print(f"❌ Error downloading collection: {e}")
        sys.exit(1)

    if not os.path.exists("companies.json"):
        print("❌ companies.json not found. Please create the file with company names.")
        sys.exit(1)

    with open("companies.json") as f:
        companies = json.load(f)

    if not companies or not isinstance(companies, list):
        print("❌ Invalid format in companies.json. Expected a list of objects with companyName.")
        sys.exit(1)

    print(f"\n📦 Total companies to process: {len(companies)}")
    os.makedirs("results/htmlextra-reports", exist_ok=True)

    failure_summary = []
    skipped_companies = []

    for company in companies:
        company_name = company.get("companyName")

        if not company_name or company_name.strip().lower() == "null":
            print(f"⚠️ Skipping invalid company name: {repr(company_name)}")
            skipped_companies.append(company_name)
            continue

        run_newman_test(company_name.strip(), failure_summary)

    if failure_summary:
        with open("failed_tests_summary.json", "w") as f:
            json.dump(failure_summary, f, indent=2)
        print(f"\n❌ {len(failure_summary)} failed tests. See failed_tests_summary.json.")
    else:
        print("\n✅ All Newman tests completed successfully.")

    if skipped_companies:
        print(f"\n⚠️ Skipped {len(skipped_companies)} invalid company names.")
        # Optional: Write skipped entries to a file
        # with open("skipped_companies.json", "w") as f:
        #     json.dump(skipped_companies, f, indent=2)


if __name__ == "__main__":
    main()
