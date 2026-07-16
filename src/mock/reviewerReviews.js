import { ref } from 'vue'

export const reviewTypeOptions = [
  { value: 'project_result', label: '项目成果审核' },
  { value: 'appeal_recheck', label: '申诉复审' },
]

export const reviewerReviews = ref([
  {
    id: 'RV-2026-001', title: '校园志愿服务项目成果', type: 'project_result', source: 'self', acceptedAt: '2026-07-15 14:20', status: 'pending_review', recognizedHours: 16, reviewOpinion: '', reviewedAt: '',
    student: { name: '李晓雨', studentNo: '2023101001', college: '计算机学院', major: '软件工程' },
    teacher: { name: '张明', department: '计算机学院', opinion: '成果材料与团队活动记录一致，确认通过。' },
    adminOpinion: '申请材料完整，同意受理并分配成果审核。',
    application: { category: '志愿服务', requestedHours: 16, description: '团队完成新生引导、场地秩序维护和活动资料整理。' },
    members: [{ name: '李晓雨', studentNo: '2023101001', college: '计算机学院', major: '软件工程', isLeader: true }, { name: '周然', studentNo: '2023101022', college: '计算机学院', major: '软件工程', isLeader: false }],
    attachments: [{ id: 'RV-A-01', name: '志愿服务成果报告.pdf', type: 'PDF', uploadedAt: '2026-07-15 09:26', description: '项目过程及成果汇总' }, { id: 'RV-A-02', name: '活动照片.zip', type: '压缩包', uploadedAt: '2026-07-15 09:28', description: '活动现场和成果照片' }],
  },
  {
    id: 'RV-2026-002', title: '创新创业项目成果复审申请', type: 'appeal_recheck', source: 'task', acceptedAt: '2026-07-14 17:40', status: 'pending_review', recognizedHours: 20, reviewOpinion: '', reviewedAt: '',
    student: { name: '王晨', studentNo: '2022102036', college: '管理学院', major: '工商管理' },
    teacher: { name: '李华', department: '管理学院', opinion: '补充成果能够说明项目完成情况，确认通过。' },
    adminOpinion: '申诉材料符合复审条件，同意受理。',
    application: { category: '创新创业', requestedHours: 24, description: '对首次成果认定课时提出申诉，并补充商业计划书和路演证明。' },
    members: [{ name: '王晨', studentNo: '2022102036', college: '管理学院', major: '工商管理', isLeader: true }],
    attachments: [{ id: 'RV-A-03', name: '申诉复审说明.docx', type: 'Word', uploadedAt: '2026-07-14 16:12', description: '申诉理由及课时计算说明' }, { id: 'RV-A-04', name: '项目路演证明.pdf', type: 'PDF', uploadedAt: '2026-07-14 16:15', description: '项目路演参与和获奖证明' }],
  },
  {
    id: 'RV-2026-003', title: '学科竞赛项目成果', type: 'project_result', source: 'task', acceptedAt: '2026-07-10 10:30', status: 'approved', recognizedHours: 32, reviewOpinion: '成果真实完整，认定 32 课时。', reviewedAt: '2026-07-11 09:15',
    student: { name: '陈思远', studentNo: '2023103058', college: '电子信息学院', major: '通信工程' }, teacher: { name: '陈强', department: '校团委', opinion: '竞赛成果信息属实，确认通过。' }, adminOpinion: '材料齐全，同意受理。', application: { category: '学科竞赛', requestedHours: 32, description: '参加省级学科竞赛并获得二等奖。' }, members: [{ name: '陈思远', studentNo: '2023103058', college: '电子信息学院', major: '通信工程', isLeader: true }], attachments: [{ id: 'RV-A-05', name: '获奖证书.pdf', type: 'PDF', uploadedAt: '2026-07-09 15:20', description: '省级竞赛二等奖证书' }],
  },
  {
    id: 'RV-2026-004', title: '社会实践成果复审申请', type: 'appeal_recheck', source: 'self', acceptedAt: '2026-07-08 13:20', status: 'rejected', recognizedHours: 0, reviewOpinion: '补充材料仍不足以证明实际参与时长。', reviewedAt: '2026-07-09 16:40',
    student: { name: '赵可欣', studentNo: '2022104107', college: '艺术学院', major: '视觉传达设计' }, teacher: { name: '王芳', department: '艺术学院', opinion: '已核对学生提交的补充说明。' }, adminOpinion: '符合申诉受理条件。', application: { category: '社会实践', requestedHours: 16, description: '申请复审社会实践成果认定。' }, members: [{ name: '赵可欣', studentNo: '2022104107', college: '艺术学院', major: '视觉传达设计', isLeader: true }], attachments: [],
  },
])

export function getReviewTypeText(type) { return reviewTypeOptions.find((option) => option.value === type)?.label ?? type }
export function getReviewSourceText(source) { return { self: '学生自主申请', task: '任务成果申请' }[source] ?? source }
export function getReviewerReview(id) { return reviewerReviews.value.find((item) => item.id === id) }

