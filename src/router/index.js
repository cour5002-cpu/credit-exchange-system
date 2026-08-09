import { createRouter, createWebHistory } from 'vue-router'
import { authState, getHomePath, getPortalRole, restoreSession } from '../stores/authStore.js'

const placeholderRoutes = [
  ['/student/feedback', 'student-feedback', '问题反馈', '提交使用过程中遇到的问题。'],
  ['/student/notifications', 'student-notifications', '信息通知', '查看学生端通知消息。'],
  ['/teacher/notifications', 'teacher-notifications', '信息通知', '查看指导老师端通知消息。'],
  ['/reviewer/notifications', 'reviewer-notifications', '信息通知', '查看审核老师端通知消息。'],
  ['/admin/appeals-complaints', 'admin-appeals-complaints', '申诉与投诉', '处理用户提交的申诉与投诉。'],
  ['/admin/extensions', 'admin-extensions', '特殊延期', '管理特殊情况的延期申请。'],
  ['/admin/notifications', 'admin-notifications', '信息通知', '查看管理员端通知消息。'],
].filter(([path]) => !['/student/notifications','/teacher/notifications','/reviewer/notifications','/admin/notifications'].includes(path)).map(([path, name, title, description]) => ({
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
    { path:'/student/notifications',name:'student-notification-list',component:()=>import('../views/NotificationListView.vue'),props:{role:'student',userId:'2024001',pageCode:'S301',portalName:'学生端',backPath:'/student/dashboard',detailBase:'/student/notifications'} },
    { path:'/student/notifications/:id',name:'student-notification-detail',component:()=>import('../views/NotificationDetailView.vue'),props:{role:'student',userId:'2024001',pageCode:'S302',listPath:'/student/notifications'} },
    { path:'/teacher/notifications',name:'teacher-notification-list',component:()=>import('../views/NotificationListView.vue'),props:{role:'advisor',userId:'T001',pageCode:'T801',portalName:'指导老师端',backPath:'/teacher/dashboard',detailBase:'/teacher/notifications'} },
    { path:'/teacher/notifications/:id',name:'teacher-notification-detail',component:()=>import('../views/NotificationDetailView.vue'),props:{role:'advisor',userId:'T001',pageCode:'T802',listPath:'/teacher/notifications'} },
    { path:'/reviewer/notifications',name:'reviewer-notification-list',component:()=>import('../views/NotificationListView.vue'),props:{role:'reviewer',userId:'reviewer001',pageCode:'R501',portalName:'审核老师端',backPath:'/reviewer/dashboard',detailBase:'/reviewer/notifications'} },
    { path:'/reviewer/notifications/:id',name:'reviewer-notification-detail',component:()=>import('../views/NotificationDetailView.vue'),props:{role:'reviewer',userId:'reviewer001',pageCode:'R502',listPath:'/reviewer/notifications'} },
    { path:'/admin/notifications',name:'admin-notification-list',component:()=>import('../views/NotificationListView.vue'),props:{role:'admin',userId:'ADMIN001',pageCode:'A1101',portalName:'管理端',backPath:'/admin/dashboard',detailBase:'/admin/notifications'} },
    { path:'/admin/notifications/:id',name:'admin-notification-detail',component:()=>import('../views/NotificationDetailView.vue'),props:{role:'admin',userId:'ADMIN001',pageCode:'A1102',listPath:'/admin/notifications'} },
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
    { path:'/student/complaints/new',name:'student-complaint-create',component:()=>import('../views/StudentComplaintCreateView.vue') },
    { path:'/student/complaints/submitted/:id',name:'student-complaint-result',component:()=>import('../views/StudentComplaintResultView.vue') },
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
    { path:'/reviewer/appeal-reviews',name:'reviewer-appeal-reviews',component:()=>import('../views/ReviewerAppealListView.vue') },
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
    {
      path: '/admin/statistics',
      name: 'admin-statistics',
      component: () => import('../views/AdminStatisticsView.vue'),
    },
    {
      path: '/admin/rule-files',
      name: 'admin-rule-files',
      component: () => import('../views/AdminRuleFilesView.vue'),
    },
    {
      path: '/admin/processed-records',
      name: 'admin-processed-records',
      redirect: '/admin/tasks/processed-records',
    },
    { path:'/admin/appeals-complaints',name:'admin-appeals',component:()=>import('../views/AdminAppealsView.vue') },
    { path:'/admin/appeals-complaints/assign',name:'admin-appeal-assignment',component:()=>import('../views/AdminAppealAssignmentListView.vue') },
    { path:'/admin/appeals-complaints/assign/:id',name:'admin-appeal-assignment-detail',component:()=>import('../views/AdminAppealAssignmentDetailView.vue') },
    { path:'/admin/appeals-complaints/complaints',name:'admin-complaints',component:()=>import('../views/AdminComplaintListView.vue') },
    { path:'/admin/appeals-complaints/complaints/:id',name:'admin-complaint-detail',component:()=>import('../views/AdminComplaintDetailView.vue') },
    { path:'/admin/appeals-complaints/final-confirm',redirect:'/admin/final-confirm/appeals' },
    { path:'/admin/appeals-complaints/final-confirm/:id',redirect:(to)=>`/admin/final-confirm/appeals/${to.params.id}` },
    { path:'/admin/appeals-complaints/:id',name:'admin-appeal-detail',component:()=>import('../views/AdminAppealDetailView.vue') },
    {
      path: '/admin/tasks',
      name: 'admin-tasks',
      component: () => import('../views/AdminTasksView.vue'),
    },
    {
      path: '/admin/tasks/list',
      name: 'admin-task-list',
      component: () => import('../views/AdminTaskListView.vue'),
    },
    {
      path: '/admin/tasks/list/:id',
      name: 'admin-task-detail',
      component: () => import('../views/AdminTaskDetailView.vue'),
    },
    {
      path: '/admin/tasks/publish',
      name: 'admin-task-publish',
      component: () => import('../views/AdminTaskPublishView.vue'),
    },
    {
      path: '/admin/tasks/processed-records',
      name: 'admin-task-processed-records',
      component: () => import('../views/AdminProcessedRecordsView.vue'),
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
      path: '/admin/final-confirm/appeals',
      name: 'admin-appeal-final-confirm',
      component: () => import('../views/AdminAppealFinalConfirmListView.vue'),
    },
    {
      path: '/admin/final-confirm/appeals/:id',
      name: 'admin-appeal-final-confirm-detail',
      component: () => import('../views/AdminAppealFinalConfirmDetailView.vue'),
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

function getRequiredRole(path) {
  if (path.startsWith('/student/')) return 'student'
  if (path.startsWith('/teacher/')) return 'advisor'
  if (path.startsWith('/reviewer/')) return 'reviewer'
  if (path.startsWith('/admin/')) return 'admin'
  return null
}

router.beforeEach(async (to) => {
  if (to.path === '/login') {
    if (authState.initialized) return authState.user ? getHomePath(authState.user) : true
    restoreSession()
      .then((user) => {
        if (user && router.currentRoute.value.path === '/login') router.replace(getHomePath(user))
      })
      .catch((error) => {
        console.warn('[auth] 后台恢复会话失败，继续显示登录页。', error)
      })
    return true
  }

  let user
  try {
    user = await restoreSession()
  } catch (error) {
    // 非认证类网络/服务端错误保留到登录页展示，避免进入受保护页面。
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  if (!user) return { path: '/login', query: { redirect: to.fullPath } }

  const requiredRole = getRequiredRole(to.path)
  if (requiredRole && requiredRole !== getPortalRole(authState.user)) return getHomePath(user)
  return true
})

export default router
