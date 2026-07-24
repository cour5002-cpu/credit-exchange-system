# 前后端 API 差距分析

## 1. 分析范围与结论

分析基准：

- 后端契约：`docs/backend-api-v1.md`，基础路径为 `/api/v1`。
- 前端数据源：`src/mock/*.js`、`src/api/*.js`，以及实际页面目录 `src/views/**/*.vue`。
- 仓库当前不存在 `src/pages`；本文将 `src/views` 作为“当前前端页面”的实际实现目录。
- 本文比较的是“页面实际消费/提交的数据”与“后端契约已声明的数据”，不代表后端接口已经实现。实际可联调状态仍需查后端开发记录。

总体结论：当前页面除任务类别与导入模块只生成请求配置外，业务数据均直接读写内存 Mock，没有统一 HTTP 客户端、响应解包、分页、错误码和登录态处理。因此不能通过简单替换 base URL 完成联调。后端契约对绝大多数核心页面已有接口覆盖，但需要一层前端 DTO 适配；申诉、投诉处理、批量任务发布确认、通知已读等少数流程还需后端确认或补充契约。

## 2. 全局差异

| 类型 | 前端现状/实际需要 | 后端契约 | 影响与建议 |
|---|---|---|---|
| 数据调用 | 页面直接 import `src/mock` 函数并同步读写数组 | HTTP API，统一 `{code,message,data}` | 前端需建立 API/service 层、异步 loading/error 处理，并从 `data` 解包 |
| 分页 | Mock 返回完整数组，页面本地筛选 | 列表统一 `items/page/page_size/total/pages` | 前端列表需改为服务端分页并传查询条件 |
| 字段风格 | 大量 camelCase，如 `studentId`、`submitTime`、`requestedHours` | snake_case，如 `student_no`、`submitted_at`、`requested_hours` | 建议前端集中做 DTO 映射，不在模板内零散兼容 |
| 主键 | 前端多用字符串业务号作路由 ID，如 `APP-2026-001`、`TASK-*`、`APL-*` | Path `id` 为 integer，业务号另有 `application_no/task_no/appeal_no` | 页面路由应保存后端整数 `id`；展示业务号使用对应 `*_no` |
| 时间 | `YYYY-MM-DD HH:mm`，表单日期有仅日期字符串 | ISO 8601 带时区 | 前端需统一解析/格式化，提交截止时间需明确时区 |
| 鉴权 | 页面写死当前用户/审核人，如 `stu001`、`reviewer001`，未发现真实登录请求 | Flask-Login session/cookie；除登录及公开规则文件外均需登录，角色路径必须匹配 | 请求必须携带 cookie（跨域时 `credentials: 'include'`）；用户与角色来自 `/me`，禁止由页面传当前用户 ID 代替鉴权 |
| 状态权限 | 前端依赖本地状态常量决定按钮 | 后端状态校验，错误码 `40901`；详情含 `actions` | 前端应以服务端 `actions` 为按钮权限主来源，并处理 409，而非只相信本地状态 |
| 附件 | 页面/Mock 保存 `File` 或 `{id,name,type,size,uploadedAt,mockUrl,description}` | 先 `POST /attachments`，业务提交仅传 `attachment_ids`；响应 `file_name/file_size/mime_type/url/...` | 必须实现上传队列、附件 ID 回填、预览/下载、删除；本地 blob/mockUrl 不能直接提交 |
| 列表接口 | 页面常将不同业务合并成一个“待确认/待受理”列表 | 契约按课时、成果、延期、兑换分别提供接口 | 前端聚合页需并发调用多个接口并统一展示，或后端确认是否提供聚合接口 |

## 3. 按业务模块对比

### 3.1 登录、当前用户、基础数据

| 前端实际需要 | 后端接口 | 差异 | 判定 |
|---|---|---|---|
| 登录后获得用户、主角色并进入对应工作台 | `POST /auth/login`、`GET /me`、`POST /auth/logout` | 当前 `LoginView` 未接真实 API；需处理 session cookie。角色值后端为 `student/advisor/reviewer/admin`，前端路由中的“teacher”语义应映射为 `advisor` | 需要前端适配 |
| 课时申请/任务发布使用任务类别 | `GET /task-types`；管理员 CRUD `/admin/task-types` | `src/api/taskTypes.js` 路径与方法基本一致；字段仍需按契约的 `id/name/code/status`（以接口条目为准）接入 | 可直接对接（经通用响应解包） |
| 指导老师选择、审核老师分配 | `GET /teachers/advisors`、`GET /admin/reviewers` | 前端使用 `{id,name,department}` 或 `{reviewerId,reviewerName,college,direction,pendingCount}`；后端使用 `TeacherSummary`，无 `direction/pendingCount` 保证 | 需要前端适配；扩展字段需后端确认 |

