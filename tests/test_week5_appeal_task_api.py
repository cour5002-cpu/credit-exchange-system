import unittest
from datetime import datetime, timedelta
from io import BytesIO

from app.commands.seed_data import seed_default_users, seed_system_configs, seed_task_types
from app.extensions import db
from app.models.appeal import Appeal
from app.models.college_task import CollegeTask
from app.models.task_result_submission_version import TaskResultSubmissionVersion
from tests.test_support import create_isolated_test_app


class Week5AppealTaskApiTest(unittest.TestCase):
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

    def client_login(self, username, password):
        client = self.app.test_client()
        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return client, response.json["data"]

    def create_final_rejected_hour_application(self):
        student_client, student_me = self.client_login("student1", "student123")
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

        response = student_client.get(f"/api/v1/student/appealable-targets/hour_application/{application_id}")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertFalse(response.json["data"]["can_appeal"])
        self.assertEqual(response.json["data"]["reason"], "同一业务对象只能申诉一次")

        response = student_client.post(
            "/api/v1/student/appeals",
            json={"target_type": "hour_application", "target_id": application_id, "reason": "重复申诉"},
        )
        self.assertEqual(response.status_code, 409)

        response = admin_client.get("/api/v1/admin/appeals?status=pending_admin_review")
        self.assertEqual(response.status_code, 200)
        self.assertIn(appeal_id, [item["id"] for item in response.json["data"]["items"]])

        response = admin_client.get(f"/api/v1/admin/appeals/{appeal_id}")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        detail = response.json["data"]
        self.assertEqual(set(detail), {"appeal", "target", "attachments"})
        self.assertEqual(detail["appeal"]["id"], appeal_id)
        self.assertEqual(detail["appeal"]["target_type"], "hour_application")
        self.assertEqual(detail["target"]["id"], application_id)
        self.assertEqual(detail["target"]["status"], "final_rejected")
        self.assertEqual(
            [item["id"] for item in detail["attachments"]],
            [upload.json["data"]["id"]],
        )

        response = admin_client.post(
            f"/api/v1/admin/appeals/{appeal_id}/approve",
            json={"admin_advice": "申诉理由成立，退回指导老师重新确认"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "processing")
        self.assertEqual(response.json["data"]["target_status"], "submitted")

    def test_without_material_appeal_reuses_submitted_material(self):
        student_client, _ = self.client_login("student1", "student123")
        advisor_client, advisor_me = self.client_login("teacher1", "teacher123")
        admin_client, _ = self.client_login("admin", "admin123")
        reviewer_client, reviewer_me = self.client_login("teacher2", "teacher123")
        task_type_id = student_client.get(
            "/api/v1/task-types?enabled=true"
        ).json["data"]["items"][0]["id"]

        response = student_client.post("/api/v1/student/hour-applications", json={
            "application_type": "without_material",
            "task_type_id": task_type_id,
            "title": "无成果补交后申诉复用成果",
            "requested_hours": 8,
            "material_due_at": (datetime.now() + timedelta(days=7)).isoformat(),
            "advisor_teacher_id": advisor_me["teacher"]["id"],
        })
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        application_id = response.json["data"]["id"]
        response = advisor_client.post(
            f"/api/v1/advisor/hour-applications/{application_id}/approve",
            json={"comment": "同意后续补交成果"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))

        material_upload = student_client.post("/api/v1/attachments", data={
            "biz_type": "hour_application",
            "file": (BytesIO(b"existing submitted material"), "existing-material.txt"),
        }, content_type="multipart/form-data")
        self.assertEqual(material_upload.status_code, 200, material_upload.get_data(as_text=True))
        material_attachment_id = material_upload.json["data"]["id"]
        response = student_client.post(
            f"/api/v1/student/hour-applications/{application_id}/materials",
            json={
                "achievement_summary": "已经补交的成果",
                "attachment_ids": [material_attachment_id],
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        response = advisor_client.post(
            f"/api/v1/advisor/hour-applications/{application_id}/materials/approve",
            json={"comment": "确认补交成果"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        response = admin_client.post(
            f"/api/v1/admin/hour-applications/{application_id}/assign-reviewer",
            json={"reviewer_teacher_id": reviewer_me["teacher"]["id"]},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        response = reviewer_client.post(
            f"/api/v1/reviewer/hour-applications/{application_id}/reject",
            json={"comment": "审核驳回，进入申诉"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))

        appeal_upload = student_client.post("/api/v1/attachments", data={
            "biz_type": "appeal",
            "file": (BytesIO(b"appeal proof"), "appeal-proof.txt"),
        }, content_type="multipart/form-data")
        response = student_client.post("/api/v1/student/appeals", json={
            "target_type": "hour_application",
            "target_id": application_id,
            "reason": "请求复核已补交成果",
            "attachment_ids": [appeal_upload.json["data"]["id"]],
        })
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        appeal_id = response.json["data"]["id"]

        response = admin_client.post(
            f"/api/v1/admin/appeals/{appeal_id}/approve",
            json={"admin_advice": "受理并复用原成果重新审核"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["target_status"], "material_submitted")

        reopened_detail = student_client.get(
            f"/api/v1/student/hour-applications/{application_id}"
        )
        self.assertEqual(reopened_detail.status_code, 200, reopened_detail.get_data(as_text=True))
        self.assertIn(
            material_attachment_id,
            [item["id"] for item in reopened_detail.json["data"]["attachments"]],
        )

        response = advisor_client.post(
            f"/api/v1/advisor/appeals/{appeal_id}/reconfirm",
            json={"decision": "approve", "comment": "复用原成果再次确认通过"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["target_status"], "pending_assignment")
        self.assertEqual(response.json["data"]["reopen_stage"], "pending_assignment")

    def test_college_task_registration_and_selection(self):
        admin_client, _ = self.client_login("admin", "admin123")
        student_client, student_me = self.client_login("student1", "student123")
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

        detail = admin_client.get(f"/api/v1/admin/tasks/{task_id}")
        self.assertEqual(detail.status_code, 200, detail.get_data(as_text=True))
        self.assertTrue(detail.json["data"]["task"]["registration_deadline"].endswith("+08:00"))

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
        self.assertEqual(response.status_code, 409, response.get_data(as_text=True))
        self.assertIn("报名尚未截止", response.json["message"])

        with self.app.app_context():
            task = db.session.get(CollegeTask, task_id)
            task.registration_deadline = datetime.now() - timedelta(seconds=1)
            db.session.commit()

        response = advisor_client.post(
            f"/api/v1/advisor/tasks/{task_id}/registrations/select",
            json={"selected_registration_ids": [registration_id]},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["selected_count"], 1)
        self.assertEqual(response.json["data"]["task_status"], "leader_pending")

        response = advisor_client.get(f"/api/v1/advisor/tasks/{task_id}/selected-members")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["items"][0]["registration_id"], registration_id)
        self.assertFalse(response.json["data"]["items"][0]["is_leader"])

        response = advisor_client.post(f"/api/v1/advisor/tasks/{task_id}/leader", json={
            "leader_student_id": student_me["student"]["id"]
        })
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["task_status"], "task_in_progress")

        response = admin_client.get(f"/api/v1/admin/tasks/{task_id}")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["registrations"][0]["status"], "selected")

    def test_student_task_detail_hides_other_registrations(self):
        admin_client, _ = self.client_login("admin", "admin123")
        student1_client, _ = self.client_login("student1", "student123")
        student2_client, _ = self.client_login("student2", "student123")
        advisor_client, advisor_me = self.client_login("teacher1", "teacher123")
        task_type_id = admin_client.get(
            "/api/v1/task-types?enabled=true"
        ).json["data"]["items"][0]["id"]
        task = admin_client.post("/api/v1/admin/tasks", json={
            "title": "学生任务详情隐私测试",
            "description": "学生只能看到自己的报名信息",
            "task_type_id": task_type_id,
            "advisor_teacher_id": advisor_me["teacher"]["id"],
            "result_requirement": "提交成果",
            "registration_deadline": (datetime.now() + timedelta(days=7)).isoformat(),
        })
        task_id = task.json["data"]["id"]
        own_registration = student1_client.post(
            f"/api/v1/student/tasks/{task_id}/registrations",
            json={"remark": "学生一报名理由"},
        ).json["data"]["registration_id"]
        student2_client.post(
            f"/api/v1/student/tasks/{task_id}/registrations",
            json={"remark": "学生二报名理由"},
        )

        detail = student1_client.get(f"/api/v1/student/tasks/{task_id}")
        self.assertEqual(detail.status_code, 200, detail.get_data(as_text=True))
        self.assertEqual(detail.json["data"]["registration"]["id"], own_registration)
        self.assertNotIn("registrations", detail.json["data"])
        self.assertNotIn("members", detail.json["data"])
        self.assertNotIn("registrations", detail.json["data"]["task"])
        self.assertNotIn("members", detail.json["data"]["task"])
        self.assertNotIn("学生二报名理由", detail.get_data(as_text=True))

    def test_selection_requires_a_decision_for_every_registration(self):
        admin_client, _ = self.client_login("admin", "admin123")
        student1_client, _ = self.client_login("student1", "student123")
        student2_client, _ = self.client_login("student2", "student123")
        advisor_client, advisor_me = self.client_login("teacher1", "teacher123")
        task_type_id = admin_client.get(
            "/api/v1/task-types?enabled=true"
        ).json["data"]["items"][0]["id"]
        task = admin_client.post("/api/v1/admin/tasks", json={
            "title": "报名完整筛选测试",
            "description": "全部报名必须明确选中或不选中",
            "task_type_id": task_type_id,
            "advisor_teacher_id": advisor_me["teacher"]["id"],
            "result_requirement": "提交成果",
            "registration_deadline": (datetime.now() + timedelta(days=7)).isoformat(),
        })
        task_id = task.json["data"]["id"]
        first_id = student1_client.post(
            f"/api/v1/student/tasks/{task_id}/registrations", json={}
        ).json["data"]["registration_id"]
        second_id = student2_client.post(
            f"/api/v1/student/tasks/{task_id}/registrations", json={}
        ).json["data"]["registration_id"]
        with self.app.app_context():
            db_task = db.session.get(CollegeTask, task_id)
            db_task.registration_deadline = datetime.now() - timedelta(seconds=1)
            db.session.commit()

        incomplete = advisor_client.post(
            f"/api/v1/advisor/tasks/{task_id}/registrations/select",
            json={"selected_registration_ids": [first_id]},
        )
        self.assertEqual(incomplete.status_code, 409, incomplete.get_data(as_text=True))
        self.assertIn("全部报名学生", incomplete.json["message"])

        complete = advisor_client.post(
            f"/api/v1/advisor/tasks/{task_id}/registrations/select",
            json={
                "selected_registration_ids": [first_id],
                "not_selected_registration_ids": [second_id],
            },
        )
        self.assertEqual(complete.status_code, 200, complete.get_data(as_text=True))

    def test_admin_and_advisor_task_publish_attachments(self):
        admin_client, _ = self.client_login("admin", "admin123")
        advisor_client, advisor_me = self.client_login("teacher1", "teacher123")
        student_client, _ = self.client_login("student1", "student123")
        task_type_id = admin_client.get(
            "/api/v1/task-types?enabled=true"
        ).json["data"]["items"][0]["id"]

        admin_upload = admin_client.post(
            "/api/v1/attachments",
            data={
                "biz_type": "task",
                "file": (BytesIO(b"admin task attachment"), "admin-task.pdf"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(admin_upload.status_code, 200, admin_upload.get_data(as_text=True))
        self.assertEqual(admin_upload.json["code"], 0)
        admin_attachment_id = admin_upload.json["data"]["id"]

        admin_task = admin_client.post("/api/v1/admin/tasks", json={
            "title": "管理员附件任务",
            "description": "验证管理员发布任务附件",
            "task_type_id": task_type_id,
            "advisor_teacher_id": advisor_me["teacher"]["id"],
            "result_requirement": "按要求提交成果",
            "registration_deadline": (datetime.now() + timedelta(days=7)).isoformat(),
            "attachment_ids": [admin_attachment_id],
        })
        self.assertEqual(admin_task.status_code, 200, admin_task.get_data(as_text=True))
        admin_task_id = admin_task.json["data"]["id"]
        admin_detail = admin_client.get(f"/api/v1/admin/tasks/{admin_task_id}")
        self.assertEqual(admin_detail.status_code, 200, admin_detail.get_data(as_text=True))
        self.assertEqual(
            [item["id"] for item in admin_detail.json["data"]["attachments"]],
            [admin_attachment_id],
        )
        student_download = student_client.get(f"/api/v1/attachments/{admin_attachment_id}")
        self.assertEqual(student_download.status_code, 200, student_download.get_data(as_text=True))

        advisor_upload = advisor_client.post(
            "/api/v1/attachments",
            data={
                "biz_type": "task",
                "file": (BytesIO(b"advisor task attachment"), "advisor-task.pdf"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(advisor_upload.status_code, 200, advisor_upload.get_data(as_text=True))
        advisor_attachment_id = advisor_upload.json["data"]["id"]

        advisor_task = advisor_client.post("/api/v1/advisor/tasks", json={
            "title": "指导老师附件任务",
            "description": "验证指导老师发布任务附件",
            "task_type_id": task_type_id,
            "result_requirement": "按要求提交成果",
            "registration_deadline": (datetime.now() + timedelta(days=7)).isoformat(),
            "attachment_ids": [advisor_attachment_id],
        })
        self.assertEqual(advisor_task.status_code, 200, advisor_task.get_data(as_text=True))
        advisor_task_id = advisor_task.json["data"]["id"]
        advisor_detail = advisor_client.get(f"/api/v1/advisor/tasks/{advisor_task_id}")
        self.assertEqual(advisor_detail.status_code, 200, advisor_detail.get_data(as_text=True))
        self.assertEqual(
            [item["id"] for item in advisor_detail.json["data"]["attachments"]],
            [advisor_attachment_id],
        )
        admin_review_detail = admin_client.get(
            f"/api/v1/admin/task-publish-requests/{advisor_task_id}"
        )
        self.assertEqual(
            admin_review_detail.status_code,
            200,
            admin_review_detail.get_data(as_text=True),
        )
        self.assertEqual(
            [item["id"] for item in admin_review_detail.json["data"]["attachments"]],
            [advisor_attachment_id],
        )

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
        with self.app.app_context():
            task = db.session.get(CollegeTask, task_id)
            task.registration_deadline = datetime.now() - timedelta(seconds=1)
            db.session.commit()
        response = advisor_client.post(f"/api/v1/advisor/tasks/{task_id}/registrations/select", json={
            "selected_registration_ids": [registration_id]
        })
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        response = advisor_client.post(f"/api/v1/advisor/tasks/{task_id}/leader", json={
            "leader_student_id": student_me["student"]["id"]
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
        self.assertEqual(response.json["data"]["status"], "submitted")

        advisor_pending = advisor_client.get(
            "/api/v1/advisor/hour-applications/pending?status=submitted"
        )
        self.assertEqual(advisor_pending.status_code, 200, advisor_pending.get_data(as_text=True))
        pending_application = next(
            item for item in advisor_pending.json["data"]["items"]
            if item["id"] == application_id
        )
        self.assertEqual(pending_application["application_type"], "task_result")
        self.assertEqual(pending_application["advisor_teacher_id"], advisor_me["teacher"]["id"])

        pending_results = advisor_client.get("/api/v1/advisor/task-result-submissions?status=submitted")
        self.assertEqual(pending_results.status_code, 200, pending_results.get_data(as_text=True))
        pending_item = next(
            item for item in pending_results.json["data"]["items"]
            if item["id"] == submission_id
        )
        self.assertEqual(pending_item["hour_application_id"], application_id)
        self.assertEqual(pending_item["attachment_count"], 1)
        self.assertEqual(pending_item["leader"]["id"], student_me["student"]["id"])

        material_pending = advisor_client.get("/api/v1/advisor/hour-applications/materials/pending")
        self.assertEqual(material_pending.status_code, 200, material_pending.get_data(as_text=True))
        self.assertNotIn(application_id, [item["id"] for item in material_pending.json["data"]["items"]])

        wrong_detail = advisor_client.get(f"/api/v1/advisor/hour-applications/{application_id}/materials")
        self.assertEqual(wrong_detail.status_code, 409, wrong_detail.get_data(as_text=True))
        wrong_approve = advisor_client.post(
            f"/api/v1/advisor/hour-applications/{application_id}/materials/approve",
            json={"comment": "不应通过补交接口处理"},
        )
        self.assertEqual(wrong_approve.status_code, 409, wrong_approve.get_data(as_text=True))

        initial_detail = advisor_client.get(f"/api/v1/advisor/task-result-submissions/{submission_id}")
        self.assertEqual(initial_detail.status_code, 200, initial_detail.get_data(as_text=True))
        self.assertEqual(
            [item["id"] for item in initial_detail.json["data"]["attachments"]],
            [upload.json["data"]["id"]],
        )
        download = advisor_client.get(f"/api/v1/attachments/{upload.json['data']['id']}?download=true")
        self.assertEqual(download.status_code, 200, download.get_data(as_text=True))
        download.close()

        response = advisor_client.post(
            f"/api/v1/advisor/task-result-submissions/{submission_id}/reject",
            json={"comment": "请补充成果材料"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["submission_status"], "advisor_rejected")

        replacement_upload = student_client.post("/api/v1/attachments", data={
            "biz_type": "task_result",
            "file": (BytesIO(b"task result proof v2"), "task-result-v2.txt"),
        }, content_type="multipart/form-data")
        response = student_client.post(
            f"/api/v1/student/task-result-submissions/{submission_id}/resubmit",
            json={
                "summary": "任务成果已补充完善",
                "requested_hours": 10,
                "attachment_ids": [replacement_upload.json["data"]["id"]],
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["submission_status"], "submitted")
        self.assertEqual(response.json["data"]["status"], "submitted")

        with self.app.app_context():
            versions = TaskResultSubmissionVersion.query.filter_by(
                submission_id=submission_id
            ).order_by(TaskResultSubmissionVersion.version_no).all()
            self.assertEqual([item.version_no for item in versions], [1, 2])
            self.assertEqual(versions[1].summary, "任务成果已补充完善")
            self.assertEqual(versions[1].attachment_ids, [replacement_upload.json["data"]["id"]])

        detail = advisor_client.get(f"/api/v1/advisor/task-result-submissions/{submission_id}")
        self.assertEqual(detail.status_code, 200, detail.get_data(as_text=True))
        self.assertEqual(len(detail.json["data"]["versions"]), 2)
        self.assertEqual(
            [item["id"] for item in detail.json["data"]["attachments"]],
            [replacement_upload.json["data"]["id"]],
        )

        response = advisor_client.post(
            f"/api/v1/advisor/hour-applications/{application_id}/approve",
            json={"comment": "成果确认"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "pending_assignment")
        task_result_detail = advisor_client.get(
            f"/api/v1/advisor/task-result-submissions/{submission_id}"
        )
        self.assertEqual(task_result_detail.status_code, 200, task_result_detail.get_data(as_text=True))
        self.assertEqual(
            task_result_detail.json["data"]["submission"]["status"],
            "converted_to_hour_application",
        )
        admin_detail = admin_client.get(f"/api/v1/admin/hour-applications/{application_id}")
        self.assertEqual(admin_detail.status_code, 200, admin_detail.get_data(as_text=True))
        self.assertEqual(
            [item["id"] for item in admin_detail.json["data"]["attachments"]],
            [replacement_upload.json["data"]["id"]],
        )
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
        response = reviewer_client.get(f"/api/v1/reviewer/appeal-reviews/{appeal_id}")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["appeal"]["id"], appeal_id)
        self.assertEqual(response.json["data"]["target"]["id"], application_id)
        response = reviewer_client.post(f"/api/v1/reviewer/appeal-reviews/{appeal_id}/approve", json={"comment": "申诉复审通过"})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["target_status"], "pending_admin_final")
        response = admin_client.post(f"/api/v1/admin/hour-applications/{application_id}/final-approve", json={"comment": "申诉后终审通过"})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["status"], "final_approved")
        with self.app.app_context():
            appeal = db.session.get(Appeal, appeal_id)
            self.assertEqual(appeal.status, "completed")
            self.assertEqual(appeal.reopen_stage, "completed")

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
