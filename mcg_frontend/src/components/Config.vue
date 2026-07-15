<template>
  <div class="mcr-shell mcr-config-shell" :data-mcr-theme="isDark ? 'dark' : 'light'">
    <div class="mcr-shell__aurora" />
    <div class="mcr-shell__noise" />
    <v-card class="mcr-frame">
      <v-defaults-provider :defaults="controlDefaults">
        <div class="mcr-config-app">
          <header class="mcr-config-topbar">
            <div class="mcr-config-brand">
              <h1 class="yh-settings-title-wrap" aria-label="配置 Configuration">
                <span class="yh-settings-en">Configuration</span>
                <span class="yh-settings-zh">配置</span>
              </h1>
            </div>
            <div class="mcr-config-topbar__meta">
              <div class="mcr-config-top-actions yh-top-actions">
                <button
                  type="button"
                  class="yh-run-btn"
                  :class="{ 'is-running': isGenerating }"
                  :style="configRunButtonProgressStyle"
                  :title="isGenerating ? configGenerationProgressLabel : '立即生成'"
                  :aria-label="isGenerating ? configGenerationProgressLabel : '立即生成'"
                  :disabled="generatingNow"
                  @click="handleGenerateAction"
                >
                  <span class="yh-run-progress" aria-hidden="true" />
                  <span class="yh-run-content">
                    <v-icon :icon="isGenerating ? 'mdi-stop-circle-outline' : 'mdi-play-circle-outline'" size="24" />
                    <span v-if="isGenerating" class="yh-run-text">生成中</span>
                    <span v-if="isGenerating" class="yh-run-percent">{{ configGenerationProgressPercent }}%</span>
                  </span>
                </button>
                <v-btn
                  size="small"
                  class="mcr-button mcr-button--ghost mcr-button--dark-neutral yh-icon-btn yh-icon-btn--save"
                  icon
                  title="保存配置"
                  aria-label="保存配置"
                  :disabled="isGenerating || generatingNow || configSaving"
                  :loading="configSaving"
                  @click="saveConfig()"
                >
                  <v-icon icon="mdi-content-save-outline" size="22" />
                </v-btn>
                <v-btn
                  size="small"
                  class="mcr-button mcr-button--ghost mcr-button--dark-neutral yh-icon-btn"
                  icon
                  title="封面预览"
                  aria-label="封面预览"
                  :disabled="isGenerating || generatingNow"
                  @click="notifySwitch"
                >
                  <v-icon icon="mdi-image-multiple-outline" size="22" />
                </v-btn>
                <v-btn
                  size="small"
                  class="mcr-button mcr-button--ghost mcr-button--dark-neutral yh-icon-btn"
                  icon
                  title="关闭"
                  aria-label="关闭"
                  @click="notifyClose"
                >
                  <v-icon icon="mdi-close" size="22" />
                </v-btn>
              </div>
              <div class="mcr-config-tags yh-header-chips" aria-label="配置摘要">
                <span class="mcr-config-tag">
                  <span>状态</span>
                  <strong>{{ config.enabled ? '启用' : '停用' }}</strong>
                </span>
                <span class="mcr-config-tag">
                  <span>调度</span>
                  <strong>{{ scheduleModeLabel }}</strong>
                </span>
              </div>
              <div class="mcr-config-top-tabs yh-segment" role="tablist" aria-label="设置页面切换">
                <button
                  v-for="item in tabItems"
                  :key="`top-${item.value}`"
                  type="button"
                  class="mcr-config-top-tab yh-segment-item"
                  :class="{ 'is-active': tab === item.value }"
                  role="tab"
                  :aria-selected="tab === item.value"
                  @click="tab = item.value"
                >
                  <v-icon :icon="item.icon" size="18" />
                  <span>{{ item.title }}</span>
                </button>
              </div>
            </div>
          </header>

          <div class="mcr-config-workspace">
            <aside class="mcr-config-sidebar" aria-label="设置页面导航">
              <div class="mcr-config-sidebar__label">Sections</div>
              <button
                v-for="item in tabItems"
                :key="item.value"
                type="button"
                class="mcr-config-nav"
                :class="{ 'mcr-config-nav--active': tab === item.value }"
                role="tab"
                :aria-selected="tab === item.value"
                @click="tab = item.value"
              >
                <v-icon :icon="item.icon" size="22" />
                <span>{{ item.title }}</span>
              </button>
              <div class="mcr-config-sidebar__spacer" />
            </aside>

            <main ref="settingsContentEl" class="mcr-config-main">
              <SettingsAnchorNav
                v-if="tab === 'basic-tab'"
                :sections="settingsAnchorSections"
                :content-element="settingsContentEl"
                :scroll-container="settingsContentEl"
                :top-offset="96"
                :theme="isDark ? 'dark' : 'light'"
              />
              <v-window v-model="tab">
          <v-window-item value="basic-tab">
            <v-card-text class="mcr-panel__body mcr-config-tabbody mcr-config-section-stack">
              <section id="settings-runtime" class="mcr-config-section-card">
                <header class="mcr-config-section-card__header">
                  <div>
                    <div class="mcr-config-section-card__title">运行与定时</div>
                    <p class="mcr-config-section-card__copy">控制插件开关和自动更新周期。</p>
                  </div>
                </header>
                <v-row class="mcr-form-grid mcr-form-grid--center" align="center">
                  <v-col cols="12" md="4" class="mcr-config-switch-col">
                    <div class="yh-switch-row">
                      <v-switch
                        v-model="config.enabled"
                        label="启用插件"
                        hide-details
                      />
                      <v-switch
                        v-model="config.auto_save_config"
                        label="自动保存配置"
                        hide-details
                        @update:model-value="onConfigAutoSaveSwitch"
                      />
                    </div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <BlueprintField
                      v-model="config.cron"
                      label="定时更新"
                      placeholder="* * * * *"
                      hint="留空则不启用定时任务，使用 5 位 cron 表达式"
                    />
                  </v-col>
                </v-row>
              </section>

              <section id="settings-monitoring" class="mcr-config-section-card">
                <header class="mcr-config-section-card__header">
                  <div>
                    <div class="mcr-config-section-card__title">入库监控</div>
                    <p class="mcr-config-section-card__copy">媒体入库后自动更新所在媒体库封面。</p>
                  </div>
                </header>
                <v-row class="mcr-form-grid mcr-form-grid--center mcr-monitor-grid" align="center">
                  <v-col cols="12" md="3" class="mcr-config-switch-col">
                    <v-switch
                      v-model="config.transfer_monitor"
                      label="入库监控"
                      hide-details
                    />
                  </v-col>
                  <v-col cols="12" md="3">
                    <BlueprintSelect
                      v-model="config.monitor_source"
                      :items="monitorSourceItems"
                      label="监控来源"
                      hint="MP 事件方便，Emby Webhook 更精准"
                      :disabled="!config.transfer_monitor"
                    />
                  </v-col>
                  <v-col cols="12" md="3" class="mcr-config-switch-col">
                    <v-switch
                      v-model="config.lock_latest_sort"
                      label="按最新入库排序"
                      hide-details
                      :disabled="!config.transfer_monitor"
                    />
                  </v-col>
                  <v-col cols="12" md="3">
                    <BlueprintField
                      v-model.number="config.delay"
                      type="number"
                      label="入库延迟（秒）"
                      placeholder="60"
                      hint="根据实际扫描速度调整延迟时间"
                    />
                  </v-col>
                </v-row>
                <p class="yh-field-hint yh-monitor-hint">
                  开启后会在媒体入库时自动更新所在媒体库封面。<br>
                  如开启「按最新入库排序」，预览页中的来源排序将被锁定，不可手动修改。
                  <br>
                  使用 Emby 入库监控时，需要手动配置媒体服务器 Webhook，回调相对路径为
                  <code>/api/v1/webhook?token=API_TOKEN&amp;source=媒体服务器名</code>（3001 端口），其中
                  <code>API_TOKEN</code> 为设置中的 API_TOKEN。Emby 需要在通知中勾选「媒体库 -> 新媒体已添加」。
                  Jellyfin 的通知配置方式暂未确认。
                </p>
              </section>

              <section id="settings-libraries" class="mcr-config-section-card">
                <header class="mcr-config-section-card__header">
                  <div>
                    <div class="mcr-config-section-card__title">媒体库范围</div>
                    <p class="mcr-config-section-card__copy">限定参与封面更新的服务器与媒体库。</p>
                  </div>
                </header>
                <v-row class="mcr-form-grid">
                  <v-col cols="12" md="6">
                    <BlueprintSelect
                      v-model="config.selected_servers"
                      :items="serverItems"
                      multiple
                      clearable
                      label="媒体服务器"
                      hint="不勾选时默认更新所有已连接服务器"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <BlueprintSelect
                      v-model="config.include_libraries"
                      :items="libraryItems"
                      multiple
                      clearable
                      label="更新媒体库"
                      hint="默认更新全部，或只更新勾选的媒体库"
                    />
                  </v-col>
                </v-row>
              </section>

              <section id="settings-schemes" class="mcr-config-section-card">
                <header class="mcr-config-section-card__header">
                  <div><div class="mcr-config-section-card__title">媒体库方案</div><p class="mcr-config-section-card__copy">为媒体库指定封面方案；未匹配的媒体库使用默认方案。</p></div>
                  <v-btn size="small" class="mcr-button mcr-button--ghost mcr-button--dark-neutral" prepend-icon="mdi-plus" @click="addSchemeRule">新增规则</v-btn>
                </header>
                <BlueprintSelect v-model="config.default_scheme_id" :items="schemeItems" label="默认方案" />
                <div v-for="(rule, index) in config.library_scheme_rules" :key="rule.id" class="mcr-config-scheme-rule">
                  <v-row class="mcr-form-grid"><v-col cols="12" md="4"><BlueprintSelect v-model="rule.scheme_id" :items="schemeItems" label="封面方案" /></v-col><v-col cols="12" md="8"><BlueprintSelect v-model="rule.library_keys" :items="ruleLibraryItems(index)" multiple label="媒体库" hint="已在其他规则中分配的媒体库不会重复显示" /></v-col></v-row>
                  <v-btn icon="mdi-close" size="x-small" variant="text" class="mcr-config-scheme-rule__remove" title="删除规则" @click="removeSchemeRule(index)" />
                </div>
              </section>

              <section id="settings-images" class="mcr-config-section-card">
                <header class="mcr-config-section-card__header">
                  <div>
                    <div class="mcr-config-section-card__title">自定义图片目录</div>
                    <p class="mcr-config-section-card__copy">优先使用指定目录中的真实素材生成封面。</p>
                  </div>
                </header>
                <BlueprintField
                  v-model="config.covers_input"
                  label="自定义图片目录"
                  hint="图片放在与媒体库同名的文件夹下；留空则使用媒体服务器素材"
                />
              </section>

              <section id="settings-history" class="mcr-config-section-card">
                <header class="mcr-config-section-card__header">
                  <div>
                    <div class="mcr-config-section-card__title">历史封面</div>
                    <p class="mcr-config-section-card__copy">按生成批次保留封面，用于时光机恢复。</p>
                  </div>
                </header>
                <v-row class="mcr-form-grid mcr-form-grid--center" align="center">
                  <v-col cols="12" md="3" class="mcr-config-switch-col">
                    <v-switch
                      v-model="config.save_recent_covers"
                      label="保存历史封面"
                      hide-details
                    />
                  </v-col>
                  <v-col cols="12" md="5">
                    <BlueprintField
                      v-model.number="config.history_retention_batches"
                      type="number"
                      label="所有批次的上限"
                      hint="默认保留最近 30 个完整批次"
                    />
                  </v-col>
                </v-row>
              </section>

              <section id="settings-fonts" class="mcr-config-section-card">
                <header class="mcr-config-section-card__header">
                  <div>
                    <div class="mcr-config-section-card__title">字体库</div>
                    <p class="mcr-config-section-card__copy">设置标题与自定义文本字体，管理上传字体。</p>
                  </div>
                </header>
                <v-row class="mcr-form-grid">
                  <v-col cols="12" md="4">
                    <BlueprintSelect
                      v-model="config.main_title_font_preset"
                      :items="mainTitleFontItems"
                      label="主标题字体"
                    />
                  </v-col>
                  <v-col cols="12" md="4">
                    <BlueprintSelect
                      v-model="config.subtitle_font_preset"
                      :items="subtitleFontItems"
                      label="副标题字体"
                    />
                  </v-col>
                  <v-col cols="12" md="4">
                    <BlueprintSelect
                      v-model="config.custom_text_font_preset"
                      :items="subtitleFontItems"
                      label="自定义文本字体"
                    />
                  </v-col>
                </v-row>
                <v-row class="mcr-form-grid mt-1">
                  <v-col cols="12" md="6" class="mcr-config-switch-col"><v-switch v-model="config.preview_font_enabled" label="预览字体" hide-details /><p>在预览页和画布编辑器中加载实际字体，使预览更接近正式生成。</p></v-col>
                  <v-col cols="12" md="6" class="mcr-config-switch-col"><v-switch v-model="config.font_subset_enabled" :disabled="!config.preview_font_enabled" label="自动精简预览字体" hide-details /><p>只保留预览中可能使用的文字，不影响正式生成使用的原始字体。</p></v-col>
                </v-row>

                <input
                  ref="fontFileInputEl"
                  class="mcr-font-file-input"
                  type="file"
                  accept=".ttf,.ttc,.otf,.woff,.woff2,font/*"
                  @change="onFontFileInputChange"
                >
                <div class="mcr-font-library">
                  <div class="mcr-font-library__header">
                    <div>
                      <div class="mcr-panel__eyebrow">Font Library</div>
                      <div class="mcr-panel__title mcr-font-library__title">自定义字体库</div>
                    </div>
                    <v-btn
                      size="small"
                      class="mcr-button mcr-button--ghost mcr-button--dark-neutral"
                      prepend-icon="mdi-upload-outline"
                      :disabled="fontLibraryLoading"
                      @click="openFontFilePicker"
                    >
                      上传字体
                    </v-btn>
                  </div>
                  <div class="mcr-font-library__import">
                    <label class="mcr-font-link-field">
                      <span class="mcr-blueprint-field__label">网络字体链接</span>
                      <span class="mcr-font-link-field__control">
                        <input
                          v-model="fontUrlInput"
                          class="mcr-blueprint-field__control mcr-font-link-field__input"
                          type="url"
                          placeholder="https://example.com/font.woff2"
                        >
                        <button
                          v-if="fontUrlInput.trim()"
                          type="button"
                          class="mcr-font-link-field__download"
                          :disabled="fontLibraryLoading"
                          title="下载字体"
                          aria-label="下载字体"
                          @click.prevent="uploadFontUrl"
                        >
                          <v-icon icon="mdi-download" size="18" />
                        </button>
                      </span>
                      <span class="mcr-blueprint-field__hint">支持 ttf / ttc / otf / woff / woff2，导入后保存到插件数据目录</span>
                    </label>
                  </div>
                  <div class="mcr-font-library__listbar">
                    <button
                      type="button"
                      class="mcr-config-collapse-button"
                      @click="fontLibraryExpanded = !fontLibraryExpanded"
                    >
                      <v-icon :icon="fontLibraryExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down'" size="18" />
                      已上传字体 {{ customFontItems.length }} 个
                    </button>
                  </div>
                  <div v-if="fontLibraryExpanded && fontLibraryLoading" class="mcr-font-library__empty">正在读取字体库...</div>
                  <div v-else-if="fontLibraryExpanded && !customFontItems.length" class="mcr-font-library__empty">暂无自定义字体</div>
                  <div v-else-if="fontLibraryExpanded" class="mcr-font-library__grid">
                    <button
                      v-for="item in customFontItems"
                      :key="item.value"
                      type="button"
                      class="mcr-font-item"
                      :title="item.name"
                      @click="config.custom_text_font_preset = item.value"
                    >
                      <span class="mcr-font-item__sample" :style="{ fontFamily: getCustomFontFamily(item) }">Aa 字</span>
                      <span class="mcr-font-item__name">{{ item.title }}</span>
                      <span
                        role="button"
                        tabindex="-1"
                        class="mcr-font-item__rename"
                        title="重命名字体"
                        @click.stop.prevent="renameFontItem(item)"
                      >
                        <v-icon icon="mdi-pencil-outline" size="15" />
                      </span>
                      <span
                        role="button"
                        tabindex="-1"
                        class="mcr-font-item__delete"
                        title="删除字体"
                        @click.stop.prevent="deleteFontItem(item)"
                      >
                        <v-icon icon="mdi-trash-can-outline" size="15" />
                      </span>
                    </button>
                  </div>
                  <div v-if="fontUploadMessage" class="mcr-font-library__status">{{ fontUploadMessage }}</div>
                </div>
              </section>

              <section id="settings-backup" class="mcr-config-section-card">
                <header class="mcr-config-section-card__header">
                  <div>
                    <div class="mcr-config-section-card__title">备份还原</div>
                    <p class="mcr-config-section-card__copy">备份完整配置，上传恢复文件，或初始化当前插件配置。</p>
                  </div>
                </header>
                <input
                  ref="backupFileInputEl"
                  class="mcr-font-file-input"
                  type="file"
                  accept=".json,application/json"
                  @change="onBackupFileInputChange"
                >
                <div class="mcr-config-backup-grid mcr-config-backup-grid--cron-only">
                  <div>
                    <BlueprintField
                      v-model="config.backup_path"
                      label="备份本地路径"
                      placeholder="留空使用插件数据目录/backups"
                      hint="可填写目录或 .json 文件路径；相对路径会保存到插件数据目录下"
                    />
                  </div>
                  <div>
                    <BlueprintField
                      v-model="config.backup_cron"
                      label="备份 cron"
                      placeholder="0 4 * * *"
                      hint="留空关闭定时备份；填写正确 5 位 cron 表达式则开启"
                    />
                  </div>
                  <div class="mcr-config-backup-grid__actions">
                    <div class="mcr-config-backup-actions">
                      <v-btn
                        class="mcr-button mcr-button--ghost mcr-button--dark-neutral"
                        prepend-icon="mdi-content-save-cog-outline"
                        :disabled="Boolean(cacheAction)"
                        @click="onBackupConfig"
                      >
                        立即备份
                      </v-btn>
                      <v-btn
                        class="mcr-button mcr-button--ghost mcr-button--dark-neutral"
                        prepend-icon="mdi-upload-box-outline"
                        :disabled="Boolean(cacheAction)"
                        @click="openBackupFilePicker"
                      >
                        上传备份
                      </v-btn>
                      <v-btn
                        class="mcr-button mcr-button--ghost mcr-button--dark-neutral"
                        prepend-icon="mdi-restore-alert"
                        :disabled="Boolean(cacheAction)"
                        @click="initializePluginConfig"
                      >
                        初始化插件
                      </v-btn>
                      <AsyncStatusDots v-if="cacheAction === 'backup'" label="备份配置" />
                      <button
                        type="button"
                        class="mcr-config-collapse-button"
                        @click="backupLibraryExpanded = !backupLibraryExpanded"
                      >
                        <v-icon :icon="backupLibraryExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down'" size="18" />
                        已备份 {{ backupItems.length }} 个
                      </button>
                    </div>
                    <div v-if="backupLibraryExpanded" class="mcr-backup-library">
                      <div v-if="backupListLoading" class="mcr-font-library__empty">正在读取备份记录...</div>
                      <div v-else-if="!backupItems.length" class="mcr-font-library__empty">暂无备份记录</div>
                      <div v-else class="mcr-backup-library__grid">
                        <article
                          v-for="item in backupItems"
                          :key="item.path || item.name"
                          class="mcr-backup-item"
                        >
                          <div class="mcr-backup-item__main">
                            <div class="mcr-backup-item__name" :title="item.name">{{ item.name }}</div>
                            <div class="mcr-backup-item__meta">
                              {{ item.exported_at || item.mtime_label || '未知时间' }}
                              <span v-if="item.version">v{{ item.version }}</span>
                            </div>
                          </div>
                          <div class="mcr-backup-item__actions">
                            <button type="button" title="下载备份" @click.stop.prevent="downloadBackupItem(item)">
                              <v-icon icon="mdi-download-outline" size="17" />
                            </button>
                            <button type="button" title="恢复配置" @click.stop.prevent="restoreBackupItem(item)">
                              <v-icon icon="mdi-restore" size="17" />
                            </button>
                            <button type="button" title="删除备份" class="mcr-backup-item__danger" @click.stop.prevent="deleteBackupItem(item)">
                              <v-icon icon="mdi-trash-can-outline" size="17" />
                            </button>
                          </div>
                        </article>
                      </div>
                    </div>
                  </div>
                </div>
              </section>

              <section id="settings-cache" class="mcr-config-section-card">
                <header class="mcr-config-section-card__header">
                  <div>
                    <div class="mcr-config-section-card__title">清理缓存</div>
                    <p class="mcr-config-section-card__copy">清理图片或字体缓存，不影响已保存的配置。</p>
                  </div>
                </header>
                <div class="mcr-config-clean-actions">
                  <div class="mcr-config-clean-action">
                    <div>
                      <strong>清理图片缓存</strong>
                      <span>释放插件生成图片缓存占用的空间。</span>
                    </div>
                    <v-btn
                      class="mcr-button mcr-button--danger mcr-config-cache-danger"
                      prepend-icon="mdi-image-remove"
                      :disabled="Boolean(cacheAction)"
                      @click="onCleanImages"
                    >
                      清理图片缓存
                    </v-btn>
                    <AsyncStatusDots v-if="cacheAction === 'images'" label="清理图片缓存" />
                  </div>
                  <div class="mcr-config-clean-action">
                    <div>
                      <strong>清理字体缓存</strong>
                      <span>遇到字体读取异常时可尝试重新清理。</span>
                    </div>
                    <v-btn
                      class="mcr-button mcr-button--danger mcr-config-cache-danger"
                      prepend-icon="mdi-format-font"
                      :disabled="Boolean(cacheAction)"
                      @click="onCleanFonts"
                    >
                      清理字体缓存
                    </v-btn>
                    <AsyncStatusDots v-if="cacheAction === 'fonts'" label="清理字体缓存" />
                  </div>
                </div>
              </section>
            </v-card-text>
          </v-window-item>

          <v-window-item value="title-tab">
            <v-card-text class="mcr-panel__body mcr-config-tabbody">
              <div class="mcr-panel__eyebrow">Titles</div>
              <div class="mcr-title-config-heading">
                <div class="mcr-panel__title">主副标题配置</div>
                <v-btn size="small" class="mcr-button mcr-button--ghost mcr-button--dark-neutral mcr-title-config-template-btn" prepend-icon="mdi-format-list-bulleted-square" :loading="titleTemplateLoading" @click="appendMissingTitleTemplates">补全媒体库模板</v-btn>
              </div>
              <p class="mcr-panel__copy mcr-config-copy">
                严格模式按标准 YAML 校验；宽容模式会兼容中文冒号、冒号后无空格和部分缩进问题。
              </p>

              <div class="mcr-title-config-toolbar">
                <v-switch
                  v-model="config.distinguish_same_name_libraries"
                  color="primary"
                  hide-details
                  density="comfortable"
                  label="区分同名媒体库"
                />
                <span class="mcr-title-config-mode">
                  开启后自动补全使用「服务器名_媒体库名」；仅使用媒体库名时，同名库共用同一配置
                </span>
                <v-switch
                  v-model="config.title_config_strict"
                  color="primary"
                  hide-details
                  density="comfortable"
                  :label="config.title_config_strict ? '严格模式' : '宽容模式'"
                />
                <span class="mcr-title-config-mode">
                  {{ config.title_config_strict ? '必须使用标准 YAML 语法' : '允许常见中文符号和空格容错' }}
                </span>
              </div>

              <div class="mcr-title-config-editor-shell">
                <BlueprintField
                  v-model="titleConfigEditorText"
                  textarea
                  label="主副标题配置 (YAML)"
                  rows="16"
                  spellcheck="false"
                  class="font-mono mcr-config-editor"
                  :placeholder="titlePlaceholder"
                  @focus="titleConfigEditorFocused = true"
                  @blur="titleConfigEditorFocused = false"
                  @compositionstart="onTitleConfigCompositionStart"
                  @compositionend="onTitleConfigCompositionEnd"
                />
                <div
                  v-if="titleConfigValidationMessage"
                  class="mcr-title-config-alert"
                  :class="{ 'mcr-title-config-alert--ok': titleConfigValidationValid }"
                  role="status"
                >
                  {{ titleConfigValidationMessage }}
                </div>
              </div>
              <div class="mcr-title-config-reference">
                <div class="mcr-title-config-reference__label">格式参考</div>
                <pre>{{ titleConfigReference }}</pre>
              </div>
            </v-card-text>
          </v-window-item>

              </v-window>
              <div class="yh-ui-rev">前端 UI {{ UI_REV }} · 主程序 v{{ PROGRAM_VERSION }}</div>
            </main>
          </div>
        </div>
        <ViewportSaveToast :message="configSaveMessage" :theme="isDark ? 'dark' : 'light'" />
      </v-defaults-provider>

    </v-card>
  </div>
