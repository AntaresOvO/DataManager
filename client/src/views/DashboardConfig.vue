<template>
  <el-card style="border-radius:12px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <div>
        <span style="font-size:18px;font-weight:600;color:#1a1a2e">仪表盘配置</span>
        <span style="font-size:13px;color:#999;margin-left:10px">拖拽卡片调整顺序</span>
      </div>
      <div style="display:flex;gap:8px">
        <el-button @click="$router.push('/')"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <el-button @click="loadSample" :loading="sampleLoading">加载示例</el-button>
        <el-button type="primary" @click="openAdd"><el-icon><Plus /></el-icon> 添加图表</el-button>
      </div>
    </div>

    <el-empty v-if="!widgets.length" description="暂无图表，点击右上角添加">
      <el-button type="primary" @click="openAdd">立即添加</el-button>
    </el-empty>

    <draggable v-else v-model="widgets" item-key="id" handle=".drag-handle"
      style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px" @end="save">
      <template #item="{ element, index }">
        <el-card shadow="hover" style="border-radius:10px;overflow:hidden" body-style="padding:0">
          <div :style="`height:4px;background:${typeColor(element.chartType)}`" />
          <div style="padding:14px 16px">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <div style="display:flex;align-items:center;gap:8px">
                <el-icon class="drag-handle" style="cursor:move;color:#ccc"><Rank /></el-icon>
                <span style="font-weight:600;font-size:14px">{{ element.title }}</span>
              </div>
              <div style="display:flex;gap:2px">
                <el-button size="small" link @click="openEdit(index)"><el-icon><Edit /></el-icon></el-button>
                <el-button size="small" link type="danger" @click="remove(index)"><el-icon><Delete /></el-icon></el-button>
              </div>
            </div>
            <div style="margin-top:10px;display:flex;gap:6px;flex-wrap:wrap">
              <el-tag size="small" type="info">{{ element.templateName }}</el-tag>
              <el-tag size="small" :color="typeBg(element.chartType)" style="border:none" :style="`color:${typeColor(element.chartType)}`">
                {{ chartTypeLabel(element.chartType) }}
              </el-tag>
              <el-tag size="small" type="success">{{ sizeLabel(element.size) }}</el-tag>
              <el-tag size="small" v-if="element.extraFields?.length">多字段 ×{{ element.extraFields.length + 1 }}</el-tag>
              <el-tag size="small" v-if="element.dateField">{{ dateGroupLabel(element.dateGroupBy) }}</el-tag>
            </div>
          </div>
        </el-card>
      </template>
    </draggable>

    <!-- 配置弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editIndex >= 0 ? '编辑图表' : '添加图表'" width="580px" draggable>
      <el-tabs v-model="activeTab">

        <!-- Tab1: 基础 -->
        <el-tab-pane label="基础" name="basic">
          <el-form :model="form" label-width="80px" style="margin-top:8px">
            <el-form-item label="标题">
              <el-input v-model="form.title" placeholder="图表标题" />
            </el-form-item>
            <el-form-item label="数据模板">
              <el-select v-model="form.templateId" placeholder="选择模板" style="width:100%" @change="onTemplateChange">
                <el-option v-for="t in templateList" :key="t.id" :label="t.name" :value="t.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="图表类型">
              <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px">
                <div v-for="opt in chartTypeOptions" :key="opt.value" @click="form.chartType = opt.value"
                  :style="`border:2px solid ${form.chartType===opt.value ? typeColor(opt.value) : '#e0e0e0'};border-radius:8px;padding:10px 4px;text-align:center;cursor:pointer;background:${form.chartType===opt.value ? typeBg(opt.value) : '#fff'};transition:all .2s`">
                  <el-icon :style="`font-size:20px;color:${typeColor(opt.value)}`"><component :is="opt.icon" /></el-icon>
                  <div style="font-size:11px;margin-top:4px;color:#555">{{ opt.label }}</div>
                </div>
              </div>
            </el-form-item>
            <el-form-item label="卡片尺寸">
              <el-radio-group v-model="form.size">
                <el-radio-button value="quarter">1/4 宽</el-radio-button>
                <el-radio-button value="half">1/2 宽</el-radio-button>
                <el-radio-button value="full">全宽</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Tab2: 数据 -->
        <el-tab-pane label="数据" name="data">
          <el-form :model="form" label-width="88px" style="margin-top:8px">

            <!-- scatter 专属 -->
            <template v-if="form.chartType === 'scatter'">
              <el-form-item label="X 轴字段">
                <el-select v-model="form.xField" placeholder="选择数值字段" style="width:100%" :disabled="!form.templateId" @change="f => { form.xFieldLabel = fieldLabel(f) }">
                  <el-option v-for="f in numericFields" :key="f.name" :label="f.label" :value="f.name" />
                </el-select>
              </el-form-item>
              <el-form-item label="Y 轴字段">
                <el-select v-model="form.yField" placeholder="选择数值字段" style="width:100%" :disabled="!form.templateId" @change="f => { form.yFieldLabel = fieldLabel(f) }">
                  <el-option v-for="f in numericFields" :key="f.name" :label="f.label" :value="f.name" />
                </el-select>
              </el-form-item>
            </template>

            <!-- table 专属 -->
            <template v-else-if="form.chartType === 'table'">
              <el-form-item label="显示字段">
                <el-select v-model="tableFieldNames" multiple placeholder="选择要显示的列" style="width:100%" :disabled="!form.templateId" @change="onTableFieldsChange">
                  <el-option v-for="f in currentFields" :key="f.name" :label="f.label" :value="f.name" />
                </el-select>
              </el-form-item>
              <el-form-item label="显示条数">
                <el-input-number v-model="form.topN" :min="1" :max="100" style="width:120px" />
              </el-form-item>
            </template>

            <!-- gauge 专属 -->
            <template v-else-if="form.chartType === 'gauge'">
              <el-form-item label="统计字段">
                <el-select v-model="form.fieldName" placeholder="选择字段" style="width:100%" :disabled="!form.templateId" @change="onFieldChange">
                  <el-option label="（记录总数）" value="__count__" />
                  <el-option v-for="f in currentFields" :key="f.name" :label="f.label" :value="f.name" />
                </el-select>
              </el-form-item>
              <el-form-item label="聚合方式">
                <el-select v-model="form.aggregation" style="width:100%">
                  <el-option v-for="a in aggOptions" :key="a.value" :label="a.label" :value="a.value" />
                </el-select>
              </el-form-item>
              <el-form-item label="最大值">
                <el-input-number v-model="form.gaugeMax" :min="1" style="width:160px" />
              </el-form-item>
            </template>

            <!-- 通用字段配置 -->
            <template v-else>
              <el-form-item label="主字段">
                <el-select v-model="form.fieldName" placeholder="选择统计字段" style="width:100%" :disabled="!form.templateId" @change="onFieldChange">
                  <el-option label="（记录总数）" value="__count__" />
                  <el-option v-for="f in currentFields" :key="f.name" :label="f.label" :value="f.name" />
                </el-select>
              </el-form-item>
              <el-form-item label="聚合方式" v-if="form.chartType !== 'pie' && form.chartType !== 'funnel'">
                <el-select v-model="form.aggregation" style="width:100%">
                  <el-option v-for="a in aggOptions" :key="a.value" :label="a.label" :value="a.value" />
                </el-select>
              </el-form-item>

              <!-- 多字段（bar/line 专属） -->
              <template v-if="form.chartType === 'bar' || form.chartType === 'line'">
                <el-form-item label="附加字段">
                  <div style="width:100%">
                    <div v-for="(ef, i) in form.extraFields" :key="i"
                      style="display:flex;gap:8px;margin-bottom:8px;align-items:center">
                      <el-select v-model="ef.name" placeholder="字段" style="flex:1" @change="n => { ef.label = fieldLabel(n); ef.type = fieldType(n) }">
                        <el-option v-for="f in currentFields" :key="f.name" :label="f.label" :value="f.name" />
                      </el-select>
                      <el-select v-model="ef.aggregation" style="width:100px">
                        <el-option v-for="a in aggOptions" :key="a.value" :label="a.label" :value="a.value" />
                      </el-select>
                      <el-button size="small" link type="danger" @click="form.extraFields.splice(i,1)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                    <el-button size="small" @click="form.extraFields.push({name:'',label:'',type:'',aggregation:'count'})" :disabled="!form.templateId">
                      <el-icon><Plus /></el-icon> 添加字段
                    </el-button>
                  </div>
                </el-form-item>
              </template>

              <!-- 日期分组 -->
              <el-form-item label="日期字段">
                <el-select v-model="form.dateField" placeholder="按日期分组（可选）" style="width:100%" clearable :disabled="!form.templateId">
                  <el-option v-for="f in dateFields" :key="f.name" :label="f.label" :value="f.name" />
                </el-select>
              </el-form-item>
              <el-form-item label="分组粒度" v-if="form.dateField">
                <el-radio-group v-model="form.dateGroupBy">
                  <el-radio-button value="day">按天</el-radio-button>
                  <el-radio-button value="week">按周</el-radio-button>
                  <el-radio-button value="month">按月</el-radio-button>
                  <el-radio-button value="year">按年</el-radio-button>
                </el-radio-group>
              </el-form-item>
            </template>

          </el-form>
        </el-tab-pane>

        <!-- Tab3: 外观 -->
        <el-tab-pane label="外观" name="visual">
          <el-form :model="form" label-width="88px" style="margin-top:8px">
            <el-form-item label="颜色主题" v-if="form.chartType === 'stat'">
              <div style="display:flex;gap:8px;flex-wrap:wrap">
                <div v-for="(g, i) in statGradients" :key="i" @click="form.colorTheme = i"
                  :style="`width:48px;height:32px;border-radius:6px;background:${g};cursor:pointer;border:3px solid ${form.colorTheme===i ? '#333' : 'transparent'};transition:all .2s`" />
              </div>
            </el-form-item>
            <el-form-item label="显示趋势" v-if="form.chartType === 'stat'">
              <el-switch v-model="form.showTrend" active-text="开启（需配合日期筛选）" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

      </el-tabs>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button @click="activeTab = activeTab === 'basic' ? 'data' : activeTab === 'data' ? 'visual' : 'basic'">
          {{ activeTab === 'visual' ? '返回基础' : '下一步' }}
        </el-button>
        <el-button type="primary" @click="confirmSave">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Rank, Plus, Edit, Delete, ArrowLeft, DataLine, PieChart, TrendCharts, Odometer, Grid, Histogram, ScaleToOriginal, DataAnalysis } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import { getTemplates } from '../api/templates'

