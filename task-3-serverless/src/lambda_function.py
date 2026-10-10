import json
import logging
import re
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def parse_log_content(content: str) -> dict:
    """Count log levels in a text log file."""
    counts = {
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
        "OTHER": 0,
    }

    lines = [line for line in content.splitlines() if line.strip()]

    for line in lines:
        match = re.search(r"\b(INFO|WARNING|ERROR)\b", line, re.IGNORECASE)

        if match:
            level = match.group(1).upper()
            counts[level] += 1
        else:
            counts["OTHER"] += 1

    return {
        "total_lines": len(lines),
        **counts,
    }


def lambda_handler(event, context):
    """Process log files whenever Amazon S3 triggers this function."""
    import boto3

    s3 = boto3.client("s3")
    records = event.get("Records", [])
    processed_files = []

    if not records:
        logger.warning("No S3 event records were received.")
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "No S3 records found"}),
        }

    for record in records:
        s3_event = record.get("s3")

        if not s3_event:
            logger.warning("Skipping an event without S3 information.")
            continue

        bucket = s3_event["bucket"]["name"]
        key = unquote_plus(s3_event["object"]["key"])

        if not key.lower().endswith((".log", ".txt")):
            logger.info("Skipping unsupported file: %s", key)
            continue

        response = s3.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode(
            "utf-8", errors="replace"
        )

        summary = parse_log_content(content)

        result = {
            "bucket": bucket,
            "key": key,
            **summary,
        }

        logger.info(
            "LOG_PROCESSING_RESULT %s",
            json.dumps(result, sort_keys=True),
        )

        processed_files.append(result)

    return {
        "statusCode": 200,
        "body": json.dumps({"processed_files": processed_files}),
    }
