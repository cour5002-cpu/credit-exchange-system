def student_summary(student):
    return {
        "id": student.id,
        "student_no": student.student_no,
        "name": student.name,
        "college": student.college,
        "major": student.major,
        "class_name": student.class_name,
        "grade": student.grade,
    }


def teacher_summary(teacher):
    return {
        "id": teacher.id,
        "username": teacher.user.username if teacher.user else None,
        "teacher_no": teacher.teacher_no,
        "name": teacher.name,
        "college": None,
        "major": teacher.major_name,
        "role_flags": teacher.role_flag_list,
    }
