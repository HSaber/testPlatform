<template>
  <div class="test-case-form-container">
    <h1>{{ isEditMode ? '编辑用例' : '创建新用例' }}</h1>
    <el-form :model="form" ref="testCaseForm" label-width="120px" class="form-wrapper">
      <el-card class="box-card">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
          </div>
        </template>
        <el-form-item label="用例名称" prop="name" required>
          <el-input v-model="form.name"></el-input>
        </el-form-item>
        <el-form-item label="用例描述" prop="description">
          <el-input type="textarea" v-model="form.description" placeholder="请输入用例描述"></el-input>
        </el-form-item>
        <el-form-item label="模块" prop="module_id">
           <el-tree-select
            v-model="form.module_id"
            :data="moduleOptions"
            :render-after-expand="false"
            check-strictly
            placeholder="请选择模块"
            clearable
            filterable
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-input-number v-model="form.priority" :min="0" label="优先级"></el-input-number>
        </el-form-item>
        <el-form-item label="请求方法" prop="method" required>
          <el-select v-model="form.method" placeholder="请选择请求方法">
            <el-option label="GET" value="GET"></el-option>
            <el-option label="POST" value="POST"></el-option>
            <el-option label="PUT" value="PUT"></el-option>
            <el-option label="DELETE" value="DELETE"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="请求URL" prop="url" required>
          <el-input v-model="form.url"></el-input>
        </el-form-item>
      </el-card>

      <el-card class="box-card">
        <template #header>
          <div class="card-header">
            <span>请求头 (Headers)</span>
            <el-button class="button" type="text" @click="addHeader">添加一项</el-button>
          </div>
        </template>
        <div v-for="(header, index) in form.headers" :key="index" class="dynamic-item">
          <el-input v-model="header.key" placeholder="Key" class="input-with-select"></el-input>
          <el-input v-model="header.value" placeholder="Value" class="input-with-select"></el-input>
          <el-button type="danger" @click.prevent="removeHeader(index)">删除</el-button>
        </div>
      </el-card>

      <el-card class="box-card">
        <template #header>
          <div class="card-header">
            <span>请求体 (Body)</span>
          </div>
        </template>
        <el-form-item label="Content-Type">
          <el-select v-model="bodyContentType" placeholder="Select" @change="handleContentTypeChange" style="width: 100%;">
            <el-option label="application/json" value="application/json"></el-option>
            <el-option label="application/x-www-form-urlencoded" value="application/x-www-form-urlencoded"></el-option>
          </el-select>
        </el-form-item>

        <div v-if="bodyContentType === 'application/json'">
          <el-input
            v-model="form.body_json"
            :rows="5"
            type="textarea"
            placeholder="请输入JSON格式的请求体"
          />
        </div>

        <div v-if="bodyContentType === 'application/x-www-form-urlencoded'">
            <div v-for="(item, index) in form.body_form_data" :key="index" class="dynamic-item">
              <el-input v-model="item.key" placeholder="Key"></el-input>
              <el-input v-model="item.value" placeholder="Value"></el-input>
              <el-button type="danger" @click.prevent="removeFormDataField(index)">删除</el-button>
            </div>
            <el-button @click="addFormDataField" type="primary" plain>添加字段</el-button>
        </div>
      </el-card>

      <el-card class="box-card">
        <template #header>
          <div class="card-header">
            <span>提取规则 (Extract Rules)</span>
            <el-button class="button" type="text" @click="addExtractRule">添加一项</el-button>
          </div>
        </template>
        <div v-for="(rule, index) in form.extract_rules" :key="index" class="dynamic-item">
          <el-input v-model="rule.name" placeholder="变量名 (e.g. token)" class="input-with-select"></el-input>
          <el-input v-model="rule.expression" placeholder="提取表达式 (e.g. json.data.token)" class="input-with-select"></el-input>
          <el-button type="danger" @click.prevent="removeExtractRule(index)">删除</el-button>
        </div>
      </el-card>

      <el-card class="box-card">
        <template #header>
          <div class="card-header">
            <span>断言规则 (Assertions)</span>
            <el-button class="button" type="text" @click="addAssertion">添加一项</el-button>
          </div>
        </template>
        <div v-for="(assertion, index) in form.assertions" :key="index" class="dynamic-item assertion-item">
          <el-input class="assertion-check" v-model="assertion.check" placeholder="检查点 (e.g., status_code, json.data.user_id)"></el-input>
          <el-select class="assertion-comparator" v-model="assertion.comparator" placeholder="比较器">
            <el-option label="contains" value="contains"></el-option>
            <el-option label="json_equals" value="json_equals"></el-option>
          </el-select>
          <el-input
            class="assertion-expect"
            v-model="assertion.expect" 
            placeholder="期望值"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 10 }"
          ></el-input>
          <el-button type="danger" @click.prevent="removeAssertion(index)">删除</el-button>
        </div>
      </el-card>

      <el-card class="box-card">
        <template #header>
          <div class="card-header">
            <span>脚本 (Scripts)</span>
          </div>
        </template>
        <el-form-item label="前置脚本">
          <el-input
            v-model="form.setup_script"
            type="textarea"
            :rows="5"
            placeholder="请输入Python代码，在请求发送前执行。可操作 variables 字典。"
          ></el-input>
        </el-form-item>
        <el-form-item label="后置脚本">
          <el-input
            v-model="form.teardown_script"
            type="textarea"
            :rows="5"
            placeholder="请输入Python代码，在请求发送后执行。可操作 variables 字典。"
          ></el-input>
        </el-form-item>
      </el-card>

      <div class="form-buttons">
        <el-button type="primary" @click="submitForm" :loading="isSaving">{{ isEditMode ? '保存修改' : '立即创建' }}</el-button>
        <el-button @click="goBack">取消</el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { apiCreateTestCase, apiUpdateTestCase, apiGetTestCaseDetail, apiGetTestModules, apiDebugTestCase } from '../api';

