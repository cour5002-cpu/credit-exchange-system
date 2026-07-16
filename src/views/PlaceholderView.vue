<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
})
</script>

<template>
  <main class="dashboard-page">
    <div class="dashboard-content">
      <header class="dashboard-header">
        <p class="eyebrow">FEATURE PAGE</p>
        <h1>{{ title }}</h1>
        <p>{{ description }}当前为功能占位页面，后续将继续完善。</p>
      </header>
    </div>
  </main>
</template>
