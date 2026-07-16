import { ref } from 'vue'

export const confirmationTypeOptions = [
  { value: 'hour_application', label: '课时申请确认' },
  { value: 'result_supplement', label: '补交成果确认' },
  { value: 'extension_application', label: '延期申请确认' },
  { value: 'credit_exchange', label: '学分兑换确认' },
]

export const teacherConfirmations = ref([
  {
    id: 'TC-2026-001',
    title: '校园志愿服务课时申请',
    student: { name: '李晓雨', studentNo: '2023101001', college: '计算机学院', major: '软件工程' },
    type: 'hour_application',
    submittedAt: '2026-07-15 09:30',
    status: 'pending_confirmation',
    primaryTeacher: { name: '张明', department: '计算机学院' },
    members: [
      { name: '李晓雨', studentNo: '2023101001', college: '计算机学院', major: '软件工程', isLeader: true },
      { name: '周然', studentNo: '2023101022', college: '计算机学院', major: '软件工程', isLeader: false },
    ],
    application: { source: '学生自主申请', category: '志愿服务', requestedHours: 16 },
    description: '团队参与校园志愿服务周，负责新生引导、场地秩序维护和活动资料整理。',
    attachment: '志愿服务记录表、活动照片及团队成员承诺书',
    attachments: [
      { id: 'A-001-1', name: '校园志愿服务申请证明.pdf', type: 'PDF', uploadedAt: '2026-07-15 09:26', description: '活动组织方出具的申请证明材料' },
      { id: 'A-001-2', name: '团队成员承诺书.docx', type: 'Word', uploadedAt: '2026-07-15 09:28', description: '全体团队成员确认后的承诺书' },
    ],
  },
  {
    id: 'TC-2026-002',
    title: '创新创业项目成果补交',
    student: { name: '王晨', studentNo: '2022102036', college: '管理学院', major: '工商管理' },
    type: 'result_supplement',
    submittedAt: '2026-07-14 16:20',
    status: 'pending_confirmation',
    primaryTeacher: { name: '李华', department: '管理学院' },
    members: [
      { name: '王晨', studentNo: '2022102036', college: '管理学院', major: '工商管理', isLeader: true },
    ],
    application: { source: '任务成果申请', category: '创新创业', requestedHours: 20 },
    description: '补交项目路演材料和最终版商业计划书。',
    attachment: '商业计划书（最终版）、项目路演 PPT',
    attachments: [
      { id: 'A-002-1', name: '创新项目成果文件.pdf', type: 'PDF', uploadedAt: '2026-07-14 16:12', description: '项目最终成果及完成情况汇总' },
      { id: 'A-002-2', name: '成果展示截图.zip', type: '压缩包', uploadedAt: '2026-07-14 16:15', description: '系统运行和路演现场截图' },
      { id: 'A-002-3', name: '成果补交说明.docx', type: 'Word', uploadedAt: '2026-07-14 16:18', description: '成果补交内容和版本变更说明' },
    ],
  },
  {
    id: 'TC-2026-003',
    title: '学科竞赛成果延期申请',
    student: { name: '陈思远', studentNo: '2023103058', college: '电子信息学院', major: '通信工程' },
    type: 'extension_application',
    submittedAt: '2026-07-13 11:05',
    status: 'pending_confirmation',
    primaryTeacher: { name: '陈强', department: '校团委' },
    members: [
      { name: '陈思远', studentNo: '2023103058', college: '电子信息学院', major: '通信工程', isLeader: true },
      { name: '孙悦', studentNo: '2023103061', college: '电子信息学院', major: '电子信息工程', isLeader: false },
    ],
    application: { source: '学生自主申请', category: '学科竞赛', requestedHours: 24 },
    description: '因赛事结果公布时间调整，申请将成果提交期限延长至 2026 年 8 月 15 日。',
    attachment: '赛事延期通知、情况说明',
    attachments: [
      { id: 'A-003-1', name: '成果提交延期说明.pdf', type: 'PDF', uploadedAt: '2026-07-13 10:58', description: '延期原因、计划及预计提交时间说明' },
      { id: 'A-003-2', name: '赛事时间调整通知.png', type: '图片', uploadedAt: '2026-07-13 11:02', description: '赛事主办方发布的时间调整证明' },
    ],
  },
  {
    id: 'TC-2026-004',
    title: '志愿服务课时学分兑换',
    student: { name: '赵可欣', studentNo: '2022104107', college: '艺术学院', major: '视觉传达设计' },
    type: 'credit_exchange',
    submittedAt: '2026-07-12 14:45',
    status: 'pending_confirmation',
    primaryTeacher: { name: '王芳', department: '艺术学院' },
    members: [
      { name: '赵可欣', studentNo: '2022104107', college: '艺术学院', major: '视觉传达设计', isLeader: true },
    ],
    application: { source: '任务成果申请', category: '志愿服务', requestedHours: 32, requestedCredits: 1 },
    description: '申请将已认定的 32 个志愿服务课时兑换为 1 个实践学分。',
    attachment: '课时认定记录、学分兑换申请表',
    attachments: [
      { id: 'A-004-1', name: '团队学分分配表.xlsx', type: 'Excel', uploadedAt: '2026-07-12 14:38', description: '团队成员拟兑换学分及分配明细' },
      { id: 'A-004-2', name: '团队成员确认材料.pdf', type: 'PDF', uploadedAt: '2026-07-12 14:42', description: '团队成员签字确认的兑换材料' },
    ],
  },
])

export function getConfirmationTypeText(type) {
  return confirmationTypeOptions.find((option) => option.value === type)?.label ?? type
}

export function getTeacherConfirmation(id) {
  return teacherConfirmations.value.find((item) => item.id === id)
}
