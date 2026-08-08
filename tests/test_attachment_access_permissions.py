import unittest
from datetime import datetime, timedelta
from io import BytesIO

from app.commands.seed_data import seed_default_users, seed_system_configs, seed_task_types
from app.extensions import db
from app.models.appeal import Appeal
from app.models.application_advisor import ApplicationAdvisor
from app.models.attachment import Attachment
from app.models.college_task import CollegeTask
from app.models.credit_exchange_application import CreditExchangeApplication
from app.models.hour_application import HourApplication
from app.models.review_assignment import ReviewAssignment
from app.models.student import Student
from app.models.task_result_submission import TaskResultSubmission
from app.models.task_type import TaskType
from app.models.teacher import Teacher
from app.models.user import User
from tests.test_support import create_isolated_test_app


class AttachmentAccessPermissionsTest(unittest.TestCase):
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
        response = client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return client

    def upload(self, client, biz_type, filename):
        response = client.post(
            "/api/v1/attachments",
            data={
                "biz_type": biz_type,
                "file": (BytesIO(filename.encode()), filename),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return response.json["data"]["id"]

    def test_task_and_appeal_attachment_access_policy(self):
        admin_client = self.client_login("admin", "admin123")
        student1_client = self.client_login("student1", "student123")
        student2_client = self.client_login("student2", "student123")
        advisor_client = self.client_login("teacher1", "teacher123")
        reviewer_client = self.client_login("teacher2", "teacher123")
        reassigned_reviewer_client = self.client_login("teacher3", "teacher123")

        with self.app.app_context():
            admin = User.query.filter_by(username="admin").first()
            student1 = Student.query.join(User).filter(User.username == "student1").first()
            advisor = Teacher.query.join(User).filter(User.username == "teacher1").first()
            reviewer = Teacher.query.join(User).filter(User.username == "teacher2").first()
            reassigned_reviewer = Teacher.query.join(User).filter(
                User.username == "teacher3"
            ).first()
            task_type = TaskType.query.filter_by(status="enabled").first()

            task = CollegeTask(
                task_no="TK-ATTACHMENT-POLICY",
                title="附件权限测试任务",
                description="验证任务发布附件与任务成果附件权限",
                task_type_id=task_type.id,
                major_name="测试专业",
                course_name="测试课程",
                requirement="提交测试成果",
                publisher_type="admin",
                publisher_user_id=admin.id,
                advisor_teacher_id=advisor.id,
                registration_deadline=datetime.now() + timedelta(days=7),
                status="result_submitted",
            )
            db.session.add(task)
            db.session.flush()

            application = HourApplication(
                application_no="HT-ATTACHMENT-POLICY",
                student_id=student1.id,
                applicant_student_id=student1.id,
                leader_student_id=student1.id,
                application_type="task_result",
                source_type="admin_task",
                source_task_id=task.id,
                task_type_id=task_type.id,
                task_type_code=task_type.type_code,
                title=task.title,
                requested_hours=8,
                status="pending_review",
                assigned_teacher_id=reviewer.id,
            )
            db.session.add(application)
            db.session.flush()

            submission = TaskResultSubmission(
                task_id=task.id,
                leader_student_id=student1.id,
                summary="附件权限测试成果",
                requested_hours=8,
                status="converted_to_hour_application",
                hour_application_id=application.id,
            )
            db.session.add(submission)
            db.session.flush()
            application.task_result_submission_id = submission.id
            db.session.add(ApplicationAdvisor(
                application_id=application.id,
                teacher_id=advisor.id,
                advisor_role="primary",
                can_operate=True,
            ))

            hour_appeal = Appeal(
                appeal_no="AP-HOUR-ATTACHMENT-POLICY",
                target_type="hour_application",
                target_id=application.id,
                applicant_student_id=student1.id,
                reason="课时申诉附件权限测试",
                status="processing",
            )
            exchange = CreditExchangeApplication(
                exchange_no="CE-ATTACHMENT-POLICY",
                student_id=student1.id,
                applicant_student_id=student1.id,
                requested_hours=8,
                total_hours=8,
                status="final_rejected",
                advisor_teacher_id=advisor.id,
            )
            db.session.add_all([hour_appeal, exchange])
            db.session.flush()
            credit_appeal = Appeal(
                appeal_no="AP-CREDIT-ATTACHMENT-POLICY",
                target_type="credit_exchange",
                target_id=exchange.id,
                applicant_student_id=student1.id,
                reason="兑换申诉附件权限测试",
                status="processing",
            )
            db.session.add(credit_appeal)
            db.session.commit()
            ids = {
                "task": task.id,
                "application": application.id,
                "submission": submission.id,
                "hour_appeal": hour_appeal.id,
                "credit_appeal": credit_appeal.id,
                "reviewer": reviewer.id,
                "reassigned_reviewer": reassigned_reviewer.id,
            }

        task_attachment_id = self.upload(admin_client, "task", "task-policy.pdf")
        result_attachment_id = self.upload(
            student1_client,
            "task_result",
            "task-result-policy.pdf",
        )
        hour_appeal_attachment_id = self.upload(
            student1_client,
            "appeal",
            "hour-appeal-policy.pdf",
        )
        credit_appeal_attachment_id = self.upload(
            student1_client,
            "appeal",
            "credit-appeal-policy.pdf",
        )

        with self.app.app_context():
            bindings = [
                (task_attachment_id, "college_task", ids["task"]),
                (result_attachment_id, "task_result", ids["submission"]),
                (hour_appeal_attachment_id, "appeal", ids["hour_appeal"]),
                (credit_appeal_attachment_id, "appeal", ids["credit_appeal"]),
            ]
            for attachment_id, owner_type, owner_id in bindings:
                attachment = db.session.get(Attachment, attachment_id)
                attachment.owner_type = owner_type
                attachment.owner_id = owner_id
            db.session.commit()

        ordinary_student_access = student2_client.get(
            f"/api/v1/attachments/{task_attachment_id}?download=true"
        )
        self.assertEqual(
            ordinary_student_access.status_code,
            200,
            ordinary_student_access.get_data(as_text=True),
        )
        ordinary_student_access.close()

        reviewer_access = reviewer_client.get(
            f"/api/v1/attachments/{result_attachment_id}?download=true"
        )
        self.assertEqual(reviewer_access.status_code, 200, reviewer_access.get_data(as_text=True))
        reviewer_access.close()

        before_reassignment = reassigned_reviewer_client.get(
            f"/api/v1/attachments/{result_attachment_id}"
        )
        self.assertEqual(before_reassignment.status_code, 403)

        with self.app.app_context():
            application = db.session.get(HourApplication, ids["application"])
            application.assigned_teacher_id = ids["reassigned_reviewer"]
            ReviewAssignment.query.filter_by(
                application_id=application.id,
                status="active",
            ).update({"status": "replaced"})
            db.session.add(ReviewAssignment(
                application_id=application.id,
                reviewer_teacher_id=ids["reassigned_reviewer"],
                assigned_by=User.query.filter_by(username="admin").first().id,
                status="active",
            ))
            db.session.commit()

        after_reassignment = reassigned_reviewer_client.get(
            f"/api/v1/attachments/{result_attachment_id}?download=true"
        )
        self.assertEqual(after_reassignment.status_code, 200, after_reassignment.get_data(as_text=True))
        after_reassignment.close()

        old_reviewer_access = reviewer_client.get(
            f"/api/v1/attachments/{result_attachment_id}"
        )
        self.assertEqual(old_reviewer_access.status_code, 403)

        for attachment_id in (
            hour_appeal_attachment_id,
            credit_appeal_attachment_id,
        ):
            advisor_access = advisor_client.get(
                f"/api/v1/attachments/{attachment_id}?download=true"
            )
            self.assertEqual(
                advisor_access.status_code,
                200,
                advisor_access.get_data(as_text=True),
            )
            advisor_access.close()


if __name__ == "__main__":
    unittest.main()
