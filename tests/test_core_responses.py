import unittest

from app import create_app
from app.commands.seed_data import seed_default_users
from app.core.errors import BusinessError
from app.core.responses import fail, handle_business, ok
from app.core.validation import parse_pagination_args
from app.extensions import db
from tests.test_support import create_isolated_test_app


class ResponseContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app("testing")

    def test_success_response_preserves_existing_envelope(self):
        with self.app.app_context():
            response = ok({"id": 1})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.get_json(),
                {"code": 0, "message": "success", "data": {"id": 1}},
            )

            empty_response = ok()
            self.assertEqual(
                empty_response.get_json(),
                {"code": 0, "message": "success", "data": {}},
            )

    def test_failure_response_preserves_existing_envelope(self):
        with self.app.app_context():
            response, status = fail("无权限", code=40301, status=403)
            self.assertEqual(status, 403)
            self.assertEqual(
                response.get_json(),
                {"code": 40301, "message": "无权限", "data": None},
            )

    def test_business_handler_preserves_error_mapping(self):
        with self.app.app_context():
            response, status = handle_business(
                lambda: (_ for _ in ()).throw(
                    BusinessError("状态冲突", code=40901, status=409)
                )
            )
            self.assertEqual(status, 409)
            self.assertEqual(
                response.get_json(),
                {"code": 40901, "message": "状态冲突", "data": None},
            )

            response, status = handle_business(
                lambda: (_ for _ in ()).throw(ValueError("参数错误"))
            )
            self.assertEqual(status, 400)
            self.assertEqual(
                response.get_json(),
                {"code": 40001, "message": "参数错误", "data": None},
            )

    def test_business_handler_does_not_hide_unexpected_errors(self):
        with self.app.app_context():
            with self.assertRaises(RuntimeError):
                handle_business(
                    lambda: (_ for _ in ()).throw(RuntimeError("unexpected"))
                )


class PaginationContractTest(unittest.TestCase):
    def test_defaults_and_numeric_strings(self):
        self.assertEqual(parse_pagination_args(), (1, 20))
        self.assertEqual(parse_pagination_args("2", "100"), (2, 100))

    def test_invalid_values_preserve_existing_messages(self):
        cases = [
            ("abc", "20", "page 和 page_size 必须是整数"),
            ("1", "", "page 和 page_size 必须是整数"),
            ("0", "20", "page 必须大于等于 1"),
            ("1", "0", "page_size 必须在 1 到 100 之间"),
            ("1", "101", "page_size 必须在 1 到 100 之间"),
        ]
        for page, page_size, message in cases:
            with self.subTest(page=page, page_size=page_size):
                with self.assertRaises(BusinessError) as context:
                    parse_pagination_args(page, page_size)
                self.assertEqual(str(context.exception), message)
                self.assertEqual(context.exception.code, 40001)
                self.assertEqual(context.exception.status, 400)


class PaginationApiContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_isolated_test_app()
        with cls.app.app_context():
            seed_default_users()
            db.session.commit()

    def setUp(self):
        self.client = self.app.test_client()
        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))

    def test_invalid_pagination_uses_business_error_envelope(self):
        cases = [
            ("page=abc", "page 和 page_size 必须是整数"),
            ("page=0", "page 必须大于等于 1"),
            ("page_size=101", "page_size 必须在 1 到 100 之间"),
        ]
        for query, message in cases:
            with self.subTest(query=query):
                response = self.client.get(
                    f"/api/v1/admin/hour-applications?{query}"
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.get_json(),
                    {"code": 40001, "message": message, "data": None},
                )


if __name__ == "__main__":
    unittest.main()
