<template>
  <el-card>
    <!-- 模板选择 -->
    <div style="display:flex;gap:12px;margin-bottom:16px;align-items:center">
      <el-select v-model="templateId" placeholder="请选择模板" style="width:220px" @change="onTemplateChange">
        <el-option v-for="t in templateList" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>
      <el-button type="primary" @click="loadData">查询</el-button>
      <el-button @click="resetSearch">重置</el-button>
      <el-button type="success" :loading="exporting" :disabled="!templateId" @click="exportData">导出Excel</el-button>
      <!-- 恢复隐藏列 -->
      <el-dropdown v-if="hiddenFields.length" style="margin-left:auto" @command="restoreColumn">
        <el-button size="small">已隐藏 {{ hiddenFields.length }} 列<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item v-for="f in hiddenFields" :key="f.name" :command="f.name">{{ f.label }}</el-dropdown-item>
            <el-dropdown-item divided command="__all__">显示全部</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <!-- 筛选条件 -->
    <div v-if="metaFields.length" style="margin-bottom:16px">
      <div v-for="(filter, idx) in filters" :key="idx" style="display:flex;gap:8px;margin-bottom:8px;align-items:center">
        <el-select v-model="filter.field" placeholder="字段" style="width:150px">
          <el-option v-for="f in metaFields" :key="f.name" :label="f.label" :value="f.name" />
        </el-select>
        <el-select v-model="filter.op" style="width:110px">
          <el-option v-for="o in getOpsForField(filter.field)" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-input v-model="filter.value" :placeholder="filter.op === 'in' ? '多个值用逗号分隔' : '值'" style="width:200px" clearable @keyup.enter="loadData" />
        <el-button :icon="Delete" circle size="small" @click="filters.splice(idx, 1)" />
      </div>
      <el-button type="primary" plain size="small" @click="addFilter">+ 添加条件</el-button>
    </div>

    <!-- 数据表格 -->
    <el-table ref="tableRef" :data="list" v-loading="loading" border style="width:100%" :header-cell-class-name="headerCellClass">
      <el-table-column prop="id" label="ID" width="60">
        <template #header>
          <span class="col-header" @click="toggleSort('id')">
            ID <span v-if="sortField === 'id'" class="sort-icon">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
          </span>
        </template>
      </el-table-column>
      <el-table-column v-for="field in visibleFields" :key="field.name" :prop="field.name" :label="field.label" min-width="120">
        <template #header>
          <div class="col-header-wrap"
            draggable="true"
            @dragstart="onDragStart(field, $event)"
            @dragover.prevent="onDragOver(field, $event)"
            @drop="onDrop(field)"
            @dragend="dragTarget = null">
            <span class="col-header" @click="toggleSort(field.name)">
              {{ field.label }}
              <span v-if="sortField === field.name" class="sort-icon">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
            </span>
            <el-icon class="col-hide-btn" @click.stop="hideColumn(field.name)"><Close /></el-icon>
          </div>
        </template>
        <template #default="{ row }">
          {{ formatCell(row.data[field.name]) }}
        </template>
      </el-table-column>
      <el-table-column prop="username" label="提交人" width="100" />
      <el-table-column prop="create_time" label="创建时间" width="170">
        <template #header>
          <span class="col-header" @click="toggleSort('create_time')">
            创建时间 <span v-if="sortField === 'create_time'" class="sort-icon">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="update_time" label="更新时间" width="170">
        <template #header>
          <span class="col-header" @click="toggleSort('update_time')">
            更新时间 <span v-if="sortField === 'update_time'" class="sort-icon">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
          </span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80" fixed="right">
        <template #default="{ row }">
          <el-button size="small" link type="primary" @click="showDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:16px;justify-content:flex-end" v-model:current-page="page" v-model:page-size="pageSize" :total="total" :page-sizes="[10,20,50,100]" layout="total,sizes,prev,pager,next" @change="loadData" />

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="数据详情" width="600px">
      <el-descriptions v-if="detailData" :column="1" border>
        <el-descriptions-item label="ID">{{ detailData.id }}</el-descriptions-item>
        <el-descriptions-item label="所属模板">{{ detailData.template_name }}</el-descriptions-item>
        <el-descriptions-item label="提交人">{{ detailData.username }}</el-descriptions-item>
        <el-descriptions-item v-for="field in metaFields" :key="field.name" :label="field.label">
          {{ formatCell(detailData.data[field.name]) }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detailData.create_time }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ detailData.update_time }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Close, ArrowDown } from '@element-plus/icons-vue'
import { getForms } from '../api/forms'
import { getTemplates } from '../api/templates'
import * as XLSX from 'xlsx'

const allOps = [
  { value: '=', label: '=' },
  { value: '!=', label: '!=' },
  { value: '>', label: '>' },
  { value: '<', label: '<' },
  { value: '>=', label: '>=' },
  { value: '<=', label: '<=' },
  { value: 'like', label: '包含' },
  { value: 'in', label: 'IN' },
  { value: 'not_in', label: 'NOT IN' },
  { value: 'contains', label: '含有' },
]
const textOps = ['=', '!=', 'like', 'in', 'not_in']
const numberOps = ['=', '!=', '>', '<', '>=', '<=', 'in', 'not_in']
const dateOps = ['=', '!=', '>', '<', '>=', '<=']
const radioOps = ['=', '!=', 'in', 'not_in']
const checkboxOps = ['contains']

const templateList = ref([])
const templateId = ref(null)
const metaFields = ref([])
const displayFields = ref([])
const visibleFields = computed(() => displayFields.value.filter(f => f.visible))
const hiddenFields = computed(() => displayFields.value.filter(f => !f.visible))
const filters = reactive([])
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const detailVisible = ref(false)
const detailData = ref(null)
const sortField = ref('')
const sortOrder = ref('desc')
const tableRef = ref()
const dragTarget = ref(null)
const exporting = ref(false)

