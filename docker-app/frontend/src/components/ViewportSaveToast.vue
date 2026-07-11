<template>
  <Teleport to="body">
    <Transition name="mcr-viewport-toast">
      <div
        v-if="message"
        class="mcr-viewport-save-toast"
        :data-mcr-theme="theme"
        role="status"
        aria-live="polite"
      >
        {{ message }}
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  message: string
  theme: 'light' | 'dark'
}>()
</script>

<style scoped>
.mcr-viewport-save-toast {
  position: fixed;
  right: max(20px, env(safe-area-inset-right));
  bottom: max(20px, env(safe-area-inset-bottom));
  z-index: 2147483000;
  max-width: min(320px, calc(100vw - 32px));
  padding: 10px 14px;
  overflow: hidden;
  border: 1px solid #dfe8f6;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.96);
  color: #53627d;
  box-shadow: 0 14px 36px rgba(28, 77, 160, 0.18);
  font-size: 13px;
  font-weight: 800;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
  pointer-events: none;
  backdrop-filter: blur(14px);
}

.mcr-viewport-save-toast[data-mcr-theme="dark"] {
  border-color: rgba(230, 236, 245, 0.14);
  background: rgba(30, 42, 66, 0.96);
  color: #dbe4f5;
  box-shadow: 0 14px 38px rgba(0, 0, 0, 0.34);
}

.mcr-viewport-toast-enter-active,
.mcr-viewport-toast-leave-active {
  transition: opacity 220ms ease, transform 220ms ease;
}

.mcr-viewport-toast-enter-from,
.mcr-viewport-toast-leave-to {
  opacity: 0;
  transform: translateY(10px) scale(0.97);
}
</style>
