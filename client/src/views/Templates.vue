<template>
  <el-card>
    <div style="display:flex;justify-content:space-between;margin-bottom:16px">
      <el-input v-model="keyword" placeholder="搜索模板名称" style="width:200px" clearable @clear="loadData" @keyup.enter="loadData" />
      <el-button v-if="user?.role === 'admin'" type="primary" @click="showDialog()">新增模板</el-button>
    </div>
    <el-table :data="list" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="模板名称" />
      <el-table-column prop="remark" label="备注" />
      <el-table-column prop="create_time" label="创建时间" />
      <el-table-column prop="update_time" label="更新时间" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="showDetail(row)">查看</el-button>
          <template v-if="user?.role === 'admin'">
            <el-button size="small" @click="showDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:16px;justify-content:flex-end" v-model:current-page="page" v-model:page-size="pageSize" :total="total" :page-sizes="[10,20,50]" layout="total,sizes,prev,pager,next" @change="loadData" />

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingTpl ? '编辑模板' : '新增模板'" width="700px" draggable :close-on-click-modal="false" style="max-height:90vh" :body-style="{overflowY:'auto',maxHeight:'70vh'}">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" />
        </el-form-item>
        <el-form-item label="字段配置" prop="meta_data">
          <FieldEditor v-model="form.meta_data" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情对话框 -->
    <el-dialog v-model="detailVisible" title="模板详情" width="600px">
      <el-descriptions :column="1" border v-if="detailTpl">
        <el-descriptions-item label="名称">{{ detailTpl.name }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ detailTpl.remark || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detailTpl.create_time }}</el-descriptions-item>
      </el-descriptions>
      <h4 style="margin:16px 0 8px">字段列表</h4>
      <el-table :data="detailTpl?.meta_data || []" border size="small">
        <el-table-column prop="name" label="字段名" />
        <el-table-column prop="label" label="显示名" />
        <el-table-column prop="type" label="类型" />
        <el-table-column prop="required" label="必填">
          <template #default="{ row }">{{ row.required ? '是' : '否' }}</template>
        </el-table-column>
        <el-table-column prop="options" label="选项">
          <template #default="{ row }">{{ row.options?.join(', ') || '-' }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTemplates, createTemplate, updateTemplate, deleteTemplate } from '../api/templates'
import { getUserInfo } from '../utils/storage'
import FieldEditor from '../components/FieldEditor.vue'

const user = computed(() => getUserInfo())
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const loading = ref(false)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const detailTpl = ref(null)
const editingTpl = ref(null)
const submitting = ref(false)
const formRef = ref()
const form = ref({ name: '', remark: '', meta_data: [] })

const formRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  meta_data: [{ validator: (r, v, cb) => v && v.length ? cb() : cb(new Error('请至少添加一个字段')), trigger: 'change' }]
}

onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    const res = await getTemplates({ page: page.value, page_size: pageSize.value, keyword: keyword.value })
    list.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function showDialog(row) {
  editingTpl.value = row || null
  form.value = row ? { name: row.name, remark: row.remark || '', meta_data: JSON.parse(JSON.stringify(row.meta_data)) } : { name: '', remark: '', meta_data: [] }
  dialogVisible.value = true
}

function showDetail(row) {
  detailTpl.value = row
  detailVisible.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    if (editingTpl.value) {
      await updateTemplate(editingTpl.value.id, form.value)
    } else {
      await createTemplate(form.value)
    }
    ElMessage.success(editingTpl.value ? '更新成功' : '创建成功')
    dialogVisible.value = false
    loadData()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定删除该模板？', '提示', { type: 'warning' })
  await deleteTemplate(row.id)
  ElMessage.success('删除成功')
  loadData()
}
</script>
