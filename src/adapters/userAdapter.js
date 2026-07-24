export function adaptStudent(student) {
  if (!student) return null
  return {
    id: student.id,
    studentId: student.student_no,
    studentNo: student.student_no,
    name: student.name,
    college: student.college ?? '',
    major: student.major ?? '',
    className: student.class_name ?? '',
    grade: student.grade ?? '',
  }
}

export function adaptTeacher(teacher) {
  if (!teacher) return null
  return {
    id: teacher.id,
    teacherId: teacher.teacher_no,
    teacherNo: teacher.teacher_no,
    name: teacher.name,
    college: teacher.college ?? '',
    department: teacher.college ?? '',
    major: teacher.major ?? '',
    roleFlags: teacher.role_flags ?? [],
  }
}

export function adaptCurrentUser(user) {
  if (!user) return null
  return {
    id: user.id,
    username: user.username,
    role: user.role,
    roles: user.roles ?? [],
    student: adaptStudent(user.student),
    teacher: adaptTeacher(user.teacher),
  }
}