</template>

<script setup lang="ts">
import '../styles/figmaTheme.css'
import { PROGRAM_VERSION, UI_REV } from '../constants/ui'
import { MCR_CONTROL_DEFAULTS } from '../constants/uiDefaults'
import { BUILTIN_FONT_ITEMS, getTemplateFontFaceName } from '../constants/fonts'
import { ref, watch, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import type { PropType } from 'vue'
import BlueprintField from './BlueprintField.vue'
import ViewportSaveToast from './ViewportSaveToast.vue'
import AsyncStatusDots from './AsyncStatusDots.vue'
import BlueprintSelect from './BlueprintSelect.vue'
import SettingsAnchorNav from './SettingsAnchorNav.vue'
import type {
  YahahaCoverStudioConfig,
  PluginApi,
  CustomStaticLayout,
  CustomStaticLayoutTemplate,
  StatusPayload,
} from '../types/plugin'

const props = defineProps({
  initialConfig: {
    type: Object as PropType<Partial<YahahaCoverStudioConfig>>,
    default: () => ({}),
  },
  api: {
    type: Object as PropType<PluginApi>,
    default: () => ({} as PluginApi),
  },
})

const emit = defineEmits<{
  (e: 'save', config: YahahaCoverStudioConfig): void
  (e: 'close'): void
  (e: 'switch'): void
}>()

const controlDefaults = MCR_CONTROL_DEFAULTS
const settingsContentEl = ref<HTMLElement | null>(null)
const settingsAnchorSections = [
  { id: 'settings-runtime', label: '运行与定时' },
  { id: 'settings-monitoring', label: '入库监控' },
  { id: 'settings-libraries', label: '媒体库范围' },
  { id: 'settings-schemes', label: '媒体库方案' },
  { id: 'settings-images', label: '自定义图片目录' },
  { id: 'settings-history', label: '历史封面' },
  { id: 'settings-fonts', label: '字体库' },
  { id: 'settings-backup', label: '备份还原' },
  { id: 'settings-cache', label: '清理缓存' },
]

const defaults: YahahaCoverStudioConfig = {
  enabled: true,
  auto_save_config: false,
  update_now: false,
  transfer_monitor: true,
  monitor_source: 'transfer',
  lock_latest_sort: false,
  cron: '',
  delay: 60,
  selected_servers: [],
  all_servers: [],
  include_libraries: [],
  all_libraries: [],
  sort_by: 'Random',
  title_config: '',
  title_config_strict: false,
  distinguish_same_name_libraries: false,
  covers_input: '',
  covers_output: '',
  save_recent_covers: true,
  history_retention_batches: 30,
  covers_history_limit_per_library: 10,
  covers_page_history_limit: 50,
  cover_style_base: 'static_1',
  cover_style_variant: 'static',
  main_title_font_preset: 'chaohei',
  subtitle_font_preset: 'EmblemaOne',
  custom_text_font_preset: 'EmblemaOne',
  main_title_font_custom: '',
  subtitle_font_custom: '',
  custom_text_font_custom: '',
  main_title_font_size: null,
  subtitle_font_size: null,
  blur_size: 50,
  color_ratio: 0.8,
  title_scale: 1.0,
  main_title_font_offset: null,
  title_spacing: null,
  subtitle_line_spacing: null,
  resolution: '480p',
  custom_width: 1920,
  custom_height: 1080,
  bg_color_mode: 'auto',
  custom_bg_color: '',
  animation_duration: 8,
  animation_scroll: 'alternate',
  animation_fps: 24,
  animation_format: 'apng',
  animation_resolution: '320x180',
  animation_reduce_colors: 'medium',
  animated_2_image_count: 6,
  animated_2_departure_type: 'fly',
  clean_images: false,
  clean_fonts: false,
  backup_enabled: false,
  backup_cron: '',
  backup_path: '',
  page_tab: 'generate-tab',
  style_naming_v2: true,
  custom_static_layout: null,
  custom_static_layouts: null,
  custom_static_active_id: null,
  preview_font_enabled: true,
  font_subset_enabled: true,
  library_scheme_rules: [],
  default_scheme_id: 'static_1',
}

const config = ref<YahahaCoverStudioConfig>({
  ...defaults,
  ...normalizeConfigInput(props.initialConfig as YahahaCoverStudioConfig),
})
const CONFIG_AUTO_SAVE_KEY = 'mcr-config-auto-save'
const generatingNow = ref(false)
const isGenerating = ref(false)
const configSaving = ref(false)
const configAutoSaveEnabled = ref(false)
const generationCurrent = ref(0)
const generationTotal = ref(0)
const generationLabel = ref('')
const optionsLoading = ref(false)
const cacheAction = ref<'images' | 'fonts' | 'backup' | ''>('')
let generationStatusTimer: number | null = null
const configBackendBusy = computed(() => isGenerating.value || generatingNow.value || optionsLoading.value || Boolean(cacheAction.value))
const configBackendBusyLabel = computed(() => {
  if (isGenerating.value) {
    if (generationTotal.value > 0) return `正在生成 ${generationCurrent.value || 0}/${generationTotal.value}`
    return generationLabel.value || '正在生成'
  }
  if (generatingNow.value) return '正在执行'
  if (cacheAction.value === 'backup') return '正在备份'
  if (cacheAction.value) return '正在清理'
  return '同步数据'
})
const configGenerationProgressLabel = computed(() => {
  if (generationTotal.value > 0) return `正在生成 ${generationCurrent.value || 0}/${generationTotal.value}`
  return generationLabel.value || '正在生成'
})
const configGenerationProgressPercent = computed(() => {
  if (generationTotal.value > 0) {
    const raw = Math.round((Math.max(0, generationCurrent.value || 0) / generationTotal.value) * 100)
    return Math.max(0, Math.min(100, raw))
  }
  return isGenerating.value ? 12 : 0
})
const configRunButtonProgressStyle = computed(() => ({
  '--yh-run-progress': `${configGenerationProgressPercent.value}%`,
}))
const configGenerateButtonLabel = computed(() =>
  isGenerating.value ? configGenerationProgressLabel.value : '立即生成',
)
const scheduleModeLabel = computed(() => {
  const hasMonitor = Boolean(config.value.transfer_monitor)
  const hasCron = Boolean(String(config.value.cron || '').trim())
  if (hasMonitor && hasCron) return '自动+定时'
  if (hasMonitor) return '自动'
  if (hasCron) return '定时'
  return '手动'
})

const monitorSourceItems = [
  { title: 'MP 整理完成（方便）', value: 'transfer' },
  { title: 'Emby 新媒体已添加（精准）', value: 'emby' },
]

interface FontLibraryItem {
  title: string
  name: string
  value: string
  path?: string
  url?: string
  dataUrl?: string
  size?: number
  mtime?: number
  renderable?: boolean
}

interface BackupItem {
  title?: string
  name: string
  path: string
  size?: number
  mtime?: number
  mtime_label?: string
  exported_at?: string
  version?: string
  schema?: string
}

const fontFileInputEl = ref<HTMLInputElement | null>(null)
const backupFileInputEl = ref<HTMLInputElement | null>(null)
const fontLibraryLoading = ref(false)
const backupListLoading = ref(false)
const customFontItems = ref<FontLibraryItem[]>([])
const backupItems = ref<BackupItem[]>([])
const fontLibraryExpanded = ref(true)
const backupLibraryExpanded = ref(true)
const fontUrlInput = ref('')
const fontUploadMessage = ref('')
const backupResult = ref('')
const configSaveMessage = ref('')
const titleConfigValidationMessage = ref('')
const titleConfigValidationValid = ref(false)
const titleConfigEditorText = ref(String(config.value.title_config || ''))
const titleConfigEditorFocused = ref(false)
const titleConfigComposing = ref(false)
const titleConfigEditorDirty = ref(false)
let titleConfigValidationRevision = 0
let suppressTitleConfigEditorWatch = false
const titleTemplateLoading = ref(false)
let titleConfigValidationTimer: number | null = null
let configAutoSaveTimer: number | null = null
let configSaveMessageTimer: number | null = null
let suppressConfigAutoSave = true
const loadedConfigFontUrls = new Map<string, Promise<void>>()

function normalizeConfigInput(input?: Partial<YahahaCoverStudioConfig> | Record<string, any>) {
  const raw = (input || {}) as Record<string, any>
  return {
    ...raw,
    update_now: false,
    auto_save_config: Boolean(raw.auto_save_config ?? defaults.auto_save_config),
    lock_latest_sort: Boolean(raw.lock_latest_sort ?? defaults.lock_latest_sort),
    monitor_source: raw.monitor_source === 'emby' ? 'emby' : 'transfer',
    main_title_font_preset: raw.main_title_font_preset ?? raw.zh_font_preset ?? defaults.main_title_font_preset,
    subtitle_font_preset: raw.subtitle_font_preset ?? raw.en_font_preset ?? defaults.subtitle_font_preset,
    custom_text_font_preset: raw.custom_text_font_preset ?? raw.subtitle_font_preset ?? raw.en_font_preset ?? defaults.custom_text_font_preset,
    main_title_font_custom: raw.main_title_font_custom ?? raw.zh_font_custom ?? defaults.main_title_font_custom,
    subtitle_font_custom: raw.subtitle_font_custom ?? raw.en_font_custom ?? defaults.subtitle_font_custom,
    custom_text_font_custom: raw.custom_text_font_custom ?? raw.subtitle_font_custom ?? raw.en_font_custom ?? defaults.custom_text_font_custom,
    main_title_font_size: raw.main_title_font_size ?? raw.zh_font_size ?? defaults.main_title_font_size,
    subtitle_font_size: raw.subtitle_font_size ?? raw.en_font_size ?? defaults.subtitle_font_size,
    main_title_font_offset: raw.main_title_font_offset ?? raw.zh_font_offset ?? defaults.main_title_font_offset,
    subtitle_line_spacing: raw.subtitle_line_spacing ?? raw.en_line_spacing ?? defaults.subtitle_line_spacing,
    title_config_strict: Boolean(raw.title_config_strict ?? defaults.title_config_strict),
    distinguish_same_name_libraries: Boolean(raw.distinguish_same_name_libraries ?? defaults.distinguish_same_name_libraries),
    backup_enabled: Boolean(raw.backup_enabled ?? defaults.backup_enabled),
    backup_cron: raw.backup_cron ?? defaults.backup_cron,
    backup_path: raw.backup_path ?? defaults.backup_path,
    preview_font_enabled: Boolean(raw.preview_font_enabled ?? defaults.preview_font_enabled),
    font_subset_enabled: Boolean(raw.font_subset_enabled ?? defaults.font_subset_enabled),
    library_scheme_rules: Array.isArray(raw.library_scheme_rules) ? raw.library_scheme_rules : [],
    default_scheme_id: raw.default_scheme_id ?? raw.cover_style ?? defaults.default_scheme_id,
  } as YahahaCoverStudioConfig
}

watch(
  () => props.initialConfig,
  (val) => {
    suppressConfigAutoSave = true
    config.value = {
      ...defaults,
      ...normalizeConfigInput(val as YahahaCoverStudioConfig),
    }
    if (!titleConfigEditorFocused.value && !titleConfigEditorDirty.value) {
      suppressTitleConfigEditorWatch = true
      titleConfigEditorText.value = String(config.value.title_config || '')
    }
    nextTick(() => {
      suppressTitleConfigEditorWatch = false
      suppressConfigAutoSave = false
    })
  },
  { deep: true },
)

watch(
  config,
  () => {
    scheduleConfigAutoSave()
  },
  { deep: true },
)

async function validateTitleConfig(showSuccess = false) {
  const titleConfig = titleConfigEditorText.value || ''
  const revision = ++titleConfigValidationRevision
  titleConfigValidationMessage.value = ''
  titleConfigValidationValid.value = false
  if (!titleConfig.trim()) {
    titleConfigValidationValid.value = true
    config.value.title_config = ''
    return true
  }
  try {
    const resp = await props.api.post<{
      code: number
      msg?: string
      data?: { valid?: boolean; errors?: string[] }
    }>('plugin/YahahaCoverStudio/validate_title_config', {
      title_config: titleConfig,
      strict: config.value.title_config_strict,
      distinguish_same_name_libraries: Boolean(config.value.distinguish_same_name_libraries),
    })
    const errors = Array.isArray(resp?.data?.errors) ? resp.data.errors : []
    const valid = Boolean(resp && resp.code === 0 && resp.data?.valid !== false && !errors.length)
    if (revision !== titleConfigValidationRevision) return false
    titleConfigValidationValid.value = valid
    if (!valid) {
      titleConfigValidationMessage.value = errors[0] || resp?.msg || '标题配置 YAML 格式不正确'
    } else {
      config.value.title_config = titleConfig
      if (showSuccess) titleConfigValidationMessage.value = ''
    }
    return valid
  } catch (error) {
    console.warn('validate title config failed', error)
    titleConfigValidationMessage.value = '标题配置验证失败，请稍后重试'
    titleConfigValidationValid.value = false
    return false
  }
}

async function appendMissingTitleTemplates() {
  titleTemplateLoading.value = true
  titleConfigValidationMessage.value = ''
  titleConfigValidationValid.value = false
  try {
    const resp = await props.api.post<{
      code: number
      msg?: string
      data?: {
        valid?: boolean
        errors?: string[]
        yaml?: string
        missing?: string[]
        reference?: string
      }
    }>('plugin/YahahaCoverStudio/title_config_template', {
      title_config: titleConfigEditorText.value || '',
      strict: config.value.title_config_strict,
      distinguish_same_name_libraries: Boolean(config.value.distinguish_same_name_libraries),
    })
    const errors = Array.isArray(resp?.data?.errors) ? resp.data.errors : []
    if (!resp || resp.code !== 0 || resp.data?.valid === false || errors.length) {
      titleConfigValidationMessage.value = errors[0] || resp?.msg || '标题配置格式不正确，无法补全媒体库模板'
      titleConfigValidationValid.value = false
      return
    }
    const yaml = String(resp.data?.yaml || '').trim()
    const missing = Array.isArray(resp.data?.missing) ? resp.data.missing : []
    if (!yaml) {
      titleConfigValidationMessage.value = '当前媒体库都已有标题配置，无需补全'
      titleConfigValidationValid.value = true
      return
    }
    const current = String(titleConfigEditorText.value || '').trimEnd()
    titleConfigEditorText.value = current ? `${current}\n\n${yaml}\n` : `${yaml}\n`
    titleConfigEditorDirty.value = true
    titleConfigValidationMessage.value = `已添加 ${missing.length || yaml.split('\n\n').length} 个媒体库配置模板`
    titleConfigValidationValid.value = true
    scheduleTitleConfigValidation()
  } catch (error) {
    console.warn('append title config templates failed', error)
    titleConfigValidationMessage.value = '获取媒体库模板失败，请确认媒体服务器可用'
    titleConfigValidationValid.value = false
  } finally {
    titleTemplateLoading.value = false
  }
}

function scheduleTitleConfigValidation() {
  if (titleConfigValidationTimer !== null && typeof window !== 'undefined') {
    window.clearTimeout(titleConfigValidationTimer)
  }
  if (typeof window === 'undefined' || titleConfigComposing.value) return
  titleConfigValidationTimer = window.setTimeout(() => {
    void validateTitleConfig(false)
  }, 500)
}

function onTitleConfigCompositionEnd() {
  titleConfigComposing.value = false
  scheduleTitleConfigValidation()
}

function onTitleConfigCompositionStart() {
  titleConfigComposing.value = true
  titleConfigValidationRevision += 1
  if (titleConfigValidationTimer !== null && typeof window !== 'undefined') {
    window.clearTimeout(titleConfigValidationTimer)
    titleConfigValidationTimer = null
  }
}

watch(titleConfigEditorText, () => {
  if (suppressTitleConfigEditorWatch) return
  titleConfigEditorDirty.value = true
  titleConfigValidationMessage.value = ''
  scheduleTitleConfigValidation()
})

watch(() => config.value.title_config_strict, scheduleTitleConfigValidation)

async function loadDynamicLibraryOptions() {
  optionsLoading.value = true
  try {
    const resp = await props.api.get<{ code: number; data?: StatusPayload; msg?: string }>(
      'plugin/YahahaCoverStudio/status',
    )
    if (!resp || resp.code !== 0 || !resp.data) return

    if (Array.isArray(resp.data.all_libraries) && resp.data.all_libraries.length) {
      config.value.all_libraries = resp.data.all_libraries
    }
    if (Array.isArray(resp.data.all_servers)) {
      config.value.all_servers = resp.data.all_servers
    }
    isGenerating.value = Boolean(resp.data.is_generating)
    generationCurrent.value = Number(resp.data.generation_current || 0)
    generationTotal.value = Number(resp.data.generation_total || 0)
    generationLabel.value = String(resp.data.generation_label || '')
    if (isGenerating.value) {
      startGenerationStatusPoller()
    } else {
      stopGenerationStatusPoller()
    }
    if ((!Array.isArray(config.value.selected_servers) || !config.value.selected_servers.length)
      && Array.isArray(resp.data.selected_servers)) {
      config.value.selected_servers = resp.data.selected_servers
    }
    if ((!Array.isArray(config.value.include_libraries) || !config.value.include_libraries.length)
      && Array.isArray(resp.data.include_libraries)) {
      config.value.include_libraries = resp.data.include_libraries
    }
  } catch (e) {
    console.error('loadDynamicLibraryOptions failed', e)
  } finally {
    optionsLoading.value = false
  }
}

function ensureConfigFontFace(item: FontLibraryItem) {
  const url = item.url || item.dataUrl
  if (!url || typeof FontFace === 'undefined' || typeof document === 'undefined') return Promise.resolve()
  const name = getTemplateFontFaceName(item.value)
  const cacheKey = `${name}:${url}`
  const cached = loadedConfigFontUrls.get(cacheKey)
  if (cached) return cached
  const pending = new FontFace(name, `url(${url})`).load()
    .then((font) => {
      document.fonts.add(font)
    })
    .catch((error) => {
      console.warn('load custom font failed', error)
    })
    .then(() => undefined)
  loadedConfigFontUrls.set(cacheKey, pending)
  return pending
}

function getCustomFontFamily(item: FontLibraryItem) {
  void ensureConfigFontFace(item)
  return `${getTemplateFontFaceName(item.value)}, var(--mcr-font-body)`
}

async function loadFontLibrary() {
  fontLibraryLoading.value = true
  try {
    const resp = await props.api.get<{ code: number; data?: { custom?: FontLibraryItem[] }; msg?: string }>('plugin/YahahaCoverStudio/fonts')
    if (!resp || resp.code !== 0) {
      throw new Error(resp?.msg || 'load fonts failed')
    }
    customFontItems.value = Array.isArray(resp.data?.custom) ? resp.data.custom : []
    await Promise.all(customFontItems.value.map((item) => ensureConfigFontFace(item)))
  } catch (error) {
    console.warn('load font library failed', error)
  } finally {
    fontLibraryLoading.value = false
  }
}

async function loadBackupLibrary() {
  backupListLoading.value = true
  try {
    const resp = await props.api.get<{ code: number; data?: BackupItem[]; msg?: string }>('plugin/YahahaCoverStudio/backups')
    if (!resp || resp.code !== 0) {
      throw new Error(resp?.msg || 'load backups failed')
    }
    backupItems.value = Array.isArray(resp.data) ? resp.data : []
  } catch (error) {
    console.warn('load backup library failed', error)
  } finally {
    backupListLoading.value = false
  }
}

function openFontFilePicker() {
  fontFileInputEl.value?.click()
}

function openBackupFilePicker() {
  backupFileInputEl.value?.click()
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(reader.error || new Error('read failed'))
    reader.onload = () => resolve(String(reader.result || ''))
    reader.readAsDataURL(file)
  })
}

