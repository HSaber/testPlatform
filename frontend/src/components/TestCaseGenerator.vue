<template>
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>API 测试用例生成器</span>
        </div>
      </template>
      <el-input
        v-model="apiDocument"
        type="textarea"
        :rows="15"
        placeholder="请粘贴 API 文档 (OpenAPI/Swagger) 的 JSON 内容"
      />
      <el-button type="primary" @click="generateTestCases" :disabled="!apiDocument || loading" :loading="loading" style="margin-top: 16px;">{{ loading ? '生成中...' : '生成测试用例' }}</el-button>
      <div v-if="testCases.length > 0" style="margin-top: 16px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
          <h3 style="margin: 0;">生成的测试用例：{{ testCases.length }} / {{ totalCount }} 条</h3>
          <div>
            <el-checkbox v-model="selectAll" :indeterminate="isIndeterminate" @change="handleSelectAll" style="margin-right: 12px;">全选</el-checkbox>
            <el-button type="success" size="small" :disabled="selectedIndices.size === 0" @click="importSelectedCases">添加至用例管理 ({{ selectedIndices.size }})</el-button>
          </div>
        </div>
        <el-progress v-if="totalCount > 0" :percentage="Math.round(testCases.length / totalCount * 100)" :status="testCases.length >= totalCount ? 'success' : ''" style="margin-bottom: 12px;" />
        <div v-for="(testCase, index) in testCases" :key="index" style="margin-bottom: 12px;">
          <el-card shadow="hover" :class="{ 'is-selected': selectedIndices.has(index) }">
            <div style="display: flex; align-items: flex-start;">
              <el-checkbox :model-value="selectedIndices.has(index)" @change="toggleSelect(index)" style="margin-right: 12px; margin-top: 2px;" />
              <div style="flex: 1;">
                <p><el-tag type="info" size="small" style="margin-right: 6px;">#{{ index + 1 }}</el-tag><b>{{ testCase.name }}</b> <el-tag size="small">{{ testCase.method }}</el-tag></p>
                <p style="color: #666;">{{ testCase.url }}</p>
                <p v-if="testCase.description" style="font-size: 13px;">{{ testCase.description }}</p>
              </div>
            </div>
          </el-card>
        </div>
      </div>
      <div v-else-if="errorMessage">
        <el-alert :title="errorMessage" type="error" />
      </div>

      <el-dialog v-model="importDialogVisible" title="选择用例模块" width="480px" @open="loadModules">
        <el-tree-select
          v-model="selectedModuleId"
          :data="moduleOptions"
          check-strictly
          :render-after-expand="false"
          placeholder="请选择所属模块"
          clearable
          filterable
          style="width: 100%"
        />
        <template #footer>
          <el-button @click="importDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="doImportCases">确定导入 ({{ selectedIndices.size }})</el-button>
        </template>
      </el-dialog>
    </el-card>
  </template>

  <script>
  import { ref, computed } from 'vue';
  import { apiGenerateTestCases, apiGenerateTestCasesBatch, apiImportTestCases, apiGetTestModules } from '../api';
  import { ElMessage, ElMessageBox } from 'element-plus';

  export default {
    setup() {
      const apiDocument = ref('');
      const testCases = ref([]);
      const errorMessage = ref('');
      const loading = ref(false);
      const totalCount = ref(0);
      const selectedIndices = ref(new Set());
      let batchContext = null;

      const selectAll = computed({
        get: () => testCases.value.length > 0 && selectedIndices.value.size === testCases.value.length,
        set: () => {}
      });
      const isIndeterminate = computed(() => selectedIndices.value.size > 0 && selectedIndices.value.size < testCases.value.length);

      const handleSelectAll = (val) => {
        if (val) {
          selectedIndices.value = new Set(testCases.value.map((_, i) => i));
        } else {
          selectedIndices.value = new Set();
        }
      };

      const toggleSelect = (index) => {
        const newSet = new Set(selectedIndices.value);
        if (newSet.has(index)) {
          newSet.delete(index);
        } else {
          newSet.add(index);
        }
        selectedIndices.value = newSet;
      };

      const importDialogVisible = ref(false);
      const selectedModuleId = ref(null);
      const moduleOptions = ref([]);

      const transformToTree = (items) => {
        const result = [];
        const itemMap = {};
        items.forEach(item => {
          itemMap[item.id] = { ...item, value: item.id, label: item.name, children: [] };
        });
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
          moduleOptions.value = transformToTree(response.data);
        } catch {
          ElMessage.error('加载模块列表失败');
        }
      };

      const importSelectedCases = () => {
        if (selectedIndices.value.size === 0) return;
        importDialogVisible.value = true;
      };

      const doImportCases = () => {
        const selected = [];
        for (const idx of selectedIndices.value) {
          selected.push(testCases.value[idx]);
        }
        apiImportTestCases(selected, selectedModuleId.value)
          .then(response => {
            ElMessage.success(`成功导入 ${response.data.created_count} 条测试用例到用例管理！`);
            selectedIndices.value = new Set();
            importDialogVisible.value = false;
            selectedModuleId.value = null;
          })
          .catch(error => {
            ElMessage.error(error.response?.data?.detail || '导入测试用例失败！');
          });
      };

      const fetchNextBatch = async () => {
        const response = await apiGenerateTestCasesBatch(batchContext);
        const data = response.data;
        testCases.value = [...testCases.value, ...data.test_cases];
        batchContext = data.batch_context;

        if (data.done) {
          loading.value = false;
          ElMessage.success('所有测试用例生成完毕！');
          return;
        }

        const remaining = data.total - data.generated_count;
        try {
          await ElMessageBox.confirm(
            `已生成 ${data.generated_count} / ${data.total} 条，还有 ${remaining} 条待生成。是否继续？`,
            '继续生成测试用例',
            { confirmButtonText: '继续生成', cancelButtonText: '结束', type: 'info' }
          );
          await fetchNextBatch();
        } catch {
          loading.value = false;
          ElMessage.info(`已停止，共生成 ${testCases.value.length} 条测试用例`);
        }
      };

      const generateTestCases = () => {
        if (!apiDocument.value) {
          errorMessage.value = '请粘贴 API 文档的 JSON 内容';
          return;
        }
        try {
          const parsedSpec = JSON.parse(apiDocument.value);
          loading.value = true;
          errorMessage.value = '';
          testCases.value = [];
          totalCount.value = 0;
          batchContext = null;

          apiGenerateTestCases(parsedSpec)
            .then(response => {
              const data = response.data;
              testCases.value = data.test_cases;
              totalCount.value = data.total;
              batchContext = data.batch_context;

              const remaining = data.total - data.generated_count;
              if (remaining <= 0) {
                loading.value = false;
                ElMessage.success('测试用例生成成功！');
                return;
              }

              ElMessageBox.confirm(
                `已生成 ${data.generated_count} / ${data.total} 条，还有 ${remaining} 条待生成。是否继续？`,
                '继续生成测试用例',
                { confirmButtonText: '继续生成', cancelButtonText: '结束', type: 'info' }
              )
                .then(() => fetchNextBatch())
                .catch(() => {
                  loading.value = false;
                  ElMessage.info(`已停止，共生成 ${testCases.value.length} 条测试用例`);
                });
            })
            .catch(error => {
              console.error('Error:', error);
              errorMessage.value = error.response?.data?.detail || '生成测试用例时出错！';
              testCases.value = [];
              loading.value = false;
              ElMessage.error(errorMessage.value);
            });
        } catch (e) {
          errorMessage.value = '无效的 JSON 格式，请检查您的输入。';
          testCases.value = [];
          ElMessage.error(errorMessage.value);
        }
      };

      return {
        apiDocument,
        testCases,
        errorMessage,
        loading,
        totalCount,
        selectedIndices,
        selectAll,
        isIndeterminate,
        handleSelectAll,
        toggleSelect,
        importSelectedCases,
        importDialogVisible,
        selectedModuleId,
        moduleOptions,
        loadModules,
        doImportCases,
        generateTestCases
      };
    }
  }
  </script>