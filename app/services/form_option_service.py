def get_test_major_options():
    return ["A", "B", "C", "D", "E", "F"]


def get_test_course_options():
    return ["智能应用开发", "数据结构设计", "网络系统基础", "产品项目实训", "信息安全导论"]


def get_test_course_map():
    course_options = get_test_course_options()
    return {major: list(course_options) for major in get_test_major_options()}


def get_test_teacher_map():
    teacher_by_course = {
        "智能应用开发": "陈老师",
        "数据结构设计": "刘老师",
        "网络系统基础": "吴老师",
        "产品项目实训": "郑老师",
        "信息安全导论": "许老师",
    }
    teacher_map = {}
    for major in get_test_major_options():
        teacher_map[major] = {
            course_name: [teacher_name]
            for course_name, teacher_name in teacher_by_course.items()
        }
    return teacher_map
