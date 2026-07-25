import { adaptTeacher } from './userAdapter.js'

export function getListItems(payload) {
  if (Array.isArray(payload)) return payload
  return Array.isArray(payload?.items) ? payload.items : []
}

export function adaptTaskType(item) {
  if (!item) return null
  return {
    id: item.id,
    value: item.id,
    code: item.type_code,
    label: item.type_name,
    name: item.type_name,
    status: item.status,
    sortOrder: item.sort_order ?? 0,
    allowStudentSelf: item.allow_student_self ?? true,
    allowAdminTask: item.allow_admin_task ?? true,
    allowTeacherTask: item.allow_teacher_task ?? true,
    isMockFallback: false,
  }
}

export function adaptAdvisor(item) {
  const teacher = adaptTeacher(item)
  return teacher && { ...teacher, advisorId: teacher.id, advisorName: teacher.name, isMockFallback: false }
}

export function adaptReviewer(item) {
  const teacher = adaptTeacher(item)
  return teacher && {
    ...teacher,
    reviewerId: teacher.id,
    reviewerName: teacher.name,
    direction: teacher.major,
    pendingCount: item.pending_count ?? 0,
    isMockFallback: false,
  }
}
