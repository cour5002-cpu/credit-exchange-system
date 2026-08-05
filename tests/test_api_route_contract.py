import hashlib
import unittest

from app import create_app


class ApiRouteContractTest(unittest.TestCase):
    EXPECTED_ROUTE_COUNT = 158
    EXPECTED_API_ROUTE_COUNT = 132
    EXPECTED_ROUTE_SHA256 = (
        "f908876d4613dfaf5feb223077a729f1934af410653d6e1e60c43e077d9a5554"
    )
    EXPECTED_API_ENDPOINT_SHA256 = (
        "c7faa0b1e095c0a7abd9268dc5e0854cba5e64680e804d90b3a6019f511b2dae"
    )

    @classmethod
    def setUpClass(cls):
        cls.app = create_app("testing")

    @staticmethod
    def _methods(rule):
        return ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))

    def test_route_paths_and_methods_match_v1_baseline(self):
        rows = sorted(
            f"{rule.rule}|{self._methods(rule)}"
            for rule in self.app.url_map.iter_rules()
        )
        api_rows = [row for row in rows if row.startswith("/api/v1")]

        self.assertEqual(len(rows), self.EXPECTED_ROUTE_COUNT)
        self.assertEqual(len(api_rows), self.EXPECTED_API_ROUTE_COUNT)
        self.assertEqual(
            hashlib.sha256("\n".join(rows).encode()).hexdigest(),
            self.EXPECTED_ROUTE_SHA256,
        )

    def test_api_endpoint_names_match_v1_baseline(self):
        rows = sorted(
            f"{rule.rule}|{self._methods(rule)}|{rule.endpoint}"
            for rule in self.app.url_map.iter_rules()
            if str(rule.rule).startswith("/api/v1")
        )
        self.assertEqual(
            hashlib.sha256("\n".join(rows).encode()).hexdigest(),
            self.EXPECTED_API_ENDPOINT_SHA256,
        )

    def test_no_api_path_and_method_is_registered_twice(self):
        pairs = []
        for rule in self.app.url_map.iter_rules():
            if not str(rule.rule).startswith("/api/v1"):
                continue
            for method in rule.methods - {"HEAD", "OPTIONS"}:
                pairs.append((str(rule.rule), method))
        self.assertEqual(len(pairs), len(set(pairs)))


if __name__ == "__main__":
    unittest.main()
