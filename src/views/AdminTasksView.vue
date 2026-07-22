<template>
  <main class="dashboard-page">
    <div class="dashboard-content">
      <header class="dashboard-header">
        <div>
          <p class="eyebrow">TASK MANAGEMENT</p>
          <h1>任务管理</h1>
          <p>集中管理任务、发布确认和任务类别。</p>
        </div>
      </header>

      <section class="entry-grid" aria-label="任务管理功能模块">
        <article class="entry-card static-entry-card">
          <h2>任务列表</h2>
          <p>查看和维护系统中的任务信息，详细功能后续完善。</p>
        </article>
        <RouterLink to="/admin/tasks/publish-confirm" class="entry-card">
          <h2>任务发布确认</h2>
          <p>确认指导老师提交的任务发布申请。</p>
        </RouterLink>
        <RouterLink to="/admin/task-categories" class="entry-card">
          <h2>任务类别管理</h2>
          <p>维护任务类别、发布类型和启用状态。</p>
        </RouterLink>
      </section>
    </div>
  </main>
</template>