function bytesToBase64(bytes: Uint8Array) {
  let binary = ''
  const step = 0x8000
  for (let index = 0; index < bytes.length; index += step) {
    binary += String.fromCharCode(...bytes.subarray(index, index + step))
  }
  return window.btoa(binary)
}

async function uploadFontPayload(payload: Record<string, string>) {
  fontLibraryLoading.value = true
  fontUploadMessage.value = ''
  try {
    const resp = await props.api.post<{ code: number; data?: FontLibraryItem; msg?: string }>('plugin/YahahaCoverStudio/upload_font', {
      ...payload,
    })
    if (!resp || resp.code !== 0 || !resp.data?.value) {
      throw new Error(resp?.msg || 'upload font failed')
    }
    customFontItems.value = [
      resp.data,
      ...customFontItems.value.filter((item) => item.value !== resp.data?.value),
    ]
    await ensureConfigFontFace(resp.data)
    void loadFontLibrary()
    fontUploadMessage.value = `已保存字体：${resp.data.name || resp.data.title}`
    return resp.data
  } catch (error) {
    console.warn('upload font failed', error)
    fontUploadMessage.value = error instanceof Error ? error.message : '字体上传失败'
    return null
  } finally {
    fontLibraryLoading.value = false
  }
}

async function uploadFontFile(file: File) {
  fontLibraryLoading.value = true
  fontUploadMessage.value = '正在上传字体...'
  try {
    const bytes = new Uint8Array(await file.arrayBuffer())
    const chunkSize = 384 * 1024
    const total = Math.max(1, Math.ceil(bytes.length / chunkSize))
    const uploadId = `font_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`
    let savedItem: FontLibraryItem | null = null
    for (let index = 0; index < total; index += 1) {
      const chunk = bytes.subarray(index * chunkSize, Math.min(bytes.length, (index + 1) * chunkSize))
      fontUploadMessage.value = `正在上传字体 ${index + 1}/${total}`
      const resp = await props.api.post<{ code: number; data?: (Partial<FontLibraryItem> & { done?: boolean }); msg?: string }>(
        'plugin/YahahaCoverStudio/upload_font',
        {
          upload_id: uploadId,
          name: file.name,
          chunk_index: String(index),
          chunk_total: String(total),
          chunk_data: bytesToBase64(chunk),
        },
      )
      if (!resp || resp.code !== 0) {
        throw new Error(resp?.msg || 'upload font failed')
      }
      if (resp.data?.done && resp.data.value) {
        savedItem = resp.data as FontLibraryItem
      }
    }
    if (!savedItem) {
      throw new Error('字体上传未完成')
    }
    customFontItems.value = [
      savedItem,
      ...customFontItems.value.filter((item) => item.value !== savedItem?.value),
    ]
    await ensureConfigFontFace(savedItem)
    await loadFontLibrary()
    fontUploadMessage.value = `已保存字体：${savedItem.name || savedItem.title}`
  } catch (error) {
    console.warn('upload font failed', error)
    fontUploadMessage.value = error instanceof Error ? error.message : '字体上传失败'
  } finally {
    fontLibraryLoading.value = false
  }
}

async function uploadFontUrl() {
  const url = fontUrlInput.value.trim()
  if (!url) return
  const imported = await uploadFontPayload({
    url,
    name: decodeURIComponent(url.split('/').pop()?.split('?')[0] || 'font'),
  })
  if (imported) {
    fontUrlInput.value = ''
  }
}

function onFontFileInputChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (file) {
    void uploadFontFile(file)
  }
}

async function deleteFontItem(item: FontLibraryItem) {
  try {
    const resp = await props.api.post<{ code: number; msg?: string }>(
      `plugin/YahahaCoverStudio/delete_font?file=${encodeURIComponent(item.value || item.path || item.name)}`,
    )
    if (!resp || resp.code !== 0) {
      throw new Error(resp?.msg || 'delete font failed')
    }
    customFontItems.value = customFontItems.value.filter((candidate) => candidate.value !== item.value)
    if (config.value.main_title_font_preset === item.value) config.value.main_title_font_preset = defaults.main_title_font_preset
    if (config.value.subtitle_font_preset === item.value) config.value.subtitle_font_preset = defaults.subtitle_font_preset
    if (config.value.custom_text_font_preset === item.value) config.value.custom_text_font_preset = defaults.custom_text_font_preset
    void loadFontLibrary()
  } catch (error) {
    console.warn('delete font failed', error)
  }
}

function fontDisplayName(item: FontLibraryItem) {
  return String(item.title || item.name || '').replace(/\.[^.]+$/, '')
}

async function renameFontItem(item: FontLibraryItem) {
  if (fontLibraryLoading.value) return
  const currentName = fontDisplayName(item)
  const nextName = typeof window !== 'undefined'
    ? window.prompt('重命名字体', currentName)
    : currentName
  const trimmedName = String(nextName || '').trim()
  if (!trimmedName || trimmedName === currentName) return
  fontLibraryLoading.value = true
  fontUploadMessage.value = ''
  try {
    const resp = await props.api.post<{ code: number; data?: FontLibraryItem; msg?: string }>('plugin/YahahaCoverStudio/rename_font', {
      value: item.value,
      path: item.path,
      name: item.name,
      new_name: trimmedName,
    })
    if (!resp || resp.code !== 0 || !resp.data) {
      throw new Error(resp?.msg || 'rename font failed')
    }
    if (config.value.main_title_font_preset === item.value) config.value.main_title_font_preset = resp.data.value
    if (config.value.subtitle_font_preset === item.value) config.value.subtitle_font_preset = resp.data.value
    if (config.value.custom_text_font_preset === item.value) config.value.custom_text_font_preset = resp.data.value
    fontUploadMessage.value = `已重命名字体：${resp.data.title}`
    await loadFontLibrary()
  } catch (error) {
    console.warn('rename font failed', error)
    fontUploadMessage.value = error instanceof Error ? error.message : '字体重命名失败'
  } finally {
    fontLibraryLoading.value = false
  }
}

function startGenerationStatusPoller() {
  if (generationStatusTimer !== null || typeof window === 'undefined') return
  generationStatusTimer = window.setInterval(() => {
    void loadDynamicLibraryOptions()
  }, 2000)
}

function stopGenerationStatusPoller() {
  if (generationStatusTimer === null || typeof window === 'undefined') return
  window.clearInterval(generationStatusTimer)
  generationStatusTimer = null
}

type ConfigTab = 'basic-tab' | 'title-tab'

const tab = ref<ConfigTab>('basic-tab')
const tabItems: { title: string; value: ConfigTab; icon: string }[] = [
  { title: '配置', value: 'basic-tab', icon: 'mdi-view-dashboard-outline' },
  { title: '标题', value: 'title-tab', icon: 'mdi-format-title' },
]

const mainTitleFontItems = computed(() => {
  const items = [...BUILTIN_FONT_ITEMS, ...customFontItems.value.map((item) => ({ title: `自定义 ${item.title}`, value: item.value }))]
  if (config.value.main_title_font_preset && !items.some((item) => item.value === config.value.main_title_font_preset)) {
    items.push({ title: config.value.main_title_font_preset, value: config.value.main_title_font_preset })
  }
  return items
})

const subtitleFontItems = computed(() => {
  const items = [...BUILTIN_FONT_ITEMS, ...customFontItems.value.map((item) => ({ title: `自定义 ${item.title}`, value: item.value }))]
  if (config.value.subtitle_font_preset && !items.some((item) => item.value === config.value.subtitle_font_preset)) {
    items.push({ title: config.value.subtitle_font_preset, value: config.value.subtitle_font_preset })
  }
  if (config.value.custom_text_font_preset && !items.some((item) => item.value === config.value.custom_text_font_preset)) {
    items.push({ title: config.value.custom_text_font_preset, value: config.value.custom_text_font_preset })
  }
  return items
})

const libraryItems = computed(() => {
  const all = (config.value as any).all_libraries as
    | { name: string; value: string; server?: string; server_id?: string }[]
    | undefined
  if (!Array.isArray(all)) return []
  const selected = new Set((config.value.selected_servers || []).map(String))
  const normalized = all.map((lib) => {
    const separator = String(lib.name || '').indexOf(':')
    const server = String(lib.server_id || lib.server || (separator >= 0 ? lib.name.slice(0, separator) : '')).trim()
    const name = separator >= 0 ? String(lib.name).slice(separator + 1).trim() : String(lib.name || '')
    return { ...lib, server, libraryName: name }
  })
  const visible = selected.size ? normalized.filter((lib) => selected.has(lib.server)) : normalized
  const showServer = selected.size !== 1
  return visible.map((lib) => ({
    title: showServer && lib.server ? `${lib.server} - ${lib.libraryName}` : lib.libraryName,
    value: String(lib.value),
  }))
})

const schemeItems = computed(() => {
  const builtin = [
    { title: '风格 1', value: 'static_1' }, { title: '风格 2', value: 'static_2' }, { title: '风格 3', value: 'static_3' }, { title: '风格 4', value: 'static_4' },
    { title: '动态风格 1', value: 'animated_1' }, { title: '动态风格 2', value: 'animated_2' }, { title: '动态风格 3', value: 'animated_3' }, { title: '动态风格 4', value: 'animated_4' },
  ]
  const custom = Array.isArray(config.value.custom_static_layouts) ? config.value.custom_static_layouts.map((item) => ({ title: String(item.name || '自定义方案'), value: String(item.id) })) : []
  return [...builtin, ...custom].filter((item, index, list) => list.findIndex((candidate) => candidate.value === item.value) === index)
})
const allSchemeLibraryItems = computed(() => ((config.value.all_libraries || []) as any[]).map((library) => ({ title: library.server ? `${library.server} - ${library.name}` : String(library.name || library.value), value: String(library.value || `${library.server_id || library.server || ''}:${library.id || library.name || ''}`) })))
function addSchemeRule() { const rules = Array.isArray(config.value.library_scheme_rules) ? [...config.value.library_scheme_rules] : []; rules.push({ id: `rule_${Date.now().toString(36)}`, scheme_id: String(config.value.default_scheme_id || 'static_1'), library_keys: [] }); config.value.library_scheme_rules = rules }
function removeSchemeRule(index: number) { const rules = Array.isArray(config.value.library_scheme_rules) ? [...config.value.library_scheme_rules] : []; rules.splice(index, 1); config.value.library_scheme_rules = rules }
function ruleLibraryItems(index: number) { const current = new Set((config.value.library_scheme_rules?.[index]?.library_keys || []).map(String)); const occupied = new Set((config.value.library_scheme_rules || []).flatMap((rule, ruleIndex) => ruleIndex === index ? [] : (rule.library_keys || []).map(String))); return allSchemeLibraryItems.value.filter((item) => current.has(item.value) || !occupied.has(item.value)) }

const serverItems = computed(() => {
  const items: { title: string; value: string }[] = []
  const seen = new Set<string>()
  const allServers = (config.value as any).all_servers
  if (Array.isArray(allServers) && allServers.length) {
    for (const item of allServers) {
      const value = typeof item === 'object' && item !== null
        ? String(item.value ?? item.title ?? item.name ?? '')
        : String(item ?? '')
      const title = typeof item === 'object' && item !== null
        ? String(item.title ?? item.name ?? item.value ?? value)
        : value
      if (value && !seen.has(value)) {
        seen.add(value)
        items.push({ title, value })
      }
    }
  }
  return items
})

const selectedServerValues = computed(() => new Set(serverItems.value.map((item) => item.value)))
const selectedLibraryValues = computed(() => new Set(libraryItems.value.map((item) => item.value)))
watch([serverItems, () => config.value.selected_servers], () => {
  const allowed = selectedServerValues.value
  if (!allowed.size || !Array.isArray(config.value.selected_servers)) return
  const filtered = config.value.selected_servers.filter((item) => allowed.has(String(item)))
  if (filtered.length !== config.value.selected_servers.length) config.value.selected_servers = filtered
}, { deep: true, immediate: true })
watch([libraryItems, () => config.value.include_libraries], () => {
  if (!Array.isArray(config.value.include_libraries)) return
  const filtered = config.value.include_libraries.filter((item) => selectedLibraryValues.value.has(String(item)))
  if (filtered.length !== config.value.include_libraries.length) config.value.include_libraries = filtered
}, { deep: true, immediate: true })

const titleConfigReference = `媒体库名称:
  title: "主标题"
  subtitle: "副标题"
  background: "#5f7185"
  texts:
    slogan: "自定义文本"
    note: "备注文本"
    any_key: "任意自定义文本"

# texts 下的 slogan / note / any_key 都不是固定变量名，可以随意命名。
# 在画布编辑的文字图层中选择「按媒体库配置」，并在「配置文本键」填写同名键即可。`

const titlePlaceholder = titleConfigReference

const selectedCustomTemplateId = ref<string | null>(
  (config.value.custom_static_active_id as string | null) ?? null,
)

const prefersDark = ref(false)
const hostThemeVersion = ref(0)
let configThemeMediaQuery: MediaQueryList | null = null
let configThemeObserver: MutationObserver | null = null

function readExplicitHostTheme() {
  if (typeof document === 'undefined') return ''
  const root = document.documentElement
  const body = document.body
  if (
    root.classList.contains('dark') ||
    body?.classList.contains('v-theme--dark') ||
    root.getAttribute('data-theme') === 'dark' ||
    body?.getAttribute('data-theme') === 'dark'
  ) {
    return 'dark'
  }
  if (
    root.classList.contains('light') ||
    body?.classList.contains('v-theme--light') ||
    root.getAttribute('data-theme') === 'light' ||
    body?.getAttribute('data-theme') === 'light'
  ) {
    return 'light'
  }
  return ''
}

function syncSystemTheme(event?: MediaQueryListEvent) {
  if (event) {
    prefersDark.value = event.matches
    return
  }
  prefersDark.value = typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-color-scheme: dark)').matches
}

const isDark = computed(() => {
  hostThemeVersion.value
  const explicitTheme = readExplicitHostTheme()
  return explicitTheme === 'dark' || prefersDark.value
})

function createLayoutId() {
  return `layout_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`
}

function cloneLayout(layout: CustomStaticLayout): CustomStaticLayout {
  return {
    version: layout.version,
    layers: layout.layers.map((layer) => ({ ...layer })),
  }
}

function getCustomTemplates(): CustomStaticLayoutTemplate[] {
  return (config.value.custom_static_layouts as CustomStaticLayoutTemplate[] | null) || []
}

function setCustomTemplates(list: CustomStaticLayoutTemplate[]) {
  config.value.custom_static_layouts = list
}

const customTemplateItems = computed(() =>
  getCustomTemplates().map((tpl) => ({
    title: tpl.name,
    value: tpl.id,
  })),
)

function createDefaultLayout(): CustomStaticLayout {
  const width = 1920
  const height = 1080
  const imageWidth = width * 0.6
  const imageHeight = height * 0.8

  return {
    version: 1,
    layers: [
      {
        id: createLayoutId(),
        type: 'image',
        sourceIndex: 1,
        x: width * 0.35,
        y: height * 0.1,
        width: imageWidth,
        height: imageHeight,
        rotation: 0,
        radius: 32,
        zIndex: 1,
      },
      {
        id: createLayoutId(),
        type: 'main_title',
        x: width * 0.05,
        y: height * 0.25,
        width: width * 0.3,
        height: height * 0.2,
        rotation: 0,
        radius: 0,
        zIndex: 2,
        fontSize: 180,
      },
      {
        id: createLayoutId(),
        type: 'subtitle',
        x: width * 0.05,
        y: height * 0.5,
        width: width * 0.3,
        height: height * 0.15,
        rotation: 0,
        radius: 0,
        zIndex: 2,
        fontSize: 75,
      },
    ],
  }
}

