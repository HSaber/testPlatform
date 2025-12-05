<script setup>
import { RouterView, useRoute } from 'vue-router'
import { Folder, Collection, Document } from '@element-plus/icons-vue'
</script>

<template>
  <el-container style="height: 100vh;">
    <el-header>
      <div class="header-content">
        <h2 style="margin: 0;">API Test Platform</h2>
        <el-menu mode="horizontal" :router="true" :default-active="$route.path" style="flex-grow: 1; justify-content: flex-end;">
          <el-menu-item index="/">用例管理</el-menu-item>
          <el-menu-item index="/modules">
            <el-icon><Folder /></el-icon>
            <span>模块管理</span>
          </el-menu-item>
          <el-menu-item index="/suites">
            <el-icon><Collection /></el-icon>
            <span>测试套件</span>
          </el-menu-item>
          <el-menu-item index="/reports">
            <el-icon><Document /></el-icon>
            <span>测试报告</span>
          </el-menu-item>
        </el-menu>
      </div>
    </el-header>
    <el-main>
      <router-view></router-view>
    </el-main>
  </el-container>
</template>

<script>
export default {
  name: 'App',
};
</script>

<style>
body {
  margin: 0;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

.el-header {
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
</style>