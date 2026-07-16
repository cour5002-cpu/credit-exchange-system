<script setup>
import { computed } from 'vue'
import { getStageDescription } from '../utils/status'

const props = defineProps({
  stage: {
    type: [String, Number],
    default: '',
  },
  description: {
    type: String,
    default: '',
  },
})

const content = computed(() => props.description || getStageDescription(props.stage))
</script>

<template>
  <p class="stage-description">{{ content }}</p>
</template>

<style scoped>
.stage-description {
  margin: 0;
  color: #64748b;
  font-size: 14px;
  line-height: 1.7;
}
</style>