const STORAGE_KEY = 'dashboard_config'
const statGradients = [
  'linear-gradient(135deg,#667eea,#764ba2)',
  'linear-gradient(135deg,#4facfe,#00f2fe)',
  'linear-gradient(135deg,#43e97b,#38f9d7)',
  'linear-gradient(135deg,#fa709a,#fee140)',
  'linear-gradient(135deg,#f093fb,#f5576c)',
  'linear-gradient(135deg,#a18cd1,#fbc2eb)',
  'linear-gradient(135deg,#ffecd2,#fcb69f)',
  'linear-gradient(135deg,#a1c4fd,#c2e9fb)',
]

const chartTypeOptions = [
  { value: 'bar',     label: '柱状图',   icon: DataLine },
  { value: 'line',    label: '折线图',   icon: TrendCharts },
  { value: 'pie',     label: '饼图',     icon: PieChart },
  { value: 'stat',    label: '数值卡片', icon: Odometer },
  { value: 'gauge',   label: '仪表盘',   icon: ScaleToOriginal },
  { value: 'funnel',  label: '漏斗图',   icon: Histogram },
  { value: 'table',   label: '数据表格', icon: Grid },
  { value: 'scatter', label: '散点图',   icon: DataAnalysis },
]

const aggOptions = [
  { value: 'count', label: '计数' },
  { value: 'sum',   label: '求和' },
  { value: 'avg',   label: '平均值' },
  { value: 'max',   label: '最大值' },
  { value: 'min',   label: '最小值' },
]

