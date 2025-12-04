import axios from 'axios';

// 创建 axios 实例，并配置后端 API 的基础 URL
// 请确保这里的端口号与您后端服务运行的端口号一致
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000', 
  headers: {
    'Content-Type': 'application/json',
  },
});

// 获取测试用例列表
export const apiGetTestCases = () => {
  return apiClient.get('/testcases/list');
};
// 获取单个测试用例详情
export const apiGetTestCaseDetail = (testCaseId) => {
  return apiClient.get(`/testcases/${testCaseId}`);
};

// 测试用例排序
export const apiReorderTestCases = (testCaseIds) => {
  return apiClient.post(`/testcases/reorder`, { test_case_ids: testCaseIds });
};

// 删除测试用例
export const apiDeleteTestCase = (id) => {
  return apiClient.delete(`/testcases/${id}`);
};

export const apiBatchDeleteTestCases = (ids) => {
  return apiClient.post('/testcases/batch', { ids });
};

export const apiGetTestModules = () => {
  return apiClient.get('/modules');
};

// 创建测试模块
export const apiCreateTestModule = (moduleData) => {
  return apiClient.post('/modules/', moduleData);
};

// 更新测试模块
export const apiUpdateTestModule = (moduleId, moduleData) => {
  return apiClient.put(`/modules/${moduleId}`, moduleData);
};

// 删除测试模块
export const apiDeleteTestModule = (moduleId) => {
  return apiClient.delete(`/modules/${moduleId}`);
};

// 更新测试用例
export const apiUpdateTestCase = (testCaseId, testCaseData) => {
  return apiClient.put(`/testcases/${testCaseId}`, testCaseData);
};

// 复制测试用例
export const apiCopyTestCase = (testCaseId) => {
  return apiClient.post(`/testcases/copy/${testCaseId}`);
};

// 创建测试用例
export const createTestCase = (testCaseData) => {
    return apiClient.post('/testcases', testCaseData);
};

// -----------------------------------------------------------------------------
// Test Suites API
// -----------------------------------------------------------------------------

// 获取测试套件列表
export const apiGetTestSuites = () => {
  return apiClient.get('/suites/');
};

// 获取单个测试套件详情
export const apiGetTestSuiteDetail = (testSuiteId) => {
  return apiClient.get(`/suites/${testSuiteId}`);
};

// 创建测试套件
export const apiCreateTestSuite = (testSuiteData) => {
  return apiClient.post('/suites/', testSuiteData);
};

// 更新测试套件
export const apiUpdateTestSuite = (testSuiteId, testSuiteData) => {
  return apiClient.put(`/suites/${testSuiteId}`, testSuiteData);
};

// 删除测试套件
export const apiDeleteTestSuite = (testSuiteId) => {
  return apiClient.delete(`/suites/${testSuiteId}`);
};

// 执行测试套件
export const apiExecuteTestSuite = (testSuiteId) => {
  return apiClient.post(`/suites/run/${testSuiteId}`);
};