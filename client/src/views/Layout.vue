<template>
  <el-container style="height:100vh">
    <el-header style="display:flex;align-items:center;justify-content:space-between;background:#001529;color:#fff">
      <span style="font-size:18px">数据管理平台</span>
      <div style="display:flex;align-items:center;gap:12px">
        <span>{{ user?.username }}</span>
        <el-dropdown @command="handleCommand">
          <el-button type="primary" text style="color:#fff">操作<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人中心</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>
    <el-container>
      <el-aside width="200px" style="background:#001529">
        <el-menu :default-active="route.path" router background-color="#001529" text-color="#fff" active-text-color="#409eff">
          <el-menu-item index="/home">
            <el-icon><HomeFilled /></el-icon><span>首页</span>
          </el-menu-item>
          <el-menu-item index="/dashboard-config">
            <el-icon><DataBoard /></el-icon><span>仪表盘配置</span>
          </el-menu-item>
          <el-menu-item index="/templates">
            <el-icon><Document /></el-icon><span>模板管理</span>
          </el-menu-item>
          <el-menu-item index="/forms">
            <el-icon><EditPen /></el-icon><span>表单数据</span>
          </el-menu-item>
          <el-menu-item index="/form-browser">
            <el-icon><Search /></el-icon><span>数据查询</span>
          </el-menu-item>
          <el-menu-item index="/form-sheet">
            <el-icon><Grid /></el-icon><span>表格编辑</span>
          </el-menu-item>
          <template v-if="user?.role === 'admin'">
            <el-menu-item index="/system/users">
              <el-icon><UserFilled /></el-icon><span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="/system/logs">
              <el-icon><List /></el-icon><span>系统日志</span>
            </el-menu-item>
          </template>
          <el-menu-item index="/system/profile">
            <el-icon><Setting /></el-icon><span>个人中心</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main style="background:#f0f2f5;padding:20px">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { HomeFilled, Document, EditPen, Search, Grid, UserFilled, List, Setting, ArrowDown, DataBoard } from '@element-plus/icons-vue'
import { logout } from '../api/auth'
import { getUserInfo, removeToken, removeUserInfo } from '../utils/storage'

const route = useRoute()
const router = useRouter()
const user = computed(() => getUserInfo())

async function handleCommand(cmd) {
  if (cmd === 'profile') {
    router.push('/system/profile')
  } else if (cmd === 'logout') {
    try { await logout() } catch {}
    removeToken()
    removeUserInfo()
    router.push('/login')
  }
}
</script>
