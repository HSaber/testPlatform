<template>
  <div class="test-suite-management">
    <el-container>
      <el-aside width="300px" class="suite-tree-container">
        <div class="tree-header">
          <h3>测试套件</h3>
          <el-button type="primary" size="small" @click="handleAddRootSuite">新建套件</el-button>
        </div>
        <el-tree
          :data="suiteTree"
          node-key="id"
          default-expand-all
          :props="defaultProps"
          @node-click="handleNodeClick"
          highlight-current
        >
          <template #default="{ node, data }">
            <span class="custom-tree-node">
              <span>{{ node.label }}</span>
              <span class="tree-actions">
                <el-button link type="primary" size="small" @click.stop="handleAddChildSuite(data)">+</el-button>
                <el-button link type="danger" size="small" @click.stop="handleDeleteSuite(data)">-</el-button>
              </span>
            </span>
          </template>
        </el-tree>
      </el-aside>
      
      <el-main>
        <div v-if="currentSuite" class="suite-detail">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>{{ currentSuite.name }}</span>
                <div>
                    <el-button type="warning" @click="handleDebugSuite">调试运行</el-button>
                    <el-button type="success" @click="handleRunSuite">执行套件</el-button>
                    <el-button type="primary" @click="handleSaveSuite">保存修改</el-button>
                    <el-button type="danger" @click="handleDeleteSuite(currentSuite)">删除套件</el-button>
                </div>
              </div>
            </template>
            
            <el-form :model="currentSuite" label-width="100px">
              <el-form-item label="套件名称">
                <el-input v-model="currentSuite.name" />
              </el-form-item>
              <el-form-item label="描述">
                <el-input type="textarea" v-model="currentSuite.description" />
              </el-form-item>
              
              <el-divider content-position="left">套件内容</el-divider>
              
              <div class="content-actions" style="margin-bottom: 15px;">
                <el-dropdown @command="handleAddItem">
                  <el-button type="primary">
                    添加内容 <el-icon class="el-icon--right"><arrow-down /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="test_case">添加测试用例</el-dropdown-item>
                      <el-dropdown-item command="test_module">添加模块</el-dropdown-item>
                      <!-- <el-dropdown-item command="test_suite">添加子套件</el-dropdown-item> 暂时先不加子套件引用，避免复杂 -->
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>

              <el-table :data="currentSuite.items" style="width: 100%" row-key="temp_id">
                <el-table-column label="类型" width="120">
                  <template #default="scope">
                    <el-tag v-if="scope.row.item_type === 'test_case'" type="success">测试用例</el-tag>
                    <el-tag v-else-if="scope.row.item_type === 'test_module'" type="warning">模块</el-tag>
                    <el-tag v-else type="info">{{ scope.row.item_type }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="名称">
                  <template #default="scope">
                    <span v-if="scope.row.item_type === 'test_case'">
                      {{ getTestCaseName(scope.row.test_case_id) }}
                    </span>
                    <span v-else-if="scope.row.item_type === 'test_module'">
                      {{ getModuleName(scope.row.module_id) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100">
                  <template #default="scope">
                    <el-button type="danger" link size="small" @click="handleRemoveItem(scope.$index)">移除</el-button>
                    <el-button link size="small" @click="handleMoveUp(scope.$index)" :disabled="scope.$index === 0">↑</el-button>
                    <el-button link size="small" @click="handleMoveDown(scope.$index)" :disabled="scope.$index === currentSuite.items.length - 1">↓</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-form>
          </el-card>
        </div>
        <div v-else class="empty-state">
          <el-empty description="请选择或创建一个测试套件" />
        </div>
      </el-main>
    </el-container>

    <!-- 新增/编辑套件弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="30%"
    >
      <el-form :model="suiteForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="suiteForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input type="textarea" v-model="suiteForm.description" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitSuiteForm">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 选择测试用例弹窗 -->
    <el-dialog v-model="caseSelectVisible" title="选择测试用例" width="50%">
       <el-table 
          :data="allTestCases" 
          @selection-change="handleCaseSelectionChange"
          height="400"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="module_id" label="所属模块">
             <template #default="scope">
                {{ getModuleName(scope.row.module_id) }}
             </template>
          </el-table-column>
       </el-table>
       <template #footer>
          <el-button @click="caseSelectVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmAddCases">确定</el-button>
       </template>
    </el-dialog>

    <!-- 选择模块弹窗 -->
    <el-dialog v-model="moduleSelectVisible" title="选择模块" width="40%">
        <el-tree
          :data="moduleTree"
          show-checkbox
          node-key="id"
          ref="moduleTreeRef"
          :props="{ label: 'name', children: 'children' }"
        />
        <template #footer>
          <el-button @click="moduleSelectVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmAddModules">确定</el-button>
        </template>
    </el-dialog>

    <!-- 执行结果弹窗 -->
    <el-dialog v-model="resultDialogVisible" title="执行结果" width="70%">
      <div class="result-summary" style="margin-bottom: 20px;">
        <el-descriptions :column="3" border>
           <el-descriptions-item label="执行状态">
              <el-tag :type="executionResult.status === 'success' ? 'success' : 'danger'">
                 {{ executionResult.status === 'success' ? '成功' : '失败' }}
              </el-tag>
           </el-descriptions-item>
           <el-descriptions-item label="提示信息">{{ executionResult.message }}</el-descriptions-item>
           <el-descriptions-item label="操作">
              <el-button type="primary" link v-if="executionResult.report_id" @click="viewReport(executionResult.report_id)">查看完整报告</el-button>
           </el-descriptions-item>
        </el-descriptions>
      </div>

      <div v-if="executionResult.details && executionResult.details.length > 0">
        <h4>执行详情</h4>
        <el-table :data="executionResult.details" height="400" style="width: 100%" border>
            <el-table-column prop="id" label="用例ID" width="80" />
            <el-table-column prop="name" label="用例名称" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">
                  {{ scope.row.status === 'success' ? '通过' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="duration" label="耗时(s)" width="100">
               <template #default="scope">
                 {{ scope.row.duration ? scope.row.duration.toFixed(2) : '0.00' }}
               </template>
            </el-table-column>
            <el-table-column label="响应/错误信息" show-overflow-tooltip>
                <template #default="scope">
                    {{ typeof scope.row.response === 'object' ? JSON.stringify(scope.row.response) : scope.row.response }}
                </template>
            </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="resultDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 调试选择用例弹窗 -->
    <el-dialog v-model="debugSelectVisible" title="选择调试用例" width="50%">
      <el-alert
        title="调试模式下，可以选择部分用例进行运行，结果不会保存到历史报告中。"
        type="info"
        show-icon
        style="margin-bottom: 15px;"
      />
       <el-table 
          :data="suiteTestCases" 
          @selection-change="handleDebugSelectionChange"
          height="400"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="test_case_id" label="ID" width="80" />
          <el-table-column label="名称">
            <template #default="scope">
                {{ getTestCaseName(scope.row.test_case_id) }}
            </template>
          </el-table-column>
          <el-table-column label="模块">
             <template #default="scope">
                {{ getModuleNameByCaseId(scope.row.test_case_id) }}
             </template>
          </el-table-column>
       </el-table>
       <template #footer>
          <el-button @click="debugSelectVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmDebugRun" :loading="debugLoading">开始调试</el-button>
       </template>
    </el-dialog>

    <!-- 调试结果弹窗 -->
    <el-drawer v-model="debugResultVisible" title="调试结果" size="80%">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="套件名称">{{ debugResult.suite_name }}</el-descriptions-item>
        <el-descriptions-item label="总耗时">{{ debugResult.total_duration ? debugResult.total_duration.toFixed(2) + 's' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="成功/总数">
          <el-tag type="success">{{ debugResult.results?.filter(r => ['pass', 'success', 'SUCCESS'].includes(r.status)).length }}</el-tag> /
          <el-tag type="info">{{ debugResult.results?.length }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <el-table :data="debugResult.results" style="width: 100%; margin-top: 20px;">
        <el-table-column prop="name" label="用例名称" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="['pass', 'success', 'SUCCESS'].includes(scope.row.status) ? 'success' : 'danger'">
              {{ ['pass', 'success', 'SUCCESS'].includes(scope.row.status) ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时(s)" width="100">
             <template #default="scope">{{ scope.row.duration?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column type="expand">
          <template #default="props">
             <div style="padding: 10px;">
                <!-- 兼容后端字段名差异 -->
                <p><strong>URL:</strong> {{ props.row.url || 'N/A' }}</p>
                <p><strong>Method:</strong> {{ props.row.method || 'N/A' }}</p>
                <p><strong>Response Code:</strong> {{ props.row.status_code || props.row.response_status_code }}</p>
                
                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                  <strong style="margin-right: 10px;">Response Body:</strong>
                  <el-tooltip content="复制Response Body" placement="top">
                    <el-button 
                      link 
                      type="primary" 
                      :icon="DocumentCopy" 
                      @click="copyToClipboard(typeof (props.row.response || props.row.response_body) === 'object' ? JSON.stringify(props.row.response || props.row.response_body, null, 2) : (props.row.response || props.row.response_body))"
                    />
                  </el-tooltip>
                </div>
                <pre style="max-height: 200px; overflow: auto; background: #f4f4f5; padding: 10px;">{{ 
                  typeof (props.row.response || props.row.response_body) === 'object' 
                    ? JSON.stringify(props.row.response || props.row.response_body, null, 2) 
                    : (props.row.response || props.row.response_body) 
                }}</pre>

                <template v-if="props.row.assertions">
                   <p><strong>Assertions:</strong></p>
                   <pre style="max-height: 150px; overflow: auto; background: #eef2f6; padding: 10px;">{{ JSON.stringify(props.row.assertions, null, 2) }}</pre>
                </template>
                
                <template v-if="props.row.logs">
                   <p><strong>Logs:</strong></p>
                   <pre style="max-height: 150px; overflow: auto; background: #282c34; color: #abb2bf; padding: 10px;">{{ props.row.logs }}</pre>
                </template>

                <p v-if="props.row.error"><strong>Error:</strong> {{ props.row.error }}</p>
             </div>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="debugResultVisible = false">关闭</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus';
import { ArrowDown, DocumentCopy } from '@element-plus/icons-vue';
import {
  apiGetTestSuites,
  apiGetTestSuiteDetail,
  apiCreateTestSuite,
  apiUpdateTestSuite,
  apiDeleteTestSuite,
  apiGetTestModules,
  apiGetTestCases,
  apiExecuteTestSuite,
  apiGetTestReports,
  apiDebugTestSuite // new import
} from '../api';

const router = useRouter();
const suiteTree = ref([]);
const moduleTree = ref([]);
const allTestCases = ref([]);
const moduleMap = ref({});
const caseMap = ref({});

const currentSuite = ref(null);
const dialogVisible = ref(false);
const dialogTitle = ref('新建套件');
const suiteForm = ref({ name: '', description: '', parent_id: null });

const caseSelectVisible = ref(false);
const moduleSelectVisible = ref(false);
const selectedCases = ref([]);
const moduleTreeRef = ref(null);

const resultDialogVisible = ref(false);
const executionResult = ref({});

// 调试相关状态
const debugSelectVisible = ref(false);
const debugResultVisible = ref(false);
const debugLoading = ref(false);
const suiteTestCases = ref([]);
const selectedDebugCases = ref([]);
const debugResult = ref({});

const defaultProps = {
  children: 'children',
  label: 'name',
};

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    ElMessage.success('复制成功');
  } catch (err) {
    ElMessage.error('复制失败');
    console.error('Failed to copy: ', err);
  }
};

const loadData = async () => {
  await Promise.all([loadModules(), loadTestCases()]);
  await loadSuites();
};

const loadSuites = async () => {
  try {
    const res = await apiGetTestSuites();
    suiteTree.value = transformToTree(res.data);
  } catch (error) {
    ElMessage.error('获取测试套件失败');
  }
};

const loadModules = async () => {
  try {
    const res = await apiGetTestModules();
    moduleTree.value = transformToTree(res.data);
    // 构建扁平 Map 方便查找名称
    flattenModules(res.data);
  } catch (error) {
    ElMessage.error('获取模块列表失败');
  }
};

const flattenModules = (modules) => {
    modules.forEach(m => {
        moduleMap.value[m.id] = m.name;
        // 后端返回的结构可能已经是树或者是列表，这里假设 apiGetTestModules 返回的是列表
    });
};

const loadTestCases = async () => {
  try {
    const res = await apiGetTestCases();
    allTestCases.value = res.data;
    res.data.forEach(tc => {
        caseMap.value[tc.id] = tc.name;
    });
  } catch (error) {
    ElMessage.error('获取测试用例失败');
  }
};

const transformToTree = (data) => {
  // 深拷贝数据，避免修改原数据，同时断开引用
  const list = JSON.parse(JSON.stringify(data));
  const map = {};
  
  // 先建立索引并重置 children，确保干净的开始
  list.forEach(item => {
    item.children = [];
    map[item.id] = item;
  });
  
  const root = [];
  list.forEach((item) => {
    if (item.parent_id && map[item.parent_id]) {
      // 如果有父节点且父节点存在，加入到父节点的 children 中
      map[item.parent_id].children.push(item);
    } else {
      // 否则作为根节点
      root.push(item);
    }
  });
  
  return root;
};

const getTestCaseName = (id) => caseMap.value[id] || `Unknown Case ${id}`;
const getModuleName = (id) => moduleMap.value[id] || `Unknown Module ${id}`;

const handleNodeClick = async (data) => {
  try {
    const res = await apiGetTestSuiteDetail(data.id);
    // 为 items 添加临时 ID 方便前端 key 绑定（如果后端没返回 ID）
    const items = res.data.items.map((item, index) => ({
        ...item,
        temp_id: item.id || Date.now() + index
    }));
    
    currentSuite.value = {
      ...res.data,
      items: items.sort((a, b) => a.sort_order - b.sort_order)
    };
  } catch (error) {
    ElMessage.error('获取套件详情失败');
  }
};

const handleAddRootSuite = () => {
    suiteForm.value = { name: '', description: '', parent_id: null };
    dialogTitle.value = '新建根套件';
    dialogVisible.value = true;
};

const handleAddChildSuite = (data) => {
    suiteForm.value = { name: '', description: '', parent_id: data.id };
    dialogTitle.value = `在 [${data.name}] 下新建套件`;
    dialogVisible.value = true;
};

const handleDeleteSuite = (data) => {
    ElMessageBox.confirm(
        `确定删除套件 "${data.name}" 吗?`,
        '警告',
        {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
        }
    ).then(async () => {
        try {
            await apiDeleteTestSuite(data.id);
            ElMessage.success('删除成功');
            loadSuites();
            if (currentSuite.value && currentSuite.value.id === data.id) {
                currentSuite.value = null;
            }
        } catch (error) {
            ElMessage.error('删除失败');
        }
    });
};

const submitSuiteForm = async () => {
    try {
        if (suiteForm.value.id) {
            await apiUpdateTestSuite(suiteForm.value.id, suiteForm.value);
        } else {
            await apiCreateTestSuite(suiteForm.value);
        }
        ElMessage.success('操作成功');
        dialogVisible.value = false;
        loadSuites();
    } catch (error) {
        ElMessage.error('操作失败');
    }
};

const handleAddItem = (command) => {
    if (command === 'test_case') {
        selectedCases.value = [];
        caseSelectVisible.value = true;
    } else if (command === 'test_module') {
        moduleSelectVisible.value = true;
    }
};

const handleCaseSelectionChange = (val) => {
    selectedCases.value = val;
};

const confirmAddCases = () => {
    const newItems = selectedCases.value.map(c => ({
        item_type: 'test_case',
        test_case_id: c.id,
        module_id: null,
        child_suite_id: null,
        temp_id: Date.now() + Math.random(),
        sort_order: 0 // 暂时设为0，保存时会重算
    }));
    // 将新项添加到当前套件的内容列表中
    if (!currentSuite.value.items) currentSuite.value.items = [];
    currentSuite.value.items.push(...newItems);
    caseSelectVisible.value = false;
};

const getModuleNameByCaseId = (caseId) => {
    const testCase = allTestCases.value.find(tc => tc.id === caseId);
    if (!testCase || !testCase.module_id) return '-';
    return getModuleName(testCase.module_id);
};

const handleDebugSuite = () => {
    if (!currentSuite.value || !currentSuite.value.items) return;
    
    // 筛选出直接关联的测试用例
    suiteTestCases.value = currentSuite.value.items.filter(item => item.item_type === 'test_case');
    
    if (suiteTestCases.value.length === 0) {
        ElMessage.warning('当前套件没有直接关联的测试用例，无法进行调试');
        return;
    }

    debugSelectVisible.value = true;
};

const handleDebugSelectionChange = (val) => {
    selectedDebugCases.value = val;
};

const confirmDebugRun = async () => {
    if (selectedDebugCases.value.length === 0) {
        ElMessage.warning('请至少选择一个用例');
        return;
    }

    debugLoading.value = true;
    try {
        const caseIds = selectedDebugCases.value.map(item => item.test_case_id);
        const payload = { include_case_ids: caseIds };
        
        const res = await apiDebugTestSuite(currentSuite.value.id, payload);
        debugResult.value = res.data;
        debugSelectVisible.value = false;
        debugResultVisible.value = true;
    } catch (error) {
        console.error(error);
        ElMessage.error('调试运行失败');
    } finally {
        debugLoading.value = false;
    }
};

const handleRemoveItem = (index) => {
    currentSuite.value.items.splice(index, 1);
};

const handleMoveUp = (index) => {
    if (index > 0) {
        const temp = currentSuite.value.items[index];
        currentSuite.value.items[index] = currentSuite.value.items[index - 1];
        currentSuite.value.items[index - 1] = temp;
    }
};

const handleMoveDown = (index) => {
    if (index < currentSuite.value.items.length - 1) {
        const temp = currentSuite.value.items[index];
        currentSuite.value.items[index] = currentSuite.value.items[index + 1];
        currentSuite.value.items[index + 1] = temp;
    }
};

const handleSaveSuite = async () => {
    if (!currentSuite.value) return;
    try {
        // 重新计算 sort_order，并清洗数据，只保留后端需要的字段
        const itemsToSave = currentSuite.value.items.map((item, index) => ({
            item_type: item.item_type,
            test_case_id: item.test_case_id || null,
            module_id: item.module_id || null,
            child_suite_id: item.child_suite_id || null,
            sort_order: index
        }));
        
        const payload = {
            name: currentSuite.value.name,
            description: currentSuite.value.description,
            parent_id: currentSuite.value.parent_id,
            items: itemsToSave
        };

        await apiUpdateTestSuite(currentSuite.value.id, payload);
        ElMessage.success('保存成功');
        loadSuites(); // 刷新树
    } catch (error) {
        ElMessage.error('保存失败');
        console.error(error);
        throw error; // 抛出错误以便调用者处理
    }
};

const handleRunSuite = async () => {
    if (!currentSuite.value || !currentSuite.value.id) return;
    
    // 1. 先保存
    try {
        await handleSaveSuite();
    } catch (e) {
        return; // 保存失败则不继续执行
    }

    // 2. 执行测试
    const loading = ElLoading.service({
        lock: true,
        text: '正在执行测试套件...',
        background: 'rgba(0, 0, 0, 0.7)',
    });
    
    try {
        const res = await apiExecuteTestSuite(currentSuite.value.id);
        const data = res.data;
        
        executionResult.value = {
            status: 'success',
            message: '测试套件执行成功',
            details: data.results,
            final_variables: data.final_variables,
            error: null,
            report_id: data.report_id
        };
        
        resultDialogVisible.value = true;
        ElMessage.success('执行完成');
    } catch (error) {
        console.error(error);
        ElMessage.error('执行请求失败');
        executionResult.value = {
            status: 'error',
            message: error.message || '网络或服务器错误',
            error: error.message || '网络或服务器错误'
        };
        resultDialogVisible.value = true;
    } finally {
        loading.close();
    }
};

const viewReport = (reportId) => {
    resultDialogVisible.value = false;
    router.push(`/reports/${reportId}`);
};

onMounted(() => {
    loadData();
});
</script>

<style scoped>
.test-suite-management {
  height: 100%;
  display: flex;
}
.el-container {
  height: calc(100vh - 80px);
}
.suite-tree-container {
  border-right: 1px solid #dcdfe6;
  padding: 10px;
  background-color: #f5f7fa;
}
.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.tree-header h3 {
  font-size: 18px;
  margin: 0;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  padding-right: 8px;
}
.suite-detail {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}
</style>