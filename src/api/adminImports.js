export const ADMIN_IMPORT_ENDPOINTS = {
  students: '/api/v1/admin/imports/students',
  teachers: '/api/v1/admin/imports/teachers',
  admins: '/api/v1/admin/imports/admins',
}

// 仅预留请求配置。本阶段的页面使用 Mock 结果，不会调用后端。
export function createImportRequest(type, file) {
  const formData = new FormData()
  formData.append('file', file)

  return {
    url: ADMIN_IMPORT_ENDPOINTS[type],
    options: {
      method: 'POST',
      body: formData,
    },
  }
}

export function importStudents(file) {
  return createImportRequest('students', file)
}

export function importTeachers(file) {
  return createImportRequest('teachers', file)
}

export function importAdmins(file) {
  return createImportRequest('admins', file)
}

// 模板下载地址待后端确认；当前页面在浏览器中生成示例 CSV，不发起请求。
export function createTemplateDownloadRequest(type) {
  return {
    url: `/api/v1/admin/imports/${type}/template`,
    options: { method: 'GET' },
  }
}
