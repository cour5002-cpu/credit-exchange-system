import click
from datetime import datetime, timedelta

from app.extensions import db
from app.models.application_advisor import ApplicationAdvisor
from app.models.hour_application import HourApplication
from app.models.student import Student
from app.models.student_hour_account import StudentHourAccount
from app.models.system_config import SystemConfig
from app.models.task_type import TaskType
from app.models.teacher import Teacher
from app.models.user import User
from app.utils.time_utils import business_now, format_api_datetime


def register_seed_commands(app) -> None:
    @app.cli.command("seed-basic-data")
    def seed_basic_data():
        seed_task_types()
        seed_system_configs()
        seed_default_users()
        db.session.commit()
        click.echo("基础数据初始化完成。")

    @app.cli.command("seed-integration-data")
    def seed_integration_data():
        seed_task_types()
        seed_system_configs()
        seed_default_users()
        db.session.commit()
        application = ensure_teacher1_pending_hour_application()
        click.echo(
            "联调数据初始化完成："
            f"student1 -> teacher1，申请 {application.application_no}，"
            f"状态 {application.status}。"
        )


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
        ("extension_special_threshold_days", "30", "延期超过30天时转管理员审核（V1固定口径）"),
        ("current_academic_year", "2026-2027", "消息模块当前学年"),
        ("current_semester", "1", "消息模块当前学期"),
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
    admin = User.query.filter_by(username="admin", status="active").first()
    if admin:
        from app.services.extension_rule_service import ensure_default_extension_rule

        ensure_default_extension_rule(admin)


def ensure_teacher1_pending_hour_application():
    student_user = User.query.filter_by(username="student1", status="active").first()
    teacher_user = User.query.filter_by(username="teacher1", status="active").first()
    if not student_user or not teacher_user:
        raise RuntimeError("请先初始化 student1 和 teacher1 测试账号")
    student = Student.query.filter_by(user_id=student_user.id, status="active").first()
    teacher = Teacher.query.filter_by(user_id=teacher_user.id, status="active").first()
    if not student or not teacher:
        raise RuntimeError("student1 或 teacher1 缺少有效角色资料")

    title = "前后端联调：student1 提交给 teacher1 的待确认课时申请"
    existing = (
        HourApplication.query.join(
            ApplicationAdvisor,
            ApplicationAdvisor.application_id == HourApplication.id,
        )
        .filter(
            HourApplication.applicant_student_id == student.id,
            HourApplication.title == title,
            HourApplication.status == "submitted",
            ApplicationAdvisor.teacher_id == teacher.id,
            ApplicationAdvisor.advisor_role == "primary",
            ApplicationAdvisor.can_operate.is_(True),
        )
        .order_by(HourApplication.id.desc())
        .first()
    )
    if existing:
        return existing

    task_type = TaskType.query.filter_by(status="enabled", allow_student_self=True).order_by(
        TaskType.sort_order,
        TaskType.id,
    ).first()
    if not task_type:
        raise RuntimeError("没有可用于学生自主申请的启用任务类型")

    from app.services.week3_hour_application_service import create_student_application

    return create_student_application(
        student_user,
        {
            "application_type": "without_material",
            "source_type": "student_self",
            "task_type_id": task_type.id,
            "requested_hours": 8,
            "title": title,
            "advisor_teacher_id": teacher.id,
            "material_due_at": format_api_datetime(business_now() + timedelta(days=30)),
            "description": "用于验证 student1 提交后，teacher1 能在指导老师待确认列表中看到该申请。",
            "course_name": "前后端接口联调",
            "member_count": 1,
            "member_student_ids": [student.id],
            "leader_student_id": student.id,
        },
        submit=True,
    )


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
            exists.real_name = real_name
            exists.status = "active"
            if teacher:
                teacher.name = real_name
                teacher.major_name = major_name
                teacher.course_name = course_name
                teacher.teacher_no = teacher_no
                teacher.role_flags = "advisor,reviewer"
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
    student_items = [
        ("student1", "student123", "测试学生1", "20260001"),
        ("student2", "student123", "测试学生2", "20260002"),
        ("student3", "student123", "测试学生3", "20260003"),
        ("student4", "student123", "测试学生4", "20260004"),
    ]
    for username, password, real_name, student_no in student_items:
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(
                username=username,
                role="student",
                real_name=real_name,
                status="active",
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
        else:
            user.role = "student"
            user.real_name = real_name
            user.status = "active"

        student = Student.query.filter_by(user_id=user.id).first()
        if not student:
            student = Student.query.filter_by(student_no=student_no).first()
        if not student:
            student = Student(user_id=user.id, student_no=student_no)
            db.session.add(student)

        student.user_id = user.id
        student.student_no = student_no
        student.name = real_name
        student.gender = student.gender or "未知"
        student.college = student.college or "示例学院"
        student.major = student.major or "软件工程"
        student.grade = student.grade or "2026"
        student.class_name = student.class_name or "1班"
        student.status = "active"
        db.session.flush()

        if not StudentHourAccount.query.filter_by(student_id=student.id).first():
            db.session.add(
                StudentHourAccount(
                    student_id=student.id,
                    total_earned_hours=0,
                    total_exchanged_hours=0,
                    available_hours=0,
                )
            )
