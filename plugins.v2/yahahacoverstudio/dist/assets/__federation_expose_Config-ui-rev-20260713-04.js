import { importShared } from './__federation_fn_import-ui-rev-20260713-04.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-ui-rev-20260713-04.js';
import { B as BUILTIN_FONT_ITEMS, M as MCR_CONTROL_DEFAULTS, b as BlueprintField, c as BlueprintSelect, A as AsyncStatusDots, V as ViewportSaveToast, a as getTemplateFontFaceName } from './ViewportSaveToast-ui-rev-20260713-04.js';

const UI_REV = "20260713-04";
const PROGRAM_VERSION = "2.0.6";

const {defineComponent:_defineComponent$1} = await importShared('vue');

const {renderList:_renderList$1,Fragment:_Fragment$1,openBlock:_openBlock$1,createElementBlock:_createElementBlock$1,createElementVNode:_createElementVNode$1,mergeProps:_mergeProps,toDisplayString:_toDisplayString$1,resolveComponent:_resolveComponent$1,withCtx:_withCtx$1,createBlock:_createBlock$1,normalizeStyle:_normalizeStyle$1,Teleport:_Teleport} = await importShared('vue');

const _hoisted_1$1 = ["data-mcr-theme"];
const _hoisted_2$1 = ["aria-label", "aria-current", "onClick"];
const {nextTick: nextTick$1,onBeforeUnmount: onBeforeUnmount$1,onMounted: onMounted$1,ref: ref$1,watch: watch$1} = await importShared('vue');

const _sfc_main$1 = /* @__PURE__ */ _defineComponent$1({
  __name: "SettingsAnchorNav",
  props: {
    sections: {},
    contentElement: { default: null },
    scrollContainer: { default: null },
    topOffset: { default: 96 },
    theme: { default: "light" }
  },
  setup(__props) {
    const props = __props;
    const activeId = ref$1(props.sections[0]?.id || "");
    const navLeft = ref$1(12);
    let observer = null;
    let resizeObserver = null;
    let resolvedScrollContainer = null;
    let clickLockUntil = 0;
    let clickUnlockTimer = null;
    function observedElements() {
      return props.sections.map((section) => document.getElementById(section.id)).filter((element) => Boolean(element));
    }
    function findScrollContainer(element) {
      let current = element?.parentElement || null;
      while (current) {
        const style = getComputedStyle(current);
        if (/(auto|scroll)/.test(`${style.overflowY} ${style.overflow}`) && current.scrollHeight > current.clientHeight) return current;
        current = current.parentElement;
      }
      return null;
    }
    function updatePosition() {
      const rect = props.contentElement?.getBoundingClientRect();
      navLeft.value = rect ? Math.max(12, Math.round(rect.left - 46)) : 12;
      resolvedScrollContainer = props.scrollContainer || findScrollContainer(props.contentElement || observedElements()[0] || null);
    }
    function setupObserver() {
      observer?.disconnect();
      updatePosition();
      const elements = observedElements();
      if (!elements.length || typeof IntersectionObserver === "undefined") return;
      observer = new IntersectionObserver((entries) => {
        if (Date.now() < clickLockUntil) return;
        const root = resolvedScrollContainer;
        const reachedBottom = root ? root.scrollTop + root.clientHeight >= root.scrollHeight - 2 : window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2;
        if (reachedBottom && props.sections.length) {
          activeId.value = props.sections.at(-1)?.id || activeId.value;
          return;
        }
        const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => Math.abs(a.boundingClientRect.top - props.topOffset) - Math.abs(b.boundingClientRect.top - props.topOffset));
        if (visible[0]?.target.id) activeId.value = visible[0].target.id;
      }, { root: resolvedScrollContainer, rootMargin: `-${props.topOffset}px 0px -62% 0px`, threshold: [0, 0.05, 0.25, 0.6] });
      elements.forEach((element) => observer?.observe(element));
    }
    function scrollToSection(id) {
      const target = document.getElementById(id);
      if (!target) return;
      activeId.value = id;
      clickLockUntil = Date.now() + 1800;
      if (resolvedScrollContainer) {
        const rootRect = resolvedScrollContainer.getBoundingClientRect();
        const targetRect = target.getBoundingClientRect();
        resolvedScrollContainer.scrollTo({ top: resolvedScrollContainer.scrollTop + targetRect.top - rootRect.top - props.topOffset, behavior: "smooth" });
      } else target.scrollIntoView({ behavior: "smooth", block: "start" });
      if (clickUnlockTimer !== null) window.clearTimeout(clickUnlockTimer);
      clickUnlockTimer = window.setTimeout(() => {
        activeId.value = id;
        clickUnlockTimer = null;
      }, 950);
    }
    watch$1(() => [props.sections, props.scrollContainer, props.contentElement], () => void nextTick$1(setupObserver), { deep: true });
    onMounted$1(() => void nextTick$1(() => {
      setupObserver();
      if (typeof ResizeObserver !== "undefined" && props.contentElement) {
        resizeObserver = new ResizeObserver(setupObserver);
        resizeObserver.observe(props.contentElement);
      }
      window.addEventListener("resize", setupObserver);
    }));
    onBeforeUnmount$1(() => {
      observer?.disconnect();
      resizeObserver?.disconnect();
      window.removeEventListener("resize", setupObserver);
      if (clickUnlockTimer !== null) window.clearTimeout(clickUnlockTimer);
    });
    return (_ctx, _cache) => {
      const _component_v_tooltip = _resolveComponent$1("v-tooltip");
      return _openBlock$1(), _createBlock$1(_Teleport, { to: "body" }, [
        _createElementVNode$1("nav", {
          class: "yh-settings-anchor",
          style: _normalizeStyle$1({ left: `${navLeft.value}px` }),
          "data-mcr-theme": __props.theme,
          "aria-label": "设置分组导航"
        }, [
          (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(__props.sections, (section) => {
            return _openBlock$1(), _createBlock$1(_component_v_tooltip, {
              key: section.id,
              location: "end",
              "open-delay": 220
            }, {
              activator: _withCtx$1(({ props: tooltipProps }) => [
                _createElementVNode$1("button", _mergeProps({ ref_for: true }, tooltipProps, {
                  type: "button",
                  class: ["yh-settings-anchor__button", { "is-active": activeId.value === section.id }],
                  "aria-label": `跳转到${section.label}`,
                  "aria-current": activeId.value === section.id ? "true" : void 0,
                  onClick: ($event) => scrollToSection(section.id)
                }), [..._cache[0] || (_cache[0] = [
                  _createElementVNode$1("span", {
                    class: "yh-settings-anchor__line",
                    "aria-hidden": "true"
                  }, null, -1)
                ])], 16, _hoisted_2$1)
              ]),
              default: _withCtx$1(() => [
                _createElementVNode$1("span", null, _toDisplayString$1(section.label), 1)
              ]),
              _: 2
            }, 1024);
          }), 128))
        ], 12, _hoisted_1$1)
      ]);
    };
  }
});

const SettingsAnchorNav = /* @__PURE__ */ _export_sfc(_sfc_main$1, [["__scopeId", "data-v-2297dccd"]]);

const {defineComponent:_defineComponent} = await importShared('vue');

const {createElementVNode:_createElementVNode,unref:_unref,resolveComponent:_resolveComponent,createVNode:_createVNode,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,toDisplayString:_toDisplayString,normalizeClass:_normalizeClass,normalizeStyle:_normalizeStyle,withCtx:_withCtx,renderList:_renderList,Fragment:_Fragment,createBlock:_createBlock,createTextVNode:_createTextVNode,vModelText:_vModelText,withDirectives:_withDirectives,withModifiers:_withModifiers} = await importShared('vue');

