<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '附件说明',
  },
  description: {
    type: String,
    default: '',
  },
  required: {
    type: Boolean,
    default: false,
  },
  acceptTypes: {
    type: [Array, String],
    default: () => [],
  },
})

const acceptedTypesText = computed(() =>
  Array.isArray(props.acceptTypes) ? props.acceptTypes.filter(Boolean).join('、') : props.acceptTypes,
)
</script>

<template>
  <aside class="attachment-notice" :class="{ 'attachment-notice--required': required }">
    <div class="attachment-notice__content">
      <div class="attachment-notice__heading">
        <h3>{{ title }}</h3>
        <span class="requirement-tag" :class="{ 'requirement-tag--optional': !required }">
          {{ required ? '必传' : '选传' }}
        </span>
      </div>
      <p v-if="description">{{ description }}</p>
      <p v-if="acceptedTypesText" class="attachment-notice__types">
        允许上传：{{ acceptedTypesText }}
      </p>
    </div>
  </aside>
</template>

<style scoped>
.attachment-notice {
  padding: 16px 18px;
  border: 1px solid #dbeafe;
  border-left: 4px solid #60a5fa;
  border-radius: 10px;
  background: #f8fbff;
}

.attachment-notice--required { border-left-color: #2563eb; }
.attachment-notice__heading { display: flex; align-items: center; gap: 10px; }
.attachment-notice h3 { margin: 0; color: #1e293b; font-size: 16px; }
.attachment-notice p { margin: 8px 0 0; color: #64748b; font-size: 14px; line-height: 1.65; }
.attachment-notice .attachment-notice__types { color: #475569; font-weight: 600; }
.requirement-tag { display: inline-flex; padding: 2px 8px; border-radius: 999px; color: #b91c1c; background: #fee2e2; font-size: 12px; font-weight: 700; white-space: nowrap; }
.requirement-tag--optional { color: #475569; background: #e2e8f0; }
</style>