const route = useRoute();
const router = useRouter();
const testCaseForm = ref(null);
const bodyContentType = ref('application/json');
const moduleOptions = ref([]); // 存储模块树形数据

// Debug related refs
const isDebugVisible = ref(false);
const debugLoading = ref(false);
const debugResult = ref(null);
const isSaving = ref(false);

const isEditMode = computed(() => !!route.params.id);
const modules = ref([]);

const form = ref({
  name: '',
  module_id: '',
  description: '',
  module_id: null, // 修改为 module_id，初始为 null
  priority: 0,
  method: 'GET',
  url: '',
  headers: [{key: 'Content-Type', value: 'application/json'}],
  body_json: '',
  body_form_data: [],
  extract_rules: [],
  assertions: [],
  setup_script: '',
  teardown_script: '',
});

const goBack = () => {
  router.push('/');
};

// 将平铺的模块列表转换为树形结构
const transformToTree = (items) => {
  const result = [];
  const itemMap = {};

  // 1. 初始化 map，并处理每个节点
  items.forEach(item => {
    itemMap[item.id] = { 
      ...item, 
      value: item.id, 
      label: item.name, 
      children: [] 
    };
  });

  // 2. 构建树
  items.forEach(item => {
    const treeItem = itemMap[item.id];
    if (item.parent_id && itemMap[item.parent_id]) {
      itemMap[item.parent_id].children.push(treeItem);
    } else {
      result.push(treeItem);
    }
  });

  return result;
};

const loadModules = async () => {
  try {
    const response = await apiGetTestModules();
    // 假设后端返回的是平铺的列表，如果后端已经是树形，则不需要 transformToTree
    // 这里为了保险，先假设是平铺的（这也是通常 get_multi 的默认行为）
    // 如果后端返回数据里包含 children 且是嵌套的，这个逻辑可能需要调整
    // 但根据通常的 CRUD 实现，get_multi 返回的是 list
    moduleOptions.value = transformToTree(response.data);
  } catch (error) {
    console.error('Failed to load modules:', error);
    ElMessage.error('加载模块数据失败');
  }
};

// Headers 操作
const addHeader = () => {
  form.value.headers.push({ key: '', value: '' });
};

const removeHeader = (index) => {
  form.value.headers.splice(index, 1);
};

// Body Content-Type 处理
const handleContentTypeChange = (val) => {
  const contentTypeHeader = form.value.headers.find(h => h.key.toLowerCase() === 'content-type');
  if (contentTypeHeader) {
    contentTypeHeader.value = val;
  } else {
    form.value.headers.push({ key: 'Content-Type', value: val });
  }
};

// Form Data 操作
const addFormDataField = () => {
  form.value.body_form_data.push({ key: '', value: '' });
};

const removeFormDataField = (index) => {
  form.value.body_form_data.splice(index, 1);
};

// 提取规则操作
const addExtractRule = () => {
  form.value.extract_rules.push({ name: '', expression: '' });
};

const removeExtractRule = (index) => {
  form.value.extract_rules.splice(index, 1);
};

// 断言规则操作
const addAssertion = () => {
  form.value.assertions.push({ check: '', comparator: 'json_equals', expect: '' });
};

const removeAssertion = (index) => {
  form.value.assertions.splice(index, 1);
};

