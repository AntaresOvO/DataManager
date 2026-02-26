<template>
  <el-card>
    <h3>个人中心</h3>
    <el-descriptions :column="1" border style="margin-bottom:20px">
      <el-descriptions-item label="用户名">{{ userInfo?.username }}</el-descriptions-item>
      <el-descriptions-item label="角色">{{ userInfo?.role === 'admin' ? '管理员' : '普通用户' }}</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ userInfo?.create_time }}</el-descriptions-item>
      <el-descriptions-item label="最后登录">{{ userInfo?.last_login_time || '-' }}</el-descriptions-item>
    </el-descriptions>
    <el-divider />
    <h4>修改密码</h4>
    <el-form :model="form" :rules="rules" ref="formRef" label-width="80px" style="max-width:400px">
      <el-form-item label="旧密码" prop="old_password">
        <el-input v-model="form.old_password" type="password" show-password />
      </el-form-item>
      <el-form-item label="新密码" prop="new_password">
        <el-input v-model="form.new_password" type="password" show-password />
      </el-form-item>
      <el-form-item label="确认密码" prop="confirm">
        <el-input v-model="form.confirm" type="password" show-password />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="handleSubmit">确认修改</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getUserInfo as fetchUserInfo, changePassword } from '../api/auth'
import { setUserInfo, getUserInfo, removeToken, removeUserInfo } from '../utils/storage'
import { useRouter } from 'vue-router'

const router = useRouter()
const userInfo = ref(null)
const formRef = ref()
const loading = ref(false)
const form = ref({ old_password: '', new_password: '', confirm: '' })

const rules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [{ required: true, message: '请输入新密码', trigger: 'blur' }, { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }],
  confirm: [{
    validator: (rule, value, callback) => {
      if (value !== form.value.new_password) callback(new Error('两次密码不一致'))
      else callback()
    }, trigger: 'blur'
  }]
}

onMounted(async () => {
  const res = await fetchUserInfo()
  userInfo.value = res.data
})

async function handleSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    await changePassword({ old_password: form.value.old_password, new_password: form.value.new_password })
    ElMessage.success('密码修改成功，请重新登录')
    const user = getUserInfo()
    if (user?.need_change_pwd) {
      user.need_change_pwd = 0
      setUserInfo(user)
    }
    removeToken()
    removeUserInfo()
    router.push('/login')
  } finally {
    loading.value = false
  }
}
</script>
