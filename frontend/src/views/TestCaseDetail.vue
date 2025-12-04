<template>
  <el-drawer
    :model-value="visible"
    title="用例详情"
    direction="rtl"
    @close="handleClose"
    size="50%"
  >
    <div class="detail-container" v-if="testCaseData">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="ID">{{ testCaseData.id }}</el-descriptions-item>
        <el-descriptions-item label="用例名称">{{ testCaseData.name }}</el-descriptions-item>
        <el-descriptions-item label="模块">
          {{ testCaseData.module_obj ? testCaseData.module_obj.name : (testCaseData.module || '默认') }}
        </el-descriptions-item>
        <el-descriptions-item label="描述">{{ testCaseData.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="请求方法">
          <el-tag :type="getMethodTagType(testCaseData.method)">{{ testCaseData.method }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="URL">{{ testCaseData.url }}</el-descriptions-item>
        <el-descriptions-item label="Content-Type">{{ testCaseData.content_type || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div class="section-title">请求头 (Headers)</div>
      <div class="code-block">
        <pre>{{ jsonToString(testCaseData.headers) }}</pre>
      </div>

      <div class="section-title">请求体 (Body)</div>
      <div class="code-block">
        <pre>{{ jsonToString(testCaseData.body) }}</pre>
      </div>

      <div class="section-title">提取规则</div>
      <div class="code-block">
        <pre>{{ jsonToString(testCaseData.extract_rules) }}</pre>
      </div>

      <div class="section-title">断言</div>
      <div class="code-block">
        <pre>{{ jsonToString(testCaseData.assertions) }}</pre>
      </div>
    </div>
    <div v-else>
      <p>没有可显示的用例数据。</p>
    </div>
    <!-- 移除底部保存按钮，只读模式不需要 -->
  </el-drawer>
</template>

<script setup>
import { defineProps, defineEmits, ref, watch } from 'vue';

const props = defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
  testCase: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(['close']);

const testCaseData = ref(null);

watch(() => props.testCase, (newVal) => {
  if (newVal) {
    testCaseData.value = JSON.parse(JSON.stringify(newVal));
  } else {
    testCaseData.value = null;
  }
}, { immediate: true, deep: true });

const jsonToString = (json) => {
    if (json === null || json === undefined) return '';
    // 如果是空对象或空数组，显示 '-'
    if (typeof json === 'object' && Object.keys(json).length === 0) return '-';
    try {
        return JSON.stringify(json, null, 2);
    } catch (e) {
        return String(json);
    }
}

const getMethodTagType = (method) => {
  const map = {
    'GET': 'success',
    'POST': 'primary',
    'PUT': 'warning',
    'DELETE': 'danger'
  };
  return map[method] || 'info';
}

const handleClose = () => {
  emit('close');
};
</script>

<style scoped>
.detail-container {
  padding: 20px;
}
.section-title {
  margin-top: 20px;
  margin-bottom: 10px;
  font-weight: bold;
  color: #303133;
  border-left: 4px solid #409EFF;
  padding-left: 10px;
}
.code-block {
  background-color: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
  overflow-x: auto;
}
.code-block pre {
  margin: 0;
  font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.5;
}
</style>