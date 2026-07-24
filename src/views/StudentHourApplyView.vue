<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AttachmentNotice from '../components/AttachmentNotice.vue'
import MemberInputTable from '../components/MemberInputTable.vue'
import StageDescription from '../components/StageDescription.vue'
import { addApplication, getApplications } from '../mock/applications.js'
import { getApprovedTaskResultsForStudent, markTaskResultApplicationCreated } from '../mock/taskResults.js'
import { getTaskById } from '../mock/tasks.js'

const router = useRouter()

// Mock 当前登录学生信息，接入登录接口后替换此处即可。
const currentUser = {
  id: 'stu001',
  name: '张三',
  studentId: '2024001',
  college: '计算机学院',
  major: '数据科学与大数据技术',
}

const teachers = [
  { id: 'T001', name: '张明', department: '计算机学院' },
  { id: 'T002', name: '李华', department: '管理学院' },
  { id: 'T003', name: '王芳', department: '艺术学院' },
  { id: 'T004', name: '陈强', department: '校团委' },
  { id: 'T005', name: '赵敏', department: '创新创业学院' },
]

function createCurrentUserMember() {
  return {
    id: currentUser.id,
    name: currentUser.name,
    studentNo: currentUser.studentId,
    college: currentUser.college,
    major: currentUser.major,
    isLeader: true,
  }
}

const form = reactive({
  title: '',
  source: 'student',
  taskId: '',
  requestedHours: '',
  applicationType: 'with_result',
  primaryTeacherId: '',
  observerTeacherIds: [],
  expectedResultDate: '',
  members: [createCurrentUserMember()],
})

const feedback = ref({ type: '', message: '' })
const observerPanelExpanded = ref(false)
const observerSearch = ref('')
const taskResultVersion = ref(0)
const approvedTaskResults = computed(() => {
  taskResultVersion.value
  const unavailableResultIds = new Set(getApplications()
    .filter((item) => item.resultId && !['advisor_rejected', 'reviewer_rejected', 'final_rejected', 'cancelled'].includes(item.status))
    .map((item) => item.resultId))
  return getApprovedTaskResultsForStudent(currentUser.studentId)
    .filter((result) => !unavailableResultIds.has(result.resultId))
})
const selectedTask = computed(() => {
  const result = approvedTaskResults.value.find((item) => item.resultId === form.taskId)
  if (!result) return null
  const sourceTask = getTaskById(result.taskId)
  return { ...result, id: result.resultId, title: result.taskTitle, publisher: `${result.advisorName}老师`, hours: result.hours || result.taskHours || sourceTask?.hours || 0, captainId: result.leaderId, members: result.teamMembers }
})
const selectedTaskCaptain = computed(() =>
  selectedTask.value?.members.find((member) => member.id === selectedTask.value.captainId) ?? null,
)
const isSelectedTaskMember = computed(() =>
  Boolean(selectedTask.value?.members.some((member) => member.studentId === currentUser.studentId)),
)
const isSelectedTaskCaptain = computed(() =>
  Boolean(selectedTask.value && selectedTask.value.captainId === currentUser.studentId),
)
const isSelfApplicationLeader = computed(() =>
  form.members.some((member) => member.id === currentUser.id && member.isLeader),
)
const permissionState = computed(() => {
  if (form.source === 'student') {
    return isSelfApplicationLeader.value
      ? { allowed: true, message: '学生自主申请由当前学生作为队长提交。' }
      : { allowed: false, message: '学生自主申请必须由当前登录学生作为队长提交。' }
  }
  if (!selectedTask.value) return { allowed: false, message: '请先选择关联任务。' }
  if (!isSelectedTaskMember.value) {
    return { allowed: false, message: '你不是该任务成员，不能提交该任务的课时申请。' }
  }
  return { allowed: true, message: isSelectedTaskCaptain.value ? '你是该任务队长，可以提交课时申请。' : '你是该任务成员，可以基于已确认成果提交课时申请。' }
})
const canSubmitApplication = computed(() => permissionState.value.allowed)
const observerTeacherOptions = computed(() =>
  teachers.filter((teacher) => teacher.id !== form.primaryTeacherId),
)
const filteredObserverTeachers = computed(() => {
  const keyword = observerSearch.value.trim().toLowerCase()
  if (!keyword) return observerTeacherOptions.value

  return observerTeacherOptions.value.filter((teacher) =>
    [teacher.name, teacher.department, teacher.major]
      .filter(Boolean)
      .some((value) => value.toLowerCase().includes(keyword)),
  )
})
const selectedObserverNames = computed(() =>
  form.observerTeacherIds
    .map((id) => teachers.find((teacher) => teacher.id === id)?.name)
    .filter(Boolean),
)

