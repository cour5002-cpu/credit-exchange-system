import unittest
from datetime import datetime, timedelta
from io import BytesIO

from app.commands.seed_data import seed_default_users, seed_system_configs, seed_task_types
from app.extensions import db
from app.models.attachment import Attachment
from app.models.extension_request import ExtensionRequest
from tests.test_support import create_isolated_test_app


class Week3HourApplicationApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_isolated_test_app()
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

    def create_pending_material_application(self, title):
        student_client, _ = self.client_login("student1", "student123")
        advisor_client, advisor_me = self.client_login("teacher1", "teacher123")
        task_type_id = student_client.get("/api/v1/task-types?enabled=true").json["data"]["items"][0]["id"]
        due_at = datetime.now() + timedelta(days=7)
        response = student_client.post(
            "/api/v1/student/hour-applications",
            json={
                "application_type": "without_material",
                "task_type_id": task_type_id,
                "title": title,
                "requested_hours": 8,
                "material_due_at": due_at.isoformat(),
                "advisor_teacher_id": advisor_me["teacher"]["id"],
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        application_id = response.json["data"]["id"]
        response = advisor_client.post(
            f"/api/v1/advisor/hour-applications/{application_id}/approve",
            json={"comment": "同意进入成果补交阶段"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "pending_material")
        return student_client, advisor_client, application_id, due_at

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

        detail = student_client.get(f"/api/v1/student/hour-applications/{application_id}")
        self.assertEqual(detail.status_code, 200, detail.get_data(as_text=True))
        self.assertIsNotNone(detail.json["data"]["advisor_reviewed_at"])
        self.assertIsNotNone(detail.json["data"]["assigned_at"])
        self.assertIsNotNone(detail.json["data"]["reviewer_reviewed_at"])
        self.assertIsNotNone(detail.json["data"]["final_reviewed_at"])
        self.assertTrue(all(
            step["completed"]
            for step in detail.json["data"]["workflow_progress"].values()
        ))

        response = admin_client.post(
            f"/api/v1/admin/hour-applications/{application_id}/final-approve",
            json={"comment": "重复确认"},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json["code"], 40901)

        response = admin_client.post(
            f"/api/v1/admin/hour-applications/{application_id}/close",
            json={"reason": "已到账申请不允许关闭"},
        )
        self.assertEqual(response.status_code, 409)

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

    def test_save_hour_application_draft(self):
        student_client, _ = self.client_login("student1", "student123")
        _, advisor_me = self.client_login("teacher1", "teacher123")
        task_type_id = student_client.get("/api/v1/task-types?enabled=true").json["data"]["items"][0]["id"]

        response = student_client.post(
            "/api/v1/student/hour-applications/drafts",
            json={
                "application_type": "with_material",
                "task_type_id": task_type_id,
                "title": "第3周课时申请草稿",
                "requested_hours": 4,
                "advisor_teacher_id": advisor_me["teacher"]["id"],
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "draft")

    def test_normal_extension_is_reviewed_by_primary_advisor_once(self):
        student_client, advisor_client, application_id, due_at = self.create_pending_material_application("第3周普通延期回归")
        admin_client, _ = self.client_login("admin", "admin123")
        requested_due_at = due_at + timedelta(days=30)

        response = student_client.post(
            f"/api/v1/student/hour-applications/{application_id}/extension-requests",
            json={"requested_due_at": requested_due_at.isoformat(), "reason": "项目设备延期到货"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "pending_advisor_review")
        self.assertEqual(response.json["data"]["application_status"], "extension_requested")
        self.assertEqual(response.json["data"]["extension_days"], 30)
        self.assertEqual(response.json["data"]["review_level"], "advisor")
        extension_id = response.json["data"]["extension_request_id"]
        with self.app.app_context():
            extension = db.session.get(ExtensionRequest, extension_id)
            self.assertEqual(extension.extension_days, 30)
            self.assertEqual(extension.review_level, "advisor")
            self.assertEqual(extension.status, "pending_advisor_review")

        response = admin_client.post(
            f"/api/v1/admin/extension-requests/{extension_id}/approve",
            json={"comment": "管理员不能审批普通延期"},
        )
        self.assertEqual(response.status_code, 403)

        response = advisor_client.get("/api/v1/advisor/extension-requests/pending")
        self.assertIn(extension_id, [item["id"] for item in response.json["data"]["items"]])
        response = advisor_client.post(
            f"/api/v1/advisor/extension-requests/{extension_id}/approve",
            json={"comment": "同意普通延期"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "extension_approved")

        response = student_client.post(
            f"/api/v1/student/hour-applications/{application_id}/extension-requests",
            json={"requested_due_at": (requested_due_at + timedelta(days=1)).isoformat(), "reason": "再次延期"},
        )
        self.assertEqual(response.status_code, 409)

        second_student_client, second_advisor_client, second_application_id, second_due_at = self.create_pending_material_application(
            "第3周普通延期驳回回归"
        )
        response = second_student_client.post(
            f"/api/v1/student/hour-applications/{second_application_id}/extension-requests",
            json={"requested_due_at": (second_due_at + timedelta(days=30)).isoformat(), "reason": "普通延期驳回验证"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        second_extension_id = response.json["data"]["extension_request_id"]
        response = second_advisor_client.post(
            f"/api/v1/advisor/extension-requests/{second_extension_id}/reject",
            json={"comment": "延期理由不充分"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "extension_rejected")

    def test_special_extension_can_be_closed_by_admin(self):
        student_client, _, application_id, due_at = self.create_pending_material_application("第3周特殊延期关闭回归")
        admin_client, _ = self.client_login("admin", "admin123")
        upload = student_client.post("/api/v1/attachments", data={
            "biz_type": "extension_request",
            "file": (BytesIO(b"extension proof"), "extension-proof.txt"),
        }, content_type="multipart/form-data")
        self.assertEqual(upload.status_code, 200, upload.get_data(as_text=True))
        attachment_id = upload.json["data"]["id"]
        response = student_client.post(
            f"/api/v1/student/hour-applications/{application_id}/extension-requests",
            json={
                "requested_due_at": (due_at + timedelta(days=31)).isoformat(),
                "reason": "延期跨度超过30天",
                "attachment_ids": [attachment_id],
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "pending_admin_review")
        self.assertEqual(response.json["data"]["application_status"], "extension_admin_review")
        self.assertEqual(response.json["data"]["extension_days"], 31)
        self.assertEqual(response.json["data"]["review_level"], "admin")
        extension_id = response.json["data"]["extension_request_id"]

        response = admin_client.get("/api/v1/admin/extension-requests/pending-special")
        special_item = next(
            item for item in response.json["data"]["items"]
            if item["id"] == extension_id
        )
        self.assertEqual(special_item["extension_days"], 31)
        self.assertEqual(special_item["review_level"], "admin")
        self.assertEqual(special_item["status"], "pending_admin_review")

        detail = admin_client.get(f"/api/v1/admin/extension-requests/{extension_id}")
        self.assertEqual(detail.status_code, 200, detail.get_data(as_text=True))
        self.assertEqual(detail.json["data"]["extension_request_id"], extension_id)
        self.assertEqual(detail.json["data"]["hour_application_id"], application_id)
        self.assertEqual(detail.json["data"]["extension_days"], 31)
        self.assertEqual(detail.json["data"]["review_level"], "admin")
        self.assertEqual(detail.json["data"]["status"], "pending_admin_review")
        self.assertEqual(detail.json["data"]["reason"], "延期跨度超过30天")
        self.assertEqual(
            set(detail.json["data"]["student"]),
            {"id", "student_no", "name"},
        )
        self.assertEqual(detail.json["data"]["attachments"], [{
            "id": attachment_id,
            "filename": "extension-proof.txt",
            "url": f"/api/v1/attachments/{attachment_id}",
        }])
        with self.app.app_context():
            attachment = db.session.get(Attachment, attachment_id)
            self.assertEqual(attachment.owner_type, "extension_request")
            self.assertEqual(attachment.owner_id, extension_id)
        download = admin_client.get(f"/api/v1/attachments/{attachment_id}?download=true")
        self.assertEqual(download.status_code, 200, download.get_data(as_text=True))
        download.close()
        response = admin_client.post(
            f"/api/v1/admin/hour-applications/{application_id}/close",
            json={},
        )
        self.assertEqual(response.status_code, 400)
        response = admin_client.post(
            f"/api/v1/admin/hour-applications/{application_id}/close",
            json={"reason": "学生临近毕业，流程已无法继续"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "closed")

        response = admin_client.post(
            f"/api/v1/admin/extension-requests/{extension_id}/approve",
            json={"comment": "关闭后不能再审批"},
        )
        self.assertEqual(response.status_code, 409)

    def test_special_extension_admin_approve_and_reject(self):
        admin_client, _ = self.client_login("admin", "admin123")

        for decision in ("approve", "reject"):
            student_client, _, application_id, due_at = self.create_pending_material_application(
                f"第3周特殊延期管理员{decision}回归"
            )
            response = student_client.post(
                f"/api/v1/student/hour-applications/{application_id}/extension-requests",
                json={"requested_due_at": (due_at + timedelta(days=200)).isoformat(), "reason": "延期跨度超过一个学期"},
            )
            self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
            extension_id = response.json["data"]["extension_request_id"]

            response = admin_client.get(f"/api/v1/extension-requests/{extension_id}")
            self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
            self.assertEqual(response.json["data"]["extension_request"]["review_level"], "admin")

            response = admin_client.post(
                f"/api/v1/admin/extension-requests/{extension_id}/{decision}",
                json={"comment": "管理员处理特殊延期"},
            )
            self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
            expected_status = "extension_approved" if decision == "approve" else "extension_rejected"
            self.assertEqual(response.json["data"]["status"], expected_status)


if __name__ == "__main__":
    unittest.main()
