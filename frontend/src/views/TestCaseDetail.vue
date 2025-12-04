<template>
  <el-drawer
    :model-value="visible"
    :title="isEditMode ? '编辑用例' : '用例详情'"
    direction="rtl"
    @close="handleClose"
    size="50%"
  >
    <div class="detail-container" v-if="testCaseData">
      <el-form :model="testCaseData" label-width="120px" ref="formRef">
        <el-form-item label="用例名称" prop="name">
          <el-input v-model="testCaseData.name"></el-input>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input type="textarea" v-model="testCaseData.description"></el-input>
        </el-form-item>
        <el-form-item label="请求方法" prop="method">
            <el-select v-model="testCaseData.method" placeholder="请选择请求方法">
                <el-option label="GET" value="GET"></el-option>
                <el-option label="POST" value="POST"></el-option>
                <el-option label="PUT" value="PUT"></el-option>
                <el-option label="DELETE" value="DELETE"></el-option>
            </el-select>
        </el-form-item>
        <el-form-item label="URL" prop="url">
          <el-input v-model="testCaseData.url"></el-input>
        </el-form-item>
        <el-form-item label="Content-Type" prop="content_type">
          <el-input v-model="testCaseData.content_type"></el-input>
        </el-form-item>
        <el-form-item label="请求头 (Headers)" prop="headers">
          <el-input type="textarea" :rows="5" v-model="editableHeaders"></el-input>
        </el-form-item>
        <el-form-item label="请求体 (Body)" prop="body">
          <el-input type="textarea" :rows="8" v-model="editableBody"></el-input>
        </el-form-item>
        <el-form-item label="提取规则" prop="extract_rules">
          <el-input type="textarea" :rows="5" v-model="editableExtractRules"></el-input>
        </el-form-item>
        <el-form-item label="断言" prop="assertions">
          <el-input type="textarea" :rows="5" v-model="editableAssertions"></el-input>
        </el-form-item>
      </el-form>
    </div>
    <div v-else>
      <p>没有可显示的用例数据。</p>
    </div>
    <template #footer>
      <div style="flex: auto">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
import { defineProps, defineEmits, ref, watch, computed } from 'vue';

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

const emit = defineEmits(['close', 'save']);

const testCaseData = ref(null);
const formRef = ref(null);

const isEditMode = computed(() => !!props.testCase);

watch(() => props.testCase, (newVal) => {
  if (newVal) {
    testCaseData.value = JSON.parse(JSON.stringify(newVal));
  } else {
    testCaseData.value = null;
  }
}, { immediate: true, deep: true });


const jsonToString = (json) => {
    if (json === null || json === undefined) return '';
    try {
        return JSON.stringify(json, null, 2);
    } catch (e) {
        return '';
    }
}

const stringToJson = (str) => {
    if (!str) return null;
    try {
        return JSON.parse(str);
    } catch (e) {
        // 可以选择在这里处理错误，例如返回一个错误提示
        console.error("Invalid JSON string:", e);
        return null; 
    }
}

const editableHeaders = computed({
    get: () => jsonToString(testCaseData.value?.headers),
    set: (val) => { if(testCaseData.value) testCaseData.value.headers = stringToJson(val) }
})

const editableBody = computed({
    get: () => jsonToString(testCaseData.value?.body),
    set: (val) => { if(testCaseData.value) testCaseData.value.body = stringToJson(val) }
})

const editableExtractRules = computed({
    get: () => jsonToString(testCaseData.value?.extract_rules),
    set: (val) => { if(testCaseData.value) testCaseData.value.extract_rules = stringToJson(val) }
})

const editableAssertions = computed({
    get: () => jsonToString(testCaseData.value?.assertions),
    set: (val) => { if(testCaseData.value) testCaseData.value.assertions = stringToJson(val) }
})


const handleClose = () => {
  emit('close');
};

const handleSave = () => {
  emit('save', testCaseData.value);
};

</script>

<style scoped>
.detail-container {
  padding: 20px;
}
</style>