function handlePrimaryTeacherChange() {
  form.observerTeacherIds = form.observerTeacherIds.filter((id) => id !== form.primaryTeacherId)
}

function isObserverDisabled(teacherId) {
  if (form.observerTeacherIds.includes(teacherId)) return false
  const maximumObservers = form.primaryTeacherId ? 2 : 3
  return form.observerTeacherIds.length >= maximumObservers
}

function handleSourceChange() {
  form.taskId = ''
  form.requestedHours = ''
  form.members = form.source === 'student' ? [createCurrentUserMember()] : []
  feedback.value = { type: '', message: '' }
}

function handleTaskChange() {
  form.requestedHours = selectedTask.value?.hours ?? ''
  form.applicationType = 'with_result'
  form.primaryTeacherId = selectedTask.value?.advisorId ?? ''
  if (selectedTask.value) form.title = `${selectedTask.value.taskTitle}课时申请`
  handlePrimaryTeacherChange()
  feedback.value = { type: '', message: '' }
}

function validateForm() {
  if (!form.title.trim()) return '请填写申请标题'
  if (form.source === 'task') {
    if (!form.taskId) return '请选择关联任务'
    form.requestedHours = selectedTask.value?.hours ?? ''
  }
  if (form.requestedHours === '' || form.requestedHours === null) return '请填写申请课时数'
  if (!Number.isFinite(Number(form.requestedHours)) || Number(form.requestedHours) <= 0) {
    return '申请课时数必须大于 0'
  }
  if (!form.primaryTeacherId) return '请选择主指导老师。'
  if (1 + form.observerTeacherIds.length > 3) return '主指导老师和查看导师总数不能超过 3 人。'
  if (form.applicationType === 'without_result' && !form.expectedResultDate) {
    return '无成果申请必须填写预计成果提交时间。'
  }
  if (form.source === 'student') {
    if (!form.members.length) return '请至少填写 1 名团队成员。'
    if (!isSelfApplicationLeader.value) return '学生自主申请必须由当前登录学生作为队长提交。'
  }
  return ''
}

function saveDraft() {
  if (!canSubmitApplication.value) {
    feedback.value = { type: 'error', message: permissionState.value.message }
    return
  }

  feedback.value = { type: 'success', message: '草稿已模拟保存，本次操作不会提交到后端。' }
  window.alert(feedback.value.message)
}

