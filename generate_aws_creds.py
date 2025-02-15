#!/usr/bin/env python3
import os

def main():
    # Provided credentials (replace these with secure ones, if needed)
    aws_access_key = "AKIA4WJPWX757RLAGXU7"
    aws_secret_key = "WgS1dAUCdPnblbA+lZgyl8ww/0boB7zIJ2Z8Quh0"
    aws_region = "us-east-2"
    
    # Generate a shell file that exports the AWS credentials.
    # In production, you should secure this file.
    content = f"""# AWS Credentials generated on {os.linesep}export AWS_ACCESS_KEY_ID="{aws_access_key}"
export AWS_SECRET_ACCESS_KEY="{aws_secret_key}"
export AWS_DEFAULT_REGION="{aws_region}"
"""
    file_path = "aws_creds.env"
    with open(file_path, "w") as f:
        f.write(content)
    print(f"Credentials saved to {file_path}. Please secure this file (e.g. add to .gitignore, move to a secure location).")

if __name__ == "__main__":
    main()

