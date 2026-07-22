<script setup>
import { ref } from 'vue'
import TaskCategoryModal from './components/TaskCategoryModal.vue'

const publishTypeLabels = {
  advisor_publish: '指导老师发布',
  admin_publish: '管理员直接发布',
}

const categories = ref([
  {
    id: 1,
    name: '志愿服务',
    type_code: 'VOLUNTEER_SERVICE',
    description: '校内外志愿服务活动及公益实践。',
    sort_order: 10,
    status: 'enabled',
    task_publish_type: 'advisor_publish',
  },
  {
    id: 2,
    name: '学科竞赛',
    type_code: 'ACADEMIC_COMPETITION',
    description: '学校认可的各级学科竞赛。',
    sort_order: 20,
    status: 'enabled',
    task_publish_type: 'admin_publish',
  },
  {
    id: 3,
    name: '专题培训',
    type_code: 'SPECIAL_TRAINING',
    description: '由教师或管理员组织的专题培训。',
    sort_order: 30,
    status: 'disabled',
    task_publish_type: 'advisor_publish',
  },
])

const showModal = ref(false)
const editingCategory = ref(null)

function openCreateModal() {
  editingCategory.value = null
  showModal.value = true
}

function openEditModal(category) {
  editingCategory.value = category
  showModal.value = true
}

function saveCategory(formData) {
  if (editingCategory.value) {
    const index = categories.value.findIndex((item) => item.id === editingCategory.value.id)
    categories.value[index] = { ...categories.value[index], ...formData }
  } else {
    const nextId = Math.max(0, ...categories.value.map((item) => item.id)) + 1
    categories.value.push({ id: nextId, ...formData })
  }

  categories.value.sort((a, b) => a.sort_order - b.sort_order)
  showModal.value = false
}

function toggleStatus(category) {
  category.status = category.status === 'enabled' ? 'disabled' : 'enabled'
}
</script>

<template>
  <main class="dashboard-page">
    <div class="dashboard-content">
      <header class="dashboard-header">
        <div>
          <p class="eyebrow">TASK CATEGORY MANAGEMENT</p>
          <h1>任务类别管理</h1>
          <p>维护任务类别、任务发布类型及启用状态。</p>
        </div>
        <button class="primary-button" type="button" @click="openCreateModal">新增类别</button>
      </header>

      <section class="management-panel" aria-labelledby="category-list-title">
        <div class="panel-header">
          <h2 id="category-list-title">类别列表</h2>
          <span>共 {{ categories.length }} 个类别</span>
        </div>

        <div class="table-wrapper">
          <table class="category-table">
            <thead>
              <tr>
                <th>排序</th>
                <th>类别名称 / 编码</th>
                <th>类别说明</th>
                <th>任务发布类型</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="category in categories" :key="category.id">
                <td>{{ category.sort_order }}</td>
                <td>
                  <strong>{{ category.name }}</strong>
                  <code>{{ category.type_code }}</code>
                </td>
                <td>{{ category.description || '—' }}</td>
                <td>
                  <span class="scope-tag">{{ publishTypeLabels[category.task_publish_type] }}</span>
                </td>
                <td>
                  <span class="status-badge" :class="`status-${category.status}`">
                    {{ category.status === 'enabled' ? '已启用' : '已停用' }}
                  </span>
                </td>
                <td>
                  <div class="table-actions">
                    <button class="text-button" type="button" @click="openEditModal(category)">编辑</button>
                    <button
                      class="text-button"
                      :class="category.status === 'enabled' ? 'danger-text' : 'success-text'"
                      type="button"
                      @click="toggleStatus(category)"
                    >
                      {{ category.status === 'enabled' ? '停用' : '启用' }}
                    </button>
                  </div>
                </td>
                </tr>
              <tr v-if="!categories.length"><td colspan="6" class="empty-state">暂无任务类别</td></tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <TaskCategoryModal
      v-if="showModal"
      :category="editingCategory"
      :existing-categories="categories"
      @close="showModal = false"
      @save="saveCategory"
    />
  </main>
</template>
