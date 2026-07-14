import unittest
from datetime import datetime, timedelta
from io import BytesIO

from app import create_app
from app.commands.seed_data import seed_default_users, seed_system_configs, seed_task_types
from app.extensions import db


class Week3HourApplicationApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app("default")
        cls.app.config["WTF_CSRF_ENABLED"] = False
        with cls.app.app_context():
            seed_task_types()
            seed_system_configs()
            seed_default_users()
            db.session.commit()

    def client_login(self, username, password):
        client = self.app.test_client()
        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return client, response.json["data"]

    def test_without_material_application_mainline(self):
        student_client, _ = self.client_login("student1", "student123")
        advisor_client, advisor_me = self.client_login("teacher1", "teacher123")
        admin_client, _ = self.client_login("admin", "admin123")
        reviewer_client, reviewer_me = self.client_login("teacher2", "teacher123")

        task_types = student_client.get("/api/v1/task-types?enabled=true").json["data"]["items"]
        task_type_id = task_types[0]["id"]
        material_due_at = (datetime.now() + timedelta(days=7)).isoformat()

        response = student_client.post(
            "/api/v1/student/hour-applications",
            json={
                "application_type": "without_material",
                "task_type_id": task_type_id,
                "title": "第3周无成果主线回归",
                "requested_hours": 8,
                "material_due_at": material_due_at,
                "advisor_teacher_id": advisor_me["teacher"]["id"],
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        application_id = response.json["data"]["id"]
        self.assertEqual(response.json["data"]["status"], "submitted")

        response = advisor_client.get("/api/v1/advisor/hour-applications/pending")
        self.assertEqual(response.status_code, 200)
        self.assertIn(application_id, [item["id"] for item in response.json["data"]["items"]])

        response = advisor_client.post(
            f"/api/v1/advisor/hour-applications/{application_id}/approve",
            json={"comment": "同意先立项，后续补交成果"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "pending_material")

        response = student_client.post(
            f"/api/v1/student/hour-applications/{application_id}/materials",
            json={"achievement_summary": "已完成成果并补交说明。"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "material_submitted")

        response = advisor_client.post(
            f"/api/v1/advisor/hour-applications/{application_id}/materials/approve",
            json={"comment": "成果材料确认通过"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "pending_assignment")

        response = admin_client.post(
            f"/api/v1/admin/hour-applications/{application_id}/assign-reviewer",
            json={"reviewer_teacher_id": reviewer_me["teacher"]["id"], "comment": "分配审核"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "pending_review")

        response = reviewer_client.get("/api/v1/reviewer/hour-applications/pending")
        self.assertEqual(response.status_code, 200)
        self.assertIn(application_id, [item["id"] for item in response.json["data"]["items"]])

        response = reviewer_client.post(
            f"/api/v1/reviewer/hour-applications/{application_id}/modified-approve",
            json={"reviewer_suggested_hours": 6, "comment": "按材料认定 6 课时"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "pending_admin_final")
        self.assertEqual(response.json["data"]["review_result"], "reviewer_modified_approved")

        response = admin_client.post(
            f"/api/v1/admin/hour-applications/{application_id}/final-approve",
            json={"comment": "最终确认"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "final_approved")
        self.assertIsInstance(response.json["data"]["hour_award_record_id"], int)

        response = admin_client.post(
            f"/api/v1/admin/hour-applications/{application_id}/final-approve",
            json={"comment": "重复确认"},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json["code"], 40901)

    def test_with_material_application_requires_uploaded_attachment(self):
        student_client, _ = self.client_login("student1", "student123")
        advisor_client, advisor_me = self.client_login("teacher1", "teacher123")

        task_types = student_client.get("/api/v1/task-types?enabled=true").json["data"]["items"]
        task_type_id = task_types[0]["id"]

        response = student_client.post(
            "/api/v1/student/hour-applications",
            json={
                "application_type": "with_material",
                "task_type_id": task_type_id,
                "title": "第3周有成果主线回归",
                "requested_hours": 4,
                "advisor_teacher_id": advisor_me["teacher"]["id"],
            },
        )
        self.assertEqual(response.status_code, 400)

        upload = student_client.post(
            "/api/v1/attachments",
            data={
                "biz_type": "hour_application",
                "file": (BytesIO(b"week3 material"), "week3-material.txt"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(upload.status_code, 200, upload.get_data(as_text=True))
        attachment_id = upload.json["data"]["id"]

        response = student_client.post(
            "/api/v1/student/hour-applications",
            json={
                "application_type": "with_material",
                "task_type_id": task_type_id,
                "title": "第3周有成果主线回归",
                "requested_hours": 4,
                "advisor_teacher_id": advisor_me["teacher"]["id"],
                "attachment_ids": [attachment_id],
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        application_id = response.json["data"]["id"]

        detail = student_client.get(f"/api/v1/student/hour-applications/{application_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json["data"]["attachments"][0]["id"], attachment_id)

        response = advisor_client.post(
            f"/api/v1/advisor/hour-applications/{application_id}/approve",
            json={"comment": "有成果申请确认通过"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "pending_assignment")


if __name__ == "__main__":
    unittest.main()