### 3.2 课时申请、审核与最终确认

后端已覆盖创建草稿、提交、学生列表/详情、指导老师确认、管理员待分配、审核老师审核、管理员最终确认、成果补交、延期和关闭。路径总体可满足页面流程。

主要字段映射：

| 前端字段 | 后端字段 | 差异 |
|---|---|---|
| `id/applicationId`（字符串） | `id`（integer）+ `application_no` | 主键与展示编号混用 |
| `studentId/studentName` | `applicant.id/student_no/name`，另有 `applicant_name` | 前端扁平，后端嵌套 |
| `applyType: with_result/without_result` | `application_type: with_material/without_material/task_result` | 枚举名称和值不同，且任务成果需单独值 |
| `source: self/task` | `source_type: student_self/admin_task/teacher_task` | 后端区分任务发布来源 |
| `requestedHours/recognizedHours/originalHours` | `requested_hours/final_hours/reviewer_suggested_hours` | 语义需逐一映射，不能仅改大小写 |
| `mainAdvisor/viewAdvisors` | `advisors[].teacher/advisor_role/can_operate` | 后端为关系数组 |
| `members[].id/name/studentId/role` | `members[].student` + `is_leader/can_view/joined_at` | 嵌套及队长字段不同 |
| `advisorComment/reviewComment/finalComment/timelineEvents` | `reviews[]`、`assignments[]` | 前端多组阶段字段需从审核记录派生 |
| `expectedResultDate/newExpectedResultTime` | `material_due_at`、延期对象 `old_due_at/requested_due_at` | 延期是独立资源，不应直接改申请对象 |

状态差异：

- 前端存在 `pending_advisor`、`pending_admin_accept`、`admin_accepted`、`pending_reviewer`；后端接口流程使用 `submitted -> pending_assignment -> pending_review -> pending_admin_final`。其中前端“管理员受理并同时分配审核老师”应映射为后端 `/admin/hour-applications/{id}/assign-reviewer`，不存在独立 `admin_accepted` 状态。
- 前端 `reviewer_approved`、`reviewer_modified_approved` 应在操作成功后统一接收后端返回的 `pending_admin_final`，审核结论从 `reviews[].decision` 展示。
- 前端无成果流程同时出现 `pending_result/need_supplement_result/pending_material`；契约明确的精确课时状态引用另一份 `状态流转.md`，但本文输入未给出该文件的完整映射。联调前需后端确认每个接口的实际返回状态。
- 前端普通/特殊延期按“30 天以内/超过 30 天”本地计算并走 advisor/admin；契约有两套待审路径，但应确认后端是否采用同一阈值且由谁最终判定。

附件差异：申请附件、成果附件、延期证明目前都是文件对象数组；后端只接受 `attachment_ids`，且要求 `biz_type` 匹配 `hour_application` 或 `task_result`。页面提交前必须先上传。

### 3.3 学院任务、报名、队长与成果

后端已覆盖管理员/指导老师草稿与发布、任务广场、报名、筛选成员、指定队长、团队查看、成果提交及指导老师确认。

| 前端字段/动作 | 后端契约 | 差异 |
|---|---|---|
| `taskId`（字符串） | `id` integer + `task_no` | 路由主键需调整 |
| `taskType` | `task_type_id/task_type_name` | 前端当前常以文本/选项值保存 |
| `hours` | 成果提交的 `requested_hours`；任务摘要未声明固定课时字段 | 前端任务发布表单要求课时，契约是否允许任务预设课时需确认 |
| `resultRequirement` | `requirement`（另有 `description`） | 前端同时有 `requirement` 与 `resultRequirement`，后端只有一个成果要求字段 |
| `registrationStartTime`、`maxParticipants` | 契约摘要只保证 `registration_deadline` | 是否支持报名开始时间/人数上限需确认 |
| `resultDeadline` | `material_due_at` | 名称不同 |
| `applicants[].applyStatus: applied` | `registration.status: submitted` | 状态值不同 |
| 批量通过/驳回任务发布 | 仅单条 `/admin/task-publish-requests/{id}/approve|reject` | 前端已有批量操作，后端契约无批量接口；前端可逐条调用或后端补批量接口 |
| `taskResults` 独立 Mock，状态 `pending_advisor_result_confirm/...` | `TaskResultSubmission.status`，详情与 approve/reject 接口 | 字段需映射；状态具体枚举契约未完整列出 |

任务主状态也不一致：前端 `pending_admin_publish/selecting/selected/leader_assigned/in_progress/result_submitted/finished`，后端为 `pending_publish_review/selection_pending/leader_pending/task_in_progress/closed` 等。应由前端建立显示映射，并始终保存后端原始状态。

