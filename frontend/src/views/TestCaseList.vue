<template>
  <div class="test-case-list">
    <div class="toolbar">
      <h1>用例管理</h1>
      <div>
        <el-button type="primary" @click="goToCreatePage">创建用例</el-button>
        <el-button type="danger" @click="handleBatchDelete" :disabled="selectedTestCases.length === 0">批量删除</el-button>
      </div>
    </div>

    <el-table 
      :data="testCases" 
      stripe 
      v-loading="loading" 
      style="width: 100%" 
      row-key="id" 
      ref="tableRef" 
      @cell-click="handleCellClick"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="80"></el-table-column>
      <el-table-column prop="name" label="用例名称" class-name="name-column-clickable"></el-table-column>
      <el-table-column prop="method" label="请求方法" width="120"></el-table-column>
      <el-table-column prop="url" label="URL"></el-table-column>
      <el-table-column label="操作" width="250">
        <template #default="scope">
          <el-button size="small" @click.stop="handleEdit(scope.row)">编辑</el-button>
          <el-button size="small" type="success" @click.stop="handleCopy(scope.row)">复制</el-button>
          <el-button size="small" type="danger" @click.stop="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <TestCaseDetail 
      :visible="detailDrawerVisible" 
      :test-case="selectedTestCase"
      @close="closeDetailDrawer"
      @save="handleSaveTestCase"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import Sortable from 'sortablejs';
import { apiGetTestCases, apiReorderTestCases, apiDeleteTestCase, apiUpdateTestCase, apiBatchDeleteTestCases, apiCopyTestCase } from '@/api';
import TestCaseDetail from './TestCaseDetail.vue';

const testCases = ref([]);
const loading = ref(true);
const router = useRouter();
const tableRef = ref(null);
const detailDrawerVisible = ref(false);
const selectedTestCase = ref(null);
const selectedTestCases = ref([]);

const handleSelectionChange = (selection) => {
  selectedTestCases.value = selection;
};

const handleBatchDelete = () => {
  if (selectedTestCases.value.length === 0) return;

  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedTestCases.value.length} 个用例吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      const ids = selectedTestCases.value.map(item => item.id);
      await apiBatchDeleteTestCases(ids);
      ElMessage.success('批量删除成功');
      // 重新获取列表
      await fetchTestCases();
      selectedTestCases.value = []; // 清空选中状态
    } catch (error) {
      console.error("批量删除失败:", error);
      ElMessage.error('批量删除失败');
    }
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
};

const handleCellClick = (row, column) => {
  if (column.className === 'name-column-clickable') {
    showDetailDrawer(row);
  }
}

const showDetailDrawer = (row) => {
  selectedTestCase.value = row;
  detailDrawerVisible.value = true;
};

const closeDetailDrawer = () => {
  detailDrawerVisible.value = false;
  // 动画结束后再清空数据，体验更好
  setTimeout(() => {
    selectedTestCase.value = null;
  }, 300); 
};

const fetchTestCases = async () => {
  try {
    loading.value = true;
    const response = await apiGetTestCases();
    testCases.value = response.data;
    
    // 数据加载完成后，在下一次 DOM 更新时初始化拖拽
    await nextTick();
    initSortable();

  } catch (error) {
    console.error("获取用例列表失败:", error);
    ElMessage.error('获取用例列表失败');
  } finally {
    loading.value = false;
  }
};

const initSortable = () => {
  if (!tableRef.value) return;
  const tbody = tableRef.value.$el.querySelector('.el-table__body-wrapper tbody');
  if (!tbody) return;

  Sortable.create(tbody, {
    animation: 150,
    onEnd: async ({ newIndex, oldIndex }) => {
      if (oldIndex === newIndex) {
        return;
      }
      // 移动数组元素以匹配新的顺序
      const currRow = testCases.value.splice(oldIndex, 1)[0];
      testCases.value.splice(newIndex, 0, currRow);

      // 等待 DOM 更新后调用后端 API
      await nextTick();
      handleReorder();
    },
  });
};

onMounted(() => {
  fetchTestCases();
});

const goToCreatePage = () => {
  router.push('/create');
};

const handleSaveTestCase = async (testCaseData) => {
  try {
    await apiUpdateTestCase(testCaseData.id, testCaseData);
    ElMessage.success('用例更新成功');
    closeDetailDrawer();
    await fetchTestCases();
  } catch (error) {
    console.error('Failed to update test case:', error);
    ElMessage.error('用例更新失败');
  }
};

const handleEdit = (row) => {
  showDetailDrawer(row);
};

const handleCopy = async (row) => {
  try {
    loading.value = true;
    await apiCopyTestCase(row.id);
    ElMessage.success('复制成功');
    await fetchTestCases();
  } catch (error) {
    console.error("复制失败:", error);
    ElMessage.error('复制失败');
  } finally {
    loading.value = false;
  }
};

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除用例 "${row.name}" 吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await apiDeleteTestCase(row.id);
      ElMessage.success('删除成功');
      // 从列表中移除被删除的项，避免重新请求数据
      const index = testCases.value.findIndex(item => item.id === row.id);
      if (index !== -1) {
        testCases.value.splice(index, 1);
      }
    } catch (error) {
      console.error("删除失败:", error);
      ElMessage.error('删除失败');
    }
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
};

const handleReorder = async () => {
  const testCaseIds = testCases.value.map(tc => tc.id);
  try {
    await apiReorderTestCases(testCaseIds);
    ElMessage.success('排序更新成功');
  } catch (error) {
    console.error("更新排序失败:", error);
    ElMessage.error('更新排序失败');
    // 如果失败，重新获取数据以恢复原始顺序
    fetchTestCases();
  }
};
</script>

<style scoped>
/* 修改样式：只为用例名称列的 *内容* 添加手型光标和样式 */
:deep(tbody .name-column-clickable .cell) {
  cursor: pointer;
  color: #409EFF;
}

:deep(tbody .name-column-clickable .cell:hover) {
  text-decoration: underline;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

/* 添加一个拖拽时的占位符样式 */
.sortable-ghost {
  opacity: 0.8;
  background-color: #c8ebfb;
}
</style>