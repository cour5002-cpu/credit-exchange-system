import unittest
from io import BytesIO

from app import create_app
from app.commands.seed_data import seed_default_users, seed_system_configs, seed_task_types
from app.extensions import db


class Week6V1AcceptanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app("default")
        cls.app.config["WTF_CSRF_ENABLED"] = False
        with cls.app.app_context():
            db.create_all()
            seed_task_types()
            seed_system_configs()
            seed_default_users()
            db.session.commit()

    def login(self, username, password):
        client = self.app.test_client()
        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200)
        return client

    def test_attachment_type_soft_delete_and_visibility(self):
        student = self.login("student1", "student123")
        response = student.post("/api/v1/attachments", data={
            "biz_type": "hour_application",
            "file": (BytesIO(b"invalid"), "malware.exe"),
        }, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 400)

        response = student.post("/api/v1/attachments", data={
            "biz_type": "hour_application",
            "file": (BytesIO(b"valid"), "material.txt"),
        }, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        attachment_id = response.json["data"]["id"]
        response = student.delete(f"/api/v1/attachments/{attachment_id}")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "deleted")
        self.assertEqual(student.get(f"/api/v1/attachments/{attachment_id}").status_code, 404)

    def test_export_and_role_boundaries(self):
        anonymous = self.app.test_client()
        self.assertEqual(anonymous.get("/api/v1/admin/exports/hour-applications").status_code, 401)
        student = self.login("student1", "student123")
        self.assertEqual(student.get("/api/v1/admin/exports/hour-applications").status_code, 403)
        self.assertEqual(student.get("/api/v1/admin/complaints").status_code, 403)
        self.assertEqual(student.get("/api/v1/operation-records?role_scope=admin").status_code, 403)

        admin = self.login("admin", "admin123")
        response = admin.get("/api/v1/admin/exports/hour-applications")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.mimetype,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertGreater(len(response.data), 100)
        response = admin.get("/api/v1/operation-records?role_scope=admin")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertIn("items", response.json["data"])
        self.assertEqual(admin.get("/api/v1/operation-records?role_scope=advisor").status_code, 403)


if __name__ == "__main__":
    unittest.main()
