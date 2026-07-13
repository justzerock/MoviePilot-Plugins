import { importShared } from './__federation_fn_import-ui-rev-20260713-08.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-ui-rev-20260713-08.js';

const MCR_CONTROL_DEFAULTS = {
  VTextField: {
    density: "compact",
    variant: "outlined",
    color: "var(--mcr-control-color)",
    baseColor: "var(--mcr-control-base)",
    bgColor: "var(--mcr-control-bg)",
    rounded: "lg",
    hideDetails: "auto"
  },
  VTextarea: {
    density: "comfortable",
    variant: "outlined",
    color: "var(--mcr-control-color)",
    baseColor: "var(--mcr-control-base)",
    bgColor: "var(--mcr-control-bg)",
    rounded: "lg",
    hideDetails: "auto"
  },
  VSelect: {
    density: "compact",
    variant: "outlined",
    color: "var(--mcr-control-color)",
    baseColor: "var(--mcr-control-base)",
    bgColor: "var(--mcr-control-bg)",
    rounded: "lg",
    hideDetails: "auto"
  },
  VSwitch: {
    density: "compact",
    color: "var(--mcr-control-color)",
    baseColor: "var(--mcr-control-base-soft)",
    hideDetails: "auto"
  },
  VSlider: {
    color: "var(--mcr-control-color)",
    trackColor: "var(--mcr-control-track)",
    thumbColor: "var(--mcr-control-color)",
    hideDetails: "auto"
  }
};

const {defineComponent:_defineComponent$3} = await importShared('vue');

const {toDisplayString:_toDisplayString$3,openBlock:_openBlock$3,createElementBlock:_createElementBlock$3,createCommentVNode:_createCommentVNode$3,mergeProps:_mergeProps$1,normalizeClass:_normalizeClass$1} = await importShared('vue');

const _hoisted_1$3 = {
  key: 0,
  class: "mcr-blueprint-field__label"
};
const _hoisted_2$2 = ["value", "rows", "placeholder"];
const _hoisted_3$1 = ["type", "value", "placeholder"];
const _hoisted_4$1 = {
  key: 3,
  class: "mcr-blueprint-field__hint"
};
const {computed: computed$1,useAttrs: useAttrs$1} = await importShared('vue');

const _sfc_main$3 = /* @__PURE__ */ _defineComponent$3({
  ...{ inheritAttrs: false },
  __name: "BlueprintField",
  props: {
    modelValue: { default: "" },
    label: { default: "" },
    type: { default: "text" },
    placeholder: { default: "" },
    hint: { default: "" },
    rows: { default: 3 },
    textarea: { type: Boolean, default: false },
    modelModifiers: { default: () => ({}) }
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const attrs = useAttrs$1();
    const rootClass = computed$1(() => attrs.class);
    const controlAttrs = computed$1(() => {
      const { class: _class, ...rest } = attrs;
      return rest;
    });
    function normalizeValue(value) {
      if (props.modelModifiers?.number || props.type === "number") {
        return value === "" ? null : Number(value);
      }
      return value;
    }
    function onInput(event) {
      const target = event.target;
      emit("update:modelValue", normalizeValue(target.value));
    }
    return (_ctx, _cache) => {
      return _openBlock$3(), _createElementBlock$3("label", {
        class: _normalizeClass$1(["mcr-blueprint-field", [
          rootClass.value,
          {
            "mcr-blueprint-field--textarea": __props.textarea,
            "mcr-blueprint-field--color": __props.type === "color"
          }
        ]])
      }, [
        __props.label ? (_openBlock$3(), _createElementBlock$3("span", _hoisted_1$3, _toDisplayString$3(__props.label), 1)) : _createCommentVNode$3("", true),
        __props.textarea ? (_openBlock$3(), _createElementBlock$3("textarea", _mergeProps$1({ key: 1 }, controlAttrs.value, {
          class: "mcr-blueprint-field__control mcr-blueprint-field__control--textarea",
          value: __props.modelValue ?? "",
          rows: __props.rows,
          placeholder: __props.placeholder,
          onInput
        }), null, 16, _hoisted_2$2)) : (_openBlock$3(), _createElementBlock$3("input", _mergeProps$1({ key: 2 }, controlAttrs.value, {
          class: "mcr-blueprint-field__control",
          type: __props.type,
          value: __props.modelValue ?? "",
          placeholder: __props.placeholder,
          onInput
        }), null, 16, _hoisted_3$1)),
        __props.hint ? (_openBlock$3(), _createElementBlock$3("span", _hoisted_4$1, _toDisplayString$3(__props.hint), 1)) : _createCommentVNode$3("", true)
      ], 2);
    };
  }
});

