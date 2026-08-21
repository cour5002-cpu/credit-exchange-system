import unittest
from datetime import datetime

from tests.test_support import create_isolated_test_app
from app.utils.time_utils import format_api_datetime, parse_api_datetime


class TimeContractUnitTest(unittest.TestCase):
    def test_inputs_are_normalized_to_shanghai_database_time(self):
        expected = datetime(2026, 7, 26, 16, 0, 0)
        self.assertEqual(parse_api_datetime("2026-07-26T08:00:00Z"), expected)
        self.assertEqual(parse_api_datetime("2026-07-26T16:00:00+08:00"), expected)
        self.assertEqual(parse_api_datetime("2026-07-26T16:00:00"), expected)

    def test_database_time_is_serialized_with_explicit_offset(self):
        self.assertEqual(
            format_api_datetime(datetime(2026, 7, 26, 16, 0, 0)),
            "2026-07-26T16:00:00+08:00",
        )


class SystemTimeApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_isolated_test_app()

    def test_system_time_is_public_and_uses_shanghai_timezone(self):
        response = self.app.test_client().get("/api/v1/system/time")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        data = response.json["data"]
        self.assertEqual(data["timezone"], "Asia/Shanghai")
        self.assertEqual(data["utc_offset"], "+08:00")
        self.assertTrue(data["server_time"].endswith("+08:00"))


if __name__ == "__main__":
    unittest.main()
