<script setup>
import { computed } from 'vue'

const props = defineProps({
  page: { type: Number, required: true },
  pageSize: { type: Number, required: true },
  total: { type: Number, required: true },
  loading: { type: Boolean, default: false },
})
const emit = defineEmits(['change'])
const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
const pageNumbers = computed(() => Array.from({ length: totalPages.value }, (_, index) => index + 1))
function changePage(target) {
  const nextPage = Math.min(Math.max(1, target), totalPages.value)
  if (nextPage !== props.page && !props.loading) emit('change', nextPage)
}
</script>

<template>
  <nav class="pagination" aria-label="列表分页">
    <span>第 {{ page }} / {{ totalPages }} 页</span>
    <button type="button" :disabled="page === 1 || loading" @click="changePage(page - 1)">上一页</button>
    <button v-for="number in pageNumbers" :key="number" type="button" :class="{ active: number === page }" :disabled="loading" @click="changePage(number)">{{ number }}</button>
    <button type="button" :disabled="page === totalPages || loading" @click="changePage(page + 1)">下一页</button>
  </nav>
</template>

<style scoped>
.pagination{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:8px;padding:18px;border-top:1px solid #e2e8f0}.pagination span{margin-right:4px;color:#64748b}.pagination button{min-width:40px;padding:8px 12px;border:1px solid #cbd5e1;border-radius:8px;color:#334155;background:#fff;font:inherit;font-weight:700;cursor:pointer}.pagination button.active{border-color:#2563eb;color:#fff;background:#2563eb}.pagination button:disabled{opacity:.5;cursor:not-allowed}
</style>