function ensureCustomTemplateInitialized() {
  if (config.value.cover_style_base !== 'custom_static') return

  const list = getCustomTemplates()

  if (!list.length) {
    const baseLayout: CustomStaticLayout =
      (config.value.custom_static_layout as CustomStaticLayout | null) ||
      createDefaultLayout()
    const id = createLayoutId()
    const tpl: CustomStaticLayoutTemplate = {
      id,
      name: '默认方案',
      layout: cloneLayout(baseLayout),
      baseStyle: config.value.cover_style_base || 'static_1',
    }
    setCustomTemplates([tpl])
    selectedCustomTemplateId.value = id
    config.value.custom_static_active_id = id
    config.value.custom_static_layout = cloneLayout(baseLayout)
    return
  }

  if (!selectedCustomTemplateId.value) {
    const id = config.value.custom_static_active_id || list[0].id
    selectedCustomTemplateId.value = id
    config.value.custom_static_active_id = id
  }

  if (!config.value.custom_static_layout) {
    const current =
      list.find((tpl) => tpl.id === selectedCustomTemplateId.value) || list[0]
    config.value.custom_static_layout = cloneLayout(current.layout)
  }
}

watch(
  () => config.value.cover_style_base,
  (base) => {
    if (base === 'custom_static') {
      ensureCustomTemplateInitialized()
    }
  },
  { immediate: true },
)

watch(selectedCustomTemplateId, (id) => {
  config.value.custom_static_active_id = id
  if (!id) return
  const list = getCustomTemplates()
  const tpl = list.find((t) => t.id === id)
  if (tpl) {
    config.value.custom_static_layout = cloneLayout(tpl.layout)
  }
})

onMounted(() => {
  if (typeof window !== 'undefined') {
    configAutoSaveEnabled.value = Boolean(config.value.auto_save_config)
    config.value.auto_save_config = configAutoSaveEnabled.value
    syncSystemTheme()
    configThemeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    configThemeMediaQuery.addEventListener?.('change', syncSystemTheme)
  }
  if (typeof document !== 'undefined') {
    configThemeObserver = new MutationObserver(() => {
      hostThemeVersion.value += 1
    })
    configThemeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class', 'data-theme'],
    })
    if (document.body) {
      configThemeObserver.observe(document.body, {
        attributes: true,
        attributeFilter: ['class', 'data-theme'],
      })
    }
  }
  void loadDynamicLibraryOptions()
  void loadFontLibrary()
  void loadBackupLibrary()
  void validateTitleConfig(false)
  nextTick(() => {
    suppressConfigAutoSave = false
  })
})

onBeforeUnmount(() => {
  stopGenerationStatusPoller()
  if (titleConfigValidationTimer !== null && typeof window !== 'undefined') {
    window.clearTimeout(titleConfigValidationTimer)
  }
  if (configAutoSaveTimer !== null && typeof window !== 'undefined') {
    window.clearTimeout(configAutoSaveTimer)
    configAutoSaveTimer = null
  }
  if (configSaveMessageTimer !== null && typeof window !== 'undefined') {
    window.clearTimeout(configSaveMessageTimer)
    configSaveMessageTimer = null
  }
  configThemeMediaQuery?.removeEventListener?.('change', syncSystemTheme)
  configThemeObserver?.disconnect()
  configThemeMediaQuery = null
  configThemeObserver = null
})

function createTemplateFromCurrent() {
  const baseLayout: CustomStaticLayout =
    (config.value.custom_static_layout as CustomStaticLayout | null) ||
    createDefaultLayout()
  const id = createLayoutId()
  const list = getCustomTemplates()
  const tpl: CustomStaticLayoutTemplate = {
    id,
    name: `方案 ${list.length + 1}`,
    layout: cloneLayout(baseLayout),
    baseStyle: config.value.cover_style_base || 'static_1',
  }
  setCustomTemplates([...list, tpl])
  selectedCustomTemplateId.value = id
  config.value.custom_static_layout = cloneLayout(baseLayout)
}

function duplicateActiveTemplate() {
  const id = selectedCustomTemplateId.value
  if (!id) return
  const list = getCustomTemplates()
  const original = list.find((t) => t.id === id)
  if (!original) return
  const newId = createLayoutId()
  const tpl: CustomStaticLayoutTemplate = {
    id: newId,
    name: `${original.name} 副本`,
    layout: cloneLayout(original.layout),
    baseStyle: original.baseStyle,
  }
  setCustomTemplates([...list, tpl])
  selectedCustomTemplateId.value = newId
}

function renameActiveTemplate() {
  const id = selectedCustomTemplateId.value
  if (!id) return
  const list = getCustomTemplates()
  const index = list.findIndex((t) => t.id === id)
  if (index === -1) return
  const current = list[index]
  const newName = window.prompt('请输入方案名称', current.name)
  if (!newName) return
  const next = [...list]
  next[index] = { ...current, name: newName }
  setCustomTemplates(next)
}

function deleteActiveTemplate() {
  const id = selectedCustomTemplateId.value
  if (!id) return
  const list = getCustomTemplates()
  const next = list.filter((t) => t.id !== id)
  setCustomTemplates(next)

  if (!next.length) {
    selectedCustomTemplateId.value = null
    config.value.custom_static_active_id = null
    config.value.custom_static_layout = null
    return
  }

  const nextActive = next[0]
  selectedCustomTemplateId.value = nextActive.id
  config.value.custom_static_active_id = nextActive.id
  config.value.custom_static_layout = cloneLayout(nextActive.layout)
}

function onLayoutUpdated(layoutValue: CustomStaticLayout) {
  config.value.custom_static_layout = layoutValue
  const id = selectedCustomTemplateId.value
  if (!id) return
  const list = getCustomTemplates()
  const index = list.findIndex((t) => t.id === id)
  if (index === -1) return
  const next = [...list]
  next[index] = { ...next[index], layout: cloneLayout(layoutValue) }
  setCustomTemplates(next)
}

function readConfigAutoSavePreference() {
  if (typeof window === 'undefined') return false
  return window.localStorage.getItem(CONFIG_AUTO_SAVE_KEY) === '1'
}

function writeConfigAutoSavePreference(value: boolean) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(CONFIG_AUTO_SAVE_KEY, value ? '1' : '0')
}

function toggleConfigAutoSave() {
  configAutoSaveEnabled.value = !configAutoSaveEnabled.value
  writeConfigAutoSavePreference(configAutoSaveEnabled.value)
  if (configAutoSaveEnabled.value) scheduleConfigAutoSave(200)
}

function onConfigAutoSaveSwitch(value: boolean | null) {
  configAutoSaveEnabled.value = Boolean(value)
  config.value.auto_save_config = configAutoSaveEnabled.value
  if (configAutoSaveEnabled.value) scheduleConfigAutoSave(200)
}

function scheduleConfigAutoSave(delay = 1200) {
  configAutoSaveEnabled.value = Boolean(config.value.auto_save_config)
  if (!configAutoSaveEnabled.value || suppressConfigAutoSave || configSaving.value || typeof window === 'undefined') return
  if (configAutoSaveTimer !== null) window.clearTimeout(configAutoSaveTimer)
  configAutoSaveTimer = window.setTimeout(() => {
    configAutoSaveTimer = null
    void saveConfig({ auto: true })
  }, delay)
}

function showConfigSaveMessage(message: string) {
  configSaveMessage.value = message
  if (typeof window === 'undefined') return
  if (configSaveMessageTimer !== null) window.clearTimeout(configSaveMessageTimer)
  configSaveMessageTimer = window.setTimeout(() => {
    configSaveMessage.value = ''
    configSaveMessageTimer = null
  }, 2600)
}

async function saveConfig(options: { auto?: boolean } = {}) {
  if (configSaving.value) return false
  configSaving.value = true
  const titleConfigOk = await validateTitleConfig(true)
  if (!titleConfigOk) {
    if (!options.auto) tab.value = 'title-tab'
    configSaving.value = false
    return false
  }
  try {
    config.value.update_now = false
    config.value.main_title_font_custom = ''
    config.value.subtitle_font_custom = ''
    config.value.custom_text_font_custom = ''
    config.value.backup_enabled = Boolean(String(config.value.backup_cron || '').trim())
    if (config.value.transfer_monitor && config.value.lock_latest_sort) {
      config.value.sort_by = 'DateCreated'
    }
    const resp = await props.api.post<{ code: number; data?: { config?: Partial<YahahaCoverStudioConfig> }; msg?: string }>(
      'plugin/YahahaCoverStudio/save_config',
      config.value,
    )
    if (!resp || resp.code !== 0) {
      throw new Error(resp?.msg || '保存配置失败')
    }
    if (resp.data?.config) {
      suppressConfigAutoSave = true
      config.value = {
        ...defaults,
        ...normalizeConfigInput(resp.data.config),
        title_config: titleConfigEditorText.value,
      }
      titleConfigEditorDirty.value = false
      nextTick(() => {
        suppressConfigAutoSave = false
      })
    }
    showConfigSaveMessage(options.auto ? '已自动保存' : '已保存')
    return true
  } catch (error) {
    console.warn('save config failed', error)
    showConfigSaveMessage(error instanceof Error ? error.message : '保存配置失败')
    return false
  } finally {
    if (typeof window !== 'undefined') {
      window.setTimeout(() => {
        configSaving.value = false
      }, 420)
    } else {
      configSaving.value = false
    }
  }
}

function initializePluginConfig() {
  if (typeof window !== 'undefined') {
    const confirmed = window.confirm('初始化插件会将当前表单恢复为默认配置，已上传字体、备份、历史封面和图片目录文件不会被删除。保存配置后生效。')
    if (!confirmed) return
  }
  const current = config.value
  config.value = {
    ...defaults,
    all_servers: current.all_servers || [],
    all_libraries: current.all_libraries || [],
    page_tab: current.page_tab || defaults.page_tab,
    custom_static_layout: current.custom_static_layout ?? defaults.custom_static_layout,
    custom_static_layouts: current.custom_static_layouts ?? defaults.custom_static_layouts,
    custom_static_active_id: current.custom_static_active_id ?? defaults.custom_static_active_id,
  }
  backupResult.value = '已恢复默认配置，点击保存配置后生效'
  tab.value = 'basic-tab'
}

function resolveRequestedCoverStyle() {
  const base = config.value.cover_style_base || 'static_1'
  if (base === 'custom_static') return 'custom_static'
  const suffix = String(base).split('_')[1] || '1'
  return config.value.cover_style_variant === 'animated' ? `animated_${suffix}` : `static_${suffix}`
}

async function startGeneration() {
  if (generatingNow.value || isGenerating.value) return
  generatingNow.value = true
  try {
    config.value.update_now = false
    const style = resolveRequestedCoverStyle()
    const resp = await props.api.post<{ code: number; msg?: string }>(
      `plugin/YahahaCoverStudio/start_generation?style=${encodeURIComponent(style)}`,
    )
    if (resp && resp.code !== 0) {
      throw new Error(resp.msg || 'start_generation failed')
    }
    isGenerating.value = true
    generationCurrent.value = 0
    generationTotal.value = 0
    generationLabel.value = '准备生成'
    startGenerationStatusPoller()
    await loadDynamicLibraryOptions()
  } catch (e) {
    console.error('config start_generation failed', e)
  } finally {
    generatingNow.value = false
  }
}

async function stopGeneration() {
  if (generatingNow.value) return
  generatingNow.value = true
  try {
    const resp = await props.api.post<{ code: number; msg?: string }>(
      'plugin/YahahaCoverStudio/stop_generation',
    )
    if (resp && resp.code !== 0) {
      throw new Error(resp.msg || 'stop_generation failed')
    }
    await loadDynamicLibraryOptions()
  } catch (e) {
    console.error('config stop_generation failed', e)
  } finally {
    generatingNow.value = false
  }
}

async function handleGenerateAction() {
  if (isGenerating.value) {
    await stopGeneration()
    return
  }
  await startGeneration()
}

function notifySwitch() {
  emit('switch')
}

function notifyClose() {
  emit('close')
}

async function onCleanImages() {
  if (cacheAction.value) return
  cacheAction.value = 'images'
  try {
    await props.api.post('plugin/YahahaCoverStudio/clean_images')
  } catch (e) {
    console.error('clean_images failed', e)
  } finally {
    cacheAction.value = ''
  }
}

async function onCleanFonts() {
  if (cacheAction.value) return
  cacheAction.value = 'fonts'
  try {
    await props.api.post('plugin/YahahaCoverStudio/clean_fonts')
  } catch (e) {
    console.error('clean_fonts failed', e)
  } finally {
    cacheAction.value = ''
  }
}

async function onBackupConfig() {
  if (cacheAction.value) return
  cacheAction.value = 'backup'
  backupResult.value = ''
  try {
    const resp = await props.api.post<{ code: number; data?: { path?: string }; msg?: string }>(
      'plugin/YahahaCoverStudio/backup_config',
      { backup_path: config.value.backup_path || '' },
    )
    if (!resp || resp.code !== 0) {
      throw new Error(resp?.msg || 'backup_config failed')
    }
    backupResult.value = resp.data?.path ? `已备份到 ${resp.data.path}` : '已完成备份'
    await loadBackupLibrary()
  } catch (e) {
    console.error('backup_config failed', e)
    backupResult.value = '备份失败，请检查路径权限'
  } finally {
    cacheAction.value = ''
  }
}

function downloadConfigBinaryPayload(
  payload: { name?: string; mime?: string; b64?: string } | undefined,
  fallbackName: string,
) {
  if (!payload?.b64 || typeof window === 'undefined') {
    throw new Error('download payload missing')
  }
  const binary = window.atob(payload.b64)
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index)
  }
  const blob = new Blob([bytes], { type: payload.mime || 'application/json' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = payload.name || fallbackName
  anchor.rel = 'noopener'
  anchor.style.position = 'fixed'
  anchor.style.left = '-9999px'
  anchor.style.top = '0'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

async function downloadBackupItem(item: BackupItem) {
  try {
    const backupKey = encodeURIComponent(item.path || item.name)
    const resp = await props.api.post<{
      code: number
      data?: { name?: string; mime?: string; b64?: string }
      msg?: string
    }>(`plugin/YahahaCoverStudio/download_backup?file=${backupKey}`)
    if (!resp || resp.code !== 0) {
      throw new Error(resp?.msg || 'download_backup failed')
    }
    downloadConfigBinaryPayload(resp.data, item.name || 'yahahacoverstudio_backup.json')
  } catch (error) {
    console.warn('download backup failed', error)
    backupResult.value = '下载备份失败'
  }
}

async function uploadBackupFile(file: File) {
  if (cacheAction.value) return
  cacheAction.value = 'backup'
  backupResult.value = ''
  try {
    const dataUrl = await readFileAsDataUrl(file)
    const resp = await props.api.post<{ code: number; data?: BackupItem; msg?: string }>('plugin/YahahaCoverStudio/upload_backup', {
      data_url: dataUrl,
      name: file.name,
    })
    if (!resp || resp.code !== 0) {
      throw new Error(resp?.msg || 'upload_backup failed')
    }
    backupResult.value = '备份文件已上传'
    await loadBackupLibrary()
  } catch (error) {
    console.warn('upload backup failed', error)
    backupResult.value = '上传备份失败'
  } finally {
    cacheAction.value = ''
  }
}

function onBackupFileInputChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (file) {
    void uploadBackupFile(file)
  }
}

async function restoreBackupItem(item: BackupItem) {
  if (cacheAction.value) return
  if (typeof window !== 'undefined' && !window.confirm(`确定从「${item.name}」恢复配置吗？当前配置会被覆盖。`)) return
  cacheAction.value = 'backup'
  backupResult.value = ''
  try {
    const resp = await props.api.post<{ code: number; data?: { config?: Partial<YahahaCoverStudioConfig> }; msg?: string }>(
      `plugin/YahahaCoverStudio/restore_backup?file=${encodeURIComponent(item.path || item.name)}`,
    )
    if (!resp || resp.code !== 0) {
      throw new Error(resp?.msg || 'restore_backup failed')
    }
    if (resp.data?.config) {
      config.value = {
        ...defaults,
        ...normalizeConfigInput(resp.data.config),
      }
    }
    backupResult.value = '配置已恢复'
    await Promise.all([loadDynamicLibraryOptions(), loadFontLibrary(), loadBackupLibrary()])
  } catch (error) {
    console.warn('restore backup failed', error)
    backupResult.value = '恢复备份失败'
  } finally {
    cacheAction.value = ''
  }
}

async function deleteBackupItem(item: BackupItem) {
  if (cacheAction.value) return
  if (typeof window !== 'undefined' && !window.confirm(`删除备份「${item.name}」？`)) return
  cacheAction.value = 'backup'
  backupResult.value = ''
  try {
    const resp = await props.api.post<{ code: number; msg?: string }>(
      `plugin/YahahaCoverStudio/delete_backup?file=${encodeURIComponent(item.path || item.name)}`,
    )
    if (!resp || resp.code !== 0) {
      throw new Error(resp?.msg || 'delete_backup failed')
    }
    backupResult.value = '备份已删除'
    await loadBackupLibrary()
  } catch (error) {
    console.warn('delete backup failed', error)
    backupResult.value = '删除备份失败'
  } finally {
    cacheAction.value = ''
  }
}
</script>

<style scoped>
/* Light settings workbench, scoped to Config.vue only. */
.mcr-config-shell {
  --mcr-config-surface: var(--mcr-color-surface);
  --mcr-config-surface-low: var(--mcr-color-surface-container-low);
  --mcr-config-surface-card: var(--mcr-color-surface-container-lowest);
  --mcr-config-surface-rail: var(--mcr-color-surface-container-lowest);
  --mcr-config-ink: var(--mcr-color-on-surface);
  --mcr-config-muted: var(--mcr-color-on-surface-variant);
  --mcr-config-faint: rgba(var(--mcr-rgb-on-surface-variant), 0.58);
  --mcr-config-primary: var(--mcr-color-primary);
  --mcr-config-primary-bright: var(--mcr-color-primary-container);
  --mcr-config-primary-soft: var(--mcr-color-primary-fixed);
  --mcr-config-border: rgba(var(--mcr-rgb-outline-variant), 0.48);
  --mcr-config-border-strong: rgba(var(--mcr-rgb-primary), 0.22);
  --mcr-config-shadow: 0 18px 44px rgba(var(--mcr-rgb-shadow), 0.08), 0 2px 10px rgba(var(--mcr-rgb-shadow), 0.05);
  --mcr-cream: var(--mcr-config-surface);
  --mcr-charcoal: var(--mcr-config-ink);
  --mcr-off-white: var(--mcr-color-surface-container-lowest);
  --mcr-muted: var(--mcr-config-muted);
  --mcr-border: var(--mcr-config-border);
  --mcr-border-interactive: rgba(var(--mcr-rgb-primary), 0.42);
  --mcr-charcoal-04: rgba(var(--mcr-rgb-primary), 0.06);
  --mcr-charcoal-82: rgba(var(--mcr-rgb-surface-container-low), 0.82);
  overflow: hidden;
  border-radius: 0;
  background:
    radial-gradient(circle at 18% 12%, rgba(var(--mcr-rgb-primary-container), 0.12), transparent 30%),
    radial-gradient(circle at 88% 20%, rgba(var(--mcr-rgb-secondary-container), 0.12), transparent 26%),
    linear-gradient(180deg, var(--mcr-config-surface), var(--mcr-config-surface-low));
  color: var(--mcr-config-ink);
  font-family: var(--mcr-font-body);
}

.mcr-config-shell,
.mcr-config-shell * {
  box-sizing: border-box;
}

.mcr-font-file-input {
  display: none;
}

.mcr-config-section-stack {
  display: grid;
  width: 100%;
  gap: 18px;
}

.mcr-config-section-card {
  scroll-margin-top: 96px;
  position: relative;
  width: 100%;
  min-width: 0;
  padding: 18px;
  border: 1px solid var(--mcr-config-border);
  border-radius: 20px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.66), rgba(255, 255, 255, 0.34)),
    var(--mcr-config-card, var(--mcr-config-surface-card));
  box-shadow: 0 16px 34px rgba(var(--mcr-rgb-shadow), 0.06);
}

.mcr-config-section-card__header {
  display: block;
  margin-bottom: 16px;
}

