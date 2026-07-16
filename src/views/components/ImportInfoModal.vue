<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const emit = defineEmits(['close'])

const importType = ref('students')
const selectedFile = ref(null)
const fileInput = ref(null)
const validationMessage = ref('')
const templateMessage = ref('')
const importResult = ref(null)

const typeOptions = [
  { value: 'students', label: '学生' },
  { value: 'teachers', label: '教师' },
  { value: 'admins', label: '管理员' },
]

const mockResults = {
  students: {
    success_count: 46,
    failure_count: 2,
    errors: [
      { row_no: 8, field: 'student_no', message: '学号已存在' },
      { row_no: 21, field: 'email', message: '邮箱格式不正确' },
    ],
  },
  teachers: {
    success_count: 18,
    failure_count: 1,
    errors: [{ row_no: 6, field: 'teacher_no', message: '教师工号不能为空' }],
  },
  admins: {
    success_count: 5,
    failure_count: 1,
    errors: [{ row_no: 4, field: 'username', message: '用户名已存在' }],
  },
}

function closeModal() {
  emit('close')
}

function handleKeydown(event) {
  if (event.key === 'Escape') closeModal()
}

function chooseFile() {
  fileInput.value?.click()
}

function handleFileChange(event) {
  const file = event.target.files?.[0]
  const allowedExtensions = ['.xlsx', '.xls', '.csv']
  const isAllowed = file && allowedExtensions.some((extension) => file.name.toLowerCase().endsWith(extension))

  validationMessage.value = ''
  importResult.value = null

  if (!file) {
    selectedFile.value = null
    return
  }

  if (!isAllowed) {
    selectedFile.value = null
    validationMessage.value = '请选择 Excel（.xlsx、.xls）或 CSV 文件。'
    event.target.value = ''
    return
  }

  selectedFile.value = file
}

function downloadTemplate() {
  const typeLabel = typeOptions.find((item) => item.value === importType.value)?.label
  const templateContent = '\uFEFF姓名,账号,邮箱\n示例用户,example001,example@school.edu.cn\n'
  const blob = new Blob([templateContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = `${typeLabel}导入模板.csv`
  link.click()
  URL.revokeObjectURL(url)
  templateMessage.value = `已生成${typeLabel}导入示例模板。`
}

function startImport() {
  if (!selectedFile.value) {
    validationMessage.value = '请先选择需要导入的文件。'
    return
  }

  validationMessage.value = ''
  importResult.value = mockResults[importType.value]
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="modal-backdrop" role="presentation" @click.self="closeModal">
    <section class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="import-modal-title">
      <header class="modal-header">
        <div>
          <p class="eyebrow">DATA IMPORT</p>
          <h2 id="import-modal-title">导入信息</h2>
        </div>
        <button class="icon-button" type="button" aria-label="关闭导入弹窗" @click="closeModal">×</button>
      </header>

      <div class="form-field">
        <label for="import-type">导入类型</label>
        <select id="import-type" v-model="importType" @change="importResult = null; templateMessage = ''">
          <option v-for="option in typeOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>

      <div class="template-row">
        <div>
          <strong>导入模板</strong>
          <p>请按照模板字段填写数据后上传。</p>
        </div>
        <button class="secondary-button" type="button" @click="downloadTemplate">下载模板</button>
      </div>
      <p v-if="templateMessage" class="success-message" role="status">{{ templateMessage }}</p>

      <div class="form-field">
        <label>上传文件</label>
        <input
          ref="fileInput"
          class="visually-hidden"
          type="file"
          accept=".xlsx,.xls,.csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
          @change="handleFileChange"
        />
        <button class="upload-area" type="button" @click="chooseFile">
          <strong>{{ selectedFile ? selectedFile.name : '点击选择文件' }}</strong>
          <span>仅支持 .xlsx、.xls 或 .csv 文件</span>
        </button>
        <p v-if="validationMessage" class="error-message" role="alert">{{ validationMessage }}</p>
      </div>

      <div class="modal-actions">
        <button class="secondary-button" type="button" @click="closeModal">取消</button>
        <button class="primary-button" type="button" @click="startImport">开始导入</button>
      </div>

      <section v-if="importResult" class="import-result" aria-live="polite">
        <h3>导入结果</h3>
        <div class="result-summary">
          <div class="result-card result-success">
            <span>成功数量</span>
            <strong>{{ importResult.success_count }}</strong>
          </div>
          <div class="result-card result-failure">
            <span>失败数量</span>
            <strong>{{ importResult.failure_count }}</strong>
          </div>
        </div>

        <div v-if="importResult.errors.length" class="error-details">
          <h3>错误明细</h3>
          <div class="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>行号</th>
                  <th>字段</th>
                  <th>错误原因</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="error in importResult.errors" :key="`${error.row_no}-${error.field}`">
                  <td>{{ error.row_no }}</td>
                  <td>{{ error.field }}</td>
                  <td>{{ error.message }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </section>
  </div>
</template>
