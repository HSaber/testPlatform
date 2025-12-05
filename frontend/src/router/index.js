import { createRouter, createWebHistory } from 'vue-router'
import TestCaseList from '../views/TestCaseList.vue'
import TestCaseForm from '../views/TestCaseForm.vue'
import ModuleManagement from '../views/ModuleManagement.vue'
// 1. 导入组件
import TestSuiteManagement from '../views/TestSuiteManagement.vue'
import TestReportList from '../views/TestReportList.vue'
import TestReportDetail from '../views/TestReportDetail.vue'

const routes = [
  {
    path: '/',
    name: 'TestCaseList',
    component: TestCaseList
  },
  {
    path: '/modules',
    name: 'ModuleManagement',
    component: ModuleManagement
  },
  // 2. 添加路由配置
  {
    path: '/suites',
    name: 'TestSuiteManagement',
    component: TestSuiteManagement
  },
  {
    path: '/reports',
    name: 'TestReportList',
    component: TestReportList
  },
  {
    path: '/reports/:id',
    name: 'TestReportDetail',
    component: TestReportDetail
  },
  {
    path: '/create',
    name: 'CreateTestCase',
    component: TestCaseForm
  },
  {
    path: '/edit/:id',
    name: 'EditTestCase',
    component: TestCaseForm
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router