.mcr-config-section-card__title {
  color: var(--mcr-config-ink);
  font-size: 18px;
  font-weight: 900;
  line-height: 1.25;
}

.mcr-config-section-card__copy {
  margin: 4px 0 0;
  color: var(--mcr-config-muted);
  font-size: 13px;
  font-weight: 650;
  line-height: 1.5;
}

.mcr-form-grid--center {
  align-items: center;
}

.mcr-config-switch-col {
  display: flex;
  align-items: flex-start;
  padding-top: 20px;
}

.mcr-config-switch-col :deep(.v-input) {
  width: 100%;
}

.mcr-config-switch-col--backup {
  padding-top: 20px;
}

.mcr-config-shell .mcr-monitor-grid .mcr-config-switch-col {
  padding-top: 10px;
}

.mcr-config-backup-grid {
  display: grid;
  grid-template-columns: minmax(280px, 1.1fr) minmax(180px, 0.7fr) minmax(220px, 0.8fr);
  align-items: start;
  gap: 14px;
}

.mcr-config-backup-grid--cron-only {
  grid-template-columns: minmax(280px, 1fr) minmax(220px, 0.82fr);
}

.mcr-config-backup-grid__actions {
  grid-column: 1 / -1;
  min-width: 0;
}

.mcr-config-clean-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.mcr-config-clean-action {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--mcr-config-border);
  border-radius: 16px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.7);
}

.mcr-config-clean-action strong {
  display: block;
  color: var(--mcr-config-ink);
  font-size: 14px;
  font-weight: 850;
}

.mcr-config-clean-action span {
  display: block;
  margin-top: 4px;
  color: var(--mcr-config-muted);
  font-size: 12px;
  font-weight: 650;
  line-height: 1.45;
}

.mcr-font-library {
  margin-top: 18px;
  padding: 16px;
  border: 1px solid var(--mcr-config-border);
  border-radius: 18px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.72);
  box-shadow: 0 12px 30px rgba(var(--mcr-rgb-shadow), 0.06);
}

.mcr-font-library__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.mcr-font-library__header-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.mcr-font-library__title {
  margin-top: 2px;
}

.mcr-font-library__import {
  display: block;
  width: 100%;
  min-width: 0;
  margin-bottom: 14px;
}

.mcr-font-link-field {
  display: grid;
  gap: 7px;
  width: 100%;
  min-width: 0;
}

.mcr-font-link-field .mcr-blueprint-field__label {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.72);
  font-size: 12px;
  font-weight: 650;
  line-height: 1.25;
}

.mcr-font-link-field .mcr-blueprint-field__hint {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.58);
  font-size: 11px;
  line-height: 1.45;
}

.mcr-font-link-field__control {
  position: relative;
  display: block;
  width: 100%;
  min-width: 0;
}

.mcr-font-link-field__input {
  display: block;
  width: 100%;
  min-height: 42px;
  box-sizing: border-box;
  padding-right: 54px !important;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.70);
  border-radius: 12px;
  outline: none;
  background: var(--mcr-color-surface-container-lowest);
  color: var(--mcr-color-on-surface);
  caret-color: var(--mcr-color-primary-container);
  font: inherit;
  font-size: 13px;
  line-height: 1.45;
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease,
    background-color 180ms ease;
}

.mcr-font-link-field__input:focus {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.74);
  box-shadow: 0 0 0 4px rgba(var(--mcr-rgb-primary-container), 0.11);
}

.mcr-font-link-field__download {
  position: absolute;
  top: 50%;
  right: 7px;
  display: inline-grid;
  width: 32px;
  height: 32px;
  place-items: center;
  transform: translateY(-50%) scale(0.92);
  border: 1px solid rgba(var(--color-rgb-primary), 0.22);
  border-radius: 10px;
  background: rgba(var(--color-rgb-primary), 0.10);
  color: var(--color-primary);
  cursor: pointer;
  opacity: 0.78;
  box-shadow:
    0 10px 22px rgba(var(--color-rgb-primary), 0.18),
    0 3px 8px var(--color-shadow),
    inset 0 1px 0 rgba(255, 255, 255, 0.42);
  animation: mcr-font-download-pop 220ms cubic-bezier(0.16, 1, 0.3, 1) both;
  transition:
    opacity 180ms ease,
    transform 180ms ease,
    border-color 160ms ease,
    background-color 160ms ease,
    box-shadow 180ms ease,
    color 160ms ease;
}

.mcr-font-link-field__download:hover {
  transform: translateY(-56%) scale(1.04);
  border-color: rgba(var(--color-rgb-primary), 0.36);
  background: var(--color-primary);
  color: #fff;
  opacity: 1;
  box-shadow:
    0 14px 28px rgba(var(--color-rgb-primary), 0.24),
    0 6px 16px var(--color-shadow);
}

.mcr-font-link-field__download:disabled {
  cursor: progress;
  opacity: 0.62;
}

@keyframes mcr-font-download-pop {
  from {
    opacity: 0;
    transform: translateY(-44%) scale(0.74);
  }
  to {
    opacity: 0.78;
    transform: translateY(-50%) scale(0.92);
  }
}

.mcr-font-library__listbar {
  display: flex;
  justify-content: flex-end;
  margin: 2px 0 10px;
}

.mcr-config-collapse-button {
  display: inline-flex;
  min-height: 34px;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 7px 10px;
  border: 1px solid var(--mcr-config-border);
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.8);
  color: var(--mcr-config-muted);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
  transition:
    border-color 180ms ease,
    color 180ms ease,
    background-color 180ms ease;
}

.mcr-config-collapse-button:hover {
  border-color: rgba(var(--mcr-rgb-primary), 0.28);
  background: var(--mcr-config-primary-soft);
  color: var(--mcr-config-primary);
}

.mcr-font-library__empty {
  display: grid;
  min-height: 72px;
  place-items: center;
  border: 1px dashed var(--mcr-config-border);
  border-radius: 14px;
  color: var(--mcr-config-muted);
  font-size: 13px;
}

.mcr-font-library__status {
  margin-top: 10px;
  color: var(--mcr-config-muted);
  font-size: 12px;
  font-weight: 750;
  overflow-wrap: anywhere;
}

.mcr-title-config-toolbar {
  display: grid;
  grid-template-columns: 190px minmax(0, 1fr);
  align-items: center;
  gap: 10px 14px;
  margin: 8px 0 12px;
}

.mcr-title-config-heading {
  display: flex;
  min-height: 40px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.mcr-title-config-toolbar :deep(.v-switch) {
  width: 190px;
  min-width: 190px;
}

.mcr-title-config-toolbar .mcr-title-config-mode {
  min-width: 240px;
}

.mcr-title-config-mode {
  color: var(--mcr-config-muted);
  font-size: 12px;
  font-weight: 750;
}

.mcr-title-config-template-btn {
  margin-left: auto;
}

.mcr-title-config-alert {
  position: absolute;
  z-index: 3;
  right: 12px;
  bottom: 12px;
  max-width: min(420px, calc(100% - 24px));
  padding: 8px 10px;
  border: 1px solid rgba(var(--mcr-rgb-error), 0.28);
  border-radius: 12px;
  background: rgba(var(--mcr-rgb-error), 0.1);
  color: var(--mcr-color-error);
  font-size: 12px;
  font-weight: 780;
  overflow-wrap: anywhere;
}

.mcr-title-config-editor-shell {
  position: relative;
}

.mcr-title-config-alert--ok {
  border-color: rgba(var(--mcr-rgb-success), 0.28);
  background: rgba(var(--mcr-rgb-success), 0.1);
  color: var(--mcr-color-success);
}

.mcr-title-config-reference {
  margin-top: 12px;
  padding: 12px;
  border: 1px solid rgba(var(--mcr-rgb-outline), 0.16);
  border-radius: 14px;
  background: rgba(var(--mcr-rgb-surface-container-low), 0.72);
}

.mcr-title-config-reference__label {
  margin-bottom: 8px;
  color: var(--mcr-config-muted);
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.mcr-title-config-reference pre {
  margin: 0;
  white-space: pre-wrap;
  color: var(--mcr-config-ink);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  line-height: 1.55;
}

.mcr-font-library__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 10px;
}

.mcr-font-item {
  position: relative;
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 10px 70px 10px 10px;
  border: 1px solid var(--mcr-config-border);
  border-radius: 14px;
  background: var(--mcr-color-surface);
  color: var(--mcr-config-ink);
  text-align: left;
  box-shadow: 0 8px 20px rgba(var(--mcr-rgb-shadow), 0.06);
  cursor: pointer;
}

.mcr-font-item__sample {
  display: grid;
  width: 48px;
  height: 36px;
  place-items: center;
  border-radius: 10px;
  background: var(--mcr-color-primary-fixed);
  color: var(--mcr-color-on-primary-fixed);
  font-size: 16px;
  font-weight: 800;
}

.mcr-font-item__name {
  min-width: 0;
  overflow: hidden;
  color: var(--mcr-config-muted);
  font-size: 12px;
  font-weight: 750;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcr-font-item__rename,
.mcr-font-item__delete {
  position: absolute;
  top: 50%;
  display: inline-grid;
  width: 26px;
  height: 26px;
  place-items: center;
  border: 0;
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-error), 0.12);
  color: var(--mcr-color-error);
  transform: translateY(-50%);
  cursor: pointer;
}

.mcr-font-item__rename {
  right: 38px;
  background: rgba(var(--mcr-rgb-primary), 0.12);
  color: var(--mcr-config-primary);
}

.mcr-font-item__delete {
  right: 8px;
}

.mcr-config-backup-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
}

.mcr-config-backup-result {
  min-width: 0;
  color: var(--mcr-config-muted);
  font-size: 12px;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.mcr-backup-library {
  margin-top: 14px;
}

.mcr-backup-library__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}

.mcr-backup-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 11px 10px 11px 12px;
  border: 1px solid var(--mcr-config-border);
  border-radius: 14px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.76);
  box-shadow: 0 10px 22px rgba(var(--mcr-rgb-shadow), 0.05);
}

.mcr-backup-item__main {
  min-width: 0;
}

.mcr-backup-item__name {
  min-width: 0;
  overflow: hidden;
  color: var(--mcr-config-ink);
  font-size: 13px;
  font-weight: 820;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcr-backup-item__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 3px;
  color: var(--mcr-config-muted);
  font-size: 11px;
  font-weight: 700;
}

.mcr-backup-item__actions {
  display: inline-flex;
  gap: 6px;
}

.mcr-backup-item__actions button {
  display: inline-grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border: 1px solid var(--mcr-config-border);
  border-radius: 10px;
  background: var(--mcr-color-surface);
  color: var(--mcr-config-primary);
  cursor: pointer;
  transition:
    transform 160ms ease,
    border-color 160ms ease,
    background-color 160ms ease;
}

.mcr-backup-item__actions button:hover {
  transform: translateY(-1px);
  border-color: rgba(var(--mcr-rgb-primary), 0.28);
  background: rgba(var(--mcr-rgb-primary), 0.08);
}

.mcr-backup-item__actions .mcr-backup-item__danger {
  color: var(--mcr-color-error);
}

.mcr-config-shell :deep(.mcr-shell__aurora) {
  opacity: 0.34;
  background:
    radial-gradient(ellipse at 18% 14%, rgba(var(--mcr-rgb-primary-container), 0.16), transparent 42%),
    radial-gradient(ellipse at 78% 18%, rgba(var(--mcr-rgb-secondary-container), 0.14), transparent 34%),
    radial-gradient(ellipse at 58% 92%, rgba(var(--mcr-rgb-primary), 0.08), transparent 46%);
}

.mcr-config-shell :deep(.mcr-shell__noise) {
  opacity: 0.42;
  background-image:
    linear-gradient(rgba(var(--mcr-rgb-primary), 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--mcr-rgb-primary), 0.035) 1px, transparent 1px);
  background-size: 24px 24px;
  mask-image: linear-gradient(180deg, rgba(var(--mcr-rgb-shadow), 0.62), transparent 78%);
}

.mcr-config-shell :deep(.mcr-frame),
.mcr-config-shell :deep(.mcr-frame__body),
.mcr-config-shell :deep(.mcr-footer-actions),
.mcr-config-shell :deep(.v-card),
.mcr-config-shell :deep(.v-card-text),
.mcr-config-shell :deep(.v-card-actions),
.mcr-config-shell :deep(.v-window),
.mcr-config-shell :deep(.v-window-item) {
  background-color: transparent !important;
}

.mcr-config-app {
  position: relative;
  z-index: 1;
  min-height: min(100dvh, 920px);
  background: var(--mcr-config-surface-low);
}

.mcr-config-topbar {
  min-height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 0 clamp(18px, 3vw, 48px);
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.94);
  border-bottom: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.68);
  backdrop-filter: blur(18px);
}

.mcr-config-brand,
.mcr-config-topbar__meta {
  display: inline-flex;
  align-items: center;
  min-width: 0;
}

.mcr-config-brand {
  gap: 14px;
}

.mcr-config-brand__name {
  color: var(--mcr-config-primary);
  font-size: clamp(1.2rem, 2vw, 1.5rem);
  line-height: 1;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.mcr-config-brand__divider {
  width: 1px;
  height: 18px;
  background: rgba(var(--mcr-rgb-outline-variant), 0.72);
}

.mcr-config-brand__section,
.mcr-config-topbar__meta {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.62);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.mcr-config-topbar__meta {
  gap: 9px;
  white-space: nowrap;
}

.mcr-config-top-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-left: 4px;
}

.mcr-config-generate {
  min-height: 34px !important;
  margin-left: 8px;
  padding-inline: 14px !important;
}

.mcr-config-save-group {
  position: relative;
  display: inline-flex;
  align-items: stretch;
  min-height: 34px;
  margin-left: 2px;
  border: 1px solid var(--mcr-button-border, var(--mcr-config-border));
  border-radius: 12px;
  overflow: visible;
  background: var(--mcr-button-white, var(--mcr-config-surface-card));
  box-shadow: var(--mcr-button-shadow, 0 8px 18px rgba(var(--mcr-rgb-shadow), 0.08));
}

.mcr-config-save-group :deep(.mcr-config-save-button) {
  min-height: 32px !important;
  border: 0 !important;
  border-radius: 11px 0 0 11px !important;
  box-shadow: none !important;
}

.mcr-config-save-mode {
  display: inline-grid;
  min-width: 62px;
  place-items: center;
  border: 0;
  border-left: 1px solid var(--mcr-config-border);
  border-radius: 0 11px 11px 0;
  background: rgba(var(--mcr-rgb-surface-container-low), 0.82);
  color: var(--mcr-config-muted);
  cursor: pointer;
  font: inherit;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.04em;
  transition:
    background-color 180ms ease,
    color 180ms ease;
}

.mcr-config-save-group--auto .mcr-config-save-mode {
  background: var(--mcr-config-primary-soft);
  color: var(--mcr-config-primary);
}

.mcr-config-save-message {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  z-index: 4;
  max-width: 150px;
  padding: 4px 8px;
  overflow: hidden;
  border: 1px solid rgba(var(--mcr-rgb-primary), 0.14);
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.94);
  color: var(--mcr-config-muted);
  box-shadow: 0 8px 18px rgba(var(--mcr-rgb-shadow), 0.08);
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0;
  line-height: 1.15;
  text-overflow: ellipsis;
  text-transform: none;
  white-space: nowrap;
  pointer-events: none;
}

.mcr-config-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--mcr-color-primary-container);
  box-shadow: 0 0 0 5px rgba(var(--mcr-rgb-primary-container), 0.12);
}

.mcr-config-status-dot--off {
  background: var(--mcr-color-tertiary-container);
  box-shadow: 0 0 0 5px rgba(var(--mcr-rgb-tertiary-container), 0.12);
}

.mcr-config-workspace {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr);
  min-height: calc(min(100dvh, 920px) - 64px);
}

.mcr-config-sidebar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 24px 12px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.92);
  border-right: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.72);
}

.mcr-config-sidebar__label {
  padding-bottom: 4px;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.42);
  font-size: 9px;
  font-weight: 900;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.mcr-config-nav {
  width: 100%;
  min-height: 66px;
  display: grid;
  place-items: center;
  gap: 5px;
  padding: 9px 4px;
  border: 1px solid transparent;
  border-radius: 14px;
  background: transparent;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.62);
  cursor: pointer;
  font: inherit;
  font-size: 11px;
  font-weight: 750;
  line-height: 1.1;
  transition:
    transform 180ms ease,
    background-color 180ms ease,
    border-color 180ms ease,
    color 180ms ease;
}

.mcr-config-nav:hover {
  transform: translateY(-1px);
  background: rgba(var(--mcr-rgb-primary), 0.055);
  color: var(--mcr-config-primary);
}

.mcr-config-nav--active {
  background: rgba(var(--mcr-rgb-primary), 0.07);
  border-color: rgba(var(--mcr-rgb-primary), 0.12);
  color: var(--mcr-config-primary);
}

.mcr-config-sidebar__spacer {
  flex: 1 1 auto;
}

.mcr-config-nav:active,
.mcr-config-shell :deep(.mcr-button:active) {
  transform: translateY(1px) scale(0.99);
}

.mcr-config-main {
  min-width: 0;
  padding: clamp(16px, 2.4vw, 32px) clamp(20px, 3vw, 48px);
  padding-bottom: 36px;
  overflow: auto;
}

.mcr-config-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  max-width: 1180px;
  margin: 0 auto 14px;
  min-height: 0;
  padding: 2px 2px 0;
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
}

.mcr-config-hero::before {
  display: none;
}

.mcr-config-shell :deep(.mcr-panel__eyebrow) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.54);
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.mcr-config-shell :deep(.mcr-title) {
  max-width: 420px;
  margin: 0;
  color: var(--mcr-config-ink);
  font-size: clamp(2rem, 3.2vw, 3rem);
  line-height: 1.02;
  font-weight: 850;
  letter-spacing: -0.035em;
  text-wrap: balance;
}

.mcr-config-shell :deep(.mcr-panel__copy),
.mcr-config-shell :deep(.mcr-hero-card__meta) {
  max-width: 65ch;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.74);
  font-size: 0.95rem;
  line-height: 1.68;
  text-wrap: pretty;
}

.mcr-config-tags {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
  min-width: 0;
}

.mcr-config-tag {
  display: inline-flex;
  align-items: baseline;
  gap: 7px;
  min-height: 30px;
  padding: 7px 10px;
  border-radius: 10px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.74);
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.78);
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.68);
  font-size: 11px;
  font-weight: 750;
  line-height: 1;
}

.mcr-config-tag strong {
  max-width: 140px;
  overflow: hidden;
  color: var(--mcr-config-primary);
  font-size: 12px;
  font-weight: 850;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcr-config-shell :deep(.mcr-panel),
.mcr-config-shell :deep(.mcr-config-clean-grid > * > *) {
  border-radius: 18px !important;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.9) !important;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.74) !important;
  box-shadow: var(--mcr-config-shadow) !important;
}

.mcr-config-tabbody {
  box-sizing: border-box;
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
  padding: clamp(20px, 2.2vw, 28px) !important;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.78);
  border-radius: 24px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.94) !important;
  box-shadow: var(--mcr-config-shadow);
}

.mcr-config-shell :deep(.mcr-panel__title) {
  color: var(--mcr-config-ink);
  font-size: 1.35rem;
  font-weight: 850;
  letter-spacing: -0.02em;
}

.mcr-config-copy {
  margin-bottom: 20px;
}

.mcr-config-shell :deep(.mcr-alert) {
  border-radius: 16px !important;
  background: rgba(var(--mcr-rgb-primary-fixed), 0.32) !important;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.2) !important;
  color: rgba(var(--mcr-rgb-on-primary), 0.88) !important;
  box-shadow: none !important;
}

.mcr-config-shell :deep(.mcr-form-grid > * > *),
.mcr-config-editor {
  border-radius: 14px;
  background: transparent;
  border: none;
  padding: 0;
}

.mcr-config-shell :deep(.mcr-blueprint-field),
.mcr-config-shell :deep(.mcr-blueprint-select) {
  gap: 8px;
  color: var(--mcr-config-ink);
  font-family: inherit;
}

.mcr-config-shell :deep(.mcr-blueprint-field__label),
.mcr-config-shell :deep(.mcr-blueprint-select__label) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.78);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.02em;
  text-transform: none;
}

