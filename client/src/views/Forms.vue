<template>
  <el-card>
    <div style="display:flex;justify-content:space-between;margin-bottom:16px">
      <el-select v-model="templateId" placeholder="选择模板" clearable style="width:200px" @change="loadData">
        <el-option v-for="t in templateList" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>
      <el-button type="primary" @click="showDialog()">填写表单</el-button>
    </div>
    <el-table :data="list" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="template_name" label="所属模板" />
      <el-table-column prop="username" label="提交人" />
      <el-table-column prop="create_time" label="创建时间" />
      <el-table-column prop="update_time" label="更新时间" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="showDetail(row)">查看</el-button>
          <el-button size="small" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:16px;justify-content:flex-end" v-model:current-page="page" v-model:page-size="pageSize" :total="total" :page-sizes="[10,20,50]" layout="total,sizes,prev,pager,next" @change="loadData" />

    <!-- 填写/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingForm ? '编辑表单' : '填写表单'" width="600px">
      <el-form-item v-if="!editingForm" label="选择模板" label-width="80px" style="margin-bottom:16px">
        <el-select v-model="selectedTplId" placeholder="请选择模板" style="width:100%" @change="onTplSelect">
          <el-option v-for="t in templateList" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
      </el-form-item>
      <DynamicForm v-if="currentMeta.length" ref="dynamicFormRef" :meta-data="currentMeta" :data="editingForm?.data || {}" />
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情 -->
    <el-dialog v-model="detailVisible" title="表单详情" width="600px">
      <template v-if="detailData">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="所属模板">{{ detailData.template_name }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ detailData.create_time }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:16px 0 8px">表单数据</h4>
        <el-descriptions :column="1" border>
          <el-descriptions-item v-for="(val, key) in detailData.data" :key="key" :label="getFieldLabel(key)">
            {{ Array.isArray(val) ? val.join(', ') : val }}
          </el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getForms, createForm, updateForm, deleteForm, getForm } from '../api/forms'
import { getTemplates, getTemplate } from '../api/templates'
import DynamicForm from '../components/DynamicForm.vue'

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const templateId = ref(null)
const templateList = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const detailData = ref(null)
const editingForm = ref(null)
const submitting = ref(false)
const dynamicFormRef = ref()
const selectedTplId = ref(null)
const currentMeta = ref([])

onMounted(async () => {
  const res = await getTemplates({ page: 1, page_size: 100 })
  templateList.value = res.data.list
  loadData()
})

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (templateId.value) params.template_id = templateId.value
    const res = await getForms(params)
    list.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function showDialog(row) {
  editingForm.value = row || null
  selectedTplId.value = null
  currentMeta.value = []
  if (row) {
    const res = await getForm(row.id)
    editingForm.value = res.data
    if (res.data.template_meta) {
      currentMeta.value = res.data.template_meta
    }
  }
  dialogVisible.value = true
}

async function onTplSelect(id) {
  if (!id) { currentMeta.value = []; return }
  const res = await getTemplate(id)
  currentMeta.value = res.data.meta_data
}

async function handleSubmit() {
  if (!currentMeta.value.length) return ElMessage.warning('请先选择模板')
  const data = await dynamicFormRef.value.validate()
  submitting.value = true
  try {
    if (editingForm.value) {
      await updateForm(editingForm.value.id, { data })
    } else {
      await createForm({ template_id: selectedTplId.value, data })
    }
    ElMessage.success(editingForm.value ? '更新成功' : '提交成功')
    dialogVisible.value = false
    loadData()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定删除该数据？', '提示', { type: 'warning' })
  await deleteForm(row.id)
  ElMessage.success('删除成功')
  loadData()
}

async function showDetail(row) {
  const res = await getForm(row.id)
  detailData.value = res.data
  detailVisible.value = true
}

function getFieldLabel(key) {
  if (!detailData.value?.template_meta) return key
  const field = detailData.value.template_meta.find(f => f.name === key)
  return field?.label || key
}
</script>
