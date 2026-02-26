<template>
  <div>
    <!-- 全局筛选栏 -->
    <div style="background:#fff;border-radius:12px;padding:14px 18px;margin-bottom:18px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
      <span style="font-size:15px;font-weight:600;color:#1a1a2e;flex:none">仪表盘</span>
      <el-date-picker v-model="globalDateRange" type="daterange" range-separator="至"
        start-placeholder="开始日期" end-placeholder="结束日期" style="width:280px"
        value-format="YYYY-MM-DD" @change="onDateChange" clearable />
      <el-select v-model="selectedTemplates" multiple collapse-tags collapse-tags-tooltip
        placeholder="筛选数据来源" style="width:240px" @change="loadData">
        <el-option v-for="t in availableTemplates" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>
      <div v-if="activeFilter" style="display:flex;align-items:center;gap:6px">
        <el-tag closable @close="activeFilter=null" type="warning" size="small">
          联动筛选: {{ activeFilter.value }}
        </el-tag>
      </div>
      <div style="margin-left:auto;display:flex;gap:8px">
        <span v-if="lastUpdated" style="font-size:12px;color:#bbb;align-self:center">{{ lastUpdated }}</span>
        <el-button :icon="Refresh" circle @click="loadData" :loading="loading" size="small" />
        <el-button size="small" @click="$router.push('/dashboard-config')">
          <el-icon><Setting /></el-icon> 配置
        </el-button>
      </div>
    </div>

    <el-empty v-if="!filteredWidgets.length" description="暂无仪表盘，点击右上角「配置」添加图表">
      <el-button type="primary" @click="$router.push('/dashboard-config')">立即配置</el-button>
    </el-empty>

    <!-- 4列网格，支持 quarter/half/full -->
    <div v-else style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px">
      <div v-for="w in filteredWidgets" :key="w.id" :style="spanStyle(w.size)">

        <!-- stat 卡片 -->
        <div v-if="w.chartType === 'stat'"
          :style="`background:${statGradient(w)};border-radius:12px;padding:24px 22px;color:#fff;height:100%;box-sizing:border-box`"
          v-loading="loading">
          <div style="font-size:13px;opacity:0.85;margin-bottom:10px">{{ w.title }}</div>
          <div style="font-size:52px;font-weight:700;line-height:1">{{ fmtNum(statValue(w)) }}</div>
          <div style="font-size:12px;opacity:0.7;margin-top:6px">
            {{ aggLabel(w.aggregation) }} · {{ w.fieldName === '__count__' ? '记录总数' : w.fieldLabel }}
          </div>
          <!-- 趋势 -->
          <div v-if="w.showTrend && trendInfo(w)" style="margin-top:14px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.2);display:flex;align-items:center;gap:6px">
            <el-icon :style="`color:${trendInfo(w).up ? '#a8ffb0' : '#ffb3b3'}`">
              <component :is="trendInfo(w).up ? ArrowUp : ArrowDown" />
            </el-icon>
            <span style="font-size:13px">{{ trendInfo(w).pct }}% 较上期</span>
          </div>
        </div>

        <!-- gauge 卡片 -->
        <el-card v-else-if="w.chartType === 'gauge'" shadow="hover" style="border-radius:12px;overflow:hidden" body-style="padding:0" v-loading="loading">
          <div :style="`background:${headerBg(w.chartType)};padding:12px 16px;display:flex;justify-content:space-between;align-items:center`">
            <div style="display:flex;align-items:center;gap:8px">
              <div :style="`width:4px;height:16px;border-radius:2px;background:${headerColor(w.chartType)}`"></div>
              <span style="font-weight:600;font-size:14px">{{ w.title }}</span>
            </div>
            <el-tag size="small" style="background:transparent;border-color:#e0e0e0">{{ w.templateName }}</el-tag>
          </div>
          <div style="padding:12px 16px">
            <DashboardChart type="gauge" :data="gaugeData(w)" :gauge-max="w.gaugeMax || 100" style="height:220px" />
          </div>
        </el-card>

        <!-- table 卡片 -->
        <el-card v-else-if="w.chartType === 'table'" shadow="hover" style="border-radius:12px;overflow:hidden" body-style="padding:0" v-loading="loading">
          <div :style="`background:${headerBg(w.chartType)};padding:12px 16px;display:flex;justify-content:space-between;align-items:center`">
            <div style="display:flex;align-items:center;gap:8px">
              <div :style="`width:4px;height:16px;border-radius:2px;background:${headerColor(w.chartType)}`"></div>
              <span style="font-weight:600;font-size:14px">{{ w.title }}</span>
            </div>
            <el-tag size="small" style="background:transparent;border-color:#e0e0e0">Top {{ w.topN || 10 }}</el-tag>
          </div>
          <div style="padding:0 16px 12px">
            <el-table :data="tableData(w)" size="small" style="width:100%" max-height="280">
              <el-table-column v-for="f in (w.tableFields || [])" :key="f.name"
                :prop="f.name" :label="f.label" show-overflow-tooltip />
            </el-table>
          </div>
        </el-card>

        <!-- 普通图表卡片 -->
        <el-card v-else shadow="hover" style="border-radius:12px;overflow:hidden" body-style="padding:0" v-loading="loading">
          <div :style="`background:${headerBg(w.chartType)};padding:12px 16px;display:flex;justify-content:space-between;align-items:center`">
            <div style="display:flex;align-items:center;gap:8px">
              <div :style="`width:4px;height:16px;border-radius:2px;background:${headerColor(w.chartType)}`"></div>
              <span style="font-weight:600;font-size:14px">{{ w.title }}</span>
            </div>
            <el-tag size="small" style="background:transparent;border-color:#e0e0e0">{{ w.templateName }}</el-tag>
          </div>
          <div style="padding:12px 16px">
            <DashboardChart
              :type="w.chartType"
              :data="singleData(w)"
              :series="multiSeries(w)"
              style="height:260px"
              @click="onChartClick(w, $event)"
            />
            <div style="margin-top:8px;padding-top:8px;border-top:1px solid #f5f5f5;display:flex;justify-content:space-between;font-size:12px;color:#999">
              <span>{{ getFilteredRows(w).length }} 条记录</span>
              <span v-if="activeFilter?.templateId === w.templateId" style="color:#e6a23c">
                已联动筛选: {{ activeFilter.value }}
              </span>
            </div>
          </div>
        </el-card>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Setting, Refresh, ArrowUp, ArrowDown } from '@element-plus/icons-vue'