.mcr-config-shell :deep(.mcr-blueprint-field__control),
.mcr-config-shell :deep(.mcr-blueprint-select__control) {
  min-height: 46px;
  padding: 11px 13px;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.62);
  border-radius: 14px;
  background: var(--mcr-color-surface-container-lowest);
  background-image: none;
  color: var(--mcr-config-ink);
  box-shadow: 0 0 0 rgba(var(--mcr-rgb-primary), 0);
  font-family: inherit;
  font-size: 14px;
  line-height: 1.45;
}

.mcr-config-shell :deep(.mcr-blueprint-select__control) {
  padding-right: 40px;
}

.mcr-config-shell :deep(.mcr-blueprint-field__control::placeholder) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.42);
}

.mcr-config-shell :deep(.mcr-blueprint-field__control:focus),
.mcr-config-shell :deep(.mcr-blueprint-select__control:focus) {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.74);
  background-color: var(--mcr-color-surface-container-lowest);
  box-shadow: 0 0 0 4px rgba(var(--mcr-rgb-primary-container), 0.11);
}

.mcr-config-shell :deep(.mcr-blueprint-select__shell::after) {
  border-color: rgba(var(--mcr-rgb-on-surface-variant), 0.68);
}

.mcr-config-shell :deep(.mcr-blueprint-select__control option) {
  background: var(--mcr-color-surface-container-lowest);
  color: var(--mcr-config-ink);
}

.mcr-config-shell :deep(.mcr-blueprint-select__control option:checked) {
  background: var(--mcr-config-primary-soft);
  color: var(--mcr-config-ink);
}

.mcr-config-shell :deep(.mcr-blueprint-field__hint),
.mcr-config-shell :deep(.mcr-blueprint-select__hint) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.56);
  font-size: 12px;
  line-height: 1.45;
}

.mcr-config-shell :deep(.mcr-blueprint-select__clear) {
  border-radius: 10px;
  border-color: rgba(var(--mcr-rgb-primary-container), 0.22);
  background: rgba(var(--mcr-rgb-primary-fixed), 0.32);
  color: var(--mcr-config-primary);
}

.mcr-config-editor :deep(.mcr-blueprint-field__control--textarea) {
  min-height: 420px;
  font-family: 'SFMono-Regular', ui-monospace, Consolas, 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.68;
}

.mcr-config-shell :deep(.v-switch) {
  min-height: 50px;
  padding: 5px 10px;
  border-radius: 14px;
  background: var(--mcr-color-surface-container-lowest);
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.82);
  box-shadow: 0 1px 2px rgba(var(--mcr-rgb-shadow), 0.04);
  transition:
    border-color 180ms ease,
    background-color 180ms ease,
    box-shadow 180ms ease,
    transform 180ms ease;
}

.mcr-config-shell :deep(.v-switch:hover) {
  transform: translateY(-1px);
  border-color: rgba(var(--mcr-rgb-primary-container), 0.34);
  box-shadow: 0 10px 22px rgba(var(--mcr-rgb-shadow), 0.07);
}

.mcr-config-shell :deep(.v-switch .v-selection-control) {
  min-height: 38px;
  display: flex;
  flex-direction: row-reverse;
  justify-content: space-between;
  gap: 12px;
}

.mcr-config-shell :deep(.v-switch .v-selection-control__wrapper) {
  flex: 0 0 auto;
}

.mcr-config-shell :deep(.v-switch .v-label) {
  flex: 1 1 auto;
  min-width: 0;
  padding-inline-start: 0;
  color: var(--mcr-color-on-surface) !important;
  font-size: 13px;
  font-weight: 800;
}

.mcr-config-shell :deep(.v-switch__track) {
  width: 42px;
  height: 24px;
  background-color: var(--mcr-color-on-surface) !important;
  opacity: 1;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.7);
  transition: background-color 180ms ease, border-color 180ms ease;
}

.mcr-config-shell :deep(.v-selection-control--dirty .v-switch__track) {
  background-color: var(--mcr-config-primary-bright) !important;
  border-color: var(--mcr-config-primary-bright);
}

.mcr-config-shell :deep(.v-switch__thumb) {
  width: 18px;
  height: 18px;
  background: var(--mcr-color-surface-container-lowest) !important;
  color: var(--mcr-color-surface-container-lowest) !important;
  box-shadow: 0 2px 7px rgba(var(--mcr-rgb-shadow), 0.18);
}

.mcr-config-shell :deep(.v-selection-control--dirty .v-switch__thumb) {
  box-shadow: 0 2px 8px rgba(var(--mcr-rgb-primary), 0.22);
}

.mcr-config-shell :deep(.v-label),
.mcr-config-shell :deep(.v-field-label),
.mcr-config-shell :deep(.v-input__details),
.mcr-config-shell :deep(.v-selection-control .v-label),
.mcr-config-shell :deep(.v-select__selection-text),
.mcr-config-shell :deep(.v-field__input),
.mcr-config-shell :deep(.v-field input),
.mcr-config-shell :deep(.v-field textarea) {
  color: var(--mcr-config-ink) !important;
  -webkit-text-fill-color: var(--mcr-config-ink) !important;
}

.mcr-config-shell :deep(.v-messages__message) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.58);
}

.mcr-divider {
  margin: 24px 0 !important;
  border-color: rgba(var(--mcr-rgb-surface-container-highest), 0.86) !important;
}

.mcr-config-maintenance-title {
  margin-bottom: 14px;
}

.mcr-config-clean-copy {
  margin-bottom: 18px;
}

.mcr-config-shell :deep(.mcr-button) {
  min-height: 42px !important;
  border-radius: 13px !important;
  padding: 8px 18px !important;
  font-size: 14px !important;
  font-weight: 800 !important;
  transition:
    transform 180ms ease,
    filter 180ms ease,
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease;
}

.mcr-config-shell :deep(.mcr-button:hover) {
  opacity: 1;
  transform: translateY(-1px);
}

.mcr-config-shell :deep(.mcr-button--primary),
.mcr-config-shell :deep(.mcr-button--active),
.mcr-config-shell :deep(.mcr-tab--active) {
  background: var(--mcr-config-primary) !important;
  color: var(--mcr-color-surface-container-lowest) !important;
  border-color: var(--mcr-config-primary) !important;
  box-shadow: 0 14px 24px rgba(var(--mcr-rgb-primary), 0.16) !important;
}

.mcr-config-shell :deep(.mcr-button--ghost) {
  background: var(--mcr-color-surface-container-lowest) !important;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.82) !important;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.72) !important;
  box-shadow: none !important;
}

.mcr-config-shell :deep(.mcr-button--danger) {
  background: var(--mcr-color-tertiary-container) !important;
  color: var(--mcr-color-surface-container-lowest) !important;
  border-color: var(--mcr-color-tertiary-container) !important;
}

.mcr-config-shell :deep(.mcr-footer-actions) {
  position: sticky;
  z-index: 4;
  bottom: 0;
  gap: 12px;
  padding: 18px clamp(18px, 3vw, 48px) !important;
  background: rgba(var(--mcr-rgb-surface), 0.84) !important;
  border-top: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.78);
  backdrop-filter: blur(18px);
}

.mcr-config-shell :deep(.mcr-focusable:focus-visible),
.mcr-config-shell :deep(.mcr-button:focus-visible),
.mcr-config-nav:focus-visible {
  outline: none;
  box-shadow: 0 0 0 4px rgba(var(--mcr-rgb-primary-container), 0.16) !important;
}

html.dark .mcr-config-shell,
.v-theme--dark .mcr-config-shell,
.mcr-config-shell[data-mcr-theme="dark"] {
  --mcr-config-surface: var(--mcr-color-surface);
  --mcr-config-surface-low: var(--mcr-color-surface-container-lowest);
  --mcr-config-card: rgba(var(--mcr-rgb-surface-container-low), 0.88);
  --mcr-config-card-soft: rgba(var(--mcr-rgb-surface-container), 0.92);
  --mcr-config-ink: var(--mcr-color-on-surface);
  --mcr-config-muted: var(--mcr-color-on-surface-variant);
  --mcr-config-faint: rgba(var(--mcr-rgb-on-surface-variant), 0.62);
  --mcr-config-primary: var(--mcr-color-primary-container);
  --mcr-config-primary-bright: var(--mcr-color-primary-container);
  --mcr-config-primary-soft: rgba(var(--mcr-rgb-primary-container), 0.16);
  --mcr-config-border: rgba(var(--mcr-rgb-outline-variant), 0.86);
  --mcr-config-border-strong: rgba(var(--mcr-rgb-primary-container), 0.46);
  --mcr-config-shadow: 0 18px 44px rgba(var(--mcr-rgb-shadow), 0.34);
  --mcr-cream: var(--mcr-color-surface);
  --mcr-charcoal: var(--mcr-color-on-surface);
  --mcr-off-white: var(--mcr-color-surface-container-lowest);
  --mcr-muted: var(--mcr-color-on-surface-variant);
  --mcr-border: rgba(var(--mcr-rgb-outline-variant), 0.86);
  --mcr-border-interactive: rgba(var(--mcr-rgb-primary-container), 0.56);
  --mcr-charcoal-04: rgba(var(--mcr-rgb-primary-container), 0.10);
  --mcr-charcoal-82: rgba(var(--mcr-rgb-surface-container-highest), 0.82);
  background:
    radial-gradient(circle at 18% 12%, rgba(var(--mcr-rgb-primary-container), 0.10), transparent 30%),
    radial-gradient(circle at 86% 18%, rgba(var(--mcr-rgb-tertiary), 0.08), transparent 28%),
    var(--mcr-color-surface);
  color: var(--mcr-color-on-surface);
}

html.dark .mcr-config-shell :deep(.mcr-shell__aurora),
.v-theme--dark .mcr-config-shell :deep(.mcr-shell__aurora) {
  opacity: 0.18;
}

html.dark .mcr-config-shell :deep(.mcr-shell__noise),
.v-theme--dark .mcr-config-shell :deep(.mcr-shell__noise) {
  opacity: 0.16;
  background-image: none;
}

html.dark .mcr-config-app,
.v-theme--dark .mcr-config-app,
html.dark .mcr-config-topbar,
.v-theme--dark .mcr-config-topbar,
html.dark .mcr-config-sidebar,
.v-theme--dark .mcr-config-sidebar,
html.dark .mcr-config-panel,
.v-theme--dark .mcr-config-panel,
html.dark .mcr-config-tabbody,
.v-theme--dark .mcr-config-tabbody,
html.dark .mcr-config-card,
.v-theme--dark .mcr-config-card {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.86) !important;
  background: rgba(var(--mcr-rgb-surface-container-low), 0.88) !important;
  color: var(--mcr-color-on-surface) !important;
  box-shadow: 0 18px 44px rgba(var(--mcr-rgb-shadow), 0.30) !important;
}

html.dark .mcr-config-shell :deep(.mcr-button--primary),
html.dark .mcr-config-shell :deep(.mcr-button--active),
html.dark .mcr-config-shell :deep(.mcr-tab--active),
.v-theme--dark .mcr-config-shell :deep(.mcr-button--primary),
.v-theme--dark .mcr-config-shell :deep(.mcr-button--active),
.v-theme--dark .mcr-config-shell :deep(.mcr-tab--active) {
  background: var(--mcr-color-primary-container) !important;
  border-color: var(--mcr-color-primary-container) !important;
  color: var(--mcr-color-on-primary) !important;
  box-shadow: 0 14px 24px rgba(var(--mcr-rgb-primary-container), 0.20) !important;
}

html.dark .mcr-config-shell :deep(.mcr-button--ghost),
.v-theme--dark .mcr-config-shell :deep(.mcr-button--ghost) {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.92) !important;
  background: rgba(var(--mcr-rgb-surface-container), 0.92) !important;
  color: var(--mcr-color-on-surface-variant) !important;
}

html.dark .mcr-config-shell :deep(.v-switch__track),
.v-theme--dark .mcr-config-shell :deep(.v-switch__track) {
  background-color: var(--mcr-color-on-surface) !important;
  border-color: var(--mcr-color-outline-variant) !important;
}

html.dark .mcr-config-shell :deep(.v-selection-control--dirty .v-switch__track),
.v-theme--dark .mcr-config-shell :deep(.v-selection-control--dirty .v-switch__track) {
  background-color: var(--mcr-color-primary-container) !important;
  border-color: var(--mcr-color-primary-container) !important;
}

html.dark .mcr-config-shell :deep(.v-switch__thumb),
.v-theme--dark .mcr-config-shell :deep(.v-switch__thumb) {
  background: var(--mcr-color-surface-container-highest) !important;
  color: var(--mcr-color-on-primary) !important;
}

html.dark .mcr-config-shell :deep(.mcr-blueprint-field__control),
html.dark .mcr-config-shell :deep(.mcr-blueprint-select__control),
html.dark .mcr-config-shell :deep(.mcr-blueprint-select__multi-option),
.v-theme--dark .mcr-config-shell :deep(.mcr-blueprint-field__control),
.v-theme--dark .mcr-config-shell :deep(.mcr-blueprint-select__control),
.v-theme--dark .mcr-config-shell :deep(.mcr-blueprint-select__multi-option) {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.92) !important;
  background: var(--mcr-color-surface-container-lowest) !important;
  color: var(--mcr-color-on-surface) !important;
  -webkit-text-fill-color: var(--mcr-color-on-surface) !important;
}

html.dark .mcr-config-shell :deep(.mcr-blueprint-select__multi-option--active),
.v-theme--dark .mcr-config-shell :deep(.mcr-blueprint-select__multi-option--active) {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.72) !important;
  background: rgba(var(--mcr-rgb-primary-container), 0.14) !important;
  color: var(--mcr-color-primary) !important;
  -webkit-text-fill-color: var(--mcr-color-primary) !important;
  box-shadow: inset 3px 0 0 var(--mcr-color-primary-container) !important;
}

html.dark .mcr-config-shell :deep(.mcr-footer-actions),
.v-theme--dark .mcr-config-shell :deep(.mcr-footer-actions) {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.86) !important;
  background: rgba(var(--mcr-rgb-surface), 0.86) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] {
  --mcr-config-surface: var(--mcr-color-surface);
  --mcr-config-surface-low: var(--mcr-color-surface-container-lowest);
  --mcr-config-surface-card: var(--mcr-color-surface-container-low);
  --mcr-config-surface-rail: var(--mcr-color-surface-container-lowest);
  --mcr-config-ink: var(--mcr-color-on-surface);
  --mcr-config-muted: var(--mcr-color-on-surface-variant);
  --mcr-config-faint: rgba(var(--mcr-rgb-on-surface-variant), 0.62);
  --mcr-config-primary: var(--mcr-color-primary-container);
  --mcr-config-primary-bright: var(--mcr-color-primary-container);
  --mcr-config-primary-soft: rgba(var(--mcr-rgb-primary-container), 0.16);
  --mcr-config-border: rgba(var(--mcr-rgb-outline-variant), 0.86);
  --mcr-config-border-strong: rgba(var(--mcr-rgb-primary-container), 0.46);
  background:
    radial-gradient(circle at 18% 12%, rgba(var(--mcr-rgb-primary-container), 0.10), transparent 30%),
    radial-gradient(circle at 86% 18%, rgba(var(--mcr-rgb-tertiary), 0.08), transparent 28%),
    var(--mcr-depth-0) !important;
  color: var(--mcr-color-on-surface) !important;
  font-family: var(--mcr-font-body);
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-app,
.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-topbar,
.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-sidebar,
.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-tabbody,
.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-frame),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-panel),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-card),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-card-text),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-window),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-window-item) {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.86) !important;
  background: rgba(var(--mcr-rgb-surface-container-low), 0.88) !important;
  background-color: rgba(var(--mcr-rgb-surface-container-low), 0.88) !important;
  color: var(--mcr-color-on-surface) !important;
  box-shadow: var(--mcr-depth-shadow-1) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-main {
  background: transparent !important;
  color: var(--mcr-color-on-surface) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-title,
.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-brand__name,
.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-panel__title),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-label),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-field-label),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-selection-control .v-label) {
  color: var(--mcr-color-on-surface) !important;
  -webkit-text-fill-color: var(--mcr-color-on-surface) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-brand__section,
.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-topbar__meta,
.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-sidebar__label,
.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-panel__eyebrow),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-panel__copy),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-input__details),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-messages__message) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.72) !important;
  -webkit-text-fill-color: rgba(var(--mcr-rgb-on-surface-variant), 0.72) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-nav {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.72) !important;
  background: transparent !important;
  color: var(--mcr-color-on-surface-variant) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-nav--active {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.56) !important;
  background: rgba(var(--mcr-rgb-primary-container), 0.14) !important;
  color: var(--mcr-color-primary) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-tag,
.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-alert) {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.86) !important;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.72) !important;
  color: var(--mcr-color-on-surface-variant) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-divider),
.mcr-config-shell[data-mcr-theme="dark"] .mcr-divider {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.86) !important;
  opacity: 1 !important;
}

@media (prefers-color-scheme: dark) {
  .mcr-config-shell {
    --mcr-config-surface: var(--mcr-color-surface);
    --mcr-config-surface-low: var(--mcr-color-surface-container-lowest);
    --mcr-config-surface-card: var(--mcr-color-surface-container-low);
    --mcr-config-surface-rail: var(--mcr-color-surface-container-lowest);
    --mcr-config-ink: var(--mcr-color-on-surface);
    --mcr-config-muted: var(--mcr-color-on-surface-variant);
    --mcr-config-faint: rgba(var(--mcr-rgb-on-surface-variant), 0.62);
    --mcr-config-primary: var(--mcr-color-primary-container);
    --mcr-config-primary-bright: var(--mcr-color-primary-container);
    --mcr-config-primary-soft: rgba(var(--mcr-rgb-primary-container), 0.16);
    --mcr-config-border: rgba(var(--mcr-rgb-outline-variant), 0.86);
    --mcr-config-border-strong: rgba(var(--mcr-rgb-primary-container), 0.46);
  }
}

/* Clean colorful config skin aligned with the shared theme tokens. */
.mcr-config-shell {
  --mcr-config-surface: var(--color-bg);
  --mcr-config-surface-low: var(--color-surface);
  --mcr-config-surface-card: var(--color-surface);
  --mcr-config-surface-rail: var(--color-surface);
  --mcr-config-card: var(--color-surface);
  --mcr-config-card-soft: var(--color-surface-soft);
  --mcr-config-ink: var(--color-text-main);
  --mcr-config-muted: var(--color-text-secondary);
  --mcr-config-faint: var(--color-text-muted);
  --mcr-config-primary: var(--color-primary);
  --mcr-config-primary-bright: var(--color-primary);
  --mcr-config-primary-soft: var(--color-primary-soft);
  --mcr-config-border: var(--color-border);
  --mcr-config-border-strong: rgba(var(--color-rgb-primary), 0.42);
  --mcr-config-shadow: 0 18px 42px var(--color-shadow);
  background:
    radial-gradient(circle at 12% 8%, rgba(var(--color-rgb-primary), 0.10), transparent 28%),
    radial-gradient(circle at 88% 10%, rgba(var(--color-rgb-secondary), 0.08), transparent 24%),
    linear-gradient(180deg, var(--color-bg), var(--color-surface-soft)) !important;
  color: var(--color-text-main) !important;
}

