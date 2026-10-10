import io
import json
import sys
import unittest
from unittest.mock import MagicMock, patch

from lambda_function import lambda_handler, parse_log_content


class TestLogParser(unittest.TestCase):
    def test_counts_log_levels(self):
        content = (
            "INFO Application started\n"
            "WARNING Slow response\n"
            "ERROR Request failed\n"
            "DEBUG Extra details\n"
        )

        result = parse_log_content(content)

        self.assertEqual(result["total_lines"], 4)
        self.assertEqual(result["INFO"], 1)
        self.assertEqual(result["WARNING"], 1)
        self.assertEqual(result["ERROR"], 1)
        self.assertEqual(result["OTHER"], 1)

    def test_empty_log(self):
        result = parse_log_content("")

        self.assertEqual(result["total_lines"], 0)
        self.assertEqual(result["INFO"], 0)
        self.assertEqual(result["WARNING"], 0)
        self.assertEqual(result["ERROR"], 0)
        self.assertEqual(result["OTHER"], 0)


class TestLambdaHandler(unittest.TestCase):
    def setUp(self):
        self.mock_s3 = MagicMock()
        self.mock_boto3 = MagicMock()
        self.mock_boto3.client.return_value = self.mock_s3
        self.patcher = patch.dict(
            sys.modules, {"boto3": self.mock_boto3}
        )
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_processes_s3_log_event(self):
        self.mock_s3.get_object.return_value = {
            "Body": io.BytesIO(
                b"INFO Started\nWARNING Slow\nERROR Failed\n"
            )
        }

        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {
                            "key": "incoming%2Fapplication.log"
                        },
                    }
                }
            ]
        }

        response = lambda_handler(event, None)
        body = json.loads(response["body"])
        result = body["processed_files"][0]

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(result["bucket"], "test-bucket")
        self.assertEqual(result["key"], "incoming/application.log")
        self.assertEqual(result["total_lines"], 3)
        self.assertEqual(result["INFO"], 1)
        self.assertEqual(result["WARNING"], 1)
        self.assertEqual(result["ERROR"], 1)

        self.mock_s3.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="incoming/application.log",
        )

    def test_skips_unsupported_file(self):
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "incoming/readme.csv"},
                    }
                }
            ]
        }

        response = lambda_handler(event, None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body["processed_files"], [])
        self.mock_s3.get_object.assert_not_called()

    def test_handles_empty_event(self):
        response = lambda_handler({}, None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(body["message"], "No S3 records found")


if __name__ == "__main__":
    unittest.main()
