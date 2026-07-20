import unittest
from datetime import datetime, timedelta
from io import BytesIO

from app import create_app
from app.commands.seed_data import seed_default_users, seed_system_configs, seed_task_types
from app.extensions import db


class Week5AppealTaskApiTest(unittest.TestCase):
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

    def client_login(self, username, password):
        client = self.app.test_client()
        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return client, response.json["data"]

    def create_final_rejected_hour_application(self):
        student_client, _ = self.client_login("student1", "student123")
        advisor_client, advisor_me = self.client_login("teacher1", "teacher123")
        admin_client, _ = self.client_login("admin", "admin123")
        reviewer_client, reviewer_me = self.client_login("teacher2", "teacher123")
        task_type_id = student_client.get("/api/v1/task-types?enabled=true").json["data"]["items"][0]["id"]

        upload = student_client.post(
            "/api/v1/attachments",
            data={
                "biz_type": "hour_application",
                "file": (BytesIO(b"week5 appeal material"), "week5-appeal-material.txt"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(upload.status_code, 200, upload.get_data(as_text=True))
        response = student_client.post(
            "/api/v1/student/hour-applications",
            json={
                "application_type": "with_material",
                "task_type_id": task_type_id,
                "title": "第5周申诉前置课时申请",
                "requested_hours": 8,
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
        response = reviewer_client.post(f"/api/v1/reviewer/hour-applications/{application_id}/approve", json={"comment": "同意"})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        response = admin_client.post(
            f"/api/v1/admin/hour-applications/{application_id}/final-reject",
            json={"comment": "终审驳回，用于申诉测试"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "final_rejected")
        return application_id, student_client, admin_client

    def create_reference_rule_file(self, admin_client):
        upload = admin_client.post(
            "/api/v1/attachments",
            data={
                "biz_type": "rule_file",
                "file": (BytesIO(b"appeal standard"), "week5-appeal-standard.txt"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(upload.status_code, 200, upload.get_data(as_text=True))
        response = admin_client.post(
            "/api/v1/admin/rule-files",
            json={
                "title": "第5周申诉审核标准",
                "rule_type": "hour_rule",
                "usage_type": "reference_only",
                "attachment_id": upload.json["data"]["id"],
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return response.json["data"]["id"]

    def test_appeal_mainline(self):
        application_id, student_client, admin_client = self.create_final_rejected_hour_application()
        rule_file_id = self.create_reference_rule_file(admin_client)

        upload = student_client.post(
            "/api/v1/attachments",
            data={
                "biz_type": "appeal",
                "file": (BytesIO(b"appeal proof"), "week5-appeal-proof.txt"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(upload.status_code, 200, upload.get_data(as_text=True))
        response = student_client.post(
            "/api/v1/student/appeals",
            json={
                "target_type": "hour_application",
                "target_id": application_id,
                "reason": "补充说明终审驳回存在异议",
                "standard_rule_file_id": rule_file_id,
                "attachment_ids": [upload.json["data"]["id"]],
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        appeal_id = response.json["data"]["id"]
        self.assertEqual(response.json["data"]["status"], "pending_admin_review")

        response = student_client.post(
            "/api/v1/student/appeals",
            json={"target_type": "hour_application", "target_id": application_id, "reason": "重复申诉"},
        )
        self.assertEqual(response.status_code, 409)

        response = admin_client.get("/api/v1/admin/appeals?status=pending_admin_review")
        self.assertEqual(response.status_code, 200)
        self.assertIn(appeal_id, [item["id"] for item in response.json["data"]["items"]])

        response = admin_client.post(
            f"/api/v1/admin/appeals/{appeal_id}/approve",
            json={"admin_advice": "申诉理由成立，退回指导老师重新确认"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "appeal_accepted")
        self.assertEqual(response.json["data"]["target_status"], "submitted")

    def test_college_task_registration_and_selection(self):
        admin_client, _ = self.client_login("admin", "admin123")
        student_client, _ = self.client_login("student1", "student123")
        advisor_client, advisor_me = self.client_login("teacher1", "teacher123")
        task_type_id = admin_client.get("/api/v1/task-types?enabled=true").json["data"]["items"][0]["id"]

        response = admin_client.post(
            "/api/v1/admin/tasks",
            json={
                "title": "第5周学院发布测试任务",
                "description": "用于验证学生报名和指导老师筛选",
                "task_type_id": task_type_id,
                "advisor_teacher_id": advisor_me["teacher"]["id"],
                "result_requirement": "提交成果说明和证明材料",
                "registration_deadline": (datetime.now() + timedelta(days=7)).isoformat(),
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        task_id = response.json["data"]["id"]
        self.assertEqual(response.json["data"]["status"], "published")

        response = student_client.get("/api/v1/student/tasks")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertIn(task_id, [item["id"] for item in response.json["data"]["items"]])

        response = student_client.post(
            f"/api/v1/student/tasks/{task_id}/registrations",
            json={"remark": "申请参加学院任务"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        registration_id = response.json["data"]["registration_id"]
        self.assertEqual(response.json["data"]["status"], "submitted")

        response = student_client.post(
            f"/api/v1/student/tasks/{task_id}/registrations",
            json={"remark": "重复报名"},
        )
        self.assertEqual(response.status_code, 409)

        response = advisor_client.get(f"/api/v1/advisor/tasks/{task_id}/registrations")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertIn(registration_id, [item["id"] for item in response.json["data"]["items"]])

        response = advisor_client.post(
            f"/api/v1/advisor/tasks/{task_id}/registrations/select",
            json={"selected_registration_ids": [registration_id]},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["task"]["status"], "task_in_progress")
        self.assertEqual(response.json["data"]["members"][0]["registration_id"], registration_id)
        self.assertTrue(response.json["data"]["members"][0]["is_leader"])

        response = admin_client.get(f"/api/v1/admin/tasks/{task_id}")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["registrations"][0]["status"], "selected")

    def test_task_result_to_hour_award_mainline(self):
        admin_client, _ = self.client_login("admin", "admin123")
        student_client, student_me = self.client_login("student1", "student123")
        advisor_client, advisor_me = self.client_login("teacher1", "teacher123")
        reviewer_client, reviewer_me = self.client_login("teacher2", "teacher123")
        task_type_id = admin_client.get("/api/v1/task-types?enabled=true").json["data"]["items"][0]["id"]

        response = admin_client.post("/api/v1/admin/tasks", json={
            "title": "第5周任务成果闭环",
            "description": "验证任务成果转课时认定",
            "task_type_id": task_type_id,
            "advisor_teacher_id": advisor_me["teacher"]["id"],
            "result_requirement": "提交完整成果材料",
            "registration_deadline": (datetime.now() + timedelta(days=7)).isoformat(),
        })
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        task_id = response.json["data"]["id"]
        registration = student_client.post(f"/api/v1/student/tasks/{task_id}/registrations", json={"remark": "报名"})
        registration_id = registration.json["data"]["registration_id"]
        response = advisor_client.post(f"/api/v1/advisor/tasks/{task_id}/registrations/select", json={
            "selected_registration_ids": [registration_id]
        })
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))

        team = student_client.get(f"/api/v1/student/tasks/{task_id}/team")
        self.assertEqual(team.status_code, 200, team.get_data(as_text=True))
        self.assertEqual(team.json["data"]["leader_student_id"], student_me["student"]["id"])
        self.assertTrue(team.json["data"]["can_submit_result"])

        upload = student_client.post("/api/v1/attachments", data={
            "biz_type": "task_result",
            "file": (BytesIO(b"task result proof"), "task-result.txt"),
        }, content_type="multipart/form-data")
        response = student_client.post(f"/api/v1/student/tasks/{task_id}/result-submissions", json={
            "summary": "任务成果已完成",
            "requested_hours": 12,
            "attachment_ids": [upload.json["data"]["id"]],
        })
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        submission_id = response.json["data"]["submission_id"]
        application_id = response.json["data"]["hour_application_id"]
        self.assertEqual(response.json["data"]["status"], "material_submitted")

        response = advisor_client.post(f"/api/v1/advisor/task-result-submissions/{submission_id}/approve", json={"comment": "成果确认"})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "pending_assignment")
        response = admin_client.post(f"/api/v1/admin/hour-applications/{application_id}/assign-reviewer", json={
            "reviewer_teacher_id": reviewer_me["teacher"]["id"]
        })
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        response = reviewer_client.post(f"/api/v1/reviewer/hour-applications/{application_id}/approve", json={"comment": "复核通过"})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        response = admin_client.post(f"/api/v1/admin/hour-applications/{application_id}/final-approve", json={"comment": "最终确认"})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "final_approved")

    def test_appeal_complete_re_review_mainline(self):
        application_id, student_client, admin_client = self.create_final_rejected_hour_application()
        advisor_client, _ = self.client_login("teacher1", "teacher123")
        reviewer_client, reviewer_me = self.client_login("teacher2", "teacher123")
        upload = student_client.post("/api/v1/attachments", data={
            "biz_type": "appeal",
            "file": (BytesIO(b"appeal full proof"), "appeal-full.txt"),
        }, content_type="multipart/form-data")
        response = student_client.post("/api/v1/student/appeals", json={
            "target_type": "hour_application",
            "target_id": application_id,
            "reason": "申请重新审核",
            "attachment_ids": [upload.json["data"]["id"]],
        })
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        appeal_id = response.json["data"]["id"]
        response = admin_client.post(f"/api/v1/admin/appeals/{appeal_id}/approve", json={"admin_advice": "同意重审"})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        response = advisor_client.post(f"/api/v1/advisor/appeals/{appeal_id}/reconfirm", json={"decision": "approve", "comment": "再次确认"})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["target_status"], "pending_assignment")
        response = admin_client.post(f"/api/v1/admin/appeals/{appeal_id}/assign-reviewer", json={
            "reviewer_teacher_id": reviewer_me["teacher"]["id"], "comment": "重新分配"
        })
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        response = reviewer_client.post(f"/api/v1/reviewer/appeal-reviews/{appeal_id}/approve", json={"comment": "申诉复审通过"})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["target_status"], "pending_admin_final")
        response = admin_client.post(f"/api/v1/admin/hour-applications/{application_id}/final-approve", json={"comment": "申诉后终审通过"})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "final_approved")

    def test_anonymous_complaint_submit_and_admin_view(self):
        student_client, _ = self.client_login("student1", "student123")
        admin_client, _ = self.client_login("admin", "admin123")
        upload = student_client.post("/api/v1/attachments", data={
            "biz_type": "complaint",
            "file": (BytesIO(b"complaint proof"), "complaint.txt"),
        }, content_type="multipart/form-data")
        response = student_client.post("/api/v1/student/complaints", json={
            "content": "匿名投诉测试内容",
            "attachment_ids": [upload.json["data"]["id"]],
        })
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        complaint_id = response.json["data"]["id"]
        self.assertNotIn("submitter_user_id", response.json["data"])
        response = admin_client.get("/api/v1/admin/complaints")
        self.assertIn(complaint_id, [item["id"] for item in response.json["data"]["items"]])
        response = admin_client.get(f"/api/v1/admin/complaints/{complaint_id}")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["complaint"]["status"], "viewed")
        self.assertNotIn("submitter_user_id", response.json["data"]["complaint"])


if __name__ == "__main__":
    unittest.main()
