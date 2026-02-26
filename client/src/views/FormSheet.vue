<template>
  <el-card>
    <!-- 顶部操作栏 -->
    <div style="display:flex;justify-content:space-between;margin-bottom:16px;align-items:center">
      <div style="display:flex;gap:12px;align-items:center">
        <el-select v-model="templateId" placeholder="请选择模板" style="width:220px" @change="onTemplateChange">
          <el-option v-for="t in templateList" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-tag v-if="changeCount" type="warning">{{ changeCount }} 项变更</el-tag>
      </div>
      <div style="display:flex;gap:8px">
        <el-button @click="addRow">添加行</el-button>
        <el-dropdown @command="handleImportCommand">
          <el-button>导入<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="template">下载导入模板</el-dropdown-item>
              <el-dropdown-item command="import">导入数据</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <input ref="importFileInput" type="file" accept=".csv,.xlsx,.xls" style="display:none" @change="onFileInputChange" />
        <el-dropdown @command="handleExport">
          <el-button>导出<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="xlsx">导出 Excel (.xlsx)</el-dropdown-item>
              <el-dropdown-item command="csv">导出 CSV (.csv)</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="primary" :loading="saving" :disabled="!changeCount" @click="handleSave">保存</el-button>
      </div>
    </div>

    <!-- 可编辑表格 -->
    <el-table :data="tableData" v-loading="loading" border style="width:100%" @cell-click="handleCellClick">
      <el-table-column type="index" label="#" width="50" />
      <el-table-column v-for="field in metaFields" :key="field.name" :label="field.label" :prop="field.name" min-width="140">
        <template #default="{ row, $index }">
          <!-- 编辑态 -->
          <template v-if="editingCell.row === $index && editingCell.col === field.name">
            <el-input v-if="field.type === 'text'" v-model="row.data[field.name]" size="small" @blur="onCellBlur(row)" @keyup.enter="editingCell = {}" />
            <el-input-number v-else-if="field.type === 'number'" v-model="row.data[field.name]" size="small" controls-position="right" @blur="onCellBlur(row)" @keyup.enter="editingCell = {}" />
            <el-date-picker v-else-if="field.type === 'date'" v-model="row.data[field.name]" type="date" value-format="YYYY-MM-DD" size="small" @change="onCellBlur(row)" />
            <el-select v-else-if="field.type === 'radio'" v-model="row.data[field.name]" size="small" @change="onCellBlur(row)">
              <el-option v-for="opt in field.options" :key="opt" :label="opt" :value="opt" />
            </el-select>
            <el-checkbox-group v-else-if="field.type === 'checkbox'" v-model="row.data[field.name]" size="small" @change="onCellBlur(row)">
              <el-checkbox v-for="opt in field.options" :key="opt" :value="opt" :label="opt" />
            </el-checkbox-group>
          </template>
          <!-- 展示态 -->
          <span v-else :class="{ 'cell-new': row._status === 'new', 'cell-modified': row._status === 'modified' }">
            {{ formatCell(row.data[field.name]) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="70" fixed="right">
        <template #default="{ row, $index }">
          <el-button size="small" link type="danger" @click="deleteRow($index, row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:16px;justify-content:flex-end" v-model:current-page="page" v-model:page-size="pageSize" :total="total" :page-sizes="[20,50,100,200]" layout="total,sizes,prev,pager,next" @change="loadData" />

    <!-- 导入预览弹窗 -->
    <el-dialog v-model="importVisible" title="导入预览" width="700px">
      <p style="margin-bottom:12px">共解析 {{ importRows.length }} 行数据，请确认列映射：</p>
      <el-table :data="importPreview" border size="small" max-height="300">
        <el-table-column v-for="(col, idx) in importHeaders" :key="idx" :label="col" min-width="120">
          <template #header>
            <div>
              <div style="font-size:12px;color:#999">{{ col }}</div>
              <el-select v-model="columnMapping[idx]" size="small" placeholder="映射到" clearable style="width:100%">
                <el-option v-for="f in metaFields" :key="f.name" :label="f.label" :value="f.name" />
              </el-select>
            </div>
          </template>
          <template #default="{ row }">{{ row[idx] }}</template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmImport">确认导入</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { getForms, updateForm, deleteForm, batchCreateForms } from '../api/forms'
import { getTemplates } from '../api/templates'

const templateList = ref([])
const templateId = ref(null)
const metaFields = ref([])
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const loading = ref(false)
const saving = ref(false)
const editingCell = reactive({ row: null, col: null })
const deletedRows = ref([])

// 导入相关
const importVisible = ref(false)
const importHeaders = ref([])
const importRows = ref([])
const importPreview = computed(() => importRows.value.slice(0, 5))
const columnMapping = reactive({})
const importFileInput = ref()

// 变更计数
const changeCount = computed(() => {
  const changed = tableData.value.filter(r => r._status === 'new' || r._status === 'modified').length
  return changed + deletedRows.value.length
})

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
  deletedRows.value = []
  page.value = 1
  loadData()
}

async function loadData() {
  if (!templateId.value) return
  loading.value = true
  try {
    const res = await getForms({ page: page.value, page_size: pageSize.value, template_id: templateId.value })
    tableData.value = res.data.list.map(r => ({ ...r, _status: '', _original: JSON.stringify(r.data) }))
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

// 单元格编辑
function handleCellClick(row, column) {
  const field = metaFields.value.find(f => f.name === column.property)
  if (!field) return
  const idx = tableData.value.indexOf(row)
  editingCell.row = idx
  editingCell.col = field.name
}

function onCellBlur(row) {
  editingCell.row = null
  editingCell.col = null
  if (row._status !== 'new') {
    row._status = JSON.stringify(row.data) !== row._original ? 'modified' : ''
  }
}

// 添加/删除行
function addRow() {
  if (!metaFields.value.length) return ElMessage.warning('请先选择模板')
  const data = {}
  for (const f of metaFields.value) {
    data[f.name] = f.type === 'checkbox' ? [] : f.type === 'number' ? 0 : ''
  }
  tableData.value.push({ id: null, data, _status: 'new', _original: '' })
}

function deleteRow(idx, row) {
  if (row.id) deletedRows.value.push(row.id)
  tableData.value.splice(idx, 1)
}

// 保存
async function handleSave() {
  saving.value = true
  try {
    const newRows = tableData.value.filter(r => r._status === 'new')
    const modifiedRows = tableData.value.filter(r => r._status === 'modified')

    // 批量新增
    if (newRows.length) {
      await batchCreateForms({ template_id: templateId.value, items: newRows.map(r => r.data) })
    }
    // 逐条更新
    for (const row of modifiedRows) {
      await updateForm(row.id, { data: row.data })
    }
    // 逐条删除
    for (const id of deletedRows.value) {
      await deleteForm(id)
    }
    ElMessage.success('保存成功')
    deletedRows.value = []
    loadData()
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 导入
function handleImportCommand(cmd) {
  if (!templateId.value) return ElMessage.warning('请先选择模板')
  if (cmd === 'template') {
    const headers = metaFields.value.map(f => f.label)
    const ws = XLSX.utils.aoa_to_sheet([headers])
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '导入模板')
    const tplName = templateList.value.find(t => t.id === templateId.value)?.name || '模板'
    XLSX.writeFile(wb, `${tplName}_导入模板.xlsx`)
  } else {
    importFileInput.value.value = ''
    importFileInput.value.click()
  }
}

function onFileInputChange(e) {
  const file = e.target.files[0]
  if (file) handleImportFile(file)
}

function handleImportFile(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    const wb = XLSX.read(e.target.result, { type: 'array' })
    const sheet = wb.Sheets[wb.SheetNames[0]]
    const raw = XLSX.utils.sheet_to_json(sheet, { header: 1 })
    if (raw.length < 2) return ElMessage.warning('文件为空或仅有表头')
    importHeaders.value = raw[0].map(String)
    importRows.value = raw.slice(1).filter(r => r.some(c => c !== '' && c != null))
    // 自动映射：表头名匹配字段 label 或 name
    for (let i = 0; i < importHeaders.value.length; i++) {
      const h = importHeaders.value[i]
      const match = metaFields.value.find(f => f.label === h || f.name === h)
      columnMapping[i] = match ? match.name : ''
    }
    importVisible.value = true
  }
  reader.readAsArrayBuffer(file)
  return false // 阻止 el-upload 自动上传
}

function confirmImport() {
  const mapped = Object.entries(columnMapping).filter(([, v]) => v)
  if (!mapped.length) return ElMessage.warning('请至少映射一列')

  const errors = []
  const parsedRows = []

  for (let rowIdx = 0; rowIdx < importRows.value.length; rowIdx++) {
    const row = importRows.value[rowIdx]
    const data = {}
    for (const f of metaFields.value) {
      data[f.name] = f.type === 'checkbox' ? [] : f.type === 'number' ? 0 : ''
    }
    for (const [colIdx, fieldName] of mapped) {
      const val = row[colIdx]
      const field = metaFields.value.find(f => f.name === fieldName)
      if (!field) continue
      if (field.type === 'number') {
        if (val !== '' && val != null && isNaN(Number(val))) {
          errors.push(`第 ${rowIdx + 1} 行「${field.label}」必须为数字，当前值：${val}`)
        }
        data[fieldName] = Number(val) || 0
      } else if (field.type === 'checkbox') {
        data[fieldName] = val ? String(val).split(',').map(s => s.trim()) : []
      } else {
        data[fieldName] = val != null ? String(val) : ''
      }
    }
    // 必填校验
    for (const f of metaFields.value) {
      if (!f.required) continue
      const v = data[f.name]
      const empty = v == null || v === '' || (Array.isArray(v) && !v.length)
      if (empty) errors.push(`第 ${rowIdx + 1} 行「${f.label}」为必填项`)
    }
    parsedRows.push(data)
  }

  if (errors.length) {
    ElMessageBox.alert(errors.slice(0, 10).join('\n') + (errors.length > 10 ? `\n...共 ${errors.length} 个错误` : ''), '数据校验失败', { type: 'error', whiteSpace: 'pre' })
    return
  }

  for (const data of parsedRows) {
    tableData.value.push({ id: null, data, _status: 'new', _original: '' })
  }
  ElMessage.success(`已导入 ${parsedRows.length} 行`)
  importVisible.value = false
}

// 导出
function handleExport(type) {
  if (!tableData.value.length) return ElMessage.warning('没有数据可导出')
  const headers = metaFields.value.map(f => f.label)
  const rows = tableData.value.map(r => metaFields.value.map(f => {
    const v = r.data[f.name]
    return Array.isArray(v) ? v.join(',') : v
  }))
  const ws = XLSX.utils.aoa_to_sheet([headers, ...rows])
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '数据')
  const tplName = templateList.value.find(t => t.id === templateId.value)?.name || '数据'
  if (type === 'csv') {
    XLSX.writeFile(wb, `${tplName}.csv`, { bookType: 'csv' })
  } else {
    XLSX.writeFile(wb, `${tplName}.xlsx`)
  }
}

function formatCell(val) {
  if (val == null) return ''
  if (Array.isArray(val)) return val.join(', ')
  return String(val)
}
</script>

<style scoped>
.cell-new { color: #67c23a; }
.cell-modified { color: #e6a23c; }
</style>
