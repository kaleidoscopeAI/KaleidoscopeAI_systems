#!/usr/bin/env bash
set -e

# Ensure this script is sourced, not executed:
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "ERROR: Please use 'source aws_creds_setup.sh' instead of running it directly."
  exit 1
fi

echo "Enter AWS Access Key ID:"
read -r AWS_ACCESS_KEY_ID_INPUT

echo "Enter AWS Secret Access Key:"
read -r AWS_SECRET_ACCESS_KEY_INPUT

echo "Enter AWS Default Region (e.g., us-east-1):"
read -r AWS_DEFAULT_REGION_INPUT

export AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID_INPUT"
export AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY_INPUT"
export AWS_DEFAULT_REGION="$AWS_DEFAULT_REGION_INPUT"

echo "AWS Credentials have been set in this shell:"
echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"
echo "AWS_SECRET_ACCESS_KEY=***HIDDEN***"
echo "AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION"
