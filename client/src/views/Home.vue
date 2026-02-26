<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <span style="font-size:16px;font-weight:600">仪表盘</span>
      <div style="display:flex;gap:8px;align-items:center">
        <el-select v-model="selectedTemplates" multiple collapse-tags collapse-tags-tooltip
          placeholder="筛选数据来源" style="width:280px" @change="loadData">
          <el-option v-for="t in availableTemplates" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button @click="$router.push('/dashboard-config')">配置仪表盘</el-button>
      </div>
    </div>

    <el-empty v-if="!filteredWidgets.length" description="暂无仪表盘，点击右上角「配置仪表盘」添加图表" />

    <div v-else style="display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:16px">
      <el-card v-for="w in filteredWidgets" :key="w.id" shadow="hover" v-loading="loading">
        <div style="font-weight:500;margin-bottom:8px;display:flex;justify-content:space-between">
          <span>{{ w.title }}</span>
          <el-tag size="small" type="info">{{ w.templateName }}</el-tag>
        </div>
        <div v-if="w.chartType === 'stat'" style="text-align:center;padding:24px 0">
          <div style="font-size:48px;font-weight:700;color:#409eff">{{ statValue(w) }}</div>
          <div style="color:#999;margin-top:4px">{{ w.fieldName === '__count__' ? '记录总数' : w.fieldLabel }}</div>
        </div>
        <DashboardChart v-else :type="w.chartType" :data="chartData(w)" style="height:260px" />
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getTemplates } from '../api/templates'
import { getForms } from '../api/forms'
import DashboardChart from '../components/DashboardChart.vue'

const STORAGE_KEY = 'dashboard_config'

const allWidgets = ref([])
const selectedTemplates = ref([])
const formDataMap = ref({}) // templateId -> rows[]
const loading = ref(false)

// 所有配置中涉及的模板（去重）
const availableTemplates = computed(() => {
  const ids = [...new Set(allWidgets.value.map(w => w.templateId))]
  return ids.map(id => ({ id, name: allWidgets.value.find(w => w.templateId === id)?.templateName || id }))
})

// 按选中模板过滤图表，未选则显示全部
const filteredWidgets = computed(() => {
  if (!selectedTemplates.value.length) return allWidgets.value
  return allWidgets.value.filter(w => selectedTemplates.value.includes(w.templateId))
})

onMounted(async () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  allWidgets.value = saved ? JSON.parse(saved) : []
  await loadData()
})

async function loadData() {
  const templateIds = selectedTemplates.value.length
    ? selectedTemplates.value
    : [...new Set(allWidgets.value.map(w => w.templateId))]
  if (!templateIds.length) return

  loading.value = true
  try {
    await Promise.all(templateIds.map(async (tid) => {
      const res = await getForms({ page: 1, page_size: 5000, template_id: tid })
      formDataMap.value[tid] = res.data.list.map(r => r.data)
    }))
  } finally {
    loading.value = false
  }
}

function chartData(w) {
  const rows = formDataMap.value[w.templateId] || []
  if (w.fieldName === '__count__') return [{ name: '总数', value: rows.length }]

  const counts = {}
  for (const row of rows) {
    const val = row[w.fieldName]
    const keys = Array.isArray(val) ? val : [val == null || val === '' ? '(空)' : String(val)]
    for (const k of keys) counts[k] = (counts[k] || 0) + 1
  }
  return Object.entries(counts)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 20)
}

function statValue(w) {
  const rows = formDataMap.value[w.templateId] || []
  if (w.fieldName === '__count__') return rows.length
  const counts = {}
  for (const row of rows) {
    const val = row[w.fieldName]
    const keys = Array.isArray(val) ? val : [String(val ?? '')]
    for (const k of keys) counts[k] = (counts[k] || 0) + 1
  }
  return Object.keys(counts).length
}
</script>
