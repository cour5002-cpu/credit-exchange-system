import unittest
from io import BytesIO
from uuid import uuid4

from openpyxl import Workbook

from app.commands.seed_data import seed_default_users, seed_system_configs, seed_task_types
from app.extensions import db
from tests.test_support import create_isolated_test_app


def make_xlsx(headers, rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


class Week2ApiRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_isolated_test_app()
        cls.app.config["WTF_CSRF_ENABLED"] = False
        with cls.app.app_context():
            seed_task_types()
            seed_system_configs()
            seed_default_users()
            db.session.commit()

    def setUp(self):
        self.client = self.app.test_client()
        self.suffix = uuid4().hex[:8]

    def login(self, username, password):
        return self.client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )

    def login_admin(self):
        response = self.login("admin", "admin123")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return response

    def post_import(self, target, headers, rows, mode="upsert"):
        file_obj = make_xlsx(headers, rows)
        return self.client.post(
            f"/api/v1/admin/imports/{target}",
            data={"mode": mode, "file": (file_obj, f"{target}.xlsx")},
            content_type="multipart/form-data",
        )

    def test_login_me_logout_and_unauthorized_json(self):
        response = self.login_admin()
        self.assertEqual(response.json["data"]["role"], "admin")

        response = self.client.get("/api/v1/me")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["role"], "admin")

        response = self.client.post("/api/v1/auth/logout")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/v1/me")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json["code"], 40101)

    def test_role_based_teacher_queries_and_admin_permission(self):
        self.login_admin()
        response = self.client.get("/api/v1/teachers/advisors")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json["data"]["items"]), 1)

        response = self.client.get("/api/v1/admin/reviewers")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json["data"]["items"]), 1)

        student_client = self.app.test_client()
        response = student_client.post(
            "/api/v1/auth/login",
            json={"username": "student1", "password": "student123"},
        )
        self.assertEqual(response.status_code, 200)
        response = student_client.get("/api/v1/admin/reviewers")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["code"], 40301)

    def test_import_templates_are_downloadable(self):
        self.login_admin()
        for target in ("students", "teachers", "admins"):
            with self.subTest(target=target):
                response = self.client.get(f"/api/v1/admin/import-templates/{target}")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.content_type,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                self.assertGreater(len(response.data), 0)

    def test_student_teacher_and_admin_imports(self):
        self.login_admin()

        student_no = f"S{self.suffix}"
        student_username = f"stu_{self.suffix}"
        response = self.post_import(
            "students",
            ["student_no", "name", "username", "password", "college", "major", "grade", "class_name"],
            [[student_no, "Week2 Student", student_username, "123456", "管理学院", "信管", "2026", "1班"]],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["success_count"], 1)
        self.assertEqual(response.json["data"]["failed_count"], 0)

        response = self.post_import(
            "students",
            ["student_no", "name", "username"],
            [[student_no, "Week2 Student", student_username]],
            mode="append",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["success_count"], 0)
        self.assertEqual(response.json["data"]["failed_count"], 1)

        response = self.post_import(
            "students",
            ["student_no"],
            [[f"S_MISSING_{self.suffix}"]],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["errors"][0]["field"], "name")

        response = self.post_import(
            "students",
            ["student_no", "name", "email"],
            [[f"S_EMAIL_{self.suffix}", "Bad Email Student", "bad-email"]],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["errors"][0]["field"], "email")

        response = self.post_import(
            "teachers",
            ["teacher_no", "name", "username", "password", "role_flags", "status"],
            [[f"T{self.suffix}", "Week2 Teacher", f"tea_{self.suffix}", "123456", "advisor,reviewer", "active"]],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["success_count"], 1)

        response = self.post_import(
            "teachers",
            ["teacher_no", "name", "role_flags"],
            [[f"T_BAD_ROLE_{self.suffix}", "Bad Role Teacher", "leader"]],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["errors"][0]["field"], "role_flags")

        response = self.post_import(
            "admins",
            ["username", "name", "password", "status"],
            [[f"adm_{self.suffix}", "Week2 Admin", "123456", "active"]],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["success_count"], 1)

        response = self.post_import(
            "admins",
            ["username", "name", "status"],
            [[f"adm_bad_status_{self.suffix}", "Bad Status Admin", "locked"]],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["errors"][0]["field"], "status")

    def test_task_type_management(self):
        self.login_admin()
        type_code = f"week2_{self.suffix}"

        response = self.client.post(
            "/api/v1/admin/task-types",
            json={
                "type_code": type_code,
                "type_name": "Week2 Regression",
                "sort_order": 99,
                "allow_student_self": False,
                "allow_admin_task": True,
                "allow_teacher_task": False,
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        item = response.json["data"]
        self.assertEqual(item["type_code"], type_code)
        self.assertFalse(item["allow_student_self"])
        task_type_id = item["id"]

        response = self.client.patch(
            f"/api/v1/admin/task-types/{task_type_id}",
            json={"type_name": "Week2 Regression Updated", "allow_teacher_task": True},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["type_name"], "Week2 Regression Updated")
        self.assertTrue(response.json["data"]["allow_teacher_task"])

        response = self.client.post(f"/api/v1/admin/task-types/{task_type_id}/disable")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["status"], "disabled")

        response = self.client.post(f"/api/v1/admin/task-types/{task_type_id}/enable")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["status"], "enabled")

        response = self.client.get("/api/v1/task-types?enabled=true")
        self.assertEqual(response.status_code, 200)
        codes = {item["type_code"] for item in response.json["data"]["items"]}
        self.assertIn(type_code, codes)


if __name__ == "__main__":
    unittest.main()
