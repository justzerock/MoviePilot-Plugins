<template>
  <div class="dashboard-widget" data-mcr-theme>
    <v-hover>
      <template #default="{ isHovering, props: hoverProps }">
        <div class="mcr-shell mcr-dashboard-shell">
          <div class="mcr-shell__aurora" />
          <div class="mcr-shell__noise" />
          <v-card v-bind="hoverProps" class="mcr-frame">
            <v-card-text class="mcr-frame__body">
              <div class="dashboard-head">
                <div>
                  <div class="mcr-kicker">Dashboard Widget</div>
                  <div class="dashboard-title">呀哈哈封面工坊</div>
                </div>
                <div v-show="isHovering" class="dashboard-drag">
                  <v-icon class="cursor-move">mdi-drag</v-icon>
                </div>
              </div>

              <div class="dashboard-meta">
                <div class="dashboard-meta__item">
                  <span>服务器</span>
                  <strong>{{ config.selected_servers?.length || 0 }}</strong>
                </div>
                <div class="dashboard-meta__item">
                  <span>风格</span>
                  <strong>{{ config.cover_style_base || 'static_1' }}</strong>
                </div>
                <div class="dashboard-meta__item">
                  <span>模式</span>
                  <strong>{{ config.cover_style_variant || 'static' }}</strong>
                </div>
              </div>

              <div class="dashboard-note">
                当前卡片只暴露最常用的生成入口，详情参数仍在插件主面板中维护。
              </div>

              <v-btn
                v-if="allowRefresh"
                class="mcr-button mcr-button--primary dashboard-action"
                prepend-icon="mdi-play-circle-outline"
                @click="generateNow"
              >
                立即生成封面
              </v-btn>
            </v-card-text>
          </v-card>
        </div>
      </template>
    </v-hover>
  </div>
</template>

<script setup lang="ts">
import '../styles/figmaTheme.css'
import type { PropType } from 'vue'
import type { YahahaCoverStudioConfig, PluginApi } from '../types/plugin'

const props = defineProps({
  config: {
    type: Object as PropType<YahahaCoverStudioConfig>,
    default: () => ({} as YahahaCoverStudioConfig),
  },
  allowRefresh: {
    type: Boolean,
    default: true,
  },
  api: {
    type: Object as PropType<PluginApi>,
    default: () => ({} as PluginApi),
  },
})

async function generateNow() {
  try {
    await props.api.post('plugin/YahahaCoverStudio/generate_now')
  } catch (e) {
    console.error('dashboard generate_now failed', e)
  }
}
</script>

<style scoped>
.dashboard-widget {
  width: 100%;
}

.mcr-dashboard-shell {
  border-radius: 12px;
}

.dashboard-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
  margin-bottom: 16px;
}

.dashboard-title {
  margin-top: 6px;
  font-family: 'McrHeading', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  font-size: 1.5rem;
  line-height: 1.10;
  letter-spacing: -0.9px;
  font-weight: 600;
  color: var(--mcr-charcoal, var(--mcr-color-on-surface));
}

.dashboard-drag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 6px;
  background: var(--mcr-charcoal-04, rgba(var(--mcr-rgb-on-surface), 0.04));
  border: 1px solid var(--mcr-border, var(--mcr-color-outline-variant));
}

.dashboard-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.dashboard-meta__item {
  display: grid;
  gap: 6px;
  padding: 12px;
  border-radius: 12px;
  background: var(--mcr-cream, var(--mcr-color-surface));
  border: 1px solid var(--mcr-border, var(--mcr-color-outline-variant));
}

.dashboard-meta__item span {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--mcr-muted, var(--mcr-color-on-surface-variant));
}

.dashboard-meta__item strong {
  font-size: 1rem;
  line-height: 1.20;
  font-weight: 600;
  color: var(--mcr-charcoal, var(--mcr-color-on-surface));
}

.dashboard-note {
  margin-top: 14px;
  margin-bottom: 16px;
  color: var(--mcr-muted, var(--mcr-color-on-surface-variant));
  font-size: 0.875rem;
  line-height: 1.50;
}

.dashboard-action {
  width: 100%;
}

@media (max-width: 959px) {
  .dashboard-meta {
    grid-template-columns: 1fr;
  }
}
</style>
