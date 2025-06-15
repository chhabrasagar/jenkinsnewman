
import os
import json
import boto3
import requests
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# File and directory paths
COLLECTION_FILE = "collection.json"
DATA_FILE = "companies.json"
REPORT_DIR = "reports"
HTML_REPORT = f"{REPORT_DIR}/htmlreport.html"
JSON_REPORT = f"{REPORT_DIR}/report.json"

# Environment configuration
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
BASE_URL = os.getenv("BASE_URL")
POSTMAN_API_KEY = os.getenv("POSTMAN_API_KEY")
COLLECTION_UID = os.getenv("COLLECTION_UID")

def download_postman_collection():
    """Download the Postman collection using the API key and UID."""
    print("Downloading Postman collection...")
    url = f"https://api.getpostman.com/collections/{COLLECTION_UID}"
    headers = {"X-Api-Key": POSTMAN_API_KEY}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        with open(COLLECTION_FILE, "w") as f:
            json.dump(response.json()["collection"], f, indent=2)
        print("Postman collection downloaded.")
        return True
    except requests.RequestException as e:
        print(f"Failed to download collection: {e}")
        return False

def fetch_web_token():
    """Log in to the system and fetch the webToken."""
    print("Logging in to fetch webToken...")

    login_url = f"{BASE_URL}/api/user/login"
    payload = {
        "email": EMAIL,
        "password": PASSWORD
    }

    try:
        response = requests.post(login_url, json=payload)
        response.raise_for_status()
        token = response.json().get("webToken")
        if token:
            print("webToken fetched successfully.")
            return token
        else:
            print("webToken not found in response.")
            return None
    except requests.RequestException as e:
        print(f"Login failed: {e}")
        return None

def run_newman(web_token):
    """Execute the Newman test run with the provided collection and data file."""
    print("Running Newman collection...")

    if not os.path.exists(DATA_FILE):
        print(f"Data file '{DATA_FILE}' not found.")
        return False

    os.makedirs(REPORT_DIR, exist_ok=True)

    if not EMAIL or not web_token:
        print("EMAIL or webToken not set.")
        return False

    auth_token = json.dumps({
        "email": EMAIL,
        "webToken": web_token
    })

    env_vars = {
        "base_url": BASE_URL,
        "Auth-Token": auth_token
    }

    env_cli_args = []
    for k, v in env_vars.items():
        if v:
            env_cli_args.extend(["--env-var", f"{k}={v}"])

    command = [
        "newman", "run", COLLECTION_FILE,
        "--iteration-data", DATA_FILE,
        *env_cli_args,
        "--reporters", "htmlextra,json",
        "--reporter-htmlextra-export", HTML_REPORT,
        "--reporter-json-export", JSON_REPORT
    ]

    try:
        subprocess.run(command, check=True)
        print("Newman run completed successfully.")
        return True
    except FileNotFoundError:
        print("Newman not found. Is it installed in your environment?")
    except subprocess.CalledProcessError as e:
        print(f"Newman run failed (code {e.returncode}).")
    return False

def upload_to_s3(file_path):
    """Upload a file to the specified S3 bucket."""
    s3 = boto3.client("s3")
    file_name = os.path.basename(file_path)

    if not os.path.exists(file_path):
        print(f"File '{file_path}' not found for S3 upload.")
        return None

    try:
        s3.upload_file(file_path, S3_BUCKET, file_name)
        print(f"Uploaded '{file_name}' to S3 bucket '{S3_BUCKET}'.")
        return file_name
    except Exception as e:
        print(f"Failed to upload to S3: {e}")
        return None

def generate_presigned_url(s3_key):
    """Generate a pre-signed S3 URL for the uploaded file."""
    s3 = boto3.client("s3")
    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": s3_key},
            ExpiresIn=3600  # 1 hour
        )
        print(f"Pre-signed URL: {url}")
        return url
    except Exception as e:
        print(f"Failed to generate pre-signed URL: {e}")
        return None

def cleanup_files():
    """Remove temporary files after execution."""
    print("Cleaning up temporary files...")
    for f in [COLLECTION_FILE, HTML_REPORT, JSON_REPORT]:
        try:
            os.remove(f)
            print(f"Deleted: {f}")
        except FileNotFoundError:
            pass

def main():
    if not download_postman_collection():
        return

    web_token = fetch_web_token()
    if not web_token:
        print("Cannot proceed without webToken.")
        return

    newman_success = run_newman(web_token)

    if os.path.exists(HTML_REPORT):
        s3_key = upload_to_s3(HTML_REPORT)
        if s3_key:
            generate_presigned_url(s3_key)
        else:
            print("Could not upload report to S3.")
    else:
        print("HTML report not generated. Skipping upload.")

    cleanup_files()

    if not newman_success:
        print("Newman run failed. Report (if generated) was still uploaded.")

if __name__ == "__main__":
    main()
