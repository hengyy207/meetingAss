// 路由配置：4 个页面
import { createRouter, createWebHistory } from 'vue-router'

import Home from '../views/Home.vue'
import CreateMeeting from '../views/CreateMeeting.vue'
import MeetingDetail from '../views/MeetingDetail.vue'
import History from '../views/History.vue'
import RealtimeMeeting from '../views/RealtimeMeeting.vue'

const routes = [
  { path: '/', name: 'home', component: Home },
  { path: '/create', name: 'create', component: CreateMeeting },
  { path: '/meeting/:id', name: 'detail', component: MeetingDetail },
  { path: '/history', name: 'history', component: History },
  { path: '/realtime', name: 'realtime', component: RealtimeMeeting },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
