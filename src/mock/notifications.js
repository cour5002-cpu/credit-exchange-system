export const NOTIFICATION_TYPES = Object.freeze({ task: '任务通知', application: '课时申请', exchange: '学分兑换', appeal: '申诉通知', complaint: '投诉通知', extension: '延期通知', system: '系统通知' })

const baseTime = ['2026-07-22 16:30','2026-07-22 15:20','2026-07-22 14:10','2026-07-22 11:40','2026-07-21 17:25','2026-07-21 14:30','2026-07-20 16:00','2026-07-20 10:15','2026-07-19 15:45','2026-07-18 13:20','2026-07-17 09:30']
const rows = [
  ['student','2024001','报名结果通知','你已成功报名“校园数据分析项目”，请等待指导老师筛选。','task','task','TASK-003'],
  ['student','2024001','任务筛选结果通知','你已被选中参与任务，请查看团队信息。','task','task','TASK-003'],
  ['student','2024001','队长指定通知','你已被指定为任务队长，可按要求上传任务成果。','task','task','TASK-003'],
  ['student','2024001','课时申请状态更新','你的课时申请已进入审核老师审核环节。','application','application','APP-003'],
  ['student','2024001','待补交成果提醒','无成果申请已由指导老师确认，请在预计时间前补交成果。','application','application','APP-004'],
  ['student','2024001','延期申请处理结果','普通延期申请已通过，请按新的截止时间补交成果。','extension','extension','APP-004'],
  ['student','2024001','课时到账通知','你的课时申请已最终确认，认定课时已到账。','application','application','APP-003'],
  ['student','2024001','学分兑换状态更新','指导老师已确认学分兑换申请，等待管理员最终确认。','exchange','exchange','EX-001'],
  ['student','2024001','学分到账通知','学分兑换已完成，兑换学分已到账。','exchange','exchange','EX-001'],
  ['student','2024001','申诉处理结果','管理员已最终确认申诉结果，请查看申诉详情。','appeal','appeal','APL-001'],
  ['student','2024001','匿名投诉已提交','投诉已提交至管理员端，当前等待处理。','complaint','complaint','CMP-001'],
  ['advisor','T001','新的课时申请待确认','张三提交了新的课时认定申请。','application','application','APP-001'],
  ['advisor','T001','新的无成果申请待确认','收到一条无成果课时申请，请完成首次确认。','application','application','APP-004'],
  ['advisor','T001','补交成果待再次确认','学生已补交成果材料，请进行再次确认。','application','application','APP-004'],
  ['advisor','T001','普通延期申请待确认','学生提交了普通延期申请。','extension','extension','APP-004'],
  ['advisor','T001','任务成果待确认','队长已上传任务成果，请进行成果确认。','task','task','TASK-003'],
  ['advisor','T001','学分兑换待确认','收到新的团队学分兑换申请。','exchange','exchange','EX-001'],
  ['advisor','T001','任务发布处理结果','管理员已确认发布任务，任务现已发布。','task','task','TASK-003'],
  ['advisor','T001','学生报名提醒','有学生报名了你发布的任务。','task','task','TASK-003'],
  ['reviewer','reviewer001','新的课时申请审核任务','管理员已向你分配一条课时申请审核任务。','application','application','APP-003'],
  ['reviewer','reviewer001','新的申诉复审任务','管理员已向你分配一条申诉复审任务。','appeal','appeal','APL-001'],
  ['reviewer','reviewer001','最终确认结果通知','管理员已最终确认你审核的课时申请。','application','application','APP-003'],
  ['reviewer','reviewer001','系统维护通知','系统将于本周末进行例行维护。','system','',''],
  ['admin','ADMIN001','新的任务发布待确认','指导老师提交了新的任务发布申请。','task','task','TASK-001'],
  ['admin','ADMIN001','新的课时申请待分配','有课时申请等待分配审核老师。','application','application','APP-003'],
  ['admin','ADMIN001','新的课时申请待最终确认','审核老师已完成审核，请进行最终确认。','application','application','APP-003'],
  ['admin','ADMIN001','新的学分兑换待最终确认','有学分兑换申请等待最终确认。','exchange','exchange','EX-001'],
  ['admin','ADMIN001','新的特殊延期申请','学生提交了特殊延期申请，请审核。','extension','extension','APP-004'],
  ['admin','ADMIN001','新的申诉待处理','学生提交了新的课时认定申诉。','appeal','appeal','APL-001'],
  ['admin','ADMIN001','申诉待分配复审老师','申诉已受理，请分配复审老师。','appeal','appeal','APL-001'],
  ['admin','ADMIN001','申诉复审结果待最终确认','审核老师已完成申诉复审。','appeal','appeal','APL-001'],
  ['admin','ADMIN001','新的投诉待处理','收到一条新的匿名投诉。','complaint','complaint','CMP-001'],
]
const notifications = rows.map((row, index) => ({ notificationId: `NTF-${String(index + 1).padStart(3, '0')}`, receiverRole: row[0], receiverId: row[1], title: row[2], content: row[3], type: row[4], relatedBizType: row[5], relatedBizId: row[6], isRead: index % 4 === 0, createTime: baseTime[index % baseTime.length] }))

function nowText(){const date=new Date();const pad=(value)=>String(value).padStart(2,'0');return`${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`}
export function getNotificationsByUser(role,userId){return notifications.filter((item)=>item.receiverRole===role&&item.receiverId===userId).sort((a,b)=>b.createTime.localeCompare(a.createTime))}
export function getUnreadCount(role,userId){return getNotificationsByUser(role,userId).filter((item)=>!item.isRead).length}
export function getNotificationById(notificationId){return notifications.find((item)=>item.notificationId===notificationId)}
export function markNotificationRead(notificationId){const item=getNotificationById(notificationId);if(!item)return null;item.isRead=true;return item}
export function markAllNotificationsRead(role,userId){const items=getNotificationsByUser(role,userId);items.forEach((item)=>{item.isRead=true});return items.length}
export function addNotification(data){if(!data?.receiverRole||!data?.receiverId||!data?.title)return null;const item={notificationId:data.notificationId||`NTF-${Date.now()}`,receiverRole:data.receiverRole,receiverId:data.receiverId,title:data.title,content:data.content||'',type:data.type||'system',relatedBizType:data.relatedBizType||'',relatedBizId:data.relatedBizId||'',isRead:false,createTime:data.createTime||nowText()};notifications.push(item);return item}
