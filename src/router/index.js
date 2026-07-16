import { createRouter, createWebHistory } from 'vue-router'

const placeholderRoutes = [
  ['/student/tasks', 'student-tasks', '我的任务', '查看和管理分配给你的任务。'],
  ['/student/task-square', 'student-task-square', '任务广场', '浏览当前可以参与的任务。'],
  ['/student/hour-progress', 'student-hour-progress', '课时申请进度', '查看课时申请的处理进度。'],
  ['/student/credit-exchange', 'student-credit-exchange', '学分兑换', '办理课时与学分兑换。'],
  ['/student/feedback', 'student-feedback', '问题反馈', '提交使用过程中遇到的问题。'],
  ['/student/notifications', 'student-notifications', '信息通知', '查看学生端通知消息。'],
  ['/teacher/tasks', 'teacher-tasks', '我的任务', '查看和管理指导任务。'],
  ['/teacher/publish-task', 'teacher-publish-task', '发布任务', '创建并发布新的任务。'],
  ['/teacher/records', 'teacher-records', '我的处理记录', '查看已经处理的业务记录。'],
  ['/teacher/notifications', 'teacher-notifications', '信息通知', '查看指导老师端通知消息。'],
  ['/reviewer/review-tasks', 'reviewer-review-tasks', '待审核成果', '查看等待审核的学生成果。'],
  ['/reviewer/review-records', 'reviewer-review-records', '我的审核记录', '查看已经完成的审核记录。'],
  ['/reviewer/notifications', 'reviewer-notifications', '信息通知', '查看审核老师端通知消息。'],
  ['/admin/review-assign', 'admin-review-assign', '审核分配', '为待审核事项分配审核老师。'],
  ['/admin/final-confirm', 'admin-final-confirm', '最终确认', '处理等待最终确认的业务。'],
  ['/admin/appeals-complaints', 'admin-appeals-complaints', '申诉与投诉', '处理用户提交的申诉与投诉。'],
  ['/admin/extensions', 'admin-extensions', '特殊延期', '管理特殊情况的延期申请。'],
  ['/admin/statistics', 'admin-statistics', '数据统计', '查看系统业务统计数据。'],
  ['/admin/notifications', 'admin-notifications', '信息通知', '查看管理员端通知消息。'],
].map(([path, name, title, description]) => ({
  path,
  name,
  component: () => import('../views/PlaceholderView.vue'),
  props: { title, description },
}))

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/login',
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/student/dashboard',
      name: 'student-dashboard',
      component: () => import('../views/StudentDashboard.vue'),
    },
    {
      path: '/student/hour-apply',
      name: 'student-hour-apply',
      component: () => import('../views/StudentHourApplyView.vue'),
    },
    {
      path: '/teacher/dashboard',
      name: 'teacher-dashboard',
      component: () => import('../views/TeacherDashboard.vue'),
    },
    {
      path: '/teacher/confirm',
      name: 'teacher-confirm',
      component: () => import('../views/TeacherConfirmListView.vue'),
    },
    {
      path: '/teacher/confirm/:id',
      name: 'teacher-confirm-detail',
      component: () => import('../views/TeacherConfirmDetailView.vue'),
    },
    {
      path: '/reviewer/dashboard',
      name: 'reviewer-dashboard',
      component: () => import('../views/ReviewerDashboard.vue'),
    },
    {
      path: '/admin/dashboard',
      name: 'admin-dashboard',
      component: () => import('../views/AdminDashboard.vue'),
    },
    {
      path: '/admin/tasks',
      name: 'admin-tasks',
      component: () => import('../views/AdminTasksView.vue'),
    },
    {
      path: '/admin/task-categories',
      name: 'admin-task-categories',
      component: () => import('../views/TaskCategoriesView.vue'),
    },
    ...placeholderRoutes,
    {
      path: '/:pathMatch(.*)*',
      redirect: '/login',
    },
  ],
})

export default router
