<template>
  <el-card>
    <div style="margin-bottom:16px">
      <el-input v-model="keyword" placeholder="搜索用户名" style="width:200px" clearable @clear="loadData" @keyup.enter="loadData" />
    </div>
    <el-table :data="list" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="login_ip" label="登录IP" />
      <el-table-column prop="login_status" label="状态">
        <template #default="{ row }">
          <el-tag :type="row.login_status === 1 ? 'success' : 'danger'">{{ row.login_status === 1 ? '成功' : '失败' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="login_time" label="登录时间" />
    </el-table>
    <el-pagination style="margin-top:16px;justify-content:flex-end" v-model:current-page="page" v-model:page-size="pageSize" :total="total" :page-sizes="[10,20,50]" layout="total,sizes,prev,pager,next" @change="loadData" />
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getLogs } from '../api/logs'

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const loading = ref(false)

onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    const res = await getLogs({ page: page.value, page_size: pageSize.value, keyword: keyword.value })
    list.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}
</script>
