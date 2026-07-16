<template>
  <span class="mcr-async-status" role="status" aria-live="polite">
    <span class="mcr-async-status__dots" aria-hidden="true">
      <i />
      <i />
      <i />
    </span>
    <span v-if="label" class="mcr-async-status__label">{{ label }}</span>
  </span>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  label?: string
}>(), {
  label: '',
})
</script>

<style scoped>
.mcr-async-status {
  display: inline-flex;
  min-width: 0;
  align-items: center;
  gap: 7px;
  color: var(--color-text-muted, var(--mcr-color-on-surface-variant));
  font-size: 11px;
  line-height: 1;
  white-space: nowrap;
}

.mcr-async-status__dots {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  height: 14px;
}

.mcr-async-status__dots i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #007aff;
  animation: mcr-async-dot 1100ms cubic-bezier(0.2, 0.78, 0.25, 1) infinite;
}

.mcr-async-status__dots i:nth-child(2) {
  background: #5ac8fa;
  animation-delay: 140ms;
}

.mcr-async-status__dots i:nth-child(3) {
  background: #34c759;
  animation-delay: 280ms;
}

.mcr-async-status__label {
  overflow: hidden;
  text-overflow: ellipsis;
}

@keyframes mcr-async-dot {
  0%, 68%, 100% {
    opacity: 0.34;
    transform: scale(0.72);
  }
  34% {
    opacity: 1;
    transform: scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .mcr-async-status__dots i {
    animation: none;
    opacity: 0.86;
  }
}
</style>
