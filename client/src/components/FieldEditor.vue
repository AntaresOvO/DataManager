<template>
  <div style="overflow-x:auto">
    <div v-for="(field, index) in fields" :key="index" style="display:flex;gap:8px;margin-bottom:8px;align-items:center;min-width:max-content">
      <el-input v-model="field.name" placeholder="字段名(英文)" style="width:120px" />
      <el-input v-model="field.label" placeholder="显示名称" style="width:120px" />
      <el-select v-model="field.type" placeholder="类型" style="width:120px" :teleported="true" @change="onTypeChange(field)">
        <el-option label="文本" value="text" />
        <el-option label="数字" value="number" />
        <el-option label="日期" value="date" />
        <el-option label="单选" value="radio" />
        <el-option label="多选" value="checkbox" />
      </el-select>
      <el-input v-if="['radio','checkbox'].includes(field.type)" v-model="field.optionsStr" placeholder="选项(逗号分隔)" style="width:180px" />
      <el-checkbox v-model="field.required">必填</el-checkbox>
      <el-button type="danger" :icon="Delete" circle size="small" @click="removeField(index)" />
    </div>
    <el-button type="primary" plain @click="addField">+ 添加字段</el-button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Delete } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:modelValue'])

const fields = ref([])

watch(() => props.modelValue, (val) => {
  if (val && val.length) {
    fields.value = val.map(f => ({
      ...f,
      optionsStr: f.options ? f.options.join(',') : ''
    }))
  } else {
    fields.value = []
  }
}, { immediate: true })

watch(fields, () => {
  emit('update:modelValue', fields.value.map(f => {
    const item = { name: f.name, label: f.label, type: f.type, required: !!f.required }
    if (['radio', 'checkbox'].includes(f.type)) {
      item.options = (f.optionsStr || '').split(',').map(s => s.trim()).filter(Boolean)
    }
    return item
  }))
}, { deep: true })

function addField() {
  fields.value.push({ name: '', label: '', type: 'text', required: false, optionsStr: '' })
}

function removeField(index) {
  fields.value.splice(index, 1)
}

function onTypeChange(field) {
  if (!['radio', 'checkbox'].includes(field.type)) {
    field.optionsStr = ''
  }
}
</script>
