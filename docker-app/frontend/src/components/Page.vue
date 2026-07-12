
<template>
  <div class="mcr-shell mcr-page-shell" :data-mcr-theme="isDark ? 'dark' : 'light'">
    <div class="mcr-shell__aurora" />
    <div class="mcr-shell__noise" />
    <v-card class="mcr-frame">
      <v-defaults-provider :defaults="controlDefaults">
        <v-card-text class="mcr-frame__body">
          <section class="mcr-shell__header mcr-page-hero">
            <div class="mcr-shell__header-grid">
              <div class="mcr-shell__copy">
                <div class="mcr-page-title-row yh-brand-row">
                  <button
                    type="button"
                    class="mcr-logo-slot yh-avatar-wrap"
                    :class="{ 'mcr-logo-slot--donor': donationAcknowledged }"
                    title="赞赏支持"
                    aria-label="赞赏支持"
                    @click="openDonationDialog"
                  >
                    <span class="yh-avatar">
                      <img v-if="donationAvatarImage" class="yh-avatar__image" :src="donationAvatarImage" alt="">
                      <v-icon v-else :icon="donationAvatarIcon" size="24" />
                    </span>
                    <span
                      v-if="donationAcknowledged"
                      class="yh-avatar-crown"
                      title="切换为 MP 头像"
                      aria-label="切换为 MP 头像"
                      @click.stop.prevent="selectMoviePilotAvatar"
                    >
                      <v-icon icon="mdi-crown" size="24" />
                    </span>
                  </button>
                  <h1 class="yh-brand-title" aria-label="呀哈哈封面工坊 Yahaha Cover Studio">
                    <span class="yh-brand-en-big" aria-hidden="true">
                      <span class="yh-brand-en-pc">Yahaha Cover Studio</span>
                      <span class="yh-brand-en-mobile">
                        <span>Yahaha</span>
                        <span>CoverStudio</span>
                      </span>
                    </span>
                    <span class="yh-brand-zh-overlap">
                      <span class="yh-brand-zh-part">呀哈哈</span><span class="yh-brand-zh-part">封面工坊</span>
                    </span>
                  </h1>
                </div>
              </div>
              <div class="blueprint-hero-actions">
                <div class="mcr-page-top-actions yh-top-actions">
                  <button
                    type="button"
                    class="mcr-logo-slot yh-avatar-wrap yh-avatar-toolbar"
                    :class="{ 'mcr-logo-slot--donor': donationAcknowledged }"
                    title="赞赏支持"
                    aria-label="赞赏支持"
                    @click="openDonationDialog"
                  >
                    <span class="yh-avatar">
                      <img v-if="donationAvatarImage" class="yh-avatar__image" :src="donationAvatarImage" alt="">
                      <v-icon v-else :icon="donationAvatarIcon" size="22" />
                    </span>
                    <span
                      v-if="donationAcknowledged"
                      class="yh-avatar-crown"
                      title="切换为 MP 头像"
                      aria-label="切换为 MP 头像"
                      @click.stop.prevent="selectMoviePilotAvatar"
                    >
                      <v-icon icon="mdi-crown" size="20" />
                    </span>
                  </button>
                  <button
                    type="button"
                    class="yh-run-btn"
                    :class="{ 'is-running': isGenerating }"
                    :style="runButtonProgressStyle"
                    :title="isGenerating ? generationProgressLabel : '生成封面'"
                    :aria-label="isGenerating ? generationProgressLabel : '生成封面'"
                    :disabled="!statusLoaded || generatingNow"
                    @click="handleGenerateAction"
                  >
                    <span class="yh-run-progress" aria-hidden="true" />
                    <span class="yh-run-content">
                      <v-icon :icon="isGenerating ? 'mdi-stop-circle-outline' : 'mdi-play-circle-outline'" size="24" />
                      <span v-if="isGenerating" class="yh-run-text">生成中</span>
                      <span v-if="isGenerating" class="yh-run-percent">{{ generationProgressPercent }}%</span>
                    </span>
                  </button>
                  <v-btn
                    size="small"
                    class="mcr-button mcr-button--ghost mcr-button--dark-neutral yh-icon-btn"
                    icon
                    title="配置"
                    aria-label="配置"
                    :disabled="controlsLocked"
                    @click="notifySwitch"
                  >
                    <v-icon icon="mdi-cog-outline" size="22" />
                  </v-btn>
                </div>
                <div class="yh-preview-chips" aria-label="当前参数">
                  <span :class="{ 'is-disabled': !programEnabled }">程序{{ programEnabled ? '已启用' : '已停用' }}</span>
                  <span>{{ currentStyleLabel }}</span>
                  <span>{{ currentVariantLabel }}</span>
                  <span>{{ sourceModeLabel }}</span>
                  <span v-if="sourceSortLocked">最新入库排序已锁定</span>
                  <AsyncStatusDots v-if="backendBusy" :label="backendBusyLabel" />
                </div>
                <div
                  class="mcr-page-tabs-shell"
                  :class="{ 'mcr-page-tabs-shell--history': pageTab === 'history-tab' }"
                >
                  <span class="mcr-page-tabs-indicator" aria-hidden="true" />
                  <div
                    role="tablist"
                    aria-label="页面切换"
                    class="mcr-page-tabs-track"
                  >
                    <button
                      type="button"
                      role="tab"
                      class="mcr-page-tab-button"
                      :class="{ 'mcr-page-tab-button--active': pageTab === 'generate-tab' }"
                      :aria-selected="pageTab === 'generate-tab'"
                      :disabled="controlsLocked"
                      @click="setPageTab('generate-tab')"
                    >
                      <span class="mcr-page-tabs-label">封面生成</span>
                    </button>
                    <button
                      type="button"
                      role="tab"
                      class="mcr-page-tab-button"
                      :class="{ 'mcr-page-tab-button--active': pageTab === 'history-tab' }"
                      :aria-selected="pageTab === 'history-tab'"
                      :disabled="controlsLocked"
                      @click="setPageTab('history-tab')"
                    >
                      <span class="mcr-page-tabs-label">历史封面</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <v-window v-model="pageTab" :touch="false">
            <v-window-item value="generate-tab">
              <div
                class="generate-layout blueprint-workbench"
                :class="{
                  'blueprint-workbench--editing': isEditingLayout,
                  'blueprint-workbench--locked': controlsLocked,
                }"
              >
                <section
                  ref="previewBayEl"
                  class="blueprint-preview-bay"
                  :class="{ 'blueprint-preview-bay--locked': controlsLocked }"
                >
                  <div class="blueprint-panel-heading">
                    <div>
                      <div class="mcr-panel__eyebrow">{{ isEditingLayout ? 'Editor' : 'Canvas' }}</div>
                      <div class="mcr-panel__title">{{ isEditingLayout ? '画布编辑' : previewModeLabel }}</div>
                    </div>
                    <v-tooltip v-if="!isEditingLayout" text="重新获取海报">
                      <template #activator="{ props: tooltipProps }">
                        <button v-bind="tooltipProps" type="button" class="mcr-preview-refresh" :class="{ 'is-loading': refreshingPreview }" aria-label="重新获取海报" :disabled="refreshingPreview || controlsLocked" @click="refreshCurrentPreview">
                          <v-icon icon="mdi-refresh" size="22" />
                        </button>
                      </template>
                    </v-tooltip>
                  </div>

                  <CustomLayoutEditor
                    v-if="isEditingLayout && customStaticLayout"
                    :key="activeEditorTemplateId || coverStyleBase"
                    :model-value="customStaticLayout"
                    :preview-source="previewSource"
                    :params="simulationParams"
                    :floating-tools-visible="pageTab === 'generate-tab' && isEditingLayout"
                    :theme="isDark ? 'dark' : 'light'"
                    :api="props.api"
                    embedded
                    @update:model-value="onLayoutUpdated"
                  >
                    <template #footer-actions>
                      <span class="mcr-editor-save-cluster">
                        <span class="mcr-editor-split-save">
                          <button
                            type="button"
                            class="mcr-button mcr-button--primary mcr-editor-save-main"
                            :disabled="controlsLocked || !activeEditorTemplateId || !customStaticLayout"
                            @click="saveCustomLayoutNow"
                          >
                            保存方案
                          </button>
                          <button
                            type="button"
                            class="mcr-button mcr-button--primary mcr-editor-save-toggle"
                            :aria-label="editorAutoSaveEnabled ? '自动保存已开启，点击关闭' : '自动保存已关闭，点击开启'"
                            :title="editorAutoSaveEnabled ? '自动保存已开启，点击关闭' : '自动保存已关闭，点击开启'"
                            :disabled="controlsLocked || !activeEditorTemplateId || !customStaticLayout"
                            @click.stop="toggleEditorAutoSave"
                          >
                            <span class="mcr-editor-save-mode">
                              {{ editorAutoSaveEnabled ? 'AUTO' : 'MANUAL' }}
                            </span>
                          </button>
                        </span>
                      </span>
                      <v-btn
                        size="small"
                        class="mcr-button mcr-button--ghost mcr-button--dark-neutral"
                        :disabled="controlsLocked || !activeEditorTemplateId"
                        @click="restoreCurrentLayoutDefaults"
                      >
                        {{ resetButtonLabel }}
                      </v-btn>
                      <v-btn
                        size="small"
                        class="mcr-button mcr-button--ghost mcr-button--dark-neutral"
                        :disabled="controlsLocked"
                        @click="isEditingLayout = false"
                      >
                        返回预览
                      </v-btn>
                    </template>
                  </CustomLayoutEditor>
	

                  <div v-else class="blueprint-preview-frame">
                    <div
                      v-if="showMainPreviewSkeleton"
                      class="blueprint-skeleton blueprint-skeleton--preview"
                      :class="{ 'blueprint-skeleton--active': resourceSkeletonActive }"
                      aria-label="预览资源加载中"
                    >
                      <span class="blueprint-skeleton__shape blueprint-skeleton__shape--visual" />
                      <span class="blueprint-skeleton__shape blueprint-skeleton__shape--title" />
                      <span class="blueprint-skeleton__shape blueprint-skeleton__shape--line" />
                      <span class="blueprint-skeleton__shape blueprint-skeleton__shape--line-short" />
                      <span class="blueprint-skeleton__shape blueprint-skeleton__shape--chip" />
                    </div>
                    <GeneratePreviewSimulation
                      v-else
                      :source="effectivePreviewSource"
                      :params="simulationParams"
                    />
                  </div>

                  <div v-if="!isEditingLayout" class="blueprint-meta-grid mcr-render-options">
                    <label class="mcr-render-option">
                      <span>海报来源</span>
                      <select v-model="posterSource" :disabled="controlsLocked" @change="saveRenderOptions">
                        <option value="backdrop">横版 Backdrop</option>
                        <option value="poster">竖版 Poster</option>
                      </select>
                    </label>
                    <label class="mcr-render-option">
                      <span class="yh-field-label">
                        <span>封面来源排序</span>
                        <span v-if="sourceSortLocked" class="yh-inline-lock-badge">已锁定</span>
                      </span>
                      <select v-model="sourceSortBy" :disabled="sourceSortDisabled" @change="saveRenderOptions">
                        <option value="Random">随机</option>
                        <option value="DateCreated">{{ sourceSortLocked ? '最新入库（已锁定）' : '最新入库' }}</option>
                        <option value="PremiereDate">最新发行</option>
                      </select>
                    </label>
                    <label class="mcr-render-option">
                      <span>分辨率</span>
                      <select
                        v-if="styleVariant === 'static'"
                        v-model="staticResolution"
                        :disabled="controlsLocked"
                        @change="saveRenderOptions"
                      >
                        <option value="480p">480p</option>
                        <option value="720p">720p</option>
                        <option value="1080p">1080p</option>
                      </select>
                      <span v-else class="mcr-render-option__value">{{ animatedResolutionLabel }}</span>
                    </label>
                  </div>
                </section>

                <aside
                  v-if="!isEditingLayout"
                  class="blueprint-control-bay"
                  :class="{ 'blueprint-control-bay--collapsed': schemeListCollapsed }"
                  :style="controlBayStyle"
                >
                  <div
                    class="blueprint-panel-heading mcr-collapsible-heading"
                    :class="{ 'mcr-collapsible-heading--collapsed': schemeListCollapsed }"
                    role="button"
                    tabindex="0"
                    :aria-expanded="!schemeListCollapsed"
                    aria-controls="mcr-scheme-list-content"
                    @click="schemeListCollapsed = !schemeListCollapsed"
                    @keydown.enter.prevent="schemeListCollapsed = !schemeListCollapsed"
                    @keydown.space.prevent="schemeListCollapsed = !schemeListCollapsed"
                  >
                    <div class="mcr-collapsible-heading__title">
                      <div class="mcr-panel__eyebrow">Presets</div>
                      <div class="mcr-panel__title">
                        封面方案
                        <v-icon
                          icon="mdi-chevron-up"
                          size="20"
                          class="mcr-collapsible-heading__icon"
                          aria-hidden="true"
                        />
                      </div>
                    </div>
                    <Transition name="mcr-mode-switch">
                      <button
                        v-if="!schemeListCollapsed"
                        class="blueprint-mode-toggle"
                        :class="{
                          'blueprint-mode-toggle--animated': styleVariant === 'animated',
                          'blueprint-mode-toggle--disabled': controlsLocked || coverStyleBase === 'custom_static',
                          'blueprint-mode-toggle--pulse': modeSwitchPulse,
                        }"
                        type="button"
                        :aria-pressed="styleVariant === 'animated'"
                        :aria-disabled="controlsLocked || coverStyleBase === 'custom_static'"
                        :disabled="controlsLocked || coverStyleBase === 'custom_static'"
                        @click.stop="onModeSwitchClick"
                        @keydown.enter.stop.prevent="onModeSwitchClick"
                        @keydown.space.stop.prevent="onModeSwitchClick"
	                      >
	                        <span class="blueprint-mode-option blueprint-mode-option--static">
	                          <span>静态</span>
	                        </span>
                        <span class="blueprint-mode-switch-track" aria-hidden="true">
                          <span class="blueprint-mode-thumb" />
                        </span>
                        <span class="blueprint-mode-option blueprint-mode-option--animated">
                          <span>动图</span>
	                        </span>
	                      </button>
                    </Transition>
	                  </div>

                  <Transition name="mcr-list-collapse">
                    <div
                      v-show="!schemeListCollapsed"
                      id="mcr-scheme-list-content"
                      class="mcr-scheme-list"
                      :class="{ 'mcr-scheme-list--animated': styleVariant === 'animated' }"
                      aria-label="封面方案列表"
                    >
                      <div v-if="animatedSettingsPanelOpen" class="mcr-animated-parameter-panel">
                        <div class="mcr-animated-parameter-panel__header">
                          <button
                            type="button"
                            class="mcr-animated-parameter-panel__back"
                            aria-label="返回动态方案列表"
                            title="返回动态方案列表"
                            @click="animatedSettingsPanelOpen = false"
                          >
                            <v-icon icon="mdi-arrow-left" size="18" />
                          </button>
                          <div>
                            <span>Motion Settings</span>
                            <strong>{{ animatedSettingsTitle }}</strong>
                          </div>
                        </div>
                        <div class="mcr-animated-settings__grid">
                          <BlueprintSelect
                            v-model="animatedSettings.animationFormat"
                            label="输出格式"
                            :items="animatedFormatItems"
                          />
                          <BlueprintSelect
                            v-model="animatedSettings.animationReduceColors"
                            label="颜色压缩"
                            :items="animatedColorReduceItems"
                          />
                          <BlueprintSelect
                            v-model="animatedSettings.mainTitleFontPreset"
                            label="主标题字体"
                            :items="dynamicFontItems"
                          />
                          <BlueprintSelect
                            v-model="animatedSettings.subtitleFontPreset"
                            label="副标题字体"
                            :items="dynamicFontItems"
                          />
                          <BlueprintRange
                            v-model="animatedSettings.mainTitleFontSize"
                            label="主标题字号"
                            :min="24"
                            :max="320"
                            :step="1"
                          />
                          <BlueprintRange
                            v-model="animatedSettings.subtitleFontSize"
                            label="副标题字号"
                            :min="12"
                            :max="220"
                            :step="1"
                          />
                          <BlueprintRange
                            v-model="animatedSettings.titleScale"
                            label="标题缩放"
                            :min="0.2"
                            :max="3"
                            :step="0.05"
                          />
                          <BlueprintRange
                            v-model="animatedSettings.blurSize"
                            label="背景模糊"
                            :min="0"
                            :max="100"
                            :step="1"
                          />
                          <BlueprintRange
                            v-model="animatedSettings.colorRatio"
                            label="背景混色"
                            :min="0"
                            :max="1"
                            :step="0.05"
                          />
                          <BlueprintRange
                            v-model="animatedSettings.animationDuration"
                            label="动画时长"
                            :min="1"
                            :max="60"
                            :step="1"
                          />
                          <BlueprintRange
                            v-model="animatedSettings.animationFps"
                            label="帧率"
                            :min="1"
                            :max="60"
                            :step="1"
                          />
                          <BlueprintRange
                            v-if="showAnimatedImageCountSetting"
                            v-model="animatedSettings.animated2ImageCount"
                            label="图片数量"
                            :min="3"
                            :max="60"
                            :step="1"
                          />
                          <BlueprintSelect
                            v-if="showAnimatedScrollSetting"
                            v-model="animatedSettings.animationScroll"
                            label="滚动方向"
                            :items="animatedScrollItems"
                          />
                          <BlueprintSelect
                            v-if="showAnimatedDepartureSetting"
                            v-model="animatedSettings.animated2DepartureType"
                            label="动画风格"
                            :items="animatedDepartureItems"
                          />
                          <p v-if="animatedSettingsBaseStyle === 'static_3'" class="mcr-note">
                            方案 3 使用固定九宫格滚动，素材数量按 9 张处理。
                          </p>
                        </div>
                        <div class="mcr-animated-parameter-panel__actions">
                          <AsyncStatusDots v-if="animatedSettingsSaving" label="保存参数" />
                          <v-btn
                            size="small"
                            class="mcr-button mcr-button--primary mcr-button--apple-primary"
                            :disabled="animatedSettingsSaving"
                            @click="saveAnimatedSettings"
                          >
                            保存参数
                          </v-btn>
                        </div>
                      </div>
                      <template v-else>
                      <div :key="schemeListKey" ref="schemeListScrollEl" class="mcr-scheme-list__scroll">
                      <div
                        v-for="item in schemeListItems"
                        :key="item.id"
                        class="mcr-scheme-row"
                        :class="{
                          'mcr-scheme-row--active': isSchemeItemActive(item),
                          'mcr-scheme-row--preset': item.kind === 'preset',
                        }"
                      >
                        <div
                          role="button"
                          class="mcr-scheme-row__select"
                          :class="{ 'mcr-scheme-row__select--disabled': controlsLocked }"
                          :aria-disabled="controlsLocked ? 'true' : 'false'"
                          :tabindex="controlsLocked ? -1 : 0"
                          @click="!controlsLocked && selectSchemeItem(item)"
                          @keydown.enter.prevent="!controlsLocked && selectSchemeItem(item)"
                          @keydown.space.prevent="!controlsLocked && selectSchemeItem(item)"
                        >
                          <span class="mcr-scheme-row__media">
                            <span
                              v-if="showStylePreviewSkeleton"
                              class="blueprint-skeleton blueprint-skeleton--card"
                              :class="{ 'blueprint-skeleton--active': resourceSkeletonActive }"
                              aria-label="方案预览资源加载中"
                            >
                              <span class="blueprint-skeleton__shape blueprint-skeleton__shape--visual" />
                              <span class="blueprint-skeleton__shape blueprint-skeleton__shape--title" />
                              <span class="blueprint-skeleton__shape blueprint-skeleton__shape--line" />
                              <span class="blueprint-skeleton__shape blueprint-skeleton__shape--line-short" />
                              <span class="blueprint-skeleton__shape blueprint-skeleton__shape--chip" />
                            </span>
                            <GeneratePreviewSimulation
                              v-else-if="buildSchemePreviewSource(item)"
                              :source="buildSchemePreviewSource(item)"
                              :params="simulationParams"
                            />
                          </span>
                          <span class="mcr-scheme-row__body">
                            <strong>{{ item.title }}</strong>
                            <span v-if="styleVariant === 'static'">{{ item.kind === 'preset' ? '预设方案' : '自定义方案' }}</span>
                            <span v-else>{{ animatedResolutionLabel }}</span>
                          </span>
                        </div>

                        <div class="mcr-scheme-row__actions">
                          <template v-if="styleVariant === 'static'">
                            <v-btn
                            icon="mdi-tune-variant"
                            size="x-small"
                            variant="text"
                            class="mcr-scheme-row__icon"
                            :disabled="controlsLocked"
                            title="编辑方案"
                            @click.stop="editSchemeItem(item)"
                            />
                            <v-btn
                            icon="mdi-form-textbox"
                            size="x-small"
                            variant="text"
                            class="mcr-scheme-row__icon"
                            :disabled="controlsLocked"
                            title="重命名"
                            @click.stop="renameSchemeItem(item)"
                            />
                            <v-menu location="bottom end" :close-on-content-click="true">
                              <template #activator="{ props: exportMenuProps }">
                                <v-btn
                                v-bind="exportMenuProps"
                                icon="mdi-export-variant"
                                size="x-small"
                                variant="text"
                                class="mcr-scheme-row__icon"
                                :disabled="controlsLocked"
                                title="导出方案"
                                @click.stop
                                />
                              </template>
                              <v-list class="mcr-template-action-menu" :data-mcr-theme="isDark ? 'dark' : 'light'" density="compact">
                                <v-list-item @click="exportSchemeItemToClipboard(item)">
                                  <v-list-item-title>复制到剪切板</v-list-item-title>
                                </v-list-item>
                                <v-list-item @click="exportSchemeItemToFile(item)">
                                  <v-list-item-title>下载 JSON 文件</v-list-item-title>
                                </v-list-item>
                              </v-list>
                            </v-menu>
                            <v-btn
                            v-if="item.kind === 'custom'"
                            icon="mdi-trash-can-outline"
                            size="x-small"
                            variant="text"
                            class="mcr-scheme-row__icon mcr-scheme-row__icon--danger"
                            :disabled="controlsLocked"
                            title="删除方案"
                            @click.stop="deleteSchemeItem(item)"
                            />
                          </template>
                          <v-btn
                            v-else-if="item.kind === 'preset'"
                            icon="mdi-tune-variant"
                            size="x-small"
                            variant="text"
                            class="mcr-scheme-row__icon"
                            :disabled="controlsLocked"
                            title="配置动态方案"
                            @click.stop="openAnimatedSettings(item)"
                          />
                        </div>
                      </div>
                    </div>

                    <div v-if="styleVariant === 'static'" class="mcr-scheme-list__tail">
                      <v-btn
                        size="small"
                        class="mcr-button mcr-button--primary mcr-button--dark-neutral mcr-scheme-tail-button"
                        prepend-icon="mdi-plus"
                        :disabled="controlsLocked"
                        @click="createTemplateFromCurrent"
                      >
                        添加方案
                      </v-btn>
                      <v-menu location="bottom end" :close-on-content-click="true">
                        <template #activator="{ props: importMenuProps }">
                          <v-btn
                            v-bind="importMenuProps"
                            size="small"
                            class="mcr-button mcr-button--ghost mcr-button--dark-neutral mcr-scheme-tail-button"
                            prepend-icon="mdi-import"
                            :disabled="controlsLocked"
                          >
                            导入方案
                          </v-btn>
                        </template>
                        <v-list class="mcr-template-action-menu" :data-mcr-theme="isDark ? 'dark' : 'light'" density="compact">
                          <v-list-item @click="importTemplateFromClipboard">
                            <v-list-item-title>从剪切板导入</v-list-item-title>
                          </v-list-item>
                          <v-list-item @click="triggerImportTemplate">
                            <v-list-item-title>从 JSON 文件导入</v-list-item-title>
                          </v-list-item>
                        </v-list>
                      </v-menu>
                      <input
                        ref="importTemplateInput"
                        type="file"
                        accept="application/json,.json"
                        class="mcr-visually-hidden"
                        @change="importTemplateFromFile"
                      >
                    </div>
                    </template>
                    </div>
                  </Transition>
                </aside>
              </div>
            </v-window-item>

            <v-window-item value="history-tab">
              <div
                ref="historyHeaderEl"
                class="mcr-history-header mcr-collapsible-heading"
                :class="{ 'mcr-collapsible-heading--collapsed': historyListCollapsed }"
                role="button"
                tabindex="0"
                :aria-expanded="!historyListCollapsed"
                aria-controls="mcr-history-list-content"
                @click="historyListCollapsed = !historyListCollapsed"
                @keydown.enter.prevent="historyListCollapsed = !historyListCollapsed"
                @keydown.space.prevent="historyListCollapsed = !historyListCollapsed"
              >
                <div class="mcr-collapsible-heading__title">
                  <div class="mcr-panel__eyebrow">History</div>
                  <div class="mcr-panel__title">
                    历史封面
                    <v-icon
                      icon="mdi-chevron-up"
                      size="20"
                      class="mcr-collapsible-heading__icon"
                      aria-hidden="true"
                    />
                    <AsyncStatusDots v-if="backendBusy" :label="backendBusyLabel" />
                  </div>
                </div>
                <Transition name="mcr-heading-tools">
                  <div v-if="!historyListCollapsed" class="mcr-history-toolbar" @click.stop @keydown.stop>
                    <v-btn-toggle v-model="historyGroupMode" mandatory divided density="compact" class="mcr-toggle mcr-history-toggle" :disabled="controlsLocked">
                      <v-btn value="library" class="mcr-button mcr-button--ghost mcr-history-mode-button" :class="{ 'mcr-history-mode-button--active': historyGroupMode === 'library' }">媒体库</v-btn>
                      <v-btn value="time-machine" class="mcr-button mcr-button--ghost mcr-history-mode-button" :class="{ 'mcr-history-mode-button--active': historyGroupMode === 'time-machine' }">时光机</v-btn>
                    </v-btn-toggle>
                    <BlueprintSelect
                      v-model="historySortMode"
                      :items="historySortItems"
                      class="mcr-control mcr-history-sort"
                      :disabled="controlsLocked"
                    />
                  </div>
                </Transition>
              </div>

              <Teleport to="body">
                <nav v-if="pageTab === 'history-tab' && historyGroupMode === 'time-machine' && groupedHistory.length" class="mcr-time-machine-timeline" :data-mcr-theme="isDark ? 'dark' : 'light'" aria-label="历史时间轴">
                  <button v-for="group in groupedHistory" :key="group.key" type="button" class="mcr-time-machine-node" :class="{ 'is-active': activeTimeRecordId === group.key }" @click="scrollToTimeRecord(group.key)">
                    <span v-if="activeTimeRecordId === group.key" class="mcr-time-machine-restore" @click.stop="restoreHistoryBatch(group.key, group.title)">回到此时</span>
                    <i aria-hidden="true" /><span>{{ group.title }}</span>
                  </button>
                </nav>
              </Teleport>

              <Teleport to="body">
                <div
                  v-if="pageTab === 'history-tab' && !historyListCollapsed && selectedHistoryPaths.length"
                  class="mcr-history-floating-actions"
                  :data-mcr-theme="isDark ? 'dark' : 'light'"
                  :style="historyFloatingStyle"
                  role="toolbar"
                  aria-label="历史封面批量操作"
                >
                  <span class="mcr-history-selection-count">已选择 {{ selectedHistoryPaths.length }}</span>
                  <button
                    type="button"
                    class="mcr-history-floating-button"
                    :disabled="controlsLocked || !history.length"
                    @pointerdown.prevent
                    @click.prevent.stop="toggleSelectAllHistory"
                  >
                    {{ allHistorySelected ? '取消全选' : '全选' }}
                  </button>
                  <button
                    type="button"
                    class="mcr-history-floating-button mcr-history-floating-button--primary"
                    :disabled="controlsLocked"
                    @pointerdown.prevent
                    @click.prevent.stop="downloadSelectedCoversDirect"
                  >
                    直接下载
                  </button>
                  <button
                    type="button"
                    class="mcr-history-floating-button"
                    :disabled="controlsLocked"
                    @pointerdown.prevent
                    @click.prevent.stop="downloadSelectedCoversZip"
                  >
                    下载 ZIP
                  </button>
                  <button
                    type="button"
                    class="mcr-history-floating-button mcr-history-floating-button--danger"
                    :disabled="controlsLocked"
                    @pointerdown.prevent
                    @click.prevent.stop="deleteSelectedCovers"
                  >
                    删除
                  </button>
                </div>
              </Teleport>

              <Transition name="mcr-list-collapse">
                <div
                  v-show="!historyListCollapsed"
                  id="mcr-history-list-content"
                  class="mcr-history-list-content"
                >
                  <div v-if="history.length" class="mcr-history-groups">
                    <section
                      v-for="group in groupedHistory"
                      :key="group.key"
                      class="mcr-history-group"
                      :class="{ 'mcr-history-group--time-machine': historyGroupMode === 'time-machine', 'is-active': activeTimeRecordId === group.key }"
                      :id="`time-record-${group.key}`"
                    >
                  <div class="mcr-history-group__heading">
                    <div class="mcr-history-group__title">
                      <span>{{ group.title }}</span>
                      <strong>{{ group.items.length }}</strong>
                    </div>
                  </div>
                  <button
                    v-if="historyGroupMode === 'time-machine'"
                    type="button"
                    class="mcr-time-machine-stack"
                    :aria-label="`查看 ${group.title} 的全部封面`"
                    @click="openHistorySnapshot(group)"
                  >
                    <span v-for="(item, index) in group.items.slice(0, historyStackLimit)" :key="item.path" class="mcr-time-machine-stack__cover" :style="timeMachineCoverStyle(group.key, index)">
                      <img :src="item.src || item.url || ''" :alt="item.library || item.name" loading="lazy">
                      <span>{{ item.library || item.name }}</span>
                    </span>
                    <span v-if="group.items.length > historyStackLimit" class="mcr-time-machine-stack__more">+{{ group.items.length - historyStackLimit }}</span>
                  </button>
                  <v-row v-else>
                    <v-col
                      v-for="item in group.items"
                      :key="item.path"
                      cols="12"
                      sm="6"
                      md="3"
                    >
                      <v-card
                        variant="flat"
                        elevation="0"
                        class="mcr-panel mcr-history-card"
                        :class="{ 'mcr-history-card--selected': selectedHistoryPaths.includes(item.path) }"
                      >
                        <div class="mcr-history-card__media">
                          <v-img
                            :src="item.src || item.url || ''"
                            aspect-ratio="16/9"
                            cover
                            class="mcr-history-card__image"
                          />
                          <button
                            type="button"
                            class="mcr-history-card__check"
                            :class="{ 'mcr-history-card__check--active': selectedHistoryPaths.includes(item.path) }"
                            :aria-pressed="selectedHistoryPaths.includes(item.path)"
                            :aria-label="selectedHistoryPaths.includes(item.path) ? '取消选择封面' : '选择封面'"
                            :disabled="controlsLocked"
                            @click.stop="toggleHistorySelection(item)"
                          >
                            <span class="mcr-history-card__check-mark" aria-hidden="true" />
                          </button>
                          <div class="mcr-history-card__title">
                            {{ item.library || item.name }}
                          </div>
                        </div>
                        <v-card-text class="mcr-panel__body mcr-panel__body--tight">
                          <div class="mcr-history-card__meta"><span>{{ item.library || item.name }}</span><span>{{ item.server || 'Unknown' }}</span></div>
                        </v-card-text>
                      </v-card>
                    </v-col>
                  </v-row>
                    </section>
                  </div>
                  <div v-else class="mcr-history-empty">还没有可以回到的时间<br><small>生成并保存封面后，历史记录会显示在这里。</small></div>
                </div>
              </Transition>
            </v-window-item>
          </v-window>
        </v-card-text>
      </v-defaults-provider>

    </v-card>

    <v-dialog v-model="restoreConfirmDialog" max-width="520" :scrim="isDark ? 'rgba(0,0,0,.66)' : 'rgba(24,32,48,.34)'">
      <v-card class="mcr-history-restore-confirm" :data-mcr-theme="isDark ? 'dark' : 'light'"><h3>确定回到此时吗？</h3><p>{{ pendingHistoryRestore?.label }}</p><p>将把该时间保存的封面重新应用到对应服务器媒体库。当前服务器上的封面会被替换，但历史记录不会被删除。</p><footer><v-btn class="mcr-button mcr-button--ghost" @click="restoreConfirmDialog = false">取消</v-btn><v-btn class="mcr-button mcr-button--primary" :loading="Boolean(restoringBatchId)" @click="executeHistoryRestore">回到此时</v-btn></footer></v-card>
    </v-dialog>
    <v-dialog v-model="historySnapshotDialog" max-width="1120" class="mcr-history-snapshot-dialog" :scrim="isDark ? 'rgba(0,0,0,.66)' : 'rgba(24,32,48,.34)'">
      <v-card v-if="selectedHistorySnapshot" class="mcr-history-snapshot" :data-mcr-theme="isDark ? 'dark' : 'light'">
        <header class="mcr-history-snapshot__header"><div><span>History</span><h3>此时的封面</h3><p>{{ selectedHistorySnapshot.fullTitle }}</p></div><v-btn icon="mdi-close" variant="text" aria-label="关闭" @click="historySnapshotDialog = false" /></header>
        <div class="mcr-history-snapshot__grid">
          <article v-for="item in selectedHistorySnapshot.items" :key="item.path" class="mcr-history-snapshot__item">
            <img :src="item.src || item.url || ''" :alt="item.library || item.name" loading="lazy">
            <div><strong>{{ item.library || item.name }}</strong><span>{{ item.server || '未知服务器' }}</span><small>{{ item.uploaded === false ? '上传失败' : '已生成并保存' }}</small></div>
            <button type="button" class="mcr-history-snapshot__check" :class="{ 'is-active': selectedHistoryPaths.includes(item.path) }" :aria-pressed="selectedHistoryPaths.includes(item.path)" @click="toggleHistorySelection(item)"><v-icon :icon="selectedHistoryPaths.includes(item.path) ? 'mdi-check' : 'mdi-plus'" size="16" /></button>
          </article>
        </div>
        <footer v-if="selectedHistoryPaths.length" class="mcr-history-snapshot__footer"><span>已选择 {{ selectedHistoryPaths.length }} 项</span><v-btn class="mcr-button mcr-button--ghost" @click="downloadSelectedCoversDirect">下载</v-btn><v-btn class="mcr-button mcr-button--primary" prepend-icon="mdi-history" :loading="restoringBatchId === selectedHistorySnapshot.key" @click="restoreHistoryBatch(selectedHistorySnapshot.key, selectedHistorySnapshot.title)">应用到服务器</v-btn><v-btn class="mcr-button mcr-button--danger" @click="deleteSelectedCovers">删除</v-btn></footer>
      </v-card>
    </v-dialog>

    <v-dialog v-model="donationDialog" max-width="460" class="mcr-donation-dialog" scrim="rgba(18, 24, 38, 0.42)">
      <v-card class="mcr-donation-card" :class="{ 'mcr-donation-card--dark': isDark }">
        <v-card-text class="mcr-donation-card__body">
          <div v-if="donationView === 'overview'" class="mcr-donation-profile">
            <div class="mcr-donation-profile__avatar" :class="{ 'is-supported': donationAcknowledged }">
              <img v-if="donationAvatarImage" :src="donationAvatarImage" alt="">
              <v-icon v-else :icon="donationAvatarIcon" size="38" />
              <span class="mcr-donation-profile__crown" aria-hidden="true">
                <v-icon icon="mdi-crown" size="26" />
              </span>
            </div>
            <h3 class="mcr-donation-title">{{ donationView === 'support' ? '感谢您的支持' : '呀哈哈封面工坊' }}</h3>
            <div class="mcr-donation-subtitle">{{ donationView === 'support' ? 'Heartfelt giving' : '使用数据统计' }}</div>
          </div>
          <template v-else>
            <div class="mcr-donation-heart" aria-hidden="true">
              <v-icon icon="mdi-heart-outline" size="30" />
            </div>
            <h3 class="mcr-donation-title">感谢您的支持</h3>
          </template>
          <div v-if="donationView === 'overview'" class="mcr-donation-stats">
            <div class="mcr-donation-stat-card">
              <div class="mcr-donation-stat-card__top">
                <span class="mcr-donation-stat-icon mcr-donation-stat-icon--static">
                  <v-icon icon="mdi-view-grid-outline" size="20" />
                </span>
                <small>Active</small>
              </div>
              <strong>{{ donationStaticSchemeCount }}</strong>
              <span>静态方案</span>
            </div>
            <div class="mcr-donation-stat-card">
              <div class="mcr-donation-stat-card__top">
                <span class="mcr-donation-stat-icon mcr-donation-stat-icon--dynamic">
                  <v-icon icon="mdi-lightning-bolt-outline" size="20" />
                </span>
                <small class="mcr-donation-live-dot" aria-label="动态方案可用" />
              </div>
              <strong>{{ donationDynamicSchemeCount }}</strong>
              <span>动态方案</span>
            </div>
            <div class="mcr-donation-stat-card">
              <div class="mcr-donation-stat-card__top">
                <span class="mcr-donation-stat-icon mcr-donation-stat-icon--history">
                  <v-icon icon="mdi-layers-outline" size="20" />
                </span>
              </div>
              <strong>{{ donationHistoryCount }}</strong>
              <span>历史封面</span>
            </div>
            <div class="mcr-donation-stat-card">
              <div class="mcr-donation-stat-card__top">
                <span class="mcr-donation-stat-icon mcr-donation-stat-icon--run">
                  <v-icon icon="mdi-play-circle-outline" size="20" />
                </span>
              </div>
              <strong>{{ donationExecutionCount }}</strong>
              <span>执行次数</span>
            </div>
          </div>
          <div v-if="donationView === 'support'" class="mcr-donation-qr">
            <img class="mcr-donation-qr__image" :src="donationQrImage" alt="赞赏码">
          </div>
          <p v-if="donationView === 'support'" class="mcr-donation-message">
            您的慷慨支持是我持续创作的动力。
          </p>
          <div class="mcr-donation-card__actions">
            <v-btn
              v-if="donationView === 'support'"
              class="mcr-button mcr-button--ghost mcr-button--dark-neutral mcr-donation-soft-action"
              @click="donationDialog = false"
            >
              下次一定！
            </v-btn>
            <v-btn
              v-if="donationView === 'overview'"
              class="mcr-button mcr-button--primary mcr-button--apple-primary mcr-donation-continue-support"
              @click="donationView = 'support'"
            >
              <v-icon class="mcr-donation-support-heart" icon="mdi-heart" size="20" />
              <span>继续支持</span>
            </v-btn>
            <v-btn
              v-else
              class="mcr-button mcr-button--primary mcr-button--apple-primary mcr-donation-support-confirm"
              @click="acknowledgeDonation"
            >
              <v-icon class="mcr-donation-support-heart" icon="mdi-heart" size="20" />
              <span>已支持</span>
            </v-btn>
          </div>
          <div v-if="donationView === 'support'" class="mcr-donation-footnote">HEARTFELT GIVING • LUMINOUS CHARITY</div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-if="false" v-model="editDialog" max-width="1200" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center pa-4">
          <span class="text-h6">编辑布局</span>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" @click="editDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4" style="max-height: 75vh;">
          <!-- Canvas / Preview area: full width, same aspect as main preview -->
          <template v-if="showInlineLayoutEditor">
            <CustomLayoutEditor
              v-if="customStaticLayout"
              :key="activeEditorTemplateId || coverStyleBase"
              :model-value="customStaticLayout"
              :preview-source="previewSource"
              :params="simulationParams"
              :floating-tools-visible="false"
              :theme="isDark ? 'dark' : 'light'"
              :api="props.api"
              @update:model-value="onLayoutUpdated"
            />
            <div v-else class="mcr-history-empty">当前布局尚未初始化</div>
          </template>

          <template v-else>
            <GeneratePreviewSimulation
              :source="effectivePreviewSource"
              :params="simulationParams"
            />
          </template>

          <!-- Controls below canvas -->
          <v-row class="mt-4" dense>
            <v-col cols="12" md="6">
              <v-card variant="outlined" class="mcr-panel">
                <v-card-text class="mcr-panel__body">
                  <div class="mcr-panel__eyebrow">Controls</div>
                  <div class="mcr-panel__title">{{ showInlineLayoutEditor ? '布局控制' : '模拟参数' }}</div>

	                  <template v-if="showInlineLayoutEditor">
                    <template v-if="showPresetRenderStyleSelector">
                      <div class="mcr-panel__eyebrow mt-3">Render Mode</div>
                      <v-btn-toggle
                        v-model="presetStaticRenderMode"
                        mandatory
                        divided
                        density="comfortable"
                        class="mcr-toggle mb-3"
                      >
                        <v-btn
                          value="preset"
                          class="mcr-button mcr-button--ghost"
                          :class="{ 'mcr-button--active': presetStaticRenderMode === 'preset' }"
                        >
                          原始风格
                        </v-btn>
                        <v-btn
                          value="layout"
                          class="mcr-button mcr-button--ghost"
                          :class="{ 'mcr-button--active': presetStaticRenderMode === 'layout' }"
                        >
                          当前布局
                        </v-btn>
                      </v-btn-toggle>
                    </template>
	                    <div class="d-flex flex-wrap align-center ga-2 mb-3">
	                      <span class="mcr-editor-save-cluster">
	                        <span class="mcr-editor-split-save">
	                          <button
	                            type="button"
	                            class="mcr-button mcr-button--primary mcr-editor-save-main"
	                            :disabled="!activeEditorTemplateId || !customStaticLayout"
	                            @click="saveCustomLayoutNow"
	                          >
	                            保存当前布局
	                          </button>
	                          <button
	                            type="button"
	                            class="mcr-button mcr-button--primary mcr-editor-save-toggle"
	                            :aria-label="editorAutoSaveEnabled ? '自动保存已开启，点击关闭' : '自动保存已关闭，点击开启'"
	                            :title="editorAutoSaveEnabled ? '自动保存已开启，点击关闭' : '自动保存已关闭，点击开启'"
	                            :disabled="!activeEditorTemplateId || !customStaticLayout"
	                            @click.stop="toggleEditorAutoSave"
	                          >
	                            <span class="mcr-editor-save-mode">
	                              {{ editorAutoSaveEnabled ? 'AUTO' : 'MANUAL' }}
	                            </span>
	                          </button>
	                        </span>
	                      </span>
	                      <v-btn
                        size="small"
                        class="mcr-button mcr-button--ghost"
                        :disabled="!activeEditorTemplateId"
                        @click="restoreCurrentLayoutDefaults"
                      >
                        {{ resetButtonLabel }}
                      </v-btn>
                    </div>

                  </template>

                  <template v-else>
                    <BlueprintRange
                      v-model="simulationParams.blur"
                      :min="0"
                      :max="100"
                      :step="5"
                      class="mcr-control mt-3"
                      label="背景模糊"
                    />
                    <div class="mcr-panel__eyebrow mt-4">Color Source</div>
                    <v-btn-toggle
                      v-model="simulationParams.colorSource"
                      mandatory
                      divided
                      density="comfortable"
                      class="mcr-toggle mb-3"
                    >
                      <v-btn
                        value="auto"
                        class="mcr-button mcr-button--ghost"
                        :class="{ 'mcr-button--active': simulationParams.colorSource === 'auto' }"
                      >
                        自动取色
                      </v-btn>
                      <v-btn
                        value="config"
                        class="mcr-button mcr-button--ghost"
                        :class="{ 'mcr-button--active': simulationParams.colorSource === 'config' }"
                      >
                        标题配置
                      </v-btn>
                      <v-btn
                        value="custom"
                        class="mcr-button mcr-button--ghost"
                        :class="{ 'mcr-button--active': simulationParams.colorSource === 'custom' }"
                      >
                        调色盘
                      </v-btn>
                    </v-btn-toggle>
                    <div
                      v-if="simulationParams.colorSource === 'custom'"
                      class="sim-color-picker-row mt-2 mb-3"
                    >
                      <input
                        v-model="simulationParams.customColor"
                        type="color"
                        class="sim-color-picker"
                      />
                      <BlueprintField
                        v-model="simulationParams.customColor"
                        label="自定义融合色"
                        class="mcr-control mcr-control--compact flex-grow-1"
                      />
                    </div>
                    <BlueprintRange
                      v-model="simulationParams.colorRatio"
                      :min="0"
                      :max="1"
                      :step="0.05"
                      class="mcr-control mt-6"
                      label="颜色融合强度"
                    />
                  </template>

                </v-card-text>
              </v-card>
            </v-col>

            <v-col cols="12" md="6">
              <v-card variant="outlined" class="mcr-panel mb-4">
                <v-card-text class="mcr-panel__body">
                  <div class="mcr-panel__eyebrow">Info</div>
                  <div class="mcr-panel__title">预览信息</div>
                  <div class="info-list mt-2">
                    <div class="info-row">
                      <span class="info-label">当前风格</span>
                      <span class="info-value">{{ currentStyleLabel }} / {{ currentVariantLabel }}</span>
                    </div>
                    <div class="info-row">
                      <span class="info-label">素材来源</span>
                      <span class="info-value">{{ sourceModeLabel }}</span>
                    </div>
                    <div class="info-row">
                      <span class="info-label">服务器</span>
                      <span class="info-value">{{ activeServerLabel }}</span>
                    </div>
                    <div class="info-row">
                      <span class="info-label">媒体库</span>
                      <span class="info-value">{{ activeLibraryLabel }}</span>
                    </div>
                    <div class="info-row">
                      <span class="info-label">素材数量</span>
                      <span class="info-value">{{ activeImageCount }}</span>
                    </div>
                  </div>
                </v-card-text>
              </v-card>

              <v-card variant="outlined" class="mcr-panel">
                <v-card-text class="mcr-panel__body">
                  <div class="mcr-panel__eyebrow">Assets</div>
                  <div class="mcr-panel__title">素材摘要</div>
                  <div v-if="previewSource?.images?.length" class="source-list mt-2">
                    <div
                      v-for="image in previewSource.images"
                      :key="image.slot"
                      class="source-row"
                    >
                      <span class="source-slot">#{{ image.slot }}</span>
                      <span class="source-name">{{ image.label || '未命名素材' }}</span>
                    </div>
                  </div>
                  <div v-else class="mcr-note">
                    当前没有可展示的预览素材。
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>

        <v-divider />
        <v-card-actions class="pa-4">
          <v-btn
            size="small"
            class="mcr-button mcr-button--ghost"
            prepend-icon="mdi-refresh"
            :loading="refreshingPreview"
            @click="refreshCurrentPreview"
          >
            刷新预览
          </v-btn>
          <v-spacer />
          <v-btn
            class="mcr-button mcr-button--primary"
            @click="editDialog = false"
          >
            完成
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <ViewportSaveToast :message="editorSaveStatus" :theme="isDark ? 'dark' : 'light'" />

  </div>