const templateList = ref([])
const widgets = ref([])
const dialogVisible = ref(false)
const editIndex = ref(-1)
const activeTab = ref('basic')
const tableFieldNames = ref([])
const sampleLoading = ref(false)

const defaultForm = () => ({
  title: '', templateId: null, size: 'half', chartType: 'bar',
  fieldName: '', fieldLabel: '', fieldType: '', aggregation: 'count',
  extraFields: [],
  dateField: '', dateGroupBy: 'month',
  xField: '', xFieldLabel: '', yField: '', yFieldLabel: '',
  tableFields: [], topN: 10,
  gaugeMax: 100,
  colorTheme: 0, showTrend: false,
})

const form = ref(defaultForm())

const currentFields = computed(() => {
  const tpl = templateList.value.find(t => t.id === form.value.templateId)
  return tpl ? tpl.meta_data : []
})

const numericFields = computed(() => currentFields.value.filter(f => f.type === 'number'))
const dateFields = computed(() => currentFields.value.filter(f => f.type === 'date' || f.type === 'datetime'))

function fieldLabel(name) {
  return currentFields.value.find(f => f.name === name)?.label || name
}
function fieldType(name) {
  return currentFields.value.find(f => f.name === name)?.type || 'text'
}

function typeColor(type) {
  return { bar: '#5470c6', pie: '#ee6666', line: '#91cc75', stat: '#9a60b4', gauge: '#73c0de', funnel: '#fac858', table: '#909399', scatter: '#3ba272' }[type] || '#999'
}
function typeBg(type) {
  return { bar: '#f0f4ff', pie: '#fff0f0', line: '#f0fff4', stat: '#fdf0ff', gauge: '#f0faff', funnel: '#fffbf0', table: '#f5f5f5', scatter: '#f0fff8' }[type] || '#f5f5f5'
}
function chartTypeLabel(t) {
  return chartTypeOptions.find(o => o.value === t)?.label || t
}
function sizeLabel(s) {
  return { quarter: '1/4宽', half: '1/2宽', full: '全宽' }[s] || '1/2宽'
}
function dateGroupLabel(g) {
  return { day: '按天', week: '按周', month: '按月', year: '按年' }[g] || '按月'
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
  form.value = defaultForm()
  tableFieldNames.value = []
  activeTab.value = 'basic'
  dialogVisible.value = true
}