const BlueprintField = /* @__PURE__ */ _export_sfc(_sfc_main$3, [["__scopeId", "data-v-a72d892d"]]);

const {defineComponent:_defineComponent$2} = await importShared('vue');

const {toDisplayString:_toDisplayString$2,openBlock:_openBlock$2,createElementBlock:_createElementBlock$2,createCommentVNode:_createCommentVNode$2,renderList:_renderList,Fragment:_Fragment,createElementVNode:_createElementVNode$1,withModifiers:_withModifiers,normalizeClass:_normalizeClass,normalizeStyle:_normalizeStyle,Teleport:_Teleport$1,createBlock:_createBlock$1,mergeProps:_mergeProps} = await importShared('vue');

const _hoisted_1$2 = {
  key: 0,
  class: "mcr-blueprint-select__label"
};
const _hoisted_2$1 = {
  key: 1,
  class: "mcr-blueprint-select__multi"
};
const _hoisted_3 = ["disabled", "aria-expanded"];
const _hoisted_4 = {
  key: 0,
  class: "mcr-blueprint-select__chips"
};
const _hoisted_5 = {
  key: 0,
  class: "mcr-blueprint-select__chip mcr-blueprint-select__chip--more"
};
const _hoisted_6 = {
  key: 1,
  class: "mcr-blueprint-select__placeholder"
};
const _hoisted_7 = {
  class: "mcr-blueprint-select__count",
  "aria-hidden": "true"
};
const _hoisted_8 = ["data-mcr-theme"];
const _hoisted_9 = ["disabled", "aria-selected", "onClick"];
const _hoisted_10 = {
  class: "mcr-blueprint-select__checkbox",
  "aria-hidden": "true"
};
const _hoisted_11 = {
  key: 0,
  class: "mcr-blueprint-select__check"
};
const _hoisted_12 = { class: "mcr-blueprint-select__multi-title" };
const _hoisted_13 = {
  key: 2,
  class: "mcr-blueprint-select__shell"
};
const _hoisted_14 = ["value"];
const _hoisted_15 = {
  key: 0,
  value: ""
};
const _hoisted_16 = ["value"];
const _hoisted_17 = {
  key: 4,
  class: "mcr-blueprint-select__hint"
};
const {computed,nextTick,onBeforeUnmount,onMounted,ref,useAttrs} = await importShared('vue');