</template>

<script setup lang="ts">
import '../styles/figmaTheme.css'
import { MCR_CONTROL_DEFAULTS } from '../constants/uiDefaults'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import type { PropType } from 'vue'
import BlueprintField from './BlueprintField.vue'
import BlueprintRange from './BlueprintRange.vue'
import BlueprintSelect from './BlueprintSelect.vue'
import AsyncStatusDots from './AsyncStatusDots.vue'
import CustomLayoutEditor from './CustomLayoutEditor.vue'
import GeneratePreviewSimulation from './GeneratePreviewSimulation.vue'
import ViewportSaveToast from './ViewportSaveToast.vue'
import { BUILTIN_FONT_ITEMS } from '../constants/fonts'
import { getThemeColor } from '../utils/themeColors'
import { formatDateTime, formatTimelineTime } from '../utils/dateTime'
import { getHistoryCache, getPreviewCache, setHistoryCache, setPreviewCache, stableCacheSignature } from '../services/contentCache'
import { images } from '../assets/base64/images.js'
import {
  cloneLayout,
  createDefaultLayout,
  createLayoutFromBuiltInStyle as createBuiltInLayoutTemplate,
  createLayoutId,
} from '../utils/customLayout'
import type {
  AnimatedStyleKey,
  AnimatedStyleSettings,
  BackendPreviewPayload,
  CoverStyleBase,
  CoverStyleVariant,
  CustomStaticLayout,
  CustomStaticLayoutTemplate,
  PluginApi,
  PreviewMode,
  PreviewSourcePayload,
  SimulationParams,
  StatusPayload,
} from '../types/plugin'

type PageTab = 'generate-tab' | 'history-tab'
type PresetStyleBase = Exclude<CoverStyleBase, 'custom_static'>
type StaticRenderMode = 'preset' | 'layout'
type DonationView = 'overview' | 'support'
type SchemeListItem = {
  id: string
  kind: 'preset' | 'custom'
  title: string
  baseStyle: CoverStyleBase
  templateId: string
  template?: CustomStaticLayoutTemplate
}

interface FontLibraryItem {
  title: string
  name: string
  value: string
  path?: string
  url?: string
  dataUrl?: string
}

const PRESET_STYLE_BASES: PresetStyleBase[] = ['static_1', 'static_2', 'static_3', 'static_4']

const props = defineProps({
  api: {
    type: Object as PropType<PluginApi>,
    default: () => ({} as PluginApi),
  },
})

const emit = defineEmits<{
  (e: 'action'): void
  (e: 'switch'): void
}>()

const controlDefaults = MCR_CONTROL_DEFAULTS

const pageTab = ref<PageTab>('generate-tab')
const DONATION_ACK_STORAGE_KEY = 'yahaha_supported'
const DONATION_LEGACY_ACK_STORAGE_KEY = 'mcr-donation-acknowledged'
const DONATION_AVATAR_STORAGE_KEY = 'yahaha_avatar_source'
const DONATION_RUN_COUNT_STORAGE_KEY = 'yahaha_generation_run_count'
const setupWarnings = ref<string[]>([])
const programEnabled = ref(false)
const styleVariant = ref<CoverStyleVariant>('static')
const coverStyleBase = ref<CoverStyleBase>('static_1')
const previewMode = ref<PreviewMode>('frontend')
const previewSource = ref<PreviewSourcePayload | null>(null)
const backendPreview = ref<BackendPreviewPayload | null>(null)
const donationDialog = ref(false)
const donationAcknowledged = ref(false)
const donationView = ref<DonationView>('overview')
const donationAvatarSource = ref<'developer' | 'mp'>('developer')
const donationExecutionCount = ref(0)
const moviePilotAvatarUrl = ref('')
const refreshingPreview = ref(false)
const previewSourcesLoading = ref(false)
const statusLoading = ref(false)
const historyLoading = ref(false)
const historyUpdating = ref(false)
const showingCachedHistory = ref(false)
const backendPreviewLoading = ref(false)
const styleUpdating = ref(false)
const layoutPersisting = ref(false)
const generatingNow = ref(false)
const previewCacheContext = ref<Record<string, unknown>>({})
let historyRequest: Promise<void> | null = null
let previewSourceRequestId = 0
const HISTORY_CACHE_KEY = 'all:newest'
const isGenerating = ref(false)
const statusLoaded = ref(false)
const previewBayEl = ref<HTMLElement | null>(null)
const schemeListScrollEl = ref<HTMLElement | null>(null)
const previewBayHeight = ref(0)
const schemeListCollapsed = ref(false)
const historyHeaderEl = ref<HTMLElement | null>(null)
const historyListCollapsed = ref(false)
const historyFloatingStyle = ref<Record<string, string>>({
  left: '50%',
  top: '88px',
  transform: 'translateX(-50%)',
})
const importTemplateInput = ref<HTMLInputElement | null>(null)
const modeSwitchPulse = ref(false)
const customStaticLayout = ref<CustomStaticLayout | null>(null)
const customTemplates = ref<CustomStaticLayoutTemplate[]>([])
const selectedCustomTemplateId = ref<string | null>(null)
const activeEditorTemplateId = ref<string | null>(null)
const presetStaticRenderMode = ref<StaticRenderMode>('layout')
const animatedSettingsPanelOpen = ref(false)
const animatedSettingsSaving = ref(false)
const animatedSettingsBaseStyle = ref<CoverStyleBase>('static_1')
const animatedSettingsByStyle = ref<Partial<Record<AnimatedStyleKey, AnimatedStyleSettings>>>({})
const customFontItems = ref<FontLibraryItem[]>([])
const posterSource = ref<'backdrop' | 'poster'>('backdrop')
const sourceSortBy = ref<'Random' | 'DateCreated' | 'PremiereDate'>('Random')
const sourceSortLocked = ref(false)
const imageCountMode = ref<'auto' | 'fixed'>('auto')
const imageCount = ref(9)
const autoImageCount = ref(9)
const staticResolution = ref('480p')
const animationResolution = ref('320x180')
const renderOptionsSaving = ref(false)
const generationCurrent = ref(0)
const generationTotal = ref(0)
const generationLabel = ref('')
const EDITOR_AUTO_SAVE_STORAGE_KEY = 'mcr-editor-auto-save-enabled'
const editorAutoSaveEnabled = ref(readEditorAutoSavePreference())
const editorSaveStatus = ref('')
const recentDownloadRegistry = new Map<string, number>()
const animatedSettings = reactive({
  animationDuration: 8,
  animationFps: 24,
  animationFormat: 'apng' as 'apng' | 'gif',
  animationScroll: 'alternate' as 'down' | 'up' | 'alternate' | 'alternate_reverse',
  animationReduceColors: 'medium' as 'off' | 'medium' | 'strong',
  animated2ImageCount: 6,
  animated2DepartureType: 'fly' as 'fly' | 'fade' | 'crossfade',
  mainTitleFontPreset: 'chaohei',
  subtitleFontPreset: 'EmblemaOne',
  customTextFontPreset: 'EmblemaOne',
  mainTitleFontSize: 170,
  subtitleFontSize: 75,
  blurSize: 50,
  colorRatio: 0.8,
  titleScale: 1,
})

const controlBayStyle = computed(() =>
  previewBayHeight.value > 0
    ? { '--mcr-scheme-panel-height': `${previewBayHeight.value}px` }
    : {},
)

const simulationParams = reactive<SimulationParams>({
  blur: 50,
  colorRatio: 0.8,
  colorSource: 'auto',
  customColor: getThemeColor('--mcr-cover-auto-blend'),
})

interface HistoryItem {
  name: string
  size: string
  src?: string
  url?: string
  path: string
  server?: string
  library?: string
  date?: string
  date_label?: string
  mtime?: string
  mtime_ts?: number
  batch_id?: string
  created_at?: string | number
  uploaded?: boolean
  upload_error?: string
}

interface HistoryGroup { key: string; title: string; items: HistoryItem[] }

const history = ref<HistoryItem[]>([])
const historyGroupMode = ref<'library' | 'time-machine'>('library')
const restoringBatchId = ref('')
const activeTimeRecordId = ref('')
const historySnapshotDialog = ref(false)
const selectedHistorySnapshot = ref<(HistoryGroup & { fullTitle: string }) | null>(null)
const restoreConfirmDialog = ref(false)
const pendingHistoryRestore = ref<{ batchId: string; label: string } | null>(null)
const historyStackLimit = ref(5)
const historySortMode = ref<'newest' | 'oldest' | 'name'>('newest')
const selectedHistoryPaths = ref<string[]>([])
const donationAvatarIcon = computed(() =>
  donationAvatarSource.value === 'mp' ? 'mdi-account-circle-outline' : 'mdi-image-filter-hdr-outline',
)
const donationAvatarImage = computed(() =>
  donationAvatarSource.value === 'developer' ? images.avatar : moviePilotAvatarUrl.value,
)
const donationQrImage = computed(() => (isDark.value ? images.wx_code_dark : images.wx_code_light))
const donationStaticSchemeCount = computed(() => PRESET_STYLE_BASES.length + getUserCustomTemplates(customTemplates.value).length)
const donationDynamicSchemeCount = computed(() => PRESET_STYLE_BASES.length)
const donationSchemeCount = computed(() => donationStaticSchemeCount.value + donationDynamicSchemeCount.value)
const donationHistoryCount = computed(() => history.value.length || 0)
const sourceSortDisabled = computed(() => controlsLocked.value || sourceSortLocked.value)

const editDialog = ref(false)
const isEditingLayout = ref(false)
const controlsLocked = computed(() => isGenerating.value || generatingNow.value || !statusLoaded.value)
const resourceSkeletonActive = computed(() => previewSourcesLoading.value || !statusLoaded.value)
const backendBusy = computed(() =>
  statusLoading.value
  || historyLoading.value
  || backendPreviewLoading.value
  || previewSourcesLoading.value
  || styleUpdating.value
  || layoutPersisting.value
  || animatedSettingsSaving.value
  || renderOptionsSaving.value
  || generatingNow.value,
)
const backendBusyLabel = computed(() => {
  if (isGenerating.value) {
    if (generationTotal.value > 0) {
      return `正在生成 ${generationCurrent.value || 0}/${generationTotal.value}`
    }
    return generationLabel.value || '正在生成'
  }
  if (generatingNow.value) return '正在执行'
  if (renderOptionsSaving.value) return '保存素材'
  if (animatedSettingsSaving.value) return '保存参数'
  if (layoutPersisting.value) return '保存布局'
  if (styleUpdating.value) return '切换方案'
  if (historyLoading.value) return '加载历史'
  if (backendPreviewLoading.value) return '渲染预览'
  if (previewSourcesLoading.value) return '加载素材'
  return '同步数据'
})

const prefersDark = ref(false)
const hostThemeVersion = ref(0)
let pageThemeMediaQuery: MediaQueryList | null = null
let pageThemeObserver: MutationObserver | null = null

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

const styleItems: Array<{ title: string; value: CoverStyleBase }> = [
  { title: '风格 1', value: 'static_1' },
  { title: '风格 2', value: 'static_2' },
  { title: '风格 3', value: 'static_3' },
  { title: '风格 4', value: 'static_4' },
  { title: '自定义', value: 'custom_static' },
]

function getStyleTitle(value: CoverStyleBase) {
  return styleItems.find((item) => item.value === value)?.title || value
}

function stripPresetEditableSuffix(name: string) {
  return String(name || '').replace(/\s*可编辑布局$/u, '').trim()
}

function getPresetSchemeTitle(baseStyle: PresetStyleBase, template?: CustomStaticLayoutTemplate | null) {
  return stripPresetEditableSuffix(template?.name || '') || getStyleTitle(baseStyle)
}

function normalizeCoverStyleBase(value?: string): CoverStyleBase {
  if (value === 'static_1' || value === 'static_2' || value === 'static_3' || value === 'static_4' || value === 'custom_static') {
    return value
  }
  return 'static_1'
}

function isPresetStaticStyle(value?: string | null): value is PresetStyleBase {
  return PRESET_STYLE_BASES.includes(value as PresetStyleBase)
}

function isSystemTemplate(template?: CustomStaticLayoutTemplate | null) {
  return Boolean(template?.system) || String(template?.id || '').startsWith('__preset_')
}

function normalizeTemplateList(templates?: CustomStaticLayoutTemplate[] | null) {
  if (!Array.isArray(templates)) return []
  return templates.map((tpl) => ({
    ...tpl,
    layout: cloneLayout(tpl.layout),
  }))
}

function getTemplateById(id: string | null) {
  if (!id) return null
  return customTemplates.value.find((tpl) => tpl.id === id) ?? null
}

function getUserCustomTemplates(templates: CustomStaticLayoutTemplate[] = customTemplates.value) {
  return templates.filter((tpl) => !isSystemTemplate(tpl))
}

function getStyleDefaultLayout(baseStyle?: string | null) {
  if (isPresetStaticStyle(baseStyle)) {
    return createBuiltInLayoutTemplate(baseStyle)
  }
  return createDefaultLayout()
}

function buildPresetTemplate(baseStyle: PresetStyleBase): CustomStaticLayoutTemplate {
  return {
    id: `__preset_${baseStyle}`,
    name: getStyleTitle(baseStyle),
    layout: cloneLayout(getStyleDefaultLayout(baseStyle)),
    baseStyle,
    system: true,
  }
}

function ensurePresetTemplate(baseStyle: PresetStyleBase) {
  const templateId = `__preset_${baseStyle}`
  const existing = getTemplateById(templateId)
  if (existing) return existing

  const presetTemplate = buildPresetTemplate(baseStyle)
  customTemplates.value = [...customTemplates.value, presetTemplate]
  return presetTemplate
}

function setEditorTemplate(templateId: string | null) {
  activeEditorTemplateId.value = templateId
  const template = getTemplateById(templateId)
  customStaticLayout.value = template ? cloneLayout(template.layout) : null
}

function setSelectedCustomTemplate(templateId: string | null) {
  selectedCustomTemplateId.value = templateId
  setEditorTemplate(templateId)
}

function syncLayoutToTemplate(templateId: string | null, layout: CustomStaticLayout | null) {
  if (!templateId || !layout) return
  const index = customTemplates.value.findIndex((tpl) => tpl.id === templateId)
  if (index === -1) return
  const next = [...customTemplates.value]
  next[index] = {
    ...next[index],
    layout: cloneLayout(layout),
  }
  customTemplates.value = next
}

function applyCustomTemplateState(templates: CustomStaticLayoutTemplate[], preferredCustomId?: string | null) {
  customTemplates.value = normalizeTemplateList(templates)
  const userTemplates = getUserCustomTemplates(customTemplates.value)

  if (preferredCustomId && userTemplates.some((tpl) => tpl.id === preferredCustomId)) {
    selectedCustomTemplateId.value = preferredCustomId
    return
  }
  if (selectedCustomTemplateId.value && userTemplates.some((tpl) => tpl.id === selectedCustomTemplateId.value)) {
    return
  }
  selectedCustomTemplateId.value = userTemplates[0]?.id ?? null
}

function ensureCustomTemplateInitialized() {
  const userTemplates = getUserCustomTemplates()
  if (!userTemplates.length) {
    const id = createLayoutId()
    const template: CustomStaticLayoutTemplate = {
      id,
      name: '自定义方案',
      layout: cloneLayout(customStaticLayout.value || createDefaultLayout()),
      baseStyle: 'custom_static',
    }
    customTemplates.value = [...customTemplates.value, template]
    setSelectedCustomTemplate(id)
    return
  }

  if (selectedCustomTemplateId.value && userTemplates.some((tpl) => tpl.id === selectedCustomTemplateId.value)) {
    setEditorTemplate(selectedCustomTemplateId.value)
    return
  }

  setSelectedCustomTemplate(userTemplates[0].id)
}

const schemeListItems = computed<SchemeListItem[]>(() => {
  const presetItems = PRESET_STYLE_BASES.map((baseStyle) => {
    const templateId = `__preset_${baseStyle}`
    const template = getTemplateById(templateId) || undefined
    return {
      id: templateId,
      kind: 'preset' as const,
      title: getPresetSchemeTitle(baseStyle, template),
      baseStyle,
      templateId,
      template,
    }
  })

  const customItems = getUserCustomTemplates().map((template) => ({
    id: template.id,
    kind: 'custom' as const,
    title: template.name || '自定义方案',
    baseStyle: 'custom_static' as CoverStyleBase,
    templateId: template.id,
    template,
  }))

  return styleVariant.value === 'animated' ? presetItems : [...presetItems, ...customItems]
})

const schemeListKey = computed(() =>
  `${styleVariant.value}:${schemeListItems.value.map((item) => item.id).join('|')}`,
)

function getReservedSchemeNames(ignoreId?: string) {
  const names = new Set<string>()
  for (const baseStyle of PRESET_STYLE_BASES) {
    const presetId = `__preset_${baseStyle}`
    if (presetId !== ignoreId) {
      names.add(getPresetSchemeTitle(baseStyle, getTemplateById(presetId)))
    }
  }
  for (const template of customTemplates.value) {
    if (template.id === ignoreId) continue
    if (isSystemTemplate(template) && isPresetStaticStyle(template.baseStyle)) {
      names.add(getPresetSchemeTitle(template.baseStyle, template))
      continue
    }
    if (template.name?.trim()) {
      names.add(template.name.trim())
    }
  }
  return names
}

function getUniqueTemplateName(name: string, ignoreId?: string) {
  const baseName = String(name || '').trim() || '自定义方案'
  const reserved = getReservedSchemeNames(ignoreId)
  if (!reserved.has(baseName)) return baseName

  let index = 2
  let nextName = `${baseName} ${index}`
  while (reserved.has(nextName)) {
    index += 1
    nextName = `${baseName} ${index}`
  }
  return nextName
}

function resolveSchemeTemplate(item: SchemeListItem, ensure = false) {
  if (item.kind === 'preset') {
    const template = ensure && isPresetStaticStyle(item.baseStyle)
      ? ensurePresetTemplate(item.baseStyle)
      : getTemplateById(item.templateId) || buildPresetTemplate(item.baseStyle as PresetStyleBase)
    return template
      ? {
        ...template,
        name: getPresetSchemeTitle(item.baseStyle as PresetStyleBase, template),
        layout: cloneLayout(template.layout),
      }
      : null
  }
  return getTemplateById(item.templateId)
}

let generationStatusTimer: number | null = null
let measureLayoutTimer: number | null = null
let measureLayoutApiAvailable = true
let measureLayoutRequestToken = 0
let lastCustomLayoutPersistAt = 0
let autoSaveLayoutTimer: number | null = null
let editorSaveStatusTimer: number | null = null
let autoSaveInFlight = false
let autoSaveQueued = false
let previewSourceReloadTimer: number | null = null
let syncingBackendState = false
let statusLoadPromise: Promise<boolean> | null = null
let componentActive = false
let previewBayResizeObserver: ResizeObserver | null = null
let editorEnterScrollToken = 0

function updatePreviewBayHeight() {
  if (typeof window === 'undefined') return
  const el = previewBayEl.value
  if (!el || isEditingLayout.value) {
    previewBayHeight.value = 0
    return
  }
  previewBayHeight.value = Math.round(el.getBoundingClientRect().height)
}

function isMobileViewport() {
  return typeof window !== 'undefined' && window.matchMedia('(max-width: 959px)').matches
}

function waitForAnimationFrame() {
  return new Promise<void>((resolve) => {
    window.requestAnimationFrame(() => resolve())
  })
}

function isScrollableElement(el: HTMLElement) {
  const style = window.getComputedStyle(el)
  const overflowY = style.overflowY
  return /(auto|scroll|overlay)/.test(overflowY) && el.scrollHeight > el.clientHeight + 2
}

function getScrollableAncestors(el: HTMLElement) {
  const ancestors: HTMLElement[] = []
  let current = el.parentElement
  while (current && current !== document.body && current !== document.documentElement) {
    if (isScrollableElement(current)) {
      ancestors.push(current)
    }
    current = current.parentElement
  }
  return ancestors
}

function alignElementInScroller(el: HTMLElement, scroller: HTMLElement, offset: number, behavior: ScrollBehavior) {
  const targetRect = el.getBoundingClientRect()
  const scrollerRect = scroller.getBoundingClientRect()
  const nextTop = scroller.scrollTop + targetRect.top - scrollerRect.top - offset
  scroller.scrollTo({
    top: Math.max(0, nextTop),
    behavior,
  })
}

function alignElementInDocument(el: HTMLElement, offset: number, behavior: ScrollBehavior) {
  const targetRect = el.getBoundingClientRect()
  const nextTop = window.scrollY + targetRect.top - offset
  window.scrollTo({
    top: Math.max(0, nextTop),
    behavior,
  })
}

function alignEditorTitleToViewport(behavior: ScrollBehavior) {
  const targetRoot = previewBayEl.value
  if (!targetRoot) return
  const heading = targetRoot.querySelector<HTMLElement>('.blueprint-panel-heading')
  const target = heading ?? targetRoot
  const offset = 10
  const scroller = getScrollableAncestors(target)[0]
  if (scroller) {
    alignElementInScroller(target, scroller, offset, behavior)
  }
  alignElementInDocument(target, offset, behavior)
}

async function scrollEditorIntoView() {
  const token = ++editorEnterScrollToken
  await nextTick()
  if (typeof window === 'undefined' || !isMobileViewport()) return
  await waitForAnimationFrame()
  await waitForAnimationFrame()
  if (token !== editorEnterScrollToken) return
  alignEditorTitleToViewport('smooth')
  const cancelDelayedAlignment = () => {
    editorEnterScrollToken += 1
    window.removeEventListener('pointerdown', cancelDelayedAlignment, true)
  }
  window.addEventListener('pointerdown', cancelDelayedAlignment, true)
  window.setTimeout(() => {
    window.removeEventListener('pointerdown', cancelDelayedAlignment, true)
    if (token !== editorEnterScrollToken) return
    alignEditorTitleToViewport('auto')
  }, 220)
}

async function normalizeSchemeListViewport() {
  await nextTick()
  if (typeof window === 'undefined') return
  window.requestAnimationFrame(() => {
    const el = schemeListScrollEl.value
    if (el) {
      const maxScrollTop = Math.max(0, el.scrollHeight - el.clientHeight)
      if (el.scrollTop > maxScrollTop) {
        el.scrollTop = maxScrollTop
      }
      if (maxScrollTop === 0) {
        el.scrollTop = 0
      }
    }
    updatePreviewBayHeight()
  })
}

function cancelPendingLayoutMeasure() {
  measureLayoutRequestToken += 1
  if (measureLayoutTimer !== null) {
    window.clearTimeout(measureLayoutTimer)
    measureLayoutTimer = null
  }
}

function cancelPendingAutoSave() {
  if (autoSaveLayoutTimer !== null) {
    window.clearTimeout(autoSaveLayoutTimer)
    autoSaveLayoutTimer = null
  }
  if (editorSaveStatusTimer !== null) {
    window.clearTimeout(editorSaveStatusTimer)
    editorSaveStatusTimer = null
  }
}

function showEditorSaveStatus(text: string) {
  editorSaveStatus.value = text
  if (editorSaveStatusTimer !== null) {
    window.clearTimeout(editorSaveStatusTimer)
  }
  editorSaveStatusTimer = window.setTimeout(() => {
    editorSaveStatus.value = ''
    editorSaveStatusTimer = null
  }, 2400)
}

function toggleEditorAutoSave() {
  editorAutoSaveEnabled.value = !editorAutoSaveEnabled.value
  showEditorSaveStatus(editorAutoSaveEnabled.value ? '已开启自动保存' : '已关闭自动保存')
}

function cancelPendingPreviewSourceReload() {
  if (previewSourceReloadTimer !== null) {
    window.clearTimeout(previewSourceReloadTimer)
    previewSourceReloadTimer = null
  }
}

function shouldBlockLockedAction() {
  if (!controlsLocked.value) return false
  if (!isGenerating.value) {
    void loadStatus()
  }
  return true
}

function isStickerLayerLike(layer: any): boolean {
  if (!layer || typeof layer !== 'object') return false
  return layer.assetKind === 'sticker' || Boolean(layer.stickerDataUrl || layer.stickerPath || layer.stickerUrl)
}

function getLayoutMaxImageSourceIndex(layout: CustomStaticLayout | null | undefined): number {
  const visit = (layers: any[]): number =>
    layers.reduce((maxIndex, layer) => {
      if (!layer || typeof layer !== 'object') return maxIndex
      const childMax = layer.type === 'group' ? visit(layer.children || []) : 0
      if (layer.type !== 'image') return Math.max(maxIndex, childMax)
      if (isStickerLayerLike(layer)) return Math.max(maxIndex, childMax)
      const sourceIndex = Number(layer.sourceIndex ?? layer.source?.slot ?? 1)
      return Math.max(maxIndex, childMax, Number.isFinite(sourceIndex) ? sourceIndex : 1)
    }, 0)
  return Math.max(1, visit(layout?.layers || []))
}

function schedulePreviewSourceReloadForLayout(layout: CustomStaticLayout | null | undefined) {
  if (controlsLocked.value) return
  const requiredItems = Math.max(1, getLayoutMaxImageSourceIndex(layout))
  const currentItems = previewSource.value?.images?.length || 0
  if (requiredItems <= currentItems) return
  cancelPendingPreviewSourceReload()
  previewSourceReloadTimer = window.setTimeout(() => {
    previewSourceReloadTimer = null
    void loadPreviewSources(requiredItems)
  }, 240)
}

function scheduleAutoSaveCustomLayout() {
  if (controlsLocked.value) return
  if (!editorAutoSaveEnabled.value) return
  if (!showInlineLayoutEditor.value || !customStaticLayout.value || !activeEditorTemplateId.value) return
  cancelPendingAutoSave()
  autoSaveLayoutTimer = window.setTimeout(() => {
    autoSaveLayoutTimer = null
    void flushAutoSaveCustomLayout()
  }, 900)
}

function readEditorAutoSavePreference() {
  if (typeof window === 'undefined') return true
  return window.localStorage.getItem(EDITOR_AUTO_SAVE_STORAGE_KEY) !== 'false'
}

async function flushAutoSaveCustomLayout() {
  if (controlsLocked.value) {
    cancelPendingAutoSave()
    autoSaveQueued = false
    return
  }
  if (!showInlineLayoutEditor.value || !customStaticLayout.value || !activeEditorTemplateId.value) return
  if (autoSaveInFlight) {
    autoSaveQueued = true
    return
  }
  autoSaveInFlight = true
  try {
    await persistCustomLayoutState()
    showEditorSaveStatus('已自动保存')
  } finally {
    autoSaveInFlight = false
    if (autoSaveQueued) {
      autoSaveQueued = false
      scheduleAutoSaveCustomLayout()
    }
  }
}

function startGenerationStatusPoller() {
  if (generationStatusTimer !== null) return
  generationStatusTimer = window.setInterval(() => {
    if (!componentActive) return
    void loadStatus()
  }, 2000)
}

function stopGenerationStatusPoller() {
  if (generationStatusTimer === null) return
  window.clearInterval(generationStatusTimer)
  generationStatusTimer = null
}

async function refreshAfterGenerationComplete() {
  if (!componentActive) return
  await loadPreviewSources()
  if (!componentActive) return
  if (previewMode.value === 'backend') {
    await loadBackendPreview()
  } else {
    backendPreview.value = null
  }
}

async function measureCustomLayout(layout: CustomStaticLayout | null) {
  if (!layout || !measureLayoutApiAvailable) return null
  try {
    const resp = await props.api.post<{
      code: number
      data?: CustomStaticLayout
      msg?: string
    }>('plugin/MediaCoverGenerator/measure_custom_static_layout', { layout })
    if (resp?.code === 0 && resp.data) {
      return cloneLayout(resp.data)
    }
  } catch (error) {
    const status = (error as any)?.response?.status
    if (status === 404) {
      measureLayoutApiAvailable = false
      console.warn('measure_custom_static_layout is unavailable on current backend, fallback to frontend layout preview')
      return null
    }
    console.error('measureCustomLayout failed', error)
  }
  return null
}

function mergeMeasuredLayout(
  baseLayout: CustomStaticLayout,
  measuredLayout: CustomStaticLayout | null,
) {
  const nextLayout = cloneLayout(baseLayout)
  if (measuredLayout?.computed) {
    nextLayout.computed = cloneLayout(measuredLayout).computed
  } else {
    delete nextLayout.computed
  }
  return nextLayout
}

function scheduleMeasureCustomLayout(layout: CustomStaticLayout | null) {
  if (controlsLocked.value) return
  measureLayoutRequestToken += 1
  if (!layout) return
  const requestToken = measureLayoutRequestToken
  const snapshot = cloneLayout(layout)
  const templateId = activeEditorTemplateId.value
  if (measureLayoutTimer !== null) {
    window.clearTimeout(measureLayoutTimer)
  }
  measureLayoutTimer = window.setTimeout(() => {
    measureLayoutTimer = null
    void (async () => {
      const measured = await measureCustomLayout(snapshot)
      if (!measured) return
      if (requestToken !== measureLayoutRequestToken) return
      if (!customStaticLayout.value) return
      if (activeEditorTemplateId.value !== templateId) return
      const mergedLayout = mergeMeasuredLayout(customStaticLayout.value, measured)
      customStaticLayout.value = mergedLayout
      syncLayoutToTemplate(templateId, mergedLayout)
    })()
  }, 180)
}

function hydrateEditorForCurrentStyle() {
  if (styleVariant.value !== 'static') {
    activeEditorTemplateId.value = null
    customStaticLayout.value = null
    return
  }

  if (isPresetStaticStyle(coverStyleBase.value)) {
    const presetTemplate = ensurePresetTemplate(coverStyleBase.value)
    setEditorTemplate(presetTemplate.id)
    scheduleMeasureCustomLayout(customStaticLayout.value)
    return
  }

  if (coverStyleBase.value === 'custom_static') {
    ensureCustomTemplateInitialized()
    scheduleMeasureCustomLayout(customStaticLayout.value)
    return
  }

  activeEditorTemplateId.value = null
  customStaticLayout.value = null
}

const showInlineLayoutEditor = computed(() =>
  styleVariant.value === 'static' && (isPresetStaticStyle(coverStyleBase.value) || coverStyleBase.value === 'custom_static'),
)

const showPresetRenderStyleSelector = computed(() =>
  showInlineLayoutEditor.value && isPresetStaticStyle(coverStyleBase.value),
)

const effectiveStaticRenderMode = computed<StaticRenderMode>(() =>
  coverStyleBase.value === 'custom_static' ? 'layout' : presetStaticRenderMode.value,
)

const useInlineLayoutForBackend = computed(() =>
  showInlineLayoutEditor.value && effectiveStaticRenderMode.value === 'layout' && !!customStaticLayout.value,
)

const effectivePreviewSource = computed<PreviewSourcePayload | null>(() => {
  const source = previewSource.value
  if (!source) return null
  const shouldUseCurrentLayout =
    showInlineLayoutEditor.value
    && !!customStaticLayout.value
    && effectiveStaticRenderMode.value === 'layout'

  return {
    ...source,
    cover_style_base: coverStyleBase.value,
    cover_style_variant: coverStyleBase.value === 'custom_static' ? 'static' : styleVariant.value,
    custom_static_layout: shouldUseCurrentLayout ? cloneLayout(customStaticLayout.value as CustomStaticLayout) : null,
  }
})
const showMainPreviewSkeleton = computed(() => !effectivePreviewSource.value)
const showStylePreviewSkeleton = computed(() => !previewSource.value)

function getCustomCardLayout(templateId?: string | null): CustomStaticLayout | null {
  const template = templateId
    ? getTemplateById(templateId)
    : selectedCustomTemplateId.value
      ? getTemplateById(selectedCustomTemplateId.value)
      : getUserCustomTemplates()[0] || null
  if (template && !isSystemTemplate(template)) {
    return cloneLayout(template.layout)
  }
  if (coverStyleBase.value === 'custom_static' && customStaticLayout.value) {
    return cloneLayout(customStaticLayout.value)
  }
  return previewSource.value?.custom_static_layout ? cloneLayout(previewSource.value.custom_static_layout) : null
}

function getPresetCardLayout(baseStyle: CoverStyleBase): CustomStaticLayout | null {
  if (!isPresetStaticStyle(baseStyle)) return null
  const template = getTemplateById(`__preset_${baseStyle}`)
  return template ? cloneLayout(template.layout) : cloneLayout(getStyleDefaultLayout(baseStyle))
}