### 3.4 学分兑换

后端已覆盖可兑换课时、表单数据、草稿/提交、学生记录、指导老师确认、管理员最终确认及批量最终通过。

| 前端字段 | 后端字段 | 差异 |
|---|---|---|
| `applicationId/projectTitle/finalHours` | `hour_award_record_id`、`hour_application_id`、`hour_award` | 后端以到账记录为兑换来源，前端以申请对象为来源 |
| `exchangeId` | `id` + `exchange_no` | 主键混用 |
| `exchangeHours/estimatedCredits` | `total_hours/estimated_total_credits` | 命名不同 |
| `memberDistributions[].allocatedHours/allocatedCredits` | `allocations[].allocated_hours/allocated_credits/credit_type/remark` | 命名及字段完整度不同 |
| `creditRule.hoursPerCredit/text` | `ConversionRuleSummary` | 后端规则对象更完整 |
| `proofMaterials` | `attachments` / 提交 `attachment_ids` | 需先上传 |
| `hoursArrived/exchanged` | 由可兑换到账记录及业务状态表达 | 不应继续作为前端可写布尔值 |

状态不一致：前端 `pending_confirmation/pending_final_confirm/pending_distribution_confirm/completed`，后端为 `submitted/advisor_approved/pending_admin_final/final_approved/...`。前端额外的“成员分配确认后完成”阶段在后端契约中没有对应动作，需要确认是删除该阶段，还是补充接口。

批量最终通过可对接 `POST /admin/credit-exchanges/batch-approve`；前端批量驳回没有对应契约，只能逐条调用 `final-reject` 或由后端补充。

### 3.5 申诉

字段需从前端 `appealId/applicationId/studentId/appealReason/appealMaterials/submitTime` 映射到后端 `id/appeal_no/target_type/target_id/student/reason/attachments/submitted_at`。附件同样须先上传并提交 ID。

此模块存在流程级冲突，不能只做 DTO 适配：

- 前端：管理员受理后直接进入“分配复审老师” (`pending_review_assignment`) → 审核老师复审 → 管理员最终确认。
- 后端：管理员申诉通过 → 原业务回到指导老师再次确认 → 管理员再次分配 → 审核老师复审；契约列出了 `/advisor/appeals/{id}/reconfirm`。
- 前端管理员“最终确认申诉复审”的页面/动作存在，但第 8 节未列出明确的申诉最终确认专用接口；后端复审通过只返回原业务 `pending_admin_final`。需要确认应复用课时/兑换的最终确认接口，还是提供申诉最终确认接口。
- 前端 `pending_admin/admin_rejected/pending_re_review/re_review_approved/final_confirmed` 与后端 `submitted/pending_admin_review/appeal_accepted/appeal_rejected/original_reopened/closed` 不一致。

### 3.6 投诉

学生提交、管理员列表与详情已有接口，但前端需要 `complaintType`、关联申请、附件以及管理员填写处理意见并变为 `processed`。后端 V1 契约仅提交 `content + attachment_ids`，`ComplaintSummary` 虽有 `target_type/target_id`，提交请求未声明这两个字段；状态仅 `submitted/viewed`，并明确“管理员只查看，不做完整处理”。

因此提交的类型/关联对象是否保留、管理员 `processComplaint(comment)` 是否取消、详情是否返回附件，都需要后端确认。当前处理动作不能直接对接。

### 3.7 通知、工作台与处理记录

- 后端有 `GET /notifications` 和 `GET /notifications/{id}`，字段可通过映射对接：`notificationId/createTime/relatedBizType/relatedBizId` → `id/created_at/target_type/target_id`。
- 前端有单条已读、全部已读操作；后端契约没有“标记已读/全部已读”接口，需后端确认。仅查询可对接。
- 四角色 dashboard 接口均在契约中标记为 V1 后置；当前前端工作台还会聚合任务成果、延期、兑换、申诉等待办，后端概览字段未完全覆盖。第一轮可由前端并发请求各列表后计算，是否启用 dashboard 接口需按开发记录确认。
- `GET /operation-records` 与详情可覆盖老师/审核老师/管理员处理记录的主体需求；当前页面通过多个 Mock 集合自行拼接，需改成后端统一记录对象。管理员页面若要求任务、投诉等所有历史，需确认后端 `target` 联合类型和 `biz_type` 枚举。

## 4. 三类对接清单

### 4.1 可直接对接

“直接”指路径、方法和业务动作一致，仍需统一处理 cookie、响应外壳、分页和 snake_case。

