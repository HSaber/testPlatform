import { createRouter, createWebHistory } from 'vue-router'
import TestCaseList from '../views/TestCaseList.vue'
import TestCaseForm from '../views/TestCaseForm.vue'

const routes = [
  {
    path: '/',
    name: 'TestCaseList',
    component: TestCaseList
  },
  {
    path: '/create',
    name: 'CreateTestCase',
    component: TestCaseForm
  },
  // 之后我们会添加编辑页面的路由
  // {
  //   path: '/edit/:id',
  //   name: 'EditTestCase',
  //   component: TestCaseForm
  // }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router