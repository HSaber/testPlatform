<template>
  <div class="test-report-list">
    <div class="header">
      <h2>测试报告列表</h2>
    </div>

    <el-table :data="reports" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="suite_id" label="测试套件 ID" width="120" />
      <el-table-column prop="suite_name" label="测试套件名称" min-width="150" />
      <el-table-column prop="start_time" label="开始时间" width="180">
        <template #default="scope">
          {{ formatDate(scope.row.start_time) }}
        </template>
      </el-table-column>
      <el-table-column prop="duration" label="耗时 (秒)" width="100">
        <template #default="scope">
          {{ scope.row.duration ? scope.row.duration.toFixed(2) : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="统计信息">
        <template #default="scope">
          <el-space>
            <el-tag type="info" size="small">总: {{ scope.row.total_cases }}</el-tag>
            <el-tag type="success" size="small">通: {{ scope.row.pass_count }}</el-tag>
            <el-tag type="danger" size="small">失: {{ scope.row.fail_count }}</el-tag>
            <el-tag type="warning" size="small">错: {{ scope.row.error_count }}</el-tag>
          </el-space>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="scope">
          <el-button type="primary" size="small" @click="viewDetail(scope.row.id)">
            查看详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiGetTestReports } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const reports = ref([])
const loading = ref(false)

const fetchReports = async () => {
  loading.value = true
  try {
    const response = await apiGetTestReports()
    reports.value = response.data
  } catch (error) {
    ElMessage.error('获取测试报告失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const viewDetail = (id) => {
  router.push({ name: 'TestReportDetail', params: { id } })
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString()
}

const getStatusType = (status) => {
  const map = {
    'completed': 'success',
    'passed': 'success',
    'success': 'success',
    'running': 'primary',
    'failed': 'danger',
    'fail': 'danger',
    'error': 'warning'
  }
  return map[status] || 'info'
}

onMounted(() => {
  fetchReports()
})
</script>

<style scoped>
.test-report-list {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  font-size: 20px;
  margin: 0;
}
</style>