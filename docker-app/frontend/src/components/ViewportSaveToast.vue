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
  border: 1px solid rgba(60, 60, 67, 0.14);
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.84);
  color: rgba(60, 60, 67, 0.88);
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.05),
    0 14px 34px rgba(28, 39, 61, 0.13);
  font-size: 13px;
  font-weight: 700;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
  pointer-events: none;
  backdrop-filter: blur(22px) saturate(150%);
  -webkit-backdrop-filter: blur(22px) saturate(150%);
}

.mcr-viewport-save-toast[data-mcr-theme="dark"] {
  border-color: rgba(255, 255, 255, 0.12);
  background: rgba(36, 36, 38, 0.84);
  color: rgba(235, 235, 245, 0.88);
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.22),
    0 16px 38px rgba(0, 0, 0, 0.32);
}

.mcr-viewport-toast-enter-active,
.mcr-viewport-toast-leave-active {
  transition:
    opacity 220ms ease,
    transform 260ms cubic-bezier(0.2, 0.78, 0.25, 1),
    backdrop-filter 220ms ease;
}

.mcr-viewport-toast-enter-from,
.mcr-viewport-toast-leave-to {
  opacity: 0;
  transform: translateY(14px) scale(0.96);
  backdrop-filter: blur(8px) saturate(120%);
}

@media (prefers-reduced-motion: reduce) {
  .mcr-viewport-toast-enter-active,
  .mcr-viewport-toast-leave-active {
    transition: opacity 160ms ease;
  }

  .mcr-viewport-toast-enter-from,
  .mcr-viewport-toast-leave-to {
    transform: none;
  }
}

@media (prefers-reduced-transparency: reduce) {
  .mcr-viewport-save-toast {
    background: #fff;
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
  }

  .mcr-viewport-save-toast[data-mcr-theme="dark"] {
    background: #242426;
  }
}
</style>
