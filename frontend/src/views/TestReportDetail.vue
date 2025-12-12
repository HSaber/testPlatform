<template>
  <div class="test-report-detail">
    <div class="header">
      <el-page-header @back="goBack" title="返回列表">
        <template #content>
          <span class="detail-title"> 测试报告详情 #{{ reportId }} </span>
        </template>
      </el-page-header>
    </div>

    <el-card v-if="report" class="info-card">
      <el-descriptions title="基本信息" :column="4" border>
        <el-descriptions-item label="套件名称">{{ report.suite_name }}</el-descriptions-item>
        <el-descriptions-item label="测试套件 ID">{{ report.suite_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(report.status)">{{ formatStatus(report.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ formatDate(report.start_time) }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ report.duration ? report.duration.toFixed(2) + 's' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="统计">
             <el-space>
                <el-tag type="info">总: {{ report.total_cases }}</el-tag>
                <el-tag type="success">通: {{ report.pass_count }}</el-tag>
                <el-tag type="danger">失: {{ report.fail_count }}</el-tag>
                <el-tag type="warning">错: {{ report.error_count }}</el-tag>
             </el-space>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <div class="records-section" v-if="report">
      <h3>执行记录</h3>
      <el-table :data="report.records" style="width: 100%" row-key="id" border>
        <el-table-column type="expand">
            <template #default="props">
                <div class="record-detail">
                    <el-tabs type="border-card">
                        <el-tab-pane label="请求信息">
                            <el-descriptions :column="1" border size="small">
                                <el-descriptions-item label="URL">{{ props.row.url }}</el-descriptions-item>
                                <el-descriptions-item label="Method">{{ props.row.method }}</el-descriptions-item>
                                <el-descriptions-item label="Headers">
                                    <pre>{{ formatJson(props.row.request_headers) }}</pre>
                                </el-descriptions-item>
                                <el-descriptions-item label="Body">
                                    <pre>{{ formatJson(props.row.request_body) }}</pre>
                                </el-descriptions-item>
                            </el-descriptions>
                        </el-tab-pane>
                        <el-tab-pane label="响应信息">
                            <el-descriptions :column="1" border size="small">
                                <el-descriptions-item label="Status Code">{{ props.row.status_code }}</el-descriptions-item>
                                <el-descriptions-item label="Headers">
                                    <pre>{{ formatJson(props.row.response_headers) }}</pre>
                                </el-descriptions-item>
                                <el-descriptions-item label="Body">
                                    <pre>{{ formatJson(props.row.response_body) }}</pre>
                                </el-descriptions-item>
                            </el-descriptions>
                        </el-tab-pane>
                        <el-tab-pane label="断言结果">
                            <el-table :data="props.row.assertions.assertion_results" border size="small">
                                <el-table-column prop="check" label="检查点" />
                                <el-table-column prop="expect" label="预期值">
                                    <template #default="scope">
                                        <pre style="margin:0; font-family:inherit; white-space: pre-wrap;">{{ scope.row.expect }}</pre>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="actual" label="实际值">
                                    <template #default="scope">
                                        <pre style="margin:0; font-family:inherit; white-space: pre-wrap;">{{ scope.row.actual }}</pre>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="result" label="状态" width="80">
                                    <template #default="scope">
                                        <el-tag :type="scope.row.result === 'success' ? 'success' : 'danger'">
                                            {{ scope.row.result === 'success' ? '通过' : '失败' }}
                                        </el-tag>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="message" label="消息" />
                            </el-table>
                        </el-tab-pane>
                        <el-tab-pane label="提取结果" v-if="props.row.extract_results && Object.keys(props.row.extract_results).length > 0">
                            <el-table :data="Object.entries(props.row.extract_results).map(([name, value]) => ({ name, value }))" border size="small">
                                <el-table-column prop="name" label="变量名" />
                                <el-table-column prop="value" label="提取值" />
                            </el-table>
                        </el-tab-pane>
                        <el-tab-pane label="错误信息" v-if="props.row.error_message">
                            <pre class="error-text">{{ props.row.error_message }}</pre>
                        </el-tab-pane>
                    </el-tabs>
                </div>
            </template>
        </el-table-column>
        <el-table-column prop="test_case_id" label="用例 ID" width="100" />
        <el-table-column prop="case_name" label="用例名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
             <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时 (秒)" width="120">
             <template #default="scope">
                {{ scope.row.duration ? scope.row.duration.toFixed(4) : '-' }}
             </template>
        </el-table-column>
        <el-table-column label="错误信息" show-overflow-tooltip>
             <template #default="scope">
                {{ scope.row.error_message }}
             </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiGetTestReportDetail } from '../api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const reportId = route.params.id
const report = ref(null)
const loading = ref(false)

const goBack = () => {
  router.back()
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

const formatStatus = (status) => {
    const map = {
        'success': '成功',
        'failed': '失败',
        'error': '错误',
        'running': '运行中'
    };
    return map[status] || status;
};

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

const formatJson = (data) => {
    if (!data) return ''
    try {
        if (typeof data === 'string') {
            return JSON.stringify(JSON.parse(data), null, 2)
        }
        return JSON.stringify(data, null, 2)
    } catch (e) {
        return data
    }
}

const loadReport = async () => {
  try {
    loading.value = true
    const res = await apiGetTestReportDetail(reportId)
    report.value = res.data
  } catch (error) {
    console.error('获取报告详情失败', error)
    ElMessage.error('获取报告详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadReport()
})
</script>

<style scoped>
.test-report-detail {
  padding: 20px;
}

.detail-title {
  font-size: 18px;
  font-weight: 600;
}

.header {
  margin-bottom: 20px;
}

.info-card {
  margin-bottom: 20px;
}

.records-section {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}

.record-detail {
    padding: 20px;
    background-color: #f5f7fa;
}

pre {
    white-space: pre-wrap;
    word-wrap: break-word;
    background-color: #f5f5f5;
    padding: 10px;
    border-radius: 4px;
    font-family: monospace;
}

.error-text {
    color: #f56c6c;
}
</style>