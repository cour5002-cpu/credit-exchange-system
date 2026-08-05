import unittest

from app.core.errors import BusinessError
from app.core.identity import current_student, current_teacher
from app.extensions import db
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User
from tests.test_support import create_isolated_test_app


class BusinessErrorTest(unittest.TestCase):
    def test_default_and_custom_error_contract(self):
        default_error = BusinessError("参数错误")
        self.assertIsInstance(default_error, ValueError)
        self.assertEqual(str(default_error), "参数错误")
        self.assertEqual(default_error.code, 40001)
        self.assertEqual(default_error.status, 400)

        forbidden_error = BusinessError("无权限", code=40301, status=403)
        self.assertEqual(str(forbidden_error), "无权限")
        self.assertEqual(forbidden_error.code, 40301)
        self.assertEqual(forbidden_error.status, 403)

    def test_week3_compatibility_exports_use_canonical_objects(self):
        from app.services.week3_hour_application_service import (
            BusinessError as LegacyBusinessError,
            current_student as legacy_current_student,
            current_teacher as legacy_current_teacher,
        )

        self.assertIs(LegacyBusinessError, BusinessError)
        self.assertIs(legacy_current_student, current_student)
        self.assertIs(legacy_current_teacher, current_teacher)


class IdentityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_isolated_test_app()
        with cls.app.app_context():
            cls.active_student_user_id = cls._create_user("core_student", "student")
            cls.inactive_student_user_id = cls._create_user("core_student_disabled", "student")
            cls.no_identity_user_id = cls._create_user("core_no_identity", "student")
            cls.advisor_user_id = cls._create_user("core_advisor", "teacher")
            cls.inactive_teacher_user_id = cls._create_user("core_teacher_disabled", "teacher")

            active_student = Student(
                user_id=cls.active_student_user_id,
                student_no="CORE-S-001",
                name="有效学生",
                status="active",
            )
            inactive_student = Student(
                user_id=cls.inactive_student_user_id,
                student_no="CORE-S-002",
                name="停用学生",
                status="disabled",
            )
            advisor = Teacher(
                user_id=cls.advisor_user_id,
                teacher_no="CORE-T-001",
                name="指导老师",
                role_flags="advisor",
                status="active",
            )
            inactive_teacher = Teacher(
                user_id=cls.inactive_teacher_user_id,
                teacher_no="CORE-T-002",
                name="停用教师",
                role_flags="advisor,reviewer",
                status="disabled",
            )
            db.session.add_all(
                [active_student, inactive_student, advisor, inactive_teacher]
            )
            db.session.commit()
            cls.active_student_id = active_student.id
            cls.advisor_id = advisor.id

    @staticmethod
    def _create_user(username, role):
        user = User(
            username=username,
            role=role,
            real_name=username,
            status="active",
        )
        user.set_password("test-password")
        db.session.add(user)
        db.session.flush()
        return user.id

    def _user(self, user_id):
        return db.session.get(User, user_id)

    def _assert_forbidden_identity(self, action, message):
        with self.assertRaises(BusinessError) as context:
            action()
        self.assertEqual(str(context.exception), message)
        self.assertEqual(context.exception.code, 40301)
        self.assertEqual(context.exception.status, 403)

    def test_current_student_returns_only_active_identity(self):
        with self.app.app_context():
            student = current_student(self._user(self.active_student_user_id))
            self.assertEqual(student.id, self.active_student_id)

            self._assert_forbidden_identity(
                lambda: current_student(self._user(self.inactive_student_user_id)),
                "当前账号没有可用学生身份",
            )
            self._assert_forbidden_identity(
                lambda: current_student(self._user(self.no_identity_user_id)),
                "当前账号没有可用学生身份",
            )

    def test_current_teacher_checks_active_identity_and_role_flag(self):
        with self.app.app_context():
            teacher = current_teacher(self._user(self.advisor_user_id))
            self.assertEqual(teacher.id, self.advisor_id)
            self.assertEqual(
                current_teacher(self._user(self.advisor_user_id), "advisor").id,
                self.advisor_id,
            )

            self._assert_forbidden_identity(
                lambda: current_teacher(self._user(self.advisor_user_id), "reviewer"),
                "当前教师不具备该操作角色",
            )
            self._assert_forbidden_identity(
                lambda: current_teacher(self._user(self.inactive_teacher_user_id)),
                "当前账号没有可用教师身份",
            )


if __name__ == "__main__":
    unittest.main()
