import { ref } from 'vue'

export const acceptanceTypeOptions = [
  { value: 'hour_application', label: '课时申请' },
  { value: 'result_supplement', label: '补交成果' },
  { value: 'extension_application', label: '延期申请' },
  { value: 'credit_exchange', label: '学分兑换' },
]

export const adminAcceptances = ref([
  {
    id: 'AC-2026-001', title: '校园志愿服务课时申请', source: 'self', type: 'hour_application', submittedAt: '2026-07-15 10:20', status: 'pending_acceptance', teacherStatus: 'confirmed',
    student: { name: '李晓雨', studentNo: '2023101001', college: '计算机学院', major: '软件工程' },
    teacher: { name: '张明', department: '计算机学院', opinion: '成员信息与活动记录一致，确认通过。', confirmedAt: '2026-07-15 10:05' },
    application: { source: '学生自主申请', category: '志愿服务', requestedHours: 16, description: '团队参与校园志愿服务周，完成新生引导和场地秩序维护。' },
    members: [
      { name: '李晓雨', studentNo: '2023101001', college: '计算机学院', major: '软件工程', isLeader: true },
      { name: '周然', studentNo: '2023101022', college: '计算机学院', major: '软件工程', isLeader: false },
    ],
    attachments: [
      { id: 'AC-A-01', name: '志愿服务申请证明.pdf', type: 'PDF', uploadedAt: '2026-07-15 09:26', description: '活动组织方出具的证明材料' },
      { id: 'AC-A-02', name: '团队成员承诺书.docx', type: 'Word', uploadedAt: '2026-07-15 09:28', description: '团队成员签字确认文件' },
    ],
  },
  {
    id: 'AC-2026-002', title: '创新创业项目成果补交', source: 'task', type: 'result_supplement', submittedAt: '2026-07-14 17:10', status: 'pending_acceptance', teacherStatus: 'confirmed',
    student: { name: '王晨', studentNo: '2022102036', college: '管理学院', major: '工商管理' },
    teacher: { name: '李华', department: '管理学院', opinion: '补交成果内容完整，确认通过。', confirmedAt: '2026-07-14 16:55' },
    application: { source: '任务成果申请', category: '创新创业', requestedHours: 20, description: '补交最终版商业计划书和项目路演材料。' },
    members: [{ name: '王晨', studentNo: '2022102036', college: '管理学院', major: '工商管理', isLeader: true }],
    attachments: [
      { id: 'AC-A-03', name: '最终成果文件.pdf', type: 'PDF', uploadedAt: '2026-07-14 16:12', description: '项目最终成果汇总' },
      { id: 'AC-A-04', name: '成果截图.zip', type: '压缩包', uploadedAt: '2026-07-14 16:15', description: '项目运行和展示截图' },
    ],
  },
  {
    id: 'AC-2026-003', title: '学科竞赛成果延期申请', source: 'self', type: 'extension_application', submittedAt: '2026-07-13 12:00', status: 'pending_acceptance', teacherStatus: 'confirmed',
    student: { name: '陈思远', studentNo: '2023103058', college: '电子信息学院', major: '通信工程' },
    teacher: { name: '陈强', department: '校团委', opinion: '延期理由真实，确认同意延期。', confirmedAt: '2026-07-13 11:42' },
    application: { source: '学生自主申请', category: '学科竞赛', requestedHours: 24, description: '因赛事结果公布时间调整，申请延长成果提交期限。' },
    members: [{ name: '陈思远', studentNo: '2023103058', college: '电子信息学院', major: '通信工程', isLeader: true }],
    attachments: [{ id: 'AC-A-05', name: '赛事延期通知.png', type: '图片', uploadedAt: '2026-07-13 11:02', description: '赛事主办方时间调整通知' }],
  },
  {
    id: 'AC-2026-004', title: '志愿服务课时学分兑换', source: 'task', type: 'credit_exchange', submittedAt: '2026-07-12 15:30', status: 'pending_acceptance', teacherStatus: 'confirmed',
    student: { name: '赵可欣', studentNo: '2022104107', college: '艺术学院', major: '视觉传达设计' },
    teacher: { name: '王芳', department: '艺术学院', opinion: '课时记录与兑换信息一致，确认通过。', confirmedAt: '2026-07-12 15:12' },
    application: { source: '任务成果申请', category: '志愿服务', requestedHours: 32, requestedCredits: 1, description: '申请将已认定的 32 个课时兑换为 1 个实践学分。' },
    members: [{ name: '赵可欣', studentNo: '2022104107', college: '艺术学院', major: '视觉传达设计', isLeader: true }],
    attachments: [{ id: 'AC-A-06', name: '团队学分分配表.xlsx', type: 'Excel', uploadedAt: '2026-07-12 14:38', description: '团队成员学分分配明细' }],
  },
])

export function getAcceptanceTypeText(type) {
  return acceptanceTypeOptions.find((option) => option.value === type)?.label ?? type
}

export function getApplicationSourceText(source) {
  return { self: '学生自主申请', task: '任务成果申请' }[source] ?? source
}

export function getAdminAcceptance(id) {
  return adminAcceptances.value.find((item) => item.id === id)
}
