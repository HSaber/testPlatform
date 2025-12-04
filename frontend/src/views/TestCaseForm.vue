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

      <div class="form-buttons">
        <el-button type="primary" @click="submitForm">{{ isEditMode ? '保存修改' : '立即创建' }}</el-button>
        <el-button @click="goBack">取消</el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { createTestCase, apiGetTestCaseDetail, apiUpdateTestCase, apiGetTestModules } from '@/api';
import { ElMessage } from 'element-plus';

const router = useRouter();
const route = useRoute();
const testCaseForm = ref(null);
const bodyContentType = ref('application/json');
const moduleOptions = ref([]); // 存储模块树形数据

const isEditMode = computed(() => !!route.params.id);

const form = ref({
  name: '',
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

const submitForm = async () => {
  // Trim the URL value before processing
  form.value.url = form.value.url.trim();

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
      try {
        // 尝试将期望值解析为JSON对象/数组或数字
        a.expect = JSON.parse(a.expect);
      } catch (e) {
        // 如果解析失败，则保持为字符串
      }
      return a;
  });

  const payload = {
    name: form.value.name,
    description: form.value.description,
    module_id: form.value.module_id, // 使用 module_id
    priority: form.value.priority,
    method: form.value.method,
    url: form.value.url,
    headers: headersObject,
    body: requestBody,
    extract_rules: extractRulesObject,
    assertions: processedAssertions,
  };

  // Remove helper properties that are not part of the API schema
  delete payload.body_json;
  delete payload.body_form_data;

  try {
    if (isEditMode.value) {
      await apiUpdateTestCase(route.params.id, payload);
      ElMessage.success('更新成功');
    } else {
      await createTestCase(payload);
      ElMessage.success('创建成功');
    }
    router.push('/');
  } catch (error) {
    console.error(error);
    ElMessage.error(isEditMode.value ? '更新失败' : '创建失败');
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
    // 确保 Content-Type 存在
    if (!headersArray.some(h => h.key.toLowerCase() === 'content-type')) {
        headersArray.push({ key: 'Content-Type', value: 'application/json' });
    }

    // 还原 body_form_data
    const formDataArray = Object.entries(data.body_form_data || {}).map(([key, value]) => ({
        key,
        value
    }));

    // 还原 extract_rules
    // 后端存储的是字典 {name: expression}，前端需要数组 [{name, expression}]
    const extractRulesArray = Object.entries(data.extract_rules || {}).map(([name, expression]) => ({
      name,
      expression
    }));

    form.value = {
      ...data,
      headers: headersArray,
      body_form_data: formDataArray,
      extract_rules: extractRulesArray,
      assertions: data.assertions || [],
      module_id: data.module_id // 确保加载 module_id
    };

    // 设置 bodyContentType
    const contentTypeHeader = headersArray.find(h => h.key.toLowerCase() === 'content-type');
    if (contentTypeHeader) {
        bodyContentType.value = contentTypeHeader.value;
    }

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

<!-- 请在此处删除所有剩余的代码，包括多余的 <template> 标签 -->