function getOpsForField(fieldName) {
  const field = metaFields.value.find(f => f.name === fieldName)
  if (!field) return allOps
  const opsMap = { number: numberOps, date: dateOps, radio: radioOps, checkbox: checkboxOps }
  const allowed = opsMap[field.type] || textOps
  return allOps.filter(o => allowed.includes(o.value))
}

function addFilter() {
  filters.push({ field: metaFields.value[0]?.name || '', op: '=', value: '' })
}

// 排序：点击表头切换
function toggleSort(field) {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortOrder.value = 'asc'
  }
  loadData()
}

// 拖拽列顺序
function onDragStart(field, e) {
  dragTarget.value = field.name
  e.dataTransfer.effectAllowed = 'move'
}
function onDragOver(field, e) {
  if (dragTarget.value && dragTarget.value !== field.name) {
    e.dataTransfer.dropEffect = 'move'
  }
}
function onDrop(targetField) {
  if (!dragTarget.value || dragTarget.value === targetField.name) return
  const arr = displayFields.value
  const fromIdx = arr.findIndex(f => f.name === dragTarget.value)
  const toIdx = arr.findIndex(f => f.name === targetField.name)
  if (fromIdx < 0 || toIdx < 0) return
  const [item] = arr.splice(fromIdx, 1)
  arr.splice(toIdx, 0, item)
  dragTarget.value = null
}

// 隐藏/恢复列
function hideColumn(name) {
  const f = displayFields.value.find(f => f.name === name)
  if (f) f.visible = false
}
function restoreColumn(name) {
  if (name === '__all__') {
    displayFields.value.forEach(f => f.visible = true)
  } else {
    const f = displayFields.value.find(f => f.name === name)
    if (f) f.visible = true
  }
}

function headerCellClass({ column }) {
  if (dragTarget.value && column.property === dragTarget.value) return 'dragging-col'
  return ''
}

onMounted(async () => {
  const res = await getTemplates({ page: 1, page_size: 100 })
  templateList.value = res.data.list
  if (templateList.value.length) {
    templateId.value = templateList.value[0].id
    onTemplateChange(templateId.value)
  }
})

function onTemplateChange(id) {
  const tpl = templateList.value.find(t => t.id === id)
  metaFields.value = tpl ? tpl.meta_data : []
  displayFields.value = metaFields.value.map(f => ({ ...f, visible: true }))
  filters.splice(0)
  sortField.value = ''
  sortOrder.value = 'desc'
  page.value = 1
  loadData()
}

function resetSearch() {
  filters.splice(0)
  sortField.value = ''
  sortOrder.value = 'desc'
  displayFields.value.forEach(f => f.visible = true)
  page.value = 1
  loadData()
}

async function loadData() {
  if (!templateId.value) {
    list.value = []
    total.value = 0
    return ElMessage.warning('请先选择模板')
  }
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value, template_id: templateId.value }
    const validFilters = filters.filter(f => f.field && f.value !== '')
    if (validFilters.length) {
      params.filters = JSON.stringify(validFilters.map(f => ({ field: f.field, op: f.op, value: f.value })))
    }
    if (sortField.value) {
      params.sort_field = sortField.value
      params.sort_order = sortOrder.value
    }
    const res = await getForms(params)
    list.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function showDetail(row) {
  detailData.value = row
  detailVisible.value = true
}

function formatCell(val) {
  if (val == null) return ''
  if (Array.isArray(val)) return val.join(', ')
  return String(val)
}

async function exportData() {
  if (!templateId.value) return ElMessage.warning('请先选择模板')
  exporting.value = true
  try {
    const params = { page: 1, page_size: 10000, template_id: templateId.value }
    const validFilters = filters.filter(f => f.field && f.value !== '')
    if (validFilters.length) {
      params.filters = JSON.stringify(validFilters.map(f => ({ field: f.field, op: f.op, value: f.value })))
    }
    if (sortField.value) {
      params.sort_field = sortField.value
      params.sort_order = sortOrder.value
    }
    const res = await getForms(params)
    const rows = res.data.list
    if (!rows.length) return ElMessage.warning('没有可导出的数据')

    const visible = displayFields.value.filter(f => f.visible)
    const headers = ['ID', ...visible.map(f => f.label), '提交人', '创建时间', '更新时间']
    const data = rows.map(row => [
      row.id,
      ...visible.map(f => formatCell(row[f.name])),
      row.username,
      row.create_time,
      row.update_time
    ])
    data.unshift(headers)

    const ws = XLSX.utils.aoa_to_sheet(data)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')

    const tpl = templateList.value.find(t => t.id === templateId.value)
    const date = new Date().toISOString().slice(0, 10)
    XLSX.writeFile(wb, `${tpl?.name || 'export'}_${date}.xlsx`)
    ElMessage.success(`已导出 ${rows.length} 条数据`)
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
.col-header-wrap {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: grab;
  user-select: none;
}
.col-header-wrap:active { cursor: grabbing; }
.col-header {
  cursor: pointer;
  user-select: none;
  flex: 1;
}
.col-header:hover { color: #409eff; }
.sort-icon { color: #409eff; font-weight: bold; }
.col-hide-btn {
  font-size: 12px;
  color: #c0c4cc;
  cursor: pointer;
  flex-shrink: 0;
}
.col-hide-btn:hover { color: #f56c6c; }
:deep(.dragging-col) { opacity: 0.5; }
</style>
