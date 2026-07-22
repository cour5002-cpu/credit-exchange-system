import { createRouter, createWebHistory } from 'vue-router'

const placeholderRoutes = [
  ['/student/tasks', 'student-tasks', '我的任务', '查看和管理分配给你的任务。'],
  ['/student/task-square', 'student-task-square', '任务广场', '浏览当前可以参与的任务。'],
  ['/student/feedback', 'student-feedback', '问题反馈', '提交使用过程中遇到的问题。'],
  ['/student/notifications', 'student-notifications', '信息通知', '查看学生端通知消息。'],
  ['/teacher/tasks', 'teacher-tasks', '我的任务', '查看和管理指导任务。'],
  ['/teacher/notifications', 'teacher-notifications', '信息通知', '查看指导老师端通知消息。'],
  ['/reviewer/notifications', 'reviewer-notifications', '信息通知', '查看审核老师端通知消息。'],
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
      path: '/student/hour-progress',
      name: 'student-hour-progress',
      component: () => import('../views/StudentHourProgressView.vue'),
    },
    {
      path: '/student/hour-progress/:id',
      name: 'student-hour-progress-detail',
      component: () => import('../views/StudentHourProgressDetailView.vue'),
    },
    {
      path: '/student/credit-exchange',
      name: 'student-credit-exchange',
      component: () => import('../views/StudentCreditExchangeView.vue'),
    },
    {
      path: '/student/credit-exchange-records',
      name: 'student-credit-exchange-records',
      component: () => import('../views/StudentCreditExchangeRecordsView.vue'),
    },
    {
      path: '/student/credit-exchange-records/:id',
      name: 'student-credit-exchange-record-detail',
      component: () => import('../views/StudentCreditExchangeRecordDetailView.vue'),
    },
    {
      path: '/teacher/dashboard',
      name: 'teacher-dashboard',
      component: () => import('../views/TeacherDashboard.vue'),
    },
    {
      path: '/teacher/publish-task',
      name: 'teacher-publish-task-management',
      component: () => import('../views/TeacherTaskPublishListView.vue'),
    },
    {
      path: '/teacher/publish-task/new',
      name: 'teacher-publish-task-create',
      component: () => import('../views/TeacherTaskPublishFormView.vue'),
    },
    {
      path: '/teacher/publish-task/:id/edit',
      name: 'teacher-publish-task-edit',
      component: () => import('../views/TeacherTaskPublishFormView.vue'),
    },
    {
      path: '/teacher/publish-task/:id',
      name: 'teacher-publish-task-detail',
      component: () => import('../views/TeacherTaskPublishDetailView.vue'),
    },
    {
      path: '/teacher/confirm',
      name: 'teacher-confirm',
      component: () => import('../views/TeacherConfirmListView.vue'),
    },
    {
      path: '/teacher/confirm/exchanges',
      name: 'teacher-credit-exchange-confirm',
      component: () => import('../views/TeacherCreditExchangeListView.vue'),
    },
    {
      path: '/teacher/confirm/exchanges/:id',
      name: 'teacher-credit-exchange-confirm-detail',
      component: () => import('../views/TeacherCreditExchangeDetailView.vue'),
    },
    {
      path: '/teacher/confirm/:id',
      name: 'teacher-confirm-detail',
      component: () => import('../views/TeacherConfirmDetailView.vue'),
    },
    {
      path: '/teacher/records',
      name: 'teacher-records',
      component: () => import('../views/TeacherRecordsView.vue'),
    },
    {
      path: '/reviewer/dashboard',
      name: 'reviewer-dashboard',
      component: () => import('../views/ReviewerDashboard.vue'),
    },
    {
      path: '/reviewer/review-tasks',
      name: 'reviewer-review-tasks',
      component: () => import('../views/ReviewerTaskListView.vue'),
    },
    {
      path: '/reviewer/review-tasks/:id',
      name: 'reviewer-review-task-detail',
      component: () => import('../views/ReviewerReviewDetailView.vue'),
    },
    {
      path: '/reviewer/review-records',
      name: 'reviewer-review-records',
      component: () => import('../views/ReviewerRecordListView.vue'),
    },
    {
      path: '/reviewer/review-records/:id',
      name: 'reviewer-review-record-detail',
      component: () => import('../views/ReviewerReviewDetailView.vue'),
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
      path: '/admin/tasks/publish-confirm',
      name: 'admin-task-publish-confirm',
      component: () => import('../views/AdminTaskPublishConfirmListView.vue'),
    },
    {
      path: '/admin/tasks/publish-confirm/:id',
      name: 'admin-task-publish-confirm-detail',
      component: () => import('../views/AdminTaskPublishConfirmDetailView.vue'),
    },
    {
      path: '/admin/task-categories',
      name: 'admin-task-categories',
      component: () => import('../views/TaskCategoriesView.vue'),
    },
    {
      path: '/admin/review-assign',
      name: 'admin-review-assign',
      component: () => import('../views/AdminAcceptanceListView.vue'),
    },
    {
      path: '/admin/review-assign/:id',
      name: 'admin-acceptance-detail',
      component: () => import('../views/AdminAcceptanceDetailView.vue'),
    },
    {
      path: '/admin/final-confirm',
      name: 'admin-final-confirm',
      component: () => import('../views/AdminFinalConfirmListView.vue'),
    },
    {
      path: '/admin/final-confirm/exchanges',
      name: 'admin-credit-exchange-final-confirm',
      component: () => import('../views/AdminCreditExchangeReviewView.vue'),
    },
    {
      path: '/admin/final-confirm/exchanges/:id',
      name: 'admin-credit-exchange-final-confirm-detail',
      component: () => import('../views/AdminCreditExchangeDetailView.vue'),
    },
    {
      path: '/admin/final-confirm/:id',
      name: 'admin-final-confirm-detail',
      component: () => import('../views/AdminFinalConfirmDetailView.vue'),
    },
    {
      path: '/admin/credit-exchange-review',
      redirect: '/admin/final-confirm/exchanges',
    },
    ...placeholderRoutes,
    {
      path: '/:pathMatch(.*)*',
      redirect: '/login',
    },
  ],
})

export default router