const getPayload = () => {
    // Trim the URL value before processing
    const url = form.value.url.trim();

    // 预处理数据
    const headersObject = form.value.headers.reduce((acc, cur) => {
        if (cur.key) acc[cur.key] = cur.value;
        return acc;
    }, {});

    // 处理提取规则
    const extractRulesObject = form.value.extract_rules.reduce((acc, cur) => {
        if (cur.name && cur.expression) acc[cur.name] = cur.expression;
        return acc;
    }, {});

    let requestBody = null;
    if (bodyContentType.value === 'application/json') {
        requestBody = form.value.body_json ? JSON.parse(form.value.body_json) : null;
    } else {
        requestBody = form.value.body_form_data.reduce((acc, cur) => {
            if (cur.key) acc[cur.key] = cur.value;
            return acc;
        }, {});
    }

    // 转换断言期望值为正确类型
    const processedAssertions = form.value.assertions.map(a => {
        const newA = { ...a };
        try {
            // 尝试将期望值解析为JSON对象/数组或数字
            newA.expect = JSON.parse(newA.expect);
        } catch (e) {
            // 如果解析失败，则保持为字符串
        }
        return newA;
    });

    const payload = {
        name: form.value.name,
        description: form.value.description,
        module_id: form.value.module_id,
        priority: form.value.priority,
        method: form.value.method,
        url: url,
        headers: headersObject,
        body: requestBody,
        extract_rules: extractRulesObject,
        assertions: processedAssertions,
        setup_script: form.value.setup_script,
        teardown_script: form.value.teardown_script,
    };
    return payload;
};

const debugCase = async () => {
    try {
        debugLoading.value = true;
        const payload = getPayload();
        const response = await apiDebugTestCase(payload);
        debugResult.value = response.data;
        isDebugVisible.value = true;
        ElMessage.success('调试执行完成');
    } catch (error) {
        console.error('Debug failed:', error);
        ElMessage.error('调试请求失败: ' + (error.response?.data?.detail || error.message));
    } finally {
        debugLoading.value = false;
    }
};

const submitForm = async () => {
  if (isSaving.value) return;
  isSaving.value = true;
  try {
    const payload = getPayload();
    
    if (isEditMode.value) {
      await apiUpdateTestCase(route.params.id, payload);
      ElMessage.success('更新成功');
    } else {
      await apiCreateTestCase(payload);
      ElMessage.success('创建成功');
    }
    router.push('/');
  } catch (error) {
    console.error(error);
    ElMessage.error(isEditMode.value ? '更新失败' : '创建失败');
  } finally {
    isSaving.value = false;
  }
};

const loadTestCaseData = async (id) => {
  try {
    const response = await apiGetTestCaseDetail(id);
    const data = response.data;

    // 还原 headers
    const headersArray = Object.entries(data.headers || {}).map(([key, value]) => ({
      key,
      value
    }));
    // 删除此处强制添加 Content-Type 的代码

    // 还原 Body 数据逻辑优化
    let bodyJsonStr = '';
    let bodyFormDataArray = [];
    
    // 获取 Content-Type
    const contentTypeHeader = headersArray.find(h => h.key.toLowerCase() === 'content-type');
    const contentType = contentTypeHeader ? contentTypeHeader.value : 'application/json';

    if (data.body) {
        if (contentType.includes('application/json')) {
            // 如果是 JSON 类型，格式化为字符串
            try {
                bodyJsonStr = JSON.stringify(data.body, null, 2);
            } catch (e) {
                bodyJsonStr = typeof data.body === 'string' ? data.body : '';
            }
        } else {
            // 如果是表单类型，转换为数组格式
            bodyFormDataArray = Object.entries(data.body || {}).map(([key, value]) => ({
                key,
                value
            }));
        }
    }

    // 还原 extract_rules
    // 后端存储的是字典 {name: expression}，前端需要数组 [{name, expression}]
    const extractRulesArray = Object.entries(data.extract_rules || {}).map(([name, expression]) => ({
      name,
      expression
    }));

    // 处理 assertions，确保 expect 是字符串以正确显示在输入框
    const assertionsArray = (data.assertions || []).map(a => ({
      ...a,
      expect: typeof a.expect === 'object' ? JSON.stringify(a.expect) : a.expect
    }));

    form.value = {
      ...data,
      headers: headersArray,
      body_json: bodyJsonStr, // 赋值 JSON 字符串
      body_form_data: bodyFormDataArray, // 赋值 Form Data 数组
      extract_rules: extractRulesArray,
      assertions: assertionsArray,
      module_id: data.module_id, // 确保加载 module_id
      setup_script: data.setup_script || '',
      teardown_script: data.teardown_script || '',
    };

    // 设置 bodyContentType
    bodyContentType.value = contentType;

  } catch (error) {
    console.error('Failed to load test case:', error);
    ElMessage.error('加载用例数据失败');
  }
};

onMounted(() => {
  loadModules(); // 加载模块数据
  if (isEditMode.value) {
    loadTestCaseData(route.params.id);
  }
});
</script>

<style scoped>
.test-case-form-container {
  max-width: 800px;
  margin: 20px auto;
}
.form-wrapper {
  margin-top: 20px;
}
.box-card {
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.dynamic-item {
  display: flex;
  margin-bottom: 10px;
  gap: 10px;
  align-items: flex-start;
}
.assertion-item .assertion-check {
  flex: 2;
  min-width: 200px;
}
.assertion-item .assertion-comparator {
  flex: 1;
  min-width: 130px;
}
.assertion-item .assertion-expect {
  flex: 3;
  min-width: 250px;
}
.form-buttons {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>