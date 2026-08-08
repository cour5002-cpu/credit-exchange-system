import unittest
from datetime import datetime, timedelta
from io import BytesIO

from app.commands.seed_data import seed_default_users, seed_system_configs, seed_task_types
from app.extensions import db
from app.models.college_task import CollegeTask
from app.models.task_result_submission import TaskResultSubmission
from tests.test_support import create_isolated_test_app


class TaskResultAppealReopenTest(unittest.TestCase):
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
        response = client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return client, response.json["data"]

    def test_task_result_appeal_restores_advisor_confirmation_state(self):
        admin_client, _ = self.login("admin", "admin123")
        student_client, student_me = self.login("student1", "student123")
        advisor_client, advisor_me = self.login("teacher1", "teacher123")
        reviewer_client, reviewer_me = self.login("teacher2", "teacher123")
        task_type_id = admin_client.get(
            "/api/v1/task-types?enabled=true"
        ).json["data"]["items"][0]["id"]

        task_response = admin_client.post("/api/v1/admin/tasks", json={
            "title": "任务成果申诉重审状态测试",
            "description": "验证管理员同意申诉后可由指导老师再次确认",
            "task_type_id": task_type_id,
            "advisor_teacher_id": advisor_me["teacher"]["id"],
            "result_requirement": "提交完整成果",
            "registration_deadline": (datetime.now() + timedelta(days=7)).isoformat(),
        })
        self.assertEqual(task_response.status_code, 200, task_response.get_data(as_text=True))
        task_id = task_response.json["data"]["id"]

        registration = student_client.post(
            f"/api/v1/student/tasks/{task_id}/registrations",
            json={"remark": "报名"},
        )
        registration_id = registration.json["data"]["registration_id"]
        with self.app.app_context():
            task = db.session.get(CollegeTask, task_id)
            task.registration_deadline = datetime.now() - timedelta(seconds=1)
            db.session.commit()

        selected = advisor_client.post(
            f"/api/v1/advisor/tasks/{task_id}/registrations/select",
            json={"selected_registration_ids": [registration_id]},
        )
        self.assertEqual(selected.status_code, 200, selected.get_data(as_text=True))
        leader = advisor_client.post(
            f"/api/v1/advisor/tasks/{task_id}/leader",
            json={"leader_student_id": student_me["student"]["id"]},
        )
        self.assertEqual(leader.status_code, 200, leader.get_data(as_text=True))

        result_upload = student_client.post(
            "/api/v1/attachments",
            data={
                "biz_type": "task_result",
                "file": (BytesIO(b"task result"), "task-result.txt"),
            },
            content_type="multipart/form-data",
        )
        submission_response = student_client.post(
            f"/api/v1/student/tasks/{task_id}/result-submissions",
            json={
                "summary": "任务成果",
                "requested_hours": 10,
                "attachment_ids": [result_upload.json["data"]["id"]],
            },
        )
        self.assertEqual(
            submission_response.status_code,
            200,
            submission_response.get_data(as_text=True),
        )
        submission_id = submission_response.json["data"]["submission_id"]
        application_id = submission_response.json["data"]["hour_application_id"]

        advisor_approve = advisor_client.post(
            f"/api/v1/advisor/hour-applications/{application_id}/approve",
            json={"comment": "首次确认"},
        )
        self.assertEqual(advisor_approve.status_code, 200, advisor_approve.get_data(as_text=True))
        assigned = admin_client.post(
            f"/api/v1/admin/hour-applications/{application_id}/assign-reviewer",
            json={"reviewer_teacher_id": reviewer_me["teacher"]["id"]},
        )
        self.assertEqual(assigned.status_code, 200, assigned.get_data(as_text=True))
        reviewed = reviewer_client.post(
            f"/api/v1/reviewer/hour-applications/{application_id}/approve",
            json={"comment": "审核通过"},
        )
        self.assertEqual(reviewed.status_code, 200, reviewed.get_data(as_text=True))
        rejected = admin_client.post(
            f"/api/v1/admin/hour-applications/{application_id}/final-reject",
            json={"comment": "最终驳回"},
        )
        self.assertEqual(rejected.status_code, 200, rejected.get_data(as_text=True))

        appeal_upload = student_client.post(
            "/api/v1/attachments",
            data={
                "biz_type": "appeal",
                "file": (BytesIO(b"appeal proof"), "appeal-proof.txt"),
            },
            content_type="multipart/form-data",
        )
        appeal_response = student_client.post("/api/v1/student/appeals", json={
            "target_type": "hour_application",
            "target_id": application_id,
            "reason": "申请重新审核任务成果",
            "attachment_ids": [appeal_upload.json["data"]["id"]],
        })
        self.assertEqual(appeal_response.status_code, 200, appeal_response.get_data(as_text=True))
        appeal_id = appeal_response.json["data"]["id"]
        accepted = admin_client.post(
            f"/api/v1/admin/appeals/{appeal_id}/approve",
            json={"admin_advice": "同意重新审核"},
        )
        self.assertEqual(accepted.status_code, 200, accepted.get_data(as_text=True))

        with self.app.app_context():
            submission = db.session.get(TaskResultSubmission, submission_id)
            self.assertEqual(submission.status, "submitted")
            self.assertEqual(submission.task.status, "result_submitted")
            self.assertIsNone(submission.advisor_comment)
            self.assertIsNone(submission.advisor_reviewed_by)
            self.assertIsNone(submission.advisor_reviewed_at)

            # Recreate the stale state left by servers before this fix. The
            # reconfirm endpoint must repair it without a manual data update.
            submission.status = "converted_to_hour_application"
            submission.task.status = "result_approved"
            db.session.commit()

        reconfirmed = advisor_client.post(
            f"/api/v1/advisor/appeals/{appeal_id}/reconfirm",
            json={"decision": "approve", "comment": "再次确认通过"},
        )
        self.assertEqual(reconfirmed.status_code, 200, reconfirmed.get_data(as_text=True))
        self.assertEqual(reconfirmed.json["data"]["target_status"], "pending_assignment")
        self.assertEqual(reconfirmed.json["data"]["reopen_stage"], "pending_assignment")

        with self.app.app_context():
            submission = db.session.get(TaskResultSubmission, submission_id)
            self.assertEqual(submission.status, "converted_to_hour_application")
            self.assertEqual(submission.task.status, "result_approved")


if __name__ == "__main__":
    unittest.main()
