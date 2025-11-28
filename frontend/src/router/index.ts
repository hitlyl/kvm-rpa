import { createRouter, createWebHashHistory, RouteRecordRaw } from 'vue-router'
import FlowList from '@/views/FlowList.vue'
import FlowEditor from '@/views/FlowEditor.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/flows'
  },
  {
    path: '/flows',
    name: 'FlowList',
    component: FlowList
  },
  {
    path: '/flows/editor/:id?',
    name: 'FlowEditor',
    component: FlowEditor
  }
]

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes
})

export default router

