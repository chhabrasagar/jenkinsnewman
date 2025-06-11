import boto3
import os
from datetime import datetime

# Set your AWS credentials (optional if set in Jenkins environment)
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION_NAME = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")

# Bucket and file settings
BUCKET_NAME = "credence-qa-results"
REPORT_FILE_PATH = "reports/htmlreport.html"  # path to local report
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
S3_KEY = f"reports/htmlreport_{timestamp}.html"  # file name in S3

def upload_report():
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION_NAME
    )

    try:
        s3.upload_file(REPORT_FILE_PATH, BUCKET_NAME, S3_KEY)
        print(f"✅ Report uploaded successfully to s3://{BUCKET_NAME}/{S3_KEY}")
    except Exception as e:
        print(f"❌ Failed to upload report: {e}")

if __name__ == "__main__":
    upload_report()
