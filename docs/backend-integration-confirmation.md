下面内容可以直接发送给前端。

# V1 接口联调确认回复

后端已根据前后端接口差距完成检查，并针对任务成果重提、报名截止状态和申诉终态进行了补充修改。当前结论如下。

## 1. 已实现及可开始联调的接口

以下模块已经实现，可以开始联调：

- Session Cookie 登录、退出、当前用户信息。
- 任务类型、指导老师、审核老师查询。
- 附件上传、下载和删除/作废。
- 学生课时申请：有成果、无成果、草稿、列表和详情。
- 无成果补交及指导老师再次确认。
- 普通延期和特殊延期。
- 课时申请完整审核流程。
- 学分兑换完整流程及管理员批量终审。
- 学生申诉、管理员受理、指导老师再确认、审核老师复审和管理员终审。
- 管理员及指导老师任务发布。
- 学生任务报名、指导老师筛选、指定队长。
- 任务成果提交、驳回重提和转课时认定。
- 投诉基础版：学生匿名提交、管理员列表和查看。
- 操作记录查询。

暂未实现：

- 通知列表、通知详情、单条已读、全部已读。
- 完整投诉处理。
- 首页统计、数据看板。

后端完整自动化测试结果：

```text
Ran 20 tests
OK
```

## 2. 状态流转确认

### 课时申请

```text
draft
→ submitted
→ pending_assignment
→ pending_review
→ pending_admin_final
→ final_approved
```

可能的驳回状态：

```text
advisor_rejected
reviewer_rejected
final_rejected
```

### 无成果补交

```text
draft
→ submitted
→ pending_material
→ material_submitted
→ pending_assignment
→ pending_review
→ pending_admin_final
→ final_approved
```

可能进入：

```text
extension_requested
extension_admin_review
material_overdue
```

### 延期申请

延期记录：

```text
submitted → approved / rejected / closed
```

课时申请相应回到：

```text
pending_material
```

如果延期驳回时原截止时间已过，则进入：

```text
material_overdue
```

### 任务及报名

管理员发布：

```text
draft → published
```

指导老师发布：

```text
draft
→ pending_publish_review
→ published / publish_rejected
```

任务执行：

```text
published
→ selection_pending
→ leader_pending
→ task_in_progress
→ result_submitted
→ result_approved
```

报名记录：

```text
submitted → selected / not_selected
```

确认口径：

```text
任务发布者填写 registration_deadline
→ 截止时间前允许报名
→ 到期后报名接口拒绝报名
→ 后端自动将任务推进到 selection_pending
→ 指导老师开始筛选
```

报名截止前不允许指导老师提前筛选，后端返回 HTTP 409。

“提前结束报名”暂不支持，可作为后续优化功能。

### 任务成果

```text
submitted
→ advisor_rejected
→ submitted
→ converted_to_hour_application
```

成果被驳回后，队长使用重提接口修改原成果，不创建第二条成果主记录。

每次提交和重提都会新增版本快照。

### 学分兑换

```text
draft
→ submitted
→ pending_admin_final
→ final_approved
```

可能进入：

```text
advisor_rejected
final_rejected
```

不存在 `pending_distribution_confirm`。

### 申诉

申诉总状态：

```text
pending_admin_review
→ processing
→ completed
```

其中 `reopen_stage` 用于表示处理中的具体环节：

```text
pending_advisor_confirmation
→ pending_assignment
→ pending_reviewer_review
→ pending_admin_final
→ completed
```

管理员不受理、指导老师重审驳回、审核老师复审驳回或管理员完成原业务终审后，申诉均进入 `completed`。

### 投诉

当前仅支持：

```text
submitted → viewed
```

暂不支持正式的 `processed` 状态。

## 3. 任务发布字段确认

| 前端字段 | 后端结论 |
|---|---|
| `hours` / `requested_hours` | 任务发布暂不支持；队长提交成果时使用 `requested_hours` |
| `resultRequirement` | 不支持该驼峰字段 |
| `result_requirement` | 支持 |
| `requirement` | 支持 |
| `registrationStartTime` | 不支持前端指定 |
| `registration_start_at` | 后端发布或审批通过时自动生成 |
| `registration_deadline` | 支持，必填 |
| `maxParticipants` | 暂不支持 |
| `material_due_at` | 任务发布暂不支持 |

任务发布建议请求格式：

```json
{
  "title": "任务名称",
  "description": "任务说明",
  "task_type_id": 1,
  "advisor_teacher_id": 2,
  "result_requirement": "成果要求",
  "registration_deadline": "2026-08-10T18:00:00"
}
```

`advisor_teacher_id` 仅管理员发布任务时需要；指导老师发布时由登录用户自动确定。

## 4. `TaskResultSubmission.status` 枚举

当前完整枚举：

- `submitted`：成果已提交，等待指导老师确认。
- `advisor_rejected`：指导老师驳回，可修改后重提。
- `converted_to_hour_application`：指导老师确认通过，已进入课时认定流程。

前端不要使用 `material_submitted` 作为 `TaskResultSubmission.status`。

`material_submitted` 是关联的 `HourApplication.status`。

