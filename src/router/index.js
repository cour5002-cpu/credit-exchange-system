import { createRouter, createWebHistory } from 'vue-router'

const placeholderRoutes = [
  ['/student/feedback', 'student-feedback', '问题反馈', '提交使用过程中遇到的问题。'],
  ['/student/notifications', 'student-notifications', '信息通知', '查看学生端通知消息。'],
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
      path: '/student/tasks',
      name: 'student-tasks',
      component: () => import('../views/StudentTasksView.vue'),
    },
    {
      path: '/student/tasks/:id',
      name: 'student-task-detail',
      component: () => import('../views/StudentTaskDetailView.vue'),
    },
    {
      path: '/student/tasks/:id/result',
      name: 'student-task-apply-result',
      component: () => import('../views/StudentTaskApplyResultView.vue'),
    },
    {
      path: '/student/tasks/:id/team',
      name: 'student-task-team',
      component: () => import('../views/StudentTaskTeamView.vue'),
    },
    {
      path: '/student/tasks/:id/result-submit',
      name: 'student-task-result-submit',
      component: () => import('../views/StudentTaskResultSubmitView.vue'),
    },
    {
      path: '/student/task-square',
      name: 'student-task-square',
      component: () => import('../views/StudentTaskSquareView.vue'),
    },
    {
      path: '/student/task-square/:id',
      name: 'student-task-square-detail',
      component: () => import('../views/StudentTaskSquareDetailView.vue'),
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
      path: '/student/hour-progress/:id/supplement-result',
      name: 'student-hour-result-supplement',
      component: () => import('../views/StudentHourResultSupplementView.vue'),
    },
    {
      path: '/student/hour-progress/:id/extension',
      name: 'student-hour-extension',
      component: () => import('../views/StudentHourExtensionView.vue'),
    },
    { path:'/student/feedback',name:'student-feedback-home',component:()=>import('../views/StudentFeedbackHomeView.vue') },
    { path:'/student/appeals/new',name:'student-appeal-create',component:()=>import('../views/StudentAppealCreateView.vue') },
    { path:'/student/appeals',name:'student-appeals',component:()=>import('../views/StudentAppealsView.vue') },
    { path:'/student/appeals/:id',name:'student-appeal-detail',component:()=>import('../views/StudentAppealDetailView.vue') },
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
      path: '/teacher/tasks',
      name: 'teacher-tasks',
      component: () => import('../views/TeacherTaskListView.vue'),
    },
    {
      path: '/teacher/tasks/:id',
      name: 'teacher-task-detail',
      component: () => import('../views/TeacherTaskDetailView.vue'),
    },
    {
      path: '/teacher/tasks/:id/applicants',
      name: 'teacher-task-applicants',
      component: () => import('../views/TeacherTaskApplicantsView.vue'),
    },
    {
      path: '/teacher/tasks/:id/applicants/select',
      name: 'teacher-task-applicant-selection',
      component: () => import('../views/TeacherTaskApplicantSelectionView.vue'),
    },
    {
      path: '/teacher/tasks/:id/leader',
      name: 'teacher-task-leader',
      component: () => import('../views/TeacherTaskLeaderView.vue'),
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
      path: '/teacher/confirm/results',
      name: 'teacher-task-result-confirm',
      component: () => import('../views/TeacherTaskResultConfirmListView.vue'),
    },
    {
      path: '/teacher/confirm/results/:id',
      name: 'teacher-task-result-confirm-detail',
      component: () => import('../views/TeacherTaskResultConfirmDetailView.vue'),
    },
    {
      path: '/teacher/confirm/supplements',
      name: 'teacher-supplement-confirm',
      component: () => import('../views/TeacherSupplementConfirmListView.vue'),
    },
    {
      path: '/teacher/confirm/supplements/:id',
      name: 'teacher-supplement-confirm-detail',
      component: () => import('../views/TeacherSupplementConfirmDetailView.vue'),
    },
    {
      path: '/teacher/confirm/extensions',
      name: 'teacher-normal-extension-confirm',
      component: () => import('../views/TeacherNormalExtensionListView.vue'),
    },
    {
      path: '/teacher/confirm/extensions/:id',
      name: 'teacher-normal-extension-confirm-detail',
      component: () => import('../views/TeacherNormalExtensionDetailView.vue'),
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
    { path:'/reviewer/appeal-reviews',name:'reviewer-appeal-reviews',redirect:'/reviewer/review-tasks' },
    { path:'/reviewer/appeal-reviews/:id',name:'reviewer-appeal-review-detail',component:()=>import('../views/ReviewerAppealDetailView.vue') },
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
    { path:'/admin/appeals-complaints',name:'admin-appeals',component:()=>import('../views/AdminAppealsView.vue') },
    { path:'/admin/appeals-complaints/assign',name:'admin-appeal-assignment',component:()=>import('../views/AdminAppealAssignmentListView.vue') },
    { path:'/admin/appeals-complaints/assign/:id',name:'admin-appeal-assignment-detail',component:()=>import('../views/AdminAppealAssignmentDetailView.vue') },
    { path:'/admin/appeals-complaints/:id',name:'admin-appeal-detail',component:()=>import('../views/AdminAppealDetailView.vue') },
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
      path: '/admin/extensions',
      name: 'admin-special-extension-review',
      component: () => import('../views/AdminSpecialExtensionListView.vue'),
    },
    {
      path: '/admin/extensions/:id',
      name: 'admin-special-extension-review-detail',
      component: () => import('../views/AdminSpecialExtensionDetailView.vue'),
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