.mcr-config-shell[data-mcr-theme="dark"],
html.dark .mcr-config-shell,
.v-theme--dark .mcr-config-shell {
  --mcr-config-surface: var(--color-bg);
  --mcr-config-surface-low: var(--color-surface);
  --mcr-config-surface-card: var(--color-surface);
  --mcr-config-surface-rail: var(--color-surface);
  --mcr-config-card: rgba(var(--color-rgb-surface), 0.88);
  --mcr-config-card-soft: rgba(var(--color-rgb-surface-soft), 0.88);
  --mcr-config-ink: var(--color-text-main);
  --mcr-config-muted: var(--color-text-secondary);
  --mcr-config-faint: var(--color-text-muted);
  --mcr-config-primary: var(--color-primary);
  --mcr-config-primary-bright: var(--color-primary);
  --mcr-config-primary-soft: var(--color-primary-soft);
  --mcr-config-border: var(--color-border);
  --mcr-config-border-strong: rgba(var(--color-rgb-primary), 0.54);
  --mcr-config-shadow: 0 18px 44px var(--color-shadow);
  background:
    radial-gradient(circle at 12% 8%, rgba(var(--color-rgb-primary), 0.13), transparent 30%),
    radial-gradient(circle at 88% 10%, rgba(var(--color-rgb-secondary), 0.11), transparent 26%),
    linear-gradient(180deg, var(--color-bg), #111B30) !important;
  color: var(--color-text-main) !important;
}

.mcr-config-app,
.mcr-config-topbar,
.mcr-config-sidebar,
.mcr-config-tabbody,
.mcr-config-card,
.mcr-config-panel,
.mcr-config-shell :deep(.mcr-frame),
.mcr-config-shell :deep(.mcr-panel),
.mcr-config-shell :deep(.v-card),
.mcr-config-shell :deep(.v-card-text),
.mcr-config-shell :deep(.v-window),
.mcr-config-shell :deep(.v-window-item) {
  border-color: var(--color-border) !important;
  background: rgba(var(--color-rgb-surface), 0.94) !important;
  color: var(--color-text-main) !important;
  box-shadow: 0 16px 36px var(--color-shadow) !important;
}

.mcr-config-main {
  background: transparent !important;
  color: var(--color-text-main) !important;
}

.mcr-config-shell .mcr-title,
.mcr-config-brand__name,
.mcr-config-shell :deep(.mcr-panel__title),
.mcr-config-shell :deep(.v-label),
.mcr-config-shell :deep(.v-field-label),
.mcr-config-shell :deep(.v-selection-control .v-label) {
  color: var(--color-text-main) !important;
  -webkit-text-fill-color: var(--color-text-main) !important;
}

.mcr-config-brand__section,
.mcr-config-topbar__meta,
.mcr-config-sidebar__label,
.mcr-config-shell :deep(.mcr-panel__copy),
.mcr-config-shell :deep(.v-input__details),
.mcr-config-shell :deep(.v-messages__message) {
  color: var(--color-text-secondary) !important;
  -webkit-text-fill-color: var(--color-text-secondary) !important;
}

.mcr-config-shell :deep(.mcr-panel__eyebrow) {
  color: var(--color-text-muted) !important;
  -webkit-text-fill-color: var(--color-text-muted) !important;
}

.mcr-config-nav {
  border-color: var(--color-border) !important;
  background: transparent !important;
  color: var(--color-text-secondary) !important;
}

.mcr-config-nav:hover {
  background: var(--color-surface-soft) !important;
  color: var(--color-primary) !important;
}

.mcr-config-nav--active {
  border-color: rgba(var(--color-rgb-primary), 0.36) !important;
  background: var(--color-primary-soft) !important;
  color: var(--color-primary) !important;
}

.mcr-config-shell :deep(.mcr-button--primary),
.mcr-config-shell :deep(.mcr-button--active),
.mcr-config-shell :deep(.mcr-tab--active) {
  border-color: var(--mcr-button-border) !important;
  background: var(--mcr-button-white) !important;
  color: var(--color-primary) !important;
  -webkit-text-fill-color: var(--color-primary) !important;
  box-shadow: var(--mcr-button-shadow) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-button--primary),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-button--active),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-tab--active),
html.dark .mcr-config-shell :deep(.mcr-button--primary),
html.dark .mcr-config-shell :deep(.mcr-button--active),
html.dark .mcr-config-shell :deep(.mcr-tab--active),
.v-theme--dark .mcr-config-shell :deep(.mcr-button--primary),
.v-theme--dark .mcr-config-shell :deep(.mcr-button--active),
.v-theme--dark .mcr-config-shell :deep(.mcr-tab--active) {
  color: var(--color-primary) !important;
  -webkit-text-fill-color: var(--color-primary) !important;
}

.mcr-config-shell :deep(.mcr-button--ghost) {
  border-color: var(--mcr-button-border) !important;
  background: var(--mcr-button-white) !important;
  color: var(--mcr-button-muted) !important;
  -webkit-text-fill-color: var(--mcr-button-muted) !important;
  box-shadow: var(--mcr-button-shadow) !important;
}

.mcr-config-shell :deep(.mcr-button--ghost:hover) {
  border-color: rgba(var(--color-rgb-primary), 0.20) !important;
  background: var(--mcr-button-white) !important;
  color: var(--color-primary) !important;
  -webkit-text-fill-color: var(--color-primary) !important;
  box-shadow: var(--mcr-button-shadow-hover) !important;
}

.mcr-config-shell :deep(.mcr-button--danger) {
  border-color: rgba(var(--color-rgb-danger), 0.18) !important;
  background: var(--mcr-button-white) !important;
  color: var(--color-danger) !important;
  -webkit-text-fill-color: var(--color-danger) !important;
  box-shadow: var(--mcr-button-shadow) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-button--danger),
html.dark .mcr-config-shell :deep(.mcr-button--danger),
.v-theme--dark .mcr-config-shell :deep(.mcr-button--danger) {
  color: var(--color-danger) !important;
  -webkit-text-fill-color: var(--color-danger) !important;
}

.mcr-config-tag,
.mcr-config-shell :deep(.mcr-alert) {
  border-color: rgba(var(--color-rgb-primary), 0.18) !important;
  background: var(--color-primary-soft) !important;
  color: var(--color-primary) !important;
}

.mcr-config-shell :deep(.mcr-blueprint-field__control),
.mcr-config-shell :deep(.mcr-blueprint-select__control),
.mcr-config-shell :deep(.mcr-blueprint-select__popover),
.mcr-config-shell :deep(.mcr-blueprint-select__multi-option),
.mcr-config-shell :deep(.v-field),
.mcr-config-shell :deep(.v-field__overlay) {
  border-color: var(--color-border) !important;
  background: var(--color-surface) !important;
  color: var(--color-text-main) !important;
  -webkit-text-fill-color: var(--color-text-main) !important;
  box-shadow: none !important;
}

.mcr-config-shell :deep(.mcr-blueprint-select__multi-option:hover),
.mcr-config-shell :deep(.mcr-blueprint-select__multi-option--active) {
  border-color: rgba(var(--color-rgb-primary), 0.34) !important;
  background: var(--color-primary-soft) !important;
  color: var(--color-primary) !important;
  -webkit-text-fill-color: var(--color-primary) !important;
}

.mcr-config-shell :deep(.mcr-footer-actions) {
  border-color: var(--color-border) !important;
  background: rgba(var(--color-rgb-bg), 0.84) !important;
  box-shadow: 0 -12px 36px var(--color-shadow) !important;
}

@media (max-width: 959px) {
  .mcr-config-app {
    min-height: 100dvh;
  }

  .mcr-config-topbar {
    min-height: auto;
    align-items: flex-start;
    flex-direction: column;
    padding: 16px;
  }

  .mcr-config-topbar__meta,
  .mcr-config-top-actions {
    width: 100%;
    flex-wrap: wrap;
    justify-content: flex-start;
    white-space: normal;
  }

  .mcr-config-workspace {
    grid-template-columns: 1fr;
    min-height: 0;
  }

  .mcr-config-sidebar {
    position: sticky;
    top: 0;
    z-index: 3;
    flex-direction: row;
    gap: 8px;
    padding: 10px 14px;
    overflow-x: auto;
    border-right: none;
    border-bottom: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.72);
  }

  .mcr-config-sidebar__label,
  .mcr-config-sidebar__spacer {
    display: none;
  }

  .mcr-config-nav {
    min-width: 84px;
    min-height: 48px;
    grid-auto-flow: column;
    grid-template-columns: auto auto;
    gap: 6px;
    padding: 8px 12px;
  }

  .mcr-config-main {
    padding: 16px;
    padding-bottom: 64px;
  }

  .mcr-font-library__import {
    display: block;
  }

  .mcr-font-library__url-btn {
    min-width: 104px;
    width: auto;
    margin-top: 18px;
    margin-bottom: 0;
  }

  .mcr-config-backup-grid {
    grid-template-columns: 1fr;
  }

  .mcr-config-switch-col--backup {
    padding-top: 0;
  }

  .mcr-config-hero {
    display: grid;
    gap: 10px;
    margin-bottom: 12px;
  }

  .mcr-config-tags {
    justify-content: flex-start;
  }

  .mcr-config-tabbody {
    padding: 16px !important;
    border-radius: 18px;
  }

  .mcr-config-editor :deep(.mcr-blueprint-field__control--textarea) {
    min-height: 320px;
  }

  .mcr-config-shell :deep(.mcr-footer-actions) {
    align-items: stretch;
    flex-wrap: wrap;
    padding: 12px 16px !important;
  }
}

/* Final dark button roles must follow all legacy settings button skins above. */
.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--apple-primary:not(.mcr-button--danger)) {
  --v-theme-overlay-multiplier: 0;
  border-color: #0a84ff !important;
  background-color: #0a84ff !important;
  background-image: none !important;
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
  box-shadow:
    0 7px 18px rgba(10, 132, 255, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.22) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--dark-neutral) {
  --v-theme-overlay-multiplier: 0;
  border-color: rgba(230, 236, 245, 0.12) !important;
  background-color: #2a3447 !important;
  background-image: none !important;
  color: #d4dbe8 !important;
  -webkit-text-fill-color: #d4dbe8 !important;
  box-shadow:
    0 7px 18px rgba(0, 0, 0, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--apple-primary:not(.mcr-button--danger) .v-btn__overlay),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--dark-neutral .v-btn__overlay) {
  opacity: 0 !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--apple-primary:not(.mcr-button--danger) .v-btn__content),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--apple-primary:not(.mcr-button--danger) .v-icon) {
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--dark-neutral .v-btn__content),
.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--dark-neutral .v-icon) {
  color: #d4dbe8 !important;
  -webkit-text-fill-color: #d4dbe8 !important;
}

/* Settings fields need near-white content on the deep settings surfaces. */
.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-blueprint-field__control) {
  color: #f5f7fb !important;
  -webkit-text-fill-color: #f5f7fb !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-field__input) {
  color: #f5f7fb !important;
  -webkit-text-fill-color: #f5f7fb !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-field input) {
  color: #f5f7fb !important;
  -webkit-text-fill-color: #f5f7fb !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-field textarea) {
  color: #f5f7fb !important;
  -webkit-text-fill-color: #f5f7fb !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-blueprint-field__control::placeholder) {
  color: #aeb8ca !important;
  -webkit-text-fill-color: #aeb8ca !important;
  opacity: 1 !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-field input::placeholder) {
  color: #aeb8ca !important;
  -webkit-text-fill-color: #aeb8ca !important;
  opacity: 1 !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-field textarea::placeholder) {
  color: #aeb8ca !important;
  -webkit-text-fill-color: #aeb8ca !important;
  opacity: 1 !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-blueprint-field__label) {
  color: #dce2ed !important;
  -webkit-text-fill-color: #dce2ed !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.v-field-label) {
  color: #dce2ed !important;
  -webkit-text-fill-color: #dce2ed !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-config-cache-danger) {
  --v-theme-overlay-multiplier: 0;
  border-color: rgba(255, 107, 107, 0.32) !important;
  background-color: #4a2028 !important;
  background-image: none !important;
  color: #ffb3b3 !important;
  -webkit-text-fill-color: #ffb3b3 !important;
  box-shadow:
    0 7px 18px rgba(26, 4, 8, 0.30),
    inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-config-cache-danger:hover) {
  border-color: rgba(255, 133, 133, 0.52) !important;
  background-color: #5b252f !important;
  color: #ffd0d0 !important;
  -webkit-text-fill-color: #ffd0d0 !important;
  box-shadow:
    0 9px 22px rgba(26, 4, 8, 0.38),
    inset 0 1px 0 rgba(255, 255, 255, 0.07) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-config-cache-danger .v-btn__content) {
  color: inherit !important;
  -webkit-text-fill-color: currentColor !important;
}

