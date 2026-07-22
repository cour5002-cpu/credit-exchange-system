export const COMPLAINT_STATUS = Object.freeze({ PENDING_ADMIN: 'pending_admin', PROCESSED: 'processed' })

const complaints = []

function nowText() {
  const date = new Date(); const pad = (value) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function addComplaint(data) {
  if (!data?.complaintType || !data?.complaintContent?.trim()) return null
  const complaint = {
    complaintId: data.complaintId || `CMP-${Date.now()}`,
    studentId: data.studentId || '', studentName: data.studentName || '', isAnonymous: data.isAnonymous !== false,
    relatedApplicationId: data.relatedApplicationId || '', relatedApplicationTitle: data.relatedApplicationTitle || '',
    complaintType: data.complaintType, complaintContent: data.complaintContent.trim(),
    complaintMaterials: (data.complaintMaterials || []).map((file) => ({ ...file })),
    submitTime: data.submitTime || nowText(), status: COMPLAINT_STATUS.PENDING_ADMIN,
    adminComment: '', adminHandleTime: '',
  }
  complaints.push(complaint)
  return complaint
}
export function getComplaints() { return complaints }
export function getComplaintById(complaintId) { return complaints.find((item) => item.complaintId === complaintId) }
export function getStudentComplaints(studentId) { return complaints.filter((item) => item.studentId === studentId) }
export function getAdminPendingComplaints() { return complaints.filter((item) => item.status === COMPLAINT_STATUS.PENDING_ADMIN) }
export function processComplaint(complaintId, comment = '') {
  const complaint = getComplaintById(complaintId)
  if (!complaint || complaint.status !== COMPLAINT_STATUS.PENDING_ADMIN || !comment.trim()) return null
  complaint.status = COMPLAINT_STATUS.PROCESSED; complaint.adminComment = comment.trim(); complaint.adminHandleTime = nowText()
  return complaint
}
