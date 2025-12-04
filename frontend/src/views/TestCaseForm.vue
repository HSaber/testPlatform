<template>
  <div class="test-case-form-container">
    <h1>创建新用例</h1>
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
        <el-button type="primary" @click="submitForm">立即创建</el-button>
        <el-button @click="goBack">取消</el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { createTestCase } from '@/api';
import { ElMessage } from 'element-plus';

const router = useRouter();
const testCaseForm = ref(null);
const bodyContentType = ref('application/json');

const form = ref({
  name: '',
  description: '',
  priority: 0,
  method: 'GET',
  url: '',
  headers: [{key: 'Content-Type', value: 'application/json'}],
  body_json: '',
  body_form_data: [],
  assertions: [],
});

const handleContentTypeChange = (value) => {
    const contentTypeHeaderIndex = form.value.headers.findIndex(h => h.key.toLowerCase() === 'content-type');
    if (contentTypeHeaderIndex > -1) {
        form.value.headers[contentTypeHeaderIndex].value = value;
    } else {
        form.value.headers.push({ key: 'Content-Type', value: value });
    }
};

const addHeader = () => {
  form.value.headers.push({ key: '', value: '' });
};

const removeHeader = (index) => {
  form.value.headers.splice(index, 1);
};

const addFormDataField = () => {
  form.value.body_form_data.push({ key: '', value: '' });
};

const removeFormDataField = (index) => {
  form.value.body_form_data.splice(index, 1);
};

const addAssertion = () => {
  form.value.assertions.push({ check: '', comparator: 'contains', expect: '' });
};

const removeAssertion = (index) => {
  form.value.assertions.splice(index, 1);
};

const goBack = () => {
  router.push('/');
};

const submitForm = async () => {
  // Trim the URL value before processing
  form.value.url = form.value.url.trim();

  // 预处理数据
  const headersObject = form.value.headers.reduce((acc, cur) => {
    if (cur.key) acc[cur.key] = cur.value;
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
    priority: form.value.priority,
    method: form.value.method,
    url: form.value.url,
    headers: headersObject,
    body: requestBody,
    assertions: processedAssertions,
  };

  try {
    await createTestCase(payload);
    ElMessage.success('用例创建成功！');
    router.push('/');
  } catch (error) {
    console.error('创建用例失败:', error);
    ElMessage.error('创建用例失败，请检查控制台输出。');
  }
};

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