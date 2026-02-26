<template>
  <div>
    <!-- 顶栏 -->
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <span style="font-size:18px;font-weight:600;color:#1a1a2e">仪表盘</span>
      <div style="display:flex;gap:8px;align-items:center">
        <el-select v-model="selectedTemplates" multiple collapse-tags collapse-tags-tooltip
          placeholder="筛选数据来源" style="width:280px" @change="loadData">
          <el-option v-for="t in availableTemplates" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button @click="$router.push('/dashboard-config')">
          <el-icon><Setting /></el-icon> 配置仪表盘
        </el-button>
        <el-button :icon="Refresh" circle @click="loadData" :loading="loading" />
      </div>
    </div>

    <el-empty v-if="!filteredWidgets.length" description="暂无仪表盘，点击右上角「配置仪表盘」添加图表">
      <el-button type="primary" @click="$router.push('/dashboard-config')">立即配置</el-button>
    </el-empty>

    <div v-else style="display:grid;grid-template-columns:repeat(auto-fill,minmax(400px,1fr));gap:18px">
      <el-card
        v-for="w in filteredWidgets" :key="w.id"
        shadow="hover"
        v-loading="loading"
        style="border-radius:12px;overflow:hidden"
        body-style="padding:0"
      >
        <!-- 卡片头 -->
        <div :style="`background:${headerBg(w.chartType)};padding:14px 18px;display:flex;justify-content:space-between;align-items:center`">
          <div style="display:flex;align-items:center;gap:8px">
            <el-icon :style="`color:${headerColor(w.chartType)};font-size:18px`">
              <component :is="chartIcon(w.chartType)" />
            </el-icon>
            <span style="font-weight:600;font-size:14px;color:#1a1a2e">{{ w.title }}</span>
          </div>
          <el-tag size="small" :color="headerBg(w.chartType)" style="border:none;color:#666">{{ w.templateName }}</el-tag>
        </div>

        <!-- stat 卡片 -->
        <div v-if="w.chartType === 'stat'" style="padding:28px 18px;text-align:center">
          <div style="font-size:56px;font-weight:700;line-height:1;background:linear-gradient(135deg,#5470c6,#91cc75);-webkit-background-clip:text;-webkit-text-fill-color:transparent">
            {{ statValue(w) }}
          </div>
          <div style="color:#999;margin-top:10px;font-size:13px">
            {{ w.fieldName === '__count__' ? '记录总数' : w.fieldLabel }}
          </div>
          <div style="margin-top:16px;padding-top:16px;border-top:1px solid #f5f5f5;display:flex;justify-content:center;gap:24px">
            <div style="text-align:center">
              <div style="font-size:20px;font-weight:600;color:#5470c6">{{ (formDataMap[w.templateId] || []).length }}</div>
              <div style="font-size:11px;color:#bbb;margin-top:2px">总记录</div>
            </div>
            <div style="text-align:center">
              <div style="font-size:20px;font-weight:600;color:#91cc75">{{ statValue(w) }}</div>
              <div style="font-size:11px;color:#bbb;margin-top:2px">{{ w.fieldName === '__count__' ? '总数' : '分类数' }}</div>
            </div>
          </div>
        </div>

        <!-- 图表 -->
        <div v-else style="padding:16px 18px">
          <DashboardChart :type="w.chartType" :data="chartData(w)" style="height:280px" />
          <!-- 图表底部摘要 -->
          <div style="margin-top:10px;padding-top:10px;border-top:1px solid #f5f5f5;display:flex;justify-content:space-between;font-size:12px;color:#999">
            <span>共 {{ (formDataMap[w.templateId] || []).length }} 条记录</span>
            <span>{{ chartData(w).length }} 个分类</span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Setting, Refresh, DataLine, PieChart, TrendCharts, Odometer } from '@element-plus/icons-vue'
import { getTemplates } from '../api/templates'
import { getForms } from '../api/forms'
import DashboardChart from '../components/DashboardChart.vue'

const STORAGE_KEY = 'dashboard_config'

const allWidgets = ref([])
const selectedTemplates = ref([])
const formDataMap = ref({})
const loading = ref(false)

const availableTemplates = computed(() => {
  const ids = [...new Set(allWidgets.value.map(w => w.templateId))]
  return ids.map(id => ({ id, name: allWidgets.value.find(w => w.templateId === id)?.templateName || id }))
})

const filteredWidgets = computed(() => {
  if (!selectedTemplates.value.length) return allWidgets.value
  return allWidgets.value.filter(w => selectedTemplates.value.includes(w.templateId))
})

function chartIcon(type) {
  return { bar: DataLine, pie: PieChart, line: TrendCharts, stat: Odometer }[type] || DataLine
}

function headerBg(type) {
  return { bar: '#f0f4ff', pie: '#fff7f0', line: '#f0fff4', stat: '#fdf0ff' }[type] || '#f5f5f5'
}

function headerColor(type) {
  return { bar: '#5470c6', pie: '#ee6666', line: '#91cc75', stat: '#9a60b4' }[type] || '#999'
}

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
