# Progree Cloud Computing Internship — Task 3

## Event-Driven Serverless Compute Application Engine

**Cloud Provider:** Amazon Web Services (AWS)  
**Region:** Europe (Ireland), `eu-west-1`  
**Runtime:** Python 3.12  
**Compute:** AWS Lambda  
**Event Source:** Amazon S3  
**Logging:** Amazon CloudWatch Logs

## 1. Project Overview

This project implements an event-driven, serverless log-processing
application using AWS Lambda, Amazon S3, and Amazon CloudWatch Logs.

When a supported log file is uploaded to a designated S3 prefix, an
S3 object-creation event automatically invokes the Lambda function.
The function retrieves the uploaded file, classifies its log entries,
calculates summary statistics, and records the results in CloudWatch.

The implementation demonstrates serverless computing, event-driven
architecture, Python development, IAM least privilege, automated
testing, and cloud monitoring.

## 2. Objectives

The objectives are to:

- Implement a Python serverless function using AWS Lambda.
- Trigger the function automatically when an object is uploaded to S3.
- Parse text logs and count INFO, WARNING, ERROR, and OTHER entries.
- Record structured execution results in CloudWatch Logs.
- Apply least-privilege permissions to the Lambda execution role.
- Test the application locally before deploying it to AWS.
- Verify the complete event-driven workflow using real AWS resources.

## 3. System Architecture

```text
                 User uploads log file
                          |
                          v
                +--------------------+
                |     Amazon S3      |
                |  incoming/ prefix  |
                +--------------------+
                          |
                          | ObjectCreated event
                          v
                +--------------------+
                |     AWS Lambda     |
                | Python 3.12         |
                | Log Processing      |
                +--------------------+
                          |
                          | Structured execution logs
                          v
                +--------------------+
                |  CloudWatch Logs   |
                | Processing Results |
                +--------------------+
```

The Lambda function reads input files from S3 and writes its processing
results to CloudWatch Logs. It does not upload output files to S3, which
avoids a recursive upload-trigger loop in the current design.

## 4. AWS Resource Configuration

| Resource | Configuration |
|---|---|
| S3 bucket | `progree-task3-logs-precious-2026` |
| Input prefix | `incoming/` |
| Lambda function | `progree-task3-log-processor` |
| AWS region | `eu-west-1` |
| Runtime | Python 3.12 |
| Architecture | x86_64 |
| Memory allocation | 128 MB |
| Timeout | 15 seconds |
| Handler | `lambda_function.lambda_handler` |
| CloudWatch log group | `/aws/lambda/progree-task3-log-processor` |

The Lambda function was created with a basic execution role that allows
it to publish execution logs to CloudWatch Logs.

## 5. Repository Structure

```text
task-3-serverless/
├── README.md
├── lambda_function.zip
├── policies/
│   └── task3-read-incoming-logs.json
├── sample-data/
│   ├── application.log
│   └── trigger-validation.log
├── screenshots/
│   ├── 05-s3-lambda-trigger.JPG
│   ├── 06-cloudwatch-processing-success.JPG
│   ├── 07-s3-trigger-details.JPG
│   └── 08-iam-least-privilege.JPG
├── src/
│   └── lambda_function.py
└── tests/
    └── test_lambda_function.py
```

The ZIP archive is the deployment package used by AWS Lambda. It should
contain `lambda_function.py` at the root of the archive.

## 6. Application Implementation

The application is implemented in Python and uses Boto3 to retrieve
objects from Amazon S3.

### 6.1 Log Parser

The `parse_log_content(content)` function:

1. Splits the input text into individual lines.
2. Ignores blank lines.
3. Identifies INFO, WARNING, and ERROR entries.
4. Classifies entries without a recognized level as OTHER.
5. Returns the total number of non-empty lines and the category counts.

### 6.2 Lambda Handler

The `lambda_handler(event, context)` function:

1. Receives an S3 event notification.
2. Extracts the bucket name and object key.
3. Decodes URL-encoded object keys.
4. Accepts files ending in `.log` or `.txt`.
5. Retrieves the uploaded object through Boto3.
6. Decodes the file contents.
7. Calls the log parser.
8. Writes a structured `LOG_PROCESSING_RESULT` message to CloudWatch.
9. Returns a response containing the processing results.

Unsupported file extensions are skipped.

## 7. IAM Security and Least Privilege

The Lambda execution role has the basic permissions required for
CloudWatch logging and an additional inline policy named:

`Task3ReadIncomingLogsOnly`

The policy is stored locally at:

`policies/task3-read-incoming-logs.json`

Its permissions are restricted to reading objects under the `incoming/`
prefix in the Task 3 bucket.

The relevant policy statement is:

```json
{
  "Sid": "ReadIncomingLogFilesOnly",
  "Effect": "Allow",
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::progree-task3-logs-precious-2026/incoming/*"
}
```

This permission does not grant bucket-wide object reads, object deletion,
or object writes.

The S3 trigger is configured for object-creation events with the
`incoming/` prefix. AWS also configures permission for S3 to invoke
the Lambda function.