import { getForms } from '../api/forms'
import DashboardChart from '../components/DashboardChart.vue'

const STORAGE_KEY = 'dashboard_config'
const STAT_GRADIENTS = [
  'linear-gradient(135deg,#667eea,#764ba2)',
  'linear-gradient(135deg,#4facfe,#00f2fe)',
  'linear-gradient(135deg,#43e97b,#38f9d7)',
  'linear-gradient(135deg,#fa709a,#fee140)',
  'linear-gradient(135deg,#f093fb,#f5576c)',
  'linear-gradient(135deg,#a18cd1,#fbc2eb)',
  'linear-gradient(135deg,#ffecd2,#fcb69f)',
  'linear-gradient(135deg,#a1c4fd,#c2e9fb)',
]

const allWidgets = ref([])
const selectedTemplates = ref([])
const formDataMap = ref({})
const loading = ref(false)
const lastUpdated = ref('')
const globalDateRange = ref(null)
const activeFilter = ref(null)

const availableTemplates = computed(() => {
  const ids = [...new Set(allWidgets.value.map(w => w.templateId))]
  return ids.map(id => ({ id, name: allWidgets.value.find(w => w.templateId === id)?.templateName || id }))
})

const filteredWidgets = computed(() => {
  if (!selectedTemplates.value.length) return allWidgets.value
  return allWidgets.value.filter(w => selectedTemplates.value.includes(w.templateId))
})

