import unittest
from datetime import datetime, timedelta
from io import BytesIO

from app.commands.seed_data import seed_default_users, seed_system_configs, seed_task_types
from app.extensions import db
from tests.test_support import create_isolated_test_app
from app.models.credit_conversion_rule import CreditConversionRule
from app.models.hour_application_member import HourApplicationMember
from app.models.hour_award_record import HourAwardRecord
from app.models.student import Student
from app.models.user import User


class Week4CreditExchangeApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_isolated_test_app()
        cls.app.config["WTF_CSRF_ENABLED"] = False
        with cls.app.app_context():
            seed_task_types()
            seed_system_configs()
            seed_default_users()
            CreditConversionRule.query.update({"status": "inactive"})
            db.session.commit()

    def client_login(self, username, password):
        client = self.app.test_client()
        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return client, response.json["data"]

    def create_hour_award(self):
        student_client, _ = self.client_login("student1", "student123")
        advisor_client, advisor_me = self.client_login("teacher1", "teacher123")
        admin_client, _ = self.client_login("admin", "admin123")
        reviewer_client, reviewer_me = self.client_login("teacher2", "teacher123")

        task_type_id = student_client.get("/api/v1/task-types?enabled=true").json["data"]["items"][0]["id"]
        upload = student_client.post(
            "/api/v1/attachments",
            data={
                "biz_type": "hour_application",
                "file": (BytesIO(b"week4 hour material"), "week4-hour-material.txt"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(upload.status_code, 200, upload.get_data(as_text=True))
        response = student_client.post(
            "/api/v1/student/hour-applications",
            json={
                "application_type": "with_material",
                "task_type_id": task_type_id,
                "title": "第4周兑换前置课时到账",
                "requested_hours": 10,
                "advisor_teacher_id": advisor_me["teacher"]["id"],
                "attachment_ids": [upload.json["data"]["id"]],
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        application_id = response.json["data"]["id"]

        response = advisor_client.post(f"/api/v1/advisor/hour-applications/{application_id}/approve", json={"comment": "确认"})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))

        response = admin_client.post(
            f"/api/v1/admin/hour-applications/{application_id}/assign-reviewer",
            json={"reviewer_teacher_id": reviewer_me["teacher"]["id"], "comment": "分配"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))

        response = reviewer_client.post(
            f"/api/v1/reviewer/hour-applications/{application_id}/approve",
            json={"comment": "同意"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))

        response = admin_client.post(
            f"/api/v1/admin/hour-applications/{application_id}/final-approve",
            json={"comment": "最终确认"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return response.json["data"]["hour_award_record_id"], student_client, advisor_client, admin_client

    def create_conversion_rule(self, admin_client):
        upload = admin_client.post(
            "/api/v1/attachments",
            data={
                "biz_type": "rule_file",
                "file": (BytesIO(b"10 hours = 1 credit"), "week4-credit-rule.txt"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(upload.status_code, 200, upload.get_data(as_text=True))
        response = admin_client.post(
            "/api/v1/admin/rule-files",
            json={
                "title": "第4周测试兑换规则文件",
                "rule_type": "credit_rule",
                "usage_type": "calculation_basis",
                "attachment_id": upload.json["data"]["id"],
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        rule_file_id = response.json["data"]["id"]

        response = admin_client.post(
            "/api/v1/admin/credit-conversion-rules",
            json={
                "rule_name": "第4周测试结构化规则",
                "hours_per_credit": 10,
                "max_single_exchange_hours": 100,
                "rounding_mode": "keep_2",
                "effective_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
                "rule_file_id": rule_file_id,
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return response.json["data"]["rule"]["id"]

    def test_credit_exchange_mainline(self):
        hour_award_record_id, student_client, advisor_client, admin_client = self.create_hour_award()

        response = student_client.get(
            f"/api/v1/student/credit-exchanges/form-data?hour_award_record_id={hour_award_record_id}"
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertFalse(response.json["data"]["can_submit"])
        self.assertEqual(len(response.json["data"]["members"]), 1)
        self.assertTrue(response.json["data"]["members"][0]["is_leader"])

        student_id = student_client.get("/api/v1/me").json["data"]["student"]["id"]
        response = student_client.post(
            "/api/v1/student/credit-exchanges/drafts",
            json={
                "hour_award_record_id": hour_award_record_id,
                "allocations": [{"student_id": student_id, "hours": 10}],
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "draft")
        self.assertNotIn("calculated_allocations", response.json["data"])

        self.create_conversion_rule(admin_client)

        response = student_client.get("/api/v1/student/credit-exchanges/available-hour-awards")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertIn(hour_award_record_id, [item["id"] for item in response.json["data"]["items"]])

        upload = student_client.post(
            "/api/v1/attachments",
            data={
                "biz_type": "credit_exchange",
                "file": (BytesIO(b"allocation proof"), "allocation-proof.txt"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(upload.status_code, 200, upload.get_data(as_text=True))

        response = student_client.post(
            "/api/v1/student/credit-exchanges",
            json={
                "hour_award_record_id": hour_award_record_id,
                "attachment_ids": [upload.json["data"]["id"]],
                "confirm_calculated_credits": True,
            },
        )
        self.assertEqual(response.status_code, 400)

        response = student_client.post(
            "/api/v1/student/credit-exchanges",
            json={
                "hour_award_record_id": hour_award_record_id,
                "attachment_ids": [upload.json["data"]["id"]],
                "allocations": [{"student_id": student_id, "hours": 10}],
                "confirm_calculated_credits": True,
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        exchange_id = response.json["data"]["id"]
        self.assertEqual(response.json["data"]["status"], "submitted")
        self.assertEqual(response.json["data"]["calculated_allocations"][0]["allocated_credits"], 1.0)

        response = advisor_client.get("/api/v1/advisor/credit-exchanges/pending")
        self.assertEqual(response.status_code, 200)
        self.assertIn(exchange_id, [item["id"] for item in response.json["data"]["items"]])

        response = advisor_client.post(
            f"/api/v1/advisor/credit-exchanges/{exchange_id}/approve",
            json={"comment": "兑换分配确认"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "pending_admin_final")

        response = admin_client.post("/api/v1/admin/credit-exchanges/batch-approve", json={
            "exchange_ids": [exchange_id, 999999999],
            "comment": "批量最终确认兑换",
        })
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["success_count"], 1)
        self.assertEqual(response.json["data"]["failed_count"], 1)
        self.assertTrue(response.json["data"]["items"][0]["success"])
        self.assertFalse(response.json["data"]["items"][1]["success"])
        self.assertIsInstance(response.json["data"]["items"][0]["credit_exchange_record_id"], int)

        response = admin_client.post(
            f"/api/v1/admin/credit-exchanges/{exchange_id}/final-approve",
            json={"comment": "重复确认"},
        )
        self.assertEqual(response.status_code, 409)

        response = student_client.get("/api/v1/student/credit-exchanges/available-hour-awards")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(hour_award_record_id, [item["id"] for item in response.json["data"]["items"]])

    def test_exchange_form_returns_all_members_even_without_active_rule(self):
        hour_award_record_id, student_client, _, _ = self.create_hour_award()
        with self.app.app_context():
            CreditConversionRule.query.update({"status": "inactive"})
            teammate_user = User(
                username="exchange_teammate",
                role="student",
                real_name="兑换队员",
                status="active",
            )
            teammate_user.set_password("student123")
            db.session.add(teammate_user)
            db.session.flush()
            teammate = Student(
                user_id=teammate_user.id,
                student_no="20269999",
                name="兑换队员",
                college="示例学院",
                major="软件工程",
                grade="2026",
                class_name="1班",
                status="active",
            )
            db.session.add(teammate)
            db.session.flush()
            award = db.session.get(HourAwardRecord, hour_award_record_id)
            db.session.add(HourApplicationMember(
                application_id=award.application_id,
                student_id=teammate.id,
                is_leader=False,
                can_view=True,
                can_apply_credit_exchange=False,
            ))
            db.session.commit()
            teammate_id = teammate.id

        response = student_client.get(
            f"/api/v1/student/credit-exchanges/form-data?hour_award_record_id={hour_award_record_id}"
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertFalse(response.json["data"]["can_submit"])
        returned_ids = {
            item["student"]["id"]
            for item in response.json["data"]["members"]
        }
        self.assertEqual(len(returned_ids), 2)
        self.assertIn(teammate_id, returned_ids)


if __name__ == "__main__":
    unittest.main()