function buildSchemePreviewSource(item: SchemeListItem): PreviewSourcePayload | null {
  const source = previewSource.value
  if (!source) return null
  const layout = item.kind === 'custom'
    ? getCustomCardLayout(item.templateId)
    : getPresetCardLayout(item.baseStyle)

  return {
    ...source,
    cover_style_base: item.baseStyle,
    cover_style_variant: item.kind === 'custom' ? 'static' : styleVariant.value,
    custom_static_layout: layout ? cloneLayout(layout) : null,
  }
}

function isSchemeItemActive(item: SchemeListItem) {
  if (item.kind === 'preset') {
    return coverStyleBase.value === item.baseStyle
  }
  return coverStyleBase.value === 'custom_static' && selectedCustomTemplateId.value === item.templateId
}

async function openStyleEditor(baseStyle: CoverStyleBase, variant: CoverStyleVariant = styleVariant.value) {
  if (shouldBlockLockedAction()) return
  if (coverStyleBase.value !== baseStyle) {
    await setCoverStyle(baseStyle, variant)
  } else if (styleVariant.value !== variant) {
    await setCoverStyle(baseStyle, variant)
  }
  hydrateEditorForCurrentStyle()
  if (isPresetStaticStyle(baseStyle)) {
    presetStaticRenderMode.value = 'layout'
  }
  const wasEditingLayout = isEditingLayout.value
  isEditingLayout.value = true
  if (!wasEditingLayout) {
    await scrollEditorIntoView()
  }
}

async function selectSchemeItem(item: SchemeListItem) {
  if (shouldBlockLockedAction()) return
  animatedSettingsPanelOpen.value = false
  if (item.kind === 'custom') {
    await persistCurrentEditorState()
    setSelectedCustomTemplate(item.templateId)
    await setCoverStyle('custom_static')
    return
  }
  await setCoverStyle(item.baseStyle)
}

async function editSchemeItem(item: SchemeListItem) {
  if (shouldBlockLockedAction()) return
  if (item.kind === 'custom') {
    await selectSchemeItem(item)
    hydrateEditorForCurrentStyle()
    const wasEditingLayout = isEditingLayout.value
    isEditingLayout.value = true
    if (!wasEditingLayout) {
      await scrollEditorIntoView()
    }
    return
  }

  await openStyleEditor(item.baseStyle, 'static')
}

function getAnimatedStyleKey(baseStyle: CoverStyleBase): AnimatedStyleKey {
  if (baseStyle === 'static_2') return 'animated_2'
  if (baseStyle === 'static_3') return 'animated_3'
  if (baseStyle === 'static_4') return 'animated_4'
  return 'animated_1'
}

function clampNumber(value: unknown, min: number, max: number, fallback: number) {
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return fallback
  return Math.max(min, Math.min(max, Math.round(parsed)))
}

function clampFloat(value: unknown, min: number, max: number, fallback: number) {
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return fallback
  return Math.max(min, Math.min(max, parsed))
}

function syncAnimatedSettings(data?: Partial<StatusPayload> | null, baseStyle: CoverStyleBase = animatedSettingsBaseStyle.value) {
  if (data?.animated_settings) {
    animatedSettingsByStyle.value = {
      ...animatedSettingsByStyle.value,
      ...data.animated_settings,
    }
  }

  const styleKey = getAnimatedStyleKey(baseStyle)
  const styleSettings = animatedSettingsByStyle.value[styleKey]
  const source = styleSettings || data
  if (!source) return

  animatedSettings.animationDuration = clampNumber(source.animation_duration ?? animatedSettings.animationDuration, 1, 60, 8)
  animatedSettings.animationFps = clampNumber(source.animation_fps ?? animatedSettings.animationFps, 1, 60, 24)
  animatedSettings.animationFormat = source.animation_format === 'gif' ? 'gif' : 'apng'
  animatedSettings.animationScroll = ['down', 'up', 'alternate', 'alternate_reverse'].includes(String(source.animation_scroll))
    ? source.animation_scroll as 'down' | 'up' | 'alternate' | 'alternate_reverse'
    : 'alternate'
  animatedSettings.animationReduceColors = ['off', 'medium', 'strong'].includes(String(source.animation_reduce_colors))
    ? source.animation_reduce_colors as 'off' | 'medium' | 'strong'
    : 'medium'
  animatedSettings.animated2ImageCount = clampNumber(source.animated_2_image_count ?? animatedSettings.animated2ImageCount, 3, 60, 6)
  animatedSettings.animated2DepartureType = ['fly', 'fade', 'crossfade'].includes(String(source.animated_2_departure_type))
    ? source.animated_2_departure_type as 'fly' | 'fade' | 'crossfade'
    : 'fly'
  animatedSettings.mainTitleFontPreset = String(source.main_title_font_preset || animatedSettings.mainTitleFontPreset || 'chaohei')
  animatedSettings.subtitleFontPreset = String(source.subtitle_font_preset || animatedSettings.subtitleFontPreset || 'EmblemaOne')
  animatedSettings.customTextFontPreset = String(source.custom_text_font_preset || animatedSettings.customTextFontPreset || animatedSettings.subtitleFontPreset || 'EmblemaOne')
  animatedSettings.mainTitleFontSize = clampNumber(source.main_title_font_size ?? animatedSettings.mainTitleFontSize, 24, 320, 170)
  animatedSettings.subtitleFontSize = clampNumber(source.subtitle_font_size ?? animatedSettings.subtitleFontSize, 12, 220, 75)
  animatedSettings.blurSize = clampNumber(source.blur_size ?? animatedSettings.blurSize, 0, 100, 50)
  animatedSettings.colorRatio = clampFloat(source.color_ratio ?? animatedSettings.colorRatio, 0, 1, 0.8)
  animatedSettings.titleScale = clampFloat(source.title_scale ?? animatedSettings.titleScale, 0.2, 3, 1)
}

function syncRenderOptions(data?: Partial<StatusPayload> | null) {
  if (!data) return
  sourceSortLocked.value = Boolean(data.lock_latest_sort)
  posterSource.value = data.poster_source === 'poster' || data.use_primary ? 'poster' : 'backdrop'
  sourceSortBy.value = ['Random', 'DateCreated', 'PremiereDate'].includes(String(data.sort_by))
    ? data.sort_by as 'Random' | 'DateCreated' | 'PremiereDate'
    : 'Random'
  imageCountMode.value = data.image_count_mode === 'fixed' ? 'fixed' : 'auto'
  imageCount.value = clampNumber(data.image_count ?? imageCount.value, 1, 60, 9)
  autoImageCount.value = clampNumber(data.auto_image_count ?? autoImageCount.value, 1, 60, 9)
  staticResolution.value = ['480p', '720p', '1080p'].includes(String(data.resolution))
    ? String(data.resolution)
    : '480p'
  animationResolution.value = typeof data.animation_resolution === 'string' && data.animation_resolution.trim()
    ? data.animation_resolution.trim()
    : '320x180'
}

async function saveRenderOptions() {
  if (shouldBlockLockedAction()) return
  imageCount.value = clampNumber(imageCount.value, 1, 60, 9)
  renderOptionsSaving.value = true
  try {
    const payload = {
      poster_source: posterSource.value,
      sort_by: sourceSortBy.value,
      image_count_mode: imageCountMode.value,
      image_count: imageCount.value,
      resolution: staticResolution.value,
    }
    const resp = await props.api.post<{
      code: number
      data?: Partial<StatusPayload>
      msg?: string
    }>('plugin/MediaCoverGenerator/set_render_options', payload)
    if (resp && resp.code !== 0) {
      throw new Error(resp.msg || 'save render options failed')
    }
    syncRenderOptions(resp?.data || payload)
    showEditorSaveStatus('已自动保存')
    backendPreview.value = null
    await loadPreviewSources()
    if (previewMode.value === 'backend') {
      await loadBackendPreview()
    }
  } catch (e) {
    console.error('save render options failed', e)
  } finally {
    renderOptionsSaving.value = false
  }
}

async function openAnimatedSettings(item: SchemeListItem) {
  if (shouldBlockLockedAction()) return
  if (item.kind !== 'preset') return
  animatedSettingsBaseStyle.value = item.baseStyle
  syncAnimatedSettings(null, item.baseStyle)
  animatedSettingsPanelOpen.value = true
  if (coverStyleBase.value !== item.baseStyle || styleVariant.value !== 'animated') {
    await setCoverStyle(item.baseStyle, 'animated')
  }
  syncAnimatedSettings(null, item.baseStyle)
}

async function saveAnimatedSettings() {
  if (shouldBlockLockedAction()) return
  animatedSettingsSaving.value = true
  try {
    const payload = {
      style: getAnimatedStyleKey(animatedSettingsBaseStyle.value),
      animation_duration: animatedSettings.animationDuration,
      animation_fps: animatedSettings.animationFps,
      animation_format: animatedSettings.animationFormat,
      animation_scroll: animatedSettings.animationScroll,
      animation_reduce_colors: animatedSettings.animationReduceColors,
      animated_2_image_count: animatedSettings.animated2ImageCount,
      animated_2_departure_type: animatedSettings.animated2DepartureType,
      main_title_font_preset: animatedSettings.mainTitleFontPreset,
      subtitle_font_preset: animatedSettings.subtitleFontPreset,
      custom_text_font_preset: animatedSettings.customTextFontPreset,
      main_title_font_size: animatedSettings.mainTitleFontSize,
      subtitle_font_size: animatedSettings.subtitleFontSize,
      blur_size: animatedSettings.blurSize,
      color_ratio: animatedSettings.colorRatio,
      title_scale: animatedSettings.titleScale,
    }
    const resp = await props.api.post<{
      code: number
      data?: Partial<StatusPayload>
      msg?: string
    }>('plugin/MediaCoverGenerator/set_animated_settings', payload)
    if (resp && resp.code !== 0) {
      throw new Error(resp.msg || 'save animated settings failed')
    }
    syncAnimatedSettings(resp?.data || payload, animatedSettingsBaseStyle.value)
    showEditorSaveStatus('已保存')
    backendPreview.value = null
    await loadPreviewSources()
  } catch (e) {
    console.error('save animated settings failed', e)
  } finally {
    animatedSettingsSaving.value = false
  }
}

const showSupplementalBackendPreview = computed(() =>
  showInlineLayoutEditor.value && previewMode.value === 'backend',
)

function resolveRequestedCoverStyle(
  baseStyle: CoverStyleBase = coverStyleBase.value,
  variant: CoverStyleVariant = styleVariant.value,
) {
  if (baseStyle === 'custom_static') return 'custom_static'
  const suffix = baseStyle.split('_')[1] || '1'
  return variant === 'animated' ? `animated_${suffix}` : `static_${suffix}`
}

const previewModeLabel = computed(() => {
  if (showInlineLayoutEditor.value) {
    return effectiveStaticRenderMode.value === 'layout' ? '可编辑画布预览' : '静态风格模拟预览'
  }
  return '前端模拟预览'
})

const previewDescription = computed(() => {
  if (showInlineLayoutEditor.value) {
    return '静态风格已统一成可编辑画布，拖拽图层或在下方属性面板直接修改参数。'
  }
  return '仅用于快速调参，结果为浏览器模拟。'
})

const inlineEditorHint = computed(() => {
  if (coverStyleBase.value === 'custom_static') {
    return '当前为自定义风格画布，图层参数直接在画布和下方属性面板中修改。'
  }
  return useInlineLayoutForBackend.value
    ? '当前预设风格已切到“当前布局”渲染；修改后仍可一键恢复回预设默认值。'
    : '当前预设风格仍按原始风格渲染；切到“当前布局”后才会按画布参数生成。'
})

const layoutControlHint = computed(() => {
  if (coverStyleBase.value === 'custom_static') {
    return '自定义风格继续保留方案能力，但不再单独拆一个页面；当前布局直接在本页保存和管理。'
  }
  return useInlineLayoutForBackend.value
    ? '当前保存的是该预设对应的可编辑布局，后端预览和生成都会按当前画布执行；恢复默认会回到该预设的初始布局。'
    : '当前保存的是该预设对应的可编辑布局；后端仍按原始风格生成，切到“当前布局”后才会使用这些参数。'
})

const currentStyleLabel = computed(() => {
  if (coverStyleBase.value === 'custom_static') {
    return getTemplateById(selectedCustomTemplateId.value)?.name || '自定义方案'
  }
  const presetId = `__preset_${coverStyleBase.value}`
  return isPresetStaticStyle(coverStyleBase.value)
    ? getPresetSchemeTitle(coverStyleBase.value, getTemplateById(presetId))
    : getStyleTitle(coverStyleBase.value)
})

const currentVariantLabel = computed(() => (styleVariant.value === 'static' ? '静态' : '动态'))
const generationProgressLabel = computed(() => {
  if (generationTotal.value > 0) return `正在生成 ${generationCurrent.value || 0}/${generationTotal.value}`
  return generationLabel.value || '正在生成'
})
const generationProgressPercent = computed(() => {
  if (generationTotal.value > 0) {
    const raw = Math.round((Math.max(0, generationCurrent.value || 0) / generationTotal.value) * 100)
    return Math.max(0, Math.min(100, raw))
  }
  return isGenerating.value ? 12 : 0
})
const runButtonProgressStyle = computed(() => ({
  '--yh-run-progress': `${generationProgressPercent.value}%`,
}))
const generateButtonLabel = computed(() =>
  isGenerating.value ? generationProgressLabel.value : '执行',
)
const generateButtonIcon = computed(() =>
  isGenerating.value ? 'mdi-stop-circle-outline' : 'mdi-play-circle-outline',
)
const generateButtonColor = computed(() => (isGenerating.value ? 'error' : 'primary'))
const resetButtonLabel = computed(() =>
  isPresetStaticStyle(coverStyleBase.value) ? '恢复预设默认' : '恢复基础默认',
)

const animatedFormatItems = [
  { title: 'APNG', value: 'apng' },
  { title: 'GIF', value: 'gif' },
]

const dynamicFontItems = computed(() => [
  ...BUILTIN_FONT_ITEMS,
  ...customFontItems.value.map((item) => ({ title: `自定义 ${item.title}`, value: item.value })),
])

const animatedColorReduceItems = [
  { title: '关闭（保真优先）', value: 'off' },
  { title: '中等压缩', value: 'medium' },
  { title: '强压缩（体积最小）', value: 'strong' },
]

const animatedScrollItems = [
  { title: '向下', value: 'down' },
  { title: '向上', value: 'up' },
  { title: '交替（两边下/中间上）', value: 'alternate' },
  { title: '交替反向（两边上/中间下）', value: 'alternate_reverse' },
]

const animatedDepartureItems = [
  { title: '旋转-飞出', value: 'fly' },
  { title: '旋转-渐隐', value: 'fade' },
  { title: '渐变', value: 'crossfade' },
]

const animatedSettingsTitle = computed(() => {
  const index = animatedSettingsBaseStyle.value.split('_')[1] || '1'
  return `动态方案 ${index} 配置`
})

const showAnimatedImageCountSetting = computed(() =>
  ['static_1', 'static_2', 'static_4'].includes(animatedSettingsBaseStyle.value),
)

const showAnimatedDepartureSetting = computed(() => animatedSettingsBaseStyle.value === 'static_1')

const showAnimatedScrollSetting = computed(() => animatedSettingsBaseStyle.value === 'static_3')

const animatedResolutionLabel = computed(() => animationResolution.value || '320x180')

const activeTitles = computed(() => previewSource.value?.titles || { zh: '', en: '' })
const sourceModeLabel = computed(() => {
  const mode = previewSource.value?.source_mode
  if (mode === 'custom') return '自定义图片目录'
  if (mode === 'cache') return '数据目录缓存海报'
  if (mode === 'media_server') return '媒体服务器'
  return '未知'
})
const autoImageCountLabel = computed(() => `${autoImageCount.value || activeImageCount.value || 1} 张`)
const activeServerLabel = computed(() => previewSource.value?.server || '--')
const activeLibraryLabel = computed(() => previewSource.value?.library || '--')
const activeImageCount = computed(() => previewSource.value?.images?.length || 0)
const historySortItems = [
  { title: '最新优先', value: 'newest' },
  { title: '最早优先', value: 'oldest' },
  { title: '名称排序', value: 'name' },
]
const sortedHistory = computed(() => {
  const items = [...history.value]
  if (historySortMode.value === 'oldest') {
    return items.sort((a, b) => (Number(a.mtime_ts || 0) - Number(b.mtime_ts || 0)))
  }
  if (historySortMode.value === 'name') {
    return items.sort((a, b) => (a.name || '').localeCompare(b.name || '', 'zh-Hans-CN'))
  }
  return items.sort((a, b) => (Number(b.mtime_ts || 0) - Number(a.mtime_ts || 0)))
})
const groupedHistory = computed(() => {
  const groups = new Map<string, HistoryGroup>()
  for (const item of sortedHistory.value) {
    const key = historyGroupMode.value === 'library' ? (item.library || '未识别媒体库') : (item.batch_id || item.date || 'legacy')
    const title = historyGroupMode.value === 'library' ? (item.library || '未识别媒体库') : formatTimelineTime(item.created_at || item.mtime || item.date || '')
    if (!groups.has(key)) {
      groups.set(key, { key, title, items: [] })
    }
    groups.get(key)?.items.push(item)
  }
  return Array.from(groups.values())
})
let timeRecordObserver: IntersectionObserver | null = null
let timeRecordClickLockUntil = 0
let timeMachineFrame = 0
function updateTimeMachineDepth() {
  historyStackLimit.value = isMobileViewport() ? 3 : 5
  if (historyGroupMode.value !== 'time-machine' || pageTab.value !== 'history-tab') return
  const center = window.innerHeight / 2
  document.querySelectorAll<HTMLElement>('.mcr-history-group--time-machine').forEach((element) => {
    const rect = element.getBoundingClientRect()
    const distance = Math.min(1, Math.abs(rect.top + rect.height / 2 - center) / Math.max(center, 1))
    element.style.setProperty('--mcr-time-scale', String(1 - distance * 0.06))
    element.style.setProperty('--mcr-time-opacity', String(1 - distance * 0.38))
    element.style.setProperty('--mcr-time-shift', `${Math.round(distance * 10)}px`)
  })
}
function scheduleTimeMachineDepth() {
  if (timeMachineFrame) return
  timeMachineFrame = window.requestAnimationFrame(() => { timeMachineFrame = 0; updateTimeMachineDepth() })
}
function observeTimeRecords() {
  timeRecordObserver?.disconnect()
  if (historyGroupMode.value !== 'time-machine' || pageTab.value !== 'history-tab') return
  const elements = groupedHistory.value.map((group) => document.getElementById(`time-record-${group.key}`)).filter((item): item is HTMLElement => Boolean(item))
  if (!elements.length) return
  activeTimeRecordId.value ||= groupedHistory.value[0]?.key || ''
  timeRecordObserver = new IntersectionObserver((entries) => {
    if (Date.now() < timeRecordClickLockUntil) return
    if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 3) {
      activeTimeRecordId.value = groupedHistory.value.at(-1)?.key || activeTimeRecordId.value
      return
    }
    const center = window.innerHeight / 2
    const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => Math.abs(a.boundingClientRect.top + a.boundingClientRect.height / 2 - center) - Math.abs(b.boundingClientRect.top + b.boundingClientRect.height / 2 - center))
    if (visible[0]?.target.id) activeTimeRecordId.value = visible[0].target.id.replace('time-record-', '')
  }, { rootMargin: '-32% 0px -32% 0px', threshold: [0, 0.1, 0.4] })
  elements.forEach((element) => timeRecordObserver?.observe(element))
}
watch([historyGroupMode, pageTab, groupedHistory], () => void nextTick(observeTimeRecords))
watch([historyGroupMode, pageTab, groupedHistory], () => void nextTick(scheduleTimeMachineDepth))