function spanStyle(size) {
  const span = { quarter: 1, half: 2, full: 4 }[size] || 2
  return `grid-column: span ${span}`
}

function headerBg(type) {
  return { bar: '#f0f4ff', pie: '#fff7f0', line: '#f0fff4', stat: '#fdf0ff', gauge: '#f0faff', funnel: '#fffbf0', table: '#f5f5f5', scatter: '#f0fff8' }[type] || '#f5f5f5'
}

function headerColor(type) {
  return { bar: '#5470c6', pie: '#ee6666', line: '#91cc75', stat: '#9a60b4', gauge: '#73c0de', funnel: '#fac858', table: '#909399', scatter: '#3ba272' }[type] || '#999'
}

function statGradient(w) {
  return STAT_GRADIENTS[(w.colorTheme ?? 0) % STAT_GRADIENTS.length]
}

function aggLabel(agg) {
  return { count: '计数', sum: '求和', avg: '平均值', max: '最大值', min: '最小值' }[agg] || '计数'
}

// 获取经过全局日期筛选 + 联动筛选后的行
function getFilteredRows(w) {
  let rows = formDataMap.value[w.templateId] || []

  // 全局日期筛选
  if (globalDateRange.value && w.dateField) {
    const [s, e] = globalDateRange.value
    const start = new Date(s), end = new Date(e + 'T23:59:59')
    rows = rows.filter(r => {
      const d = new Date(r[w.dateField])
      return d >= start && d <= end
    })
  }

  // 联动筛选（来自其他 widget 的点击）
  if (activeFilter.value && activeFilter.value.templateId === w.templateId && activeFilter.value.widgetId !== w.id) {
    const { fieldName, value } = activeFilter.value
    rows = rows.filter(r => {
      const v = r[fieldName]
      return Array.isArray(v) ? v.includes(value) : String(v ?? '') === String(value)
    })
  }

  return rows
}

// 聚合计算
function aggregate(values, agg) {
  if (agg === 'count') return values.length  // count 统计总行数，不限于数值
  const nums = values.map(Number).filter(v => !isNaN(v))
  if (!nums.length) return 0
  switch (agg) {
    case 'sum': return Math.round(nums.reduce((a, b) => a + b, 0) * 100) / 100
    case 'avg': return Math.round(nums.reduce((a, b) => a + b, 0) / nums.length * 100) / 100
    case 'max': return Math.max(...nums)
    case 'min': return Math.min(...nums)
    default: return values.length
  }
}

// 按日期分组
function groupByDate(rows, dateField, groupBy) {
  const groups = {}
  for (const row of rows) {
    const d = new Date(row[dateField])
    if (isNaN(d)) continue
    let key
    if (groupBy === 'year') key = `${d.getFullYear()}`
    else if (groupBy === 'month') key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    else if (groupBy === 'week') {
      const jan1 = new Date(d.getFullYear(), 0, 1)
      const wk = Math.ceil(((d - jan1) / 86400000 + jan1.getDay() + 1) / 7)
      key = `${d.getFullYear()}-W${String(wk).padStart(2, '0')}`
    } else {
      key = row[dateField]?.slice(0, 10) || ''
    }
    if (!key) continue
    groups[key] = groups[key] || []
    groups[key].push(row)
  }
  return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b))
}

// 单系列数据（pie/funnel/scatter/单字段bar/line）
function singleData(w) {
  const rows = getFilteredRows(w)
  if (w.chartType === 'scatter') {
    return rows.map(r => ({ x: Number(r[w.xField] ?? 0), y: Number(r[w.yField] ?? 0), name: r[w.xField] }))
  }
  if (w.dateField && w.dateGroupBy && !w.extraFields?.length) {
    const groups = groupByDate(rows, w.dateField, w.dateGroupBy)
    return groups.map(([k, r]) => ({ name: k, value: aggregate(r.map(row => row[w.fieldName]), w.aggregation || 'count') }))
  }
  if (w.fieldName === '__count__') return [{ name: '总数', value: rows.length }]
  const counts = {}
  for (const row of rows) {
    const val = row[w.fieldName]
    const keys = Array.isArray(val) ? val : [val == null || val === '' ? '(空)' : String(val)]
    for (const k of keys) counts[k] = (counts[k] || 0) + 1
  }
  return Object.entries(counts).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value).slice(0, 20)
}

