<script setup>
import { computed } from 'vue'
import { getStatusColor, getStatusText } from '../utils/status'

const props = defineProps({
  status: {
    type: [String, Number],
    default: '',
  },
  text: {
    type: String,
    default: '',
  },
})

const color = computed(() => getStatusColor(props.status))
const label = computed(() => props.text || getStatusText(props.status))
</script>

<template>
  <span class="status-tag" :class="`status-tag--${color}`">{{ label }}</span>
</template>

<style scoped>
.status-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  color: #475569;
  background: #f1f5f9;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.5;
  white-space: nowrap;
}

.status-tag--success { color: #166534; background: #dcfce7; }
.status-tag--warning { color: #92400e; background: #fef3c7; }
.status-tag--danger { color: #b91c1c; background: #fee2e2; }
.status-tag--info { color: #1d4ed8; background: #dbeafe; }
</style>

