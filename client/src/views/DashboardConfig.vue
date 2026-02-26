<template>
  <el-card>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <span style="font-size:16px;font-weight:600">仪表盘配置</span>
      <el-button type="primary" @click="openAdd">+ 添加图表</el-button>
    </div>

    <el-empty v-if="!widgets.length" description="暂无图表，点击右上角添加" />

    <draggable v-else v-model="widgets" item-key="id" handle=".drag-handle"
      style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px"
      @end="save">
      <template #item="{ element, index }">
        <el-card shadow="hover" style="position:relative">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div style="display:flex;align-items:center;gap:8px">
              <el-icon class="drag-handle" style="cursor:move;color:#999"><Rank /></el-icon>
              <span style="font-weight:500">{{ element.title }}</span>
            </div>
            <div style="display:flex;gap:4px">
              <el-button size="small" link @click="openEdit(index)">编辑</el-button>
              <el-button size="small" link type="danger" @click="remove(index)">删除</el-button>
            </div>
          </div>
          <div style="margin-top:8px;font-size:12px;color:#999">
            {{ element.templateName }} · {{ element.fieldLabel || element.fieldName }} · {{ chartTypeLabel(element.chartType) }}
          </div>
        </el-card>
      </template>
    </draggable>

    <!-- 添加/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editIndex >= 0 ? '编辑图表' : '添加图表'" width="480px" draggable>
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="图表标题" />
        </el-form-item>
        <el-form-item label="数据模板">
          <el-select v-model="form.templateId" placeholder="选择模板" style="width:100%" @change="onTemplateChange">
            <el-option v-for="t in templateList" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="统计字段">
          <el-select v-model="form.fieldName" placeholder="选择字段" style="width:100%" :disabled="!form.templateId" @change="onFieldChange">
            <el-option label="（记录总数）" value="__count__" />
            <el-option v-for="f in currentFields" :key="f.name" :label="f.label" :value="f.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="图表类型">
          <el-select v-model="form.chartType" style="width:100%">
            <el-option label="柱状图" value="bar" />
            <el-option label="饼图" value="pie" />
            <el-option label="折线图" value="line" />
            <el-option label="数值统计" value="stat" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmSave">确定</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Rank } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import { getTemplates } from '../api/templates'

const STORAGE_KEY = 'dashboard_config'

const templateList = ref([])
const widgets = ref([])
const dialogVisible = ref(false)
const editIndex = ref(-1)
const form = ref({ title: '', templateId: null, fieldName: '', chartType: 'bar' })

const currentFields = computed(() => {
  const tpl = templateList.value.find(t => t.id === form.value.templateId)
  return tpl ? tpl.meta_data : []
})

onMounted(async () => {
  const res = await getTemplates({ page: 1, page_size: 100 })
  templateList.value = res.data.list
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) widgets.value = JSON.parse(saved)
})

function save() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(widgets.value))
}

function chartTypeLabel(t) {
  return { bar: '柱状图', pie: '饼图', line: '折线图', stat: '数值统计' }[t] || t
}

function openAdd() {
  editIndex.value = -1
  form.value = { title: '', templateId: null, fieldName: '', chartType: 'bar' }
  dialogVisible.value = true
}

function openEdit(idx) {
  editIndex.value = idx
  form.value = { ...widgets.value[idx] }
  dialogVisible.value = true
}

function remove(idx) {
  widgets.value.splice(idx, 1)
  save()
}

function onTemplateChange() {
  form.value.fieldName = ''
  const tpl = templateList.value.find(t => t.id === form.value.templateId)
  if (tpl && !form.value.title) form.value.title = tpl.name
}

function onFieldChange() {
  const field = currentFields.value.find(f => f.name === form.value.fieldName)
  if (field && !form.value.title) form.value.title = field.label
}

function confirmSave() {
  if (!form.value.title) return ElMessage.warning('请填写标题')
  if (!form.value.templateId) return ElMessage.warning('请选择模板')
  if (!form.value.fieldName) return ElMessage.warning('请选择统计字段')

  const tpl = templateList.value.find(t => t.id === form.value.templateId)
  const field = currentFields.value.find(f => f.name === form.value.fieldName)
  const widget = {
    id: editIndex.value >= 0 ? widgets.value[editIndex.value].id : Date.now().toString(),
    title: form.value.title,
    templateId: form.value.templateId,
    templateName: tpl?.name || '',
    fieldName: form.value.fieldName,
    fieldLabel: field?.label || form.value.fieldName,
    fieldType: field?.type || 'text',
    chartType: form.value.chartType,
  }

  if (editIndex.value >= 0) {
    widgets.value[editIndex.value] = widget
  } else {
    widgets.value.push(widget)
  }
  save()
  dialogVisible.value = false
}
</script>
