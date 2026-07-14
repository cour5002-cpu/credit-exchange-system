import click

from app.extensions import db
from app.models.student import Student
from app.models.student_hour_account import StudentHourAccount
from app.models.system_config import SystemConfig
from app.models.task_type import TaskType
from app.models.teacher import Teacher
from app.models.user import User


def register_seed_commands(app) -> None:
    @app.cli.command("seed-basic-data")
    def seed_basic_data():
        seed_task_types()
        seed_system_configs()
        seed_default_users()
        db.session.commit()
        click.echo("基础数据初始化完成。")


def seed_task_types() -> None:
    items = [
        ("project", "项目类", 1),
        ("practice", "实践类", 2),
        ("competition", "竞赛类", 3),
        ("certificate", "证书类", 4),
    ]
    valid_codes = {code for code, _, _ in items}
    for task_type in TaskType.query.all():
        if task_type.type_code not in valid_codes:
            task_type.status = "disabled"

    for code, name, order in items:
        exists = TaskType.query.filter_by(type_code=code).first()
        if exists:
            exists.type_name = name
            exists.sort_order = order
            exists.status = "enabled"
            exists.allow_student_self = True
            exists.allow_admin_task = True
            exists.allow_teacher_task = True
            continue
        db.session.add(
            TaskType(
                type_code=code,
                type_name=name,
                sort_order=order,
                allow_student_self=True,
                allow_admin_task=True,
                allow_teacher_task=True,
            )
        )


def seed_system_configs() -> None:
    items = [
        ("credit_exchange_ratio", "10:1", "10课时兑换1学分"),
        ("max_single_exchange_hours", "100", "单次最大兑换课时数"),
        ("allow_student_resubmit", "0", "是否允许驳回后重新提交"),
    ]
    for key, value, description in items:
        exists = SystemConfig.query.filter_by(config_key=key).first()
        if exists:
            continue
        db.session.add(
            SystemConfig(
                config_key=key,
                config_value=value,
                description=description,
            )
        )


def seed_default_users() -> None:
    ensure_admin_user()
    ensure_teacher_users()
    ensure_student_user()


def ensure_admin_user() -> None:
    exists = User.query.filter_by(username="admin").first()
    if exists:
        return
    user = User(
        username="admin",
        role="admin",
        real_name="系统管理员",
        status="active",
    )
    user.set_password("admin123")
    db.session.add(user)


def ensure_teacher_users() -> None:
    teacher_items = [
        ("teacher1", "teacher123", "张老师", "A", "1", "T2026001"),
        ("teacher2", "teacher123", "李老师", "B", "2", "T2026002"),
        ("teacher3", "teacher123", "王老师", "C", "3", "T2026003"),
        ("teacher4", "teacher123", "赵老师", "D", "4", "T2026004"),
        ("teacher5", "teacher123", "孙老师", "E", "1", "T2026005"),
        ("teacher6", "teacher123", "周老师", "F", "2", "T2026006"),
    ]
    for username, password, real_name, major_name, course_name, teacher_no in teacher_items:
        exists = User.query.filter_by(username=username).first()
        if exists:
            teacher = Teacher.query.filter_by(user_id=exists.id).first()
            if teacher:
                teacher.name = real_name
                teacher.major_name = major_name
                teacher.course_name = course_name
                teacher.teacher_no = teacher_no
                teacher.status = "active"
            continue

        user = User(
            username=username,
            role="teacher",
            real_name=real_name,
            status="active",
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        db.session.add(
            Teacher(
                user_id=user.id,
                teacher_no=teacher_no,
                name=real_name,
                major_name=major_name,
                course_name=course_name,
                role_flags="advisor,reviewer",
                department="教务处",
                title="讲师",
                status="active",
            )
        )


def ensure_student_user() -> None:
    exists = User.query.filter_by(username="student1").first()
    if exists:
        return

    user = User(
        username="student1",
        role="student",
        real_name="测试学生",
        status="active",
    )
    user.set_password("student123")
    db.session.add(user)
    db.session.flush()

    student = Student(
        user_id=user.id,
        student_no="20260001",
        name=user.real_name,
        gender="未知",
        college="示例学院",
        major="软件工程",
        grade="2026",
        class_name="1班",
        status="active",
    )
    db.session.add(student)
    db.session.flush()

    db.session.add(
        StudentHourAccount(
            student_id=student.id,
            total_earned_hours=0,
            total_exchanged_hours=0,
            available_hours=0,
        )
    )