- 登录、登出、当前用户：`POST /auth/login`、`POST /auth/logout`、`GET /me`。
- 任务类别查询与管理员单条 CRUD/启停：`/task-types`、`/admin/task-types...`。
- 管理员三类导入：`POST /admin/imports/students|teachers|admins`。注意模板正确路径是 `GET /admin/import-templates/{target}`。
- 附件上传、详情、删除：`POST /attachments`、`GET|DELETE /attachments/{id}`。
- 课时申请的学生提交/查询、指导老师确认、审核老师审核、管理员分配与最终确认的单条接口。
- 成果补交与延期的单条查询/处理接口。
- 任务广场、报名、成员筛选、指定队长、团队查询、成果提交与指导老师确认的单条接口。
- 学分兑换的可兑换来源、草稿/提交/查询、指导老师确认、管理员单条最终确认和批量最终通过。
- 申诉的学生提交/查询、管理员受理/驳回、审核老师复审查询与操作（仅单个动作层面；完整流程序列见“后端确认”）。
- 投诉提交、管理员列表/详情的只读 V1 能力。
- 通知列表/详情、处理记录列表/详情的查询能力。

### 4.2 需要前端适配

- 新增统一 API 客户端：base URL、`credentials: 'include'`、JSON/FormData、`code !== 0`、401/403/409、分页和取消重复请求。
- 将所有页面从同步 Mock 函数迁移为异步 service；增加 loading、空态、失败重试及提交防重复。
- 用 `/me` 替换写死的 `studentId/advisorId/reviewerId/adminId`，按后端角色控制路由。
- 建立 DTO 映射层：camelCase ↔ snake_case、扁平人员字段 ↔ `StudentSummary/TeacherSummary`、字符串业务号 ↔ integer `id`。
- 重写状态展示映射，以后端原始状态与详情 `actions` 为准；不要在前端自行推进服务端状态。
- 列表改为服务端分页；前端综合待办页并发调用各业务列表后合并。
- 实现附件“先上传、获 attachment ID、再提交业务”的流程，并使用后端 `url` 预览/下载。
- 任务类别导入模板路径从当前 `/admin/imports/{type}/template` 改为 `/admin/import-templates/{target}`。
- 任务发布批量通过/驳回若不补后端接口，前端改为逐条调用并汇总部分失败。
- 学分兑换批量驳回若不补接口，前端改为逐条 `final-reject`。
- 处理记录页改用 `/operation-records`，停止从多个业务 Mock 拼接历史。

### 4.3 需要后端确认

1. 契约是“计划提供”而非实现清单：本次列为可对接的接口，哪些已实现并可联调？尤其是文档明确后置的 dashboard、通知与统计。
2. 课时申请完整状态枚举及与前端现有状态的映射，尤其无成果补交、普通/特殊延期、指导老师通过后到管理员分配之间的状态。
3. 任务发布是否支持前端必填的 `hours`、`resultRequirement`、`registrationStartTime`、`maxParticipants`；若支持，请补充请求/响应字段。
4. 任务成果 `TaskResultSubmission.status` 的完整枚举，以及成果通过后创建课时申请的准确入口与状态。
5. 任务发布批量通过/驳回是否需要后端批量接口。
6. 学分兑换是否存在前端 `pending_distribution_confirm -> completed` 的成员分配确认阶段；如不存在，前端应删除。批量驳回是否补接口。
7. 申诉必须确认最终流程：管理员通过后是否强制指导老师 `reconfirm`；管理员最终确认复审结果应复用哪个接口；不同 `target_type` 的最终确认路径如何选择。
8. 投诉提交是否接受 `target_type/target_id/complaint_type`，投诉详情是否返回附件；V1 是否明确取消管理员处理意见与 `processed` 状态。
9. 通知是否补 `mark-read` 和 `mark-all-read` 接口；否则 `is_read` 无法由当前前端操作持久化。
10. 老师/审核人列表是否提供页面需要的 `direction`、实时 `pending_count`；若不提供，前端应移除或另取数据。
11. 附件上传的 multipart 字段名、允许类型/大小、业务提交失败后的孤立附件清理策略，以及 `url` 是否要求登录、是否支持预览与 `Content-Disposition` 下载。
12. 前后端跨域部署时 session cookie 的 `SameSite/Secure/CORS credentials` 配置；未登录与过期是否始终返回 HTTP 401 + 业务码 `40101`。

## 5. 建议联调顺序

1. 先打通登录、`/me`、统一响应与 cookie。
2. 打通任务类别、老师列表、附件上传三个公共依赖。
3. 按“课时申请 → 指导老师 → 管理员分配 → 审核老师 → 管理员最终确认”完成一条闭环。
4. 再接任务/成果、延期、学分兑换。
5. 申诉在流程问题确认后接入；投诉、通知、dashboard 按 V1 实现范围最后处理。