const _hoisted_1 = ["data-mcr-theme"];
const _hoisted_2 = { class: "mcr-config-app" };
const _hoisted_3 = { class: "mcr-config-topbar" };
const _hoisted_4 = { class: "mcr-config-topbar__meta" };
const _hoisted_5 = { class: "mcr-config-top-actions yh-top-actions" };
const _hoisted_6 = ["title", "aria-label", "disabled"];
const _hoisted_7 = { class: "yh-run-content" };
const _hoisted_8 = {
  key: 0,
  class: "yh-run-text"
};
const _hoisted_9 = {
  key: 1,
  class: "yh-run-percent"
};
const _hoisted_10 = {
  class: "mcr-config-tags yh-header-chips",
  "aria-label": "配置摘要"
};
const _hoisted_11 = { class: "mcr-config-tag" };
const _hoisted_12 = { class: "mcr-config-tag" };
const _hoisted_13 = {
  class: "mcr-config-top-tabs yh-segment",
  role: "tablist",
  "aria-label": "设置页面切换"
};
const _hoisted_14 = ["aria-selected", "onClick"];
const _hoisted_15 = { class: "mcr-config-workspace" };
const _hoisted_16 = {
  class: "mcr-config-sidebar",
  "aria-label": "设置页面导航"
};
const _hoisted_17 = ["aria-selected", "onClick"];
const _hoisted_18 = {
  id: "settings-runtime",
  class: "mcr-config-section-card"
};
const _hoisted_19 = { class: "yh-switch-row" };
const _hoisted_20 = {
  id: "settings-monitoring",
  class: "mcr-config-section-card"
};
const _hoisted_21 = {
  id: "settings-libraries",
  class: "mcr-config-section-card"
};
const _hoisted_22 = {
  id: "settings-images",
  class: "mcr-config-section-card"
};
const _hoisted_23 = {
  id: "settings-history",
  class: "mcr-config-section-card"
};
const _hoisted_24 = {
  id: "settings-fonts",
  class: "mcr-config-section-card"
};
const _hoisted_25 = { class: "mcr-font-library" };
const _hoisted_26 = { class: "mcr-font-library__header" };
const _hoisted_27 = { class: "mcr-font-library__import" };
const _hoisted_28 = { class: "mcr-font-link-field" };
const _hoisted_29 = { class: "mcr-font-link-field__control" };
const _hoisted_30 = ["disabled"];
const _hoisted_31 = { class: "mcr-font-library__listbar" };
const _hoisted_32 = {
  key: 0,
  class: "mcr-font-library__empty"
};
const _hoisted_33 = {
  key: 1,
  class: "mcr-font-library__empty"
};
const _hoisted_34 = {
  key: 2,
  class: "mcr-font-library__grid"
};
const _hoisted_35 = ["title", "onClick"];
const _hoisted_36 = { class: "mcr-font-item__name" };
const _hoisted_37 = ["onClick"];
const _hoisted_38 = ["onClick"];
const _hoisted_39 = {
  key: 3,
  class: "mcr-font-library__status"
};
const _hoisted_40 = {
  id: "settings-backup",
  class: "mcr-config-section-card"
};
const _hoisted_41 = { class: "mcr-config-backup-grid mcr-config-backup-grid--cron-only" };
const _hoisted_42 = { class: "mcr-config-backup-grid__actions" };
const _hoisted_43 = { class: "mcr-config-backup-actions" };
const _hoisted_44 = {
  key: 0,
  class: "mcr-backup-library"
};
const _hoisted_45 = {
  key: 0,
  class: "mcr-font-library__empty"
};
const _hoisted_46 = {
  key: 1,
  class: "mcr-font-library__empty"
};
const _hoisted_47 = {
  key: 2,
  class: "mcr-backup-library__grid"
};
const _hoisted_48 = { class: "mcr-backup-item__main" };
const _hoisted_49 = ["title"];
const _hoisted_50 = { class: "mcr-backup-item__meta" };
const _hoisted_51 = { key: 0 };
const _hoisted_52 = { class: "mcr-backup-item__actions" };
const _hoisted_53 = ["onClick"];
const _hoisted_54 = ["onClick"];
const _hoisted_55 = ["onClick"];
const _hoisted_56 = {
  id: "settings-cache",
  class: "mcr-config-section-card"
};
const _hoisted_57 = { class: "mcr-config-clean-actions" };
const _hoisted_58 = { class: "mcr-config-clean-action" };
const _hoisted_59 = { class: "mcr-config-clean-action" };
const _hoisted_60 = { class: "mcr-title-config-heading" };
const _hoisted_61 = { class: "mcr-title-config-toolbar" };
const _hoisted_62 = { class: "mcr-title-config-mode" };
const _hoisted_63 = { class: "yh-ui-rev" };
const {ref,watch,computed,nextTick,onMounted,onBeforeUnmount} = await importShared('vue');
const titleConfigReference = `媒体库名称:
  title: "主标题"
  subtitle: "副标题"
  background: "#5f7185"
  texts:
    slogan: "自定义文本"
    note: "备注文本"
    any_key: "任意自定义文本"

# texts 下的 slogan / note / any_key 都不是固定变量名，可以随意命名。
# 在画布编辑的文字图层中选择「按媒体库配置」，并在「配置文本键」填写同名键即可。`;
const _sfc_main = /* @__PURE__ */ _defineComponent({
  __name: "Config",
  props: {
    initialConfig: {
      type: Object,
      default: () => ({})
    },
    api: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ["save", "close", "switch"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const controlDefaults = MCR_CONTROL_DEFAULTS;
    const settingsContentEl = ref(null);
    const settingsAnchorSections = [
      { id: "settings-runtime", label: "运行与定时" },
      { id: "settings-monitoring", label: "入库监控" },
      { id: "settings-libraries", label: "媒体库范围" },
      { id: "settings-images", label: "自定义图片目录" },
      { id: "settings-history", label: "历史封面" },
      { id: "settings-fonts", label: "字体库" },
      { id: "settings-backup", label: "备份还原" },
      { id: "settings-cache", label: "清理缓存" }
    ];
    const defaults = {
      enabled: true,
      auto_save_config: false,
      update_now: false,
      transfer_monitor: true,
      monitor_source: "transfer",
      lock_latest_sort: false,
      cron: "",
      delay: 60,
      selected_servers: [],
      all_servers: [],
      include_libraries: [],
      all_libraries: [],
      sort_by: "Random",
      title_config: "",
      title_config_strict: false,
      distinguish_same_name_libraries: false,
      covers_input: "",
      covers_output: "",
      save_recent_covers: true,
      history_retention_batches: 30,
      covers_history_limit_per_library: 10,
      covers_page_history_limit: 50,
      cover_style_base: "static_1",
      cover_style_variant: "static",
      main_title_font_preset: "chaohei",
      subtitle_font_preset: "EmblemaOne",
      custom_text_font_preset: "EmblemaOne",
      main_title_font_custom: "",
      subtitle_font_custom: "",
      custom_text_font_custom: "",
      main_title_font_size: null,
      subtitle_font_size: null,
      blur_size: 50,
      color_ratio: 0.8,
      title_scale: 1,
      main_title_font_offset: null,
      title_spacing: null,
      subtitle_line_spacing: null,
      resolution: "480p",
      custom_width: 1920,
      custom_height: 1080,
      bg_color_mode: "auto",
      custom_bg_color: "",
      animation_duration: 8,
      animation_scroll: "alternate",
      animation_fps: 24,
      animation_format: "apng",
      animation_resolution: "320x180",
      animation_reduce_colors: "medium",
      animated_2_image_count: 6,
      animated_2_departure_type: "fly",
      clean_images: false,
      clean_fonts: false,
      backup_enabled: false,
      backup_cron: "",
      backup_path: "",
      page_tab: "generate-tab",
      style_naming_v2: true,
      custom_static_layout: null,
      custom_static_layouts: null,
      custom_static_active_id: null
    };
    const config = ref({
      ...defaults,
      ...normalizeConfigInput(props.initialConfig)
    });
    const generatingNow = ref(false);
    const isGenerating = ref(false);
    const configSaving = ref(false);
    const configAutoSaveEnabled = ref(false);
    const generationCurrent = ref(0);
    const generationTotal = ref(0);
    const generationLabel = ref("");
    const optionsLoading = ref(false);
    const cacheAction = ref("");
    let generationStatusTimer = null;
    computed(() => isGenerating.value || generatingNow.value || optionsLoading.value || Boolean(cacheAction.value));
    computed(() => {
      if (isGenerating.value) {
        if (generationTotal.value > 0) return `正在生成 ${generationCurrent.value || 0}/${generationTotal.value}`;
        return generationLabel.value || "正在生成";
      }
      if (generatingNow.value) return "正在执行";
      if (cacheAction.value === "backup") return "正在备份";
      if (cacheAction.value) return "正在清理";
      return "同步数据";
    });
    const configGenerationProgressLabel = computed(() => {
      if (generationTotal.value > 0) return `正在生成 ${generationCurrent.value || 0}/${generationTotal.value}`;
      return generationLabel.value || "正在生成";
    });
    const configGenerationProgressPercent = computed(() => {
      if (generationTotal.value > 0) {
        const raw = Math.round(Math.max(0, generationCurrent.value || 0) / generationTotal.value * 100);
        return Math.max(0, Math.min(100, raw));
      }
      return isGenerating.value ? 12 : 0;
    });
    const configRunButtonProgressStyle = computed(() => ({
      "--yh-run-progress": `${configGenerationProgressPercent.value}%`
    }));
    computed(
      () => isGenerating.value ? configGenerationProgressLabel.value : "立即生成"
    );
    const scheduleModeLabel = computed(() => {
      const hasMonitor = Boolean(config.value.transfer_monitor);
      const hasCron = Boolean(String(config.value.cron || "").trim());
      if (hasMonitor && hasCron) return "自动+定时";
      if (hasMonitor) return "自动";
      if (hasCron) return "定时";
      return "手动";
    });
    const monitorSourceItems = [
      { title: "MP 整理完成（方便）", value: "transfer" },
      { title: "Emby 新媒体已添加（精准）", value: "emby" }
    ];
    const fontFileInputEl = ref(null);
    const backupFileInputEl = ref(null);
    const fontLibraryLoading = ref(false);
    const backupListLoading = ref(false);
    const customFontItems = ref([]);
    const backupItems = ref([]);
    const fontLibraryExpanded = ref(true);
    const backupLibraryExpanded = ref(true);
    const fontUrlInput = ref("");
    const fontUploadMessage = ref("");
    const backupResult = ref("");
    const configSaveMessage = ref("");
    const titleConfigValidationMessage = ref("");
    const titleConfigValidationValid = ref(false);
    const titleTemplateLoading = ref(false);
    let titleConfigValidationTimer = null;
    let configAutoSaveTimer = null;
    let configSaveMessageTimer = null;
    let suppressConfigAutoSave = true;
    const loadedConfigFontUrls = /* @__PURE__ */ new Map();
    function normalizeConfigInput(input) {
      const raw = input || {};
      return {
        ...raw,
        update_now: false,
        auto_save_config: Boolean(raw.auto_save_config ?? defaults.auto_save_config),
        lock_latest_sort: Boolean(raw.lock_latest_sort ?? defaults.lock_latest_sort),
        monitor_source: raw.monitor_source === "emby" ? "emby" : "transfer",
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
        backup_path: raw.backup_path ?? defaults.backup_path
      };
    }
    watch(
      () => props.initialConfig,
      (val) => {
        suppressConfigAutoSave = true;
        config.value = {
          ...defaults,
          ...normalizeConfigInput(val)
        };
        nextTick(() => {
          suppressConfigAutoSave = false;
        });
      },
      { deep: true }
    );
    watch(
      config,
      () => {
        scheduleConfigAutoSave();
      },
      { deep: true }
    );
    async function validateTitleConfig(showSuccess = false) {
      const titleConfig = config.value.title_config || "";
      titleConfigValidationMessage.value = "";
      titleConfigValidationValid.value = false;
      if (!titleConfig.trim()) {
        titleConfigValidationValid.value = true;
        return true;
      }
      try {
        const resp = await props.api.post("plugin/YahahaCoverStudio/validate_title_config", {
          title_config: titleConfig,
          strict: config.value.title_config_strict,
          distinguish_same_name_libraries: Boolean(config.value.distinguish_same_name_libraries)
        });
        const errors = Array.isArray(resp?.data?.errors) ? resp.data.errors : [];
        const valid = Boolean(resp && resp.code === 0 && resp.data?.valid !== false && !errors.length);
        titleConfigValidationValid.value = valid;
        if (!valid) {
          titleConfigValidationMessage.value = errors[0] || resp?.msg || "标题配置 YAML 格式不正确";
        } else if (showSuccess) {
          titleConfigValidationMessage.value = "标题配置格式正确";
        }
        return valid;
      } catch (error) {
        console.warn("validate title config failed", error);
        titleConfigValidationMessage.value = "标题配置验证失败，请稍后重试";
        titleConfigValidationValid.value = false;
        return false;
      }
    }
    async function appendMissingTitleTemplates() {
      titleTemplateLoading.value = true;
      titleConfigValidationMessage.value = "";
      titleConfigValidationValid.value = false;
      try {
        const resp = await props.api.post("plugin/YahahaCoverStudio/title_config_template", {
          title_config: config.value.title_config || "",
          strict: config.value.title_config_strict,
          distinguish_same_name_libraries: Boolean(config.value.distinguish_same_name_libraries)
        });
        const errors = Array.isArray(resp?.data?.errors) ? resp.data.errors : [];
        if (!resp || resp.code !== 0 || resp.data?.valid === false || errors.length) {
          titleConfigValidationMessage.value = errors[0] || resp?.msg || "标题配置格式不正确，无法补全媒体库模板";
          titleConfigValidationValid.value = false;
          return;
        }
        const yaml = String(resp.data?.yaml || "").trim();
        const missing = Array.isArray(resp.data?.missing) ? resp.data.missing : [];
        if (!yaml) {
          titleConfigValidationMessage.value = "当前媒体库都已有标题配置，无需补全";
          titleConfigValidationValid.value = true;
          return;
        }
        const current = String(config.value.title_config || "").trimEnd();
        config.value.title_config = current ? `${current}

${yaml}
` : `${yaml}
`;
        titleConfigValidationMessage.value = `已添加 ${missing.length || yaml.split("\n\n").length} 个媒体库配置模板`;
        titleConfigValidationValid.value = true;
        scheduleTitleConfigValidation();
      } catch (error) {
        console.warn("append title config templates failed", error);
        titleConfigValidationMessage.value = "获取媒体库模板失败，请确认媒体服务器可用";
        titleConfigValidationValid.value = false;
      } finally {
        titleTemplateLoading.value = false;
      }
    }
    function scheduleTitleConfigValidation() {
      if (titleConfigValidationTimer !== null && typeof window !== "undefined") {
        window.clearTimeout(titleConfigValidationTimer);
      }
      if (typeof window === "undefined") return;
      titleConfigValidationTimer = window.setTimeout(() => {
        void validateTitleConfig(false);
      }, 500);
    }
    watch(
      () => [config.value.title_config, config.value.title_config_strict],
      () => {
        scheduleTitleConfigValidation();
      }
    );
    async function loadDynamicLibraryOptions() {
      optionsLoading.value = true;
      try {
        const resp = await props.api.get(
          "plugin/YahahaCoverStudio/status"
        );
        if (!resp || resp.code !== 0 || !resp.data) return;
        if (Array.isArray(resp.data.all_libraries) && resp.data.all_libraries.length) {
          config.value.all_libraries = resp.data.all_libraries;
        }
        if (Array.isArray(resp.data.all_servers)) {
          config.value.all_servers = resp.data.all_servers;
        }
        isGenerating.value = Boolean(resp.data.is_generating);
        generationCurrent.value = Number(resp.data.generation_current || 0);
        generationTotal.value = Number(resp.data.generation_total || 0);
        generationLabel.value = String(resp.data.generation_label || "");
        if (isGenerating.value) {
          startGenerationStatusPoller();
        } else {
          stopGenerationStatusPoller();
        }
        if ((!Array.isArray(config.value.selected_servers) || !config.value.selected_servers.length) && Array.isArray(resp.data.selected_servers)) {
          config.value.selected_servers = resp.data.selected_servers;
        }
        if ((!Array.isArray(config.value.include_libraries) || !config.value.include_libraries.length) && Array.isArray(resp.data.include_libraries)) {
          config.value.include_libraries = resp.data.include_libraries;
        }
      } catch (e) {
        console.error("loadDynamicLibraryOptions failed", e);
      } finally {
        optionsLoading.value = false;
      }
    }
    function ensureConfigFontFace(item) {
      const url = item.url || item.dataUrl;
      if (!url || typeof FontFace === "undefined" || typeof document === "undefined") return Promise.resolve();
      const name = getTemplateFontFaceName(item.value);
      const cacheKey = `${name}:${url}`;
      const cached = loadedConfigFontUrls.get(cacheKey);
      if (cached) return cached;
      const pending = new FontFace(name, `url(${url})`).load().then((font) => {
        document.fonts.add(font);
      }).catch((error) => {
        console.warn("load custom font failed", error);
      }).then(() => void 0);
      loadedConfigFontUrls.set(cacheKey, pending);
      return pending;
    }
    function getCustomFontFamily(item) {
      void ensureConfigFontFace(item);
      return `${getTemplateFontFaceName(item.value)}, var(--mcr-font-body)`;
    }
    async function loadFontLibrary() {
      fontLibraryLoading.value = true;
      try {
        const resp = await props.api.get("plugin/YahahaCoverStudio/fonts");
        if (!resp || resp.code !== 0) {
          throw new Error(resp?.msg || "load fonts failed");
        }
        customFontItems.value = Array.isArray(resp.data?.custom) ? resp.data.custom : [];
        await Promise.all(customFontItems.value.map((item) => ensureConfigFontFace(item)));
      } catch (error) {
        console.warn("load font library failed", error);
      } finally {
        fontLibraryLoading.value = false;
      }
    }
    async function loadBackupLibrary() {
      backupListLoading.value = true;
      try {
        const resp = await props.api.get("plugin/YahahaCoverStudio/backups");
        if (!resp || resp.code !== 0) {
          throw new Error(resp?.msg || "load backups failed");
        }
        backupItems.value = Array.isArray(resp.data) ? resp.data : [];
      } catch (error) {
        console.warn("load backup library failed", error);
      } finally {
        backupListLoading.value = false;
      }
    }
    function openFontFilePicker() {
      fontFileInputEl.value?.click();
    }
    function openBackupFilePicker() {
      backupFileInputEl.value?.click();
    }
    function readFileAsDataUrl(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onerror = () => reject(reader.error || new Error("read failed"));
        reader.onload = () => resolve(String(reader.result || ""));
        reader.readAsDataURL(file);
      });
    }
    function bytesToBase64(bytes) {
      let binary = "";
      const step = 32768;
      for (let index = 0; index < bytes.length; index += step) {
        binary += String.fromCharCode(...bytes.subarray(index, index + step));
      }
      return window.btoa(binary);
    }
    async function uploadFontPayload(payload) {
      fontLibraryLoading.value = true;
      fontUploadMessage.value = "";
      try {
        const resp = await props.api.post("plugin/YahahaCoverStudio/upload_font", {
          ...payload
        });
        if (!resp || resp.code !== 0 || !resp.data?.value) {
          throw new Error(resp?.msg || "upload font failed");
        }
        customFontItems.value = [
          resp.data,
          ...customFontItems.value.filter((item) => item.value !== resp.data?.value)
        ];
        await ensureConfigFontFace(resp.data);
        void loadFontLibrary();
        fontUploadMessage.value = `已保存字体：${resp.data.name || resp.data.title}`;
        return resp.data;
      } catch (error) {
        console.warn("upload font failed", error);
        fontUploadMessage.value = error instanceof Error ? error.message : "字体上传失败";
        return null;
      } finally {
        fontLibraryLoading.value = false;
      }
    }
    async function uploadFontFile(file) {
      fontLibraryLoading.value = true;
      fontUploadMessage.value = "正在上传字体...";
      try {
        const bytes = new Uint8Array(await file.arrayBuffer());
        const chunkSize = 384 * 1024;
        const total = Math.max(1, Math.ceil(bytes.length / chunkSize));
        const uploadId = `font_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
        let savedItem = null;
        for (let index = 0; index < total; index += 1) {
          const chunk = bytes.subarray(index * chunkSize, Math.min(bytes.length, (index + 1) * chunkSize));
          fontUploadMessage.value = `正在上传字体 ${index + 1}/${total}`;
          const resp = await props.api.post(
            "plugin/YahahaCoverStudio/upload_font",
            {
              upload_id: uploadId,
              name: file.name,
              chunk_index: String(index),
              chunk_total: String(total),
              chunk_data: bytesToBase64(chunk)
            }
          );
          if (!resp || resp.code !== 0) {
            throw new Error(resp?.msg || "upload font failed");
          }
          if (resp.data?.done && resp.data.value) {
            savedItem = resp.data;
          }
        }
        if (!savedItem) {
          throw new Error("字体上传未完成");
        }
        customFontItems.value = [
          savedItem,
          ...customFontItems.value.filter((item) => item.value !== savedItem?.value)
        ];
        await ensureConfigFontFace(savedItem);
        await loadFontLibrary();
        fontUploadMessage.value = `已保存字体：${savedItem.name || savedItem.title}`;
      } catch (error) {
        console.warn("upload font failed", error);
        fontUploadMessage.value = error instanceof Error ? error.message : "字体上传失败";
      } finally {
        fontLibraryLoading.value = false;
      }
    }
    async function uploadFontUrl() {
      const url = fontUrlInput.value.trim();
      if (!url) return;
      const imported = await uploadFontPayload({
        url,
        name: decodeURIComponent(url.split("/").pop()?.split("?")[0] || "font")
      });
      if (imported) {
        fontUrlInput.value = "";
      }
    }
    function onFontFileInputChange(event) {
      const input = event.target;
      const file = input.files?.[0];
      input.value = "";
      if (file) {
        void uploadFontFile(file);
      }
    }
    async function deleteFontItem(item) {
      try {
        const resp = await props.api.post(
          `plugin/YahahaCoverStudio/delete_font?file=${encodeURIComponent(item.value || item.path || item.name)}`
        );
        if (!resp || resp.code !== 0) {
          throw new Error(resp?.msg || "delete font failed");
        }
        customFontItems.value = customFontItems.value.filter((candidate) => candidate.value !== item.value);
        if (config.value.main_title_font_preset === item.value) config.value.main_title_font_preset = defaults.main_title_font_preset;
        if (config.value.subtitle_font_preset === item.value) config.value.subtitle_font_preset = defaults.subtitle_font_preset;
        if (config.value.custom_text_font_preset === item.value) config.value.custom_text_font_preset = defaults.custom_text_font_preset;
        void loadFontLibrary();
      } catch (error) {
        console.warn("delete font failed", error);
      }
    }
    function fontDisplayName(item) {
      return String(item.title || item.name || "").replace(/\.[^.]+$/, "");
    }
    async function renameFontItem(item) {
      if (fontLibraryLoading.value) return;
      const currentName = fontDisplayName(item);
      const nextName = typeof window !== "undefined" ? window.prompt("重命名字体", currentName) : currentName;
      const trimmedName = String(nextName || "").trim();
      if (!trimmedName || trimmedName === currentName) return;
      fontLibraryLoading.value = true;
      fontUploadMessage.value = "";
      try {
        const resp = await props.api.post("plugin/YahahaCoverStudio/rename_font", {
          value: item.value,
          path: item.path,
          name: item.name,
          new_name: trimmedName
        });
        if (!resp || resp.code !== 0 || !resp.data) {
          throw new Error(resp?.msg || "rename font failed");
        }
        if (config.value.main_title_font_preset === item.value) config.value.main_title_font_preset = resp.data.value;
        if (config.value.subtitle_font_preset === item.value) config.value.subtitle_font_preset = resp.data.value;
        if (config.value.custom_text_font_preset === item.value) config.value.custom_text_font_preset = resp.data.value;
        fontUploadMessage.value = `已重命名字体：${resp.data.title}`;
        await loadFontLibrary();
      } catch (error) {
        console.warn("rename font failed", error);
        fontUploadMessage.value = error instanceof Error ? error.message : "字体重命名失败";
      } finally {
        fontLibraryLoading.value = false;
      }
    }
    function startGenerationStatusPoller() {
      if (generationStatusTimer !== null || typeof window === "undefined") return;
      generationStatusTimer = window.setInterval(() => {
        void loadDynamicLibraryOptions();
      }, 2e3);
    }
    function stopGenerationStatusPoller() {
      if (generationStatusTimer === null || typeof window === "undefined") return;
      window.clearInterval(generationStatusTimer);
      generationStatusTimer = null;
    }
    const tab = ref("basic-tab");
    const tabItems = [
      { title: "配置", value: "basic-tab", icon: "mdi-view-dashboard-outline" },
      { title: "标题", value: "title-tab", icon: "mdi-format-title" }
    ];
    const mainTitleFontItems = computed(() => {
      const items = [...BUILTIN_FONT_ITEMS, ...customFontItems.value.map((item) => ({ title: `自定义 ${item.title}`, value: item.value }))];
      if (config.value.main_title_font_preset && !items.some((item) => item.value === config.value.main_title_font_preset)) {
        items.push({ title: config.value.main_title_font_preset, value: config.value.main_title_font_preset });
      }
      return items;
    });
    const subtitleFontItems = computed(() => {
      const items = [...BUILTIN_FONT_ITEMS, ...customFontItems.value.map((item) => ({ title: `自定义 ${item.title}`, value: item.value }))];
      if (config.value.subtitle_font_preset && !items.some((item) => item.value === config.value.subtitle_font_preset)) {
        items.push({ title: config.value.subtitle_font_preset, value: config.value.subtitle_font_preset });
      }
      if (config.value.custom_text_font_preset && !items.some((item) => item.value === config.value.custom_text_font_preset)) {
        items.push({ title: config.value.custom_text_font_preset, value: config.value.custom_text_font_preset });
      }
      return items;
    });
    const libraryItems = computed(() => {
      const all = config.value.all_libraries;
      if (!Array.isArray(all)) return [];
      const selected = new Set((config.value.selected_servers || []).map(String));
      const normalized = all.map((lib) => {
        const separator = String(lib.name || "").indexOf(":");
        const server = String(lib.server_id || lib.server || (separator >= 0 ? lib.name.slice(0, separator) : "")).trim();
        const name = separator >= 0 ? String(lib.name).slice(separator + 1).trim() : String(lib.name || "");
        return { ...lib, server, libraryName: name };
      });
      const visible = selected.size ? normalized.filter((lib) => selected.has(lib.server)) : normalized;
      const showServer = selected.size !== 1;
      return visible.map((lib) => ({
        title: showServer && lib.server ? `${lib.server} - ${lib.libraryName}` : lib.libraryName,
        value: String(lib.value)
      }));
    });
    const serverItems = computed(() => {
      const items = [];
      const seen = /* @__PURE__ */ new Set();
      const allServers = config.value.all_servers;
      if (Array.isArray(allServers) && allServers.length) {
        for (const item of allServers) {
          const value = typeof item === "object" && item !== null ? String(item.value ?? item.title ?? item.name ?? "") : String(item ?? "");
          const title = typeof item === "object" && item !== null ? String(item.title ?? item.name ?? item.value ?? value) : value;
          if (value && !seen.has(value)) {
            seen.add(value);
            items.push({ title, value });
          }
        }
      }
      return items;
    });
    const selectedServerValues = computed(() => new Set(serverItems.value.map((item) => item.value)));
    const selectedLibraryValues = computed(() => new Set(libraryItems.value.map((item) => item.value)));
    watch([serverItems, () => config.value.selected_servers], () => {
      const allowed = selectedServerValues.value;
      if (!allowed.size || !Array.isArray(config.value.selected_servers)) return;
      const filtered = config.value.selected_servers.filter((item) => allowed.has(String(item)));
      if (filtered.length !== config.value.selected_servers.length) config.value.selected_servers = filtered;
    }, { deep: true, immediate: true });
    watch([libraryItems, () => config.value.include_libraries], () => {
      if (!Array.isArray(config.value.include_libraries)) return;
      const filtered = config.value.include_libraries.filter((item) => selectedLibraryValues.value.has(String(item)));
      if (filtered.length !== config.value.include_libraries.length) config.value.include_libraries = filtered;
    }, { deep: true, immediate: true });
    const titlePlaceholder = titleConfigReference;
    const selectedCustomTemplateId = ref(
      config.value.custom_static_active_id ?? null
    );
    const prefersDark = ref(false);
    const hostThemeVersion = ref(0);
    let configThemeMediaQuery = null;
    let configThemeObserver = null;
    function readExplicitHostTheme() {
      if (typeof document === "undefined") return "";
      const root = document.documentElement;
      const body = document.body;
      if (root.classList.contains("dark") || body?.classList.contains("v-theme--dark") || root.getAttribute("data-theme") === "dark" || body?.getAttribute("data-theme") === "dark") {
        return "dark";
      }
      if (root.classList.contains("light") || body?.classList.contains("v-theme--light") || root.getAttribute("data-theme") === "light" || body?.getAttribute("data-theme") === "light") {
        return "light";
      }
      return "";
    }
    function syncSystemTheme(event) {
      if (event) {
        prefersDark.value = event.matches;
        return;
      }
      prefersDark.value = typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    const isDark = computed(() => {
      hostThemeVersion.value;
      const explicitTheme = readExplicitHostTheme();
      return explicitTheme === "dark" || prefersDark.value;
    });
    function createLayoutId() {
      return `layout_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
    }
    function cloneLayout(layout) {
      return {
        version: layout.version,
        layers: layout.layers.map((layer) => ({ ...layer }))
      };
    }
    function getCustomTemplates() {
      return config.value.custom_static_layouts || [];
    }
    function setCustomTemplates(list) {
      config.value.custom_static_layouts = list;
    }
    computed(
      () => getCustomTemplates().map((tpl) => ({
        title: tpl.name,
        value: tpl.id
      }))
    );
    function createDefaultLayout() {
      const width = 1920;
      const height = 1080;
      const imageWidth = width * 0.6;
      const imageHeight = height * 0.8;
      return {
        version: 1,
        layers: [
          {
            id: createLayoutId(),
            type: "image",
            sourceIndex: 1,
            x: width * 0.35,
            y: height * 0.1,
            width: imageWidth,
            height: imageHeight,
            rotation: 0,
            radius: 32,
            zIndex: 1
          },
          {
            id: createLayoutId(),
            type: "main_title",
            x: width * 0.05,
            y: height * 0.25,
            width: width * 0.3,
            height: height * 0.2,
            rotation: 0,
            radius: 0,
            zIndex: 2,
            fontSize: 180
          },
          {
            id: createLayoutId(),
            type: "subtitle",
            x: width * 0.05,
            y: height * 0.5,
            width: width * 0.3,
            height: height * 0.15,
            rotation: 0,
            radius: 0,
            zIndex: 2,
            fontSize: 75
          }
        ]
      };
    }
    function ensureCustomTemplateInitialized() {
      if (config.value.cover_style_base !== "custom_static") return;
      const list = getCustomTemplates();
      if (!list.length) {
        const baseLayout = config.value.custom_static_layout || createDefaultLayout();
        const id = createLayoutId();
        const tpl = {
          id,
          name: "默认方案",
          layout: cloneLayout(baseLayout),
          baseStyle: config.value.cover_style_base || "static_1"
        };
        setCustomTemplates([tpl]);
        selectedCustomTemplateId.value = id;
        config.value.custom_static_active_id = id;
        config.value.custom_static_layout = cloneLayout(baseLayout);
        return;
      }
      if (!selectedCustomTemplateId.value) {
        const id = config.value.custom_static_active_id || list[0].id;
        selectedCustomTemplateId.value = id;
        config.value.custom_static_active_id = id;
      }
      if (!config.value.custom_static_layout) {
        const current = list.find((tpl) => tpl.id === selectedCustomTemplateId.value) || list[0];
        config.value.custom_static_layout = cloneLayout(current.layout);
      }
    }
    watch(
      () => config.value.cover_style_base,
      (base) => {
        if (base === "custom_static") {
          ensureCustomTemplateInitialized();
        }
      },
      { immediate: true }
    );
    watch(selectedCustomTemplateId, (id) => {
      config.value.custom_static_active_id = id;
      if (!id) return;
      const list = getCustomTemplates();
      const tpl = list.find((t) => t.id === id);
      if (tpl) {
        config.value.custom_static_layout = cloneLayout(tpl.layout);
      }
    });
    onMounted(() => {
      if (typeof window !== "undefined") {
        configAutoSaveEnabled.value = Boolean(config.value.auto_save_config);
        config.value.auto_save_config = configAutoSaveEnabled.value;
        syncSystemTheme();
        configThemeMediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
        configThemeMediaQuery.addEventListener?.("change", syncSystemTheme);
      }
      if (typeof document !== "undefined") {
        configThemeObserver = new MutationObserver(() => {
          hostThemeVersion.value += 1;
        });
        configThemeObserver.observe(document.documentElement, {
          attributes: true,
          attributeFilter: ["class", "data-theme"]
        });
        if (document.body) {
          configThemeObserver.observe(document.body, {
            attributes: true,
            attributeFilter: ["class", "data-theme"]
          });
        }
      }
      void loadDynamicLibraryOptions();
      void loadFontLibrary();
      void loadBackupLibrary();
      void validateTitleConfig(false);
      nextTick(() => {
        suppressConfigAutoSave = false;
      });
    });
    onBeforeUnmount(() => {
      stopGenerationStatusPoller();
      if (titleConfigValidationTimer !== null && typeof window !== "undefined") {
        window.clearTimeout(titleConfigValidationTimer);
      }
      if (configAutoSaveTimer !== null && typeof window !== "undefined") {
        window.clearTimeout(configAutoSaveTimer);
        configAutoSaveTimer = null;
      }
      if (configSaveMessageTimer !== null && typeof window !== "undefined") {
        window.clearTimeout(configSaveMessageTimer);
        configSaveMessageTimer = null;
      }
      configThemeMediaQuery?.removeEventListener?.("change", syncSystemTheme);
      configThemeObserver?.disconnect();
      configThemeMediaQuery = null;
      configThemeObserver = null;
    });
    function onConfigAutoSaveSwitch(value) {
      configAutoSaveEnabled.value = Boolean(value);
      config.value.auto_save_config = configAutoSaveEnabled.value;
      if (configAutoSaveEnabled.value) scheduleConfigAutoSave(200);
    }
    function scheduleConfigAutoSave(delay = 1200) {
      configAutoSaveEnabled.value = Boolean(config.value.auto_save_config);
      if (!configAutoSaveEnabled.value || suppressConfigAutoSave || configSaving.value || typeof window === "undefined") return;
      if (configAutoSaveTimer !== null) window.clearTimeout(configAutoSaveTimer);
      configAutoSaveTimer = window.setTimeout(() => {
        configAutoSaveTimer = null;
        void saveConfig({ auto: true });
      }, delay);
    }
    function showConfigSaveMessage(message) {
      configSaveMessage.value = message;
      if (typeof window === "undefined") return;
      if (configSaveMessageTimer !== null) window.clearTimeout(configSaveMessageTimer);
      configSaveMessageTimer = window.setTimeout(() => {
        configSaveMessage.value = "";
        configSaveMessageTimer = null;
      }, 2600);
    }
    async function saveConfig(options = {}) {
      if (configSaving.value) return false;
      configSaving.value = true;
      const titleConfigOk = await validateTitleConfig(true);
      if (!titleConfigOk) {
        if (!options.auto) tab.value = "title-tab";
        configSaving.value = false;
        return false;
      }
      try {
        config.value.update_now = false;
        config.value.main_title_font_custom = "";
        config.value.subtitle_font_custom = "";
        config.value.custom_text_font_custom = "";
        config.value.backup_enabled = Boolean(String(config.value.backup_cron || "").trim());
        if (config.value.transfer_monitor && config.value.lock_latest_sort) {
          config.value.sort_by = "DateCreated";
        }
        const resp = await props.api.post(
          "plugin/YahahaCoverStudio/save_config",
          config.value
        );
        if (!resp || resp.code !== 0) {
          throw new Error(resp?.msg || "保存配置失败");
        }
        if (resp.data?.config) {
          suppressConfigAutoSave = true;
          config.value = {
            ...defaults,
            ...normalizeConfigInput(resp.data.config)
          };
          nextTick(() => {
            suppressConfigAutoSave = false;
          });
        }
        showConfigSaveMessage(options.auto ? "已自动保存" : "已保存");
        return true;
      } catch (error) {
        console.warn("save config failed", error);
        showConfigSaveMessage(error instanceof Error ? error.message : "保存配置失败");
        return false;
      } finally {
        if (typeof window !== "undefined") {
          window.setTimeout(() => {
            configSaving.value = false;
          }, 420);
        } else {
          configSaving.value = false;
        }
      }
    }
    function initializePluginConfig() {
      if (typeof window !== "undefined") {
        const confirmed = window.confirm("初始化插件会将当前表单恢复为默认配置，已上传字体、备份、历史封面和图片目录文件不会被删除。保存配置后生效。");
        if (!confirmed) return;
      }
      const current = config.value;
      config.value = {
        ...defaults,
        all_servers: current.all_servers || [],
        all_libraries: current.all_libraries || [],
        page_tab: current.page_tab || defaults.page_tab,
        custom_static_layout: current.custom_static_layout ?? defaults.custom_static_layout,
        custom_static_layouts: current.custom_static_layouts ?? defaults.custom_static_layouts,
        custom_static_active_id: current.custom_static_active_id ?? defaults.custom_static_active_id
      };
      backupResult.value = "已恢复默认配置，点击保存配置后生效";
      tab.value = "basic-tab";
    }
    function resolveRequestedCoverStyle() {
      const base = config.value.cover_style_base || "static_1";
      if (base === "custom_static") return "custom_static";
      const suffix = String(base).split("_")[1] || "1";
      return config.value.cover_style_variant === "animated" ? `animated_${suffix}` : `static_${suffix}`;
    }
    async function startGeneration() {
      if (generatingNow.value || isGenerating.value) return;
      generatingNow.value = true;
      try {
        config.value.update_now = false;
        const style = resolveRequestedCoverStyle();
        const resp = await props.api.post(
          `plugin/YahahaCoverStudio/start_generation?style=${encodeURIComponent(style)}`
        );
        if (resp && resp.code !== 0) {
          throw new Error(resp.msg || "start_generation failed");
        }
        isGenerating.value = true;
        generationCurrent.value = 0;
        generationTotal.value = 0;
        generationLabel.value = "准备生成";
        startGenerationStatusPoller();
        await loadDynamicLibraryOptions();
      } catch (e) {
        console.error("config start_generation failed", e);
      } finally {
        generatingNow.value = false;
      }
    }
    async function stopGeneration() {
      if (generatingNow.value) return;
      generatingNow.value = true;
      try {
        const resp = await props.api.post(
          "plugin/YahahaCoverStudio/stop_generation"
        );
        if (resp && resp.code !== 0) {
          throw new Error(resp.msg || "stop_generation failed");
        }
        await loadDynamicLibraryOptions();
      } catch (e) {
        console.error("config stop_generation failed", e);
      } finally {
        generatingNow.value = false;
      }
    }
    async function handleGenerateAction() {
      if (isGenerating.value) {
        await stopGeneration();
        return;
      }
      await startGeneration();
    }
    function notifySwitch() {
      emit("switch");
    }
    function notifyClose() {
      emit("close");
    }
    async function onCleanImages() {
      if (cacheAction.value) return;
      cacheAction.value = "images";
      try {
        await props.api.post("plugin/YahahaCoverStudio/clean_images");
      } catch (e) {
        console.error("clean_images failed", e);
      } finally {
        cacheAction.value = "";
      }
    }
    async function onCleanFonts() {
      if (cacheAction.value) return;
      cacheAction.value = "fonts";
      try {
        await props.api.post("plugin/YahahaCoverStudio/clean_fonts");
      } catch (e) {
        console.error("clean_fonts failed", e);
      } finally {
        cacheAction.value = "";
      }
    }
    async function onBackupConfig() {
      if (cacheAction.value) return;
      cacheAction.value = "backup";
      backupResult.value = "";
      try {
        const resp = await props.api.post(
          "plugin/YahahaCoverStudio/backup_config",
          { backup_path: config.value.backup_path || "" }
        );
        if (!resp || resp.code !== 0) {
          throw new Error(resp?.msg || "backup_config failed");
        }
        backupResult.value = resp.data?.path ? `已备份到 ${resp.data.path}` : "已完成备份";
        await loadBackupLibrary();
      } catch (e) {
        console.error("backup_config failed", e);
        backupResult.value = "备份失败，请检查路径权限";
      } finally {
        cacheAction.value = "";
      }
    }
    function downloadConfigBinaryPayload(payload, fallbackName) {
      if (!payload?.b64 || typeof window === "undefined") {
        throw new Error("download payload missing");
      }
      const binary = window.atob(payload.b64);
      const bytes = new Uint8Array(binary.length);
      for (let index = 0; index < binary.length; index += 1) {
        bytes[index] = binary.charCodeAt(index);
      }
      const blob = new Blob([bytes], { type: payload.mime || "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = payload.name || fallbackName;
      anchor.rel = "noopener";
      anchor.style.position = "fixed";
      anchor.style.left = "-9999px";
      anchor.style.top = "0";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    }
    async function downloadBackupItem(item) {
      try {
        const backupKey = encodeURIComponent(item.path || item.name);
        const resp = await props.api.post(`plugin/YahahaCoverStudio/download_backup?file=${backupKey}`);
        if (!resp || resp.code !== 0) {
          throw new Error(resp?.msg || "download_backup failed");
        }
        downloadConfigBinaryPayload(resp.data, item.name || "yahahacoverstudio_backup.json");
      } catch (error) {
        console.warn("download backup failed", error);
        backupResult.value = "下载备份失败";
      }
    }
    async function uploadBackupFile(file) {
      if (cacheAction.value) return;
      cacheAction.value = "backup";
      backupResult.value = "";
      try {
        const dataUrl = await readFileAsDataUrl(file);
        const resp = await props.api.post("plugin/YahahaCoverStudio/upload_backup", {
          data_url: dataUrl,
          name: file.name
        });
        if (!resp || resp.code !== 0) {
          throw new Error(resp?.msg || "upload_backup failed");
        }
        backupResult.value = "备份文件已上传";
        await loadBackupLibrary();
      } catch (error) {
        console.warn("upload backup failed", error);
        backupResult.value = "上传备份失败";
      } finally {
        cacheAction.value = "";
      }
    }
    function onBackupFileInputChange(event) {
      const input = event.target;
      const file = input.files?.[0];
      input.value = "";
      if (file) {
        void uploadBackupFile(file);
      }
    }
    async function restoreBackupItem(item) {
      if (cacheAction.value) return;
      if (typeof window !== "undefined" && !window.confirm(`确定从「${item.name}」恢复配置吗？当前配置会被覆盖。`)) return;
      cacheAction.value = "backup";
      backupResult.value = "";
      try {
        const resp = await props.api.post(
          `plugin/YahahaCoverStudio/restore_backup?file=${encodeURIComponent(item.path || item.name)}`
        );
        if (!resp || resp.code !== 0) {
          throw new Error(resp?.msg || "restore_backup failed");
        }
        if (resp.data?.config) {
          config.value = {
            ...defaults,
            ...normalizeConfigInput(resp.data.config)
          };
        }
        backupResult.value = "配置已恢复";
        await Promise.all([loadDynamicLibraryOptions(), loadFontLibrary(), loadBackupLibrary()]);
      } catch (error) {
        console.warn("restore backup failed", error);
        backupResult.value = "恢复备份失败";
      } finally {
        cacheAction.value = "";
      }
    }
    async function deleteBackupItem(item) {
      if (cacheAction.value) return;
      if (typeof window !== "undefined" && !window.confirm(`删除备份「${item.name}」？`)) return;
      cacheAction.value = "backup";
      backupResult.value = "";
      try {
        const resp = await props.api.post(
          `plugin/YahahaCoverStudio/delete_backup?file=${encodeURIComponent(item.path || item.name)}`
        );
        if (!resp || resp.code !== 0) {
          throw new Error(resp?.msg || "delete_backup failed");
        }
        backupResult.value = "备份已删除";
        await loadBackupLibrary();
      } catch (error) {
        console.warn("delete backup failed", error);
        backupResult.value = "删除备份失败";
      } finally {
        cacheAction.value = "";
      }
    }
    return (_ctx, _cache) => {
      const _component_v_icon = _resolveComponent("v-icon");
      const _component_v_btn = _resolveComponent("v-btn");
      const _component_v_switch = _resolveComponent("v-switch");
      const _component_v_col = _resolveComponent("v-col");
      const _component_v_row = _resolveComponent("v-row");
      const _component_v_card_text = _resolveComponent("v-card-text");
      const _component_v_window_item = _resolveComponent("v-window-item");
      const _component_v_window = _resolveComponent("v-window");
      const _component_v_defaults_provider = _resolveComponent("v-defaults-provider");
      const _component_v_card = _resolveComponent("v-card");
      return _openBlock(), _createElementBlock("div", {
        class: "mcr-shell mcr-config-shell",
        "data-mcr-theme": isDark.value ? "dark" : "light"
      }, [
        _cache[57] || (_cache[57] = _createElementVNode("div", { class: "mcr-shell__aurora" }, null, -1)),
        _cache[58] || (_cache[58] = _createElementVNode("div", { class: "mcr-shell__noise" }, null, -1)),
        _createVNode(_component_v_card, { class: "mcr-frame" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_defaults_provider, { defaults: _unref(controlDefaults) }, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_2, [
                  _createElementVNode("header", _hoisted_3, [
                    _cache[28] || (_cache[28] = _createElementVNode("div", { class: "mcr-config-brand" }, [
                      _createElementVNode("h1", {
                        class: "yh-settings-title-wrap",
                        "aria-label": "配置 Configuration"
                      }, [
                        _createElementVNode("span", { class: "yh-settings-en" }, "Configuration"),
                        _createElementVNode("span", { class: "yh-settings-zh" }, "配置")
                      ])
                    ], -1)),
                    _createElementVNode("div", _hoisted_4, [
                      _createElementVNode("div", _hoisted_5, [
                        _createElementVNode("button", {
                          type: "button",
                          class: _normalizeClass(["yh-run-btn", { "is-running": isGenerating.value }]),
                          style: _normalizeStyle(configRunButtonProgressStyle.value),
                          title: isGenerating.value ? configGenerationProgressLabel.value : "立即生成",
                          "aria-label": isGenerating.value ? configGenerationProgressLabel.value : "立即生成",
                          disabled: generatingNow.value,
                          onClick: handleGenerateAction
                        }, [
                          _cache[25] || (_cache[25] = _createElementVNode("span", {
                            class: "yh-run-progress",
                            "aria-hidden": "true"
                          }, null, -1)),
                          _createElementVNode("span", _hoisted_7, [
                            _createVNode(_component_v_icon, {
                              icon: isGenerating.value ? "mdi-stop-circle-outline" : "mdi-play-circle-outline",
                              size: "24"
                            }, null, 8, ["icon"]),
                            isGenerating.value ? (_openBlock(), _createElementBlock("span", _hoisted_8, "生成中")) : _createCommentVNode("", true),
                            isGenerating.value ? (_openBlock(), _createElementBlock("span", _hoisted_9, _toDisplayString(configGenerationProgressPercent.value) + "%", 1)) : _createCommentVNode("", true)
                          ])
                        ], 14, _hoisted_6),
                        _createVNode(_component_v_btn, {
                          size: "small",
                          class: "mcr-button mcr-button--ghost mcr-button--dark-neutral yh-icon-btn yh-icon-btn--save",
                          icon: "",
                          title: "保存配置",
                          "aria-label": "保存配置",
                          disabled: isGenerating.value || generatingNow.value || configSaving.value,
                          loading: configSaving.value,
                          onClick: _cache[0] || (_cache[0] = ($event) => saveConfig())
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_icon, {
                              icon: "mdi-content-save-outline",
                              size: "22"
                            })
                          ]),
                          _: 1
                        }, 8, ["disabled", "loading"]),
                        _createVNode(_component_v_btn, {
                          size: "small",
                          class: "mcr-button mcr-button--ghost mcr-button--dark-neutral yh-icon-btn",
                          icon: "",
                          title: "封面预览",
                          "aria-label": "封面预览",
                          disabled: isGenerating.value || generatingNow.value,
                          onClick: notifySwitch
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_icon, {
                              icon: "mdi-image-multiple-outline",
                              size: "22"
                            })
                          ]),
                          _: 1
                        }, 8, ["disabled"]),
                        _createVNode(_component_v_btn, {
                          size: "small",
                          class: "mcr-button mcr-button--ghost mcr-button--dark-neutral yh-icon-btn",
                          icon: "",
                          title: "关闭",
                          "aria-label": "关闭",
                          onClick: notifyClose
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_icon, {
                              icon: "mdi-close",
                              size: "22"
                            })
                          ]),
                          _: 1
                        })
                      ]),
                      _createElementVNode("div", _hoisted_10, [
                        _createElementVNode("span", _hoisted_11, [
                          _cache[26] || (_cache[26] = _createElementVNode("span", null, "状态", -1)),
                          _createElementVNode("strong", null, _toDisplayString(config.value.enabled ? "启用" : "停用"), 1)
                        ]),
                        _createElementVNode("span", _hoisted_12, [
                          _cache[27] || (_cache[27] = _createElementVNode("span", null, "调度", -1)),
                          _createElementVNode("strong", null, _toDisplayString(scheduleModeLabel.value), 1)
                        ])
                      ]),
                      _createElementVNode("div", _hoisted_13, [
                        (_openBlock(), _createElementBlock(_Fragment, null, _renderList(tabItems, (item) => {
                          return _createElementVNode("button", {
                            key: `top-${item.value}`,
                            type: "button",
                            class: _normalizeClass(["mcr-config-top-tab yh-segment-item", { "is-active": tab.value === item.value }]),
                            role: "tab",
                            "aria-selected": tab.value === item.value,
                            onClick: ($event) => tab.value = item.value
                          }, [
                            _createVNode(_component_v_icon, {
                              icon: item.icon,
                              size: "18"
                            }, null, 8, ["icon"]),
                            _createElementVNode("span", null, _toDisplayString(item.title), 1)
                          ], 10, _hoisted_14);
                        }), 64))
                      ])
                    ])
                  ]),
                  _createElementVNode("div", _hoisted_15, [
                    _createElementVNode("aside", _hoisted_16, [
                      _cache[29] || (_cache[29] = _createElementVNode("div", { class: "mcr-config-sidebar__label" }, "Sections", -1)),
                      (_openBlock(), _createElementBlock(_Fragment, null, _renderList(tabItems, (item) => {
                        return _createElementVNode("button", {
                          key: item.value,
                          type: "button",
                          class: _normalizeClass(["mcr-config-nav", { "mcr-config-nav--active": tab.value === item.value }]),
                          role: "tab",
                          "aria-selected": tab.value === item.value,
                          onClick: ($event) => tab.value = item.value
                        }, [
                          _createVNode(_component_v_icon, {
                            icon: item.icon,
                            size: "22"
                          }, null, 8, ["icon"]),
                          _createElementVNode("span", null, _toDisplayString(item.title), 1)
                        ], 10, _hoisted_17);
                      }), 64)),
                      _cache[30] || (_cache[30] = _createElementVNode("div", { class: "mcr-config-sidebar__spacer" }, null, -1))
                    ]),
                    _createElementVNode("main", {
                      ref_key: "settingsContentEl",
                      ref: settingsContentEl,
                      class: "mcr-config-main"
                    }, [
                      tab.value === "basic-tab" ? (_openBlock(), _createBlock(SettingsAnchorNav, {
                        key: 0,
                        sections: settingsAnchorSections,
                        "content-element": settingsContentEl.value,
                        "top-offset": 96,
                        theme: isDark.value ? "dark" : "light"
                      }, null, 8, ["content-element", "theme"])) : _createCommentVNode("", true),
                      _createVNode(_component_v_window, {
                        modelValue: tab.value,
                        "onUpdate:modelValue": _cache[24] || (_cache[24] = ($event) => tab.value = $event)
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_window_item, { value: "basic-tab" }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_card_text, { class: "mcr-panel__body mcr-config-tabbody mcr-config-section-stack" }, {
                                default: _withCtx(() => [
                                  _createElementVNode("section", _hoisted_18, [
                                    _cache[31] || (_cache[31] = _createElementVNode("header", { class: "mcr-config-section-card__header" }, [
                                      _createElementVNode("div", null, [
                                        _createElementVNode("div", { class: "mcr-config-section-card__title" }, "运行与定时"),
                                        _createElementVNode("p", { class: "mcr-config-section-card__copy" }, "控制插件开关和自动更新周期。")
                                      ])
                                    ], -1)),
                                    _createVNode(_component_v_row, {
                                      class: "mcr-form-grid mcr-form-grid--center",
                                      align: "center"
                                    }, {
                                      default: _withCtx(() => [
                                        _createVNode(_component_v_col, {
                                          cols: "12",
                                          md: "4",
                                          class: "mcr-config-switch-col"
                                        }, {
                                          default: _withCtx(() => [
                                            _createElementVNode("div", _hoisted_19, [
                                              _createVNode(_component_v_switch, {
                                                modelValue: config.value.enabled,
                                                "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => config.value.enabled = $event),
                                                label: "启用插件",
                                                "hide-details": ""
                                              }, null, 8, ["modelValue"]),
                                              _createVNode(_component_v_switch, {
                                                modelValue: config.value.auto_save_config,
                                                "onUpdate:modelValue": [
                                                  _cache[2] || (_cache[2] = ($event) => config.value.auto_save_config = $event),
                                                  onConfigAutoSaveSwitch
                                                ],
                                                label: "自动保存配置",
                                                "hide-details": ""
                                              }, null, 8, ["modelValue"])
                                            ])
                                          ]),
                                          _: 1
                                        }),
                                        _createVNode(_component_v_col, {
                                          cols: "12",
                                          md: "8"
                                        }, {
                                          default: _withCtx(() => [
                                            _createVNode(BlueprintField, {
                                              modelValue: config.value.cron,
                                              "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => config.value.cron = $event),
                                              label: "定时更新",
                                              placeholder: "* * * * *",
                                              hint: "留空则不启用定时任务，使用 5 位 cron 表达式"
                                            }, null, 8, ["modelValue"])
                                          ]),
                                          _: 1
                                        })
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _createElementVNode("section", _hoisted_20, [
                                    _cache[32] || (_cache[32] = _createElementVNode("header", { class: "mcr-config-section-card__header" }, [
                                      _createElementVNode("div", null, [
                                        _createElementVNode("div", { class: "mcr-config-section-card__title" }, "入库监控"),
                                        _createElementVNode("p", { class: "mcr-config-section-card__copy" }, "媒体入库后自动更新所在媒体库封面。")
                                      ])
                                    ], -1)),
                                    _createVNode(_component_v_row, {
                                      class: "mcr-form-grid mcr-form-grid--center mcr-monitor-grid",
                                      align: "center"
                                    }, {
                                      default: _withCtx(() => [
                                        _createVNode(_component_v_col, {
                                          cols: "12",
                                          md: "3",
                                          class: "mcr-config-switch-col"
                                        }, {
                                          default: _withCtx(() => [
                                            _createVNode(_component_v_switch, {
                                              modelValue: config.value.transfer_monitor,
                                              "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => config.value.transfer_monitor = $event),
                                              label: "入库监控",
                                              "hide-details": ""
                                            }, null, 8, ["modelValue"])
                                          ]),
                                          _: 1
                                        }),
                                        _createVNode(_component_v_col, {
                                          cols: "12",
                                          md: "3"
                                        }, {
                                          default: _withCtx(() => [
                                            _createVNode(BlueprintSelect, {
                                              modelValue: config.value.monitor_source,
                                              "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => config.value.monitor_source = $event),
                                              items: monitorSourceItems,
                                              label: "监控来源",
                                              hint: "MP 事件方便，Emby Webhook 更精准",
                                              disabled: !config.value.transfer_monitor
                                            }, null, 8, ["modelValue", "disabled"])
                                          ]),
                                          _: 1
                                        }),
                                        _createVNode(_component_v_col, {
                                          cols: "12",
                                          md: "3",
                                          class: "mcr-config-switch-col"
                                        }, {
                                          default: _withCtx(() => [
                                            _createVNode(_component_v_switch, {
                                              modelValue: config.value.lock_latest_sort,
                                              "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => config.value.lock_latest_sort = $event),
                                              label: "按最新入库排序",
                                              "hide-details": "",
                                              disabled: !config.value.transfer_monitor
                                            }, null, 8, ["modelValue", "disabled"])
                                          ]),
                                          _: 1
                                        }),
                                        _createVNode(_component_v_col, {
                                          cols: "12",
                                          md: "3"
                                        }, {
                                          default: _withCtx(() => [
                                            _createVNode(BlueprintField, {
                                              modelValue: config.value.delay,
                                              "onUpdate:modelValue": _cache[7] || (_cache[7] = ($event) => config.value.delay = $event),
                                              modelModifiers: { number: true },
                                              type: "number",
                                              label: "入库延迟（秒）",
                                              placeholder: "60",
                                              hint: "根据实际扫描速度调整延迟时间"
                                            }, null, 8, ["modelValue"])
                                          ]),
                                          _: 1
                                        })
                                      ]),
                                      _: 1
                                    }),
                                    _cache[33] || (_cache[33] = _createElementVNode("p", { class: "yh-field-hint yh-monitor-hint" }, [
                                      _createTextVNode(" 开启后会在媒体入库时自动更新所在媒体库封面。"),
                                      _createElementVNode("br"),
                                      _createTextVNode(" 如开启「按最新入库排序」，预览页中的来源排序将被锁定，不可手动修改。 "),
                                      _createElementVNode("br"),
                                      _createTextVNode(" 使用 Emby 入库监控时，需要手动配置媒体服务器 Webhook，回调相对路径为 "),
                                      _createElementVNode("code", null, "/api/v1/webhook?token=API_TOKEN&source=媒体服务器名"),
                                      _createTextVNode("（3001 端口），其中 "),
                                      _createElementVNode("code", null, "API_TOKEN"),
                                      _createTextVNode(" 为设置中的 API_TOKEN。Emby 需要在通知中勾选「媒体库 -> 新媒体已添加」。 Jellyfin 的通知配置方式暂未确认。 ")
                                    ], -1))
                                  ]),
                                  _createElementVNode("section", _hoisted_21, [
                                    _cache[34] || (_cache[34] = _createElementVNode("header", { class: "mcr-config-section-card__header" }, [
                                      _createElementVNode("div", null, [
                                        _createElementVNode("div", { class: "mcr-config-section-card__title" }, "媒体库范围"),
                                        _createElementVNode("p", { class: "mcr-config-section-card__copy" }, "限定参与封面更新的服务器与媒体库。")
                                      ])
                                    ], -1)),
                                    _createVNode(_component_v_row, { class: "mcr-form-grid" }, {
                                      default: _withCtx(() => [
                                        _createVNode(_component_v_col, {
                                          cols: "12",
                                          md: "6"
                                        }, {
                                          default: _withCtx(() => [
                                            _createVNode(BlueprintSelect, {
                                              modelValue: config.value.selected_servers,
                                              "onUpdate:modelValue": _cache[8] || (_cache[8] = ($event) => config.value.selected_servers = $event),
                                              items: serverItems.value,
                                              multiple: "",
                                              clearable: "",
                                              label: "媒体服务器",
                                              hint: "不勾选时默认更新所有已连接服务器"
                                            }, null, 8, ["modelValue", "items"])
                                          ]),
                                          _: 1
                                        }),
                                        _createVNode(_component_v_col, {
                                          cols: "12",
                                          md: "6"
                                        }, {
                                          default: _withCtx(() => [
                                            _createVNode(BlueprintSelect, {
                                              modelValue: config.value.include_libraries,
                                              "onUpdate:modelValue": _cache[9] || (_cache[9] = ($event) => config.value.include_libraries = $event),
                                              items: libraryItems.value,
                                              multiple: "",
                                              clearable: "",
                                              label: "更新媒体库",
                                              hint: "默认更新全部，或只更新勾选的媒体库"
                                            }, null, 8, ["modelValue", "items"])
                                          ]),
                                          _: 1
                                        })
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _createElementVNode("section", _hoisted_22, [
                                    _cache[35] || (_cache[35] = _createElementVNode("header", { class: "mcr-config-section-card__header" }, [
                                      _createElementVNode("div", null, [
                                        _createElementVNode("div", { class: "mcr-config-section-card__title" }, "自定义图片目录"),
                                        _createElementVNode("p", { class: "mcr-config-section-card__copy" }, "优先使用指定目录中的真实素材生成封面。")
                                      ])
                                    ], -1)),
                                    _createVNode(BlueprintField, {
                                      modelValue: config.value.covers_input,
                                      "onUpdate:modelValue": _cache[10] || (_cache[10] = ($event) => config.value.covers_input = $event),
                                      label: "自定义图片目录",
                                      hint: "图片放在与媒体库同名的文件夹下；留空则使用媒体服务器素材"
                                    }, null, 8, ["modelValue"])
                                  ]),
                                  _createElementVNode("section", _hoisted_23, [
                                    _cache[36] || (_cache[36] = _createElementVNode("header", { class: "mcr-config-section-card__header" }, [
                                      _createElementVNode("div", null, [
                                        _createElementVNode("div", { class: "mcr-config-section-card__title" }, "历史封面"),
                                        _createElementVNode("p", { class: "mcr-config-section-card__copy" }, "按生成批次保留封面，用于时光机恢复。")
                                      ])
                                    ], -1)),
                                    _createVNode(_component_v_row, {
                                      class: "mcr-form-grid mcr-form-grid--center",
                                      align: "center"
                                    }, {
                                      default: _withCtx(() => [
                                        _createVNode(_component_v_col, {
                                          cols: "12",
                                          md: "3",
                                          class: "mcr-config-switch-col"
                                        }, {
                                          default: _withCtx(() => [
                                            _createVNode(_component_v_switch, {
                                              modelValue: config.value.save_recent_covers,
                                              "onUpdate:modelValue": _cache[11] || (_cache[11] = ($event) => config.value.save_recent_covers = $event),
                                              label: "保存历史封面",
                                              "hide-details": ""
                                            }, null, 8, ["modelValue"])
                                          ]),
                                          _: 1
                                        }),
                                        _createVNode(_component_v_col, {
                                          cols: "12",
                                          md: "5"
                                        }, {
                                          default: _withCtx(() => [
                                            _createVNode(BlueprintField, {
                                              modelValue: config.value.history_retention_batches,
                                              "onUpdate:modelValue": _cache[12] || (_cache[12] = ($event) => config.value.history_retention_batches = $event),
                                              modelModifiers: { number: true },
                                              type: "number",
                                              label: "所有批次的上限",
                                              hint: "默认保留最近 30 个完整批次"
                                            }, null, 8, ["modelValue"])
                                          ]),
                                          _: 1
                                        })
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _createElementVNode("section", _hoisted_24, [
                                    _cache[41] || (_cache[41] = _createElementVNode("header", { class: "mcr-config-section-card__header" }, [
                                      _createElementVNode("div", null, [
                                        _createElementVNode("div", { class: "mcr-config-section-card__title" }, "字体库"),
                                        _createElementVNode("p", { class: "mcr-config-section-card__copy" }, "设置标题与自定义文本字体，管理上传字体。")
                                      ])
                                    ], -1)),
                                    _createVNode(_component_v_row, { class: "mcr-form-grid" }, {
                                      default: _withCtx(() => [
                                        _createVNode(_component_v_col, {
                                          cols: "12",
                                          md: "4"
                                        }, {
                                          default: _withCtx(() => [
                                            _createVNode(BlueprintSelect, {
                                              modelValue: config.value.main_title_font_preset,
                                              "onUpdate:modelValue": _cache[13] || (_cache[13] = ($event) => config.value.main_title_font_preset = $event),
                                              items: mainTitleFontItems.value,
                                              label: "主标题字体"
                                            }, null, 8, ["modelValue", "items"])
                                          ]),
                                          _: 1
                                        }),
                                        _createVNode(_component_v_col, {
                                          cols: "12",
                                          md: "4"
                                        }, {
                                          default: _withCtx(() => [
                                            _createVNode(BlueprintSelect, {
                                              modelValue: config.value.subtitle_font_preset,
                                              "onUpdate:modelValue": _cache[14] || (_cache[14] = ($event) => config.value.subtitle_font_preset = $event),
                                              items: subtitleFontItems.value,
                                              label: "副标题字体"
                                            }, null, 8, ["modelValue", "items"])
                                          ]),
                                          _: 1
                                        }),
                                        _createVNode(_component_v_col, {
                                          cols: "12",
                                          md: "4"
                                        }, {
                                          default: _withCtx(() => [
                                            _createVNode(BlueprintSelect, {
                                              modelValue: config.value.custom_text_font_preset,
                                              "onUpdate:modelValue": _cache[15] || (_cache[15] = ($event) => config.value.custom_text_font_preset = $event),
                                              items: subtitleFontItems.value,
                                              label: "自定义文本字体"
                                            }, null, 8, ["modelValue", "items"])
                                          ]),
                                          _: 1
                                        })
                                      ]),
                                      _: 1
                                    }),
                                    _createElementVNode("input", {
                                      ref_key: "fontFileInputEl",
                                      ref: fontFileInputEl,
                                      class: "mcr-font-file-input",
                                      type: "file",
                                      accept: ".ttf,.ttc,.otf,.woff,.woff2,font/*",
                                      onChange: onFontFileInputChange
                                    }, null, 544),
                                    _createElementVNode("div", _hoisted_25, [
                                      _createElementVNode("div", _hoisted_26, [
                                        _cache[38] || (_cache[38] = _createElementVNode("div", null, [
                                          _createElementVNode("div", { class: "mcr-panel__eyebrow" }, "Font Library"),
                                          _createElementVNode("div", { class: "mcr-panel__title mcr-font-library__title" }, "自定义字体库")
                                        ], -1)),
                                        _createVNode(_component_v_btn, {
                                          size: "small",
                                          class: "mcr-button mcr-button--ghost mcr-button--dark-neutral",
                                          "prepend-icon": "mdi-upload-outline",
                                          disabled: fontLibraryLoading.value,
                                          onClick: openFontFilePicker
                                        }, {
                                          default: _withCtx(() => [..._cache[37] || (_cache[37] = [
                                            _createTextVNode(" 上传字体 ", -1)
                                          ])]),
                                          _: 1
                                        }, 8, ["disabled"])
                                      ]),
                                      _createElementVNode("div", _hoisted_27, [
                                        _createElementVNode("label", _hoisted_28, [
                                          _cache[39] || (_cache[39] = _createElementVNode("span", { class: "mcr-blueprint-field__label" }, "网络字体链接", -1)),
                                          _createElementVNode("span", _hoisted_29, [
                                            _withDirectives(_createElementVNode("input", {
                                              "onUpdate:modelValue": _cache[16] || (_cache[16] = ($event) => fontUrlInput.value = $event),
                                              class: "mcr-blueprint-field__control mcr-font-link-field__input",
                                              type: "url",
                                              placeholder: "https://example.com/font.woff2"
                                            }, null, 512), [
                                              [_vModelText, fontUrlInput.value]
                                            ]),
                                            fontUrlInput.value.trim() ? (_openBlock(), _createElementBlock("button", {
                                              key: 0,
                                              type: "button",
                                              class: "mcr-font-link-field__download",
                                              disabled: fontLibraryLoading.value,
                                              title: "下载字体",
                                              "aria-label": "下载字体",
                                              onClick: _withModifiers(uploadFontUrl, ["prevent"])
                                            }, [
                                              _createVNode(_component_v_icon, {
                                                icon: "mdi-download",
                                                size: "18"
                                              })
                                            ], 8, _hoisted_30)) : _createCommentVNode("", true)
                                          ]),
                                          _cache[40] || (_cache[40] = _createElementVNode("span", { class: "mcr-blueprint-field__hint" }, "支持 ttf / ttc / otf / woff / woff2，导入后保存到插件数据目录", -1))
                                        ])
                                      ]),
                                      _createElementVNode("div", _hoisted_31, [
                                        _createElementVNode("button", {
                                          type: "button",
                                          class: "mcr-config-collapse-button",
                                          onClick: _cache[17] || (_cache[17] = ($event) => fontLibraryExpanded.value = !fontLibraryExpanded.value)
                                        }, [
                                          _createVNode(_component_v_icon, {
                                            icon: fontLibraryExpanded.value ? "mdi-chevron-up" : "mdi-chevron-down",
                                            size: "18"
                                          }, null, 8, ["icon"]),
                                          _createTextVNode(" 已上传字体 " + _toDisplayString(customFontItems.value.length) + " 个 ", 1)
                                        ])
                                      ]),
                                      fontLibraryExpanded.value && fontLibraryLoading.value ? (_openBlock(), _createElementBlock("div", _hoisted_32, "正在读取字体库...")) : fontLibraryExpanded.value && !customFontItems.value.length ? (_openBlock(), _createElementBlock("div", _hoisted_33, "暂无自定义字体")) : fontLibraryExpanded.value ? (_openBlock(), _createElementBlock("div", _hoisted_34, [
                                        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(customFontItems.value, (item) => {
                                          return _openBlock(), _createElementBlock("button", {
                                            key: item.value,
                                            type: "button",
                                            class: "mcr-font-item",
                                            title: item.name,
                                            onClick: ($event) => config.value.custom_text_font_preset = item.value
                                          }, [
                                            _createElementVNode("span", {
                                              class: "mcr-font-item__sample",
                                              style: _normalizeStyle({ fontFamily: getCustomFontFamily(item) })
                                            }, "Aa 字", 4),
                                            _createElementVNode("span", _hoisted_36, _toDisplayString(item.title), 1),
                                            _createElementVNode("span", {
                                              role: "button",
                                              tabindex: "-1",
                                              class: "mcr-font-item__rename",
                                              title: "重命名字体",
                                              onClick: _withModifiers(($event) => renameFontItem(item), ["stop", "prevent"])
                                            }, [
                                              _createVNode(_component_v_icon, {
                                                icon: "mdi-pencil-outline",
                                                size: "15"
                                              })
                                            ], 8, _hoisted_37),
                                            _createElementVNode("span", {
                                              role: "button",
                                              tabindex: "-1",
                                              class: "mcr-font-item__delete",
                                              title: "删除字体",
                                              onClick: _withModifiers(($event) => deleteFontItem(item), ["stop", "prevent"])
                                            }, [
                                              _createVNode(_component_v_icon, {
                                                icon: "mdi-trash-can-outline",
                                                size: "15"
                                              })
                                            ], 8, _hoisted_38)
                                          ], 8, _hoisted_35);
                                        }), 128))
                                      ])) : _createCommentVNode("", true),
                                      fontUploadMessage.value ? (_openBlock(), _createElementBlock("div", _hoisted_39, _toDisplayString(fontUploadMessage.value), 1)) : _createCommentVNode("", true)
                                    ])
                                  ]),
                                  _createElementVNode("section", _hoisted_40, [
                                    _cache[45] || (_cache[45] = _createElementVNode("header", { class: "mcr-config-section-card__header" }, [
                                      _createElementVNode("div", null, [
                                        _createElementVNode("div", { class: "mcr-config-section-card__title" }, "备份还原"),
                                        _createElementVNode("p", { class: "mcr-config-section-card__copy" }, "备份完整配置，上传恢复文件，或初始化当前插件配置。")
                                      ])
                                    ], -1)),
                                    _createElementVNode("input", {
                                      ref_key: "backupFileInputEl",
                                      ref: backupFileInputEl,
                                      class: "mcr-font-file-input",
                                      type: "file",
                                      accept: ".json,application/json",
                                      onChange: onBackupFileInputChange
                                    }, null, 544),
                                    _createElementVNode("div", _hoisted_41, [
                                      _createElementVNode("div", null, [
                                        _createVNode(BlueprintField, {
                                          modelValue: config.value.backup_path,
                                          "onUpdate:modelValue": _cache[18] || (_cache[18] = ($event) => config.value.backup_path = $event),
                                          label: "备份本地路径",
                                          placeholder: "留空使用插件数据目录/backups",
                                          hint: "可填写目录或 .json 文件路径；相对路径会保存到插件数据目录下"
                                        }, null, 8, ["modelValue"])
                                      ]),
                                      _createElementVNode("div", null, [
                                        _createVNode(BlueprintField, {
                                          modelValue: config.value.backup_cron,
                                          "onUpdate:modelValue": _cache[19] || (_cache[19] = ($event) => config.value.backup_cron = $event),
                                          label: "备份 cron",
                                          placeholder: "0 4 * * *",
                                          hint: "留空关闭定时备份；填写正确 5 位 cron 表达式则开启"
                                        }, null, 8, ["modelValue"])
                                      ]),
                                      _createElementVNode("div", _hoisted_42, [
                                        _createElementVNode("div", _hoisted_43, [
                                          _createVNode(_component_v_btn, {
                                            class: "mcr-button mcr-button--ghost mcr-button--dark-neutral",
                                            "prepend-icon": "mdi-content-save-cog-outline",
                                            disabled: Boolean(cacheAction.value),
                                            onClick: onBackupConfig
                                          }, {
                                            default: _withCtx(() => [..._cache[42] || (_cache[42] = [
                                              _createTextVNode(" 立即备份 ", -1)
                                            ])]),
                                            _: 1
                                          }, 8, ["disabled"]),
                                          _createVNode(_component_v_btn, {
                                            class: "mcr-button mcr-button--ghost mcr-button--dark-neutral",
                                            "prepend-icon": "mdi-upload-box-outline",
                                            disabled: Boolean(cacheAction.value),
                                            onClick: openBackupFilePicker
                                          }, {
                                            default: _withCtx(() => [..._cache[43] || (_cache[43] = [
                                              _createTextVNode(" 上传备份 ", -1)
                                            ])]),
                                            _: 1
                                          }, 8, ["disabled"]),
                                          _createVNode(_component_v_btn, {
                                            class: "mcr-button mcr-button--ghost mcr-button--dark-neutral",
                                            "prepend-icon": "mdi-restore-alert",
                                            disabled: Boolean(cacheAction.value),
                                            onClick: initializePluginConfig
                                          }, {
                                            default: _withCtx(() => [..._cache[44] || (_cache[44] = [
                                              _createTextVNode(" 初始化插件 ", -1)
                                            ])]),
                                            _: 1
                                          }, 8, ["disabled"]),
                                          cacheAction.value === "backup" ? (_openBlock(), _createBlock(AsyncStatusDots, {
                                            key: 0,
                                            label: "备份配置"
                                          })) : _createCommentVNode("", true),
                                          _createElementVNode("button", {
                                            type: "button",
                                            class: "mcr-config-collapse-button",
                                            onClick: _cache[20] || (_cache[20] = ($event) => backupLibraryExpanded.value = !backupLibraryExpanded.value)
                                          }, [
                                            _createVNode(_component_v_icon, {
                                              icon: backupLibraryExpanded.value ? "mdi-chevron-up" : "mdi-chevron-down",
                                              size: "18"
                                            }, null, 8, ["icon"]),
                                            _createTextVNode(" 已备份 " + _toDisplayString(backupItems.value.length) + " 个 ", 1)
                                          ])
                                        ]),
                                        backupLibraryExpanded.value ? (_openBlock(), _createElementBlock("div", _hoisted_44, [
                                          backupListLoading.value ? (_openBlock(), _createElementBlock("div", _hoisted_45, "正在读取备份记录...")) : !backupItems.value.length ? (_openBlock(), _createElementBlock("div", _hoisted_46, "暂无备份记录")) : (_openBlock(), _createElementBlock("div", _hoisted_47, [
                                            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(backupItems.value, (item) => {
                                              return _openBlock(), _createElementBlock("article", {
                                                key: item.path || item.name,
                                                class: "mcr-backup-item"
                                              }, [
                                                _createElementVNode("div", _hoisted_48, [
                                                  _createElementVNode("div", {
                                                    class: "mcr-backup-item__name",
                                                    title: item.name
                                                  }, _toDisplayString(item.name), 9, _hoisted_49),
                                                  _createElementVNode("div", _hoisted_50, [
                                                    _createTextVNode(_toDisplayString(item.exported_at || item.mtime_label || "未知时间") + " ", 1),
                                                    item.version ? (_openBlock(), _createElementBlock("span", _hoisted_51, "v" + _toDisplayString(item.version), 1)) : _createCommentVNode("", true)
                                                  ])
                                                ]),
                                                _createElementVNode("div", _hoisted_52, [
                                                  _createElementVNode("button", {
                                                    type: "button",
                                                    title: "下载备份",
                                                    onClick: _withModifiers(($event) => downloadBackupItem(item), ["stop", "prevent"])
                                                  }, [
                                                    _createVNode(_component_v_icon, {
                                                      icon: "mdi-download-outline",
                                                      size: "17"
                                                    })
                                                  ], 8, _hoisted_53),
                                                  _createElementVNode("button", {
                                                    type: "button",
                                                    title: "恢复配置",
                                                    onClick: _withModifiers(($event) => restoreBackupItem(item), ["stop", "prevent"])
                                                  }, [
                                                    _createVNode(_component_v_icon, {
                                                      icon: "mdi-restore",
                                                      size: "17"
                                                    })
                                                  ], 8, _hoisted_54),
                                                  _createElementVNode("button", {
                                                    type: "button",
                                                    title: "删除备份",
                                                    class: "mcr-backup-item__danger",
                                                    onClick: _withModifiers(($event) => deleteBackupItem(item), ["stop", "prevent"])
                                                  }, [
                                                    _createVNode(_component_v_icon, {
                                                      icon: "mdi-trash-can-outline",
                                                      size: "17"
                                                    })
                                                  ], 8, _hoisted_55)
                                                ])
                                              ]);
                                            }), 128))
                                          ]))
                                        ])) : _createCommentVNode("", true)
                                      ])
                                    ])
                                  ]),
                                  _createElementVNode("section", _hoisted_56, [
                                    _cache[50] || (_cache[50] = _createElementVNode("header", { class: "mcr-config-section-card__header" }, [
                                      _createElementVNode("div", null, [
                                        _createElementVNode("div", { class: "mcr-config-section-card__title" }, "清理缓存"),
                                        _createElementVNode("p", { class: "mcr-config-section-card__copy" }, "清理图片或字体缓存，不影响已保存的配置。")
                                      ])
                                    ], -1)),
                                    _createElementVNode("div", _hoisted_57, [
                                      _createElementVNode("div", _hoisted_58, [
                                        _cache[47] || (_cache[47] = _createElementVNode("div", null, [
                                          _createElementVNode("strong", null, "清理图片缓存"),
                                          _createElementVNode("span", null, "释放插件生成图片缓存占用的空间。")
                                        ], -1)),
                                        _createVNode(_component_v_btn, {
                                          class: "mcr-button mcr-button--danger mcr-config-cache-danger",
                                          "prepend-icon": "mdi-image-remove",
                                          disabled: Boolean(cacheAction.value),
                                          onClick: onCleanImages
                                        }, {
                                          default: _withCtx(() => [..._cache[46] || (_cache[46] = [
                                            _createTextVNode(" 清理图片缓存 ", -1)
                                          ])]),
                                          _: 1
                                        }, 8, ["disabled"]),
                                        cacheAction.value === "images" ? (_openBlock(), _createBlock(AsyncStatusDots, {
                                          key: 0,
                                          label: "清理图片缓存"
                                        })) : _createCommentVNode("", true)
                                      ]),
                                      _createElementVNode("div", _hoisted_59, [
                                        _cache[49] || (_cache[49] = _createElementVNode("div", null, [
                                          _createElementVNode("strong", null, "清理字体缓存"),
                                          _createElementVNode("span", null, "遇到字体读取异常时可尝试重新清理。")
                                        ], -1)),
                                        _createVNode(_component_v_btn, {
                                          class: "mcr-button mcr-button--danger mcr-config-cache-danger",
                                          "prepend-icon": "mdi-format-font",
                                          disabled: Boolean(cacheAction.value),
                                          onClick: onCleanFonts
                                        }, {
                                          default: _withCtx(() => [..._cache[48] || (_cache[48] = [
                                            _createTextVNode(" 清理字体缓存 ", -1)
                                          ])]),
                                          _: 1
                                        }, 8, ["disabled"]),
                                        cacheAction.value === "fonts" ? (_openBlock(), _createBlock(AsyncStatusDots, {
                                          key: 0,
                                          label: "清理字体缓存"
                                        })) : _createCommentVNode("", true)
                                      ])
                                    ])
                                  ])
                                ]),
                                _: 1
                              })
                            ]),
                            _: 1
                          }),
                          _createVNode(_component_v_window_item, { value: "title-tab" }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_card_text, { class: "mcr-panel__body mcr-config-tabbody" }, {
                                default: _withCtx(() => [
                                  _cache[55] || (_cache[55] = _createElementVNode("div", { class: "mcr-panel__eyebrow" }, "Titles", -1)),
                                  _createElementVNode("div", _hoisted_60, [
                                    _cache[52] || (_cache[52] = _createElementVNode("div", { class: "mcr-panel__title" }, "主副标题配置", -1)),
                                    _createVNode(_component_v_btn, {
                                      size: "small",
                                      class: "mcr-button mcr-button--ghost mcr-button--dark-neutral mcr-title-config-template-btn",
                                      "prepend-icon": "mdi-format-list-bulleted-square",
                                      loading: titleTemplateLoading.value,
                                      onClick: appendMissingTitleTemplates
                                    }, {
                                      default: _withCtx(() => [..._cache[51] || (_cache[51] = [
                                        _createTextVNode("补全媒体库模板", -1)
                                      ])]),
                                      _: 1
                                    }, 8, ["loading"])
                                  ]),
                                  _cache[56] || (_cache[56] = _createElementVNode("p", { class: "mcr-panel__copy mcr-config-copy" }, " 严格模式按标准 YAML 校验；宽容模式会兼容中文冒号、冒号后无空格和部分缩进问题。 ", -1)),
                                  _createElementVNode("div", _hoisted_61, [
                                    _createVNode(_component_v_switch, {
                                      modelValue: config.value.distinguish_same_name_libraries,
                                      "onUpdate:modelValue": _cache[21] || (_cache[21] = ($event) => config.value.distinguish_same_name_libraries = $event),
                                      color: "primary",
                                      "hide-details": "",
                                      density: "comfortable",
                                      label: "区分同名媒体库"
                                    }, null, 8, ["modelValue"]),
                                    _cache[53] || (_cache[53] = _createElementVNode("span", { class: "mcr-title-config-mode" }, " 开启后自动补全使用「服务器名_媒体库名」；仅使用媒体库名时，同名库共用同一配置 ", -1)),
                                    _createVNode(_component_v_switch, {
                                      modelValue: config.value.title_config_strict,
                                      "onUpdate:modelValue": _cache[22] || (_cache[22] = ($event) => config.value.title_config_strict = $event),
                                      color: "primary",
                                      "hide-details": "",
                                      density: "comfortable",
                                      label: config.value.title_config_strict ? "严格模式" : "宽容模式"
                                    }, null, 8, ["modelValue", "label"]),
                                    _createElementVNode("span", _hoisted_62, _toDisplayString(config.value.title_config_strict ? "必须使用标准 YAML 语法" : "允许常见中文符号和空格容错"), 1)
                                  ]),
                                  titleConfigValidationMessage.value ? (_openBlock(), _createElementBlock("div", {
                                    key: 0,
                                    class: _normalizeClass(["mcr-title-config-alert", { "mcr-title-config-alert--ok": titleConfigValidationValid.value }])
                                  }, _toDisplayString(titleConfigValidationMessage.value), 3)) : _createCommentVNode("", true),
                                  _createVNode(BlueprintField, {
                                    modelValue: config.value.title_config,
                                    "onUpdate:modelValue": _cache[23] || (_cache[23] = ($event) => config.value.title_config = $event),
                                    textarea: "",
                                    label: "主副标题配置 (YAML)",
                                    rows: "16",
                                    spellcheck: "false",
                                    class: "font-mono mcr-config-editor",
                                    placeholder: _unref(titlePlaceholder)
                                  }, null, 8, ["modelValue", "placeholder"]),
                                  _createElementVNode("div", { class: "mcr-title-config-reference" }, [
                                    _cache[54] || (_cache[54] = _createElementVNode("div", { class: "mcr-title-config-reference__label" }, "格式参考", -1)),
                                    _createElementVNode("pre", null, _toDisplayString(titleConfigReference))
                                  ])
                                ]),
                                _: 1
                              })
                            ]),
                            _: 1
                          })
                        ]),
                        _: 1
                      }, 8, ["modelValue"]),
                      _createElementVNode("div", _hoisted_63, "前端 UI " + _toDisplayString(_unref(UI_REV)) + " · 主程序 v" + _toDisplayString(_unref(PROGRAM_VERSION)), 1)
                    ], 512)
                  ])
                ]),
                _createVNode(ViewportSaveToast, {
                  message: configSaveMessage.value,
                  theme: isDark.value ? "dark" : "light"
                }, null, 8, ["message", "theme"])
              ]),
              _: 1
            }, 8, ["defaults"])
          ]),
          _: 1
        })
      ], 8, _hoisted_1);
    };
  }
});

const Config = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-af9d57a1"]]);

export { Config as default };
