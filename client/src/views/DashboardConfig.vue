<template>
  <el-card style="border-radius:12px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <div>
        <span style="font-size:18px;font-weight:600;color:#1a1a2e">仪表盘配置</span>
        <span style="font-size:13px;color:#999;margin-left:10px">拖拽卡片可调整顺序</span>
      </div>
      <div style="display:flex;gap:8px">
        <el-button @click="$router.push('/')">
          <el-icon><ArrowLeft /></el-icon> 返回仪表盘
        </el-button>
        <el-button type="primary" @click="openAdd">
          <el-icon><Plus /></el-icon> 添加图表
        </el-button>
      </div>
    </div>

    <el-empty v-if="!widgets.length" description="暂无图表配置，点击右上角添加">
      <el-button type="primary" @click="openAdd">立即添加</el-button>
    </el-empty>

    <draggable v-else v-model="widgets" item-key="id" handle=".drag-handle"
      style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px"
      @end="save">
      <template #item="{ element, index }">
        <el-card shadow="hover" style="border-radius:10px;overflow:hidden" body-style="padding:0">
          <!-- 彩色顶条 -->
          <div :style="`height:4px;background:${typeColor(element.chartType)}`" />
          <div style="padding:14px 16px">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <div style="display:flex;align-items:center;gap:8px">
                <el-icon class="drag-handle" style="cursor:move;color:#ccc;font-size:16px"><Rank /></el-icon>
                <span style="font-weight:600;font-size:14px">{{ element.title }}</span>
              </div>
              <div style="display:flex;gap:4px">
                <el-button size="small" link @click="openEdit(index)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button size="small" link type="danger" @click="remove(index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <div style="margin-top:10px;display:flex;gap:6px;flex-wrap:wrap">
              <el-tag size="small" type="info">{{ element.templateName }}</el-tag>
              <el-tag size="small" :color="typeBg(element.chartType)" style="border:none" :style="`color:${typeColor(element.chartType)}`">
                {{ chartTypeLabel(element.chartType) }}
              </el-tag>
              <el-tag size="small" type="success" v-if="element.fieldName !== '__count__'">{{ element.fieldLabel }}</el-tag>
              <el-tag size="small" v-else>记录总数</el-tag>
            </div>
          </div>
        </el-card>
      </template>
    </draggable>

    <!-- 添加/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editIndex >= 0 ? '编辑图表' : '添加图表'" width="500px" draggable>
      <el-form :model="form" label-width="88px">
        <el-form-item label="图表标题">
          <el-input v-model="form.title" placeholder="输入图表标题" />
        </el-form-item>
        <el-form-item label="数据模板">
          <el-select v-model="form.templateId" placeholder="选择数据来源模板" style="width:100%" @change="onTemplateChange">
            <el-option v-for="t in templateList" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="统计字段">
          <el-select v-model="form.fieldName" placeholder="选择统计字段" style="width:100%" :disabled="!form.templateId" @change="onFieldChange">
            <el-option label="（记录总数）" value="__count__" />
            <el-option v-for="f in currentFields" :key="f.name" :label="f.label" :value="f.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="图表类型">
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;width:100%">
            <div v-for="opt in chartTypeOptions" :key="opt.value"
              @click="form.chartType = opt.value"
              :style="`border:2px solid ${form.chartType === opt.value ? typeColor(opt.value) : '#e0e0e0'};border-radius:8px;padding:10px 6px;text-align:center;cursor:pointer;background:${form.chartType === opt.value ? typeBg(opt.value) : '#fff'};transition:all .2s`">
              <el-icon :style="`font-size:22px;color:${typeColor(opt.value)}`">
                <component :is="opt.icon" />
              </el-icon>
              <div style="font-size:12px;margin-top:4px;color:#555">{{ opt.label }}</div>
            </div>
          </div>
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
import { Rank, Plus, Edit, Delete, ArrowLeft, DataLine, PieChart, TrendCharts, Odometer } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import { getTemplates } from '../api/templates'

const STORAGE_KEY = 'dashboard_config'

const templateList = ref([])
const widgets = ref([])
const dialogVisible = ref(false)
const editIndex = ref(-1)
const form = ref({ title: '', templateId: null, fieldName: '', chartType: 'bar' })

const chartTypeOptions = [
  { value: 'bar', label: '柱状图', icon: DataLine },
  { value: 'pie', label: '饼图', icon: PieChart },
  { value: 'line', label: '折线图', icon: TrendCharts },
  { value: 'stat', label: '数值统计', icon: Odometer },
]

const currentFields = computed(() => {
  const tpl = templateList.value.find(t => t.id === form.value.templateId)
  return tpl ? tpl.meta_data : []
})

function typeColor(type) {
  return { bar: '#5470c6', pie: '#ee6666', line: '#91cc75', stat: '#9a60b4' }[type] || '#999'
}

function typeBg(type) {
  return { bar: '#f0f4ff', pie: '#fff0f0', line: '#f0fff4', stat: '#fdf0ff' }[type] || '#f5f5f5'
}

function chartTypeLabel(t) {
  return { bar: '柱状图', pie: '饼图', line: '折线图', stat: '数值统计' }[t] || t
}

onMounted(async () => {
  const res = await getTemplates({ page: 1, page_size: 100 })
  templateList.value = res.data.list
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) widgets.value = JSON.parse(saved)
})

function save() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(widgets.value))
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
