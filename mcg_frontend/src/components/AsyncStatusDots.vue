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
  color: var(--mcr-color-on-surface-variant);
  font-size: 11px;
  line-height: 1;
  white-space: nowrap;
}

.mcr-async-status__dots {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 14px;
}

.mcr-async-status__dots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--mcr-color-primary);
  animation: mcr-async-dot 900ms ease-in-out infinite;
}

.mcr-async-status__dots i:nth-child(2) {
  background: var(--mcr-color-secondary);
  animation-delay: 120ms;
}

.mcr-async-status__dots i:nth-child(3) {
  background: var(--mcr-color-success);
  animation-delay: 240ms;
}

.mcr-async-status__label {
  overflow: hidden;
  text-overflow: ellipsis;
}

@keyframes mcr-async-dot {
  0%, 70%, 100% {
    opacity: 0.42;
    transform: translateY(2px) scale(0.82);
  }
  35% {
    opacity: 1;
    transform: translateY(-3px) scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .mcr-async-status__dots i {
    animation: none;
    opacity: 0.86;
  }
}
</style>
