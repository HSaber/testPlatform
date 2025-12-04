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
// 测试用例排序
export const apiReorderTestCases = (testCaseIds) => {
  return apiClient.post(`/testcases/reorder`, { test_case_ids: testCaseIds });
};

// 删除测试用例
export const apiDeleteTestCase = (testCaseId) => {
  return apiClient.delete(`/testcases/${testCaseId}`);
};

// 更新测试用例
export const apiUpdateTestCase = (testCaseId, testCaseData) => {
  return apiClient.put(`/testcases/${testCaseId}`, testCaseData);
};

// 创建测试用例
export const createTestCase = (testCaseData) => {
    return apiClient.post('/testcases', testCaseData);
};