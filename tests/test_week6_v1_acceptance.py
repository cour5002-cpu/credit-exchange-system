import unittest
from datetime import datetime
from io import BytesIO

from app.commands.seed_data import seed_default_users, seed_system_configs, seed_task_types
from app.extensions import db
from tests.test_support import create_isolated_test_app


class Week6V1AcceptanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_isolated_test_app()
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

    def test_submitted_attachment_can_only_be_voided_by_admin_with_reason(self):
        student = self.login("student1", "student123")
        advisor = self.login("teacher1", "teacher123")
        admin = self.login("admin", "admin123")
        advisor_id = advisor.get("/api/v1/me").json["data"]["teacher"]["id"]
        task_type_id = student.get("/api/v1/task-types?enabled=true").json["data"]["items"][0]["id"]

        upload = student.post("/api/v1/attachments", data={
            "biz_type": "hour_application",
            "file": (BytesIO(b"submitted material"), "submitted-material.txt"),
        }, content_type="multipart/form-data")
        self.assertEqual(upload.status_code, 200, upload.get_data(as_text=True))
        attachment_id = upload.json["data"]["id"]

        submit = student.post("/api/v1/student/hour-applications", json={
            "application_type": "with_material",
            "task_type_id": task_type_id,
            "title": f"附件作废验收-{datetime.now().isoformat()}",
            "requested_hours": 4,
            "advisor_teacher_id": advisor_id,
            "attachment_ids": [attachment_id],
        })
        self.assertEqual(submit.status_code, 200, submit.get_data(as_text=True))

        response = student.delete(f"/api/v1/attachments/{attachment_id}")
        self.assertEqual(response.status_code, 409, response.get_data(as_text=True))
        response = admin.delete(f"/api/v1/attachments/{attachment_id}", json={})
        self.assertEqual(response.status_code, 400, response.get_data(as_text=True))
        response = admin.delete(
            f"/api/v1/attachments/{attachment_id}",
            json={"reason": "验收：材料内容无效"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "voided")
        self.assertEqual(student.get(f"/api/v1/attachments/{attachment_id}").status_code, 404)

        response = admin.get(f"/api/v1/admin/attachments/{attachment_id}/operation-records")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["attachment"]["status"], "voided")
        self.assertEqual(response.json["data"]["items"][0]["action"], "void")
        self.assertEqual(response.json["data"]["items"][0]["detail"], "验收：材料内容无效")
        self.assertEqual(response.json["data"]["page"], 1)
        self.assertEqual(response.json["data"]["page_size"], 20)
        self.assertEqual(response.json["data"]["total"], 1)

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
        self.assertEqual(response.json["data"]["page"], 1)
        self.assertEqual(response.json["data"]["page_size"], 20)
        self.assertIn("total", response.json["data"])
        self.assertIn("pages", response.json["data"])
        self.assertEqual(admin.get("/api/v1/operation-records?role_scope=advisor").status_code, 403)
        self.assertEqual(admin.get("/api/v1/operation-records?role_scope=admin&page_size=101").status_code, 400)


if __name__ == "__main__":
    unittest.main()
