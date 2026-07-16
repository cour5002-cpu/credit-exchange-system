<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'

const props = defineProps({
  category: {
    type: Object,
    default: null,
  },
  existingCategories: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['close', 'save'])

const publishTypeOptions = [
  {
    value: 'advisor_publish',
    label: '指导老师发布',
    description: '指导老师发布任务，管理员审核同意后，学生可以报名',
  },
  {
    value: 'admin_publish',
    label: '管理员直接发布',
    description: '管理员端直接发布任务',
  },
]

const form = reactive({
  name: props.category?.name ?? '',
  type_code: props.category?.type_code ?? '',
  description: props.category?.description ?? '',
  sort_order: props.category?.sort_order ?? 0,
  status: props.category?.status ?? 'enabled',
  task_publish_type: props.category?.task_publish_type ?? '',
})

const formError = ref('')

function closeModal() {
  emit('close')
}

function handleKeydown(event) {
  if (event.key === 'Escape') closeModal()
}

function save() {
  const normalizedCode = form.type_code.trim().toUpperCase()
  const duplicatedCode = props.existingCategories.some(
    (item) => item.id !== props.category?.id && item.type_code.toUpperCase() === normalizedCode,
  )

  if (!form.name.trim() || !normalizedCode) {
    formError.value = '类别名称和类别编码不能为空。'
    return
  }

  if (!/^[A-Z][A-Z0-9_]*$/.test(normalizedCode)) {
    formError.value = '类别编码只能使用大写字母、数字和下划线，且必须以字母开头。'
    return
  }

  if (duplicatedCode) {
    formError.value = '类别编码已存在，请使用其他编码。'
    return
  }

  if (!form.task_publish_type) {
    formError.value = '请选择一个任务发布类型。'
    return
  }

  emit('save', {
    ...form,
    name: form.name.trim(),
    type_code: normalizedCode,
    description: form.description.trim(),
    sort_order: Number(form.sort_order),
    task_publish_type: form.task_publish_type,
  })
}

onMounted(() => document.addEventListener('keydown', handleKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', handleKeydown))
</script>

<template>
  <div class="modal-backdrop" role="presentation" @click.self="closeModal">
    <section class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="category-modal-title">
      <header class="modal-header">
        <div>
          <p class="eyebrow">TASK CATEGORY</p>
          <h2 id="category-modal-title">{{ category ? '编辑类别' : '新增类别' }}</h2>
        </div>
        <button class="icon-button" type="button" aria-label="关闭弹窗" @click="closeModal">×</button>
      </header>

      <form @submit.prevent="save">
        <div class="form-grid">
          <div class="form-field">
            <label for="category-name">类别名称</label>
            <input id="category-name" v-model="form.name" type="text" placeholder="例如：志愿服务" />
          </div>
          <div class="form-field">
            <label for="category-code">类别编码</label>
            <input id="category-code" v-model="form.type_code" type="text" placeholder="例如：VOLUNTEER_SERVICE" />
          </div>
          <div class="form-field form-field-wide">
            <label for="category-description">类别说明</label>
            <textarea id="category-description" v-model="form.description" rows="3" placeholder="请输入类别用途说明"></textarea>
          </div>
          <div class="form-field">
            <label for="category-sort">排序</label>
            <input id="category-sort" v-model.number="form.sort_order" type="number" min="0" step="1" />
          </div>
          <div class="form-field">
            <label for="category-status">状态</label>
            <select id="category-status" v-model="form.status">
              <option value="enabled">启用</option>
              <option value="disabled">停用</option>
            </select>
          </div>
          <fieldset class="form-field form-field-wide publish-type-fieldset">
            <legend>任务发布类型</legend>
            <label v-for="option in publishTypeOptions" :key="option.value" class="radio-option">
              <input v-model="form.task_publish_type" type="radio" name="task-publish-type" :value="option.value" />
              <span>
                <strong>{{ option.label }}</strong>
                <small>{{ option.description }}</small>
              </span>
            </label>
          </fieldset>
        </div>

        <p v-if="formError" class="error-message" role="alert">{{ formError }}</p>

        <div class="modal-actions">
          <button class="secondary-button" type="button" @click="closeModal">取消</button>
          <button class="primary-button" type="submit">保存</button>
        </div>
      </form>
    </section>
  </div>
</template>