function scrollToTimeRecord(id: string) {
  timeRecordClickLockUntil = Date.now() + 1200
  activeTimeRecordId.value = id
  document.getElementById(`time-record-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function openHistorySnapshot(group: HistoryGroup) {
  const timestamp = group.items[0]?.created_at || group.items[0]?.mtime || group.items[0]?.date || ''
  selectedHistorySnapshot.value = { ...group, fullTitle: formatDateTime(timestamp) }
  historySnapshotDialog.value = true
}

function timeMachineCoverStyle(groupKey: string, index: number) {
  let seed = 0
  for (const char of groupKey) seed = (seed * 31 + char.charCodeAt(0)) >>> 0
  const offsets = [0, 36, 76, 118, 160]
  const rotations = [-1.4, 1.1, -0.6, 1.8, -1]
  const vertical = [2, -5, 6, -2, 4]
  const variant = (seed + index * 7) % 5
  return {
    '--mcr-stack-x': `${offsets[index] || offsets.at(-1)}px`,
    '--mcr-stack-hover-x': `${Math.round((offsets[index] || offsets.at(-1) || 0) * 1.22)}px`,
    '--mcr-stack-y': `${vertical[variant]}px`,
    '--mcr-stack-r': `${rotations[variant]}deg`,
    '--mcr-stack-z': String(20 - index),
  }
}

async function restoreHistoryBatch(batchId: string, label = '') {
  if (!batchId || restoringBatchId.value) return
  pendingHistoryRestore.value = { batchId, label }
  restoreConfirmDialog.value = true
}
async function executeHistoryRestore() {
  const pending = pendingHistoryRestore.value
  if (!pending || restoringBatchId.value) return
  const { batchId } = pending
  restoringBatchId.value = batchId
  try {
    const resp = await props.api.post<{ code: number; data?: { restored?: number; skipped?: number; failed?: number }; msg?: string }>('plugin/MediaCoverGenerator/restore_history_batch', { batch_id: batchId })
    if (!resp || resp.code !== 0) throw new Error(resp?.msg || '恢复失败')
    restoreConfirmDialog.value = false
    showEditorSaveStatus(`已回到此时：成功 ${resp.data?.restored || 0} 个，跳过 ${resp.data?.skipped || 0} 个，失败 ${resp.data?.failed || 0} 个`)
  } catch (error) {
    showEditorSaveStatus(error instanceof Error ? error.message : '恢复失败')
  } finally {
    restoringBatchId.value = ''
  }
}
const allHistorySelected = computed(() =>
  history.value.length > 0 && selectedHistoryPaths.value.length === history.value.length,
)
const supplementalPreviewHint = computed(() =>
  useInlineLayoutForBackend.value
    ? '当前画布继续保持可编辑，下方结果按当前布局的后端真实链路返回。'
    : '当前画布继续保持可编辑，下方结果按当前所选原始风格的后端真实链路返回。',
)
const supplementalPreviewChipLabel = computed(() =>
  useInlineLayoutForBackend.value ? '按当前布局渲染' : '按原始风格渲染',
)

function getPersistedCustomTemplateId(templates: CustomStaticLayoutTemplate[]) {
  const userTemplates = getUserCustomTemplates(templates)
  if (!userTemplates.length) return ''
  if (selectedCustomTemplateId.value && userTemplates.some((tpl) => tpl.id === selectedCustomTemplateId.value)) {
    return selectedCustomTemplateId.value
  }
  return userTemplates[0]?.id || ''
}

function buildPersistPayload() {
  const templates = customTemplates.value.map((tpl) => {
    if (activeEditorTemplateId.value && tpl.id === activeEditorTemplateId.value && customStaticLayout.value) {
      return {
        ...tpl,
        layout: cloneLayout(customStaticLayout.value),
      }
    }
    return {
      ...tpl,
      layout: cloneLayout(tpl.layout),
    }
  })
  const normalizedTemplates = normalizeTemplateList(templates)
  const persistedCustomTemplateId = getPersistedCustomTemplateId(normalizedTemplates)
  const persistedCustomTemplate = persistedCustomTemplateId
    ? normalizedTemplates.find((tpl) => tpl.id === persistedCustomTemplateId) || null
    : null
  const activeEditorTemplate = activeEditorTemplateId.value
    ? normalizedTemplates.find((tpl) => tpl.id === activeEditorTemplateId.value) || null
    : null

  return {
    active_id: persistedCustomTemplateId,
    layout: activeEditorTemplate?.layout
      ? cloneLayout(activeEditorTemplate.layout)
      : persistedCustomTemplate
        ? cloneLayout(persistedCustomTemplate.layout)
        : null,
    templates: normalizedTemplates,
  }
}

async function persistCustomLayoutState() {
  if (isGenerating.value) return
  layoutPersisting.value = true
  const currentEditorId = activeEditorTemplateId.value
  cancelPendingAutoSave()
  cancelPendingLayoutMeasure()
  lastCustomLayoutPersistAt = Date.now()
  const savedLayoutSnapshot = customStaticLayout.value ? cloneLayout(customStaticLayout.value) : null
  const payload = buildPersistPayload()
  const localTemplates = normalizeTemplateList(payload.templates.map((tpl) => (
    currentEditorId && savedLayoutSnapshot && tpl.id === currentEditorId
      ? { ...tpl, layout: cloneLayout(savedLayoutSnapshot) }
      : tpl
  )))
  const localActiveId = payload.active_id

  customTemplates.value = localTemplates
  if (currentEditorId && savedLayoutSnapshot) {
    customStaticLayout.value = cloneLayout(savedLayoutSnapshot)
    syncLayoutToTemplate(currentEditorId, savedLayoutSnapshot)
  }

  try {
    const resp = await props.api.post<{
      code: number
      data?: {
        custom_static_layout?: CustomStaticLayout | null
        custom_static_layouts?: CustomStaticLayoutTemplate[] | null
        custom_static_active_id?: string | null
      }
      msg?: string
    }>('plugin/MediaCoverGenerator/set_custom_static_layout', payload)

    if (resp && resp.code !== 0) {
      throw new Error(resp.msg || 'save failed')
    }

    const backendTemplates = normalizeTemplateList(resp?.data?.custom_static_layouts || [])
    const backendActiveId = resp?.data?.custom_static_active_id || localActiveId
    const nextTemplates = backendTemplates.length ? backendTemplates : localTemplates

    applyCustomTemplateState(
      nextTemplates,
      backendActiveId,
    )

    const backendEditorTemplate = currentEditorId
      ? nextTemplates.find((tpl) => tpl.id === currentEditorId)
      : null
    if (currentEditorId && backendEditorTemplate?.layout) {
      customStaticLayout.value = cloneLayout(backendEditorTemplate.layout)
      syncLayoutToTemplate(currentEditorId, backendEditorTemplate.layout)
      activeEditorTemplateId.value = currentEditorId
    } else if (currentEditorId && savedLayoutSnapshot) {
      customStaticLayout.value = cloneLayout(savedLayoutSnapshot)
      syncLayoutToTemplate(currentEditorId, savedLayoutSnapshot)
      activeEditorTemplateId.value = currentEditorId
    } else if (coverStyleBase.value === 'custom_static' && selectedCustomTemplateId.value && getTemplateById(selectedCustomTemplateId.value)) {
      setEditorTemplate(selectedCustomTemplateId.value)
    }

  } catch (e) {
    console.error('persist custom layout failed', e)
  } finally {
    layoutPersisting.value = false
  }
}

async function persistCurrentEditorState() {
  if (isGenerating.value) return
  if (!showInlineLayoutEditor.value || !customStaticLayout.value || !activeEditorTemplateId.value) return
  cancelPendingAutoSave()
  await persistCustomLayoutState()
}

async function restoreCurrentLayoutDefaults() {
  if (shouldBlockLockedAction()) return
  const activeId = activeEditorTemplateId.value
  if (!activeId) return

  const activeTemplate = getTemplateById(activeId)
  const baseStyle = normalizeCoverStyleBase(
    activeTemplate?.baseStyle || (isPresetStaticStyle(coverStyleBase.value) ? coverStyleBase.value : 'custom_static'),
  )
  const nextLayout = cloneLayout(getStyleDefaultLayout(baseStyle))

  customStaticLayout.value = nextLayout
  syncLayoutToTemplate(activeId, nextLayout)
  scheduleMeasureCustomLayout(nextLayout)
  backendPreview.value = null
  await persistCustomLayoutState()
}

watch(previewMode, async (nextMode) => {
  if (nextMode !== 'frontend') {
    previewMode.value = 'frontend'
  }
})

watch(presetStaticRenderMode, async (nextMode, prevMode) => {
  if (nextMode === prevMode) return
  if (controlsLocked.value) {
    presetStaticRenderMode.value = prevMode
    return
  }
  backendPreview.value = null
  if (previewMode.value === 'backend' && showPresetRenderStyleSelector.value) {
    await loadBackendPreview()
  }
})

watch(selectedCustomTemplateId, (nextId, prevId) => {
  if (nextId === prevId) return
  if (controlsLocked.value && !syncingBackendState) {
    selectedCustomTemplateId.value = prevId
    return
  }
  if (coverStyleBase.value !== 'custom_static') return
  if (!nextId) {
    activeEditorTemplateId.value = null
    customStaticLayout.value = null
    return
  }
  setEditorTemplate(nextId)
  backendPreview.value = null
})

watch(
  () => schemeListItems.value.length,
  () => {
    void normalizeSchemeListViewport()
  },
  { flush: 'post' },
)

watch(editorAutoSaveEnabled, (enabled) => {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(EDITOR_AUTO_SAVE_STORAGE_KEY, enabled ? 'true' : 'false')
  }
  if (!enabled) {
    cancelPendingAutoSave()
    autoSaveQueued = false
    editorSaveStatus.value = ''
  }
})

async function createTemplateFromCurrent() {
  if (shouldBlockLockedAction()) return
  await persistCurrentEditorState()
  const id = createLayoutId()
  const template: CustomStaticLayoutTemplate = {
    id,
    name: getUniqueTemplateName(`自定义方案 ${getUserCustomTemplates().length + 1}`),
    layout: cloneLayout(customStaticLayout.value || getStyleDefaultLayout(coverStyleBase.value)),
    baseStyle: 'custom_static',
  }
  customTemplates.value = [...customTemplates.value, template]
  setSelectedCustomTemplate(id)
  backendPreview.value = null
  await setCoverStyle('custom_static')
  await persistCustomLayoutState()
}

async function renameSchemeItem(item: SchemeListItem) {
  if (shouldBlockLockedAction()) return
  const active = resolveSchemeTemplate(item, true)
  if (!active) return
  const newName = window.prompt('请输入方案名称', item.title || active.name)
  if (!newName) return
  const trimmedName = newName.trim()
  if (!trimmedName) return
  const uniqueName = getUniqueTemplateName(trimmedName, active.id)
  customTemplates.value = customTemplates.value.map((tpl) =>
    tpl.id === active.id ? { ...tpl, name: uniqueName } : tpl,
  )
  await persistCustomLayoutState()
}

function buildTemplateExportPayload(active: CustomStaticLayoutTemplate) {
  return {
    schema: 'mcr-custom-static-template/v1',
    exported_at: new Date().toISOString(),
    template: {
      ...active,
      layout: cloneLayout(active.layout),
    },
  }
}

function stringifyTemplateExport(active: CustomStaticLayoutTemplate) {
  return JSON.stringify(buildTemplateExportPayload(active), null, 2)
}

function downloadTextFile(filename: string, text: string, type = 'application/json') {
  const blob = new Blob([text], { type })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

async function writeClipboardText(text: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.left = '-9999px'
  textarea.style.top = '0'
  document.body.appendChild(textarea)
  textarea.focus()
  textarea.select()
  const copied = document.execCommand('copy')
  textarea.remove()
  if (!copied) {
    throw new Error('clipboard unavailable')
  }
}

function getTemplateExportFileName(template: CustomStaticLayoutTemplate) {
  const safeName = String(template.name || 'custom-layout')
    .replace(/[\\/:*?"<>|]+/g, '-')
    .replace(/\s+/g, '-')
    .replace(/^-+|-+$/g, '')
  return `${safeName || 'custom-layout'}.json`
}

function exportSchemeItemToFile(item: SchemeListItem) {
  if (shouldBlockLockedAction()) return
  const active = resolveSchemeTemplate(item)
  if (!active) return
  downloadTextFile(getTemplateExportFileName(active), stringifyTemplateExport(active))
}

async function exportSchemeItemToClipboard(item: SchemeListItem) {
  if (shouldBlockLockedAction()) return
  const active = resolveSchemeTemplate(item)
  if (!active) return
  const text = stringifyTemplateExport(active)
  try {
    await writeClipboardText(text)
    showEditorSaveStatus('方案已复制')
  } catch (e) {
    console.error('copy custom template failed', e)
    window.prompt('剪切板不可用，请手动复制方案 JSON', text)
  }
}

function triggerImportTemplate() {
  if (shouldBlockLockedAction()) return
  importTemplateInput.value?.click()
}

async function importTemplateFromRaw(raw: string, fallbackName: string) {
  const parsed = JSON.parse(raw)
  const imported = parsed?.template || parsed
  if (!imported?.layout?.layers || !Array.isArray(imported.layout.layers)) {
    throw new Error('invalid template file')
  }
  await persistCurrentEditorState()
  const id = createLayoutId()
  const importedName = String(imported.name || fallbackName || `导入方案 ${getUserCustomTemplates().length + 1}`)
  const template: CustomStaticLayoutTemplate = {
    id,
    name: getUniqueTemplateName(importedName),
    layout: cloneLayout(imported.layout),
    baseStyle: 'custom_static',
  }
  customTemplates.value = [...customTemplates.value, template]
  setSelectedCustomTemplate(id)
  backendPreview.value = null
  await setCoverStyle('custom_static')
  await persistCustomLayoutState()
}

async function importTemplateFromClipboard() {
  if (shouldBlockLockedAction()) return
  try {
    let raw = ''
    if (navigator.clipboard?.readText) {
      try {
        raw = await navigator.clipboard.readText()
      } catch (clipboardError) {
        console.warn('read clipboard failed, fallback to manual paste', clipboardError)
      }
    }
    if (!raw) {
      raw = window.prompt('粘贴方案 JSON') || ''
    }
    if (!raw.trim()) return
    await importTemplateFromRaw(raw, `剪切板方案 ${getUserCustomTemplates().length + 1}`)
  } catch (e) {
    console.error('import custom template from clipboard failed', e)
  }
}

async function importTemplateFromFile(event: Event) {
  if (shouldBlockLockedAction()) return
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  try {
    const raw = await file.text()
    await importTemplateFromRaw(raw, file.name.replace(/\.json$/i, '') || `导入方案 ${getUserCustomTemplates().length + 1}`)
  } catch (e) {
    console.error('import custom template failed', e)
  }
}

async function deleteSchemeItem(item: SchemeListItem) {
  if (shouldBlockLockedAction()) return
  if (item.kind !== 'custom') return
  const id = item.templateId
  if (!id || isSystemTemplate(getTemplateById(id))) return

  try {
    const resp = await props.api.post<{
      code: number
      data?: {
        custom_static_layout?: CustomStaticLayout | null
        custom_static_layouts?: CustomStaticLayoutTemplate[] | null
        custom_static_active_id?: string | null
      }
      msg?: string
    }>(`plugin/MediaCoverGenerator/delete_custom_static_template?id=${encodeURIComponent(id)}`)

    if (resp && resp.code !== 0) {
      throw new Error(resp.msg || 'delete failed')
    }

    const incomingTemplates = normalizeTemplateList(resp?.data?.custom_static_layouts)
    applyCustomTemplateState(incomingTemplates, resp?.data?.custom_static_active_id || null)
    if (coverStyleBase.value === 'custom_static' && !getUserCustomTemplates(customTemplates.value).length) {
      await setCoverStyle('static_1', 'static')
    } else {
      hydrateEditorForCurrentStyle()
    }
    backendPreview.value = null
    void normalizeSchemeListViewport()
  } catch (e) {
    console.error('delete custom template failed', e)
  }
}

function onLayoutUpdated(layoutValue: CustomStaticLayout) {
  if (shouldBlockLockedAction()) return
  const nextLayout = cloneLayout(layoutValue)
  customStaticLayout.value = nextLayout
  syncLayoutToTemplate(activeEditorTemplateId.value, nextLayout)
  schedulePreviewSourceReloadForLayout(nextLayout)
  scheduleMeasureCustomLayout(nextLayout)
  scheduleAutoSaveCustomLayout()
  backendPreview.value = null
}

function saveCustomLayout() {
  if (shouldBlockLockedAction()) return
  if (!showInlineLayoutEditor.value) return
  if (!activeEditorTemplateId.value) {
    hydrateEditorForCurrentStyle()
  }
  if (!customStaticLayout.value) return
  void persistCustomLayoutState()
}

async function saveCustomLayoutNow() {
  if (shouldBlockLockedAction()) return
  if (!showInlineLayoutEditor.value) return
  if (!activeEditorTemplateId.value) {
    hydrateEditorForCurrentStyle()
  }
  if (!customStaticLayout.value) return
  await persistCustomLayoutState()
  showEditorSaveStatus('已保存')
}

async function loadStatus(): Promise<boolean> {
  if (statusLoadPromise) return statusLoadPromise
  statusLoadPromise = loadStatusInner().finally(() => {
    statusLoadPromise = null
  })
  return statusLoadPromise
}

async function loadStatusInner(): Promise<boolean> {
  statusLoading.value = true
  try {
    const resp = await props.api.get<{ code: number; data?: StatusPayload; msg?: string }>('plugin/MediaCoverGenerator/status')
    if (!componentActive) return false
    if (resp && resp.code === 0 && resp.data) {
      const data = resp.data
      previewCacheContext.value = {
        mode: (data as any).local_mode ? 'local' : 'server',
        servers: (data as any).selected_servers || [],
        libraries: (data as any).include_libraries || [],
        coversInput: (data as any).covers_input || '',
      }
      const wasGenerating = isGenerating.value
      const nextIsGenerating = Boolean(data.is_generating)
      setupWarnings.value = Array.isArray(data.warnings) ? data.warnings : []
      programEnabled.value = Boolean(data.enabled)
      isGenerating.value = nextIsGenerating
      generationCurrent.value = Number(data.generation_current || 0)
      generationTotal.value = Number(data.generation_total || 0)
      generationLabel.value = String(data.generation_label || '')
      statusLoaded.value = true
      coverStyleBase.value = normalizeCoverStyleBase(data.cover_style_base)
      styleVariant.value = data.cover_style_variant === 'animated' ? 'animated' : 'static'
      syncAnimatedSettings(data, coverStyleBase.value)
      syncRenderOptions(data)

      const shouldPreserveEditingLayout =
        isEditingLayout.value
        || (lastCustomLayoutPersistAt > 0 && Date.now() - lastCustomLayoutPersistAt < 5000)

      if (!nextIsGenerating && !shouldPreserveEditingLayout) {
        let incomingTemplates = normalizeTemplateList(data.custom_static_layouts)
        if (!incomingTemplates.length && data.custom_static_layout) {
          incomingTemplates = [
            {
              id: createLayoutId(),
              name: '自定义方案',
              layout: cloneLayout(data.custom_static_layout),
              baseStyle: 'custom_static',
            },
          ]
        }

        syncingBackendState = true
        try {
          applyCustomTemplateState(incomingTemplates, data.custom_static_active_id || null)
          hydrateEditorForCurrentStyle()
        } finally {
          syncingBackendState = false
        }
      }

      if (isGenerating.value) {
        cancelPendingAutoSave()
        cancelPendingLayoutMeasure()
        cancelPendingPreviewSourceReload()
        autoSaveQueued = false
        backendPreview.value = null
        startGenerationStatusPoller()
      } else {
        stopGenerationStatusPoller()
      }

      if (wasGenerating && !isGenerating.value) {
        void refreshAfterGenerationComplete()
      }
      return true
    } else if (resp && resp.code !== 0) {
      console.error('load status failed', resp.msg || resp)
    }
  } catch (e) {
    console.error('loadStatus failed', e)
  } finally {
    statusLoading.value = false
  }
  return false
}

function normalizeHistoryItems(items: HistoryItem[]) {
  return items.map((item) => ({ ...item, src: item.src || item.url || '' }))
}

function mergeHistoryItems(current: HistoryItem[], incoming: HistoryItem[]) {
  const currentByPath = new Map(current.map((item) => [item.path, item]))
  return incoming.map((item) => {
    const previous = currentByPath.get(item.path)
    return previous && previous.src === item.src && previous.mtime === item.mtime && previous.size === item.size ? previous : item
  })
}

function previewRequestBaseKey() {
  return stableCacheSignature({
    ...previewCacheContext.value,
    posterSource: posterSource.value,
    sort: sourceSortBy.value,
    imageCountMode: imageCountMode.value,
  })
}

async function loadHistory() {
  if (!history.value.length) {
    const cached = await getHistoryCache<HistoryItem[]>(HISTORY_CACHE_KEY)
    if (cached?.length) {
      history.value = normalizeHistoryItems(cached)
      showingCachedHistory.value = true
    }
  }
  historyUpdating.value = true
  historyLoading.value = true
  try {
    const resp = await props.api.get<{ code: number; data?: HistoryItem[]; msg?: string }>('plugin/MediaCoverGenerator/history')
    if (resp && resp.code === 0 && Array.isArray(resp.data)) {
      history.value = resp.data.map((item) => ({
        ...item,
        src: item.src || item.url || '',
      }))
      showingCachedHistory.value = false
      await setHistoryCache(HISTORY_CACHE_KEY, history.value)
      selectedHistoryPaths.value = selectedHistoryPaths.value.filter((path) =>
        resp.data?.some((item) => item.path === path),
      )
    } else if (resp && resp.code !== 0) {
      console.error('load history failed', resp.msg || resp)
    }
  } catch (e) {
    console.error('loadHistory failed', e)
  } finally {
    historyLoading.value = false
    historyUpdating.value = false
  }
}

async function loadPreviewSources(requiredItems?: number, forceRefresh = false) {
  if (!componentActive) return
  if (isGenerating.value) {
    previewSourcesLoading.value = false
    return
  }
  const capacity = Math.max(1, Number(requiredItems) || 9)
  const baseKey = previewRequestBaseKey()
  const requestId = ++previewSourceRequestId
  if (!forceRefresh) {
    const cached = await getPreviewCache<PreviewSourcePayload>(baseKey, capacity)
      if (cached?.images?.length) {
        previewSource.value = cached
      return
    }
  }
  previewSourcesLoading.value = !previewSource.value?.images?.length
  try {
    const query = new URLSearchParams({ required_items: String(capacity) })
    if (forceRefresh) query.set('force_refresh', 'true')
    const suffix = `?${query}`
    const resp = await props.api.get<{ code: number; data?: PreviewSourcePayload; msg?: string }>(`plugin/MediaCoverGenerator/preview_sources${suffix}`)
    if (!componentActive || requestId !== previewSourceRequestId) return
    if (resp && resp.code === 0 && resp.data) {
      previewSource.value = {
        ...resp.data,
        custom_static_layout: resp.data.custom_static_layout ? cloneLayout(resp.data.custom_static_layout) : resp.data.custom_static_layout,
      }
      if (requestId !== previewSourceRequestId) return
      await setPreviewCache(baseKey, Math.max(capacity, previewSource.value.images.length), previewSource.value)
      if (forceRefresh) showEditorSaveStatus('海报已刷新')
    } else {
      if (forceRefresh) showEditorSaveStatus('刷新失败，继续使用当前海报')
      if (resp && resp.code !== 0) {
        console.error('load preview sources failed', resp.msg || resp)
      }
    }
  } catch (e) {
    if (forceRefresh) showEditorSaveStatus('刷新失败，继续使用当前海报')
    console.error('loadPreviewSources failed', e)
  } finally {
    if (componentActive) {
      if (requestId === previewSourceRequestId) previewSourcesLoading.value = false
    }
  }
}

async function loadBackendPreview() {
  if (!componentActive) return
  backendPreviewLoading.value = true
  try {
    const payload: Record<string, any> = {
      style: coverStyleBase.value === 'custom_static' ? 'custom_static' : resolveRequestedCoverStyle(),
    }
    if (showInlineLayoutEditor.value && customStaticLayout.value) {
      payload.layout = cloneLayout(customStaticLayout.value)
    }

    const resp = await props.api.post<{ code: number; data?: BackendPreviewPayload; msg?: string }>(
      'plugin/MediaCoverGenerator/preview',
      payload,
    )
    if (!componentActive) return

    if (resp && resp.code === 0 && resp.data?.src) {
      backendPreview.value = resp.data
    } else {
      backendPreview.value = null
      if (resp && resp.code !== 0) {
        console.error('load backend preview failed', resp.msg || resp)
      }
    }
  } catch (e) {
    backendPreview.value = null
    console.error('loadBackendPreview failed', e)
  } finally {
    backendPreviewLoading.value = false
  }
}

async function refreshCurrentPreview() {
  if (shouldBlockLockedAction()) return
  refreshingPreview.value = true
  try {
    await loadPreviewSources(undefined, true)
    if (previewMode.value === 'backend') {
      await loadBackendPreview()
    }
  } finally {
    refreshingPreview.value = false
  }
}

async function setPageTab(tab: PageTab) {
  if (shouldBlockLockedAction()) return
  if (pageTab.value === 'generate-tab' && tab !== 'generate-tab') {
    await persistCurrentEditorState()
  }
  pageTab.value = tab
  try {
    if (tab === 'history-tab') {
      await loadHistory()
      return
    }

    await loadStatus()
    if (isGenerating.value) return
    await loadPreviewSources()
    if (previewMode.value === 'backend') {
      await loadBackendPreview()
    }
  } catch (e) {
    console.error('set_page_tab failed', e)
  }
}

async function setCoverStyle(targetBase: CoverStyleBase, targetVariant: CoverStyleVariant = styleVariant.value) {
  if (shouldBlockLockedAction()) return
  styleUpdating.value = true
  const previousBase = coverStyleBase.value
  const previousVariant = styleVariant.value
  try {
    await persistCurrentEditorState()

    if (targetBase === 'custom_static') {
      ensureCustomTemplateInitialized()
      coverStyleBase.value = 'custom_static'
      styleVariant.value = 'static'
      await props.api.post('plugin/MediaCoverGenerator/set_cover_style?style=custom_static')
    } else {
      coverStyleBase.value = targetBase
      styleVariant.value = targetVariant
      const style = `${targetVariant}_${targetBase.split('_')[1]}`
      await props.api.post(`plugin/MediaCoverGenerator/set_cover_style?style=${style}`)
    }

    showEditorSaveStatus('已自动保存')
    backendPreview.value = null
    hydrateEditorForCurrentStyle()
  } catch (e) {
    coverStyleBase.value = previousBase
    styleVariant.value = previousVariant
    hydrateEditorForCurrentStyle()
    console.error('set_cover_style failed', e)
  } finally {
    styleUpdating.value = false
  }
}

async function toggleStyleVariant() {
  if (shouldBlockLockedAction()) return
  if (coverStyleBase.value === 'custom_static') return
  const previousVariant = styleVariant.value
  const nextVariant: CoverStyleVariant = previousVariant === 'static' ? 'animated' : 'static'
  animatedSettingsPanelOpen.value = false
  styleUpdating.value = true
  try {
    await persistCurrentEditorState()
    styleVariant.value = nextVariant
    await props.api.post('plugin/MediaCoverGenerator/toggle_style_variant')
    showEditorSaveStatus('已自动保存')
    backendPreview.value = null
    hydrateEditorForCurrentStyle()
  } catch (e) {
    styleVariant.value = previousVariant
    hydrateEditorForCurrentStyle()
    console.error('toggle_style_variant failed', e)
  } finally {
    styleUpdating.value = false
  }
}

function onModeSwitchClick() {
  if (shouldBlockLockedAction()) return
  if (coverStyleBase.value === 'custom_static') return
  modeSwitchPulse.value = false
  window.requestAnimationFrame(() => {
    modeSwitchPulse.value = true
    window.setTimeout(() => {
      modeSwitchPulse.value = false
    }, 360)
  })
  void toggleStyleVariant()
}

async function startGeneration() {
  if (!statusLoaded.value || isGenerating.value) return
  generatingNow.value = true
  try {
    const targetStyle = (useInlineLayoutForBackend.value || coverStyleBase.value === 'custom_static')
      ? 'custom_static'
      : resolveRequestedCoverStyle()
    const endpoint = `plugin/MediaCoverGenerator/start_generation?style=${encodeURIComponent(targetStyle)}`

    if (showInlineLayoutEditor.value) {
      await persistCurrentEditorState()
    }
    cancelPendingAutoSave()
    cancelPendingLayoutMeasure()
    cancelPendingPreviewSourceReload()

    const resp = await props.api.post<{ code: number; msg?: string }>(endpoint)
    if (resp && resp.code !== 0) {
      throw new Error(resp.msg || 'start_generation failed')
    }
    isGenerating.value = true
    generationCurrent.value = 0
    generationTotal.value = 0
    generationLabel.value = '准备生成'
    incrementDonationExecutionCount()
    startGenerationStatusPoller()
    await loadStatus()
    emit('action')
  } catch (e) {
    console.error('start_generation failed', e)
  } finally {
    generatingNow.value = false
  }
}

async function stopGeneration() {
  generatingNow.value = true
  try {
    const resp = await props.api.post<{ code: number; msg?: string }>(
      'plugin/MediaCoverGenerator/stop_generation',
    )
    if (resp && resp.code !== 0) {
      throw new Error(resp.msg || 'stop_generation failed')
    }
    await loadStatus()
  } catch (e) {
    console.error('stop_generation failed', e)
  } finally {
    generatingNow.value = false
  }
}

async function handleGenerateAction() {
  if (!statusLoaded.value) {
    await loadStatus()
    return
  }
  if (isGenerating.value) {
    await stopGeneration()
    return
  }
  await startGeneration()
}

async function deleteCover(item: HistoryItem) {
  if (shouldBlockLockedAction()) return
  try {
    const url = `plugin/MediaCoverGenerator/delete_saved_cover?file=${encodeURIComponent(item.path)}`
    await props.api.post(url)
    history.value = history.value.filter((h) => h.path !== item.path)
    void setHistoryCache(HISTORY_CACHE_KEY, history.value)
    selectedHistoryPaths.value = selectedHistoryPaths.value.filter((path) => path !== item.path)
  } catch (e) {
    console.error('delete_saved_cover failed', e)
  }
}

function toggleHistorySelection(item: HistoryItem) {
  if (shouldBlockLockedAction()) return
  if (selectedHistoryPaths.value.includes(item.path)) {
    selectedHistoryPaths.value = selectedHistoryPaths.value.filter((path) => path !== item.path)
    return
  }
  selectedHistoryPaths.value = [...selectedHistoryPaths.value, item.path]
}

function toggleSelectAllHistory() {
  if (shouldBlockLockedAction()) return
  selectedHistoryPaths.value = allHistorySelected.value
    ? []
    : history.value.map((item) => item.path)
}

async function deleteSelectedCovers() {
  if (shouldBlockLockedAction()) return
  const paths = [...selectedHistoryPaths.value]
  if (!paths.length) return
  try {
    const resp = await props.api.post<{ code: number; msg?: string }>(
      'plugin/MediaCoverGenerator/delete_saved_covers',
      { files: paths },
    )
    if (resp && resp.code !== 0) {
      throw new Error(resp.msg || 'delete selected covers failed')
    }
    history.value = history.value.filter((item) => !paths.includes(item.path))
    void setHistoryCache(HISTORY_CACHE_KEY, history.value)
    selectedHistoryPaths.value = []
  } catch (e) {
    console.error('delete selected covers failed', e)
  }
}

function downloadBinaryPayload(
  payload: { name?: string; mime?: string; b64?: string } | undefined,
  fallbackName: string,
) {
  if (!payload?.b64) {
    throw new Error('download payload missing')
  }
  const binary = window.atob(payload.b64)
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index)
  }
  const blob = new Blob([bytes], { type: payload.mime || 'application/octet-stream' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  const scrollX = window.scrollX
  const scrollY = window.scrollY
  anchor.href = url
  anchor.download = payload.name || fallbackName
  anchor.rel = 'noopener'
  anchor.tabIndex = -1
  anchor.style.position = 'fixed'
  anchor.style.left = '-9999px'
  anchor.style.top = '0'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
  window.requestAnimationFrame(() => {
    window.scrollTo(scrollX, scrollY)
  })
}

function confirmRecentDownload(paths: string[]) {
  const key = [...paths].sort().join('|')
  const now = Date.now()
  const last = recentDownloadRegistry.get(key) || 0
  if (last && now - last < 3 * 60 * 1000) {
    const confirmed = window.confirm('相同内容短时间内已经下载过，是否再次下载？')
    if (!confirmed) return false
  }
  recentDownloadRegistry.set(key, now)
  return true
}

async function fetchCoverPayload(path: string) {
  const resp = await props.api.get<{
    code: number
    data?: { name: string; mime: string; b64: string }
    msg?: string
  }>(`plugin/MediaCoverGenerator/download_saved_cover?file=${encodeURIComponent(path)}`)
  if (!resp || resp.code !== 0 || !resp.data?.b64) {
    throw new Error(resp?.msg || 'download failed')
  }
  return resp.data
}

async function downloadCover(item: HistoryItem) {
  if (shouldBlockLockedAction()) return
  if (!confirmRecentDownload([item.path])) return
  try {
    downloadBinaryPayload(await fetchCoverPayload(item.path), item.name || 'cover')
  } catch (e) {
    console.error('download cover failed', e)
  }
}

async function downloadSelectedCoversZip() {
  if (shouldBlockLockedAction()) return
  const paths = [...selectedHistoryPaths.value]
  if (!paths.length) return
  if (!confirmRecentDownload(paths)) return
  try {
    const resp = await props.api.post<{
      code: number
      data?: { name: string; mime: string; b64: string }
      msg?: string
    }>('plugin/MediaCoverGenerator/download_saved_covers', { files: paths })
    if (!resp || resp.code !== 0 || !resp.data?.b64) {
      throw new Error(resp?.msg || 'batch download failed')
    }
    downloadBinaryPayload(resp.data, 'covers.zip')
  } catch (e) {
    console.error('download selected covers zip failed', e)
  }
}

async function downloadSelectedCoversDirect() {
  if (shouldBlockLockedAction()) return
  const paths = [...selectedHistoryPaths.value]
  if (!paths.length) return
  if (!confirmRecentDownload(paths)) return
  const items = paths.map((path) => history.value.find((item) => item.path === path)).filter(Boolean) as HistoryItem[]
  try {
    for (const item of items) {
      downloadBinaryPayload(await fetchCoverPayload(item.path), item.name || 'cover')
      await new Promise((resolve) => window.setTimeout(resolve, 120))
    }
  } catch (e) {
    console.error('download selected covers direct failed', e)
  }
}

function notifySwitch() {
  if (shouldBlockLockedAction()) return
  emit('switch')
}

function openDonationDialog() {
  donationView.value = donationAcknowledged.value ? 'overview' : 'support'
  donationDialog.value = true
  if (!history.value.length && !historyLoading.value) {
    void loadHistory()
  }
}

function selectMoviePilotAvatar() {
  setDonationAvatarSource(donationAvatarSource.value === 'mp' ? 'developer' : 'mp')
}

function setDonationAvatarSource(source: 'developer' | 'mp') {
  donationAvatarSource.value = source
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(DONATION_AVATAR_STORAGE_KEY, source)
  }
  if (source === 'mp' && !moviePilotAvatarUrl.value) {
    void discoverMoviePilotAvatar()
  }
}

function acknowledgeDonation() {
  donationAcknowledged.value = true
  donationView.value = 'overview'
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(DONATION_ACK_STORAGE_KEY, '1')
  }
}

function incrementDonationExecutionCount() {
  donationExecutionCount.value += 1
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(DONATION_RUN_COUNT_STORAGE_KEY, String(donationExecutionCount.value))
  }
}

function normalizeMoviePilotAvatarUrl(value: unknown): string {
  const raw = typeof value === 'string' ? value.trim() : ''
  if (!raw) return ''
  if (raw.startsWith('data:image/')) return raw
  if (/^https?:\/\//i.test(raw)) return raw
  if (raw.startsWith('//')) return `${window.location.protocol}${raw}`
  if (raw.startsWith('/')) return raw
  if (/^(api|static|assets|avatar|user|profile)\//i.test(raw)) return `/${raw}`
  return ''
}

function findAvatarInPayload(payload: unknown, depth = 0): string {
  if (!payload || depth > 5) return ''
  if (typeof payload === 'string') {
    const normalized = normalizeMoviePilotAvatarUrl(payload)
    if (!normalized) return ''
    const lower = normalized.toLowerCase()
    if (lower.includes('wx_code') || lower.includes('qrcode') || lower.includes('qr-code')) return ''
    if (
      normalized.startsWith('data:image/')
      || /\.(png|jpe?g|webp|gif|svg)(\?|#|$)/i.test(normalized)
      || /(avatar|headimg|profile|portrait|face)/i.test(normalized)
    ) {
      return normalized
    }
    return ''
  }
  if (Array.isArray(payload)) {
    for (const item of payload) {
      const found = findAvatarInPayload(item, depth + 1)
      if (found) return found
    }
    return ''
  }
  if (typeof payload === 'object') {
    const record = payload as Record<string, unknown>
    const preferredKeys = [
      'avatar',
      'avatarUrl',
      'avatar_url',
      'headimgurl',
      'headImgUrl',
      'photo',
      'picture',
      'portrait',
      'face',
      'icon',
      'image',
    ]
    for (const key of preferredKeys) {
      const found = findAvatarInPayload(record[key], depth + 1)
      if (found) return found
    }
    for (const [key, value] of Object.entries(record)) {
      if (!/(user|profile|account|avatar|photo|picture|portrait|face|icon|image)/i.test(key)) continue
      const found = findAvatarInPayload(value, depth + 1)
      if (found) return found
    }
  }
  return ''
}

function discoverMoviePilotAvatarFromDom(): string {
  if (typeof document === 'undefined') return ''
  const selectors = [
    '.v-avatar img',
    '[class*="avatar" i] img',
    '[class*="user" i] img',
    '[class*="profile" i] img',
    'img[alt*="头像" i]',
    'img[title*="头像" i]',
  ]
  const imagesInDom = Array.from(document.querySelectorAll<HTMLImageElement>(selectors.join(',')))
  for (const image of imagesInDom) {
    if (image.closest('.mcr-page-shell')) continue
    const src = normalizeMoviePilotAvatarUrl(image.currentSrc || image.src)
    if (src && findAvatarInPayload(src)) return src
  }
  return ''
}

function discoverMoviePilotAvatarFromStorage(): string {
  if (typeof window === 'undefined') return ''
  const stores = [window.localStorage, window.sessionStorage].filter(Boolean)
  for (const store of stores) {
    for (let index = 0; index < store.length; index += 1) {
      const key = store.key(index) || ''
      if (!/(user|profile|account|auth|login|avatar)/i.test(key)) continue
      const value = store.getItem(key)
      if (!value) continue
      const direct = findAvatarInPayload(value)
      if (direct) return direct
      try {
        const parsed = JSON.parse(value)
        const found = findAvatarInPayload(parsed)
        if (found) return found
      } catch {
        // Ignore non-JSON storage values.
      }
    }
  }
  const globalCandidates = [
    (window as any).__INITIAL_STATE__,
    (window as any).__APP_INITIAL_STATE__,
    (window as any).__PINIA__,
    (window as any).$pinia?.state?.value,
  ]
  for (const candidate of globalCandidates) {
    const found = findAvatarInPayload(candidate)
    if (found) return found
  }
  return ''
}

async function discoverMoviePilotAvatarFromApi(): Promise<string> {
  if (typeof window === 'undefined' || typeof fetch !== 'function') return ''
  const endpoints = [
    '/api/v1/user/current',
    '/api/v1/user/info',
    '/api/v1/user',
    '/api/v1/auth/user',
    '/api/v1/users/current',
  ]
  for (const endpoint of endpoints) {
    try {
      const response = await fetch(endpoint, {
        credentials: 'include',
        headers: { accept: 'application/json' },
      })
      if (!response.ok) continue
      const payload = await response.json()
      const found = findAvatarInPayload(payload)
      if (found) return found
    } catch {
      // Optional host API probing only; missing endpoints are expected on some MP builds.
    }
  }
  return ''
}

async function discoverMoviePilotAvatar() {
  const fromDom = discoverMoviePilotAvatarFromDom()
  if (fromDom) {
    moviePilotAvatarUrl.value = fromDom
    return
  }
  const fromStorage = discoverMoviePilotAvatarFromStorage()
  if (fromStorage) {
    moviePilotAvatarUrl.value = fromStorage
    return
  }
  const fromApi = await discoverMoviePilotAvatarFromApi()
  if (fromApi) {
    moviePilotAvatarUrl.value = fromApi
  }
}

function syncBackendStatusWhenVisible() {
  if (!componentActive) return
  if (typeof document !== 'undefined' && document.visibilityState !== 'visible') return
  void loadStatus()
}

function updateHistoryFloatingActionsPosition() {
  if (typeof window === 'undefined') return
  const stickyTop = Math.max(72, Math.min(112, window.innerHeight * 0.08))
  const headerRect = historyHeaderEl.value?.getBoundingClientRect()
  const preferredTop = headerRect ? headerRect.bottom + 12 : stickyTop
  const top = Math.max(stickyTop, preferredTop)
  historyFloatingStyle.value = {
    left: '50%',
    top: `${Math.round(top)}px`,
    transform: 'translateX(-50%)',
  }
}

watch(
  () => [selectedHistoryPaths.value.length, pageTab.value, history.length],
  () => {
    if (typeof window === 'undefined') return
    window.requestAnimationFrame(updateHistoryFloatingActionsPosition)
  },
)

watch(pageTab, (nextTab) => {
  if (nextTab !== 'history-tab') {
    selectedHistoryPaths.value = []
  }
})

watch(isEditingLayout, () => {
  if (typeof window === 'undefined') return
  window.requestAnimationFrame(updatePreviewBayHeight)
})

async function loadFontLibrary() {
  try {
    const resp = await props.api.get<{ code: number; data?: { custom?: FontLibraryItem[] }; msg?: string }>('plugin/MediaCoverGenerator/fonts')
    if (!resp || resp.code !== 0) {
      throw new Error(resp?.msg || 'load fonts failed')
    }
    customFontItems.value = Array.isArray(resp.data?.custom) ? resp.data.custom : []
  } catch (error) {
    console.warn('load page font library failed', error)
  }
}

onMounted(async () => {
  componentActive = true
  if (typeof window !== 'undefined') {
    donationAcknowledged.value =
      window.localStorage.getItem(DONATION_ACK_STORAGE_KEY) === '1'
      || window.localStorage.getItem(DONATION_LEGACY_ACK_STORAGE_KEY) === '1'
    donationAvatarSource.value = window.localStorage.getItem(DONATION_AVATAR_STORAGE_KEY) === 'mp' ? 'mp' : 'developer'
    donationExecutionCount.value = Math.max(0, Number(window.localStorage.getItem(DONATION_RUN_COUNT_STORAGE_KEY) || 0) || 0)
    void discoverMoviePilotAvatar()
    syncSystemTheme()
    pageThemeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    pageThemeMediaQuery.addEventListener?.('change', syncSystemTheme)
	    window.addEventListener('focus', syncBackendStatusWhenVisible)
	    window.addEventListener('scroll', updateHistoryFloatingActionsPosition, true)
	    window.addEventListener('resize', updateHistoryFloatingActionsPosition)
	    window.addEventListener('resize', updatePreviewBayHeight)
	    window.addEventListener('scroll', scheduleTimeMachineDepth, true)
	    window.addEventListener('resize', scheduleTimeMachineDepth)
	  }
	  if (typeof ResizeObserver !== 'undefined') {
	    previewBayResizeObserver = new ResizeObserver(updatePreviewBayHeight)
	    if (previewBayEl.value) {
	      previewBayResizeObserver.observe(previewBayEl.value)
	    }
	  }
	  if (typeof document !== 'undefined') {
    pageThemeObserver = new MutationObserver(() => {
      hostThemeVersion.value += 1
    })
    pageThemeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class', 'data-theme'],
    })
    if (document.body) {
      pageThemeObserver.observe(document.body, {
        attributes: true,
        attributeFilter: ['class', 'data-theme'],
      })
    }
    document.addEventListener('visibilitychange', syncBackendStatusWhenVisible)
  }
		  void loadFontLibrary()
		  await loadStatus()
	  if (isGenerating.value) return
	  await loadPreviewSources()
	  window.requestAnimationFrame(updatePreviewBayHeight)
	})

onBeforeUnmount(() => {
  timeRecordObserver?.disconnect()
  componentActive = false
  if (typeof window !== 'undefined') {
    pageThemeMediaQuery?.removeEventListener?.('change', syncSystemTheme)
	    window.removeEventListener('focus', syncBackendStatusWhenVisible)
	    window.removeEventListener('scroll', updateHistoryFloatingActionsPosition, true)
	    window.removeEventListener('resize', updateHistoryFloatingActionsPosition)
	    window.removeEventListener('resize', updatePreviewBayHeight)
	    window.removeEventListener('scroll', scheduleTimeMachineDepth, true)
	    window.removeEventListener('resize', scheduleTimeMachineDepth)
	    if (timeMachineFrame) window.cancelAnimationFrame(timeMachineFrame)
	  }
  if (typeof document !== 'undefined') {
    document.removeEventListener('visibilitychange', syncBackendStatusWhenVisible)
  }
	  pageThemeObserver?.disconnect()
	  pageThemeObserver = null
	  previewBayResizeObserver?.disconnect()
	  previewBayResizeObserver = null
  pageThemeMediaQuery = null
  stopGenerationStatusPoller()
  cancelPendingPreviewSourceReload()
  if (autoSaveLayoutTimer !== null) {
    window.clearTimeout(autoSaveLayoutTimer)
    autoSaveLayoutTimer = null
    if (!controlsLocked.value) {
      void persistCustomLayoutState()
    }
  }
  if (measureLayoutTimer !== null) {
    window.clearTimeout(measureLayoutTimer)
    measureLayoutTimer = null
  }
})
</script>

<style scoped>
.mcr-page-shell {
  min-height: 100%;
  --mcr-blueprint-bg: var(--mcr-color-surface);
  --mcr-blueprint-bg-deep: var(--mcr-color-surface-container-lowest);
  --mcr-blueprint-bg-ink: var(--mcr-color-surface-container);
  --mcr-blueprint-panel: rgba(var(--mcr-rgb-surface), 0.82);
  --mcr-blueprint-panel-strong: rgba(var(--mcr-rgb-surface-container), 0.94);
  --mcr-blueprint-line: rgba(var(--mcr-rgb-surface-container-lowest), 0.72);
  --mcr-blueprint-line-soft: rgba(var(--mcr-rgb-primary-container), 0.34);
  --mcr-blueprint-cyan: var(--mcr-color-primary-container);
  --mcr-blueprint-danger: var(--mcr-color-error);
  --mcr-cream: var(--mcr-color-surface);
  --mcr-charcoal: rgba(var(--mcr-rgb-surface-container-lowest), 0.92);
  --mcr-off-white: var(--mcr-color-surface-container-lowest);
  --mcr-muted: rgba(var(--mcr-rgb-primary-fixed-dim), 0.72);
  --mcr-border: rgba(var(--mcr-rgb-primary-container), 0.38);
  --mcr-border-interactive: rgba(var(--mcr-rgb-primary-container), 0.68);
  --mcr-charcoal-04: rgba(var(--mcr-rgb-primary-container), 0.10);
  --mcr-charcoal-82: rgba(var(--mcr-rgb-surface-container-lowest), 0.84);
  background:
    radial-gradient(circle at 18% 10%, rgba(var(--mcr-rgb-primary-container), 0.14), transparent 28%),
    radial-gradient(circle at 86% 18%, rgba(var(--mcr-rgb-primary-container), 0.13), transparent 32%),
    linear-gradient(rgba(var(--mcr-rgb-surface-container-lowest), 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--mcr-rgb-surface-container-lowest), 0.04) 1px, transparent 1px),
    linear-gradient(rgba(var(--mcr-rgb-primary-container), 0.11) 2px, transparent 2px),
    linear-gradient(90deg, rgba(var(--mcr-rgb-primary-container), 0.11) 2px, transparent 2px),
    linear-gradient(135deg, var(--mcr-blueprint-bg-deep) 0%, var(--mcr-blueprint-bg) 48%, var(--mcr-color-surface-bright) 100%);
  background-size: 100% 100%, 100% 100%, 20px 20px, 20px 20px, 100px 100px, 100px 100px, cover;
  color: var(--mcr-charcoal);
  font-family: 'IBM Plex Mono', 'SFMono-Regular', Consolas, 'Courier New', monospace;
}

.mcr-page-shell :deep(.v-slide-group .v-slide-group__container) {
  align-content: center;
  align-items: center;
}

.mcr-frame__body,
.mcr-footer-actions {
  background-color: var(--mcr-blueprint-bg) !important;
}

.mcr-page-shell :global(.mcr-frame__body),
.mcr-page-shell :global(.mcr-footer-actions),
.mcr-page-shell :global(.mcr-frame),
.mcr-page-shell :global(.v-card),
.mcr-page-shell :global(.v-card-text),
.mcr-page-shell :global(.v-card-actions) {
  background-color: var(--mcr-blueprint-bg) !important;
}

.mcr-page-shell :global(.v-tabs) {
  align-items: center !important;
}

.mcr-page-shell :global(.v-slide-group),
.mcr-page-shell :global(.v-slide-group__container),
.mcr-page-shell :global(.v-slide-group__content) {
  align-items: center !important;
}

:global(.v-overlay__content .mcr-page-shell .v-card:not(.bg-primary)),
:global(.v-overlay__content .mcr-page-shell .mcr-frame.v-card:not(.bg-primary)),
:global(.v-overlay__content .mcr-page-shell .mcr-frame__body),
:global(.v-overlay__content .mcr-page-shell .mcr-footer-actions),
:global(.v-overlay__content .mcr-page-shell .generate-layout),
:global(.v-overlay__content .mcr-page-shell .blueprint-workbench),
:global(.v-overlay__content .mcr-page-shell .blueprint-preview-bay),
:global(.v-overlay__content .mcr-page-shell .blueprint-panel-heading),
:global(.v-overlay__content .mcr-page-shell .v-window),
:global(.v-overlay__content .mcr-page-shell .v-window-item) {
  backdrop-filter: none !important;
  background-color: var(--mcr-blueprint-bg) !important;
}

.mcr-page-shell :deep(.v-card),
.mcr-page-shell :deep(.v-window),
.mcr-page-shell :deep(.v-window-item),
.mcr-page-shell :deep(.v-card-text),
.mcr-page-shell :deep(.v-card-actions) {
  background-color: var(--mcr-blueprint-bg) !important;
}

.mcr-page-shell :deep(.v-overlay__content > .v-card) {
  background-color: var(--mcr-blueprint-bg) !important;
}

.mcr-page-shell :deep(.v-slider) {
  color: var(--mcr-blueprint-cyan) !important;
  --v-theme-primary: var(--mcr-v-theme-slider-primary);
  --v-theme-surface-variant: var(--mcr-v-theme-slider-surface-variant);
}

.mcr-page-shell :deep(.v-slider__label),
.mcr-page-shell :deep(.v-slider-track__tick-label) {
  color: rgba(var(--mcr-rgb-primary-fixed), 0.92) !important;
  opacity: 1 !important;
}

.mcr-page-shell :deep(.v-slider-track__background),
.mcr-page-shell :deep(.v-slider-track__tick),
.mcr-page-shell :deep(.v-slider-track__track) {
  background-color: rgba(var(--mcr-rgb-primary-fixed), 0.30) !important;
  border-color: rgba(var(--mcr-rgb-primary-fixed), 0.30) !important;
  opacity: 1 !important;
}

.mcr-page-shell :deep(.v-slider-track__fill) {
  background:
    linear-gradient(90deg, rgba(var(--mcr-rgb-primary-container), 0.95), rgba(var(--mcr-rgb-primary-fixed-dim), 0.98)) !important;
  border-color: rgba(var(--mcr-rgb-primary-container), 0.98) !important;
  opacity: 1 !important;
  box-shadow:
    0 0 10px rgba(var(--mcr-rgb-primary-container), 0.42),
    0 0 20px rgba(var(--mcr-rgb-primary-container), 0.16) !important;
}

.mcr-page-shell :deep(.v-slider-thumb__surface) {
  background-color: var(--mcr-color-primary-fixed) !important;
  border: 2px solid var(--mcr-color-primary-container) !important;
  color: var(--mcr-color-surface-container-lowest) !important;
  box-shadow:
    0 0 0 4px rgba(var(--mcr-rgb-primary-container), 0.16),
    0 0 16px rgba(var(--mcr-rgb-primary-container), 0.56) !important;
}

.mcr-page-shell :deep(.v-slider-thumb__label) {
  background-color: var(--mcr-color-primary-fixed) !important;
  color: var(--mcr-color-surface-container-lowest) !important;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.72);
}

.mcr-page-shell .mcr-shell__aurora {
  opacity: 0;
}

.mcr-page-shell .mcr-shell__noise {
  opacity: 0.5;
  background-image:
    linear-gradient(rgba(var(--mcr-rgb-surface-container-lowest), 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--mcr-rgb-surface-container-lowest), 0.05) 1px, transparent 1px);
  background-size: 20px 20px;
  mask-image: none;
}

.mcr-page-hero {
  margin-bottom: 14px;
  min-height: 132px;
  border-radius: 0;
  background:
    linear-gradient(90deg, rgba(var(--mcr-rgb-primary-container), 0.14), transparent 58%),
    linear-gradient(135deg, rgba(var(--mcr-rgb-surface-container-lowest), 0.86), rgba(var(--mcr-rgb-surface-container), 0.66)) !important;
  border-color: var(--mcr-blueprint-line-soft) !important;
}

.mcr-page-hero::before {
  content: '';
  position: absolute;
  inset: 12px;
  pointer-events: none;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-lowest), 0.14);
}

.mcr-page-hero::after {
  content: 'X: 000 Y: 000';
  position: absolute;
  right: 18px;
  bottom: 14px;
  color: rgba(var(--mcr-rgb-primary-fixed-dim), 0.48);
  font-size: 10px;
  letter-spacing: 0;
}

.mcr-page-shell :deep(.mcr-button--primary),
.mcr-page-shell :deep(.mcr-button--active),
.mcr-page-shell :deep(.mcr-tab--active) {
  background: var(--mcr-blueprint-cyan) !important;
  color: var(--mcr-blueprint-bg) !important;
  border-color: var(--mcr-blueprint-cyan) !important;
  box-shadow: 0 0 20px rgba(var(--mcr-rgb-primary-container), 0.22) !important;
}

.mcr-page-shell :deep(.mcr-button--danger) {
  background: var(--mcr-blueprint-danger) !important;
  color: var(--mcr-blueprint-bg) !important;
  border-color: var(--mcr-blueprint-danger) !important;
}

.mcr-title--compact {
  max-width: 720px;
  font-size: clamp(1.85rem, 3.4vw, 3.15rem);
  line-height: 0.98;
  letter-spacing: 0;
  text-transform: uppercase;
  color: var(--mcr-color-surface-container-lowest);
}

.mcr-page-subtitle {
  max-width: 680px;
  color: rgba(var(--mcr-rgb-primary-fixed-dim), 0.74);
  font-size: 0.92rem;
  line-height: 1.7;
}

.mcr-page-warning {
  margin-bottom: 14px;
}

.mcr-page-tabs {
  align-items: center !important;
  margin-bottom: 4px;
}

.mcr-page-tabs--hero {
  width: min(360px, 34vw);
  min-width: 286px;
  margin-bottom: 0;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.38);
  background:
    linear-gradient(135deg, rgba(var(--mcr-rgb-primary-container), 0.10), transparent 58%),
    rgba(var(--mcr-rgb-surface-container-lowest), 0.68);
  box-shadow: inset 0 0 0 1px rgba(var(--mcr-rgb-surface-container-lowest), 0.05);
}

.mcr-page-tabs :deep(.v-slide-group__container),
.mcr-page-tabs :deep(.v-slide-group__content) {
  align-items: center !important;
}

.mcr-page-tabs :deep(.v-tab) {
  align-self: center;
}

.mcr-page-tabs--hero :deep(.v-tab) {
  min-height: 44px !important;
  height: 44px !important;
  font-size: 12px;
}

.generate-layout {
  padding-top: 10px;
}

.blueprint-workbench {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(360px, 0.65fr);
  gap: 20px;
  align-items: stretch;
}

.blueprint-workbench--editing {
  grid-template-columns: 1fr;
}

.blueprint-workbench--locked .blueprint-preview-bay,
.blueprint-workbench--locked .blueprint-control-bay {
  opacity: 0.72;
}

.blueprint-preview-bay,
.blueprint-control-bay {
  position: relative;
  min-height: 100%;
  border: 1px solid var(--mcr-blueprint-line-soft);
  background: var(--mcr-blueprint-panel);
  box-shadow:
    inset 0 0 0 1px rgba(var(--mcr-rgb-surface-container-lowest), 0.05),
    0 26px 70px rgba(var(--mcr-rgb-shadow), 0.2),
    0 0 34px rgba(var(--mcr-rgb-primary-container), 0.06);
}

.blueprint-preview-bay::before,
.blueprint-control-bay::before {
  content: '';
  position: absolute;
  inset: 10px;
  pointer-events: none;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-lowest), 0.16);
}

.blueprint-preview-bay--locked > :not(.blueprint-panel-heading) {
  pointer-events: none;
}

.blueprint-preview-bay {
  padding: 20px;
}

.blueprint-workbench--editing .blueprint-preview-bay {
  padding: 18px;
}

.blueprint-control-bay {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  padding: 18px;
  overflow: hidden;
  transition: height 340ms cubic-bezier(0.16, 1, 0.3, 1);
}

.blueprint-control-bay--collapsed {
  grid-template-rows: auto;
  min-height: 0;
}

@media (min-width: 960px) {
  .blueprint-workbench {
    align-items: start;
  }

  .blueprint-control-bay {
    align-self: start;
    height: var(--mcr-scheme-panel-height, clamp(520px, calc(100vh - 280px), 680px));
    min-height: 0;
  }

  .blueprint-control-bay--collapsed {
    height: 82px;
  }
}

.blueprint-panel-heading {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.mcr-preview-refresh {
  display: inline-grid;
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  color: var(--color-text-secondary);
  background: var(--color-surface-soft);
  transition: color 160ms ease, background 160ms ease, transform 160ms ease;
}

.mcr-preview-refresh:hover:not(:disabled) {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.mcr-preview-refresh:disabled { opacity: 0.55; }
.mcr-preview-refresh.is-loading .v-icon { animation: mcr-preview-refresh-spin 700ms linear infinite; }
@keyframes mcr-preview-refresh-spin { to { transform: rotate(360deg); } }

.blueprint-hero-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  justify-items: stretch;
  gap: 8px;
  justify-self: end;
  min-width: 286px;
  max-width: 380px;
}

.blueprint-mode-toggle {
  position: relative;
  display: grid;
  grid-template-columns: minmax(44px, auto) 58px minmax(44px, auto);
  align-items: center;
  gap: 7px;
  min-height: 42px;
  width: 100%;
  padding: 5px 9px;
  border: 1px solid var(--mcr-blueprint-line-soft);
  appearance: none;
  background:
    linear-gradient(135deg, rgba(var(--mcr-rgb-primary-container), 0.11), transparent 52%),
    rgba(var(--mcr-rgb-surface-container-lowest), 0.68);
  color: rgba(var(--mcr-rgb-surface-container-lowest), 0.86);
  font-family: inherit;
  font-size: 12px;
  cursor: pointer;
  overflow: hidden;
  transition:
    background-color 260ms cubic-bezier(0.16, 1, 0.3, 1),
    border-color 260ms cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow 260ms cubic-bezier(0.16, 1, 0.3, 1),
    transform 260ms cubic-bezier(0.16, 1, 0.3, 1);
}

.blueprint-panel-heading .blueprint-mode-toggle {
  flex: 0 0 190px;
  width: 190px;
}

.blueprint-mode-toggle::after {
  content: '';
  position: absolute;
  inset: 3px;
  pointer-events: none;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0);
  transform: scaleX(0.72);
  opacity: 0;
  transition:
    opacity 260ms cubic-bezier(0.16, 1, 0.3, 1),
    transform 260ms cubic-bezier(0.16, 1, 0.3, 1),
    border-color 260ms cubic-bezier(0.16, 1, 0.3, 1);
}

.blueprint-mode-toggle:hover,
.blueprint-mode-toggle:focus-visible,
.blueprint-mode-toggle--pulse {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.74);
  box-shadow: 0 0 18px rgba(var(--mcr-rgb-primary-container), 0.18);
}

.blueprint-mode-toggle:active {
  transform: scale(0.985);
}

.blueprint-mode-toggle--pulse::after {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.64);
  opacity: 1;
  transform: scaleX(1);
}

.blueprint-mode-toggle--disabled {
  cursor: not-allowed;
  opacity: 0.72;
  filter: saturate(0.72);
}

.blueprint-mode-option {
  display: inline-flex;
  min-width: 0;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: rgba(var(--mcr-rgb-primary-fixed-dim), 0.64);
  line-height: 1;
  transition:
    color 220ms cubic-bezier(0.16, 1, 0.3, 1),
    transform 220ms cubic-bezier(0.16, 1, 0.3, 1),
    opacity 220ms cubic-bezier(0.16, 1, 0.3, 1);
}

.blueprint-mode-option span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.blueprint-mode-switch-track {
  position: relative;
  display: block;
  width: 58px;
  height: 28px;
  justify-self: center;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.44);
  background:
    linear-gradient(90deg, rgba(var(--mcr-rgb-surface-container-lowest), 0.08), transparent),
    rgba(var(--mcr-rgb-surface-container-lowest), 0.82);
  box-shadow:
    inset 0 0 0 1px rgba(var(--mcr-rgb-surface-container-lowest), 0.06),
    inset 0 -10px 18px rgba(var(--mcr-rgb-shadow), 0.2);
  border-radius: 999px;
}

.blueprint-mode-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-lowest), 0.84);
  border-radius: 50%;
  background: var(--mcr-color-surface-container-lowest);
  box-shadow:
    0 4px 12px rgba(var(--mcr-rgb-shadow), 0.32),
    inset 0 1px 0 rgba(var(--mcr-rgb-surface-container-lowest), 0.86);
  transition:
    transform 360ms cubic-bezier(0.34, 1.56, 0.64, 1),
    background-color 260ms cubic-bezier(0.16, 1, 0.3, 1),
    border-color 260ms cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow 260ms cubic-bezier(0.16, 1, 0.3, 1);
}

.blueprint-mode-thumb::after {
  content: '';
  position: absolute;
  inset: -16px;
  pointer-events: none;
  border-radius: 50%;
  opacity: 0;
  background:
    radial-gradient(circle at 50% 50%,
      rgba(var(--mcr-rgb-primary-container), 0.52) 0%,
      rgba(var(--mcr-rgb-primary-container), 0.36) 18%,
      rgba(var(--mcr-rgb-primary-container), 0.20) 38%,
      rgba(var(--mcr-rgb-primary-container), 0.09) 58%,
      rgba(var(--mcr-rgb-primary-container), 0.00) 78%);
  filter: blur(5px);
  transform: translateZ(0);
}

.blueprint-mode-toggle:not(.blueprint-mode-toggle--animated) .blueprint-mode-option--static,
.blueprint-mode-toggle--animated .blueprint-mode-option--animated {
  color: var(--mcr-color-surface-container-lowest);
  transform: translateY(-1px);
}

.blueprint-mode-toggle--animated .blueprint-mode-switch-track {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.7);
  background:
    linear-gradient(90deg, rgba(var(--mcr-rgb-primary-container), 0.72), rgba(var(--mcr-rgb-primary-container), 0.34)),
    rgba(var(--mcr-rgb-surface-container-lowest), 0.82);
  box-shadow:
    inset 0 0 0 1px rgba(var(--mcr-rgb-surface-container-lowest), 0.14),
    0 0 18px rgba(var(--mcr-rgb-primary-container), 0.24);
}

.blueprint-mode-toggle--animated .blueprint-mode-thumb {
  transform: translateX(30px);
  background: var(--mcr-color-primary-container);
  border-color: rgba(var(--mcr-rgb-primary-fixed), 0.98);
  box-shadow:
    0 5px 14px rgba(var(--mcr-rgb-shadow), 0.34),
    0 0 8px rgba(var(--mcr-rgb-primary-fixed-dim), 0.72),
    0 0 18px rgba(var(--mcr-rgb-primary-container), 0.34),
    inset 0 1px 0 rgba(var(--mcr-rgb-surface-container-lowest), 0.72);
}

.blueprint-mode-toggle--animated .blueprint-mode-thumb::after {
  opacity: 0.88;
  animation: blueprint-mode-halo 3.8s ease-in-out infinite;
}

.blueprint-mode-toggle--disabled .blueprint-mode-switch-track {
  border-color: rgba(var(--mcr-rgb-surface-container-lowest), 0.22);
  background: rgba(var(--mcr-rgb-surface-container-high), 0.78);
}

.blueprint-mode-toggle--disabled .blueprint-mode-thumb {
  background: rgba(var(--mcr-rgb-on-surface), 0.88);
  transform: translateX(0);
}

.blueprint-mode-toggle--disabled .blueprint-mode-option--animated {
  opacity: 0.42;
}

@keyframes blueprint-mode-halo {
  0%,
  100% {
    opacity: 0.72;
    filter: blur(5px);
    background:
      radial-gradient(circle at 50% 50%,
        rgba(var(--mcr-rgb-primary-container), 0.46) 0%,
        rgba(var(--mcr-rgb-primary-container), 0.30) 20%,
        rgba(var(--mcr-rgb-primary-container), 0.17) 40%,
        rgba(var(--mcr-rgb-primary-container), 0.075) 60%,
        rgba(var(--mcr-rgb-primary-container), 0.00) 80%);
  }
  50% {
    opacity: 0.96;
    filter: blur(6.5px);
    background:
      radial-gradient(circle at 50% 50%,
        rgba(var(--mcr-rgb-primary-container), 0.58) 0%,
        rgba(var(--mcr-rgb-primary-container), 0.40) 19%,
        rgba(var(--mcr-rgb-primary-container), 0.23) 42%,
        rgba(var(--mcr-rgb-primary-container), 0.10) 64%,
        rgba(var(--mcr-rgb-primary-container), 0.00) 84%);
  }
}

.blueprint-status-strip {
  display: flex;
  flex-wrap: nowrap;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: var(--mcr-blueprint-cyan);
  font-size: 11px;
  letter-spacing: 0;
  text-transform: uppercase;
}

.blueprint-preview-heading-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 14px;
  min-width: min(620px, 58%);
}

.blueprint-status-strip span {
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.48);
  padding: 5px 8px;
  background: rgba(var(--mcr-rgb-primary-container), 0.08);
  white-space: nowrap;
}

.blueprint-preview-frame {
  position: relative;
  z-index: 1;
  padding: 14px;
  border: 1px solid var(--mcr-blueprint-line);
  background:
    linear-gradient(rgba(var(--mcr-rgb-surface-container-lowest), 0.055) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--mcr-rgb-surface-container-lowest), 0.055) 1px, transparent 1px),
    rgba(var(--mcr-rgb-surface-container-lowest), 0.68);
  background-size: 20px 20px;
  box-shadow:
    inset 0 0 0 1px rgba(var(--mcr-rgb-surface-container-lowest), 0.08),
    0 16px 44px rgba(var(--mcr-rgb-shadow), 0.28);
}

.blueprint-preview-frame::before,
.blueprint-preview-frame::after {
  content: '';
  position: absolute;
  width: 58px;
  height: 58px;
  pointer-events: none;
  border-color: var(--mcr-blueprint-cyan);
  opacity: 0.82;
}

.blueprint-preview-frame::before {
  left: -1px;
  top: -1px;
  border-left: 2px solid;
  border-top: 2px solid;
}

.blueprint-preview-frame::after {
  right: -1px;
  bottom: -1px;
  border-right: 2px solid;
  border-bottom: 2px solid;
}

.blueprint-skeleton {
  position: relative;
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.34);
  background:
    linear-gradient(rgba(var(--mcr-rgb-surface-container-lowest), 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--mcr-rgb-surface-container-lowest), 0.05) 1px, transparent 1px),
    linear-gradient(135deg, rgba(var(--mcr-rgb-surface-container-low), 0.98), rgba(var(--mcr-rgb-surface-container), 0.82));
  background-size: 18px 18px, 18px 18px, cover;
  box-shadow:
    inset 0 0 0 1px rgba(var(--mcr-rgb-surface-container-lowest), 0.06),
    inset 0 0 42px rgba(var(--mcr-rgb-primary-container), 0.07);
}

.blueprint-skeleton::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    105deg,
    transparent 0%,
    rgba(var(--mcr-rgb-primary-container), 0.08) 36%,
    rgba(var(--mcr-rgb-surface-container-lowest), 0.18) 48%,
    rgba(var(--mcr-rgb-primary-container), 0.08) 60%,
    transparent 100%
  );
  transform: translateX(-120%);
}

.blueprint-skeleton--active::before {
  animation: blueprint-skeleton-scan 1.45s cubic-bezier(0.16, 1, 0.3, 1) infinite;
}

.blueprint-skeleton__grid {
  position: absolute;
  inset: 10px;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-lowest), 0.16);
}

.blueprint-skeleton__poster {
  position: absolute;
  left: 12%;
  top: 18%;
  width: 24%;
  height: 58%;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.42);
  background: rgba(var(--mcr-rgb-primary-container), 0.16);
  box-shadow: 0 0 18px rgba(var(--mcr-rgb-primary-container), 0.12);
}

.blueprint-skeleton__poster--main {
  left: 8%;
  top: 15%;
  width: 22%;
  height: 64%;
}

.blueprint-skeleton__line {
  position: absolute;
  left: 42%;
  height: 10px;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.38);
  background: rgba(var(--mcr-rgb-primary-fixed-dim), 0.12);
}

.blueprint-skeleton--preview .blueprint-skeleton__line {
  height: 16px;
}

.blueprint-skeleton__line--wide {
  top: 36%;
  width: 42%;
}

.blueprint-skeleton__line--short {
  top: 52%;
  width: 28%;
}

.blueprint-skeleton--card .blueprint-skeleton__line {
  height: 7px;
}

@keyframes blueprint-skeleton-scan {
  0% {
    transform: translateX(-120%);
  }
  100% {
    transform: translateX(120%);
  }
}

.blueprint-meta-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  border: 1px solid var(--mcr-blueprint-line-soft);
  border-top: 0;
}

.blueprint-meta-grid.mcr-render-options {
  grid-template-columns: 1.1fr 1fr 0.82fr;
  align-items: stretch;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.54);
}

.blueprint-meta-grid--editor {
  margin-top: 10px;
  border-top: 1px solid var(--mcr-blueprint-line-soft);
}

.blueprint-meta-grid > div,
.mcr-render-option {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 10px 12px;
  border-right: 1px solid var(--mcr-blueprint-line-soft);
}

.blueprint-meta-grid > div:last-child,
.mcr-render-option:last-child {
  border-right: 0;
}

.blueprint-meta-grid span,
.blueprint-control-label {
  color: rgba(var(--mcr-rgb-primary-fixed-dim), 0.62);
  font-size: 10px;
  line-height: 1;
  letter-spacing: 0;
  text-transform: uppercase;
}

.mcr-render-option {
  margin: 0;
}

.mcr-render-option select,
.mcr-render-option input {
  width: 100%;
  min-width: 0;
  height: 28px;
  padding: 0 8px;
  color: var(--mcr-color-surface-container-lowest);
  font-size: 12px;
  font-weight: 700;
  line-height: 28px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.78);
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.28);
  border-radius: 9px;
  outline: none;
}

.mcr-render-option__value {
  display: inline-flex;
  align-items: center;
  width: 100%;
  min-width: 0;
  height: 28px;
  padding: 0 8px;
  color: var(--mcr-color-surface-container-lowest);
  font-size: 12px;
  font-weight: 700;
  line-height: 28px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.58);
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.42);
  border-radius: 9px;
}

.mcr-render-option select:focus,
.mcr-render-option input:focus {
  border-color: var(--mcr-color-primary);
  box-shadow: 0 0 0 2px rgba(var(--mcr-rgb-primary), 0.12);
}

.mcr-render-option select:disabled,
.mcr-render-option input:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.blueprint-meta-grid strong {
  overflow: hidden;
  color: var(--mcr-color-surface-container-lowest);
  font-size: 13px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcr-scheme-list {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 10px;
  min-height: 0;
  height: 100%;
}

.mcr-collapsible-heading {
  cursor: pointer;
  user-select: none;
}

.mcr-collapsible-heading:focus-visible {
  outline: 2px solid var(--mcr-color-primary);
  outline-offset: 3px;
}

.mcr-collapsible-heading__title {
  min-width: 0;
}

.mcr-collapsible-heading__title .mcr-panel__title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.mcr-collapsible-heading__icon {
  flex: 0 0 auto;
  color: var(--mcr-color-primary);
  transition: transform 220ms cubic-bezier(0.16, 1, 0.3, 1);
}

.mcr-collapsible-heading--collapsed .mcr-collapsible-heading__icon {
  transform: rotate(180deg);
}

.blueprint-panel-heading.mcr-collapsible-heading--collapsed {
  margin-bottom: 0;
}

.mcr-list-collapse-enter-active,
.mcr-list-collapse-leave-active {
  overflow: hidden;
  transition:
    max-height 340ms cubic-bezier(0.16, 1, 0.3, 1),
    opacity 220ms ease,
    transform 340ms cubic-bezier(0.16, 1, 0.3, 1);
}

.mcr-list-collapse-enter-from,
.mcr-list-collapse-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-8px);
}

.mcr-list-collapse-enter-to,
.mcr-list-collapse-leave-from {
  max-height: 2400px;
  opacity: 1;
  transform: translateY(0);
}

.mcr-mode-switch-enter-active,
.mcr-mode-switch-leave-active,
.mcr-heading-tools-enter-active,
.mcr-heading-tools-leave-active {
  transition:
    opacity 200ms ease,
    transform 280ms cubic-bezier(0.16, 1, 0.3, 1);
}

.mcr-mode-switch-enter-from,
.mcr-heading-tools-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.mcr-mode-switch-leave-to,
.mcr-heading-tools-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.mcr-mode-switch-enter-to,
.mcr-mode-switch-leave-from,
.mcr-heading-tools-enter-to,
.mcr-heading-tools-leave-from {
  opacity: 1;
  transform: translateY(0);
}

@media (prefers-reduced-motion: reduce) {
  .blueprint-control-bay,
  .mcr-collapsible-heading__icon,
  .mcr-list-collapse-enter-active,
  .mcr-list-collapse-leave-active,
  .mcr-mode-switch-enter-active,
  .mcr-mode-switch-leave-active,
  .mcr-heading-tools-enter-active,
  .mcr-heading-tools-leave-active {
    transition-duration: 1ms !important;
  }
}

.mcr-scheme-list__scroll {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-auto-rows: auto;
  align-content: start;
  gap: 12px;
  min-height: 0;
  height: 100%;
  padding: 3px 4px 0 0;
  overflow-y: auto;
  scrollbar-gutter: stable;
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--mcr-rgb-primary-container), 0.46) rgba(var(--mcr-rgb-surface-container-lowest), 0.18);
}

.mcr-scheme-list__scroll::-webkit-scrollbar {
  width: 6px;
}

.mcr-scheme-list__scroll::-webkit-scrollbar-track {
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.18);
}

.mcr-scheme-list__scroll::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-primary-container), 0.46);
}

.mcr-scheme-row {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: stretch;
  height: auto;
  min-width: 0;
  padding: 5px;
  overflow: hidden;
  color: var(--mcr-color-surface-container-lowest);
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.74);
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.38);
  border-radius: 14px;
  transition:
    border-color 260ms cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow 260ms cubic-bezier(0.16, 1, 0.3, 1);
}

.mcr-scheme-row:hover,
.mcr-scheme-row--active {
  border-color: var(--mcr-blueprint-cyan);
  box-shadow: 0 0 18px rgba(var(--mcr-rgb-primary-container), 0.22);
}

.mcr-scheme-row--active {
  background: var(--mcr-color-primary-container);
  color: var(--mcr-color-on-primary-container);
}

.mcr-scheme-row--active .mcr-scheme-row__media {
  border-color: transparent;
  border-width: 0;
}

.mcr-scheme-row__select {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  grid-template-rows: auto minmax(36px, auto);
  align-content: start;
  gap: 5px;
  min-width: 0;
  min-height: 0;
  width: 100%;
  padding: 0;
  color: inherit;
  text-align: left;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.mcr-scheme-row__select--disabled,
.mcr-scheme-row__select[aria-disabled="true"] {
  cursor: not-allowed;
  opacity: 0.56;
}

.mcr-scheme-row__media {
  position: relative;
  z-index: 1;
  display: block;
  width: 100%;
  min-height: 0;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.28);
  border-radius: 9px;
  background: var(--mcr-color-surface-container-lowest);
}

.mcr-scheme-row__media :deep(.simulation-canvas),
.mcr-scheme-row__media :deep(.simulation-empty) {
  height: 100%;
  aspect-ratio: 16 / 9;
  border: 0;
  border-radius: 0;
  background: transparent !important;
  transform: scale(1.01);
  transform-origin: center;
}

.mcr-scheme-row:hover .mcr-scheme-row__media :deep(.simulation-canvas) {
  transform: scale(1.045);
}

.mcr-scheme-row__body {
  position: relative;
  z-index: 2;
  display: grid;
  align-content: center;
  gap: 1px;
  min-width: 0;
  min-height: 36px;
  padding: 2px 4px;
  pointer-events: none;
}

.mcr-scheme-row__body strong,
.mcr-scheme-row__body span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcr-scheme-row__body strong {
  font-size: 12px;
  font-weight: 760;
  letter-spacing: 0;
}

.mcr-scheme-row__body span {
  color: rgba(var(--mcr-rgb-primary-fixed-dim), 0.64);
  font-size: 9px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.mcr-scheme-row__actions {
  position: absolute;
  right: 10px;
  bottom: 10px;
  z-index: 3;
  display: flex;
  align-items: center;
  gap: 0;
  padding: 2px;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.34);
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.78);
  box-shadow: 0 8px 20px rgba(var(--mcr-rgb-shadow), 0.20);
  opacity: 0;
  pointer-events: none;
  transform: translateY(4px);
  transition:
    opacity 160ms ease,
    transform 160ms ease;
  backdrop-filter: blur(12px);
}

.mcr-scheme-row--active .mcr-scheme-row__body strong,
.mcr-scheme-row--active .mcr-scheme-row__body span {
  color: var(--mcr-color-on-primary-container);
}

.mcr-scheme-list--animated .mcr-scheme-row__actions {
  right: 8px;
  bottom: 8px;
}

.mcr-scheme-list--animated .mcr-scheme-row__icon {
  width: 30px !important;
  height: 30px !important;
}

.mcr-scheme-row:hover .mcr-scheme-row__actions,
.mcr-scheme-row:focus-within .mcr-scheme-row__actions,
.mcr-scheme-row--active .mcr-scheme-row__actions {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0);
}

.mcr-scheme-row__icon {
  width: 28px !important;
  height: 28px !important;
  color: var(--mcr-blueprint-cyan) !important;
}

.mcr-scheme-row__icon--danger {
  color: var(--mcr-blueprint-danger) !important;
}

.mcr-scheme-list__tail {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 0;
  padding-top: 10px;
  border-top: 1px dashed rgba(var(--mcr-rgb-primary-container), 0.30);
}

.mcr-scheme-tail-button {
  min-width: 0 !important;
  min-height: 30px !important;
  height: 30px !important;
  padding-inline: 9px !important;
  border-radius: 10px !important;
  font-size: 11px !important;
  line-height: 1 !important;
}

.mcr-editor-save-cluster {
  position: relative;
  display: inline-flex;
  align-items: center;
  min-width: 0;
}

.mcr-editor-split-save {
  display: inline-flex;
  align-items: stretch;
  min-width: 0;
  overflow: hidden;
  border: 1px solid rgba(0, 122, 255, 0.16);
  border-radius: 12px;
  background: #fff;
  box-shadow:
    0 1px 2px rgba(47, 76, 128, 0.06),
    0 8px 20px rgba(47, 76, 128, 0.09),
    inset 0 1px 0 rgba(255, 255, 255, 0.94);
}

.mcr-editor-split-save :deep(.v-btn),
.mcr-editor-split-save :deep(.mcr-button) {
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

.mcr-editor-split-save :deep(.v-btn:hover),
.mcr-editor-split-save :deep(.mcr-button:hover) {
  background: rgba(0, 122, 255, 0.055) !important;
  box-shadow: none !important;
  transform: none;
}

.mcr-editor-split-save :deep(.v-btn:active),
.mcr-editor-split-save :deep(.mcr-button:active) {
  background: rgba(0, 122, 255, 0.09) !important;
  box-shadow: none !important;
}

.mcr-editor-split-save :deep(.mcr-editor-save-main) {
  min-height: 38px !important;
  margin: 0 !important;
  padding-inline: 14px 10px !important;
  color: var(--color-text-main) !important;
  -webkit-text-fill-color: var(--color-text-main) !important;
}

.mcr-editor-split-save :deep(.mcr-editor-save-toggle) {
  width: auto !important;
  min-width: 56px !important;
  min-height: 38px !important;
  margin: 0 !important;
  padding: 0 12px 0 7px !important;
  color: #007aff !important;
  -webkit-text-fill-color: #007aff !important;
}

.mcr-editor-save-mode {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 38px;
  min-height: 20px;
  padding: 0 6px;
  border-radius: 6px;
  background: rgba(0, 122, 255, 0.08);
  color: #007aff;
  font-size: 9px;
  font-weight: 850;
  line-height: 1;
  letter-spacing: 0.06em;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-editor-split-save {
  border-color: rgba(10, 132, 255, 0.22);
  background: #fff;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-editor-save-mode {
  background: rgba(0, 122, 255, 0.10);
  color: #007aff;
}

/* Legacy split-button declarations kept neutral so the control reads as one unit. */
.mcr-editor-split-save {
  background: #fff;
}

.mcr-editor-split-save :deep(.v-btn) {
  border-radius: 0 !important;
}

.mcr-editor-split-save :deep(.mcr-editor-save-main) {
  overflow: hidden;
  margin-inline-end: 0 !important;
}

.mcr-editor-split-save :deep(.mcr-editor-save-toggle) {
  margin-inline-start: 0 !important;
  border-left-color: transparent !important;
}

.mcr-editor-save-hint {
  position: absolute;
  left: 50%;
  bottom: calc(100% + 8px);
  z-index: 24;
  display: inline-flex;
  min-height: 28px;
  align-items: center;
  gap: 5px;
  padding: 0 10px;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.32);
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.94);
  color: var(--mcr-blueprint-cyan);
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  pointer-events: none;
  box-shadow: 0 12px 28px rgba(var(--mcr-rgb-shadow), 0.16);
  backdrop-filter: blur(14px);
  transform: translateX(-50%);
}

.mcr-animated-settings__grid {
  display: grid;
  gap: 14px;
  margin-top: 16px;
}

.mcr-animated-parameter-panel {
  min-height: 0;
  height: 100%;
  padding: 4px 6px 2px 2px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--mcr-rgb-primary), 0.42) transparent;
}

.mcr-animated-parameter-panel__header {
  position: sticky;
  top: 0;
  z-index: 4;
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  padding: 4px 0 12px;
  background: linear-gradient(180deg, var(--mcr-color-surface-container-lowest) 78%, transparent);
}

.mcr-animated-parameter-panel__header div {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.mcr-animated-parameter-panel__header span {
  color: var(--mcr-color-on-surface-variant);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
}

.mcr-animated-parameter-panel__header strong {
  overflow: hidden;
  color: var(--mcr-color-on-surface);
  font-size: 16px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcr-animated-parameter-panel__back {
  display: grid;
  width: 36px;
  height: 36px;
  place-items: center;
  padding: 0;
  border: 1px solid var(--mcr-color-outline-variant);
  border-radius: 10px;
  background: var(--mcr-color-surface-container-low);
  color: var(--mcr-color-on-surface);
  cursor: pointer;
}

.mcr-animated-parameter-panel__back:hover {
  border-color: var(--mcr-color-primary);
  color: var(--mcr-color-primary);
}

.mcr-animated-parameter-panel__actions {
  position: sticky;
  bottom: 0;
  display: flex;
  min-height: 54px;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
  padding: 10px 0 2px;
  background: linear-gradient(0deg, var(--mcr-color-surface-container-lowest) 78%, transparent);
}

.mcr-animated-parameter-panel__saved {
  color: var(--mcr-color-success);
  font-size: 11px;
  font-weight: 700;
}

.mcr-save-hint-enter-active,
.mcr-save-hint-leave-active {
  transition:
    opacity 420ms ease,
    transform 420ms ease;
}

.mcr-save-hint-enter-from,
.mcr-save-hint-leave-to {
  opacity: 0;
  transform: translate(-50%, 6px);
}

@media (hover: none) {
  .mcr-scheme-row__actions {
    opacity: 0;
    pointer-events: none;
    transform: translateY(4px);
  }

  .mcr-scheme-row:focus-within .mcr-scheme-row__actions,
  .mcr-scheme-row--active .mcr-scheme-row__actions {
    opacity: 1;
    pointer-events: auto;
    transform: translateY(0);
  }
}

.blueprint-control-group {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 8px;
  margin-top: 16px;
}

.blueprint-action-stack {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 10px;
  margin-top: 18px;
}

.blueprint-generate-button {
  flex: 0 0 auto;
  min-height: 38px !important;
  padding-inline: 12px !important;
  font-size: 13px !important;
  min-width: 132px !important;
}

.preview-card,
.backend-preview-empty {
  background: var(--mcr-blueprint-panel-strong);
  border: 1px solid var(--mcr-border);
}

.editor-preview-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.backend-preview-shell,
.backend-preview-empty {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 0;
  overflow: hidden;
  background: var(--mcr-blueprint-panel-strong);
  border: 1px solid var(--mcr-border);
}

.backend-preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 0 24px;
  color: var(--mcr-muted, var(--mcr-color-on-surface-variant));
}

.sim-color-picker-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sim-color-picker {
  width: 42px;
  height: 34px;
  padding: 0;
  border: 1px solid var(--mcr-border, var(--mcr-color-outline-variant));
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
}

.sim-color-picker::-webkit-color-swatch-wrapper {
  padding: 0;
}

.sim-color-picker::-webkit-color-swatch {
  border: 1px solid var(--mcr-border, var(--mcr-color-outline-variant));
  border-radius: 4px;
}

.info-list,
.source-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row,
.source-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--mcr-border, var(--mcr-color-outline-variant));
}

.info-row:last-child,
.source-row:last-child {
  border-bottom: 0;
}

.info-label,
.source-slot {
  color: var(--mcr-muted, var(--mcr-color-on-surface-variant));
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  white-space: nowrap;
}

.info-value,
.source-name {
  text-align: right;
  font-size: 14px;
  color: var(--mcr-charcoal-82, rgba(var(--mcr-rgb-on-surface), 0.82));
  word-break: break-word;
}

.page-title-preview__zh {
  font-family: 'McrHeading', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  font-size: 2rem;
  line-height: 1.10;
  letter-spacing: -1.2px;
  font-weight: 600;
  color: var(--mcr-charcoal, var(--mcr-color-on-surface));
}

.page-title-preview__en {
  margin-top: 8px;
  color: var(--mcr-muted, var(--mcr-color-on-surface-variant));
  font-size: 0.875rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.mcr-preview-media {
  width: 100%;
  height: 100%;
}

.mcr-history-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 16px;
  align-items: end;
  margin-bottom: 16px;
}

.mcr-history-toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}

.mcr-history-sort {
  width: 132px;
}

.mcr-history-groups {
  display: grid;
  gap: 20px;
}

.mcr-history-list-content {
  min-height: 0;
}

.mcr-history-group {
  border-top: 1px solid rgba(var(--mcr-rgb-primary-container), 0.3);
  padding-top: 12px;
}

.mcr-history-group__heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  color: rgba(var(--mcr-rgb-on-surface), 0.9);
  font-family: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
  font-size: 12px;
  letter-spacing: 0;
  text-transform: uppercase;
}

.mcr-history-group__heading strong {
  color: var(--mcr-blueprint-cyan);
  font-weight: 600;
}

.mcr-history-card {
  height: 100%;
  overflow: hidden;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.34);
  border-radius: 0;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.78);
  box-shadow: 0 0 16px rgba(var(--mcr-rgb-primary-container), 0.08);
  transition:
    border-color 260ms cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow 260ms cubic-bezier(0.16, 1, 0.3, 1),
    transform 260ms cubic-bezier(0.16, 1, 0.3, 1);
}

.mcr-history-card--selected,
.mcr-history-card:hover {
  border-color: var(--mcr-blueprint-cyan);
  box-shadow: 0 0 18px rgba(var(--mcr-rgb-primary-container), 0.2);
  transform: translateY(-2px);
}

.mcr-history-card:active {
  transform: translateY(0) scale(0.99);
}

.mcr-history-card__media {
  position: relative;
}

.mcr-history-card__image {
  border-radius: 0;
}

.mcr-history-card__check {
  position: absolute;
  top: 4px;
  right: 6px;
  z-index: 2;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.42);
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.72);
  box-shadow: 0 0 12px rgba(var(--mcr-rgb-primary-container), 0.16);
}

.mcr-history-card__title {
  display: -webkit-box;
  min-height: 2.6rem;
  overflow: hidden;
  line-height: 1.3rem;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  color: rgba(var(--mcr-rgb-surface-container-lowest), 0.94);
}

.mcr-history-card__meta {
  margin-top: 8px;
  font-size: 0.875rem;
  color: rgba(var(--mcr-rgb-primary-fixed-dim), 0.68);
}

.mcr-history-card__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 10px;
}

/* Tablet / small desktop: stack preview above controls */
@media (max-width: 959px) {
  .blueprint-workbench {
    grid-template-columns: 1fr;
  }

  .blueprint-hero-actions {
    justify-self: stretch;
    max-width: none;
  }

  .mcr-page-tabs--hero {
    width: 100%;
  }

  .blueprint-control-bay,
  .blueprint-preview-bay {
    min-height: 0;
    padding: 14px;
  }

  .blueprint-control-bay {
    height: auto;
  }

  .mcr-scheme-list {
    grid-template-rows: auto auto;
    height: auto;
  }

  .mcr-scheme-list__scroll {
    height: auto;
    max-height: none;
    overflow: visible;
    padding-right: 0;
    scrollbar-gutter: auto;
  }

  .info-row,
  .source-row {
    flex-direction: column;
    gap: 4px;
  }

  .info-value,
  .source-name {
    text-align: left;
  }

  .page-title-preview__zh {
    font-size: 1.6rem;
  }

  .backend-preview-shell,
  .backend-preview-empty {
    border-radius: 0;
  }
}

/* Mobile: full width preview, compact controls */
@media (max-width: 599px) {
  .mcr-title--compact {
    font-size: 1.8rem;
  }

  .generate-main-row {
    gap: 12px;
  }

  .blueprint-panel-heading,
  .blueprint-preview-heading-actions,
  .blueprint-status-strip,
  .mcr-history-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .blueprint-panel-heading {
    display: grid;
  }

  .blueprint-preview-heading-actions {
    flex-wrap: wrap;
    justify-items: start;
    justify-content: flex-start;
    gap: 10px;
    width: 100%;
  }

  .blueprint-status-strip {
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .blueprint-panel-heading .blueprint-mode-toggle,
  .blueprint-generate-button {
    width: 100%;
  }

  .mcr-history-header {
    grid-template-columns: 1fr;
  }

  .mcr-history-toolbar {
    justify-content: flex-start;
  }

  .blueprint-meta-grid {
    grid-template-columns: 1fr;
  }

  .blueprint-meta-grid > div {
    border-right: 0;
    border-bottom: 1px solid var(--mcr-blueprint-line-soft);
  }

  .blueprint-meta-grid > div:last-child {
    border-bottom: 0;
  }
}

/* Emby Studio light editor skin. Keeps existing preview/editor layout and logic intact. */
.mcr-page-shell {
  --mcr-blueprint-bg: var(--mcr-color-surface-container-low);
  --mcr-blueprint-bg-deep: var(--mcr-color-surface-container-low);
  --mcr-blueprint-bg-ink: var(--mcr-color-surface-container-high);
  --mcr-blueprint-panel: var(--mcr-color-surface-container-lowest);
  --mcr-blueprint-panel-strong: var(--mcr-color-surface-container-lowest);
  --mcr-blueprint-line: rgba(var(--mcr-rgb-surface-container-highest), 0.92);
  --mcr-blueprint-line-soft: rgba(var(--mcr-rgb-outline-variant), 0.68);
  --mcr-blueprint-cyan: var(--mcr-color-primary-container);
  --mcr-blueprint-danger: var(--mcr-color-error);
  --mcr-cream: var(--mcr-color-surface-container-low);
  --mcr-charcoal: var(--mcr-color-on-surface);
  --mcr-off-white: var(--mcr-color-surface-container-lowest);
  --mcr-muted: var(--mcr-color-on-surface-variant);
  --mcr-border: rgba(var(--mcr-rgb-outline-variant), 0.58);
  --mcr-border-interactive: rgba(var(--mcr-rgb-primary), 0.34);
  --mcr-charcoal-04: rgba(var(--mcr-rgb-primary), 0.06);
  --mcr-charcoal-82: rgba(var(--mcr-rgb-surface-container-low), 0.82);
  --mcr-page-shadow: 0 18px 44px rgba(var(--mcr-rgb-shadow), 0.08), 0 2px 10px rgba(var(--mcr-rgb-shadow), 0.05);
  --mcr-page-shadow-soft: 0 10px 24px rgba(var(--mcr-rgb-shadow), 0.07);
  border: 0;
  border-radius: 0;
  background:
    radial-gradient(circle at 14% 10%, rgba(var(--mcr-rgb-primary-container), 0.12), transparent 28%),
    radial-gradient(circle at 92% 12%, rgba(var(--mcr-rgb-secondary-container), 0.10), transparent 24%),
    linear-gradient(180deg, var(--mcr-color-surface) 0%, var(--mcr-color-surface-container-low) 100%);
  color: var(--mcr-charcoal);
  font-family: var(--mcr-font-body);
}

.mcr-page-shell .mcr-shell__aurora {
  opacity: 0.28;
  background:
    radial-gradient(ellipse at 18% 14%, rgba(var(--mcr-rgb-primary-container), 0.16), transparent 42%),
    radial-gradient(ellipse at 82% 18%, rgba(var(--mcr-rgb-secondary-container), 0.12), transparent 34%);
}

.mcr-page-shell .mcr-shell__noise {
  opacity: 0;
}

.mcr-page-shell :global(.mcr-frame__body),
.mcr-page-shell :global(.mcr-footer-actions),
.mcr-page-shell :global(.mcr-frame),
.mcr-page-shell :global(.v-card),
.mcr-page-shell :global(.v-card-text),
.mcr-page-shell :global(.v-card-actions),
.mcr-page-shell :deep(.v-card),
.mcr-page-shell :deep(.v-window),
.mcr-page-shell :deep(.v-window-item),
.mcr-page-shell :deep(.v-card-text),
.mcr-page-shell :deep(.v-card-actions),
:global(.v-overlay__content .mcr-page-shell .v-card:not(.bg-primary)),
:global(.v-overlay__content .mcr-page-shell .mcr-frame.v-card:not(.bg-primary)),
:global(.v-overlay__content .mcr-page-shell .mcr-frame__body),
:global(.v-overlay__content .mcr-page-shell .mcr-footer-actions),
:global(.v-overlay__content .mcr-page-shell .generate-layout),
:global(.v-overlay__content .mcr-page-shell .blueprint-workbench),
:global(.v-overlay__content .mcr-page-shell .blueprint-preview-bay),
:global(.v-overlay__content .mcr-page-shell .blueprint-panel-heading),
:global(.v-overlay__content .mcr-page-shell .v-window),
:global(.v-overlay__content .mcr-page-shell .v-window-item) {
  background-color: transparent !important;
}

.mcr-frame__body {
  padding: clamp(16px, 2.5vw, 32px) !important;
}

.mcr-page-hero {
  min-height: 72px;
  margin-bottom: 20px;
  padding: 16px 20px;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.74) !important;
  border-radius: 0;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.94) !important;
  box-shadow: 0 1px 0 rgba(var(--mcr-rgb-surface-container-lowest), 0.72), var(--mcr-page-shadow-soft);
}

.mcr-page-hero::before,
.mcr-page-hero::after,
.blueprint-preview-bay::before,
.blueprint-control-bay::before,
.blueprint-preview-frame::before,
.blueprint-preview-frame::after {
  display: none !important;
}

.mcr-page-hero .mcr-shell__header-grid {
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px;
  align-items: center;
}

.mcr-page-hero .mcr-shell__copy {
  gap: 5px;
}

.mcr-kicker-row {
  gap: 8px;
}

.mcr-page-shell :deep(.mcr-kicker),
.mcr-page-shell :deep(.mcr-rev),
.mcr-page-shell :deep(.mcr-panel__eyebrow) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.54);
  font-size: 10px;
  font-weight: 850;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.mcr-page-shell :deep(.mcr-rev) {
  padding: 5px 8px;
  border-radius: 8px;
  border-color: rgba(var(--mcr-rgb-surface-container-highest), 0.86);
  background: rgba(var(--mcr-rgb-surface-container-low), 0.72);
  color: var(--mcr-blueprint-cyan);
}

.mcr-title--compact {
  max-width: 640px;
  color: var(--mcr-charcoal);
  font-size: clamp(1.55rem, 2.4vw, 2.35rem);
  line-height: 1.02;
  letter-spacing: -0.035em;
  text-transform: none;
}

.mcr-page-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.mcr-logo-slot {
  position: relative;
  display: inline-grid;
  width: 46px;
  height: 46px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.78);
  border-radius: 15px;
  background: rgba(var(--mcr-rgb-surface-container-low), 0.76);
  color: var(--mcr-blueprint-cyan);
  cursor: pointer;
  box-shadow: 0 12px 24px rgba(var(--mcr-rgb-shadow), 0.08);
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    background-color 180ms ease,
    color 180ms ease;
}

.mcr-logo-slot:hover {
  transform: translateY(-1px);
  border-color: rgba(var(--mcr-rgb-primary), 0.34);
  background: var(--color-primary-soft);
}

.mcr-logo-slot--donor {
  border-color: rgba(var(--color-rgb-warning), 0.42);
  background: var(--color-warning-soft);
  color: #d99a00;
}

.mcr-page-subtitle {
  max-width: 620px;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.74);
  font-size: 0.88rem;
  line-height: 1.55;
}

.blueprint-hero-actions {
  flex-direction: column;
  align-items: flex-end;
}

.mcr-page-top-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  width: 100%;
}

.mcr-donation-card {
  border: 1px solid var(--color-border) !important;
  border-radius: 24px !important;
  background: var(--color-surface) !important;
  color: var(--color-text-main) !important;
  overflow: hidden;
  box-shadow: 0 24px 58px rgba(47, 76, 128, 0.14) !important;
}

.mcr-donation-card__body {
  display: grid;
  justify-items: center;
  gap: 16px;
  padding: 30px 28px 22px !important;
  text-align: center;
}

.mcr-donation-profile {
  display: grid;
  justify-items: center;
  gap: 7px;
  width: 100%;
}

.mcr-donation-profile__avatar {
  position: relative;
  display: inline-grid;
  width: 88px;
  height: 88px;
  place-items: center;
  border: 7px solid rgba(255, 213, 116, 0.42);
  border-radius: 50%;
  background:
    radial-gradient(circle at 35% 25%, rgba(255, 255, 255, 0.92), transparent 38%),
    linear-gradient(135deg, #fff6d7, #ffe7a6);
  color: #1777ff;
  box-shadow:
    0 14px 30px rgba(170, 126, 28, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.mcr-donation-profile__avatar img {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: inherit;
  object-fit: cover;
}

.mcr-donation-profile__crown {
  position: absolute;
  top: -14px;
  right: -7px;
  display: inline-grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border-radius: 50%;
  background: #fff7d7;
  color: #d59b18;
  transform: rotate(16deg);
  box-shadow: 0 10px 20px rgba(170, 126, 28, 0.16);
}

.mcr-donation-heart {
  display: inline-grid;
  width: 56px;
  height: 56px;
  place-items: center;
  border: 1px solid rgba(255, 133, 166, 0.24);
  border-radius: 50%;
  background:
    radial-gradient(circle at 34% 24%, rgba(255, 255, 255, 0.8), transparent 34%),
    linear-gradient(135deg, #ffe7ef, #ffd4e1);
  color: #ff6f9c;
  box-shadow:
    0 12px 26px rgba(255, 111, 156, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.mcr-donation-title {
  margin: 2px 0 0;
  color: var(--color-text-main);
  font-size: 22px;
  font-weight: 900;
  letter-spacing: 0;
  line-height: 1.18;
}

.mcr-donation-subtitle {
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0.12em;
  line-height: 1;
  text-transform: uppercase;
}

.mcr-donation-message {
  max-width: 300px;
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 600;
  line-height: 1.6;
}

.mcr-donation-qr {
  display: grid;
  width: 100%;
  max-width: 286px;
  min-height: 260px;
  place-items: center;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 22px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.78), transparent 54%),
    var(--color-surface-soft);
  color: var(--color-text-muted);
  font-weight: 850;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.78),
    0 10px 26px rgba(47, 76, 128, 0.08);
}

.mcr-donation-qr__image {
  display: block;
  width: min(224px, 68vw);
  max-width: 100%;
  aspect-ratio: 1;
  border-radius: 18px;
  object-fit: contain;
  background: #fff;
  box-shadow: 0 12px 28px rgba(47, 76, 128, 0.12);
}

.mcr-donation-card__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  width: 100%;
  margin-top: 2px;
}

.mcr-donation-card__actions .v-btn {
  width: min(230px, 100%);
  min-height: 44px;
  border-radius: 16px !important;
  font-weight: 850 !important;
}

.mcr-donation-card__actions .v-btn:only-child {
  width: min(230px, 100%);
}

.mcr-donation-card__actions .mcr-button--apple-primary {
  background: #1777ff !important;
  color: #10213f !important;
  box-shadow: 0 12px 24px rgba(23, 119, 255, 0.18) !important;
}

.mcr-donation-card__actions .mcr-donation-support-confirm {
  border: 1px solid rgba(223, 232, 246, 0.9) !important;
  background: #f3f5f8 !important;
  color: #2f3a4f !important;
  box-shadow: 0 10px 22px rgba(47, 76, 128, 0.08) !important;
}

.mcr-donation-card__actions .mcr-donation-soft-action {
  border: 1px solid rgba(223, 232, 246, 0.9) !important;
  background: #f3f5f8 !important;
  color: #2f3a4f !important;
  box-shadow: 0 10px 22px rgba(47, 76, 128, 0.08) !important;
}

.mcr-donation-card__actions .mcr-donation-continue-support {
  border: 1px solid rgba(223, 232, 246, 0.9) !important;
  background: #f3f5f8 !important;
  color: #2f3a4f !important;
  box-shadow: 0 10px 22px rgba(47, 76, 128, 0.08) !important;
}

.mcr-donation-card__actions .mcr-donation-support-confirm :deep(.v-btn__prepend),
.mcr-donation-card__actions .mcr-donation-continue-support :deep(.v-icon),
.mcr-donation-card__actions .mcr-donation-support-confirm :deep(.v-icon) {
  color: #ff3b30 !important;
  opacity: 1 !important;
}

.mcr-donation-support-heart {
  margin-right: 8px;
  color: #ff3b30 !important;
  opacity: 1 !important;
}

.mcr-donation-card__actions :deep(.mcr-donation-support-heart),
.mcr-donation-card__actions :deep(.mcr-donation-support-heart .v-icon__svg) {
  color: #ff3b30 !important;
  fill: currentColor !important;
  opacity: 1 !important;
}

.mcr-donation-footnote {
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 850;
  letter-spacing: 0.12em;
  line-height: 1.3;
  opacity: 0.72;
}

.mcr-page-tabs--hero {
  min-width: 254px;
  width: min(320px, 32vw);
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.86);
  border-radius: 14px;
  background: var(--mcr-color-surface-container-low);
  box-shadow: none;
}

.mcr-page-tabs--hero :deep(.v-tab),
.mcr-page-shell :deep(.mcr-tab) {
  min-height: 42px !important;
  height: 42px !important;
  border-radius: 11px !important;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.72) !important;
  font-size: 13px !important;
  font-weight: 750 !important;
  letter-spacing: 0 !important;
}

.mcr-page-shell :deep(.mcr-button--primary),
.mcr-page-shell :deep(.mcr-button--active),
.mcr-page-shell :deep(.mcr-tab--active) {
  background: var(--mcr-color-primary) !important;
  color: var(--mcr-color-surface-container-lowest) !important;
  border-color: var(--mcr-color-primary) !important;
  box-shadow: 0 12px 24px rgba(var(--mcr-rgb-primary), 0.16) !important;
}

.mcr-page-shell :deep(.mcr-button--ghost) {
  background: var(--mcr-color-surface-container-lowest) !important;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.86) !important;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.72) !important;
  box-shadow: none !important;
}

.mcr-page-shell :deep(.mcr-button--danger) {
  background: var(--mcr-color-error) !important;
  color: var(--mcr-color-surface-container-lowest) !important;
  border-color: var(--mcr-color-error) !important;
  box-shadow: 0 12px 24px rgba(var(--mcr-rgb-error), 0.12) !important;
}

.mcr-page-shell :deep(.mcr-button) {
  border-radius: 12px !important;
  font-weight: 750 !important;
  transition:
    transform 180ms ease,
    filter 180ms ease,
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease;
}

.mcr-page-shell :deep(.mcr-button:hover) {
  opacity: 1;
  transform: translateY(-1px);
}

.generate-layout {
  padding-top: 0;
}

.blueprint-workbench {
  gap: 20px;
}

.blueprint-preview-bay,
.blueprint-control-bay {
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.78);
  border-radius: 0;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.94);
  box-shadow: var(--mcr-page-shadow);
}

.blueprint-preview-bay {
  padding: clamp(16px, 2vw, 24px);
}

.blueprint-control-bay {
  padding: 20px;
}

.blueprint-workbench--editing .blueprint-preview-bay {
  padding: 18px;
}

.blueprint-panel-heading {
  align-items: center;
  margin-bottom: 16px;
}

.mcr-page-shell :deep(.mcr-panel__title) {
  color: var(--mcr-charcoal);
  font-size: 1.22rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.blueprint-preview-heading-actions {
  gap: 12px;
}

.blueprint-status-strip {
  color: var(--mcr-blueprint-cyan);
  font-size: 11px;
  text-transform: none;
}

.blueprint-status-strip span {
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.22);
  border-radius: 999px;
  padding: 6px 9px;
  background: rgba(var(--mcr-rgb-primary-fixed), 0.32);
  color: var(--mcr-color-primary);
}

.blueprint-preview-frame {
  padding: clamp(10px, 1.6vw, 16px);
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.82);
  border-bottom: 0;
  border-radius: 24px 24px 0 0;
  background:
    linear-gradient(135deg, rgba(var(--mcr-rgb-surface-container-lowest), 0.94), rgba(var(--mcr-rgb-surface), 0.82)),
    var(--mcr-color-surface-container-lowest);
  box-shadow:
    0 1px 2px rgba(var(--mcr-rgb-shadow), 0.07),
    0 18px 42px rgba(var(--mcr-rgb-shadow), 0.12);
}

.blueprint-preview-frame :deep(.simulation-canvas),
.blueprint-preview-frame :deep(.simulation-empty) {
  overflow: hidden;
  border-radius: 18px;
  border: 0;
}

.blueprint-meta-grid {
  overflow: hidden;
  margin-top: 0;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.82);
  border-top: 0;
  border-radius: 0 0 24px 24px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.72);
}

.blueprint-meta-grid--editor {
  border-top: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.82);
  border-radius: 18px;
}

.blueprint-meta-grid > div {
  border-right: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.82);
}

.blueprint-meta-grid span,
.blueprint-control-label {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.55);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.blueprint-meta-grid strong {
  color: var(--mcr-charcoal);
  font-size: 13px;
  font-weight: 750;
}

.blueprint-mode-toggle {
  grid-template-columns: minmax(42px, auto) 52px minmax(42px, auto);
  min-height: 40px;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.86);
  border-radius: 12px;
  background: var(--mcr-color-surface-container-low);
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.78);
  font-size: 12px;
  box-shadow: none;
}

.blueprint-mode-toggle::after {
  display: none;
}

.blueprint-mode-toggle:hover,
.blueprint-mode-toggle:focus-visible,
.blueprint-mode-toggle--pulse {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.34);
  box-shadow: 0 10px 20px rgba(var(--mcr-rgb-shadow), 0.07);
}

.blueprint-mode-option {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.62);
}

.blueprint-mode-toggle:not(.blueprint-mode-toggle--animated) .blueprint-mode-option--static,
.blueprint-mode-toggle--animated .blueprint-mode-option--animated {
  color: var(--mcr-color-primary);
}

.blueprint-mode-switch-track {
  width: 52px;
  height: 28px;
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.74);
  background: var(--mcr-color-surface-container-highest);
  box-shadow: inset 0 1px 2px rgba(var(--mcr-rgb-shadow), 0.08);
}

.blueprint-mode-thumb {
  border: 0;
  background: var(--mcr-color-surface-container-lowest);
  box-shadow: 0 2px 8px rgba(var(--mcr-rgb-shadow), 0.18);
}

.blueprint-mode-thumb::after {
  display: none;
}

.blueprint-mode-toggle--animated .blueprint-mode-switch-track {
  border-color: var(--mcr-color-primary-container);
  background: var(--mcr-color-primary-container);
  box-shadow: inset 0 1px 2px rgba(var(--mcr-rgb-primary), 0.18);
}

.blueprint-mode-toggle--animated .blueprint-mode-thumb {
  transform: translateX(24px);
  background: var(--mcr-color-surface-container-lowest);
  border-color: transparent;
  box-shadow: 0 2px 8px rgba(var(--mcr-rgb-primary), 0.22);
}

.mcr-scheme-list {
  gap: 12px;
}

.mcr-scheme-list__scroll {
  gap: 12px;
  scrollbar-color: rgba(var(--mcr-rgb-primary-container), 0.42) rgba(var(--mcr-rgb-surface-container-high), 0.54);
}

.mcr-scheme-list__scroll::-webkit-scrollbar-track {
  background: rgba(var(--mcr-rgb-surface-container-high), 0.54);
}

.mcr-scheme-list__scroll::-webkit-scrollbar-thumb {
  background: rgba(var(--mcr-rgb-primary-container), 0.42);
}

.mcr-scheme-row {
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.82);
  border-radius: 14px;
  background: var(--mcr-color-surface-container-low);
  color: var(--mcr-charcoal);
  box-shadow: none;
}

.mcr-scheme-row:hover,
.mcr-scheme-row--active {
  border-color: var(--mcr-color-primary);
  box-shadow: 0 14px 28px rgba(var(--mcr-rgb-shadow), 0.10);
}

.mcr-scheme-row--active {
  background: var(--mcr-color-primary-container);
  color: var(--mcr-color-on-primary-container);
}

.mcr-scheme-row__media {
  border-color: rgba(var(--mcr-rgb-surface-container-highest), 0.72);
  background: var(--mcr-color-surface-container-high);
}

.mcr-scheme-row--active .mcr-scheme-row__media {
  border-color: transparent;
  border-width: 0;
}

.mcr-scheme-row__media :deep(.simulation-canvas),
.mcr-scheme-row__media :deep(.simulation-empty) {
  transition: transform 700ms ease;
}

.mcr-scheme-row:hover .mcr-scheme-row__media :deep(.simulation-canvas) {
  transform: scale(1.045);
}

.mcr-scheme-row__body strong {
  color: var(--mcr-charcoal);
}

.mcr-scheme-row__body span {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.70);
}

.mcr-scheme-row--active .mcr-scheme-row__body strong,
.mcr-scheme-row--active .mcr-scheme-row__body span {
  color: var(--mcr-color-on-primary-container);
}

.mcr-scheme-row__actions {
  border-color: rgba(var(--mcr-rgb-surface-container-highest), 0.72);
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.90);
  box-shadow: 0 10px 22px rgba(var(--mcr-rgb-shadow), 0.12);
}

.mcr-scheme-row__icon {
  color: var(--mcr-color-primary) !important;
}

.mcr-scheme-list__tail {
  border-top-color: rgba(var(--mcr-rgb-surface-container-highest), 0.58);
}

.mcr-scheme-tail-button {
  min-height: 30px !important;
  height: 30px !important;
  border-radius: 10px !important;
}

.blueprint-skeleton {
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.82);
  border-radius: 14px;
  background:
    linear-gradient(90deg, rgba(var(--mcr-rgb-surface-container-low), 0.68), rgba(var(--mcr-rgb-surface-container-lowest), 0.94), rgba(var(--mcr-rgb-surface-container-low), 0.68)),
    var(--mcr-color-surface-container);
  background-size: 200% 100%, cover;
  box-shadow: none;
}

.blueprint-skeleton::before {
  background: linear-gradient(
    105deg,
    transparent 0%,
    rgba(var(--mcr-rgb-surface-container-lowest), 0.20) 38%,
    rgba(var(--mcr-rgb-primary-container), 0.12) 50%,
    rgba(var(--mcr-rgb-surface-container-lowest), 0.20) 62%,
    transparent 100%
  );
}

.blueprint-skeleton__grid {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.55);
}

.blueprint-skeleton__poster,
.blueprint-skeleton__line {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.7);
  background: rgba(var(--mcr-rgb-surface-container-highest), 0.74);
  box-shadow: none;
}

.preview-card,
.backend-preview-shell,
.backend-preview-empty {
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.82);
  border-radius: 18px;
  background: var(--mcr-color-surface-container-lowest);
}

.backend-preview-empty {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.72);
}

.mcr-page-shell :deep(.v-slider) {
  color: var(--mcr-color-primary-container) !important;
  --v-theme-primary: var(--mcr-v-theme-slider-primary);
  --v-theme-surface-variant: var(--mcr-v-theme-slider-surface-variant);
}

.mcr-page-shell :deep(.v-slider__label),
.mcr-page-shell :deep(.v-slider-track__tick-label) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.82) !important;
}

.mcr-page-shell :deep(.v-slider-track__background),
.mcr-page-shell :deep(.v-slider-track__tick),
.mcr-page-shell :deep(.v-slider-track__track) {
  background-color: rgba(var(--mcr-rgb-surface-container-highest), 0.86) !important;
  border-color: rgba(var(--mcr-rgb-surface-container-highest), 0.86) !important;
}

.mcr-page-shell :deep(.v-slider-track__fill) {
  background: var(--mcr-color-primary-container) !important;
  border-color: var(--mcr-color-primary-container) !important;
  box-shadow: none !important;
}

.mcr-page-shell :deep(.v-slider-thumb__surface) {
  background-color: var(--mcr-color-surface-container-lowest) !important;
  border: 4px solid var(--mcr-color-primary-container) !important;
  color: var(--mcr-color-primary) !important;
  box-shadow: 0 2px 8px rgba(var(--mcr-rgb-shadow), 0.16) !important;
}

.mcr-page-shell :deep(.v-slider-thumb__label) {
  background-color: var(--mcr-color-primary) !important;
  color: var(--mcr-color-surface-container-lowest) !important;
  border: 0;
}

.mcr-history-header {
  align-items: center;
  gap: 14px;
  width: 100%;
  max-width: none;
  margin: 0 0 18px;
  padding: 16px 20px;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.78);
  border-radius: 16px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.94);
  box-shadow: var(--mcr-page-shadow-soft);
  overflow: visible;
}

.mcr-history-toolbar {
  gap: 12px;
  flex-wrap: nowrap;
  justify-content: flex-end;
  overflow: visible;
  padding: 4px 0;
  scrollbar-width: none;
}

.mcr-history-toolbar::-webkit-scrollbar {
  display: none;
}

.mcr-history-toggle {
  overflow: visible !important;
  border-radius: 999px !important;
}

.mcr-history-toggle :deep(.v-btn) {
  min-height: 38px;
}

.mcr-history-sort {
  width: 168px;
  min-width: 168px;
  flex: 0 0 168px;
  background: transparent;
  border: 0;
  box-shadow: none;
}

.mcr-history-sort :deep(.mcr-blueprint-select__control) {
  min-height: 40px;
}

.mcr-history-floating-actions {
  position: fixed;
  z-index: 2400;
  left: 50%;
  top: clamp(72px, 8vh, 112px);
  transform: translateX(-50%);
  display: flex;
  width: max-content;
  max-width: min(680px, calc(100vw - 24px));
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0;
  padding: 8px;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.72);
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.92);
  box-shadow: 0 18px 42px rgba(var(--mcr-rgb-shadow), 0.16);
  backdrop-filter: blur(18px);
}

.mcr-history-floating-button {
  min-height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 12px;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.76);
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-surface-container), 0.72);
  color: var(--mcr-color-on-surface);
  font: inherit;
  font-size: 12px;
  font-weight: 760;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease, color 0.16s ease;
}

.mcr-history-floating-button:hover {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.68);
  background: rgba(var(--mcr-rgb-primary-fixed), 0.22);
  color: var(--mcr-color-primary);
  transform: translateY(-1px);
}

.mcr-history-floating-button:disabled {
  cursor: not-allowed;
  opacity: 0.48;
  transform: none;
}

.mcr-history-floating-button--primary {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.88);
  background: var(--mcr-color-primary-container);
  color: var(--mcr-color-on-primary-container);
}

.mcr-history-floating-button--primary:hover {
  background: var(--mcr-color-primary);
  color: var(--mcr-color-on-primary);
}

.mcr-history-floating-button--danger {
  border-color: rgba(var(--mcr-rgb-error-container), 0.76);
  background: rgba(var(--mcr-rgb-error-container), 0.14);
  color: var(--mcr-color-error);
}

.mcr-history-floating-button--danger:hover {
  background: var(--mcr-color-error);
  color: var(--mcr-color-on-error);
}

.mcr-history-selection-count {
  padding: 0 8px 0 10px;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.74);
  font-size: 12px;
  font-weight: 750;
  white-space: nowrap;
}

.mcr-history-empty {
  display: grid;
  min-height: 160px;
  place-items: center;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.62);
  font-size: 0.92rem;
}

.mcr-visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

:global(.mcr-template-action-menu) {
  min-width: 176px;
  padding: 6px !important;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.72) !important;
  border-radius: 14px !important;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.96) !important;
  color: var(--mcr-color-on-surface) !important;
  box-shadow: var(--mcr-depth-shadow-2) !important;
  backdrop-filter: blur(18px);
}

:global(.mcr-template-action-menu .v-list-item) {
  min-height: 34px !important;
  border-radius: 10px !important;
  color: var(--mcr-color-on-surface) !important;
}

:global(.mcr-template-action-menu .v-list-item-title),
:global(.mcr-template-action-menu .v-list-item__content) {
  color: inherit !important;
  -webkit-text-fill-color: currentColor !important;
}

:global(.mcr-template-action-menu .v-list-item:hover) {
  background: rgba(var(--mcr-rgb-primary-fixed), 0.18) !important;
  color: var(--mcr-color-primary) !important;
}

:global(.mcr-template-action-menu[data-mcr-theme="dark"]) {
  border-color: #3d484f !important;
  background: #1b2024 !important;
  color: #dee3e8 !important;
  box-shadow: 0 18px 42px rgba(0, 0, 0, 0.42) !important;
}

:global(.mcr-template-action-menu[data-mcr-theme="dark"] .v-list-item),
:global(.mcr-template-action-menu[data-mcr-theme="dark"] .v-list-item-title),
:global(.mcr-template-action-menu[data-mcr-theme="dark"] .v-list-item__content) {
  color: #dee3e8 !important;
  -webkit-text-fill-color: #dee3e8 !important;
}

:global(.mcr-template-action-menu[data-mcr-theme="dark"] .v-list-item:hover) {
  background: rgba(0, 180, 240, 0.18) !important;
  color: #79d1ff !important;
  -webkit-text-fill-color: #79d1ff !important;
}

:global(.mcr-template-action-menu[data-mcr-theme="dark"] .v-list-item:hover .v-list-item-title),
:global(.mcr-template-action-menu[data-mcr-theme="dark"] .v-list-item:hover .v-list-item__content) {
  color: #79d1ff !important;
  -webkit-text-fill-color: #79d1ff !important;
}

.mcr-history-groups {
  width: 100%;
  max-width: none;
  margin: 0;
  gap: 24px;
}

.mcr-history-group {
  padding-top: 0;
  border-top: 0;
}

.mcr-history-group__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  color: var(--mcr-charcoal);
  font-family: inherit;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: none;
}

.mcr-history-group__title {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
}

.mcr-history-group__title span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcr-history-group__heading strong {
  min-width: 28px;
  min-height: 24px;
  display: inline-grid;
  place-items: center;
  border-radius: 8px;
  background: rgba(var(--mcr-rgb-primary-fixed), 0.44);
  color: var(--mcr-color-primary);
}

.mcr-history-group__select {
  min-width: 76px !important;
  flex: 0 0 auto;
  padding-inline: 10px !important;
}

.mcr-history-card {
  overflow: hidden;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.58);
  border-radius: 16px;
  background: var(--mcr-color-surface-container-lowest) !important;
  box-shadow: none;
}

.mcr-history-card--selected,
.mcr-history-card:hover {
  border-color: rgba(var(--mcr-rgb-primary), 0.42);
  box-shadow: 0 16px 34px rgba(var(--mcr-rgb-shadow), 0.11);
  transform: translateY(-2px);
}

.mcr-history-card__media {
  position: relative;
  overflow: hidden;
}

.mcr-history-card__image {
  border-radius: 0;
  transition: transform 700ms ease;
}

.mcr-history-card:hover .mcr-history-card__image {
  transform: none;
}

.mcr-history-card__check {
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  display: inline-grid;
  place-items: center;
  padding: 0;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-lowest), 0.74);
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-shadow), 0.28);
  box-shadow: 0 6px 18px rgba(var(--mcr-rgb-shadow), 0.12);
  backdrop-filter: blur(10px);
  cursor: pointer;
  opacity: 0;
  transform: scale(0.94);
  transition:
    opacity 180ms ease,
    transform 180ms ease,
    background-color 180ms ease,
    border-color 180ms ease;
}

.mcr-history-card:hover .mcr-history-card__check,
.mcr-history-card__check--active {
  opacity: 1;
  transform: scale(1);
}

.mcr-history-card__check:disabled {
  cursor: not-allowed;
  opacity: 0.42;
}

.mcr-history-card__check-mark {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(var(--mcr-rgb-surface-container-lowest), 0.92);
  border-radius: 999px;
}

.mcr-history-card__check--active {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.86);
  background: var(--mcr-color-primary-container);
}

.mcr-history-card__check--active .mcr-history-card__check-mark {
  width: 13px;
  height: 8px;
  border-top: 0;
  border-right: 0;
  border-radius: 0;
  transform: translateY(-1px) rotate(-45deg);
}

.mcr-history-card__title {
  position: absolute;
  left: 10px;
  bottom: 10px;
  z-index: 2;
  max-width: calc(100% - 20px);
  overflow: hidden;
  min-height: 20px;
  padding: 3px 7px;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-lowest), 0.28);
  border-radius: 7px;
  background: rgba(var(--mcr-rgb-shadow), 0.46);
  color: rgba(var(--mcr-rgb-surface-container-lowest), 0.94);
  font-size: 11px;
  font-weight: 650;
  line-height: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
  backdrop-filter: blur(12px);
}

.mcr-history-card__meta {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.66);
  font-size: 0.82rem;
  line-height: 1.45;
}

.mcr-history-card__actions {
  position: absolute;
  z-index: 3;
  right: 8px;
  bottom: 8px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  opacity: 0;
  max-height: none;
  margin-top: 0;
  overflow: visible;
  pointer-events: none;
  transform: translateY(6px);
  transition:
    opacity 180ms ease,
    transform 180ms ease;
}

.mcr-history-card:hover .mcr-history-card__actions,
.mcr-history-card__actions:focus-within {
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}

.mcr-history-card__actions :deep(.v-btn) {
  min-height: 32px !important;
  padding-inline: 10px !important;
  backdrop-filter: blur(14px);
}

.mcr-page-shell :deep(.mcr-alert) {
  border-radius: 16px !important;
  background: rgba(var(--mcr-rgb-primary-fixed), 0.32) !important;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.20) !important;
  color: var(--mcr-color-on-surface) !important;
  box-shadow: none !important;
}

.mcr-page-shell :deep(.v-alert.v-theme--light.text-info),
.mcr-page-shell :deep(.v-alert.v-theme--light.text-info .v-alert__content),
.mcr-page-shell :deep(.v-alert.v-theme--light.text-info .v-alert-title) {
  color: var(--mcr-color-on-surface) !important;
  -webkit-text-fill-color: var(--mcr-color-on-surface) !important;
}

.mcr-page-shell[data-mcr-theme="light"] :deep(.mcr-alert),
.mcr-page-shell[data-mcr-theme="light"] :deep(.mcr-alert *),
.mcr-page-shell[data-mcr-theme="light"] :deep(.v-alert.v-theme--light.text-info),
.mcr-page-shell[data-mcr-theme="light"] :deep(.v-alert.v-theme--light.text-info *) {
  color: var(--mcr-color-on-surface) !important;
  -webkit-text-fill-color: var(--mcr-color-on-surface) !important;
}

.mcr-control,
.mcr-history-sort {
  border-radius: 12px;
  background: var(--mcr-color-surface-container-lowest);
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.72);
}

.mcr-history-sort {
  background: transparent;
  border: 0;
}

.mcr-page-shell :deep(.mcr-blueprint-field),
.mcr-page-shell :deep(.mcr-blueprint-select) {
  gap: 7px;
  color: var(--mcr-charcoal);
  font-family: inherit;
}

.mcr-page-shell :deep(.mcr-blueprint-field__label),
.mcr-page-shell :deep(.mcr-blueprint-select__label) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.70);
  font-size: 12px;
  font-weight: 750;
  letter-spacing: 0.02em;
  text-transform: none;
}

.mcr-page-shell :deep(.mcr-blueprint-field__control),
.mcr-page-shell :deep(.mcr-blueprint-select__control) {
  min-height: 42px;
  padding: 10px 12px;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.66);
  border-radius: 12px;
  background: var(--mcr-color-surface-container-lowest);
  background-image: none;
  color: var(--mcr-charcoal);
  box-shadow: none;
  font-family: inherit;
  font-size: 13px;
}

.mcr-page-shell :deep(.mcr-blueprint-select__control) {
  padding-right: 34px;
}

.mcr-page-shell :deep(.mcr-blueprint-field__control:focus),
.mcr-page-shell :deep(.mcr-blueprint-select__control:focus) {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.74);
  background: var(--mcr-color-surface-container-lowest);
  box-shadow: 0 0 0 4px rgba(var(--mcr-rgb-primary-container), 0.11);
}

.mcr-page-shell :deep(.mcr-blueprint-select__shell::after) {
  border-color: rgba(var(--mcr-rgb-on-surface-variant), 0.70);
}

.mcr-page-shell :deep(.mcr-blueprint-select__multi-list) {
  grid-template-columns: repeat(auto-fit, minmax(172px, 1fr));
}

.mcr-page-shell :deep(.mcr-blueprint-field__hint),
.mcr-page-shell :deep(.mcr-blueprint-select__hint) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.56);
}

.info-label,
.source-slot {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.60);
}

.info-value,
.source-name {
  color: rgba(var(--mcr-rgb-surface-container-low), 0.82);
}

.mcr-footer-actions {
  gap: 12px;
  padding: 16px clamp(16px, 2.5vw, 32px) !important;
  border-top: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.78);
  background: rgba(var(--mcr-rgb-surface), 0.84) !important;
  backdrop-filter: blur(16px);
}

.mcr-page-shell[data-mcr-theme="dark"] {
  --mcr-blueprint-bg: var(--mcr-color-surface);
  --mcr-blueprint-bg-deep: var(--mcr-color-surface-container-lowest);
  --mcr-blueprint-panel: var(--mcr-color-surface-container-low);
  --mcr-blueprint-panel-soft: var(--mcr-color-surface-container);
  --mcr-blueprint-border: rgba(var(--mcr-rgb-outline-variant), 0.86);
  --mcr-blueprint-line: rgba(var(--mcr-rgb-outline), 0.30);
  --mcr-blueprint-cyan: var(--mcr-color-primary-container);
  --mcr-blueprint-cyan-soft: rgba(var(--mcr-rgb-primary-container), 0.18);
  --mcr-cream: var(--mcr-color-surface);
  --mcr-off-white: var(--mcr-color-surface-container-lowest);
  --mcr-charcoal: var(--mcr-color-on-surface);
  --mcr-muted: var(--mcr-color-on-surface-variant);
  --mcr-border: rgba(var(--mcr-rgb-outline-variant), 0.86);
  --mcr-border-interactive: rgba(var(--mcr-rgb-primary-container), 0.56);
  background:
    radial-gradient(circle at 18% 12%, rgba(var(--mcr-rgb-primary-container), 0.10), transparent 28%),
    radial-gradient(circle at 84% 14%, rgba(var(--mcr-rgb-tertiary), 0.08), transparent 28%),
    var(--mcr-depth-0) !important;
  color: var(--mcr-color-on-surface);
  font-family: var(--mcr-font-body);
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-frame),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-frame__body),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.v-card),
.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-hero,
.mcr-page-shell[data-mcr-theme="dark"] .blueprint-control-bay,
.mcr-page-shell[data-mcr-theme="dark"] .blueprint-preview-bay,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-history-header,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-history-card,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-control,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-history-sort {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.86) !important;
  background: rgba(var(--mcr-rgb-surface-container-low), 0.88) !important;
  color: var(--mcr-color-on-surface) !important;
  box-shadow: var(--mcr-depth-shadow-1) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-history-card--selected,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-history-card:hover,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row--active,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row:hover {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.64) !important;
  box-shadow: 0 20px 42px rgba(var(--mcr-rgb-shadow), 0.38) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-panel__eyebrow,
.mcr-page-shell[data-mcr-theme="dark"] .blueprint-panel-heading__meta,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-history-card__meta,
.mcr-page-shell[data-mcr-theme="dark"] .info-label,
.mcr-page-shell[data-mcr-theme="dark"] .source-slot {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.72) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-panel__title,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-history-card__title,
.mcr-page-shell[data-mcr-theme="dark"] .info-value,
.mcr-page-shell[data-mcr-theme="dark"] .source-name,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-history-group__heading {
  color: var(--mcr-color-on-surface) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-history-card__title {
  border-color: rgba(var(--mcr-rgb-surface-container-lowest), 0.22) !important;
  background: rgba(var(--mcr-rgb-shadow), 0.56) !important;
  color: rgba(var(--mcr-rgb-on-surface), 0.94) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-history-sort {
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-history-floating-actions,
.mcr-history-floating-actions[data-mcr-theme="dark"] {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.92);
  background: rgba(var(--mcr-rgb-surface-container-low), 0.92);
  box-shadow: var(--mcr-depth-shadow-2);
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-history-group__heading strong {
  background: rgba(var(--mcr-rgb-primary-container), 0.16);
  color: var(--mcr-color-primary);
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-button--primary),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-button--active),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-tab--active) {
  background: var(--mcr-color-primary-container) !important;
  border-color: var(--mcr-color-primary-container) !important;
  color: var(--mcr-color-on-primary) !important;
  box-shadow: 0 14px 24px rgba(var(--mcr-rgb-primary-container), 0.20) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-button--ghost) {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.92) !important;
  background: rgba(var(--mcr-rgb-surface-container), 0.92) !important;
  color: var(--mcr-color-on-surface-variant) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-blueprint-field__control),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-blueprint-select__control),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-blueprint-select__multi-option) {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.92) !important;
  background: var(--mcr-color-surface-container-lowest) !important;
  color: var(--mcr-color-on-surface) !important;
  -webkit-text-fill-color: var(--mcr-color-on-surface) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-blueprint-select__multi-option--active) {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.72) !important;
  background: rgba(var(--mcr-rgb-primary-container), 0.14) !important;
  color: var(--mcr-color-primary) !important;
  -webkit-text-fill-color: var(--mcr-color-primary) !important;
  box-shadow: inset 3px 0 0 var(--mcr-color-primary-container) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-footer-actions {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.86) !important;
  background: rgba(var(--mcr-rgb-surface), 0.86) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .blueprint-workbench,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-list,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-history-groups {
  background: transparent !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-panel),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-panel__body),
.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row,
.mcr-page-shell[data-mcr-theme="dark"] .preview-card,
.mcr-page-shell[data-mcr-theme="dark"] .backend-preview-shell,
.mcr-page-shell[data-mcr-theme="dark"] .backend-preview-empty,
.mcr-page-shell[data-mcr-theme="dark"] .blueprint-side-panel {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.86) !important;
  background: rgba(var(--mcr-rgb-surface-container-low), 0.88) !important;
  background-color: rgba(var(--mcr-rgb-surface-container-low), 0.88) !important;
  color: var(--mcr-color-on-surface) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-title,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-subtitle,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row__body strong,
.mcr-page-shell[data-mcr-theme="dark"] .page-title-preview__zh,
.mcr-page-shell[data-mcr-theme="dark"] :deep(.v-label),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.v-field-label),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.v-selection-control .v-label) {
  color: var(--mcr-color-on-surface) !important;
  -webkit-text-fill-color: var(--mcr-color-on-surface) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-note,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row__body span,
.mcr-page-shell[data-mcr-theme="dark"] .page-title-preview__en,
.mcr-page-shell[data-mcr-theme="dark"] :deep(.v-input__details),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.v-messages__message) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.72) !important;
  -webkit-text-fill-color: rgba(var(--mcr-rgb-on-surface-variant), 0.72) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row--active {
  background: var(--mcr-color-primary-container) !important;
  background-color: var(--mcr-color-primary-container) !important;
  color: var(--mcr-color-on-primary-container) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row--active .mcr-scheme-row__body strong,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row--active .mcr-scheme-row__body span {
  color: var(--mcr-color-on-primary-container) !important;
  -webkit-text-fill-color: var(--mcr-color-on-primary-container) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.v-divider) {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.86) !important;
  opacity: 1 !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.v-switch__track) {
  background-color: var(--mcr-color-on-surface) !important;
  border-color: var(--mcr-color-outline-variant) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.v-selection-control--dirty .v-switch__track) {
  background-color: var(--mcr-color-primary-container) !important;
  border-color: var(--mcr-color-primary-container) !important;
}

@media (prefers-color-scheme: dark) {
  .mcr-page-shell {
    --mcr-blueprint-bg: var(--mcr-color-surface);
    --mcr-blueprint-bg-deep: var(--mcr-color-surface-container-lowest);
    --mcr-blueprint-panel: var(--mcr-color-surface-container-low);
    --mcr-blueprint-panel-soft: var(--mcr-color-surface-container);
    --mcr-blueprint-border: rgba(var(--mcr-rgb-outline-variant), 0.86);
    --mcr-blueprint-line: rgba(var(--mcr-rgb-outline), 0.30);
    --mcr-blueprint-cyan: var(--mcr-color-primary-container);
    --mcr-blueprint-cyan-soft: rgba(var(--mcr-rgb-primary-container), 0.18);
    --mcr-cream: var(--mcr-color-surface);
    --mcr-off-white: var(--mcr-color-surface-container-lowest);
    --mcr-charcoal: var(--mcr-color-on-surface);
    --mcr-muted: var(--mcr-color-on-surface-variant);
    --mcr-border: rgba(var(--mcr-rgb-outline-variant), 0.86);
    --mcr-border-interactive: rgba(var(--mcr-rgb-primary-container), 0.56);
  }
}

/* Clean colorful page skin. This intentionally targets only the application UI
   chrome; preview canvases keep their own rendering colors. */
.mcr-page-shell {
  --mcr-blueprint-bg: var(--color-bg);
  --mcr-blueprint-bg-deep: var(--color-bg);
  --mcr-blueprint-bg-ink: var(--color-surface-soft);
  --mcr-blueprint-panel: var(--color-surface);
  --mcr-blueprint-panel-strong: var(--color-surface);
  --mcr-blueprint-panel-soft: var(--color-surface-soft);
  --mcr-blueprint-border: var(--color-border);
  --mcr-blueprint-line: rgba(var(--color-rgb-primary), 0.12);
  --mcr-blueprint-line-soft: var(--color-border);
  --mcr-blueprint-cyan: var(--color-primary);
  --mcr-blueprint-cyan-soft: var(--color-primary-soft);
  --mcr-blueprint-danger: var(--color-danger);
  --mcr-cream: var(--color-surface);
  --mcr-charcoal: var(--color-text-main);
  --mcr-off-white: var(--color-bg);
  --mcr-muted: var(--color-text-secondary);
  --mcr-border: var(--color-border);
  --mcr-border-interactive: rgba(var(--color-rgb-primary), 0.42);
  --mcr-page-shadow: 0 18px 42px var(--color-shadow);
  --mcr-page-shadow-soft: 0 12px 28px var(--color-shadow);
  background:
    radial-gradient(circle at 12% 8%, rgba(var(--color-rgb-primary), 0.10), transparent 28%),
    radial-gradient(circle at 88% 8%, rgba(var(--color-rgb-secondary), 0.09), transparent 24%),
    linear-gradient(180deg, var(--color-bg), var(--color-surface-soft)) !important;
  color: var(--color-text-main);
}

.mcr-page-shell[data-mcr-theme="dark"] {
  background:
    radial-gradient(circle at 12% 8%, rgba(var(--color-rgb-primary), 0.13), transparent 30%),
    radial-gradient(circle at 88% 10%, rgba(var(--color-rgb-secondary), 0.11), transparent 26%),
    linear-gradient(180deg, var(--color-bg), #111B30) !important;
}

.mcr-page-shell .mcr-shell__aurora {
  opacity: 0.18;
  background:
    radial-gradient(ellipse at 16% 14%, rgba(var(--color-rgb-primary), 0.14), transparent 44%),
    radial-gradient(ellipse at 82% 18%, rgba(var(--color-rgb-secondary), 0.12), transparent 36%),
    radial-gradient(ellipse at 54% 86%, rgba(var(--color-rgb-success), 0.08), transparent 44%);
}

.mcr-page-shell .mcr-shell__noise {
  opacity: 0;
}

.mcr-page-hero,
.blueprint-preview-bay,
.blueprint-control-bay,
.mcr-history-header,
.mcr-history-card,
.mcr-control,
.preview-card,
.backend-preview-shell,
.backend-preview-empty,
.blueprint-side-panel,
.mcr-page-shell :deep(.mcr-panel),
.mcr-page-shell :deep(.mcr-panel__body),
.mcr-page-shell :deep(.v-card) {
  border-color: var(--color-border) !important;
  background: rgba(var(--color-rgb-surface), 0.94) !important;
  color: var(--color-text-main) !important;
  box-shadow: var(--mcr-page-shadow) !important;
}

.mcr-page-hero,
.blueprint-preview-bay,
.blueprint-control-bay {
  border-radius: 20px;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-hero,
.mcr-page-shell[data-mcr-theme="dark"] .blueprint-preview-bay,
.mcr-page-shell[data-mcr-theme="dark"] .blueprint-control-bay,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-history-header,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-history-card,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-control,
.mcr-page-shell[data-mcr-theme="dark"] .preview-card,
.mcr-page-shell[data-mcr-theme="dark"] .backend-preview-shell,
.mcr-page-shell[data-mcr-theme="dark"] .backend-preview-empty,
.mcr-page-shell[data-mcr-theme="dark"] .blueprint-side-panel,
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-panel),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-panel__body),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.v-card) {
  background: rgba(var(--color-rgb-surface), 0.88) !important;
  border-color: var(--color-border) !important;
  color: var(--color-text-main) !important;
  box-shadow: 0 18px 44px var(--color-shadow) !important;
}

.mcr-page-shell :deep(.mcr-button--primary),
.mcr-page-shell :deep(.mcr-button--active),
.mcr-history-floating-button--primary {
  border-color: var(--mcr-button-border) !important;
  background: var(--mcr-button-white) !important;
  color: var(--color-primary) !important;
  -webkit-text-fill-color: var(--color-primary) !important;
  box-shadow: var(--mcr-button-shadow) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-button--primary),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-button--active),
.mcr-history-floating-actions[data-mcr-theme="dark"] .mcr-history-floating-button--primary {
  color: var(--color-primary) !important;
  -webkit-text-fill-color: var(--color-primary) !important;
}

.mcr-page-shell :deep(.mcr-button--ghost),
.mcr-history-floating-button {
  border-color: var(--mcr-button-border) !important;
  background: var(--mcr-button-white) !important;
  color: var(--mcr-button-muted) !important;
  -webkit-text-fill-color: var(--mcr-button-muted) !important;
  box-shadow: var(--mcr-button-shadow) !important;
}

.mcr-page-shell :deep(.mcr-button--ghost:hover),
.mcr-history-floating-button:hover {
  border-color: rgba(var(--color-rgb-primary), 0.20) !important;
  background: var(--mcr-button-white) !important;
  color: var(--color-primary) !important;
  -webkit-text-fill-color: var(--color-primary) !important;
  box-shadow: var(--mcr-button-shadow-hover) !important;
}

.mcr-page-shell :deep(.mcr-button--danger),
.mcr-history-floating-button--danger {
  border-color: rgba(var(--color-rgb-danger), 0.18) !important;
  background: var(--mcr-button-white) !important;
  color: var(--color-danger) !important;
  -webkit-text-fill-color: var(--color-danger) !important;
  box-shadow: var(--mcr-button-shadow) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-button--danger),
.mcr-history-floating-actions[data-mcr-theme="dark"] .mcr-history-floating-button--danger {
  color: var(--color-danger) !important;
  -webkit-text-fill-color: var(--color-danger) !important;
}

.mcr-page-tabs--hero {
  overflow: visible !important;
  border-color: rgba(0, 122, 255, 0.12) !important;
  background:
    radial-gradient(ellipse at 22% 50%, rgba(0, 122, 255, 0.16), transparent 42%),
    radial-gradient(ellipse at 78% 50%, rgba(0, 122, 255, 0.10), transparent 46%),
    rgba(var(--color-rgb-surface), 0.72) !important;
  box-shadow:
    0 0 24px rgba(0, 122, 255, 0.10),
    0 10px 28px rgba(47, 76, 128, 0.07),
    inset 0 1px 0 rgba(255, 255, 255, 0.72) !important;
}

.mcr-page-tabs--hero :deep(.v-tab),
.mcr-page-tabs--hero :deep(.mcr-tab--active) {
  border: 0 !important;
  background: transparent !important;
  color: var(--color-text-secondary) !important;
  -webkit-text-fill-color: var(--color-text-secondary) !important;
  box-shadow: none !important;
  backdrop-filter: none;
}

.mcr-page-tabs--hero :deep(.mcr-tab--active),
.mcr-page-tabs--hero :deep(.v-tab.v-tab--selected) {
  border: 0 !important;
  background: transparent !important;
  color: #007aff !important;
  -webkit-text-fill-color: #007aff !important;
  text-shadow: 0 0 14px rgba(0, 122, 255, 0.30);
  box-shadow: none !important;
}

.mcr-page-tabs--hero::before {
  display: none !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-tabs--hero {
  border-color: rgba(10, 132, 255, 0.18) !important;
  background:
    radial-gradient(ellipse at 22% 50%, rgba(10, 132, 255, 0.20), transparent 42%),
    radial-gradient(ellipse at 78% 50%, rgba(10, 132, 255, 0.12), transparent 46%),
    rgba(var(--color-rgb-surface), 0.72) !important;
  box-shadow:
    0 0 28px rgba(10, 132, 255, 0.13),
    0 12px 30px rgba(0, 0, 0, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-tabs--hero :deep(.mcr-tab--active),
.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-tabs--hero :deep(.v-tab.v-tab--selected) {
  color: #0a84ff !important;
  -webkit-text-fill-color: #0a84ff !important;
  text-shadow: 0 0 16px rgba(10, 132, 255, 0.38);
}

.mcr-scheme-row--active,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row--active {
  border-color: #007aff !important;
  background: #007aff !important;
  color: #fff !important;
  box-shadow:
    0 12px 28px rgba(0, 122, 255, 0.22),
    0 0 0 1px rgba(0, 122, 255, 0.08) !important;
}

.mcr-scheme-row--active .mcr-scheme-row__body strong,
.mcr-scheme-row--active .mcr-scheme-row__body span,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row--active .mcr-scheme-row__body strong,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row--active .mcr-scheme-row__body span {
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
}

.mcr-page-shell :deep(.mcr-kicker),
.mcr-page-shell :deep(.mcr-rev),
.mcr-page-shell :deep(.mcr-panel__eyebrow),
.blueprint-meta-grid span,
.blueprint-control-label {
  color: var(--color-text-muted) !important;
  -webkit-text-fill-color: var(--color-text-muted) !important;
}

.mcr-page-shell :deep(.mcr-panel__title),
.mcr-title--compact,
.mcr-history-card__title,
.mcr-history-group__heading,
.mcr-scheme-row__body strong,
.blueprint-meta-grid strong,
.info-value,
.source-name {
  color: var(--color-text-main) !important;
  -webkit-text-fill-color: var(--color-text-main) !important;
}

.mcr-page-subtitle,
.mcr-history-card__meta,
.mcr-scheme-row__body span,
.page-title-preview__en,
.info-label,
.source-slot,
.mcr-note,
.mcr-history-selection-count {
  color: var(--color-text-secondary) !important;
  -webkit-text-fill-color: var(--color-text-secondary) !important;
}

.mcr-page-shell :deep(.mcr-rev),
.blueprint-status-strip span,
.mcr-history-group__heading strong {
  border-color: rgba(var(--color-rgb-primary), 0.18) !important;
  background: var(--color-primary-soft) !important;
  color: var(--color-primary) !important;
  -webkit-text-fill-color: var(--color-primary) !important;
}

.mcr-scheme-row {
  border-color: var(--color-border) !important;
  background: var(--color-surface-soft) !important;
  color: var(--color-text-main) !important;
  box-shadow: none !important;
}

.mcr-scheme-row:hover {
  border-color: rgba(var(--color-rgb-primary), 0.42) !important;
  background: var(--color-surface) !important;
  box-shadow: 0 16px 34px var(--color-shadow) !important;
}

.mcr-scheme-row--active {
  border-color: rgba(var(--color-rgb-primary), 0.72) !important;
  background: var(--color-primary-soft) !important;
  box-shadow: 0 16px 34px rgba(var(--color-rgb-primary), 0.16) !important;
}

.mcr-scheme-row--active .mcr-scheme-row__body strong {
  color: var(--color-primary) !important;
  -webkit-text-fill-color: var(--color-primary) !important;
}

.mcr-scheme-row--active .mcr-scheme-row__body span {
  color: var(--color-text-secondary) !important;
  -webkit-text-fill-color: var(--color-text-secondary) !important;
}

.mcr-scheme-row__actions,
.mcr-history-floating-actions,
:global(.mcr-template-action-menu) {
  border-color: var(--color-border) !important;
  background: rgba(var(--color-rgb-surface), 0.94) !important;
  color: var(--color-text-main) !important;
  box-shadow: 0 20px 48px var(--color-shadow) !important;
}

:global(.mcr-template-action-menu[data-mcr-theme="dark"]) {
  border-color: var(--color-border) !important;
  background: rgba(var(--color-rgb-surface), 0.96) !important;
  color: var(--color-text-main) !important;
}

:global(.mcr-template-action-menu .v-list-item),
:global(.mcr-template-action-menu .v-list-item-title),
:global(.mcr-template-action-menu .v-list-item__content),
:global(.mcr-template-action-menu[data-mcr-theme="dark"] .v-list-item),
:global(.mcr-template-action-menu[data-mcr-theme="dark"] .v-list-item-title),
:global(.mcr-template-action-menu[data-mcr-theme="dark"] .v-list-item__content) {
  color: var(--color-text-main) !important;
  -webkit-text-fill-color: var(--color-text-main) !important;
}

:global(.mcr-template-action-menu .v-list-item:hover),
:global(.mcr-template-action-menu[data-mcr-theme="dark"] .v-list-item:hover) {
  background: var(--color-primary-soft) !important;
  color: var(--color-primary) !important;
  -webkit-text-fill-color: var(--color-primary) !important;
}

.blueprint-preview-frame,
.blueprint-meta-grid {
  border-color: var(--color-border) !important;
  background: var(--color-surface) !important;
  box-shadow: 0 14px 34px var(--color-shadow) !important;
}

.blueprint-mode-toggle,
.blueprint-mode-switch-track,
.mcr-control,
.mcr-page-shell :deep(.mcr-blueprint-field__control),
.mcr-page-shell :deep(.mcr-blueprint-select__control),
.mcr-page-shell :deep(.mcr-blueprint-select__multi-option) {
  border-color: var(--color-border) !important;
  background: var(--color-surface) !important;
  color: var(--color-text-main) !important;
  -webkit-text-fill-color: var(--color-text-main) !important;
}

.mcr-page-shell :deep(.mcr-blueprint-field__control:focus),
.mcr-page-shell :deep(.mcr-blueprint-select__control:focus) {
  border-color: rgba(var(--color-rgb-primary), 0.68) !important;
  box-shadow: 0 0 0 4px rgba(var(--color-rgb-primary), 0.14) !important;
}

.mcr-page-shell :deep(.mcr-blueprint-select__multi-option:hover),
.mcr-page-shell :deep(.mcr-blueprint-select__multi-option--active) {
  border-color: rgba(var(--color-rgb-primary), 0.34) !important;
  background: var(--color-primary-soft) !important;
  color: var(--color-primary) !important;
  -webkit-text-fill-color: var(--color-primary) !important;
}

.mcr-page-shell :deep(.mcr-alert),
.mcr-page-shell :deep(.v-alert.v-theme--light.text-info) {
  border-color: rgba(var(--color-rgb-primary), 0.18) !important;
  background: var(--color-primary-soft) !important;
  color: var(--color-text-main) !important;
  -webkit-text-fill-color: var(--color-text-main) !important;
}

@media (max-width: 959px) {
  .mcr-page-hero .mcr-shell__header-grid {
    grid-template-columns: 1fr;
  }

  .blueprint-hero-actions,
  .mcr-page-top-actions {
    align-items: stretch;
    justify-content: flex-start;
    width: 100%;
  }

  .blueprint-control-bay,
  .blueprint-preview-bay {
    border-radius: 18px;
  }

}

@media (max-width: 599px) {
  .mcr-frame__body {
    padding: 12px !important;
  }

  .mcr-page-hero,
  .mcr-history-header {
    padding: 14px;
    border-radius: 0;
  }

  .mcr-title--compact {
    font-size: 1.65rem;
  }

  .blueprint-panel-heading,
  .blueprint-preview-heading-actions,
  .mcr-history-header {
    align-items: flex-start;
  }

  .blueprint-panel-heading {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 8px 10px;
  }

  .blueprint-panel-heading > div:first-child {
    min-width: 0;
  }

  .blueprint-preview-heading-actions {
    display: contents;
  }

  .blueprint-generate-button {
    grid-column: 2;
    grid-row: 1;
    min-width: 0 !important;
    min-height: 36px !important;
    align-self: center;
    padding-inline: 12px !important;
    white-space: nowrap;
  }

  .blueprint-status-strip {
    grid-column: 1 / -1;
    display: flex;
    max-width: 100%;
    gap: 6px;
    overflow-x: auto;
    padding-bottom: 2px;
  }

  .blueprint-status-strip span {
    flex: 0 0 auto;
    padding: 4px 7px;
    font-size: 10px;
  }

  .mcr-history-toolbar {
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .mcr-history-floating-actions {
    width: calc(100vw - 20px);
    gap: 6px;
    padding: 6px;
    border-radius: 18px;
  }

  .mcr-history-selection-count {
    flex: 1 0 100%;
    padding: 0;
    text-align: center;
    font-size: 11px;
  }

  .mcr-history-floating-button {
    flex: 1 1 calc(50% - 6px);
    min-height: 28px;
    padding: 0 8px;
    font-size: 11px;
  }

  .mcr-scheme-row__select {
    grid-template-columns: 1fr;
  }

  .mcr-scheme-row__actions {
    right: 7px;
    bottom: 7px;
  }

  .blueprint-status-strip,
  .mcr-scheme-row__body span {
    display: none;
  }

  .mcr-scheme-row__select {
    grid-template-rows: auto minmax(28px, auto);
  }

  .mcr-scheme-row__body {
    min-height: 28px;
    padding-block: 1px;
  }

  .blueprint-meta-grid {
    grid-template-columns: 1fr;
  }

  .blueprint-meta-grid {
    display: none !important;
  }

  .blueprint-meta-grid > div {
    border-right: 0;
    border-bottom: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.82);
  }
}

@media (max-width: 720px) {
  .blueprint-meta-grid {
    display: none !important;
  }
}

/* Final interaction overrides: sliding tab indicator, selected scheme and fused save control. */
.mcr-page-tabs--hero {
  position: relative;
  isolation: isolate;
  overflow: hidden !important;
  padding: 5px !important;
  border: 1px solid var(--color-border) !important;
  background: var(--color-surface-soft) !important;
  box-shadow: none !important;
}

.mcr-page-tabs--hero::after {
  content: '';
  position: absolute;
  z-index: 0;
  top: 5px;
  bottom: 5px;
  left: 5px;
  width: calc(50% - 5px);
  border-radius: 10px;
  background: #007aff;
  box-shadow: none;
  transform: translateX(0);
  transition: transform 280ms cubic-bezier(0.22, 1, 0.36, 1);
  pointer-events: none;
}

.mcr-page-tabs--hero.mcr-page-tabs--history::after {
  transform: translateX(100%);
}

.mcr-page-tabs--hero :deep(.v-slide-group__container),
.mcr-page-tabs--hero :deep(.v-slide-group__content),
.mcr-page-tabs--hero :deep(.v-tab) {
  position: relative;
  z-index: 2;
}

.mcr-page-tabs--hero :deep(.v-btn__content) {
  position: relative;
  z-index: 3;
}

.mcr-page-tabs--hero :deep(.v-tab),
.mcr-page-tabs--hero :deep(.mcr-tab),
.mcr-page-tabs--hero :deep(.mcr-tab--active),
.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-tabs--hero :deep(.v-tab),
.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-tabs--hero :deep(.mcr-tab--active) {
  border: 0 !important;
  background: transparent !important;
  color: var(--color-text-secondary) !important;
  -webkit-text-fill-color: var(--color-text-secondary) !important;
  text-shadow: none !important;
  box-shadow: none !important;
}

.mcr-page-tabs--hero :deep(.mcr-tab--active),
.mcr-page-tabs--hero :deep(.v-tab.v-tab--selected),
.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-tabs--hero :deep(.mcr-tab--active),
.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-tabs--hero :deep(.v-tab.v-tab--selected) {
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-tabs--hero {
  border-color: var(--color-border) !important;
  background: var(--color-surface-soft) !important;
  box-shadow: none !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-tabs--hero::after {
  background: #0a84ff;
  box-shadow: none;
}

.mcr-page-shell .mcr-scheme-row.mcr-scheme-row--active,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row.mcr-scheme-row--active {
  border-color: #007aff !important;
  background: #007aff !important;
  background-color: #007aff !important;
  color: #fff !important;
  box-shadow:
    0 12px 28px rgba(0, 122, 255, 0.22),
    0 0 0 1px rgba(0, 122, 255, 0.08) !important;
}

.mcr-page-shell .mcr-scheme-row.mcr-scheme-row--active .mcr-scheme-row__select,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row.mcr-scheme-row--active .mcr-scheme-row__select {
  background: transparent !important;
  color: #fff !important;
}

.mcr-page-shell .mcr-scheme-row.mcr-scheme-row--active .mcr-scheme-row__body,
.mcr-page-shell .mcr-scheme-row.mcr-scheme-row--active .mcr-scheme-row__body strong,
.mcr-page-shell .mcr-scheme-row.mcr-scheme-row--active .mcr-scheme-row__body span,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row.mcr-scheme-row--active .mcr-scheme-row__body,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row.mcr-scheme-row--active .mcr-scheme-row__body strong,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-scheme-row.mcr-scheme-row--active .mcr-scheme-row__body span {
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
}

.mcr-page-shell .mcr-editor-split-save {
  display: inline-flex;
  gap: 0 !important;
  overflow: hidden !important;
  border: 1px solid rgba(0, 122, 255, 0.16) !important;
  border-radius: 12px !important;
  background: #fff !important;
  box-shadow:
    0 1px 2px rgba(47, 76, 128, 0.06),
    0 8px 20px rgba(47, 76, 128, 0.09) !important;
}

.mcr-page-shell .mcr-editor-split-save :deep(.v-btn),
.mcr-page-shell .mcr-editor-split-save :deep(.mcr-button),
.mcr-page-shell .mcr-editor-split-save :deep(.mcr-editor-save-main),
.mcr-page-shell .mcr-editor-split-save :deep(.mcr-editor-save-toggle) {
  margin: 0 !important;
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  transform: none !important;
}

.mcr-page-shell .mcr-editor-split-save .mcr-button,
.mcr-page-shell .mcr-editor-split-save .mcr-editor-save-main,
.mcr-page-shell .mcr-editor-split-save .mcr-editor-save-toggle {
  appearance: none;
  margin: 0 !important;
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  transform: none !important;
}

.mcr-page-shell .mcr-editor-split-save :deep(.v-btn__overlay),
.mcr-page-shell .mcr-editor-split-save :deep(.v-btn__underlay) {
  border-radius: 0 !important;
  box-shadow: none !important;
}

.mcr-page-shell .mcr-editor-split-save :deep(.mcr-editor-save-main) {
  padding-inline: 14px 8px !important;
  color: var(--color-text-main) !important;
  -webkit-text-fill-color: var(--color-text-main) !important;
}

.mcr-page-shell .mcr-editor-split-save .mcr-editor-save-main {
  min-height: 38px !important;
  padding: 0 8px 0 14px !important;
  color: var(--color-text-main) !important;
  -webkit-text-fill-color: var(--color-text-main) !important;
}

.mcr-page-shell .mcr-editor-split-save :deep(.mcr-editor-save-toggle) {
  min-width: 58px !important;
  padding-inline: 6px 12px !important;
  color: #007aff !important;
  -webkit-text-fill-color: #007aff !important;
}

.mcr-page-shell .mcr-editor-split-save .mcr-editor-save-toggle {
  flex: 0 0 68px;
  width: 68px !important;
  min-width: 68px !important;
  min-height: 38px !important;
  padding: 0 12px 0 6px !important;
  color: #007aff !important;
  -webkit-text-fill-color: #007aff !important;
}

.mcr-page-shell .mcr-editor-split-save :deep(.v-btn:hover),
.mcr-page-shell .mcr-editor-split-save :deep(.mcr-button:hover) {
  background: rgba(0, 122, 255, 0.055) !important;
  box-shadow: none !important;
}

.mcr-page-shell .mcr-editor-split-save .mcr-button:hover {
  border: 0 !important;
  border-radius: 0 !important;
  background: rgba(0, 122, 255, 0.055) !important;
  box-shadow: none !important;
  transform: none !important;
}

.mcr-page-shell .mcr-editor-split-save :deep(.v-btn:active),
.mcr-page-shell .mcr-editor-split-save :deep(.mcr-button:active) {
  background: rgba(0, 122, 255, 0.09) !important;
  box-shadow: none !important;
}

.mcr-page-shell .mcr-editor-split-save .mcr-button:active {
  border: 0 !important;
  border-radius: 0 !important;
  background: rgba(0, 122, 255, 0.09) !important;
  box-shadow: none !important;
}

.mcr-page-shell .mcr-editor-split-save .mcr-button:disabled {
  background: transparent !important;
  box-shadow: none !important;
  opacity: 0.46;
}

.mcr-page-shell .mcr-editor-save-mode {
  width: 48px;
  min-width: 48px;
  background: rgba(0, 122, 255, 0.08);
  color: #007aff;
}

/* Isolated segmented tabs: only the indicator owns a colored background. */
.mcr-page-tabs-shell {
  position: relative;
  isolation: isolate;
  width: min(320px, 32vw);
  min-width: 254px;
  padding: 5px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: #eef1f5;
}

.mcr-page-tabs-indicator {
  position: absolute;
  z-index: 0;
  top: 5px;
  bottom: 5px;
  left: 5px;
  width: calc((100% - 10px) / 2);
  border-radius: 10px;
  background: #007aff;
  transform: translateX(0);
  transition: transform 280ms cubic-bezier(0.22, 1, 0.36, 1);
  pointer-events: none;
}

.mcr-page-tabs-shell--history .mcr-page-tabs-indicator {
  transform: translateX(100%);
}

.mcr-page-tabs-track {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: stretch;
  width: 100%;
  height: 46px;
  min-width: 0;
  padding: 0 !important;
  overflow: visible !important;
  border: 0 !important;
  border-radius: 10px;
  background: transparent !important;
  box-shadow: none !important;
}

.mcr-page-tabs-track > .mcr-page-tab-button {
  all: unset;
  position: relative;
  z-index: 2;
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  padding: 0 14px;
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  color: #4b5563;
  -webkit-text-fill-color: #4b5563;
  font-family: inherit;
  font-size: 13px;
  font-weight: 750;
  letter-spacing: 0;
  box-shadow: none !important;
  text-shadow: none !important;
  appearance: none;
  cursor: pointer;
}

.mcr-page-tabs-track > .mcr-page-tab-button:disabled {
  cursor: default;
  opacity: 0.48;
}

.mcr-page-tabs-label {
  position: relative;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  background: transparent !important;
  color: currentColor;
  -webkit-text-fill-color: currentColor;
}

.mcr-page-tabs-track > .mcr-page-tab-button--active {
  background: transparent !important;
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
}

.mcr-page-tabs-track > .mcr-page-tab-button[aria-selected="false"],
.mcr-page-tabs-track > .mcr-page-tab-button[aria-selected="false"]:hover,
.mcr-page-tabs-track > .mcr-page-tab-button[aria-selected="false"]:focus,
.mcr-page-tabs-track > .mcr-page-tab-button[aria-selected="false"]:active {
  border-color: transparent !important;
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  color: #4b5563 !important;
  -webkit-text-fill-color: #4b5563 !important;
  box-shadow: none !important;
}

.mcr-page-tabs-track > .mcr-page-tab-button::before,
.mcr-page-tabs-track > .mcr-page-tab-button::after {
  display: none !important;
  content: none !important;
  background: transparent !important;
  box-shadow: none !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-tabs-shell {
  border-color: var(--color-border);
  background: #252f42;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-tabs-indicator {
  background: #0a84ff;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-tabs-track > .mcr-page-tab-button[aria-selected="false"] {
  color: #c7d0e3 !important;
  -webkit-text-fill-color: #c7d0e3 !important;
}

/* Macaron state colors for the static / animated switch. */
.mcr-page-shell .blueprint-mode-thumb,
.mcr-page-shell .blueprint-mode-toggle:not(.blueprint-mode-toggle--animated) .blueprint-mode-thumb {
  border: 1px solid rgba(255, 255, 255, 0.88) !important;
  background: #f6afc1 !important;
  box-shadow:
    0 3px 9px rgba(203, 101, 131, 0.24),
    inset 0 1px 0 rgba(255, 255, 255, 0.72) !important;
  transition:
    transform 340ms cubic-bezier(0.34, 1.42, 0.64, 1),
    background-color 280ms ease,
    border-color 280ms ease,
    box-shadow 280ms ease !important;
}

.mcr-page-shell .blueprint-mode-toggle--animated .blueprint-mode-thumb {
  transform: translateX(24px);
  border-color: rgba(255, 255, 255, 0.88) !important;
  background: #8fd8b5 !important;
  box-shadow:
    0 3px 9px rgba(55, 157, 112, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.72) !important;
}

/* Monochrome rounded-block skeletons for preview and scheme cards. */
.mcr-page-shell .blueprint-skeleton {
  --mcr-skeleton-block: rgba(var(--color-rgb-primary), 0.14);
  border: 0 !important;
  border-radius: 14px;
  background: var(--color-surface-soft) !important;
  box-shadow: none !important;
}

.mcr-page-shell .blueprint-skeleton::before {
  display: none !important;
  content: none !important;
}

.mcr-page-shell .blueprint-skeleton__shape {
  position: absolute;
  display: block;
  border: 0;
  border-radius: 10px;
  background: var(--mcr-skeleton-block);
  box-shadow: none;
  opacity: 0.72;
}

.mcr-page-shell .blueprint-skeleton__shape--visual {
  inset: 10% 48% 10% 6%;
  border-radius: 14px;
}

.mcr-page-shell .blueprint-skeleton__shape--title {
  top: 20%;
  left: 58%;
  width: 31%;
  height: 14%;
}

.mcr-page-shell .blueprint-skeleton__shape--line {
  top: 43%;
  left: 58%;
  width: 36%;
  height: 9%;
}

.mcr-page-shell .blueprint-skeleton__shape--line-short {
  top: 59%;
  left: 58%;
  width: 24%;
  height: 9%;
}

.mcr-page-shell .blueprint-skeleton__shape--chip {
  left: 58%;
  bottom: 12%;
  width: 15%;
  height: 10%;
  border-radius: 999px;
}

.mcr-page-shell .blueprint-skeleton--active .blueprint-skeleton__shape {
  animation: mcr-skeleton-breathe 1.55s ease-in-out infinite alternate;
}

.mcr-page-shell .blueprint-skeleton--active .blueprint-skeleton__shape--title {
  animation-delay: 90ms;
}

.mcr-page-shell .blueprint-skeleton--active .blueprint-skeleton__shape--line {
  animation-delay: 180ms;
}

.mcr-page-shell .blueprint-skeleton--active .blueprint-skeleton__shape--line-short {
  animation-delay: 270ms;
}

.mcr-page-shell .blueprint-skeleton--active .blueprint-skeleton__shape--chip {
  animation-delay: 360ms;
}

.mcr-page-shell .blueprint-skeleton--card .blueprint-skeleton__shape {
  border-radius: 7px;
}

.mcr-page-shell .blueprint-skeleton--card .blueprint-skeleton__shape--visual {
  inset: 12% 50% 12% 7%;
  border-radius: 9px;
}

.mcr-page-shell[data-mcr-theme="dark"] .blueprint-skeleton {
  --mcr-skeleton-block: rgba(var(--color-rgb-primary), 0.18);
  background: var(--color-surface-soft) !important;
}

@keyframes mcr-skeleton-breathe {
  from {
    opacity: 0.52;
  }
  to {
    opacity: 0.92;
  }
}

@media (prefers-reduced-motion: reduce) {
  .mcr-page-shell .blueprint-skeleton--active .blueprint-skeleton__shape {
    animation: none;
    opacity: 0.72;
  }
}

@media (max-width: 959px) {
  .mcr-page-tabs-shell {
    width: 100%;
    min-width: 0;
  }
}

/* Final dark button roles must follow all legacy page button skins above. */
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--apple-primary:not(.mcr-button--danger)) {
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

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--dark-neutral) {
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

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--apple-primary:not(.mcr-button--danger) .v-btn__overlay),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--dark-neutral .v-btn__overlay) {
  opacity: 0 !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--apple-primary:not(.mcr-button--danger) .v-btn__content),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--apple-primary:not(.mcr-button--danger) .v-icon) {
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--dark-neutral .v-btn__content),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-button.mcr-button--dark-neutral .v-icon) {
  color: #d4dbe8 !important;
  -webkit-text-fill-color: #d4dbe8 !important;
}

/* Canvas layer creation controls use the same quiet dark utility treatment. */
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-layer-actions--canvas > .mcr-button:not(.mcr-layer-button)) {
  --v-theme-overlay-multiplier: 0;
  border-color: rgba(230, 236, 245, 0.12) !important;
  background-color: #2a3447 !important;
  background-image: none !important;
  color: #d4dbe8 !important;
  -webkit-text-fill-color: #d4dbe8 !important;
  box-shadow:
    0 6px 16px rgba(0, 0, 0, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-layer-actions--canvas > .mcr-button:not(.mcr-layer-button):hover) {
  border-color: rgba(230, 236, 245, 0.20) !important;
  background-color: #344056 !important;
  color: #f0f3f8 !important;
  -webkit-text-fill-color: #f0f3f8 !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-layer-actions--canvas > .mcr-button:not(.mcr-layer-button) .v-btn__overlay) {
  opacity: 0 !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-layer-actions--canvas > .mcr-button:not(.mcr-layer-button) .v-btn__content),
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-layer-actions--canvas > .mcr-button:not(.mcr-layer-button) .v-icon) {
  color: inherit !important;
  -webkit-text-fill-color: currentColor !important;
}

/* Keep save and AUTO/MANUAL visually fused while giving the control a dark surface. */
.mcr-page-shell[data-mcr-theme="dark"] .mcr-editor-split-save {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: #2a3447 !important;
  box-shadow:
    0 7px 18px rgba(0, 0, 0, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-editor-split-save :deep(.mcr-editor-save-main),
.mcr-page-shell[data-mcr-theme="dark"] .mcr-editor-split-save :deep(.mcr-editor-save-toggle) {
  border: 0 !important;
  background: transparent !important;
  color: #d4dbe8 !important;
  -webkit-text-fill-color: #d4dbe8 !important;
  box-shadow: none !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-editor-split-save :deep(.mcr-editor-save-toggle) {
  border-left: 1px solid rgba(230, 236, 245, 0.10) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-editor-split-save :deep(.mcr-button:hover) {
  background: rgba(255, 255, 255, 0.055) !important;
  color: #f0f3f8 !important;
  -webkit-text-fill-color: #f0f3f8 !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-editor-save-mode {
  background: rgba(255, 255, 255, 0.07) !important;
  color: #d4dbe8 !important;
  -webkit-text-fill-color: #d4dbe8 !important;
}

.mcr-page-shell .blueprint-meta-grid.mcr-render-options {
  display: grid !important;
  grid-template-columns: 1.15fr 1fr 0.78fr !important;
}

.mcr-page-shell .mcr-render-option {
  min-width: 0;
  border-right: 1px solid var(--color-border) !important;
}

.mcr-page-shell .mcr-render-option:last-child {
  border-right: 0 !important;
}

.mcr-page-shell .mcr-render-option span {
  color: var(--color-text-muted) !important;
  -webkit-text-fill-color: var(--color-text-muted) !important;
}

.mcr-page-shell .mcr-render-option select,
.mcr-page-shell .mcr-render-option input {
  background: var(--color-surface) !important;
  border-color: var(--color-border) !important;
  color: var(--color-text-main) !important;
  -webkit-text-fill-color: var(--color-text-main) !important;
}

.mcr-page-shell .mcr-render-option__value {
  background: var(--color-surface-soft) !important;
  border-color: var(--color-border) !important;
  color: var(--color-text-main) !important;
  -webkit-text-fill-color: var(--color-text-main) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-render-option select,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-render-option input {
  background: #222e43 !important;
  border-color: rgba(230, 236, 245, 0.12) !important;
  color: #f4f7fb !important;
  -webkit-text-fill-color: #f4f7fb !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-render-option__value {
  background: #222e43 !important;
  border-color: rgba(230, 236, 245, 0.12) !important;
  color: #f4f7fb !important;
  -webkit-text-fill-color: #f4f7fb !important;
}

.mcr-page-shell .mcr-scheme-row--active .mcr-scheme-row__actions,
.mcr-page-shell .mcr-scheme-row:hover .mcr-scheme-row__actions,
.mcr-page-shell .mcr-scheme-row:focus-within .mcr-scheme-row__actions {
  opacity: 1 !important;
  pointer-events: auto !important;
  transform: translateY(0) !important;
}

/* Scheme cards derive a stable height from the 16:9 preview plus the title row. */
.mcr-scheme-list__scroll {
  grid-auto-rows: max-content !important;
  align-items: start;
}

.mcr-scheme-row {
  height: auto !important;
  min-height: 0 !important;
}

.mcr-scheme-row__select {
  height: auto;
  grid-template-rows: auto 36px !important;
}

.mcr-scheme-row__media {
  width: 100%;
  height: auto;
  aspect-ratio: 16 / 9;
}

/* Remaining history and editor utilities use explicit dark surfaces. */
.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-history-toggle .mcr-history-mode-button) {
  --v-theme-overlay-multiplier: 0;
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: #2a3447 !important;
  color: #d4dbe8 !important;
  -webkit-text-fill-color: #d4dbe8 !important;
  box-shadow: none !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-history-mode-button--active) {
  border-color: #0a84ff !important;
  background: #0a84ff !important;
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-history-card__action--download) {
  border-color: rgba(230, 236, 245, 0.14) !important;
  background: rgba(42, 52, 71, 0.94) !important;
  color: #d4dbe8 !important;
  -webkit-text-fill-color: #d4dbe8 !important;
  box-shadow: 0 7px 18px rgba(0, 0, 0, 0.18) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-history-card__action--danger) {
  border-color: rgba(255, 133, 133, 0.24) !important;
  background: rgba(92, 39, 48, 0.94) !important;
  color: #ffb0b0 !important;
  -webkit-text-fill-color: #ffb0b0 !important;
  box-shadow: 0 7px 18px rgba(0, 0, 0, 0.18) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] :deep(.mcr-layer-button) {
  --v-theme-overlay-multiplier: 0;
  border-color: rgba(110, 162, 255, 0.28) !important;
  background: #222e43 !important;
  background-image: none !important;
  color: #b9c8df !important;
  -webkit-text-fill-color: #b9c8df !important;
  box-shadow:
    0 7px 18px rgba(0, 0, 0, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

.mcr-history-floating-actions[data-mcr-theme="dark"] {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(23, 32, 51, 0.96) !important;
  color: #d4dbe8 !important;
}

.mcr-history-floating-actions[data-mcr-theme="dark"] .mcr-history-floating-button {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: #2a3447 !important;
  color: #d4dbe8 !important;
  -webkit-text-fill-color: #d4dbe8 !important;
  box-shadow: none !important;
}

.mcr-history-floating-actions[data-mcr-theme="dark"] .mcr-history-floating-button--primary {
  border-color: #0a84ff !important;
  background: #0a84ff !important;
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
}

.mcr-history-floating-actions[data-mcr-theme="dark"] .mcr-history-floating-button--danger {
  border-color: rgba(255, 133, 133, 0.24) !important;
  background: #5c2730 !important;
  color: #ffb0b0 !important;
  -webkit-text-fill-color: #ffb0b0 !important;
}

@media (max-width: 959px) {
  .mcr-page-shell .blueprint-meta-grid.mcr-render-options {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }

  .mcr-page-shell .mcr-render-option:nth-child(2n) {
    border-right: 0 !important;
  }

  .mcr-scheme-list__scroll {
    max-height: 520px !important;
    overflow-y: auto !important;
    scrollbar-gutter: stable;
  }
}

@media (max-width: 599px) {
  .mcr-page-shell .blueprint-meta-grid.mcr-render-options {
    grid-template-columns: 1fr !important;
  }

  .mcr-page-shell .mcr-render-option {
    border-right: 0 !important;
    border-bottom: 1px solid var(--color-border) !important;
  }

  .mcr-page-shell .mcr-render-option:last-child {
    border-bottom: 0 !important;
  }

  .mcr-scheme-list__scroll {
    max-height: 420px !important;
  }

  .mcr-scheme-row {
    height: auto !important;
    min-height: 0 !important;
  }

  .mcr-scheme-row__select {
    grid-template-rows: auto 28px !important;
  }
}

.mcr-page-shell .mcr-page-top-actions {
  display: inline-flex;
  width: auto;
  min-width: 0;
  padding: 4px;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.78);
  border-radius: 16px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.78);
  box-shadow: 0 12px 24px rgba(var(--mcr-rgb-shadow), 0.08);
}

.mcr-page-shell {
  --yahaha-blue: #1677ff;
  --yahaha-blue-soft: #eef5ff;
  --yahaha-border: #dfe8f6;
  --yahaha-text: #121a2f;
  --yahaha-muted: #5b6b88;
  --yahaha-card: rgba(255, 255, 255, 0.92);
  --yahaha-radius-lg: 22px;
  --yahaha-radius-md: 18px;
}

.mcr-page-shell .mcr-page-hero {
  position: relative;
}

.mcr-page-shell .mcr-kicker-row {
  padding-right: 104px;
}

.mcr-page-shell .yh-top-actions {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 30;
  display: flex;
  align-items: center;
  gap: 8px;
}

.mcr-page-shell .mcr-page-top-actions.yh-top-actions {
  width: auto;
  min-width: 0;
  padding: 0;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

.mcr-page-shell .yh-icon-btn {
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

.mcr-page-shell .yh-icon-btn:active {
  transform: scale(0.96);
  background: var(--yahaha-blue-soft) !important;
}

.mcr-page-shell .yh-icon-btn:hover {
  background: var(--yahaha-blue-soft) !important;
  color: var(--yahaha-blue) !important;
  -webkit-text-fill-color: var(--yahaha-blue) !important;
}

.mcr-page-shell .yh-icon-btn :deep(.v-btn__overlay),
.mcr-page-shell .yh-icon-btn :deep(.v-btn__underlay) {
  opacity: 0 !important;
}

.mcr-page-shell .yh-segment,
.mcr-page-shell .mcr-page-tabs-shell {
  display: inline-flex;
  gap: 6px;
  padding: 6px;
  border: 1px solid rgba(223, 232, 246, 0.82) !important;
  border-radius: var(--yahaha-radius-lg) !important;
  background: #eef2f7 !important;
  box-shadow: 0 4px 12px rgba(28, 77, 160, 0.08) !important;
}

.mcr-page-shell .yh-btn,
.mcr-page-shell .mcr-page-tabs-track > .mcr-page-tab-button {
  --v-theme-overlay-multiplier: 0;
  min-height: 42px !important;
  height: 42px;
  border-radius: var(--yahaha-radius-md) !important;
  font-weight: 700 !important;
  letter-spacing: 0.02em;
}

.mcr-page-shell .yh-btn-secondary {
  border: 1px solid var(--yahaha-border) !important;
  background: rgba(255, 255, 255, 0.92) !important;
  background-image: none !important;
  color: var(--yahaha-muted) !important;
  -webkit-text-fill-color: var(--yahaha-muted) !important;
  box-shadow: 0 4px 12px rgba(28, 77, 160, 0.08) !important;
}

.mcr-page-shell .yh-btn-secondary:hover {
  background: var(--yahaha-blue-soft) !important;
  color: var(--yahaha-blue) !important;
  -webkit-text-fill-color: var(--yahaha-blue) !important;
}

.mcr-page-shell .mcr-page-tabs-shell {
  border-radius: var(--yahaha-radius-lg) !important;
}

.mcr-page-shell .mcr-page-tabs-indicator {
  top: 6px;
  bottom: 6px;
  left: 6px;
  width: calc((100% - 12px) / 2);
  border-radius: 17px;
  background: var(--yahaha-blue);
}

.mcr-page-shell .mcr-page-tabs-track {
  height: 42px;
}

.mcr-page-shell[data-mcr-theme="dark"] .yh-segment,
.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-tabs-shell {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(15, 23, 42, 0.50) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .yh-btn-secondary {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(30, 42, 66, 0.72) !important;
  color: #c7d0e3 !important;
  -webkit-text-fill-color: #c7d0e3 !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .yh-icon-btn {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(30, 42, 66, 0.72) !important;
  color: #c7d0e3 !important;
  -webkit-text-fill-color: #c7d0e3 !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .yh-icon-btn:hover {
  background: rgba(110, 162, 255, 0.14) !important;
  color: #8fc2ff !important;
  -webkit-text-fill-color: #8fc2ff !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .yh-btn-secondary:hover {
  background: rgba(110, 162, 255, 0.14) !important;
  color: #8fc2ff !important;
  -webkit-text-fill-color: #8fc2ff !important;
}

.mcr-page-shell .mcr-page-top-actions :deep(.mcr-button) {
  --v-theme-overlay-multiplier: 0;
  min-height: 34px !important;
  padding-inline: 12px !important;
  border: 0 !important;
  border-radius: 12px !important;
  background: transparent !important;
  background-image: none !important;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.82) !important;
  -webkit-text-fill-color: rgba(var(--mcr-rgb-on-surface-variant), 0.82) !important;
  box-shadow: none !important;
}

.mcr-page-shell .mcr-page-top-actions :deep(.mcr-button:hover) {
  background: rgba(var(--mcr-rgb-primary), 0.08) !important;
  color: var(--mcr-blueprint-cyan) !important;
  -webkit-text-fill-color: var(--mcr-blueprint-cyan) !important;
}

.mcr-page-shell .mcr-page-top-actions :deep(.mcr-button .v-btn__overlay),
.mcr-page-shell .mcr-page-top-actions :deep(.mcr-button .v-btn__underlay) {
  opacity: 0 !important;
}

.mcr-page-shell .blueprint-hero-actions {
  min-width: min(100%, 286px);
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-top-actions {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(23, 32, 51, 0.88) !important;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.20) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-top-actions :deep(.mcr-button) {
  color: #c7d0e3 !important;
  -webkit-text-fill-color: #c7d0e3 !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-top-actions :deep(.mcr-button:hover) {
  background: rgba(110, 162, 255, 0.14) !important;
  color: #8fc2ff !important;
  -webkit-text-fill-color: #8fc2ff !important;
}

@media (max-width: 959px) {
  .mcr-page-shell .mcr-kicker-row {
    padding-right: 104px;
  }

  .mcr-page-shell .blueprint-hero-actions {
    align-items: flex-end;
  }

  .mcr-page-shell .mcr-page-top-actions {
    align-self: flex-end;
    width: auto;
    max-width: 100%;
    justify-content: flex-end;
  }

  .mcr-page-shell .mcr-page-top-actions :deep(.mcr-button) {
    flex: 0 0 auto;
  }

  .mcr-page-shell .mcr-page-tabs-shell {
    width: 100%;
  }
}

.mcr-page-shell .mcr-page-hero .mcr-shell__header-grid {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) auto !important;
  grid-template-areas:
    "brand actions"
    "tabs tabs";
  gap: 16px 18px !important;
  align-items: start !important;
}

.mcr-page-shell .mcr-page-hero .mcr-shell__copy {
  grid-area: brand;
  min-width: 0;
}

.mcr-page-shell .blueprint-hero-actions {
  grid-area: actions;
  display: contents !important;
  min-width: 0 !important;
}

.mcr-page-shell .mcr-page-top-actions.yh-top-actions {
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

.mcr-page-shell .mcr-page-tabs-shell {
  grid-area: tabs;
  justify-self: stretch;
  width: min(460px, 100%) !important;
  margin-top: 0 !important;
}

.mcr-page-shell .mcr-kicker-row {
  padding-right: 0 !important;
}

.mcr-page-shell .yh-run-btn {
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

.mcr-page-shell .yh-run-btn:hover {
  background: #2f86ff;
  box-shadow: 0 10px 22px rgba(22, 119, 255, 0.26);
}

.mcr-page-shell .yh-run-btn:active {
  transform: scale(0.96);
}

.mcr-page-shell .yh-run-btn:disabled {
  cursor: default;
  opacity: 0.68;
  transform: none;
}

.mcr-page-shell .yh-run-btn.is-running {
  width: 148px;
  min-width: 148px;
  border-radius: 18px;
}

.mcr-page-shell .yh-run-progress {
  position: absolute;
  inset: 0 auto 0 0;
  width: var(--yh-run-progress);
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.24), rgba(255, 255, 255, 0.08));
  transition: width 0.25s ease;
}

.mcr-page-shell .yh-run-content {
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

.mcr-page-shell .yh-run-text,
.mcr-page-shell .yh-run-percent {
  font-size: 14px;
}

.mcr-page-shell .mcr-page-top-actions :deep(.yh-icon-btn.mcr-button),
.mcr-page-shell .yh-icon-btn {
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

.mcr-page-shell .mcr-page-top-actions :deep(.yh-icon-btn.mcr-button:hover),
.mcr-page-shell .yh-icon-btn:hover {
  border-color: #c9dcff !important;
  background: var(--yahaha-blue-soft) !important;
  color: var(--yahaha-blue) !important;
  -webkit-text-fill-color: var(--yahaha-blue) !important;
}

.mcr-page-shell[data-mcr-theme="dark"] .mcr-page-top-actions :deep(.yh-icon-btn.mcr-button),
.mcr-page-shell[data-mcr-theme="dark"] .yh-icon-btn {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(30, 42, 66, 0.72) !important;
  color: #c7d0e3 !important;
  -webkit-text-fill-color: #c7d0e3 !important;
}

@media (min-width: 768px) {
  .mcr-page-shell .yh-run-btn,
  .mcr-page-shell .mcr-page-top-actions :deep(.yh-icon-btn.mcr-button),
  .mcr-page-shell .yh-icon-btn {
    width: 46px !important;
    height: 46px !important;
    min-width: 46px !important;
    border-radius: 17px !important;
  }

  .mcr-page-shell .yh-run-btn.is-running {
    width: 154px !important;
    min-width: 154px !important;
    border-radius: 18px !important;
  }
}

@media (max-width: 600px) {
  .mcr-page-shell .mcr-page-hero .mcr-shell__header-grid {
    grid-template-columns: minmax(0, 1fr) auto !important;
    gap: 12px 10px !important;
  }

  .mcr-page-shell .yh-run-btn,
  .mcr-page-shell .mcr-page-top-actions :deep(.yh-icon-btn.mcr-button),
  .mcr-page-shell .yh-icon-btn {
    width: 40px !important;
    height: 40px !important;
    min-width: 40px !important;
    border-radius: 15px !important;
  }

  .mcr-page-shell .yh-run-btn.is-running {
    width: 128px !important;
    min-width: 128px !important;
  }

  .mcr-page-shell .mcr-page-top-actions.yh-top-actions {
    gap: 6px;
  }

  .mcr-page-shell .yh-run-text,
  .mcr-page-shell .yh-run-percent {
    font-size: 13px;
  }
}

.mcr-page-shell .yh-brand-row {
  align-items: center;
  gap: 14px;
}

.mcr-page-shell .yh-brand-title {
  position: relative;
  min-height: 86px;
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
  margin: 0;
}

.mcr-page-shell .yh-brand-en-big {
  position: relative;
  z-index: 0;
  display: block;
  color: rgba(83, 125, 198, 0.12);
  font-size: clamp(34px, 4vw, 64px);
  font-weight: 950;
  letter-spacing: -0.04em;
  line-height: 0.95;
  pointer-events: none;
  user-select: none;
  white-space: nowrap;
}

.mcr-page-shell .yh-brand-zh-overlap {
  position: relative;
  z-index: 1;
  display: block;
  margin-top: -18px;
  margin-left: 8px;
  color: var(--yahaha-text);
  font-size: clamp(28px, 3vw, 48px);
  font-weight: 900;
  letter-spacing: -0.04em;
  line-height: 1.05;
}

.mcr-page-shell[data-mcr-theme="dark"] .yh-brand-en-big {
  color: rgba(110, 162, 255, 0.13);
}

.mcr-page-shell[data-mcr-theme="dark"] .yh-brand-zh-overlap {
  color: #f4f7fb;
}

.mcr-page-shell .mcr-logo-slot.yh-avatar-wrap,
.mcr-page-shell .mcr-donation-avatar.yh-avatar-wrap {
  position: relative;
}

.mcr-page-shell .yh-avatar {
  display: inline-grid;
  width: 100%;
  height: 100%;
  place-items: center;
  border-radius: inherit;
  overflow: hidden;
}

.mcr-page-shell .yh-avatar__image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.mcr-page-shell .yh-avatar-crown {
  position: absolute;
  top: -12px;
  left: 5px;
  z-index: 2;
  color: #f5b800;
  filter: drop-shadow(0 3px 5px rgba(143, 99, 0, 0.25));
  cursor: pointer;
  pointer-events: auto;
  transform: rotate(-14deg);
}

.mcr-page-shell .mcr-page-tabs-shell {
  width: min(620px, calc(100% - clamp(180px, 28vw, 520px))) !important;
  max-width: 620px !important;
  margin-left: clamp(180px, 28vw, 520px) !important;
}

.mcr-donation-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px 14px;
  width: 100%;
  max-width: 386px;
}

.mcr-donation-stat-card {
  display: grid;
  min-height: 120px;
  align-content: start;
  gap: 6px;
  padding: 17px 18px;
  border: 1px solid rgba(230, 226, 222, 0.8);
  border-radius: 10px;
  background: #f7f3f1;
  text-align: left;
}

.mcr-donation-stat-card__top {
  display: flex;
  min-height: 24px;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 2px;
}

.mcr-donation-stat-card__top small {
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 850;
  letter-spacing: 0.06em;
  line-height: 1;
  text-transform: uppercase;
}

.mcr-donation-stat-card strong {
  color: #1777ff;
  font-size: 34px;
  font-weight: 900;
  letter-spacing: -0.02em;
  line-height: 0.95;
}

.mcr-donation-stat-card > span:not(.mcr-donation-stat-icon) {
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 800;
  line-height: 1.2;
}

.mcr-donation-stat-icon {
  display: inline-grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border-radius: 9px;
}

.mcr-donation-stat-icon--static {
  background: rgba(54, 211, 153, 0.16);
  color: #19a96f;
}

.mcr-donation-stat-icon--dynamic {
  background: rgba(23, 119, 255, 0.13);
  color: #1777ff;
}

.mcr-donation-stat-icon--history {
  background: rgba(255, 209, 102, 0.24);
  color: #c28a11;
}

.mcr-donation-stat-icon--run {
  background: rgba(20, 128, 86, 0.14);
  color: #0f7b52;
}

.mcr-donation-live-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #34c759;
  box-shadow: 0 0 0 4px rgba(52, 199, 89, 0.12);
}

.mcr-donation-card--dark {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: #172033 !important;
  color: #f4f7fb !important;
  box-shadow: 0 24px 58px rgba(0, 0, 0, 0.34) !important;
}

.mcr-donation-card--dark .mcr-donation-title {
  color: #f4f7fb;
}

.mcr-donation-card--dark .mcr-donation-subtitle,
.mcr-donation-card--dark .mcr-donation-message,
.mcr-donation-card--dark .mcr-donation-footnote {
  color: #8794ad;
}

.mcr-donation-card--dark .mcr-donation-heart {
  border-color: rgba(255, 133, 166, 0.24);
  background:
    radial-gradient(circle at 34% 24%, rgba(255, 255, 255, 0.14), transparent 34%),
    linear-gradient(135deg, rgba(255, 133, 166, 0.22), rgba(255, 111, 156, 0.12));
  color: #ff9bb9;
  box-shadow:
    0 14px 28px rgba(255, 111, 156, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.mcr-donation-card--dark .mcr-donation-qr {
  border-color: rgba(230, 236, 245, 0.12);
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.06), transparent 54%),
    rgba(30, 42, 66, 0.78);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 10px 26px rgba(0, 0, 0, 0.18);
}

.mcr-donation-card--dark .mcr-donation-qr__image {
  background: #f8fafc;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.26);
}

.mcr-donation-card--dark .mcr-donation-profile__avatar {
  border-color: rgba(255, 217, 120, 0.22);
  background:
    radial-gradient(circle at 35% 25%, rgba(255, 255, 255, 0.12), transparent 38%),
    linear-gradient(135deg, rgba(255, 217, 120, 0.16), rgba(255, 209, 102, 0.08));
}

.mcr-donation-card--dark .mcr-donation-profile__crown {
  background: rgba(255, 247, 215, 0.14);
  color: #ffd978;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.22);
}

.mcr-donation-card--dark .mcr-donation-stat-card {
  border-color: rgba(230, 236, 245, 0.1);
  background: rgba(244, 247, 251, 0.07);
}

.mcr-donation-card--dark .mcr-donation-stat-card > span:not(.mcr-donation-stat-icon) {
  color: #c7d0e3;
}

.mcr-donation-card--dark .mcr-donation-stat-card strong {
  color: #6ea2ff;
}

.mcr-donation-card--dark .mcr-donation-stat-card__top small {
  color: #8794ad;
}

.mcr-donation-card--dark .mcr-donation-card__actions .mcr-donation-support-confirm,
.mcr-donation-card--dark .mcr-donation-card__actions .mcr-donation-soft-action,
.mcr-donation-card--dark .mcr-donation-card__actions .mcr-donation-continue-support {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(244, 247, 251, 0.08) !important;
  color: #c7d0e3 !important;
}

.mcr-donation-card--dark .mcr-donation-card__actions .mcr-button--dark-neutral {
  border-color: rgba(230, 236, 245, 0.12) !important;
  background: rgba(244, 247, 251, 0.08) !important;
  color: #c7d0e3 !important;
}

@media (max-width: 768px) {
  .mcr-donation-card__body {
    padding: 24px 18px 20px !important;
  }

  .mcr-donation-title {
    font-size: 23px;
  }

  .mcr-donation-qr {
    max-width: 100%;
    min-height: 238px;
  }

  .mcr-donation-card__actions {
    gap: 8px;
  }

  .mcr-donation-card__actions .v-btn {
    width: calc(50% - 4px);
    min-width: 0 !important;
    padding-inline: 10px !important;
  }

  .mcr-donation-stats {
    gap: 8px;
  }

  .mcr-donation-stat-card {
    min-height: 66px;
    padding: 12px;
  }

  .mcr-donation-stat-card strong {
    font-size: 28px;
  }

  .mcr-page-shell .mcr-page-tabs-shell {
    width: 100% !important;
    max-width: none !important;
    margin-left: 0 !important;
  }
}

.mcr-time-machine-timeline { position: fixed; top: 50%; right: 18px; z-index: 26; display: grid; gap: 6px; max-height: 68vh; padding: 10px 0; overflow-y: auto; border: 0; background: transparent; box-shadow: none; transform: translateY(-50%); }
.mcr-time-machine-node { position: relative; min-height: 30px; display: flex; align-items: center; justify-content: flex-end; gap: 8px; padding: 0; border: 0; background: transparent; color: var(--color-text-muted); font: inherit; font-size: 11px; cursor: pointer; }
.mcr-time-machine-node i { width: 6px; height: 6px; border-radius: 50%; background: currentColor; transition: transform 180ms ease, background-color 180ms ease; }
.mcr-time-machine-node.is-active { color: var(--color-primary); font-weight: 800; }
.mcr-time-machine-node.is-active i { transform: scale(1.55); }
.mcr-time-machine-restore { padding: 7px 10px; border: 1px solid var(--color-border); border-radius: 10px; background: var(--color-surface); color: var(--color-primary); box-shadow: 0 6px 16px var(--color-shadow); }
.mcr-history-group--time-machine { scroll-margin-top: 110px; margin-bottom: -18px; opacity: var(--mcr-time-opacity, .82); transform: translateY(var(--mcr-time-shift, 0)) scale(var(--mcr-time-scale, .97)); transform-origin: center; transition: opacity 190ms ease, transform 190ms ease, filter 190ms ease; }
.mcr-history-group--time-machine.is-active { opacity: 1; transform: translateY(0) scale(1); filter: drop-shadow(0 14px 22px color-mix(in srgb, var(--color-shadow) 70%, transparent)); }
.mcr-history-groups:has(.mcr-history-group--time-machine) { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 760px) minmax(96px, 13vw); }
.mcr-history-group--time-machine { grid-column: 2; width: 100%; }
.mcr-time-machine-stack { position: relative; width: min(760px, 100%); height: 250px; display: block; margin: 0 auto; padding: 0; border: 0; background: transparent; cursor: pointer; transform: translateY(0); transition: transform 220ms ease, filter 220ms ease; }
.mcr-time-machine-stack:hover { transform: translateY(-3px); filter: drop-shadow(0 12px 18px var(--color-shadow)); }
.mcr-time-machine-stack__cover { position: absolute; top: 0; left: var(--mcr-stack-x); z-index: var(--mcr-stack-z); width: min(420px, 68vw); aspect-ratio: 16 / 9; overflow: hidden; border: 1px solid var(--color-border); border-radius: 16px; background: var(--color-surface); box-shadow: 0 8px 20px var(--color-shadow); transform: translateY(var(--mcr-stack-y)) rotate(var(--mcr-stack-r)); transition: left 220ms ease, transform 220ms ease, box-shadow 220ms ease; }
.mcr-time-machine-stack:hover .mcr-time-machine-stack__cover { left: var(--mcr-stack-hover-x); transform: translateY(var(--mcr-stack-y)) rotate(calc(var(--mcr-stack-r) * .55)); }
.mcr-time-machine-stack__cover img { width: 100%; height: 100%; display: block; object-fit: cover; }
.mcr-time-machine-stack__cover > span { position: absolute; left: 12px; bottom: 10px; max-width: calc(100% - 24px); padding: 5px 8px; overflow: hidden; border-radius: 7px; background: rgba(10,16,24,.68); color: white; font-size: 12px; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.mcr-time-machine-stack__more { position: absolute; z-index: 20; top: 96px; right: 8px; padding: 8px 10px; border-radius: 999px; background: var(--color-primary); color: white; font-weight: 800; box-shadow: 0 6px 16px var(--color-shadow); }
.mcr-history-restore-confirm { padding: 24px; border: 1px solid var(--color-border); border-radius: 20px !important; background: var(--color-surface) !important; color: var(--color-text-main) !important; }
.mcr-history-restore-confirm h3 { margin: 0 0 12px; font-size: 24px; }.mcr-history-restore-confirm p { margin: 8px 0; color: var(--color-text-secondary); line-height: 1.65; }.mcr-history-restore-confirm footer { display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px; }
.mcr-history-snapshot { max-height: min(82vh, 900px); overflow: hidden; border: 1px solid color-mix(in srgb, var(--color-border) 76%, transparent); border-radius: 22px !important; background: color-mix(in srgb, var(--color-surface) 84%, transparent) !important; color: var(--color-text-main) !important; box-shadow: 0 24px 72px var(--color-shadow); backdrop-filter: blur(24px) saturate(140%); }
.mcr-history-snapshot__header { display: flex; align-items: flex-start; justify-content: space-between; padding: 22px 24px 14px; border-bottom: 1px solid var(--color-border); }
.mcr-history-snapshot__header span { color: var(--color-primary); font-size: 11px; font-weight: 800; text-transform: uppercase; }
.mcr-history-snapshot__header h3 { margin: 2px 0 0; font-size: 26px; }
.mcr-history-snapshot__header p { margin: 3px 0 0; color: var(--color-text-muted); }
.mcr-history-snapshot__grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; max-height: 58vh; padding: 18px 24px; overflow: auto; }
.mcr-history-snapshot__item { display: grid; grid-template-columns: 1fr auto; gap: 10px; padding: 10px; border: 1px solid var(--color-border); border-radius: 14px; background: var(--color-surface-soft); }
.mcr-history-snapshot__item img { grid-column: 1 / -1; width: 100%; aspect-ratio: 16 / 9; border-radius: 10px; object-fit: cover; }
.mcr-history-snapshot__item div { min-width: 0; display: grid; }
.mcr-history-snapshot__item strong, .mcr-history-snapshot__item span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mcr-history-snapshot__item span, .mcr-history-snapshot__item small { color: var(--color-text-muted); }
.mcr-history-snapshot__check { width: 30px; height: 30px; display: grid; place-items: center; align-self: start; border: 1px solid var(--color-border); border-radius: 9px; color: var(--color-text-muted); background: transparent; }.mcr-history-snapshot__check.is-active { color: white; background: var(--color-primary); border-color: var(--color-primary); }
.mcr-history-snapshot__footer { display: flex; align-items: center; justify-content: flex-end; gap: 8px; padding: 14px 24px 20px; border-top: 1px solid var(--color-border); }.mcr-history-snapshot__footer > span { margin-right: auto; color: var(--color-text-muted); font-size: 13px; }
@media (max-width: 900px) { .mcr-history-snapshot__grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 768px) { .mcr-history-groups:has(.mcr-history-group--time-machine) { display: block; } .mcr-time-machine-timeline { right: 4px; } .mcr-time-machine-node > span:last-child { display: none; } .mcr-time-machine-restore { position: fixed; right: 30px; bottom: 24px; } .mcr-time-machine-stack { width: calc(100% - 24px); height: 190px; } .mcr-time-machine-stack__cover { width: min(310px, 76vw); border-radius: 13px; } .mcr-history-snapshot__grid { grid-template-columns: 1fr 1fr; gap: 8px; padding: 12px; } .mcr-history-snapshot__item { grid-template-columns: 1fr; } }
@media (max-width: 420px) { .mcr-history-snapshot__grid { grid-template-columns: 1fr; } }
@media (prefers-reduced-motion: reduce) { .mcr-history-group--time-machine, .mcr-time-machine-stack, .mcr-time-machine-stack__cover { transition: none; transform: none; } }

@media (max-width: 600px) {
  .mcr-page-shell .yh-brand-title {
    min-height: 70px;
  }

  .mcr-page-shell .yh-brand-en-big {
    font-size: 34px;
    white-space: normal;
  }

  .mcr-page-shell .yh-brand-zh-overlap {
    margin-top: -10px;
    font-size: 30px;
  }

  .mcr-donation-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 360px) {
  .mcr-donation-stats {
    grid-template-columns: 1fr;
  }

  .mcr-donation-card__actions .v-btn {
    width: 100%;
  }
}

.mcr-page-shell .mcr-page-hero .mcr-shell__header-grid {
  grid-template-areas:
    "brand actions"
    "chips chips"
    "tabs tabs" !important;
}

.mcr-page-shell .yh-brand-row > .mcr-logo-slot {
  width: 78px;
  height: 78px;
  border-radius: 24px;
}

.mcr-page-shell .yh-brand-row > .mcr-logo-slot .v-icon {
  font-size: 34px !important;
}

.mcr-page-shell .yh-avatar-toolbar {
  display: none !important;
}

.mcr-page-shell .yh-brand-zh-overlap {
  color: #1c2740;
  font-weight: 900;
}

.mcr-page-shell .yh-brand-en-big {
  color: rgba(90, 120, 180, 0.18);
}

.mcr-page-shell .yh-preview-chips {
  grid-area: chips;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  min-width: 0;
  margin-top: 2px;
}

.mcr-page-shell .yh-preview-chips > span {
  display: inline-flex;
  min-height: 28px;
  align-items: center;
  padding: 6px 10px;
  border: 1px solid rgba(223, 232, 246, 0.86);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  color: var(--yahaha-muted);
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
  box-shadow: 0 4px 12px rgba(28, 77, 160, 0.06);
}

.mcr-page-shell .yh-preview-chips > span:first-child {
  border-color: rgba(var(--mcr-rgb-success), 0.3);
  background: rgba(var(--mcr-rgb-success), 0.12);
  color: var(--mcr-color-success);
}

.mcr-page-shell .yh-preview-chips > span:first-child.is-disabled {
  border-color: var(--color-border);
  background: var(--color-surface-soft);
  color: var(--color-text-muted);
}

.mcr-page-shell .mcr-page-tabs-shell {
  justify-self: end !important;
  width: min(620px, 100%) !important;
  max-width: 620px !important;
  margin-left: auto !important;
}

.mcr-page-shell .mcr-render-option__hint {
  display: block;
  margin-top: 4px;
  color: var(--color-text-muted);
  font-size: 11px;
  font-style: normal;
  font-weight: 750;
  line-height: 1.25;
}

.mcr-page-shell .mcr-render-option select:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.mcr-page-shell[data-mcr-theme="dark"] .yh-preview-chips > span {
  border-color: rgba(230, 236, 245, 0.12);
  background: rgba(30, 42, 66, 0.72);
  color: #c7d0e3;
}

@media (max-width: 768px) {
  .mcr-page-shell .mcr-page-tabs-shell {
    justify-self: center !important;
    width: calc(100% - 8px) !important;
    max-width: none !important;
    margin-inline: auto !important;
  }
}

@media (max-width: 600px) {
  .mcr-page-shell .mcr-page-hero .mcr-shell__header-grid {
    grid-template-areas:
      "brand actions"
      "chips chips"
      "tabs tabs" !important;
  }

  .mcr-page-shell .yh-brand-row > .mcr-logo-slot {
    display: none !important;
  }

  .mcr-page-shell .yh-avatar-toolbar {
    display: inline-grid !important;
    width: 40px !important;
    height: 40px !important;
    min-width: 40px !important;
    border-radius: 15px !important;
  }

  .mcr-page-shell .yh-avatar-toolbar .yh-avatar-crown {
    top: -8px;
    left: 3px;
  }

  .mcr-page-shell .yh-preview-chips {
    gap: 6px;
  }

  .mcr-page-shell .yh-preview-chips > span {
    min-height: 26px;
    padding: 5px 8px;
    font-size: 11px;
  }
}

.mcr-page-shell .mcr-page-hero {
  min-height: 0 !important;
  margin-bottom: 14px !important;
  padding: 20px 28px 22px !important;
}

.mcr-page-shell .mcr-page-hero .mcr-shell__header-grid {
  row-gap: 10px !important;
  column-gap: 18px !important;
  align-items: start !important;
}

.mcr-page-shell .yh-brand-row {
  align-items: center !important;
  gap: 16px !important;
}

.mcr-page-shell .yh-brand-row > .mcr-logo-slot {
  width: 76px !important;
  height: 76px !important;
  border-radius: 24px !important;
}

.mcr-page-shell .yh-brand-title {
  min-height: 76px !important;
  justify-content: center !important;
}

.mcr-page-shell .yh-brand-en-big {
  font-size: clamp(42px, 4vw, 66px) !important;
  line-height: 0.9 !important;
  color: rgba(90, 120, 180, 0.16) !important;
}

.mcr-page-shell .yh-brand-zh-overlap {
  margin-top: -20px !important;
  margin-left: 10px !important;
  font-size: clamp(32px, 3vw, 50px) !important;
  line-height: 0.95 !important;
}

.mcr-page-shell .yh-preview-chips {
  gap: 7px !important;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
}

.mcr-page-shell .yh-preview-chips > span {
  min-height: 26px !important;
  padding: 5px 9px !important;
  font-size: 11px !important;
}

.mcr-page-shell .mcr-page-tabs-shell {
  width: min(560px, 100%) !important;
  max-width: 560px !important;
  margin-top: 4px !important;
}

.mcr-page-shell .mcr-page-top-actions.yh-top-actions {
  align-self: start !important;
}

@media (max-width: 768px) {
  .mcr-page-shell .mcr-page-hero {
    padding: 14px 14px 16px !important;
  }

  .mcr-page-shell .mcr-page-hero .mcr-shell__header-grid {
    row-gap: 8px !important;
    column-gap: 10px !important;
  }

  .mcr-page-shell .yh-brand-title {
    min-height: 58px !important;
  }

  .mcr-page-shell .yh-brand-en-big {
    font-size: 34px !important;
    line-height: 0.95 !important;
  }

  .mcr-page-shell .yh-brand-zh-overlap {
    margin-top: -10px !important;
    margin-left: 6px !important;
    font-size: 28px !important;
    line-height: 1 !important;
  }

  .mcr-page-shell .mcr-page-tabs-shell {
    width: calc(100% - 8px) !important;
    margin-top: 2px !important;
  }
}

.mcr-page-shell .mcr-page-hero .mcr-shell__header-grid {
  grid-template-areas:
    "brand actions"
    "chips tabs" !important;
}

.mcr-page-shell .yh-preview-chips {
  align-self: end !important;
  margin-top: 8px !important;
}

.mcr-page-shell .mcr-page-tabs-shell {
  align-self: end !important;
  justify-self: end !important;
  width: clamp(420px, 34vw, 540px) !important;
  max-width: 540px !important;
  margin-top: 0 !important;
}

.mcr-page-shell .yh-field-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.mcr-page-shell .yh-inline-lock-badge {
  display: inline-flex;
  height: 20px;
  align-items: center;
  padding: 0 8px;
  border: 1px solid rgba(167, 187, 225, 0.45);
  border-radius: 999px;
  background: rgba(93, 136, 214, 0.08);
  color: #6d7d99;
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
  white-space: nowrap;
}

.mcr-page-shell[data-mcr-theme="dark"] .yh-inline-lock-badge {
  border-color: rgba(230, 236, 245, 0.12);
  background: rgba(110, 162, 255, 0.12);
  color: #c7d0e3;
}

.mcr-page-shell .yh-brand-zh-overlap {
  white-space: nowrap !important;
}

.mcr-page-shell .yh-brand-zh-part {
  display: inline;
}

@media (max-width: 768px) {
  .mcr-page-shell .mcr-page-hero .mcr-shell__header-grid {
    grid-template-areas:
      "brand actions"
      "chips chips"
      "tabs tabs" !important;
    row-gap: 8px !important;
  }

  .mcr-page-shell .yh-brand-title {
    max-width: 100% !important;
    overflow: hidden !important;
  }

  .mcr-page-shell .yh-brand-en-big {
    max-width: 100% !important;
    overflow: hidden !important;
    color: rgba(90, 120, 180, 0.15) !important;
    font-size: 56px !important;
    font-weight: 950 !important;
    line-height: 0.9 !important;
    text-overflow: clip !important;
    white-space: nowrap !important;
  }

  .mcr-page-shell .yh-brand-zh-overlap {
    white-space: nowrap !important;
  }

  .mcr-page-shell .yh-preview-chips {
    margin-top: 10px !important;
    margin-bottom: -2px !important;
  }

  .mcr-page-shell .mcr-page-tabs-shell {
    width: calc(100% - 8px) !important;
    max-width: none !important;
    margin-top: 0 !important;
  }
}

@media (max-width: 420px) {
  .mcr-page-shell .yh-brand-zh-overlap {
    white-space: normal !important;
    line-height: 0.95 !important;
  }

  .mcr-page-shell .yh-brand-zh-part {
    display: block;
  }
}

.mcr-page-shell .yh-brand-en-mobile {
  display: none;
}

@media (max-width: 768px) {
  .mcr-page-shell .mcr-page-hero {
    overflow: hidden !important;
  }

  .mcr-page-shell .mcr-page-hero .mcr-shell__copy,
  .mcr-page-shell .yh-brand-row {
    min-width: 0 !important;
    overflow: visible !important;
  }

  .mcr-page-shell .yh-brand-title {
    position: relative !important;
    width: 100% !important;
    min-height: 150px !important;
    max-width: none !important;
    overflow: visible !important;
  }

  .mcr-page-shell .yh-brand-en-big {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    z-index: 0 !important;
    display: block !important;
    width: max-content !important;
    max-width: none !important;
    overflow: visible !important;
    color: rgba(90, 120, 180, 0.14) !important;
    font-size: inherit !important;
    line-height: 1 !important;
    pointer-events: none;
    text-overflow: clip !important;
    white-space: normal !important;
  }

  .mcr-page-shell .yh-brand-en-pc {
    display: none !important;
  }

  .mcr-page-shell .yh-brand-en-mobile {
    display: flex !important;
    width: max-content !important;
    max-width: none !important;
    flex-direction: column;
    gap: 6px;
    overflow: visible !important;
  }

  .mcr-page-shell .yh-brand-en-mobile > span {
    display: block;
    color: inherit;
    font-size: clamp(58px, 15vw, 88px);
    font-weight: 950;
    letter-spacing: -0.06em;
    line-height: 0.86;
    white-space: nowrap;
  }

  .mcr-page-shell .yh-brand-zh-overlap {
    position: relative !important;
    z-index: 2 !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    margin: 0 !important;
    padding-top: 70px !important;
    color: #1c2740 !important;
    font-size: clamp(36px, 10vw, 52px) !important;
    font-weight: 950 !important;
    letter-spacing: -0.04em !important;
    line-height: 1.05 !important;
    white-space: normal !important;
  }

  .mcr-page-shell .yh-brand-zh-part {
    display: block !important;
  }

  .mcr-page-shell .mcr-page-top-actions.yh-top-actions {
    position: relative !important;
    z-index: 5 !important;
  }

  .mcr-page-shell .yh-run-btn,
  .mcr-page-shell .yh-icon-btn,
  .mcr-page-shell .yh-avatar-toolbar {
    position: relative !important;
    z-index: 6 !important;
  }

  .mcr-page-shell[data-mcr-theme="dark"] .yh-brand-en-big {
    color: rgba(110, 162, 255, 0.13) !important;
  }

  .mcr-page-shell[data-mcr-theme="dark"] .yh-brand-zh-overlap {
    color: #f4f7fb !important;
  }
}

@media (max-width: 420px) {
  .mcr-page-shell .yh-brand-title {
    min-height: 144px !important;
  }

  .mcr-page-shell .yh-brand-en-mobile > span {
    font-size: clamp(54px, 16vw, 72px);
  }

  .mcr-page-shell .yh-brand-zh-overlap {
    gap: 9px !important;
    padding-top: 66px !important;
  }
}

@media (max-width: 768px) {
  .mcr-page-shell .mcr-page-hero {
    overflow: hidden !important;
  }

  .mcr-page-shell .yh-brand-title {
    position: relative !important;
    width: 100% !important;
    min-height: 130px !important;
    max-width: none !important;
    overflow: visible !important;
  }

  .mcr-page-shell .yh-brand-en-big {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    z-index: 0 !important;
    width: max-content !important;
    max-width: none !important;
    overflow: visible !important;
    pointer-events: none;
    white-space: normal !important;
  }

  .mcr-page-shell .yh-brand-en-mobile {
    gap: 8px !important;
    width: max-content !important;
    max-width: none !important;
    overflow: visible !important;
  }

  .mcr-page-shell .yh-brand-en-mobile > span {
    font-size: clamp(60px, 17vw, 92px) !important;
    letter-spacing: -0.065em !important;
    line-height: 0.88 !important;
    white-space: nowrap !important;
  }

  .mcr-page-shell .yh-brand-zh-overlap {
    position: absolute !important;
    top: 28px !important;
    left: 0 !important;
    z-index: 2 !important;
    display: flex !important;
    width: max-content !important;
    max-width: none !important;
    flex-direction: column !important;
    gap: 8px !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
    color: #1c2740 !important;
    font-size: clamp(42px, 12vw, 60px) !important;
    font-weight: 950 !important;
    letter-spacing: -0.05em !important;
    line-height: 1.02 !important;
    overflow-wrap: normal !important;
    white-space: nowrap !important;
    word-break: keep-all !important;
  }

  .mcr-page-shell .yh-brand-zh-part {
    display: block !important;
    width: max-content !important;
    max-width: none !important;
    overflow: visible !important;
    overflow-wrap: normal !important;
    white-space: nowrap !important;
    word-break: keep-all !important;
  }

  .mcr-page-shell .yh-preview-chips {
    margin-top: 8px !important;
  }
}

@media (max-width: 390px) {
  .mcr-page-shell .yh-brand-title {
    min-height: 130px !important;
  }

  .mcr-page-shell .yh-brand-en-mobile > span {
    font-size: 58px !important;
  }

  .mcr-page-shell .yh-brand-zh-overlap {
    top: 28px !important;
    font-size: 40px !important;
  }
}

.mcr-page-shell[data-mcr-theme="dark"] .yh-brand-en-big,
.mcr-page-shell[data-mcr-theme="dark"] .yh-brand-en-big span,
html.dark .mcr-page-shell .yh-brand-en-big,
html.dark .mcr-page-shell .yh-brand-en-big span,
[data-theme="dark"] .mcr-page-shell .yh-brand-en-big,
[data-theme="dark"] .mcr-page-shell .yh-brand-en-big span,
.v-theme--dark .mcr-page-shell .yh-brand-en-big,
.v-theme--dark .mcr-page-shell .yh-brand-en-big span {
  color: rgba(244, 247, 251, 0.035) !important;
  opacity: 1 !important;
  text-shadow: none !important;
  -webkit-text-fill-color: rgba(244, 247, 251, 0.035) !important;
}

@media (prefers-color-scheme: dark) {
  .mcr-page-shell .yh-brand-en-big,
  .mcr-page-shell .yh-brand-en-big span {
    color: rgba(244, 247, 251, 0.035) !important;
    opacity: 1 !important;
    text-shadow: none !important;
    -webkit-text-fill-color: rgba(244, 247, 251, 0.035) !important;
  }
}

.mcr-page-shell[data-mcr-theme="dark"] .yh-brand-zh-overlap,
.mcr-page-shell[data-mcr-theme="dark"] .yh-brand-zh-overlap .yh-brand-zh-part {
  color: #f4f7fb !important;
}

.mcr-page-shell .mcr-history-card__media {
  display: block !important;
  width: 100% !important;
  aspect-ratio: 16 / 9 !important;
  min-height: 136px !important;
  background: rgba(var(--mcr-rgb-surface-container-high), 0.5) !important;
}

.mcr-page-shell .mcr-history-card__image {
  display: block !important;
  width: 100% !important;
  height: 100% !important;
  min-height: 136px !important;
}

.mcr-page-shell .mcr-history-card__image :deep(.v-img__img),
.mcr-page-shell .mcr-history-card__image :deep(img) {
  width: 100% !important;
  height: 100% !important;
  object-fit: cover !important;
}

@media (max-width: 599px) {
  .mcr-page-shell .mcr-history-card__media,
  .mcr-page-shell .mcr-history-card__image {
    min-height: 108px !important;
  }
}
</style>
