<template>
  <main class="yh-auth-page" :data-mcr-theme="isDark ? 'dark' : 'light'">
    <section class="yh-auth-card" aria-labelledby="yh-auth-title">
      <div class="yh-auth-mark" aria-hidden="true">
        <v-icon icon="mdi-image-filter-hdr-outline" size="28" />
      </div>
      <p class="yh-auth-eyebrow">YAHAHA COVER STUDIO</p>
      <h1 id="yh-auth-title">{{ setup ? '设置管理员账号' : '欢迎回来' }}</h1>
      <p class="yh-auth-copy">
        {{ setup ? '创建一个本机管理员账号，保护配置和生成接口。' : '登录后继续管理封面与媒体库。' }}
      </p>

      <form class="yh-auth-form" @submit.prevent="submit">
        <label>
          <span>用户名</span>
          <input v-model.trim="username" autocomplete="username" minlength="2" maxlength="32" required autofocus>
        </label>
        <label>
          <span>密码</span>
          <div class="yh-auth-password">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              :autocomplete="setup ? 'new-password' : 'current-password'"
              minlength="8"
              required
            >
            <button type="button" :aria-label="showPassword ? '隐藏密码' : '显示密码'" @click="showPassword = !showPassword">
              <v-icon :icon="showPassword ? 'mdi-eye-off-outline' : 'mdi-eye-outline'" size="20" />
            </button>
          </div>
        </label>
        <label v-if="setup">
          <span>确认密码</span>
          <input v-model="confirmation" type="password" autocomplete="new-password" minlength="8" required>
        </label>
        <p v-if="error" class="yh-auth-error" role="alert">{{ error }}</p>
        <button class="yh-auth-submit" type="submit" :disabled="submitting">
          <v-progress-circular v-if="submitting" indeterminate size="18" width="2" />
          <span>{{ setup ? '完成设置' : '登录' }}</span>
        </button>
      </form>
      <p class="yh-auth-footnote">登录状态会安全保存在当前浏览器。</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { loginDocker, setupDockerAuth } from '../dockerApi'

const props = defineProps<{ mode: 'setup' | 'login' }>()
const emit = defineEmits<{ (event: 'authenticated', username: string): void }>()
const setup = computed(() => props.mode === 'setup')
const username = ref('')
const password = ref('')
const confirmation = ref('')
const showPassword = ref(false)
const submitting = ref(false)
const error = ref('')
const isDark = ref(false)
let themeQuery: MediaQueryList | null = null

function syncTheme(event?: MediaQueryListEvent) {
  isDark.value = event?.matches ?? themeQuery?.matches ?? false
}

async function submit() {
  error.value = ''
  if (setup.value && password.value !== confirmation.value) {
    error.value = '两次输入的密码不一致'
    return
  }
  submitting.value = true
  try {
    const session = setup.value
      ? await setupDockerAuth(username.value, password.value)
      : await loginDocker(username.value, password.value)
    emit('authenticated', session.username)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '登录失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  themeQuery = window.matchMedia('(prefers-color-scheme: dark)')
  syncTheme()
  themeQuery.addEventListener?.('change', syncTheme)
})

onBeforeUnmount(() => themeQuery?.removeEventListener?.('change', syncTheme))
</script>

<style scoped>
.yh-auth-page {
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 24px;
  color: #182033;
  background: #f7f9fc;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC", sans-serif;
}

.yh-auth-card {
  width: min(100%, 390px);
  padding: 34px 32px 28px;
  border: 1px solid #e2e9f4;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 18px 55px rgba(47, 76, 128, 0.12), 0 2px 8px rgba(47, 76, 128, 0.05);
  backdrop-filter: blur(20px) saturate(145%);
}

.yh-auth-mark {
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
  margin-bottom: 24px;
  border-radius: 15px;
  color: #fff;
  background: #1677ff;
  box-shadow: 0 8px 22px rgba(22, 119, 255, 0.22);
}

.yh-auth-eyebrow {
  margin: 0 0 8px;
  color: #8794ad;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

h1 { margin: 0; font-size: 28px; line-height: 1.2; letter-spacing: 0; }
.yh-auth-copy { margin: 10px 0 28px; color: #65718a; font-size: 14px; line-height: 1.55; }
.yh-auth-form { display: grid; gap: 18px; }
.yh-auth-form label { display: grid; gap: 8px; color: #4b587c; font-size: 13px; font-weight: 650; }
.yh-auth-form input {
  width: 100%; height: 48px; box-sizing: border-box; padding: 0 14px;
  color: #182033; background: #f8faff; border: 1px solid #dfe8f6; border-radius: 12px;
  outline: none; font: inherit; transition: border-color 160ms ease, box-shadow 160ms ease, background 160ms ease;
}
.yh-auth-form input:focus { border-color: #1677ff; background: #fff; box-shadow: 0 0 0 4px rgba(22, 119, 255, 0.11); }
.yh-auth-password { position: relative; }
.yh-auth-password input { padding-right: 48px; }
.yh-auth-password button {
  position: absolute; right: 4px; top: 4px; width: 40px; height: 40px; display: grid; place-items: center;
  color: #71809a; border: 0; border-radius: 10px; background: transparent; cursor: pointer;
}
.yh-auth-password button:active { transform: scale(0.96); background: #eef5ff; }
.yh-auth-submit {
  height: 48px; display: flex; align-items: center; justify-content: center; gap: 9px;
  color: #fff; border: 0; border-radius: 13px; background: #1677ff; font-size: 15px; font-weight: 750;
  box-shadow: 0 8px 20px rgba(22, 119, 255, 0.2); cursor: pointer; transition: transform 120ms ease, opacity 160ms ease;
}
.yh-auth-submit:active { transform: scale(0.98); }
.yh-auth-submit:disabled { opacity: 0.65; cursor: wait; }
.yh-auth-error { margin: -4px 0 0; color: #d92d36; font-size: 13px; line-height: 1.4; }
.yh-auth-footnote { margin: 20px 0 0; color: #8a96b8; font-size: 12px; text-align: center; }

[data-mcr-theme="dark"] { color: #f4f7fb; background: #0f172a; }
[data-mcr-theme="dark"] .yh-auth-card { background: rgba(23, 32, 51, 0.95); border-color: rgba(230, 236, 245, 0.12); box-shadow: 0 24px 64px rgba(0, 0, 0, 0.32); }
[data-mcr-theme="dark"] .yh-auth-copy,
[data-mcr-theme="dark"] .yh-auth-form label { color: #c7d0e3; }
[data-mcr-theme="dark"] .yh-auth-form input { color: #f4f7fb; background: #111a2c; border-color: rgba(230, 236, 245, 0.14); }
[data-mcr-theme="dark"] .yh-auth-form input:focus { background: #172033; border-color: #6ea2ff; }
[data-mcr-theme="dark"] .yh-auth-password button { color: #c7d0e3; }

@media (max-width: 480px) {
  .yh-auth-page { padding: 16px; }
  .yh-auth-card { padding: 28px 22px 24px; border-radius: 18px; }
}

@media (prefers-reduced-motion: reduce) {
  .yh-auth-form input, .yh-auth-submit { transition: none; }
}
</style>
