<script setup>
defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  approveText: {
    type: String,
    default: '通过',
  },
  rejectText: {
    type: String,
    default: '驳回',
  },
})

defineEmits(['approve', 'reject'])
</script>

<template>
  <div class="review-action-bar">
    <slot name="before" />
    <button
      class="review-action review-action--reject"
      type="button"
      :disabled="disabled || loading"
      @click="$emit('reject')"
    >
      {{ rejectText }}
    </button>
    <button
      class="review-action review-action--approve"
      type="button"
      :disabled="disabled || loading"
      @click="$emit('approve')"
    >
      {{ loading ? '处理中…' : approveText }}
    </button>
    <slot name="after" />
  </div>
</template>

<style scoped>
.review-action-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
}

.review-action {
  min-width: 96px;
  padding: 10px 18px;
  border-radius: 10px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.review-action--reject {
  border: 1px solid #fecaca;
  color: #b91c1c;
  background: #fff;
}

.review-action--approve {
  border: 1px solid #2563eb;
  color: #fff;
  background: #2563eb;
}

.review-action:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
</style>
