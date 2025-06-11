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
    # Generate timestamped filename
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    local_file = 'reports/htmlreport.html'
    s3_key = f'reports/htmlreport_{timestamp}.html'

    if not os.path.exists(local_file):
        print(f"Report not found at {local_file}")
        return

    # Upload to S3
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION_NAME
    )

    try:
        s3.upload_file(local_file, BUCKET_NAME, s3_key)
        print(f"Report uploaded successfully to s3://{BUCKET_NAME}/{s3_key}")
        return s3_key
    except Exception as e:
        print(f"Failed to upload report: {e}")
        return None

def generate_presigned_url(s3_key):
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION_NAME
    )

    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=86400
        )
        print(f"\n Pre-signed URL (valid for 24 hour):\n{url}")
    except Exception as e:
        print(f"Could not generate pre-signed URL: {e}")

if __name__ == "__main__":
    uploaded_key = upload_report()
    if uploaded_key:
        generate_presigned_url(uploaded_key)