function openEdit(idx) {
  editIndex.value = idx
  form.value = { ...defaultForm(), ...JSON.parse(JSON.stringify(widgets.value[idx])) }
  tableFieldNames.value = (form.value.tableFields || []).map(f => f.name)
  activeTab.value = 'basic'
  dialogVisible.value = true
}

function remove(idx) {
  widgets.value.splice(idx, 1)
  save()
}

function onTemplateChange() {
  form.value.fieldName = ''
  form.value.extraFields = []
  form.value.tableFields = []
  tableFieldNames.value = []
  const tpl = templateList.value.find(t => t.id === form.value.templateId)
  if (tpl && !form.value.title) form.value.title = tpl.name
}

function onFieldChange(name) {
  const f = currentFields.value.find(f => f.name === name)
  form.value.fieldLabel = f?.label || name
  form.value.fieldType = f?.type || 'text'
  if (!form.value.title && f) form.value.title = f.label
}

function onTableFieldsChange(names) {
  form.value.tableFields = names.map(n => ({ name: n, label: fieldLabel(n) }))
}

async function loadSample() {
  sampleLoading.value = true
  try {
    const res = await getTemplates({ page: 1, page_size: 100 })
    const tpls = res.data.list
    const emp = tpls.find(t => t.name === '员工信息表')
    const fb  = tpls.find(t => t.name === '产品反馈表')
    const samples = []

    if (emp) {
      samples.push(
        { id:'s1',  title:'员工总数',           templateId:emp.id, templateName:emp.name, size:'quarter', chartType:'stat',   fieldName:'__count__', fieldLabel:'记录总数', aggregation:'count', colorTheme:0, showTrend:true,  extraFields:[], dateField:'', dateGroupBy:'month' },
        { id:'s2',  title:'平均年龄',           templateId:emp.id, templateName:emp.name, size:'quarter', chartType:'stat',   fieldName:'age',       fieldLabel:'年龄',    aggregation:'avg',   colorTheme:1, showTrend:false, extraFields:[], dateField:'', dateGroupBy:'month' },
        { id:'s3',  title:'性别比例',           templateId:emp.id, templateName:emp.name, size:'quarter', chartType:'pie',    fieldName:'gender',    fieldLabel:'性别',    aggregation:'count', colorTheme:0, showTrend:false, extraFields:[], dateField:'', dateGroupBy:'month' },
        { id:'s4',  title:'部门人数分布',       templateId:emp.id, templateName:emp.name, size:'half',    chartType:'bar',    fieldName:'department',fieldLabel:'部门',    aggregation:'count', colorTheme:0, showTrend:false, extraFields:[], dateField:'', dateGroupBy:'month' },
        { id:'s5',  title:'技能分布',           templateId:emp.id, templateName:emp.name, size:'half',    chartType:'bar',    fieldName:'skills',    fieldLabel:'技能',    aggregation:'count', colorTheme:0, showTrend:false, extraFields:[], dateField:'', dateGroupBy:'month' },
        { id:'s6',  title:'入职趋势（按月）',   templateId:emp.id, templateName:emp.name, size:'full',    chartType:'line',   fieldName:'__count__', fieldLabel:'入职人数',aggregation:'count', colorTheme:0, showTrend:false, extraFields:[], dateField:'entry_date', dateGroupBy:'month' },
        { id:'s7',  title:'各部门平均年龄',     templateId:emp.id, templateName:emp.name, size:'half',    chartType:'bar',    fieldName:'department',fieldLabel:'部门',    aggregation:'count', colorTheme:0, showTrend:false,
          extraFields:[{ name:'age', label:'平均年龄', type:'number', aggregation:'avg' }], dateField:'', dateGroupBy:'month' },
      )
    }

    if (fb) {
      samples.push(
        { id:'s8',  title:'反馈总数',           templateId:fb.id, templateName:fb.name, size:'quarter', chartType:'stat',   fieldName:'__count__', fieldLabel:'记录总数', aggregation:'count', colorTheme:2, showTrend:false, extraFields:[], dateField:'', dateGroupBy:'month' },
        { id:'s9',  title:'平均评分',           templateId:fb.id, templateName:fb.name, size:'quarter', chartType:'gauge',  fieldName:'rating',    fieldLabel:'评分',    aggregation:'avg',   gaugeMax:10,  colorTheme:0, showTrend:false, extraFields:[], dateField:'', dateGroupBy:'month' },
        { id:'s10', title:'各产品反馈量',       templateId:fb.id, templateName:fb.name, size:'half',    chartType:'bar',    fieldName:'product',   fieldLabel:'产品名称',aggregation:'count', colorTheme:0, showTrend:false, extraFields:[], dateField:'', dateGroupBy:'month' },
        { id:'s11', title:'问题分布',           templateId:fb.id, templateName:fb.name, size:'half',    chartType:'pie',    fieldName:'issues',    fieldLabel:'遇到的问题',aggregation:'count',colorTheme:0, showTrend:false, extraFields:[], dateField:'', dateGroupBy:'month' },
        { id:'s12', title:'问题严重程度漏斗',   templateId:fb.id, templateName:fb.name, size:'half',    chartType:'funnel', fieldName:'issues',    fieldLabel:'遇到的问题',aggregation:'count',colorTheme:0, showTrend:false, extraFields:[], dateField:'', dateGroupBy:'month' },
        { id:'s13', title:'各产品评分 vs 使用时长', templateId:fb.id, templateName:fb.name, size:'full', chartType:'bar',  fieldName:'product',   fieldLabel:'产品名称',aggregation:'count', colorTheme:0, showTrend:false,
          extraFields:[{ name:'rating', label:'平均评分', type:'number', aggregation:'avg' }, { name:'usage_time', label:'平均使用时长(月)', type:'number', aggregation:'avg' }], dateField:'', dateGroupBy:'month' },
        { id:'s14', title:'最新反馈记录',       templateId:fb.id, templateName:fb.name, size:'half',    chartType:'table',  fieldName:'product',   fieldLabel:'产品名称',aggregation:'count', colorTheme:0, showTrend:false, extraFields:[], dateField:'', dateGroupBy:'month',
          tableFields:[{ name:'product', label:'产品名称' }, { name:'rating', label:'评分' }, { name:'usage_time', label:'使用时长(月)' }, { name:'issues', label:'问题' }, { name:'suggestion', label:'改进建议' }], topN:10 },
      )
    }

    if (!samples.length) return ElMessage.warning('未找到示例模板，请先运行 seed_data.py')
    widgets.value = samples
    save()
    ElMessage.success(`已加载 ${samples.length} 个示例图表`)
  } catch {
    // 错误已由 request 拦截器统一处理（ElMessage.error）
  } finally {
    sampleLoading.value = false
  }
}

function confirmSave() {
  if (!form.value.title) return ElMessage.warning('请填写标题')
  if (!form.value.templateId) return ElMessage.warning('请选择模板')

  const tpl = templateList.value.find(t => t.id === form.value.templateId)
  const widget = {
    id: editIndex.value >= 0 ? widgets.value[editIndex.value].id : Date.now().toString(),
    ...form.value,
    templateName: tpl?.name || '',
    extraFields: form.value.extraFields.filter(f => f.name),
  }

  if (editIndex.value >= 0) {
    widgets.value[editIndex.value] = widget
  } else {
    widgets.value.push(widget)
  }
  save()
  dialogVisible.value = false
  ElMessage.success('保存成功')
}
</script>
