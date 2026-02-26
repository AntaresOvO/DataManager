<template>
  <el-form :model="formData" :ref="el => formRef = el" label-width="120px">
    <el-form-item
      v-for="field in fields"
      :key="field.name"
      :label="field.label"
      :prop="field.name"
      :rules="field.required ? [{ required: true, message: `请填写${field.label}`, trigger: 'blur' }] : []"
    >
      <el-input v-if="field.type === 'text'" v-model="formData[field.name]" />
      <el-input-number v-else-if="field.type === 'number'" v-model="formData[field.name]" />
      <el-date-picker v-else-if="field.type === 'date'" v-model="formData[field.name]" type="date" value-format="YYYY-MM-DD" />
      <el-radio-group v-else-if="field.type === 'radio'" v-model="formData[field.name]">
        <el-radio v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</el-radio>
      </el-radio-group>
      <el-checkbox-group v-else-if="field.type === 'checkbox'" v-model="formData[field.name]">
        <el-checkbox v-for="opt in field.options" :key="opt" :value="opt" :label="opt" />
      </el-checkbox-group>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  metaData: { type: Array, default: () => [] },
  data: { type: Object, default: () => ({}) }
})

const formRef = ref()
const formData = ref({})
const fields = ref([])

watch(() => props.metaData, (val) => {
  fields.value = val || []
  initFormData()
}, { immediate: true })

watch(() => props.data, () => initFormData(), { immediate: true })

function initFormData() {
  const d = {}
  for (const f of fields.value) {
    d[f.name] = props.data?.[f.name] ?? (f.type === 'checkbox' ? [] : f.type === 'number' ? 0 : '')
  }
  formData.value = d
}

async function validate() {
  await formRef.value.validate()
  return { ...formData.value }
}

defineExpose({ validate })
</script>