function submitApplication() {
  if (!canSubmitApplication.value) {
    feedback.value = { type: 'error', message: permissionState.value.message }
    window.alert(permissionState.value.message)
    return
  }

  const error = validateForm()
  if (error) {
    feedback.value = { type: 'error', message: error }
    window.alert(error)
    return
  }

  const task = selectedTask.value
  if (form.source === 'task') {
    const duplicated = getApplications().some((item) => item.resultId === task?.resultId && !['advisor_rejected', 'reviewer_rejected', 'final_rejected', 'cancelled'].includes(item.status))
    if (duplicated) {
      feedback.value = { type: 'error', message: '该任务成果已生成课时申请，请勿重复提交。' }
      window.alert(feedback.value.message)
      taskResultVersion.value += 1
      return
    }
  }
  const applicationMembers = form.source === 'task'
    ? task.members.map((member) => ({ ...member }))
    : form.members.map((member) => ({
        id: member.id || member.studentNo,
        name: member.name,
        studentId: member.studentNo,
        college: member.college,
        major: member.major,
        role: member.isLeader ? 'captain' : 'member',
      }))
  const mainAdvisor = form.source === 'task'
    ? { id: task.advisorId, name: task.advisorName, department: '' }
    : teachers.find((teacher) => teacher.id === form.primaryTeacherId) ?? null
  const viewAdvisors = form.observerTeacherIds
    .map((id) => teachers.find((teacher) => teacher.id === id))
    .filter(Boolean)

  const addedApplication = addApplication({
    title: form.title.trim(),
    studentName: currentUser.name,
    studentId: currentUser.studentId,
    source: form.source === 'student' ? 'self' : 'task_result',
    sourceText: form.source === 'student' ? '学生自主申请' : '任务成果申请',
    applyType: form.applicationType,
    expectedResultDate: form.expectedResultDate,
    requestedHours: Number(form.requestedHours),
    taskId: task?.taskId ?? '',
    taskTitle: task?.taskTitle ?? '',
    resultId: task?.resultId ?? '',
    leaderId: task?.leaderId ?? '',
    leaderName: task?.leaderName ?? '',
    teamMembers: form.source === 'task' ? applicationMembers.map((member) => ({ ...member })) : [],
    advisorId: task?.advisorId ?? mainAdvisor?.id ?? '',
    advisorName: task?.advisorName ?? mainAdvisor?.name ?? '',
    resultDescription: task?.resultDescription ?? '',
    resultMaterials: form.source === 'task' ? task.resultMaterials.map((file) => ({ ...file })) : [],
    proofMaterials: form.source === 'task' ? task.proofMaterials.map((file) => ({ ...file })) : [],
    // captainId 沿用当前前端登录用户标识；任务中的学号身份单独保存在 leaderId。
    captainId: currentUser.id,
    currentUserId: currentUser.id,
    members: applicationMembers,
    mainAdvisor: mainAdvisor ? { ...mainAdvisor } : null,
    viewAdvisors: viewAdvisors.map((advisor) => ({ ...advisor })),
    materials: form.source === 'task' ? [...task.resultMaterials, ...task.proofMaterials].map((file) => ({ ...file })) : [],
    attachments: form.source === 'task' ? [...task.resultMaterials, ...task.proofMaterials].map((file) => ({ ...file })) : [
      {
        id: `ATT-${Date.now()}`,
        name: form.applicationType === 'with_result' ? '成果证明材料.pdf' : '团队成员承诺书.pdf',
        type: 'PDF',
        description: form.applicationType === 'with_result'
          ? 'Mock 成果证明材料'
          : 'Mock 团队成员确认材料',
      },
    ],
  })

  if (form.source === 'task') {
    markTaskResultApplicationCreated(task.resultId, addedApplication.id)
    taskResultVersion.value += 1
    form.taskId = ''
    form.requestedHours = ''
  }

  feedback.value = { type: 'success', message: '课时申请已提交，等待指导老师确认。' }
  window.alert(feedback.value.message)
  router.push('/student/hour-progress')
}

function previewTaskResultFile() { window.alert('当前为 Mock 附件预览，真实预览需后端文件服务支持。') }
function downloadTaskResultFile() { window.alert('当前为 Mock 附件下载，真实下载需后端文件服务支持。') }

function goBack() {
  router.push('/student/dashboard')
}
</script>

