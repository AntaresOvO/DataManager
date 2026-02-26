import { createRouter, createWebHistory } from 'vue-router'
import { getToken, getUserInfo } from '../utils/storage'

const routes = [
  { path: '/login', component: () => import('../views/Login.vue') },
  { path: '/401', component: () => import('../views/Forbidden.vue') },
  { path: '/:pathMatch(.*)*', component: () => import('../views/NotFound.vue') },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    redirect: '/home',
    children: [
      { path: 'home', component: () => import('../views/Home.vue') },
      { path: 'templates', component: () => import('../views/Templates.vue') },
      { path: 'forms', component: () => import('../views/Forms.vue') },
      { path: 'form-browser', component: () => import('../views/FormBrowser.vue') },
      { path: 'form-sheet', component: () => import('../views/FormSheet.vue') },
      { path: 'dashboard-config', component: () => import('../views/DashboardConfig.vue') },
      { path: 'system/users', component: () => import('../views/Users.vue'), meta: { admin: true } },
      { path: 'system/logs', component: () => import('../views/Logs.vue'), meta: { admin: true } },
      { path: 'system/profile', component: () => import('../views/Profile.vue') }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const whiteList = ['/login', '/401', '/404']

router.beforeEach((to, from, next) => {
  if (whiteList.includes(to.path)) return next()

  const token = getToken()
  if (!token) return next('/login')

  const user = getUserInfo()
  if (user?.need_change_pwd && to.path !== '/system/profile') {
    return next('/system/profile')
  }

  if (to.meta.admin && user?.role !== 'admin') {
    return next('/401')
  }

  next()
})

export default router