// 多系列数据（多字段 bar/line）
function multiSeries(w) {
  if (!w.extraFields?.length) return []
  if (w.chartType !== 'bar' && w.chartType !== 'line') return []
  const rows = getFilteredRows(w)
  const allFields = [{ name: w.fieldName, label: w.fieldLabel, aggregation: w.aggregation || 'count' }, ...w.extraFields]

  if (w.dateField && w.dateGroupBy) {
    const groups = groupByDate(rows, w.dateField, w.dateGroupBy)
    return allFields.map(f => ({
      name: f.label,
      data: groups.map(([k, r]) => ({ name: k, value: aggregate(r.map(row => row[f.name]), f.aggregation || 'count') }))
    }))
  }

  // 按主字段分类，每个额外字段作为一个系列
  const categories = [...new Set(rows.map(r => String(r[w.fieldName] ?? '(空)')))]
  return allFields.map(f => ({
    name: f.label,
    data: categories.map(cat => {
      const catRows = rows.filter(r => String(r[w.fieldName] ?? '(空)') === cat)
      return { name: cat, value: aggregate(catRows.map(r => r[f.name]), f.aggregation || 'count') }
    })
  }))
}

// stat 值
function statValue(w) {
  const rows = getFilteredRows(w)
  if (w.fieldName === '__count__') return rows.length
  return aggregate(rows.map(r => r[w.fieldName]), w.aggregation || 'count')
}

// gauge 数据
function gaugeData(w) {
  return [{ name: w.title, value: statValue(w) }]
}

// table 数据
function tableData(w) {
  const rows = getFilteredRows(w)
  return rows.slice(0, w.topN || 10)
}

// 趋势：对比全量数据 vs 筛选后数据
function trendInfo(w) {
  if (!globalDateRange.value) return null
  const all = formDataMap.value[w.templateId] || []
  const filtered = getFilteredRows(w)
  const allVal = w.fieldName === '__count__' ? all.length : aggregate(all.map(r => r[w.fieldName]), w.aggregation || 'count')
  const curVal = w.fieldName === '__count__' ? filtered.length : aggregate(filtered.map(r => r[w.fieldName]), w.aggregation || 'count')
  if (!allVal) return null
  const pct = Math.abs(Math.round((curVal - allVal) / allVal * 100))
  return { up: curVal >= allVal, pct }
}

function fmtNum(v) {
  if (typeof v === 'number' && v >= 1000) return v.toLocaleString()
  return v
}

function onChartClick(w, params) {
  const val = params.name
  if (activeFilter.value?.widgetId === w.id && activeFilter.value?.value === val) {
    activeFilter.value = null
  } else {
    activeFilter.value = { widgetId: w.id, templateId: w.templateId, fieldName: w.fieldName, value: val }
  }
}

function onDateChange() {
  // 日期变化时重新渲染（数据已在内存中，无需重新请求）
}

onMounted(async () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  allWidgets.value = saved ? JSON.parse(saved) : []
  await loadData()
})

async function loadData() {
  const templateIds = [...new Set(allWidgets.value.map(w => w.templateId))].filter(Boolean)
  if (!templateIds.length) return
  loading.value = true
  try {
    await Promise.all(templateIds.map(async tid => {
      const res = await getForms({ page: 1, page_size: 5000, template_id: tid })
      formDataMap.value[tid] = res.data.list.map(r => r.data)
    }))
    const now = new Date()
    lastUpdated.value = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')} 更新`
  } finally {
    loading.value = false
  }
}
</script>