<template>
  <main class="hour-apply-page">
    <div class="hour-apply-content">
      <header class="page-header">
        <div>
          <p class="eyebrow">HOUR APPLICATION</p>
          <h1>课时申请</h1>
          <StageDescription description="填写申请信息并确认团队成员，提交后将进入指导老师确认阶段。" />
        </div>
        <button class="secondary-button" type="button" @click="goBack">返回学生首页</button>
      </header>

      <section
        class="permission-notice"
        :class="canSubmitApplication ? 'permission-notice--allowed' : 'permission-notice--denied'"
        role="status"
      >
        <span class="permission-notice__icon" aria-hidden="true">{{ canSubmitApplication ? '✓' : '!' }}</span>
        <div>
          <strong>{{ permissionState.message }}</strong>
          <p>当前登录学生：{{ currentUser.name }}（{{ currentUser.id }}）</p>
        </div>
      </section>

      <form class="application-form" @submit.prevent="submitApplication">
          <section class="form-section">
          <div class="section-heading">
            <h2>基本信息</h2>
            <span>请根据实际申请情况填写</span>
          </div>

          <div class="form-grid">
            <div class="form-field form-field-wide">
              <label for="application-title">申请标题 <span class="required-mark">*</span></label>
              <input
                id="application-title"
                v-model="form.title"
                type="text"
                placeholder="请输入本次课时申请标题"
                :disabled="!canSubmitApplication"
              />
            </div>

            <fieldset class="form-field form-field-wide option-fieldset">
              <legend>申请来源</legend>
              <label class="option-card">
                <input v-model="form.source" type="radio" value="student" @change="handleSourceChange" />
                <span><strong>学生自主申请</strong><small>由学生发起新的课时认定申请</small></span>
              </label>
              <p class="task-member-empty">任务成果请在“我的任务 → 队长上传成果”中提交，后端会自动创建课时申请。</p>
            </fieldset>

            <fieldset class="form-field form-field-wide option-fieldset">
              <legend>申请类型</legend>
              <label class="option-card">
                <input v-model="form.applicationType" type="radio" value="with_result" :disabled="!canSubmitApplication" />
                <span><strong>有成果申请</strong><small>当前已有可供审核的成果材料</small></span>
              </label>
              <label class="option-card">
                <input v-model="form.applicationType" type="radio" value="without_result" :disabled="!canSubmitApplication || form.source === 'task'" />
                <span><strong>无成果申请</strong><small>成果将在后续约定时间内补充提交</small></span>
              </label>
            </fieldset>

            <div v-if="form.source === 'task'" class="form-field form-field-wide">
              <label for="source-task">已确认任务成果 <span class="required-mark">*</span></label>
              <select id="source-task" v-model="form.taskId" @change="handleTaskChange">
                <option value="">请选择指导老师已确认的任务成果</option>
                <option v-for="task in approvedTaskResults" :key="task.resultId" :value="task.resultId">
                  {{ task.taskTitle }} · {{ task.advisorName }}老师 · {{ task.taskHours }} 课时
                </option>
              </select>
            </div>

            <div class="form-field">
              <label for="requested-hours">申请课时数 <span class="required-mark">*</span></label>
              <input
                id="requested-hours"
                v-model="form.requestedHours"
                type="number"
                min="1"
                step="1"
                placeholder="请输入申请课时数"
                :readonly="form.source === 'task'"
              />
              <small v-if="form.source === 'task'">
                任务成果申请的课时数由任务发布时设置，学生不可修改。
              </small>
            </div>

            <div v-if="form.applicationType === 'without_result'" class="form-field">
              <label for="expected-result-date">预计成果提交时间 <span class="required-mark">*</span></label>
              <input id="expected-result-date" v-model="form.expectedResultDate" type="date" :disabled="!canSubmitApplication" />
            </div>
          </div>

          <div v-if="form.source === 'task' && selectedTask" class="task-summary">
            <div>
              <span>任务名称</span>
              <strong>{{ selectedTask.taskTitle }}</strong>
              <small>{{ selectedTask.taskId }}</small>
            </div>
            <div>
              <span>任务队长</span>
              <strong>{{ selectedTaskCaptain?.name ?? '未设置' }}</strong>
              <small>{{ selectedTaskCaptain?.studentId ?? '--' }}</small>
            </div>
            <div>
              <span>任务成员数</span>
              <strong>{{ selectedTask.members.length }} 人</strong>
              <small>成员信息由任务自动带出</small>
            </div>
            <div>
              <span>成果材料</span>
              <strong>{{ selectedTask.resultMaterials.length }} 项</strong>
              <small>证明材料 {{ selectedTask.proofMaterials.length }} 项</small>
            </div>
            <div>
              <span>指导老师</span>
              <strong>{{ selectedTask.advisorName }}</strong>
              <small>{{ selectedTask.advisorId }}</small>
            </div>
            <div>
              <span>成果确认时间</span>
              <strong>{{ selectedTask.advisorConfirmTime || '--' }}</strong>
              <small>{{ selectedTask.advisorComment || '暂无确认意见' }}</small>
            </div>
            <div class="task-summary-wide">
              <span>成果说明</span>
              <strong>{{ selectedTask.resultDescription }}</strong>
            </div>
          </div>
          <div v-if="form.source === 'task' && selectedTask" class="task-member-table">
            <table><thead><tr><th>团队成员</th><th>学号</th><th>学院</th><th>专业</th><th>角色</th></tr></thead><tbody><tr v-for="member in selectedTask.members" :key="member.studentId"><td>{{ member.name }}</td><td>{{ member.studentId }}</td><td>{{ member.college || '--' }}</td><td>{{ member.major || '--' }}</td><td>{{ member.role === 'captain' ? '队长' : '成员' }}</td></tr></tbody></table>
          </div>
          <div v-if="form.source === 'task' && selectedTask" class="task-result-files">
            <h3>成果材料</h3><article v-for="file in selectedTask.resultMaterials" :key="file.id"><div><strong>{{ file.name || file.fileName }}</strong><small>{{ file.type || file.fileType || '未知类型' }} · {{ file.size || file.fileSize || '--' }} · {{ file.uploadedAt || file.uploadTime || '--' }}</small></div><div><button type="button" @click="previewTaskResultFile">预览</button><button type="button" @click="downloadTaskResultFile">下载</button></div></article><p v-if="!selectedTask.resultMaterials.length">暂无附件材料</p>
            <h3>证明材料</h3><article v-for="file in selectedTask.proofMaterials" :key="file.id"><div><strong>{{ file.name || file.fileName }}</strong><small>{{ file.type || file.fileType || '未知类型' }} · {{ file.size || file.fileSize || '--' }} · {{ file.uploadedAt || file.uploadTime || '--' }}</small></div><div><button type="button" @click="previewTaskResultFile">预览</button><button type="button" @click="downloadTaskResultFile">下载</button></div></article><p v-if="!selectedTask.proofMaterials.length">暂无附件材料</p>
          </div>
          <p v-if="form.source === 'task' && !approvedTaskResults.length" class="task-member-empty">暂无可申请课时的已确认任务成果。请先由队长上传成果，并等待指导老师确认通过。</p>

          <AttachmentNotice
            v-if="form.applicationType === 'with_result'"
            title="成果材料上传说明"
            description="请准备能够证明项目过程和完成情况的成果材料，正式上传功能将在后续开放。"
            :required="true"
            :accept-types="['PDF', 'Word', '图片']"
          />
          </section>

          <section class="form-section">
          <fieldset class="section-fieldset" :disabled="!canSubmitApplication">
          <div class="section-heading">
            <h2>指导老师</h2>
            <span>主指导老师与查看导师合计最多 3 人</span>
          </div>
          <div class="form-grid">
            <div class="form-field">
              <label for="primary-teacher">主指导老师 <span class="required-mark">*</span></label>
              <select id="primary-teacher" v-model="form.primaryTeacherId" @change="handlePrimaryTeacherChange">
                <option value="">请选择主指导老师</option>
                <option v-for="teacher in teachers" :key="teacher.id" :value="teacher.id">
                  {{ teacher.name }} · {{ teacher.department }}
                </option>
              </select>
            </div>
            <div class="form-field observer-field">
              <div class="observer-panel">
                <div class="observer-panel__header">
                  <div>
                    <div class="observer-panel__title">
                      <strong>查看导师</strong>
                      <span>已选择 {{ form.observerTeacherIds.length }} 人</span>
                    </div>
                    <p v-if="selectedObserverNames.length">
                      已选择：{{ selectedObserverNames.join('、') }}
                    </p>
                    <p v-else>未选择查看导师</p>
                  </div>
                  <button
                    class="observer-toggle"
                    type="button"
                    :aria-expanded="observerPanelExpanded"
                    aria-controls="observer-panel-content"
                    @click="observerPanelExpanded = !observerPanelExpanded"
                  >
                    {{ observerPanelExpanded ? '收起' : '展开' }}
                  </button>
                </div>

                <div v-show="observerPanelExpanded" id="observer-panel-content" class="observer-panel__content">
                  <label class="observer-search">
                    <span class="visually-hidden">搜索查看导师</span>
                    <input
                      v-model="observerSearch"
                      type="search"
                      placeholder="按教师姓名、学院或专业搜索"
                    />
                  </label>

                  <div v-if="filteredObserverTeachers.length" class="observer-options" aria-label="查看导师列表">
                    <label
                      v-for="teacher in filteredObserverTeachers"
                      :key="teacher.id"
                      class="observer-option"
                      :class="{ 'observer-option--disabled': isObserverDisabled(teacher.id) }"
                    >
                      <input
                        v-model="form.observerTeacherIds"
                        type="checkbox"
                        :value="teacher.id"
                        :disabled="isObserverDisabled(teacher.id)"
                      />
                      <span>
                        <strong>{{ teacher.name }}</strong>
                        <small>{{ [teacher.department, teacher.major].filter(Boolean).join(' / ') }}</small>
                      </span>
                    </label>
                  </div>
                  <p v-else class="observer-empty">没有找到匹配的导师。</p>
                  <small>主指导老师与查看导师合计最多 3 人。</small>
                </div>
              </div>
            </div>
          </div>
          </fieldset>
          </section>

          <section class="form-section">
          <div class="section-heading">
            <h2>团队信息</h2>
            <span>至少 1 名成员，且必须指定 1 名队长</span>
          </div>
          <MemberInputTable
            v-if="form.source === 'student'"
            v-model="form.members"
            :locked-leader-id="currentUser.id"
          />
          <div v-else-if="selectedTask" class="task-member-table">
            <table>
              <thead><tr><th>姓名</th><th>学号</th><th>角色</th></tr></thead>
              <tbody>
                <tr v-for="member in selectedTask.members" :key="member.id">
                  <td>{{ member.name }}</td>
                  <td>{{ member.studentId }}</td>
                  <td><span class="member-role">{{ member.role === 'captain' ? '队长' : '成员' }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="task-member-empty">选择关联任务后，将自动展示任务成员信息。</p>
          <p class="leader-notice">
            {{ form.source === 'student' ? '当前登录学生已锁定为队长，可继续添加其他成员。' : '任务成员信息来源于关联任务，不可在此修改。' }}
          </p>
          </section>

          <section class="form-section">
          <div class="section-heading"><h2>附件说明</h2></div>
          <AttachmentNotice
            title="承诺书上传说明"
            description="请上传团队成员确认后的承诺书或相关证明材料，用于确认成员信息和课时分配责任。"
            :required="true"
            :accept-types="['PDF', 'Word', '图片']"
          />
          </section>

        <p v-if="feedback.message" class="form-feedback" :class="`form-feedback--${feedback.type}`" role="status">
          {{ feedback.message }}
        </p>

        <div class="form-actions">
          <button class="secondary-button" type="button" @click="goBack">返回</button>
          <button class="secondary-button" type="button" :disabled="!canSubmitApplication" @click="saveDraft">保存草稿</button>
          <button class="primary-button" type="submit" :disabled="!canSubmitApplication">提交申请</button>
        </div>
      </form>
    </div>
  </main>
</template>

<style scoped>
.hour-apply-page { min-height: 100vh; padding: 40px 24px; background: #f3f6fb; }
.hour-apply-content { width: min(100%, 1080px); margin: 0 auto; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; margin-bottom: 28px; }
.page-header h1 { margin: 0 0 8px; font-size: 30px; }
.application-form { display: grid; gap: 22px; }
.permission-notice { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 22px; padding: 16px 18px; border: 1px solid; border-radius: 12px; }
.permission-notice--allowed { color: #166534; border-color: #bbf7d0; background: #f0fdf4; }
.permission-notice--denied { color: #b45309; border-color: #fed7aa; background: #fff7ed; }
.permission-notice__icon { display: grid; flex: 0 0 24px; width: 24px; height: 24px; place-items: center; border: 1px solid currentColor; border-radius: 50%; font-weight: 800; }
.permission-notice strong { line-height: 1.6; }
.permission-notice p { margin: 3px 0 0; color: #64748b; font-size: 13px; }
.form-section { padding: 24px; border: 1px solid #e2e8f0; border-radius: 16px; background: #fff; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04); }
.section-fieldset { min-width: 0; margin: 0; padding: 0; border: 0; }
.section-fieldset:disabled { opacity: 0.6; }
.section-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.section-heading h2 { margin: 0; font-size: 20px; }
.section-heading span { color: #64748b; font-size: 14px; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.form-field { margin: 0; }
.form-field-wide { grid-column: 1 / -1; }
.form-field > label, .option-fieldset legend { display: block; margin-bottom: 8px; color: #334155; font-weight: 700; }
.form-field select, .form-field input { width: 100%; padding: 11px 12px; border: 1px solid #cbd5e1; border-radius: 9px; background: #fff; font: inherit; }
.form-field small { display: block; margin-top: 7px; color: #64748b; }
.observer-panel { overflow: hidden; border: 1px solid #cbd5e1; border-radius: 10px; }
.observer-panel__header { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 13px 14px; background: #f8fafc; }
.observer-panel__title { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; color: #334155; }
.observer-panel__title span { padding: 2px 8px; border-radius: 999px; color: #1d4ed8; background: #dbeafe; font-size: 12px; font-weight: 700; }
.observer-panel__header p { margin: 5px 0 0; color: #64748b; font-size: 13px; }
.observer-toggle { padding: 6px 12px; border: 1px solid #bfdbfe; border-radius: 8px; color: #1d4ed8; background: #fff; font: inherit; font-weight: 700; cursor: pointer; }
.observer-panel__content { padding: 14px; border-top: 1px solid #e2e8f0; }
.observer-search { display: block; margin-bottom: 12px; }
.observer-search input { padding-left: 12px; }
.observer-options { display: grid; gap: 8px; }
.observer-option { display: flex; align-items: center; gap: 10px; margin: 0; padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 9px; color: #334155; cursor: pointer; }
.observer-option:has(input:checked) { border-color: #60a5fa; background: #eff6ff; }
.observer-option input { width: 17px; height: 17px; padding: 0; accent-color: #2563eb; }
.observer-option span, .observer-option strong { display: block; }
.observer-option small { margin-top: 2px; }
.observer-option--disabled { cursor: not-allowed; opacity: 0.5; }
.observer-empty { margin: 12px 0; color: #64748b; font-size: 14px; text-align: center; }
.visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
.option-fieldset { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; padding: 0; border: 0; }
.option-fieldset legend { grid-column: 1 / -1; }
.option-card { display: flex; align-items: flex-start; gap: 10px; padding: 14px; border: 1px solid #e2e8f0; border-radius: 10px; cursor: pointer; }
.option-card:has(input:checked) { border-color: #60a5fa; background: #eff6ff; }
.option-card input { width: auto; margin-top: 3px; accent-color: #2563eb; }
.option-card strong, .option-card small { display: block; }
.option-card small { margin-top: 4px; color: #64748b; line-height: 1.5; }
.required-mark { color: #dc2626; }
.task-summary { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 18px; padding: 16px; border: 1px solid #dbeafe; border-radius: 10px; background: #f8fbff; }
.task-summary div { display: grid; gap: 4px; }
.task-summary span, .task-summary small { color: #64748b; font-size: 13px; }
.task-summary strong { color: #1e3a8a; }
.task-summary-wide { grid-column: 1 / -1; }
.task-result-files { display: grid; gap: 10px; margin-top: 18px; }
.task-result-files h3 { margin: 10px 0 0; }
.task-result-files article { display: flex; justify-content: space-between; gap: 14px; padding: 13px; border: 1px solid #e2e8f0; border-radius: 9px; background: #f8fafc; }
.task-result-files small { display: block; margin-top: 5px; color: #64748b; }
.task-result-files article > div:last-child { display: flex; gap: 8px; }
.task-result-files button { padding: 7px 10px; border: 1px solid #bfdbfe; border-radius: 8px; color: #2563eb; background: #fff; font-weight: 700; }
.task-member-table { overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 12px; }
.task-member-table table { width: 100%; border-collapse: collapse; }
.task-member-table th, .task-member-table td { padding: 12px 14px; border-bottom: 1px solid #e2e8f0; text-align: left; }
.task-member-table th { color: #475569; background: #f8fafc; font-size: 13px; }
.task-member-table tbody tr:last-child td { border-bottom: 0; }
.member-role { display: inline-block; padding: 3px 9px; border-radius: 999px; color: #1d4ed8; background: #dbeafe; font-size: 12px; font-weight: 700; }
.task-member-empty { margin: 0; padding: 24px; border: 1px dashed #cbd5e1; border-radius: 12px; color: #64748b; text-align: center; }
.leader-notice { margin: 12px 0 0; color: #64748b; font-size: 14px; }
.form-feedback { margin: 0; padding: 12px 16px; border-radius: 10px; }
.form-feedback--error { color: #b91c1c; background: #fef2f2; }
.form-feedback--success { color: #166534; background: #f0fdf4; }
.form-actions { display: flex; justify-content: flex-end; gap: 12px; }
.form-actions button:disabled { cursor: not-allowed; opacity: 0.5; }

@media (max-width: 680px) {
  .hour-apply-page { padding: 24px 14px; }
  .page-header, .section-heading { align-items: stretch; flex-direction: column; }
  .form-grid, .option-fieldset, .task-summary { grid-template-columns: 1fr; }
  .form-field-wide, .option-fieldset legend { grid-column: auto; }
  .form-actions { flex-wrap: wrap; }
}
</style>
