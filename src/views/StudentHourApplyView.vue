<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AttachmentNotice from '../components/AttachmentNotice.vue'
import MemberInputTable from '../components/MemberInputTable.vue'
import StageDescription from '../components/StageDescription.vue'

const router = useRouter()

const teachers = [
  { id: 'T001', name: '张明', department: '计算机学院' },
  { id: 'T002', name: '李华', department: '管理学院' },
  { id: 'T003', name: '王芳', department: '艺术学院' },
  { id: 'T004', name: '陈强', department: '校团委' },
  { id: 'T005', name: '赵敏', department: '创新创业学院' },
]

const form = reactive({
  source: 'student',
  taskId: '',
  applicationType: 'with_result',
  primaryTeacherId: '',
  observerTeacherIds: [],
  expectedResultDate: '',
  members: [],
})

const feedback = ref({ type: '', message: '' })
const observerPanelExpanded = ref(false)
const observerSearch = ref('')
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

function validateForm() {
  if (!form.primaryTeacherId) return '请选择主指导老师。'
  if (1 + form.observerTeacherIds.length > 3) return '主指导老师和查看导师总数不能超过 3 人。'
  if (form.applicationType === 'without_result' && !form.expectedResultDate) {
    return '无成果申请必须填写预计成果提交时间。'
  }
  if (!form.members.length) return '请至少填写 1 名团队成员。'
  if (!form.members.some((member) => member.isLeader)) return '请选择 1 名队长。'
  return ''
}

function saveDraft() {
  feedback.value = { type: 'success', message: '草稿已模拟保存，本次操作不会提交到后端。' }
  window.alert(feedback.value.message)
}

function submitApplication() {
  const error = validateForm()
  if (error) {
    feedback.value = { type: 'error', message: error }
    window.alert(error)
    return
  }

  feedback.value = { type: 'success', message: '校验通过，申请已模拟提交。' }
  window.alert(feedback.value.message)
}

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
          <StageDescription description="填写申请信息并确认团队成员，提交后将进入指导老师审核阶段。" />
        </div>
        <button class="secondary-button" type="button" @click="goBack">返回学生首页</button>
      </header>

      <form class="application-form" @submit.prevent="submitApplication">
        <section class="form-section">
          <div class="section-heading">
            <h2>基本信息</h2>
            <span>请根据实际申请情况填写</span>
          </div>

          <div class="form-grid">
            <fieldset class="form-field form-field-wide option-fieldset">
              <legend>申请来源</legend>
              <label class="option-card">
                <input v-model="form.source" type="radio" value="student" />
                <span><strong>学生自主申请</strong><small>由学生发起新的课时认定申请</small></span>
              </label>
              <label class="option-card">
                <input v-model="form.source" type="radio" value="task" />
                <span><strong>任务成果申请</strong><small>基于已参与任务的成果发起申请</small></span>
              </label>
            </fieldset>

            <div v-if="form.source === 'task'" class="form-field form-field-wide">
              <label for="source-task">关联任务（Mock）</label>
              <select id="source-task" v-model="form.taskId">
                <option value="">请选择任务</option>
                <option value="TASK-001">校园志愿服务周</option>
                <option value="TASK-002">创新创业专题实践</option>
              </select>
            </div>

            <fieldset class="form-field form-field-wide option-fieldset">
              <legend>申请类型</legend>
              <label class="option-card">
                <input v-model="form.applicationType" type="radio" value="with_result" />
                <span><strong>有成果申请</strong><small>当前已有可供审核的成果材料</small></span>
              </label>
              <label class="option-card">
                <input v-model="form.applicationType" type="radio" value="without_result" />
                <span><strong>无成果申请</strong><small>成果将在后续约定时间内补充提交</small></span>
              </label>
            </fieldset>

            <div v-if="form.applicationType === 'without_result'" class="form-field">
              <label for="expected-result-date">预计成果提交时间 <span class="required-mark">*</span></label>
              <input id="expected-result-date" v-model="form.expectedResultDate" type="date" />
            </div>
          </div>

          <AttachmentNotice
            v-if="form.applicationType === 'with_result'"
            title="成果材料上传说明"
            description="请准备能够证明项目过程和完成情况的成果材料，正式上传功能将在后续开放。"
            :required="true"
            :accept-types="['PDF', 'Word', '图片']"
          />
        </section>

        <section class="form-section">
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
        </section>

        <section class="form-section">
          <div class="section-heading">
            <h2>团队信息</h2>
            <span>至少 1 名成员，且必须指定 1 名队长</span>
          </div>
          <MemberInputTable v-model="form.members" />
          <p class="leader-notice">队长负责后续成果提交和学分兑换，请谨慎选择。</p>
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
          <button class="secondary-button" type="button" @click="saveDraft">保存草稿</button>
          <button class="primary-button" type="submit">提交申请</button>
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
.form-section { padding: 24px; border: 1px solid #e2e8f0; border-radius: 16px; background: #fff; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04); }
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
.leader-notice { margin: 12px 0 0; color: #64748b; font-size: 14px; }
.form-feedback { margin: 0; padding: 12px 16px; border-radius: 10px; }
.form-feedback--error { color: #b91c1c; background: #fef2f2; }
.form-feedback--success { color: #166534; background: #f0fdf4; }
.form-actions { display: flex; justify-content: flex-end; gap: 12px; }

@media (max-width: 680px) {
  .hour-apply-page { padding: 24px 14px; }
  .page-header, .section-heading { align-items: stretch; flex-direction: column; }
  .form-grid, .option-fieldset { grid-template-columns: 1fr; }
  .form-field-wide, .option-fieldset legend { grid-column: auto; }
  .form-actions { flex-wrap: wrap; }
}
</style>
