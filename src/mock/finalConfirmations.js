import { ref } from 'vue'

export const finalConfirmations = ref([
  {
    id: 'FC-2026-001', title: '校园志愿服务项目成果', source: 'self', status: 'pending_final_confirmation', originalHours: 16, recognizedHours: 16, reviewResult: 'approved', reviewedAt: '2026-07-16 09:20',
    student: { name: '李晓雨', studentNo: '2023101001', college: '计算机学院', major: '软件工程' }, reviewer: { name: '刘老师', opinion: '成果完整，同意认定 16 课时。' }, teacher: { name: '张明', opinion: '成果材料与活动记录一致，确认通过。' }, acceptanceOpinion: '材料完整，同意受理。',
    application: { category: '志愿服务', description: '团队完成校园志愿服务周相关工作。' }, members: [{ name: '李晓雨', studentNo: '2023101001', college: '计算机学院', major: '软件工程', isLeader: true }, { name: '周然', studentNo: '2023101022', college: '计算机学院', major: '软件工程', isLeader: false }],
    attachments: [{ id: 'FC-A-01', name: '志愿服务成果报告.pdf', type: 'PDF', uploadedAt: '2026-07-15 09:26', description: '项目过程及成果汇总' }, { id: 'FC-A-02', name: '团队成员承诺书.docx', type: 'Word', uploadedAt: '2026-07-15 09:28', description: '团队成员签字确认材料' }],
    timeline: [{ title: '学生提交申请', time: '2026-07-15 09:30' }, { title: '指导老师确认通过', time: '2026-07-15 10:05' }, { title: '管理员受理通过', time: '2026-07-15 14:20' }, { title: '审核老师审核通过', time: '2026-07-16 09:20' }],
  },
  {
    id: 'FC-2026-002', title: '创新创业项目成果复审', source: 'task', status: 'pending_final_confirmation', originalHours: 24, recognizedHours: 20, reviewResult: 'approved', reviewedAt: '2026-07-15 15:40',
    student: { name: '王晨', studentNo: '2022102036', college: '管理学院', major: '工商管理' }, reviewer: { name: '孙老师', opinion: '部分工作量重复，调整为 20 课时后通过。' }, teacher: { name: '李华', opinion: '补充成果内容完整，确认通过。' }, acceptanceOpinion: '符合复审受理条件。', application: { category: '创新创业', description: '补充商业计划书及项目路演证明。' }, members: [{ name: '王晨', studentNo: '2022102036', college: '管理学院', major: '工商管理', isLeader: true }], attachments: [{ id: 'FC-A-03', name: '最终成果文件.pdf', type: 'PDF', uploadedAt: '2026-07-14 16:12', description: '项目最终成果汇总' }], timeline: [{ title: '学生提交申请', time: '2026-07-14 16:20' }, { title: '指导老师确认通过', time: '2026-07-14 16:55' }, { title: '管理员受理通过', time: '2026-07-14 17:40' }, { title: '审核老师调整课时并通过', time: '2026-07-15 15:40' }],
  },
  {
    id: 'FC-2026-003', title: '社会实践成果复审申请', source: 'self', status: 'pending_final_confirmation', originalHours: 16, recognizedHours: 0, reviewResult: 'rejected', reviewedAt: '2026-07-14 11:10',
    student: { name: '赵可欣', studentNo: '2022104107', college: '艺术学院', major: '视觉传达设计' }, reviewer: { name: '刘老师', opinion: '材料不足以证明实际参与时长，建议驳回。' }, teacher: { name: '王芳', opinion: '已确认学生补充说明。' }, acceptanceOpinion: '符合复审受理条件。', application: { category: '社会实践', description: '申请复审社会实践成果认定。' }, members: [{ name: '赵可欣', studentNo: '2022104107', college: '艺术学院', major: '视觉传达设计', isLeader: true }], attachments: [], timeline: [{ title: '学生提交复审', time: '2026-07-12 10:00' }, { title: '指导老师确认', time: '2026-07-12 13:30' }, { title: '管理员受理', time: '2026-07-13 09:10' }, { title: '审核老师驳回', time: '2026-07-14 11:10' }],
  },
])

export function getFinalSourceText(source) { return { self: '学生自主申请', task: '任务成果申请' }[source] ?? source }
export function getFinalConfirmation(id) { return finalConfirmations.value.find((item) => item.id === id) }