The bucket remains private. The function accesses objects through its
execution role rather than requiring public object access.

No AWS access keys, secret keys, or session tokens should be committed
to this repository.

## 8. Local Testing

The log parser was tested locally using the sample file:

`sample-data/application.log`

Run the following command from the repository root:

```bash
PYTHONPATH=task-3-serverless/src python3 - <<'PY'
import json
from pathlib import Path
from lambda_function import parse_log_content

content = Path(
    "task-3-serverless/sample-data/application.log"
).read_text(encoding="utf-8")

result = parse_log_content(content)
print(json.dumps(result, indent=2))

expected = {
    "total_lines": 7,
    "INFO": 3,
    "WARNING": 1,
    "ERROR": 2,
    "OTHER": 1,
}

assert result == expected
print("PASS: All log-processing assertions passed.")
PY
```

Expected counts:

- Total lines: 7
- INFO: 3
- WARNING: 1
- ERROR: 2
- OTHER: 1

### Automated Test Suite

Run the automated tests with:

```bash
PYTHONPATH=task-3-serverless/src \
python3 -m unittest discover \
-s task-3-serverless/tests -v
```

**Recorded result: all five automated tests passed.**

The tests cover:

- Counting log levels.
- Handling empty input.
- Processing a simulated S3 event using a mocked S3 client.
- Skipping unsupported file types.
- Handling an event without S3 records.

The mocked tests run locally and do not upload objects to AWS.

## 9. Lambda Deployment Package

The deployment archive is:

`lambda_function.zip`

It contains `lambda_function.py` at the root of the archive.

The configured handler is:

`lambda_function.lambda_handler`

The ZIP package was created and verified locally before it was uploaded
to the Lambda console.

## 10. AWS Deployment and Verification

### 10.1 Initial Deployment

The Lambda function was created in `eu-west-1` using Python 3.12.
The tested ZIP package was uploaded successfully, and the handler
configuration was verified.

The function was initially configured with a three-second timeout.
Early invocations timed out while attempting to retrieve an S3 object.
The timeout was increased to 15 seconds, after which subsequent
invocations completed successfully.

The available evidence does not establish a single definitive root
cause for the initial delay.

### 10.2 Direct Lambda Test

A direct Lambda test simulated an S3 event for:

`incoming/application.log`

The function returned HTTP-style status code 200 and the following
processing result:

```json
{
  "total_lines": 7,
  "INFO": 3,
  "WARNING": 1,
  "ERROR": 2,
  "OTHER": 1
}
```

This verified that the deployed function could retrieve the object,
parse its contents, and return the expected summary.

### 10.3 Automatic S3 Trigger Test

A separate test file was uploaded to:

`incoming/trigger-validation.log`

S3 automatically invoked the Lambda function following the upload.

CloudWatch recorded the following result:

```json
{
  "total_lines": 3,
  "INFO": 1,
  "WARNING": 1,
  "ERROR": 1,
  "OTHER": 0
}
```

The corresponding Lambda invocation completed successfully, with a
reported duration of approximately 378 milliseconds.

This confirms that the S3 event notification, Lambda invocation,
S3 object retrieval, log parsing, and CloudWatch logging worked together.

## 11. Evidence Screenshots

The following screenshots document the deployed implementation:

| Screenshot | Evidence |
|---|---|
| `05-s3-lambda-trigger.JPG` | Lambda function overview showing the S3 trigger |
| `06-cloudwatch-processing-success.JPG` | Successful processing results in CloudWatch |
| `07-s3-trigger-details.JPG` | S3 trigger configuration details |
| `08-iam-least-privilege.JPG` | IAM execution-role permissions and restricted S3 policy |

Screenshots should be checked for credentials, session tokens, and other
sensitive information before being published to a public repository.

## 12. Cost Considerations

This project uses Amazon S3, AWS Lambda, and CloudWatch Logs.

Actual AWS costs depend on account eligibility, the applicable account
plan, requests, execution duration, stored data, log ingestion, and
retention. Free allowances or account credits should not be treated as
a guarantee that usage will cost zero.

AWS Billing and Cost Management should be monitored during the project.
Temporary resources should be removed when they are no longer required.

## 13. Limitations and Future Improvements

Potential improvements include:

- Using structured logging formats and stricter log parsing rules.
- Adding more comprehensive error handling for failed S3 requests.
- Introducing retry handling and a dead-letter strategy where appropriate.
- Adding automated integration tests for AWS event delivery.
- Setting an appropriate CloudWatch log retention period.
- Adding metrics or alarms for failed invocations.
- Evaluating resource lifecycle and cost-management controls.

These improvements are not represented as completed features in the
current implementation.

## 14. Conclusion

Task 3 demonstrates an event-driven serverless processing pipeline
using Amazon S3, AWS Lambda, Python, and CloudWatch Logs.

The log parser passed five local automated tests, the deployment package
was verified, and successful AWS executions confirmed both direct
processing and automatic invocation following an S3 object upload.

The implementation demonstrates event-driven architecture, serverless
compute, least-privilege IAM permissions, automated testing, and
cloud-based execution logging.
