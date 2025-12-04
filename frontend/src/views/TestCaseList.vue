<template>
  <div class="test-case-list">
    <div class="toolbar">
      <h1>用例管理</h1>
      <el-button type="primary" @click="goToCreatePage">创建用例</el-button>
    </div>

    <el-table :data="testCases" stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80"></el-table-column>
      <el-table-column prop="name" label="用例名称"></el-table-column>
      <el-table-column prop="method" label="请求方法" width="120"></el-table-column>
      <el-table-column prop="url" label="URL"></el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { apiGetTestCases } from '@/api'; // 确保导入的是 apiGetTestCases
import { ElMessage } from 'element-plus';

const testCases = ref([]);
const loading = ref(true);
const router = useRouter();

const fetchTestCases = async () => {
  try {
    loading.value = true;
    const response = await apiGetTestCases(); // 确保调用的是 apiGetTestCases
    testCases.value = response.data;
  } catch (error) {
    console.error("获取用例列表失败:", error);
    ElMessage.error('获取用例列表失败');
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchTestCases();
});

const goToCreatePage = () => {
  router.push('/create');
};

const handleEdit = (row) => {
  // 我们将在下一步实现
  console.log('编辑', row);
  ElMessage.info('编辑功能待实现');
};

const handleDelete = (row) => {
  // 我们将在下一步实现
  console.log('删除', row);
  ElMessage.warning('删除功能待实现');
};
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>