.mcr-config-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-config-cache-danger .v-icon) {
  color: inherit !important;
  -webkit-text-fill-color: currentColor !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-section-card {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background:
    linear-gradient(180deg, rgba(30, 42, 66, 0.92), rgba(23, 32, 51, 0.94)),
    var(--color-surface) !important;
  box-shadow: 0 18px 42px rgba(0, 0, 0, 0.24) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-clean-action,
.mcr-config-shell[data-mcr-theme="dark"] .mcr-font-library,
.mcr-config-shell[data-mcr-theme="dark"] .mcr-backup-item,
.mcr-config-shell[data-mcr-theme="dark"] .mcr-font-library__empty {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(15, 23, 42, 0.34) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-font-item {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(30, 42, 66, 0.82) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-save-group {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: #2a3447 !important;
  box-shadow:
    0 7px 18px rgba(0, 0, 0, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-save-group :deep(.mcr-config-save-button) {
  background: transparent !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-save-mode {
  border-left-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(15, 23, 42, 0.34) !important;
  color: #d4dbe8 !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-save-group--auto .mcr-config-save-mode {
  background: rgba(10, 132, 255, 0.18) !important;
  color: #8fc2ff !important;
}

.mcr-config-shell .mcr-config-save-group :deep(.mcr-config-save-button.mcr-button) {
  min-height: 32px !important;
  border: 0 !important;
  border-radius: 11px 0 0 11px !important;
  background: transparent !important;
  box-shadow: none !important;
}

.mcr-config-shell .mcr-config-save-group :deep(.mcr-config-save-button.mcr-button:hover) {
  background: rgba(var(--color-rgb-primary), 0.05) !important;
  box-shadow: none !important;
}

.mcr-config-shell .mcr-config-save-group :deep(.mcr-config-save-button .v-btn__overlay),
.mcr-config-shell .mcr-config-save-group :deep(.mcr-config-save-button .v-btn__underlay) {
  border-radius: 11px 0 0 11px !important;
}

.mcr-config-shell .mcr-config-save-group .mcr-config-save-mode {
  min-width: 72px;
  border-radius: 0 11px 11px 0 !important;
  box-shadow: none !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-save-message {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(30, 42, 66, 0.96) !important;
  color: #d4dbe8 !important;
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.18) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-collapse-button {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(30, 42, 66, 0.78) !important;
  color: #c7d0e3 !important;
}

.mcr-config-shell {
  --yahaha-blue: #1677ff;
  --yahaha-blue-soft: #eef5ff;
  --yahaha-border: #dfe8f6;
  --yahaha-text: #121a2f;
  --yahaha-muted: #5b6b88;
  --yahaha-card: rgba(255, 255, 255, 0.92);
  --yahaha-radius-lg: 22px;
  --yahaha-radius-md: 18px;
}

.mcr-config-shell .mcr-config-topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  min-height: 0;
  align-items: flex-start;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px 16px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--yahaha-border) !important;
  background: rgba(255, 255, 255, 0.86) !important;
  backdrop-filter: blur(14px);
  box-shadow: 0 12px 28px rgba(var(--mcr-rgb-shadow), 0.08);
}

.mcr-config-shell .mcr-config-brand {
  min-height: 34px;
  align-self: start;
  padding-right: 104px;
}

.mcr-config-shell .yh-mobile-title {
  display: none;
  color: var(--yahaha-text);
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0;
  line-height: 1.15;
}

.mcr-config-shell .mcr-config-topbar__meta {
  display: grid;
  justify-items: end;
  gap: 8px;
  min-width: 0;
  white-space: normal;
}

.mcr-config-shell .mcr-config-main-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
  min-width: 0;
}

.mcr-config-shell .mcr-config-top-actions {
  margin-left: 0;
}

.mcr-config-shell .yh-segment {
  display: inline-flex;
  gap: 6px;
  padding: 6px;
  border: 1px solid rgba(223, 232, 246, 0.82);
  border-radius: var(--yahaha-radius-lg);
  background: #eef2f7;
}

.mcr-config-shell .yh-btn,
.mcr-config-shell .yh-segment-item {
  --v-theme-overlay-multiplier: 0;
  min-height: 42px !important;
  height: 42px;
  border-radius: var(--yahaha-radius-md) !important;
  font-weight: 700 !important;
  letter-spacing: 0.02em;
  box-shadow: 0 4px 12px rgba(28, 77, 160, 0.08) !important;
}

.mcr-config-shell .yh-btn-primary {
  border-color: var(--yahaha-blue) !important;
  background: var(--yahaha-blue) !important;
  background-image: none !important;
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
}

.mcr-config-shell .yh-btn-secondary,
.mcr-config-shell .yh-segment-item {
  border: 1px solid var(--yahaha-border) !important;
  background: rgba(255, 255, 255, 0.92) !important;
  background-image: none !important;
  color: var(--yahaha-muted) !important;
  -webkit-text-fill-color: var(--yahaha-muted) !important;
}

.mcr-config-shell .yh-btn-secondary:hover,
.mcr-config-shell .yh-segment-item:hover {
  background: var(--yahaha-blue-soft) !important;
  color: var(--yahaha-blue) !important;
  -webkit-text-fill-color: var(--yahaha-blue) !important;
}

.mcr-config-shell .yh-btn :deep(.v-btn__overlay),
.mcr-config-shell .yh-btn :deep(.v-btn__underlay) {
  opacity: 0 !important;
}

.mcr-config-shell .yh-top-actions {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 30;
  display: flex;
  align-items: center;
  gap: 8px;
}

.mcr-config-shell .mcr-config-top-actions.yh-top-actions {
  padding: 0;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

.mcr-config-shell .yh-icon-btn {
  --v-theme-overlay-multiplier: 0;
  width: 42px !important;
  height: 42px !important;
  min-width: 42px !important;
  padding: 0 !important;
  border: 1px solid var(--yahaha-border) !important;
  border-radius: 16px !important;
  background: rgba(255, 255, 255, 0.92) !important;
  background-image: none !important;
  color: var(--yahaha-muted) !important;
  -webkit-text-fill-color: var(--yahaha-muted) !important;
  box-shadow: 0 4px 12px rgba(28, 77, 160, 0.08) !important;
  backdrop-filter: blur(10px);
  transition:
    transform 140ms ease,
    background-color 160ms ease,
    color 160ms ease,
    box-shadow 160ms ease;
}

.mcr-config-shell .yh-icon-btn:active {
  transform: scale(0.96);
  background: var(--yahaha-blue-soft) !important;
}

.mcr-config-shell .yh-icon-btn:hover {
  background: var(--yahaha-blue-soft) !important;
  color: var(--yahaha-blue) !important;
  -webkit-text-fill-color: var(--yahaha-blue) !important;
}

.mcr-config-shell .yh-icon-btn :deep(.v-btn__overlay),
.mcr-config-shell .yh-icon-btn :deep(.v-btn__underlay) {
  opacity: 0 !important;
}

.mcr-config-shell .yh-save-segment {
  min-height: 42px;
  border-color: var(--yahaha-border) !important;
  border-radius: var(--yahaha-radius-md) !important;
  background: rgba(255, 255, 255, 0.92) !important;
  box-shadow: 0 4px 12px rgba(28, 77, 160, 0.08) !important;
}

.mcr-config-shell .yh-save-segment :deep(.mcr-config-save-button.mcr-button) {
  min-height: 40px !important;
  height: 40px !important;
  border-radius: 17px 0 0 17px !important;
}

.mcr-config-shell .yh-save-segment .mcr-config-save-mode {
  min-height: 40px;
  height: 40px;
  border-radius: 0 17px 17px 0 !important;
  color: var(--yahaha-muted);
}

.mcr-config-shell .mcr-config-top-tabs {
  width: min(320px, 100%);
  justify-self: end;
}

.mcr-config-shell .mcr-config-top-tab {
  flex: 1 1 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 0 !important;
  cursor: pointer;
  font: inherit;
}

.mcr-config-shell .mcr-config-top-tab.is-active {
  border-color: var(--yahaha-blue) !important;
  background: var(--yahaha-blue) !important;
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
}

.mcr-config-shell .mcr-config-sidebar {
  display: none !important;
}

.mcr-config-shell .mcr-config-workspace {
  grid-template-columns: 1fr !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-topbar {
  background: rgba(23, 32, 51, 0.86) !important;
  border-color: rgba(230, 236, 245, 0.12) !important;
  box-shadow: 0 14px 32px rgba(0, 0, 0, 0.24) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .yh-segment {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(15, 23, 42, 0.50) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-top-actions {
  border-color: rgba(230, 236, 245, 0.12) !important;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.20) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .yh-btn-secondary,
.mcr-config-shell[data-mcr-theme="dark"] .yh-segment-item,
.mcr-config-shell[data-mcr-theme="dark"] .yh-save-segment,
.mcr-config-shell[data-mcr-theme="dark"] .yh-icon-btn {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(30, 42, 66, 0.72) !important;
  color: #c7d0e3 !important;
  -webkit-text-fill-color: #c7d0e3 !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .yh-btn-secondary:hover,
.mcr-config-shell[data-mcr-theme="dark"] .yh-segment-item:hover,
.mcr-config-shell[data-mcr-theme="dark"] .yh-icon-btn:hover {
  background: rgba(110, 162, 255, 0.14) !important;
  color: #8fc2ff !important;
  -webkit-text-fill-color: #8fc2ff !important;
}

@media (max-width: 959px) {
  .mcr-config-section-stack {
    gap: 14px;
  }

  .mcr-config-shell .mcr-config-topbar {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    min-height: 0;
    gap: 8px;
    padding: 8px 12px;
  }

  .mcr-config-shell .mcr-config-brand {
    min-height: 0;
    max-width: 100%;
    padding-right: 104px;
  }

  .mcr-config-shell .yh-mobile-title {
    display: inline-flex;
  }

  .mcr-config-shell .yh-settings-en-title {
    display: none !important;
  }

  .mcr-config-shell .mcr-config-topbar__meta {
    display: grid;
    justify-items: end;
    width: 100%;
    min-width: 0;
    flex: 0 1 auto;
    gap: 8px;
  }

  .mcr-config-shell .mcr-config-main-actions {
    display: flex;
    justify-content: flex-end;
    flex-wrap: nowrap;
    width: 100%;
    gap: 7px;
    overflow-x: auto;
    scrollbar-width: none;
  }

  .mcr-config-shell .mcr-config-main-actions::-webkit-scrollbar {
    display: none;
  }

  .mcr-config-shell .mcr-config-status-label {
    display: none;
  }

  .mcr-config-shell .mcr-config-generate {
    min-width: 118px;
    margin-left: 0;
    padding-inline: 10px !important;
  }

  .mcr-config-shell .mcr-config-save-group {
    flex: 0 0 auto;
  }

  .mcr-config-shell .mcr-config-save-group :deep(.mcr-config-save-button.mcr-button) {
    min-width: 86px;
    padding-inline: 10px !important;
  }

  .mcr-config-shell .mcr-config-save-group .mcr-config-save-mode {
    min-width: 58px;
  }

  .mcr-config-shell .mcr-config-topbar__meta,
  .mcr-config-shell .mcr-config-top-actions {
    justify-content: flex-end;
  }

  .mcr-config-shell .mcr-config-top-actions {
    position: static;
    justify-self: end;
    width: auto;
    max-width: 100%;
    justify-content: flex-end;
  }

  .mcr-config-shell .mcr-config-top-actions :deep(.mcr-button) {
    flex: 0 0 auto;
    min-width: 0;
  }

  .mcr-config-shell .mcr-config-top-tabs {
    width: 100%;
  }

  .mcr-config-section-card {
    padding: 14px;
    border-radius: 18px;
  }

  .mcr-config-section-card__header {
    margin-bottom: 12px;
  }

  .mcr-config-clean-actions,
  .mcr-config-clean-action {
    grid-template-columns: 1fr;
  }

  .mcr-config-clean-action {
    align-items: stretch;
  }

  .mcr-config-clean-action :deep(.mcr-button) {
    width: 100%;
  }
}

.mcr-config-shell .mcr-config-topbar {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) auto !important;
  grid-template-areas:
    "brand actions"
    "tabs tabs";
  gap: 12px 18px !important;
  align-items: start !important;
  padding: 12px 16px 14px !important;
}

.mcr-config-shell .mcr-config-brand {
  grid-area: brand;
  min-width: 0;
  min-height: 44px;
  padding-right: 0 !important;
}

.mcr-config-shell .mcr-config-topbar__meta {
  display: contents !important;
}

.mcr-config-shell .mcr-config-top-actions.yh-top-actions {
  grid-area: actions;
  position: static !important;
  top: auto !important;
  right: auto !important;
  z-index: 2;
  display: inline-flex !important;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  align-self: start;
  justify-self: end;
  width: auto !important;
  max-width: none !important;
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  white-space: nowrap;
}

.mcr-config-shell .mcr-config-top-tabs {
  grid-area: tabs;
  justify-self: stretch;
  width: min(360px, 100%) !important;
}

.mcr-config-shell .mcr-config-save-message--floating {
  position: absolute;
  top: 60px;
  right: 16px;
  z-index: 4;
  max-width: min(260px, calc(100% - 32px));
  padding: 7px 10px;
  border: 1px solid var(--yahaha-border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
  color: var(--yahaha-muted);
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
  white-space: nowrap;
  box-shadow: 0 10px 24px rgba(28, 77, 160, 0.12);
  pointer-events: none;
}

.mcr-config-shell .yh-run-btn {
  --yh-run-progress: 0%;
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  min-width: 44px;
  padding: 0;
  overflow: hidden;
  border: 1px solid var(--yahaha-blue);
  border-radius: 16px;
  background: var(--yahaha-blue);
  color: #fff;
  cursor: pointer;
  box-shadow: 0 8px 18px rgba(22, 119, 255, 0.22);
  transition:
    width 0.28s ease,
    min-width 0.28s ease,
    border-radius 0.28s ease,
    transform 0.14s ease,
    background-color 0.18s ease,
    box-shadow 0.18s ease;
}

.mcr-config-shell .yh-run-btn:hover {
  background: #2f86ff;
  box-shadow: 0 10px 22px rgba(22, 119, 255, 0.26);
}

.mcr-config-shell .yh-run-btn:active {
  transform: scale(0.96);
}

.mcr-config-shell .yh-run-btn:disabled {
  cursor: default;
  opacity: 0.68;
  transform: none;
}

.mcr-config-shell .yh-run-btn.is-running {
  width: 148px;
  min-width: 148px;
  border-radius: 18px;
}

.mcr-config-shell .yh-run-progress {
  position: absolute;
  inset: 0 auto 0 0;
  width: var(--yh-run-progress);
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.24), rgba(255, 255, 255, 0.08));
  transition: width 0.25s ease;
}

.mcr-config-shell .yh-run-content {
  position: relative;
  z-index: 1;
  display: inline-flex;
  height: 100%;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 12px;
  font-weight: 800;
  line-height: 1;
  white-space: nowrap;
}

.mcr-config-shell .yh-run-text,
.mcr-config-shell .yh-run-percent {
  font-size: 14px;
}

.mcr-config-shell .mcr-config-top-actions :deep(.yh-icon-btn.mcr-button),
.mcr-config-shell .yh-icon-btn {
  width: 44px !important;
  height: 44px !important;
  min-width: 44px !important;
  padding: 0 !important;
  border: 1px solid var(--yahaha-border) !important;
  border-radius: 16px !important;
  background: rgba(255, 255, 255, 0.94) !important;
  color: var(--yahaha-muted) !important;
  -webkit-text-fill-color: var(--yahaha-muted) !important;
  box-shadow: 0 4px 12px rgba(28, 77, 160, 0.08) !important;
  backdrop-filter: blur(10px);
}

.mcr-config-shell .mcr-config-top-actions :deep(.yh-icon-btn--save.mcr-button),
.mcr-config-shell .yh-icon-btn--save {
  border-color: #cfe0ff !important;
  background: var(--yahaha-blue-soft) !important;
  color: var(--yahaha-blue) !important;
  -webkit-text-fill-color: var(--yahaha-blue) !important;
}

.mcr-config-shell .mcr-config-top-actions :deep(.yh-icon-btn.mcr-button:hover),
.mcr-config-shell .yh-icon-btn:hover {
  border-color: #c9dcff !important;
  background: var(--yahaha-blue-soft) !important;
  color: var(--yahaha-blue) !important;
  -webkit-text-fill-color: var(--yahaha-blue) !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-top-actions :deep(.yh-icon-btn.mcr-button),
.mcr-config-shell[data-mcr-theme="dark"] .yh-icon-btn {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(30, 42, 66, 0.72) !important;
  color: #c7d0e3 !important;
  -webkit-text-fill-color: #c7d0e3 !important;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-save-message--floating {
  border-color: rgba(230, 236, 245, 0.12);
  background: rgba(30, 42, 66, 0.94);
  color: #c7d0e3;
}

@media (min-width: 768px) {
  .mcr-config-shell .yh-run-btn,
  .mcr-config-shell .mcr-config-top-actions :deep(.yh-icon-btn.mcr-button),
  .mcr-config-shell .yh-icon-btn {
    width: 46px !important;
    height: 46px !important;
    min-width: 46px !important;
    border-radius: 17px !important;
  }

  .mcr-config-shell .yh-run-btn.is-running {
    width: 154px !important;
    min-width: 154px !important;
    border-radius: 18px !important;
  }
}

@media (max-width: 600px) {
  .mcr-config-shell .mcr-config-topbar {
    grid-template-columns: minmax(0, 1fr) auto !important;
    gap: 10px 8px !important;
    padding: 10px 12px 12px !important;
  }

  .mcr-config-shell .mcr-config-brand {
    min-height: 40px;
  }

  .mcr-config-shell .mcr-config-top-actions.yh-top-actions {
    gap: 6px;
  }

  .mcr-config-shell .yh-run-btn,
  .mcr-config-shell .mcr-config-top-actions :deep(.yh-icon-btn.mcr-button),
  .mcr-config-shell .yh-icon-btn {
    width: 40px !important;
    height: 40px !important;
    min-width: 40px !important;
    border-radius: 15px !important;
  }

  .mcr-config-shell .yh-run-btn.is-running {
    width: 128px !important;
    min-width: 128px !important;
  }

  .mcr-config-shell .yh-run-text,
  .mcr-config-shell .yh-run-percent {
    font-size: 13px;
  }

  .mcr-config-shell .mcr-config-save-message--floating {
    top: 54px;
    right: 12px;
  }
}

.mcr-config-shell .yh-settings-title {
  margin: 0;
  color: var(--yahaha-text);
  font-size: clamp(34px, 4vw, 56px);
  font-weight: 900;
  letter-spacing: -0.04em;
  line-height: 0.95;
}

.mcr-config-shell[data-mcr-theme="dark"] .yh-settings-title {
  color: #f4f7fb;
}

.mcr-config-shell .mcr-config-hero {
  justify-content: flex-start;
  margin-bottom: 12px;
}

.mcr-config-shell .yh-switch-row {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
}

.mcr-config-shell .yh-switch-row :deep(.v-switch) {
  flex: 0 0 auto;
}

.mcr-config-shell .yh-field-hint {
  margin: 6px 0 0;
  color: #8a96aa;
  font-size: 13px;
  line-height: 1.5;
}

.mcr-config-shell[data-mcr-theme="dark"] .yh-field-hint {
  color: #8794ad;
}

.mcr-config-shell .mcr-config-top-tabs {
  width: min(520px, calc(100% - clamp(180px, 28vw, 520px))) !important;
  max-width: 520px !important;
  margin-left: clamp(180px, 28vw, 520px) !important;
}

.mcr-config-shell .yh-ui-rev {
  max-width: 1180px;
  margin: 24px auto 8px;
  padding-left: 4px;
  color: #a8b1c3;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.mcr-config-shell[data-mcr-theme="dark"] .yh-ui-rev {
  color: #8794ad;
}

@media (max-width: 768px) {
  .mcr-config-shell .mcr-config-top-tabs {
    width: 100% !important;
    max-width: none !important;
    margin-left: 0 !important;
  }
}

@media (max-width: 600px) {
  .mcr-config-shell .yh-settings-title {
    font-size: 34px;
  }

  .mcr-config-shell .yh-switch-row {
    gap: 10px 16px;
  }

  .mcr-config-shell .mcr-monitor-grid .mcr-config-switch-col {
    padding-top: 0;
  }
}

.mcr-config-shell .mcr-config-topbar {
  grid-template-areas:
    "brand actions"
    "chips tabs" !important;
  align-items: start !important;
}

.mcr-config-shell .yh-settings-title-wrap {
  position: relative;
  min-height: 70px;
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
  margin: 0;
}

.mcr-config-shell .yh-settings-en {
  display: block;
  color: rgba(90, 120, 180, 0.17);
  font-size: clamp(32px, 3.6vw, 54px);
  font-weight: 900;
  letter-spacing: -0.04em;
  line-height: 0.95;
  white-space: nowrap;
}

.mcr-config-shell .yh-settings-zh {
  position: relative;
  display: block;
  margin-top: -15px;
  margin-left: 8px;
  color: #1c2740;
  font-size: clamp(28px, 3vw, 46px);
  font-weight: 900;
  letter-spacing: -0.04em;
  line-height: 1.05;
}

.mcr-config-shell .yh-header-chips {
  grid-area: chips;
  justify-content: flex-start;
  align-self: center;
}

.mcr-config-shell .mcr-config-top-tabs {
  grid-area: tabs;
  justify-self: end !important;
  align-self: center;
  width: min(520px, 100%) !important;
  max-width: 520px !important;
  margin-left: auto !important;
}

.mcr-config-shell .mcr-config-top-tab {
  min-width: 0;
  padding-inline: 14px;
}

.mcr-config-shell .mcr-config-tag {
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 4px 12px rgba(28, 77, 160, 0.06);
}

.mcr-config-shell .yh-monitor-hint {
  margin-top: 14px;
  padding: 12px 14px;
  border: 1px solid rgba(167, 187, 225, 0.35);
  border-radius: 14px;
  background: rgba(93, 136, 214, 0.08);
  color: #7f8da6;
  font-size: 13px;
  line-height: 1.65;
}

.mcr-config-shell .yh-monitor-hint code {
  display: inline-block;
  max-width: 100%;
  padding: 2px 7px;
  border: 1px solid rgba(167, 187, 225, 0.28);
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.55);
  color: #52637f;
  font-family: 'SFMono-Regular', ui-monospace, Consolas, 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.45;
  overflow-wrap: anywhere;
  vertical-align: baseline;
}

.mcr-config-shell[data-mcr-theme="dark"] .yh-settings-en {
  color: rgba(110, 162, 255, 0.16);
}

.mcr-config-shell[data-mcr-theme="dark"] .yh-settings-zh {
  color: #f4f7fb;
}

.mcr-config-shell[data-mcr-theme="dark"] .mcr-config-tag {
  background: rgba(30, 42, 66, 0.72);
}

.mcr-config-shell[data-mcr-theme="dark"] .yh-monitor-hint {
  border-color: rgba(230, 236, 245, 0.12);
  background: rgba(110, 162, 255, 0.10);
  color: #c7d0e3;
}

.mcr-config-shell[data-mcr-theme="dark"] .yh-monitor-hint code {
  border-color: rgba(230, 236, 245, 0.12);
  background: rgba(244, 247, 251, 0.08);
  color: #dbe7ff;
}

@media (max-width: 768px) {
  .mcr-config-shell .mcr-config-topbar {
    grid-template-areas:
      "brand actions"
      "chips chips"
      "tabs tabs" !important;
  }

  .mcr-config-shell .mcr-config-top-tabs {
    justify-self: center !important;
    width: calc(100% - 8px) !important;
    max-width: none !important;
    margin-inline: auto !important;
  }

  .mcr-config-shell .yh-header-chips {
    flex-wrap: wrap;
  }
}

@media (max-width: 600px) {
  .mcr-config-shell .yh-settings-title-wrap {
    min-height: 58px;
  }

  .mcr-config-shell .yh-settings-en {
    font-size: 31px;
    white-space: normal;
  }

  .mcr-config-shell .yh-settings-zh {
    margin-top: -9px;
    font-size: 30px;
  }
}

@media (max-width: 768px) {
  .mcr-config-shell .yh-settings-title-wrap {
    max-width: 100%;
    overflow: hidden;
  }

  .mcr-config-shell .yh-settings-en {
    max-width: 100%;
    overflow: hidden;
    color: rgba(90, 120, 180, 0.15);
    font-size: 58px;
    font-weight: 950;
    line-height: 0.9;
    text-overflow: clip;
    white-space: nowrap;
  }

  .mcr-config-shell .yh-settings-zh {
    margin-top: -18px;
    font-size: 44px;
    font-weight: 950;
    line-height: 0.95;
  }
}

@media (max-width: 768px) {
  .mcr-config-shell .mcr-config-topbar {
    overflow: hidden !important;
  }

  .mcr-config-shell .mcr-config-brand {
    min-width: 0 !important;
    overflow: visible !important;
  }

  .mcr-config-shell .yh-settings-title-wrap {
    position: relative !important;
    min-height: 120px !important;
    max-width: none !important;
    overflow: visible !important;
  }

  .mcr-config-shell .yh-settings-en {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    z-index: 0 !important;
    width: max-content !important;
    max-width: none !important;
    overflow: visible !important;
    color: rgba(90, 120, 180, 0.14) !important;
    font-size: clamp(60px, 16vw, 92px) !important;
    font-weight: 950 !important;
    letter-spacing: -0.065em !important;
    line-height: 0.86 !important;
    pointer-events: none;
    text-overflow: clip !important;
    white-space: nowrap !important;
  }

  .mcr-config-shell .yh-settings-zh {
    position: relative !important;
    z-index: 2 !important;
    margin: 0 !important;
    padding-top: 58px !important;
    color: #1c2740 !important;
    font-size: clamp(46px, 12vw, 64px) !important;
    font-weight: 950 !important;
    letter-spacing: -0.05em !important;
    line-height: 1.02 !important;
  }

  .mcr-config-shell .mcr-config-top-actions.yh-top-actions {
    position: relative !important;
    z-index: 5 !important;
  }

  .mcr-config-shell .yh-run-btn,
  .mcr-config-shell .yh-icon-btn {
    position: relative !important;
    z-index: 6 !important;
  }

  .mcr-config-shell[data-mcr-theme="dark"] .yh-settings-en {
    color: rgba(110, 162, 255, 0.16) !important;
  }

  .mcr-config-shell[data-mcr-theme="dark"] .yh-settings-zh {
    color: #f4f7fb !important;
  }
}

@media (max-width: 768px) {
  .mcr-config-shell .mcr-config-topbar {
    overflow: hidden !important;
  }

  .mcr-config-shell .yh-settings-title-wrap {
    position: relative !important;
    min-height: 130px !important;
    max-width: none !important;
    overflow: visible !important;
  }

  .mcr-config-shell .yh-settings-en {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    z-index: 0 !important;
    width: max-content !important;
    max-width: none !important;
    overflow: visible !important;
    color: rgba(90, 120, 180, 0.14) !important;
    font-size: clamp(64px, 17vw, 96px) !important;
    font-weight: 950 !important;
    letter-spacing: -0.065em !important;
    line-height: 0.88 !important;
    pointer-events: none;
    text-overflow: clip !important;
    white-space: nowrap !important;
  }

  .mcr-config-shell .yh-settings-zh {
    position: absolute !important;
    top: 48px !important;
    left: 0 !important;
    z-index: 2 !important;
    width: max-content !important;
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
    color: #1c2740 !important;
    font-size: clamp(54px, 14vw, 72px) !important;
    font-weight: 950 !important;
    letter-spacing: -0.06em !important;
    line-height: 1 !important;
    overflow-wrap: normal !important;
    white-space: nowrap !important;
    word-break: keep-all !important;
  }

  .mcr-config-shell .mcr-config-top-actions.yh-top-actions {
    position: relative !important;
    z-index: 5 !important;
  }

  .mcr-config-shell[data-mcr-theme="dark"] .yh-settings-en {
    color: rgba(110, 162, 255, 0.16) !important;
  }

  .mcr-config-shell[data-mcr-theme="dark"] .yh-settings-zh {
    color: #f4f7fb !important;
  }

  .mcr-title-config-heading { align-items: flex-start; }
  .mcr-title-config-toolbar { grid-template-columns: 1fr; }
  .mcr-title-config-toolbar .mcr-title-config-mode { min-width: 0; }
}
</style>