const _sfc_main$2 = /* @__PURE__ */ _defineComponent$2({
  ...{ inheritAttrs: false },
  __name: "BlueprintSelect",
  props: {
    modelValue: { type: [String, Number, Boolean, null, Array], default: "" },
    items: { default: () => [] },
    label: { default: "" },
    hint: { default: "" },
    placeholder: { default: "" },
    multiple: { type: Boolean, default: false },
    clearable: { type: Boolean, default: false }
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const attrs = useAttrs();
    const rootEl = ref(null);
    const popoverEl = ref(null);
    const isOpen = ref(false);
    const popoverPlacement = ref("bottom");
    const popoverTheme = ref("light");
    const popoverStyle = ref({});
    const rootClass = computed(() => attrs.class);
    const controlAttrs = computed(() => {
      const { class: _class, ...rest } = attrs;
      return rest;
    });
    const normalizedItems = computed(() => props.items.map((item) => {
      if (typeof item === "object" && item !== null) {
        const value = item.value ?? item.title ?? item.label ?? item.name ?? "";
        return {
          title: String(item.title ?? item.label ?? item.name ?? value),
          value
        };
      }
      return {
        title: String(item),
        value: item
      };
    }));
    const selectValue = computed(() => props.multiple ? Array.isArray(props.modelValue) ? props.modelValue.map((item) => String(item)) : [] : String(props.modelValue ?? ""));
    const selectedCount = computed(() => Array.isArray(props.modelValue) ? props.modelValue.length : 0);
    const selectedItems = computed(() => Array.isArray(props.modelValue) ? normalizedItems.value.filter((item) => isSelected(item.value)) : []);
    const visibleSelectedItems = computed(() => selectedItems.value.slice(0, 2));
    const hiddenSelectedCount = computed(() => Math.max(0, selectedItems.value.length - visibleSelectedItems.value.length));
    const isDisabled = computed(() => attrs.disabled === true || attrs.disabled === "" || attrs.disabled === "true");
    function denormalizeValue(raw) {
      const found = normalizedItems.value.find((item) => String(item.value) === raw);
      return found ? found.value : raw;
    }
    function onChange(event) {
      const select = event.target;
      emit("update:modelValue", denormalizeValue(select.value));
    }
    function isSelected(value) {
      if (!Array.isArray(props.modelValue)) return false;
      return props.modelValue.some((item) => String(item) === String(value));
    }
    function toggleMultiple(value) {
      if (isDisabled.value) return;
      const scrollSnapshot = captureScrollSnapshot();
      const current = Array.isArray(props.modelValue) ? props.modelValue : [];
      const exists = current.some((item) => String(item) === String(value));
      emit(
        "update:modelValue",
        exists ? current.filter((item) => String(item) !== String(value)) : [...current, value]
      );
      nextTick(() => {
        restoreScrollSnapshot(scrollSnapshot);
        updatePopoverPosition();
      });
    }
    function toggleOpen() {
      if (isDisabled.value) return;
      isOpen.value = !isOpen.value;
      if (isOpen.value) {
        nextTick(updatePopoverPosition);
      }
    }
    function clearMultiple() {
      const scrollSnapshot = captureScrollSnapshot();
      emit("update:modelValue", []);
      isOpen.value = false;
      nextTick(() => restoreScrollSnapshot(scrollSnapshot));
    }
    function closePopover() {
      const scrollSnapshot = captureScrollSnapshot();
      isOpen.value = false;
      nextTick(() => restoreScrollSnapshot(scrollSnapshot));
    }
    function captureScrollSnapshot() {
      if (typeof window === "undefined" || typeof document === "undefined") return null;
      return {
        windowX: window.scrollX,
        windowY: window.scrollY,
        docTop: document.documentElement.scrollTop,
        bodyTop: document.body?.scrollTop || 0
      };
    }
    function restoreScrollSnapshot(snapshot) {
      if (!snapshot || typeof window === "undefined" || typeof document === "undefined") return;
      document.documentElement.scrollTop = snapshot.docTop;
      if (document.body) document.body.scrollTop = snapshot.bodyTop;
      window.scrollTo(snapshot.windowX, snapshot.windowY);
      window.requestAnimationFrame?.(() => {
        document.documentElement.scrollTop = snapshot.docTop;
        if (document.body) document.body.scrollTop = snapshot.bodyTop;
        window.scrollTo(snapshot.windowX, snapshot.windowY);
      });
    }
    function onDocumentPointerDown(event) {
      if (!isOpen.value || !rootEl.value) return;
      const target = event.target;
      if (!rootEl.value.contains(target) && !popoverEl.value?.contains(target)) {
        isOpen.value = false;
      }
    }
    function onDocumentKeydown(event) {
      if (event.key === "Escape") {
        isOpen.value = false;
      }
    }
    function readPopoverTheme() {
      const themedRoot = rootEl.value?.closest("[data-mcr-theme]");
      const explicitTheme = themedRoot?.getAttribute("data-mcr-theme");
      if (explicitTheme === "dark" || explicitTheme === "light") {
        popoverTheme.value = explicitTheme;
        return;
      }
      popoverTheme.value = typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    function updatePopoverPosition() {
      if (!isOpen.value || typeof window === "undefined") return;
      const trigger = rootEl.value?.querySelector(".mcr-blueprint-select__multi-trigger");
      const anchor = trigger || rootEl.value;
      if (!anchor) return;
      readPopoverTheme();
      const rect = anchor.getBoundingClientRect();
      const viewportWidth = window.innerWidth || document.documentElement.clientWidth;
      const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
      const gutter = 12;
      const desiredWidth = viewportWidth < 680 ? viewportWidth - gutter * 2 : Math.min(Math.max(rect.width, 560), viewportWidth - gutter * 2);
      const left = Math.min(
        Math.max(gutter, rect.left),
        Math.max(gutter, viewportWidth - desiredWidth - gutter)
      );
      const spaceBelow = viewportHeight - rect.bottom - gutter;
      const spaceAbove = rect.top - gutter;
      const shouldOpenTop = spaceBelow < 260 && spaceAbove > spaceBelow;
      const maxHeight = Math.max(
        180,
        Math.min(360, (shouldOpenTop ? spaceAbove : spaceBelow) - 8)
      );
      popoverPlacement.value = shouldOpenTop ? "top" : "bottom";
      popoverStyle.value = shouldOpenTop ? {
        left: `${left}px`,
        bottom: `${viewportHeight - rect.top + 8}px`,
        width: `${desiredWidth}px`,
        maxHeight: `${maxHeight}px`
      } : {
        left: `${left}px`,
        top: `${rect.bottom + 8}px`,
        width: `${desiredWidth}px`,
        maxHeight: `${maxHeight}px`
      };
    }
    onMounted(() => {
      document.addEventListener("pointerdown", onDocumentPointerDown);
      document.addEventListener("keydown", onDocumentKeydown);
      window.addEventListener("resize", updatePopoverPosition);
      window.addEventListener("scroll", updatePopoverPosition, true);
    });
    onBeforeUnmount(() => {
      document.removeEventListener("pointerdown", onDocumentPointerDown);
      document.removeEventListener("keydown", onDocumentKeydown);
      window.removeEventListener("resize", updatePopoverPosition);
      window.removeEventListener("scroll", updatePopoverPosition, true);
    });
    return (_ctx, _cache) => {
      return _openBlock$2(), _createElementBlock$2("label", {
        ref_key: "rootEl",
        ref: rootEl,
        class: _normalizeClass(["mcr-blueprint-select", rootClass.value])
      }, [
        __props.label ? (_openBlock$2(), _createElementBlock$2("span", _hoisted_1$2, _toDisplayString$2(__props.label), 1)) : _createCommentVNode$2("", true),
        __props.multiple ? (_openBlock$2(), _createElementBlock$2("span", _hoisted_2$1, [
          _createElementVNode$1("button", {
            type: "button",
            class: _normalizeClass(["mcr-blueprint-select__multi-trigger", { "mcr-blueprint-select__multi-trigger--open": isOpen.value }]),
            disabled: isDisabled.value,
            "aria-expanded": isOpen.value,
            onClick: _withModifiers(toggleOpen, ["prevent"])
          }, [
            selectedItems.value.length ? (_openBlock$2(), _createElementBlock$2("span", _hoisted_4, [
              (_openBlock$2(true), _createElementBlock$2(_Fragment, null, _renderList(visibleSelectedItems.value, (item) => {
                return _openBlock$2(), _createElementBlock$2("span", {
                  key: String(item.value),
                  class: "mcr-blueprint-select__chip"
                }, _toDisplayString$2(item.title), 1);
              }), 128)),
              hiddenSelectedCount.value > 0 ? (_openBlock$2(), _createElementBlock$2("span", _hoisted_5, " ··· ")) : _createCommentVNode$2("", true)
            ])) : (_openBlock$2(), _createElementBlock$2("span", _hoisted_6, _toDisplayString$2(__props.placeholder || "不指定，默认全部"), 1)),
            _createElementVNode$1("span", _hoisted_7, _toDisplayString$2(selectedItems.value.length || normalizedItems.value.length), 1)
          ], 10, _hoisted_3),
          (_openBlock$2(), _createBlock$1(_Teleport$1, { to: "body" }, [
            isOpen.value ? (_openBlock$2(), _createElementBlock$2("span", {
              key: 0,
              ref_key: "popoverEl",
              ref: popoverEl,
              class: _normalizeClass(["mcr-blueprint-select__popover", `mcr-blueprint-select__popover--${popoverPlacement.value}`]),
              "data-mcr-theme": popoverTheme.value,
              style: _normalizeStyle(popoverStyle.value),
              role: "listbox",
              "aria-multiselectable": "true"
            }, [
              (_openBlock$2(true), _createElementBlock$2(_Fragment, null, _renderList(normalizedItems.value, (item) => {
                return _openBlock$2(), _createElementBlock$2("button", {
                  key: String(item.value),
                  type: "button",
                  class: _normalizeClass(["mcr-blueprint-select__multi-option", { "mcr-blueprint-select__multi-option--active": isSelected(item.value) }]),
                  disabled: isDisabled.value,
                  role: "option",
                  "aria-selected": isSelected(item.value),
                  onPointerdown: _cache[0] || (_cache[0] = _withModifiers(() => {
                  }, ["prevent", "stop"])),
                  onClick: _withModifiers(($event) => toggleMultiple(item.value), ["prevent", "stop"])
                }, [
                  _createElementVNode$1("span", _hoisted_10, [
                    isSelected(item.value) ? (_openBlock$2(), _createElementBlock$2("span", _hoisted_11, "✓")) : _createCommentVNode$2("", true)
                  ]),
                  _createElementVNode$1("span", _hoisted_12, _toDisplayString$2(item.title), 1)
                ], 42, _hoisted_9);
              }), 128)),
              _createElementVNode$1("button", {
                type: "button",
                class: "mcr-blueprint-select__done",
                onPointerdown: _cache[1] || (_cache[1] = _withModifiers(() => {
                }, ["prevent", "stop"])),
                onClick: _withModifiers(closePopover, ["prevent", "stop"])
              }, " 完成 ", 32)
            ], 14, _hoisted_8)) : _createCommentVNode$2("", true)
          ]))
        ])) : (_openBlock$2(), _createElementBlock$2("span", _hoisted_13, [
          _createElementVNode$1("select", _mergeProps(controlAttrs.value, {
            class: "mcr-blueprint-select__control",
            value: selectValue.value,
            onChange
          }), [
            __props.clearable ? (_openBlock$2(), _createElementBlock$2("option", _hoisted_15, _toDisplayString$2(__props.placeholder || "不指定"), 1)) : _createCommentVNode$2("", true),
            (_openBlock$2(true), _createElementBlock$2(_Fragment, null, _renderList(normalizedItems.value, (item) => {
              return _openBlock$2(), _createElementBlock$2("option", {
                key: String(item.value),
                value: item.value
              }, _toDisplayString$2(item.title), 9, _hoisted_16);
            }), 128))
          ], 16, _hoisted_14)
        ])),
        __props.clearable && __props.multiple && selectedCount.value > 0 ? (_openBlock$2(), _createElementBlock$2("button", {
          key: 3,
          type: "button",
          class: "mcr-blueprint-select__clear",
          onClick: _withModifiers(clearMultiple, ["prevent"])
        }, " 清除已选 " + _toDisplayString$2(selectedCount.value) + " 项 ", 1)) : _createCommentVNode$2("", true),
        __props.hint ? (_openBlock$2(), _createElementBlock$2("span", _hoisted_17, _toDisplayString$2(__props.hint), 1)) : _createCommentVNode$2("", true)
      ], 2);
    };
  }
});

const BlueprintSelect = /* @__PURE__ */ _export_sfc(_sfc_main$2, [["__scopeId", "data-v-1e7ebd55"]]);

const {defineComponent:_defineComponent$1} = await importShared('vue');

const {createElementVNode:_createElementVNode,toDisplayString:_toDisplayString$1,openBlock:_openBlock$1,createElementBlock:_createElementBlock$1,createCommentVNode:_createCommentVNode$1} = await importShared('vue');

const _hoisted_1$1 = {
  class: "mcr-async-status",
  role: "status",
  "aria-live": "polite"
};
const _hoisted_2 = {
  key: 0,
  class: "mcr-async-status__label"
};
const _sfc_main$1 = /* @__PURE__ */ _defineComponent$1({
  __name: "AsyncStatusDots",
  props: {
    label: { default: "" }
  },
  setup(__props) {
    return (_ctx, _cache) => {
      return _openBlock$1(), _createElementBlock$1("span", _hoisted_1$1, [
        _cache[0] || (_cache[0] = _createElementVNode("span", {
          class: "mcr-async-status__dots",
          "aria-hidden": "true"
        }, [
          _createElementVNode("i"),
          _createElementVNode("i"),
          _createElementVNode("i")
        ], -1)),
        __props.label ? (_openBlock$1(), _createElementBlock$1("span", _hoisted_2, _toDisplayString$1(__props.label), 1)) : _createCommentVNode$1("", true)
      ]);
    };
  }
});

const AsyncStatusDots = /* @__PURE__ */ _export_sfc(_sfc_main$1, [["__scopeId", "data-v-534605a2"]]);

const BUILTIN_FONT_ITEMS = [
  { title: "潮黑 chaohei", value: "chaohei" },
  { title: "粗雅宋 yasong", value: "yasong" },
  { title: "Emblema One", value: "EmblemaOne" },
  { title: "Melete", value: "Melete" },
  { title: "Phosphate", value: "Phosphate" },
  { title: "Josefin Sans", value: "JosefinSans" },
  { title: "Lilita One", value: "LilitaOne" }
];
const SEMANTIC_FONT_ITEMS = [
  { title: "主标题字体", value: "main_title" },
  { title: "副标题字体", value: "subtitle" },
  { title: "自定义文本字体", value: "custom_text" }
];
function getTemplateFontFaceName(fontFamily) {
  if (fontFamily === "subtitle") return "McrSubtitleFont";
  if (fontFamily === "custom_text") return "McrCustomTextFont";
  if (!fontFamily || fontFamily === "main_title") return "McrMainTitleFont";
  return `McrFont_${String(fontFamily).replace(/[^a-zA-Z0-9_-]/g, "_")}`;
}
function containsCjkText(value) {
  return /[\u3400-\u9fff]/.test(String(value || ""));
}
function isCjkFontFamily(fontFamily) {
  const normalized = String(fontFamily || "").toLowerCase().replace(/[\s_-]+/g, "");
  return [
    "chaohei",
    "yasong",
    "wenquanyi",
    "wqy",
    "notosanscjk",
    "notoserifcjk",
    "sourcehansans",
    "sourcehanserif",
    "sarasa",
    "unifont",
    "ipag"
  ].some((token) => normalized.includes(token));
}
function getTemplateFontFamilyStack(fontFamily, text) {
  const primary = getTemplateFontFaceName(fontFamily || "main_title");
  const systemCjk = '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", "WenQuanYi Zen Hei"';
  if (containsCjkText(text) && !isCjkFontFamily(fontFamily)) {
    return `McrFont_chaohei, McrFont_yasong, ${primary}, ${systemCjk}, sans-serif`;
  }
  return `${primary}, ${systemCjk}, sans-serif`;
}

const {defineComponent:_defineComponent} = await importShared('vue');

const {toDisplayString:_toDisplayString,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,Transition:_Transition,withCtx:_withCtx,createVNode:_createVNode,Teleport:_Teleport,createBlock:_createBlock} = await importShared('vue');

const _hoisted_1 = ["data-mcr-theme"];
const _sfc_main = /* @__PURE__ */ _defineComponent({
  __name: "ViewportSaveToast",
  props: {
    message: {},
    theme: {}
  },
  setup(__props) {
    return (_ctx, _cache) => {
      return _openBlock(), _createBlock(_Teleport, { to: "body" }, [
        _createVNode(_Transition, { name: "mcr-viewport-toast" }, {
          default: _withCtx(() => [
            __props.message ? (_openBlock(), _createElementBlock("div", {
              key: 0,
              class: "mcr-viewport-save-toast",
              "data-mcr-theme": __props.theme,
              role: "status",
              "aria-live": "polite"
            }, _toDisplayString(__props.message), 9, _hoisted_1)) : _createCommentVNode("", true)
          ]),
          _: 1
        })
      ]);
    };
  }
});

const ViewportSaveToast = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-73fc809b"]]);

export { AsyncStatusDots as A, BUILTIN_FONT_ITEMS as B, MCR_CONTROL_DEFAULTS as M, SEMANTIC_FONT_ITEMS as S, ViewportSaveToast as V, getTemplateFontFaceName as a, BlueprintField as b, BlueprintSelect as c, getTemplateFontFamilyStack as g };
