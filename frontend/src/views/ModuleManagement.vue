<template>
  <div class="module-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>模块管理</span>
          <el-button type="primary" @click="handleAddRoot">新建根模块</el-button>
        </div>
      </template>

      <el-tree
        :data="moduleTree"
        node-key="id"
        default-expand-all
        :expand-on-click-node="false"
        :props="{ label: 'name' }"
      >
        <template #default="{ node, data }">
          <span class="custom-tree-node">
            <span>{{ node.label }}</span>
            <span class="actions">
              <el-button link type="primary" @click.stop="handleAppend(data)">
                添加子模块
              </el-button>
              <el-button link type="primary" @click.stop="handleEdit(data)">
                编辑
              </el-button>
              <el-button link type="danger" @click.stop="handleDelete(data)">
                删除
              </el-button>
            </span>
          </span>
        </template>
      </el-tree>
    </el-card>

    <!-- 模块编辑/创建对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="30%"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" autocomplete="off"></el-input>
        </el-form-item>
        <el-form-item label="父模块" v-if="form.parent_id">
           <!-- 显示父模块名称，不可修改，或者使用 TreeSelect 修改 -->
           <el-input :value="getParentName(form.parent_id)" disabled></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { 
  apiGetTestModules, 
  apiCreateTestModule, 
  apiUpdateTestModule, 
  apiDeleteTestModule 
} from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';

const moduleTree = ref([]);
const rawModules = ref([]);
const dialogVisible = ref(false);
const isEdit = ref(false);
const form = ref({
  id: null,
  name: '',
  parent_id: null
});

const dialogTitle = computed(() => isEdit.value ? '编辑模块' : '新建模块');

const getParentName = (parentId) => {
  const parent = rawModules.value.find(m => m.id === parentId);
  return parent ? parent.name : '根模块';
};

const transformToTree = (items) => {
  const result = [];
  const itemMap = {};
  
  // Deep copy to avoid mutating original items during multiple renders
  const itemsCopy = items.map(item => ({...item, children: []}));

  itemsCopy.forEach(item => {
    itemMap[item.id] = item;
  });

  itemsCopy.forEach(item => {
    if (item.parent_id && itemMap[item.parent_id]) {
      itemMap[item.parent_id].children.push(item);
    } else {
      result.push(item);
    }
  });

  return result;
};

const loadModules = async () => {
  try {
    const response = await apiGetTestModules();
    rawModules.value = response.data;
    moduleTree.value = transformToTree(response.data);
  } catch (error) {
    console.error('Failed to load modules:', error);
    ElMessage.error('加载模块失败');
  }
};

const handleAddRoot = () => {
  isEdit.value = false;
  form.value = { name: '', parent_id: null };
  dialogVisible.value = true;
};

const handleAppend = (data) => {
  isEdit.value = false;
  form.value = { name: '', parent_id: data.id };
  dialogVisible.value = true;
};

const handleEdit = (data) => {
  isEdit.value = true;
  form.value = { id: data.id, name: data.name, parent_id: data.parent_id };
  dialogVisible.value = true;
};

const handleDelete = (data) => {
  ElMessageBox.confirm(
    '确定删除该模块吗？如果有子模块或关联用例，可能会受到影响。',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        await apiDeleteTestModule(data.id);
        ElMessage.success('删除成功');
        loadModules();
      } catch (error) {
        console.error(error);
        ElMessage.error('删除失败');
      }
    })
    .catch(() => {});
};

const submitForm = async () => {
  if (!form.value.name) {
    ElMessage.warning('请输入模块名称');
    return;
  }

  try {
    if (isEdit.value) {
      await apiUpdateTestModule(form.value.id, { 
        name: form.value.name, 
        parent_id: form.value.parent_id 
      });
      ElMessage.success('更新成功');
    } else {
      await apiCreateTestModule({
        name: form.value.name,
        parent_id: form.value.parent_id
      });
      ElMessage.success('创建成功');
    }
    dialogVisible.value = false;
    loadModules();
  } catch (error) {
    console.error(error);
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败');
  }
};

onMounted(() => {
  loadModules();
});
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  padding-right: 8px;
}

.actions {
  display: flex;
  gap: 8px;
}
</style>