## 5. 任务成果如何进入课时申请

首次提交成果：

```http
POST /api/v1/student/tasks/{task_id}/result-submissions
```

请求示例：

```json
{
  "summary": "成果说明",
  "requested_hours": 20,
  "attachment_ids": [1, 2]
}
```

调用该接口时，后端会自动创建关联的课时申请。学生不需要再调用普通课时申请接口。

指导老师通过：

```http
POST /api/v1/advisor/task-result-submissions/{submission_id}/approve
```

通过后关联课时申请自动进入：

```text
pending_assignment
```

## 6. 成果驳回重提接口

新增接口：

```http
POST /api/v1/student/task-result-submissions/{submission_id}/resubmit
```

请求示例：

```json
{
  "summary": "修改后的成果说明",
  "requested_hours": 18,
  "attachment_ids": [10, 11]
}
```

限制：

- 只能由任务队长操作。
- 当前成果状态必须是 `advisor_rejected`。
- 当前任务状态必须是 `task_in_progress`。
- 必须重新提交附件。
- 修改原成果和原课时申请，不创建重复的课时申请。

重提成功后：

```text
TaskResultSubmission.status = submitted
HourApplication.status = material_submitted
CollegeTask.status = result_submitted
```

指导老师查看成果详情时，响应中新增：

```json
{
  "versions": [
    {
      "version_no": 1,
      "summary": "首次提交内容",
      "requested_hours": 20,
      "attachment_ids": [1],
      "submitted_at": "..."
    },
    {
      "version_no": 2,
      "summary": "修改后的内容",
      "requested_hours": 18,
      "attachment_ids": [10, 11],
      "submitted_at": "..."
    }
  ]
}
```

顶层 `attachments` 只返回当前最新版本附件。

## 7. 申诉流程确认

当前后端流程仍然保留指导老师再次确认：

```text
学生申诉
→ 管理员受理
→ 指导老师再次确认
→ 管理员分配复审老师
→ 审核老师复审
→ 管理员最终确认
```

所以前端必须保留指导老师再次确认页面和操作。

申诉总状态已统一为：

- `pending_admin_review`
- `processing`
- `completed`

具体待办环节请结合 `reopen_stage` 判断。

## 8. 投诉支持情况

| 字段/能力 | 是否支持 |
|---|---|
| `content` | 支持 |
| `attachment_ids` | 支持 |
| `complaint_type` | 暂不支持 |
| `target_type` | 暂不支持 |
| `target_id` | 暂不支持 |
| 管理员处理意见 | 暂不支持 |
| `processed` | 暂不支持 |
| `viewed` | 支持 |

当前投诉接口：

```http
POST /api/v1/student/complaints
GET /api/v1/admin/complaints
GET /api/v1/admin/complaints/{complaint_id}
```

管理员查看详情后，投诉自动从 `submitted` 变为 `viewed`。

## 9. 通知接口

以下接口目前均未实现：

```http
GET  /api/v1/notifications
GET  /api/v1/notifications/{id}
POST /api/v1/notifications/{id}/read
POST /api/v1/notifications/read-all
```

前端现阶段请继续使用 Mock，或暂时隐藏通知已读操作。

## 10. 学分兑换状态

确认不增加：

```text
pending_distribution_confirm
```

前端应移除该状态，直接使用：

```text
final_approved
```

表示学分兑换已完成。

# 本次后端修改点

1. 增加成果驳回重提接口。
2. 增加任务成果版本表。
3. 首次成果提交和每次重提均保存版本快照。
4. 重提时同步更新原课时申请，不重复创建申请。
5. 报名截止后自动推进到 `selection_pending`。
6. 报名截止前禁止筛选。
7. 增加前端可使用的 `can_resubmit_result`。
8. 任务团队信息返回 `task_result_submission_id`。
9. 申诉状态统一为 `pending_admin_review / processing / completed`。
10. 原课时申请或学分兑换完成终审后，同步完成关联申诉。
11. 新增数据库迁移，兼容旧成果和旧申诉状态。
12. 学分兑换状态不变，不增加分配确认阶段。

# 联调问题

采用cpolar内网穿透的方式

最推荐的方案是只穿透前端，让前端开发服务器把 `/api` 代理到本地后端：

```text
浏览器
→ https://前端地址.cpolar...
→ 前端开发服务器
   └─ /api → http://127.0.0.1:5000
```

浏览器看到前端和 API 是同一个域名，此时：

- 后端不需要配置 CORS。
- Session Cookie 属于前端 cpolar 域名。
- 前端请求仍建议设置 `credentials: "include"`。
- 这是联调最稳定的方案。

例如前端代理：

```javascript
// vite.config.js
server: {
  proxy: {
    "/api": {
      target: "http://127.0.0.1:5000",
      changeOrigin: true
    }
  }
}
```

前端调用使用相对路径：

```javascript
fetch("/api/v1/auth/login", {
  method: "POST",
  credentials: "include"
})
```

不要写完整的后端 cpolar 地址。


注意：免费 cpolar 地址重启后可能变化；一旦前端地址变化，后端允许的 Origin 也要更新。
