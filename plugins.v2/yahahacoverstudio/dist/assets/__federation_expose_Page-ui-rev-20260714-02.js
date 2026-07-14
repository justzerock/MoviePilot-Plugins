import { importShared } from './__federation_fn_import-ui-rev-20260714-02.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-ui-rev-20260714-02.js';
import { g as getTemplateFontFamilyStack, S as SEMANTIC_FONT_ITEMS, B as BUILTIN_FONT_ITEMS, a as getTemplateFontFaceName, b as BlueprintField, c as BlueprintSelect, M as MCR_CONTROL_DEFAULTS, A as AsyncStatusDots, V as ViewportSaveToast } from './ViewportSaveToast-ui-rev-20260714-02.js';

const {defineComponent:_defineComponent$4} = await importShared('vue');

const {normalizeStyle:_normalizeStyle$3,createElementVNode:_createElementVNode$3,toDisplayString:_toDisplayString$3,openBlock:_openBlock$4,createElementBlock:_createElementBlock$4} = await importShared('vue');

const _hoisted_1$4 = { class: "blueprint-range" };
const _hoisted_2$3 = ["min", "max", "step", "value"];
const _hoisted_3$3 = { class: "blueprint-range__content" };
const _hoisted_4$3 = { class: "blueprint-range__label" };
const _hoisted_5$3 = ["min", "max", "step", "value"];
const {computed: computed$5} = await importShared('vue');

const _sfc_main$4 = /* @__PURE__ */ _defineComponent$4({
  __name: "BlueprintRange",
  props: {
    modelValue: { default: 0 },
    min: { default: 0 },
    max: { default: 100 },
    step: { default: 1 },
    label: { default: "" }
  },
  emits: ["update:modelValue", "change", "start", "end"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const numericValue = computed$5(() => {
      const next = Number(props.modelValue ?? props.min);
      return Number.isFinite(next) ? next : props.min;
    });
    const sliderValue = computed$5(() => Math.max(props.min, Math.min(props.max, numericValue.value)));
    const manualMin = computed$5(() => props.min < 0 ? props.min * 10 : props.min);
    const manualMax = computed$5(() => props.max > 0 ? props.max * 10 : props.max);
    const percent = computed$5(() => {
      const span = props.max - props.min;
      if (!span) return 0;
      return Math.max(0, Math.min(100, (sliderValue.value - props.min) / span * 100));
    });
    const displayValue = computed$5(() => {
      const stepText = String(props.step);
      const decimals = stepText.includes(".") ? stepText.split(".")[1].length : 0;
      if (!decimals) return String(Math.round(numericValue.value));
      return numericValue.value.toFixed(decimals).replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
    });
    const rangeStyle = computed$5(() => ({
      "--blueprint-range-progress": `${percent.value}%`
    }));
    function readValue(event) {
      const value = Number(event.target.value);
      return Number.isFinite(value) ? value : props.min;
    }
    function onInput(event) {
      emit("update:modelValue", readValue(event));
    }
    function onChange(event) {
      emit("change", readValue(event));
    }
    function normalizeManualValue(raw) {
      const value = Number(raw);
      if (!Number.isFinite(value)) return numericValue.value;
      return Math.max(manualMin.value, Math.min(manualMax.value, value));
    }
    function onNumberInput(event) {
      emit("update:modelValue", normalizeManualValue(event.target.value));
    }
    function onNumberChange(event) {
      const value = normalizeManualValue(event.target.value);
      emit("update:modelValue", value);
      emit("change", value);
    }
    return (_ctx, _cache) => {
      return _openBlock$4(), _createElementBlock$4("label", _hoisted_1$4, [
        _createElementVNode$3("input", {
          class: "blueprint-range__input",
          type: "range",
          min: __props.min,
          max: __props.max,
          step: __props.step,
          value: sliderValue.value,
          style: _normalizeStyle$3(rangeStyle.value),
          onPointerdown: _cache[0] || (_cache[0] = ($event) => emit("start")),
          onPointerup: _cache[1] || (_cache[1] = ($event) => emit("end")),
          onPointercancel: _cache[2] || (_cache[2] = ($event) => emit("end")),
          onBlur: _cache[3] || (_cache[3] = ($event) => emit("end")),
          onInput,
          onChange
        }, null, 44, _hoisted_2$3),
        _createElementVNode$3("span", _hoisted_3$3, [
          _createElementVNode$3("span", _hoisted_4$3, _toDisplayString$3(__props.label), 1),
          _createElementVNode$3("input", {
            class: "blueprint-range__value",
            type: "number",
            min: manualMin.value,
            max: manualMax.value,
            step: __props.step,
            value: displayValue.value,
            onFocus: _cache[4] || (_cache[4] = ($event) => emit("start")),
            onInput: onNumberInput,
            onChange: onNumberChange,
            onBlur: _cache[5] || (_cache[5] = ($event) => emit("end"))
          }, null, 40, _hoisted_5$3)
        ])
      ]);
    };
  }
});

const BlueprintRange = /* @__PURE__ */ _export_sfc(_sfc_main$4, [["__scopeId", "data-v-fa32df23"]]);

function readCssVariable(name) {
  if (typeof document === "undefined") return "";
  const rootValue = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  if (rootValue) return rootValue;
  return getComputedStyle(document.body).getPropertyValue(name).trim();
}
function getThemeColor(name, fallbackName = "--mcr-color-on-surface") {
  return readCssVariable(name) || readCssVariable(fallbackName);
}
function getThemeRgba(rgbName, alpha, fallbackRgbName = "--mcr-rgb-on-surface") {
  const channels = readCssVariable(rgbName) || readCssVariable(fallbackRgbName);
  return channels ? `rgba(${channels}, ${alpha})` : getThemeColor("--mcr-color-on-surface");
}

const EDITOR_BASE_WIDTH = 1920;
const EDITOR_BASE_HEIGHT = 1080;
function createLayoutId() {
  return `layout_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}
function normalizeLayerType(type) {
  if (type === "group") return "group";
  if (type === "image") return "image";
  if (type === "main_title" || type === "title_zh") return "main_title";
  if (type === "subtitle" || type === "title_en") return "subtitle";
  if (type === "text") return "text";
  return "image";
}
function isImageLayer(layer) {
  return normalizeLayerType(layer.type) === "image";
}
function isMainTitleLayer(layer) {
  return normalizeLayerType(layer.type) === "main_title";
}
function isCustomTextLayer(layer) {
  return normalizeLayerType(layer.type) === "text";
}
function isTextLayer(layer) {
  const normalized = normalizeLayerType(layer.type);
  return normalized === "main_title" || normalized === "subtitle" || normalized === "text";
}
function withLegacyLayerFields(layer) {
  const normalized = layer;
  normalized.frame = {
    x: normalized.x,
    y: normalized.y,
    width: normalized.width,
    height: normalized.height
  };
  normalized.cornerRadius = normalized.radius ?? 0;
  normalized.shadow = {
    x: normalized.shadowOffsetX ?? 0,
    y: normalized.shadowOffsetY ?? 0,
    blur: normalized.shadowBlur ?? 0,
    opacity: normalized.shadowOpacity ?? 0.28
  };
  if (isTextLayer(normalized)) {
    normalized.textStyle = {
      fontFamily: normalized.fontFamily,
      fontSize: normalized.fontSize,
      textAlign: normalized.textAlign ?? "center",
      maskMode: normalized.maskMode ?? "normal",
      ...isCustomTextLayer(normalized) ? { content: normalized.content } : {}
    };
  } else {
    delete normalized.textStyle;
  }
  return normalized;
}
function normalizeLayerEffects(layer) {
  const normalizedType = normalizeLayerType(layer.type);
  if (normalizedType === "group") {
    const group = layer;
    const rotation2 = group.rotation ?? group.transform?.rotation ?? 0;
    const pivotX2 = group.pivotX ?? group.transform?.pivotX ?? 0.5;
    const pivotY2 = group.pivotY ?? group.transform?.pivotY ?? 0.5;
    const opacity2 = group.opacity ?? group.transform?.opacity ?? 1;
    const blur2 = group.blur ?? group.effects?.blur ?? 0;
    const shadowBlur2 = group.shadowBlur ?? group.effects?.shadow?.blur ?? 0;
    const shadowOffsetX2 = group.shadowOffsetX ?? group.effects?.shadow?.offsetX ?? 0;
    const shadowOffsetY2 = group.shadowOffsetY ?? group.effects?.shadow?.offsetY ?? 0;
    const shadowOpacity2 = group.shadowOpacity ?? group.effects?.shadow?.opacity ?? 0.28;
    return withLegacyLayerFields({
      ...group,
      type: "group",
      rotation: rotation2,
      pivotX: pivotX2,
      pivotY: pivotY2,
      opacity: opacity2,
      blur: blur2,
      shadowBlur: shadowBlur2,
      shadowOffsetX: shadowOffsetX2,
      shadowOffsetY: shadowOffsetY2,
      shadowOpacity: shadowOpacity2,
      transform: {
        rotation: rotation2,
        pivotX: pivotX2,
        pivotY: pivotY2,
        opacity: opacity2
      },
      effects: {
        blur: blur2,
        shadow: {
          blur: shadowBlur2,
          offsetX: shadowOffsetX2,
          offsetY: shadowOffsetY2,
          opacity: shadowOpacity2,
          color: group.effects?.shadow?.color ?? getThemeColor("--mcr-cover-shadow")
        }
      },
      children: (group.children || []).map((child) => normalizeLayerEffects({ ...child }))
    });
  }
  const shadowBlur = layer.shadowBlur ?? layer.effects?.shadow?.blur ?? 0;
  const shadowOffsetX = layer.shadowOffsetX ?? layer.effects?.shadow?.offsetX ?? 0;
  const shadowOffsetY = layer.shadowOffsetY ?? layer.effects?.shadow?.offsetY ?? 0;
  const shadowOpacity = layer.shadowOpacity ?? layer.effects?.shadow?.opacity ?? 0.28;
  const opacity = layer.opacity ?? layer.transform?.opacity ?? 1;
  const rotation = layer.rotation ?? layer.transform?.rotation ?? 0;
  const pivotX = layer.pivotX ?? layer.transform?.pivotX ?? 0.5;
  const pivotY = layer.pivotY ?? layer.transform?.pivotY ?? 0.5;
  const blur = layer.blur ?? layer.effects?.blur ?? 0;
  return withLegacyLayerFields({
    ...layer,
    type: normalizedType,
    ...normalizedType === "image" ? {
      assetKind: layer.assetKind === "sticker" || Boolean(
        layer.stickerDataUrl || layer.stickerPath || layer.stickerUrl
      ) ? "sticker" : "source",
      stickerDataUrl: layer.stickerDataUrl,
      stickerPath: layer.stickerPath,
      stickerUrl: layer.stickerUrl,
      stickerName: layer.stickerName,
      stickerWidth: layer.stickerWidth,
      stickerHeight: layer.stickerHeight,
      cropFocusX: layer.cropFocusX ?? 0.5,
      cropFocusY: layer.cropFocusY ?? 0.5,
      sourceIndex: layer.sourceIndex ?? layer.source?.slot ?? 1,
      source: {
        kind: "slot",
        slot: layer.sourceIndex ?? layer.source?.slot ?? 1
      },
      fit: layer.fit ?? "cover",
      maskPolygon: layer.maskPolygon
    } : {},
    rotation,
    pivotX,
    pivotY,
    opacity,
    blur,
    shadowBlur,
    shadowOffsetX,
    shadowOffsetY,
    shadowOpacity,
    transform: {
      rotation,
      pivotX,
      pivotY,
      opacity
    },
    effects: {
      blur,
      shadow: {
        blur: shadowBlur,
        offsetX: shadowOffsetX,
        offsetY: shadowOffsetY,
        opacity: shadowOpacity,
        color: layer.effects?.shadow?.color ?? getThemeColor("--mcr-cover-shadow")
      }
    },
    ...normalizedType !== "image" ? {
      fontFamily: layer.fontFamily ?? (normalizedType === "subtitle" ? "subtitle" : normalizedType === "text" ? "custom_text" : "main_title"),
      textAlign: layer.textAlign ?? "center",
      maskMode: layer.maskMode ?? "normal"
    } : {},
    ...normalizedType === "text" ? { content: layer.content ?? "自定义文本" } : {}
  });
}
function cloneLayout(layout) {
  return {
    ...layout,
    schema: layout.schema ?? "mcr-template/v1",
    version: layout.version,
    canvas: layout.canvas ? { ...layout.canvas } : layout.document ? { ...layout.document } : void 0,
    document: layout.document ? { ...layout.document } : void 0,
    background: layout.background ? {
      ...layout.background,
      imageSource: layout.background.imageSource ? { ...layout.background.imageSource } : void 0,
      colorSource: layout.background.colorSource ?? "auto",
      opacity: layout.background.opacity ?? layout.background.colorOpacity ?? 1,
      grain: layout.background.grain ?? 0
    } : void 0,
    assets: layout.assets ? { ...layout.assets } : void 0,
    layers: layout.layers.map((layer) => normalizeLayerEffects({ ...layer })),
    computed: layout.computed ? {
      ...layout.computed,
      textLayout: layout.computed.textLayout ? Object.fromEntries(
        Object.entries(layout.computed.textLayout).map(([key, value]) => [key, {
          ...value,
          frame: { ...value.frame },
          pivot: { ...value.pivot },
          shadow: { ...value.shadow },
          lines: value.lines.map((line) => ({ ...line }))
        }])
      ) : void 0
    } : void 0
  };
}
function createImageLayer(partial) {
  return normalizeLayerEffects({
    id: createLayoutId(),
    type: "image",
    sourceIndex: partial.sourceIndex,
    x: partial.x,
    y: partial.y,
    width: partial.width,
    height: partial.height,
    zIndex: partial.zIndex,
    rotation: partial.rotation ?? 0,
    radius: partial.radius ?? 0,
    pivotX: partial.pivotX ?? 0.5,
    pivotY: partial.pivotY ?? 0.5,
    opacity: partial.opacity,
    blur: partial.blur,
    shadowBlur: partial.shadowBlur,
    shadowOffsetX: partial.shadowOffsetX,
    shadowOffsetY: partial.shadowOffsetY,
    shadowOpacity: partial.shadowOpacity,
    assetKind: partial.assetKind,
    stickerDataUrl: partial.stickerDataUrl,
    stickerPath: partial.stickerPath,
    stickerUrl: partial.stickerUrl,
    stickerName: partial.stickerName,
    stickerWidth: partial.stickerWidth,
    stickerHeight: partial.stickerHeight,
    cropFocusX: partial.cropFocusX ?? 0.5,
    cropFocusY: partial.cropFocusY ?? 0.5,
    fit: partial.fit ?? "cover",
    maskPolygon: partial.maskPolygon,
    colorSource: partial.colorSource ?? "none",
    color: partial.color,
    colorRatio: partial.colorRatio ?? 0
  });
}
function createTitleLayer(partial) {
  const normalizedType = normalizeLayerType(partial.type);
  return normalizeLayerEffects({
    id: createLayoutId(),
    type: normalizedType === "subtitle" ? "subtitle" : "main_title",
    x: partial.x,
    y: partial.y,
    width: partial.width,
    height: partial.height,
    zIndex: partial.zIndex,
    fontSize: partial.fontSize,
    fontFamily: partial.fontFamily ?? (normalizedType === "subtitle" ? "subtitle" : "main_title"),
    rotation: partial.rotation ?? 0,
    radius: partial.radius ?? 0,
    pivotX: partial.pivotX ?? 0.5,
    pivotY: partial.pivotY ?? 0.5,
    opacity: partial.opacity,
    blur: partial.blur,
    shadowBlur: partial.shadowBlur,
    shadowOffsetX: partial.shadowOffsetX,
    shadowOffsetY: partial.shadowOffsetY,
    shadowOpacity: partial.shadowOpacity,
    maskMode: partial.maskMode ?? "normal"
  });
}
function createTextLayer(partial) {
  return normalizeLayerEffects({
    id: createLayoutId(),
    type: "text",
    content: partial?.content ?? "自定义文本",
    fontFamily: partial?.fontFamily ?? "custom_text",
    x: partial?.x ?? EDITOR_BASE_WIDTH * 0.1,
    y: partial?.y ?? EDITOR_BASE_HEIGHT * 0.72,
    width: partial?.width ?? EDITOR_BASE_WIDTH * 0.35,
    height: partial?.height ?? EDITOR_BASE_HEIGHT * 0.12,
    zIndex: partial?.zIndex ?? 10,
    fontSize: partial?.fontSize ?? 72,
    textAlign: partial?.textAlign ?? "center",
    rotation: partial?.rotation ?? 0,
    radius: partial?.radius ?? 0,
    pivotX: partial?.pivotX ?? 0.5,
    pivotY: partial?.pivotY ?? 0.5,
    opacity: partial?.opacity,
    blur: partial?.blur,
    shadowBlur: partial?.shadowBlur ?? 14,
    shadowOffsetX: partial?.shadowOffsetX ?? 0,
    shadowOffsetY: partial?.shadowOffsetY ?? 8,
    shadowOpacity: partial?.shadowOpacity ?? 0.2,
    maskMode: partial?.maskMode ?? "normal"
  });
}
function createDefaultLayout() {
  const width = EDITOR_BASE_WIDTH;
  const height = EDITOR_BASE_HEIGHT;
  const imageWidth = width * 0.6;
  const imageHeight = height * 0.8;
  return {
    schema: "mcr-template/v1",
    version: "1.0",
    canvas: {
      width,
      height,
      unit: "px"
    },
    background: {
      type: "blurred-image-color",
      imageSource: { kind: "slot", slot: 1 },
      colorSource: "auto",
      color: getThemeColor("--mcr-cover-auto-blend"),
      color2: getThemeColor("--mcr-cover-deep-gradient"),
      colorRatio: 0.8,
      opacity: 1,
      blur: 50,
      grain: 0.18,
      zIndex: 0
    },
    document: {
      width,
      height,
      unit: "px"
    },
    layers: [
      createImageLayer({
        sourceIndex: 1,
        x: width * 0.35,
        y: height * 0.1,
        width: imageWidth,
        height: imageHeight,
        radius: 32,
        zIndex: 1,
        shadowBlur: 24,
        shadowOffsetX: 0,
        shadowOffsetY: 18,
        shadowOpacity: 0.22
      }),
      createTitleLayer({
        type: "main_title",
        x: width * 0.05,
        y: height * 0.25,
        width: width * 0.3,
        height: height * 0.2,
        zIndex: 2,
        fontSize: 180,
        shadowBlur: 18,
        shadowOffsetX: 0,
        shadowOffsetY: 10,
        shadowOpacity: 0.24
      }),
      createTitleLayer({
        type: "subtitle",
        x: width * 0.05,
        y: height * 0.5,
        width: width * 0.3,
        height: height * 0.15,
        zIndex: 2,
        fontSize: 75,
        shadowBlur: 14,
        shadowOffsetX: 0,
        shadowOffsetY: 8,
        shadowOpacity: 0.2
      })
    ]
  };
}
function createLayoutFromBuiltInStyle(baseStyle) {
  if (baseStyle === "static_1") {
    return {
      version: "1.0",
      document: {
        width: EDITOR_BASE_WIDTH,
        height: EDITOR_BASE_HEIGHT,
        unit: "px"
      },
      layers: [
        createImageLayer({
          sourceIndex: 1,
          x: 1002,
          y: 162,
          width: 756,
          height: 756,
          rotation: 36,
          radius: 94,
          zIndex: 1,
          opacity: 0.56,
          blur: 8,
          shadowBlur: 12,
          shadowOffsetX: 10,
          shadowOffsetY: 16,
          shadowOpacity: 0.4
        }),
        createImageLayer({
          sourceIndex: 1,
          x: 1002,
          y: 162,
          width: 756,
          height: 756,
          rotation: 18,
          radius: 94,
          zIndex: 2,
          opacity: 0.74,
          blur: 4,
          shadowBlur: 15,
          shadowOffsetX: 15,
          shadowOffsetY: 22,
          shadowOpacity: 0.5
        }),
        createImageLayer({
          sourceIndex: 1,
          x: 1002,
          y: 162,
          width: 756,
          height: 756,
          rotation: 0,
          radius: 94,
          zIndex: 3,
          shadowBlur: 18,
          shadowOffsetX: 20,
          shadowOffsetY: 26,
          shadowOpacity: 0.6
        }),
        createTitleLayer({
          type: "main_title",
          x: 80,
          y: 340,
          width: 800,
          height: 180,
          zIndex: 4,
          fontSize: 170,
          shadowBlur: 12,
          shadowOffsetX: 12,
          shadowOffsetY: 12,
          shadowOpacity: 0.3
        }),
        createTitleLayer({
          type: "subtitle",
          x: 100,
          y: 540,
          width: 760,
          height: 140,
          zIndex: 4,
          fontSize: 75,
          shadowBlur: 10,
          shadowOffsetX: 8,
          shadowOffsetY: 8,
          shadowOpacity: 0.26
        })
      ]
    };
  }
  if (baseStyle === "static_2") {
    return {
      version: 1,
      background: {
        type: "blurred-image-color",
        imageSource: { kind: "slot", slot: 1 },
        colorSource: "auto",
        color: getThemeColor("--mcr-cover-auto-blend"),
        color2: getThemeColor("--mcr-cover-deep-gradient"),
        colorRatio: 0.42,
        opacity: 1,
        blur: 58,
        grain: 0.14,
        zIndex: 0
      },
      layers: [
        createImageLayer({
          sourceIndex: 1,
          x: 758,
          y: 0,
          width: 1162,
          height: 1080,
          zIndex: 1,
          radius: 0,
          cropFocusX: 0.75,
          cropFocusY: 0.5,
          shadowBlur: 20,
          shadowOffsetX: -18,
          shadowOffsetY: 0,
          shadowOpacity: 0.16,
          maskPolygon: {
            units: "relative",
            points: [[0.22, 0], [1, 0], [1, 1], [0, 1]]
          }
        }),
        createTitleLayer({
          type: "main_title",
          x: 80,
          y: 340,
          width: 800,
          height: 180,
          zIndex: 2,
          fontSize: 187,
          shadowBlur: 12,
          shadowOffsetX: 12,
          shadowOffsetY: 12,
          shadowOpacity: 0.24
        }),
        createTitleLayer({
          type: "subtitle",
          x: 100,
          y: 545,
          width: 760,
          height: 140,
          zIndex: 2,
          fontSize: 82,
          shadowBlur: 10,
          shadowOffsetX: 8,
          shadowOffsetY: 8,
          shadowOpacity: 0.22
        })
      ]
    };
  }
  if (baseStyle === "static_3") {
    const order = [3, 1, 5, 4, 2, 6, 9, 8, 7];
    const rowOffsets = [
      { x: 0, y: 0 },
      { x: -174, y: 618 },
      { x: -349, y: 1241 }
    ];
    const columnOffsets = [
      { x: 0, y: 0 },
      { x: 466, y: -7 },
      { x: 968, y: -112 }
    ];
    const positions = order.map((_, index) => {
      const column = Math.floor(index / 3);
      const row = index % 3;
      return {
        x: 977 + columnOffsets[column].x + rowOffsets[row].x,
        y: -334 + columnOffsets[column].y + rowOffsets[row].y
      };
    });
    const layers = order.map(
      (sourceIndex, index) => createImageLayer({
        sourceIndex,
        x: positions[index].x,
        y: positions[index].y,
        width: 410,
        height: 610,
        rotation: 15.8,
        radius: 46,
        zIndex: index + 1,
        shadowBlur: 18,
        shadowOffsetX: 10,
        shadowOffsetY: 14,
        shadowOpacity: 0.2
      })
    );
    layers.push(
      createTitleLayer({
        type: "main_title",
        x: -18,
        y: 383,
        width: 902,
        height: 124,
        zIndex: 20,
        fontSize: 170,
        shadowBlur: 10,
        shadowOffsetX: 8,
        shadowOffsetY: 8,
        shadowOpacity: 0.24
      })
    );
    layers.push(
      createTitleLayer({
        type: "subtitle",
        x: 124,
        y: 625,
        width: 620,
        height: 150,
        zIndex: 20,
        fontSize: 75,
        shadowBlur: 8,
        shadowOffsetX: 6,
        shadowOffsetY: 6,
        shadowOpacity: 0.2
      })
    );
    return { version: 1, layers };
  }
  if (baseStyle === "static_4") {
    return {
      version: 1,
      layers: [
        createTitleLayer({
          type: "main_title",
          x: 260,
          y: 360,
          width: 1400,
          height: 180,
          zIndex: 2,
          fontSize: 190,
          shadowBlur: 18,
          shadowOffsetY: 12,
          shadowOpacity: 0.24
        }),
        createTitleLayer({
          type: "subtitle",
          x: 320,
          y: 560,
          width: 1280,
          height: 150,
          zIndex: 2,
          fontSize: 80,
          shadowBlur: 14,
          shadowOffsetY: 8,
          shadowOpacity: 0.2
        })
      ]
    };
  }
  return createDefaultLayout();
}
function getLayerShadowStyle(layer) {
  const shadowBlur = Number(layer.shadowBlur ?? 0);
  const shadowOffsetX = Number(layer.shadowOffsetX ?? 0);
  const shadowOffsetY = Number(layer.shadowOffsetY ?? 0);
  const shadowOpacity = Number(layer.shadowOpacity ?? 0);
  if (shadowBlur <= 0 && shadowOffsetX === 0 && shadowOffsetY === 0) {
    return "none";
  }
  const alpha = Math.max(0, Math.min(0.9, shadowOpacity || 0.24));
  return `${shadowOffsetX}px ${shadowOffsetY}px ${Math.max(0, shadowBlur)}px ${getThemeRgba("--mcr-cover-shadow-rgb", alpha)}`;
}

const getDefaultBlendColor = () => getThemeColor("--mcr-cover-auto-blend");
const loadedImages = /* @__PURE__ */ new Map();
function getDocumentSize(layout) {
  return {
    width: Math.max(1, Number(layout?.document?.width || EDITOR_BASE_WIDTH)),
    height: Math.max(1, Number(layout?.document?.height || EDITOR_BASE_HEIGHT))
  };
}
function normalizeHexColor(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  const hex = raw.startsWith("#") ? raw : `#${raw}`;
  if (/^#[0-9a-fA-F]{6}$/.test(hex)) return hex.toLowerCase();
  return "";
}
function hexToRgb(hex) {
  const normalized = normalizeHexColor(hex) || normalizeHexColor(getDefaultBlendColor());
  return {
    r: parseInt(normalized.slice(1, 3), 16),
    g: parseInt(normalized.slice(3, 5), 16),
    b: parseInt(normalized.slice(5, 7), 16)
  };
}
function rgbToHex(r, g, b) {
  const toHex = (value) => Math.max(0, Math.min(255, Math.round(value))).toString(16).padStart(2, "0");
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}
function hexToRgba(hex, alpha) {
  const { r, g, b } = hexToRgb(hex);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
function rgbToHsl(r, g, b) {
  const rn = r / 255;
  const gn = g / 255;
  const bn = b / 255;
  const max = Math.max(rn, gn, bn);
  const min = Math.min(rn, gn, bn);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case rn:
        h = (gn - bn) / d + (gn < bn ? 6 : 0);
        break;
      case gn:
        h = (bn - rn) / d + 2;
        break;
      default:
        h = (rn - gn) / d + 4;
        break;
    }
    h /= 6;
  }
  return { h, s, l };
}
function hslToRgb(h, s, l) {
  if (s === 0) {
    const gray = l * 255;
    return { r: gray, g: gray, b: gray };
  }
  const hue2rgb = (p2, q2, t) => {
    let tt = t;
    if (tt < 0) tt += 1;
    if (tt > 1) tt -= 1;
    if (tt < 1 / 6) return p2 + (q2 - p2) * 6 * tt;
    if (tt < 1 / 2) return q2;
    if (tt < 2 / 3) return p2 + (q2 - p2) * (2 / 3 - tt) * 6;
    return p2;
  };
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;
  return {
    r: hue2rgb(p, q, h + 1 / 3) * 255,
    g: hue2rgb(p, q, h) * 255,
    b: hue2rgb(p, q, h - 1 / 3) * 255
  };
}
function adjustHexColor(hex, lightnessOffset) {
  const { r, g, b } = hexToRgb(hex);
  const { h, s, l } = rgbToHsl(r, g, b);
  const nextL = Math.min(0.84, Math.max(0.18, l + lightnessOffset));
  const nextS = Math.min(0.72, Math.max(0.24, s));
  const next = hslToRgb(h, nextS, nextL);
  return rgbToHex(next.r, next.g, next.b);
}
function darkenHexColor(hex, amount) {
  return adjustHexColor(hex, -Math.abs(amount));
}
function lightenHexColor(hex, amount) {
  return adjustHexColor(hex, Math.abs(amount));
}
function loadImage(src) {
  const cached = loadedImages.get(src);
  if (cached) return cached;
  const pending = new Promise((resolve, reject) => {
    const image = new Image();
    image.decoding = "async";
    image.onload = () => resolve(image);
    image.onerror = reject;
    image.src = src;
  });
  loadedImages.set(src, pending);
  return pending;
}
async function extractComfortableColor(src) {
  try {
    const image = await loadImage(src);
    const canvas = document.createElement("canvas");
    canvas.width = 48;
    canvas.height = 48;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    if (!context) return "";
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    const { data } = context.getImageData(0, 0, canvas.width, canvas.height);
    let totalR = 0;
    let totalG = 0;
    let totalB = 0;
    let totalWeight = 0;
    for (let index = 0; index < data.length; index += 4) {
      const alpha = data[index + 3];
      if (alpha < 160) continue;
      const r = data[index];
      const g = data[index + 1];
      const b = data[index + 2];
      const { s, l } = rgbToHsl(r, g, b);
      if (l < 0.16 || l > 0.86) continue;
      const weight = 0.55 + Math.min(0.45, s);
      totalR += r * weight;
      totalG += g * weight;
      totalB += b * weight;
      totalWeight += weight;
    }
    if (!totalWeight) return "";
    const base = rgbToHex(totalR / totalWeight, totalG / totalWeight, totalB / totalWeight);
    return adjustHexColor(base, -0.06);
  } catch (error) {
    console.error("extractComfortableColor failed", error);
    return "";
  }
}
function resolveBlendColor(source, params, autoColor = DEFAULT_BLEND_COLOR) {
  if (params.colorSource === "custom") {
    return normalizeHexColor(params.customColor) || autoColor;
  }
  if (params.colorSource === "config") {
    return normalizeHexColor(source?.bg_color || "") || autoColor;
  }
  return autoColor;
}
function buildBackgroundStyle(imageSrc, blur, strong = false) {
  return {
    backgroundImage: imageSrc ? `url(${imageSrc})` : "none",
    backgroundPosition: "center",
    backgroundSize: "cover",
    filter: `blur(${Math.max(0, blur) / (strong ? 10 : 8)}px)${strong ? " brightness(0.82)" : ""}`,
    transform: `scale(${strong ? 1.04 : 1.08})`
  };
}
function buildOverlayStyle(color, colorRatio) {
  return {
    background: hexToRgba(color, 1),
    opacity: String(Math.min(0.9, Math.max(0.08, colorRatio)))
  };
}
function getLayerFrameStyle(layer) {
  const normalized = normalizeLayerEffects(layer);
  return {
    left: `${normalized.x}px`,
    top: `${normalized.y}px`,
    width: `${normalized.width}px`,
    height: `${normalized.height}px`,
    zIndex: String(normalized.zIndex || 0)
  };
}
function getLayerTransformStyle(layer) {
  const normalized = normalizeLayerEffects(layer);
  return {
    transform: `rotate(${normalized.rotation || 0}deg)`,
    transformOrigin: `${(normalized.pivotX ?? 0.5) * 100}% ${(normalized.pivotY ?? 0.5) * 100}%`
  };
}
function getPreviewFontFamily(fontFamily, text) {
  return getTemplateFontFamilyStack(fontFamily, text);
}

const DEFAULT_SHADOW = {
  blur: 0,
  offsetX: 0,
  offsetY: 0,
  opacity: 0.28,
  color: getThemeColor("--mcr-cover-shadow")
};
function numberOr(value, fallback) {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}
function normalizeGroupLayer(layer) {
  const x = numberOr(layer.x, 0);
  const y = numberOr(layer.y, 0);
  const width = numberOr(layer.width, EDITOR_BASE_WIDTH);
  const height = numberOr(layer.height, EDITOR_BASE_HEIGHT);
  const rotation = numberOr(layer.rotation ?? layer.transform?.rotation, 0);
  const pivotX = numberOr(layer.pivotX ?? layer.transform?.pivotX, 0.5);
  const pivotY = numberOr(layer.pivotY ?? layer.transform?.pivotY, 0.5);
  const opacity = numberOr(layer.opacity ?? layer.transform?.opacity, 1);
  const shadow = {
    ...DEFAULT_SHADOW,
    ...layer.effects?.shadow || {},
    blur: numberOr(layer.shadowBlur ?? layer.effects?.shadow?.blur, DEFAULT_SHADOW.blur),
    offsetX: numberOr(layer.shadowOffsetX ?? layer.effects?.shadow?.offsetX, DEFAULT_SHADOW.offsetX),
    offsetY: numberOr(layer.shadowOffsetY ?? layer.effects?.shadow?.offsetY, DEFAULT_SHADOW.offsetY),
    opacity: numberOr(layer.shadowOpacity ?? layer.effects?.shadow?.opacity, DEFAULT_SHADOW.opacity)
  };
  const blur = numberOr(layer.blur ?? layer.effects?.blur, 0);
  return normalizeLayerEffects({
    id: layer.id || createLayoutId(),
    type: "group",
    x,
    y,
    width,
    height,
    zIndex: numberOr(layer.zIndex, 0),
    rotation,
    pivotX,
    pivotY,
    opacity,
    blur,
    shadowBlur: shadow.blur,
    shadowOffsetX: shadow.offsetX,
    shadowOffsetY: shadow.offsetY,
    shadowOpacity: shadow.opacity,
    children: (layer.children || []).map((child) => normalizeTemplateLayer(child)).filter(Boolean),
    effects: {
      blur,
      shadow
    }
  });
}
function normalizeTemplateLayer(layer) {
  if (!layer) return null;
  const normalizedType = layer.type === "group" ? "group" : normalizeLayerType(layer.type);
  if (normalizedType === "group") {
    return normalizeGroupLayer(layer);
  }
  const shadow = {
    ...DEFAULT_SHADOW,
    ...layer.effects?.shadow || {},
    blur: numberOr(layer.shadowBlur ?? layer.effects?.shadow?.blur, DEFAULT_SHADOW.blur),
    offsetX: numberOr(layer.shadowOffsetX ?? layer.effects?.shadow?.offsetX, DEFAULT_SHADOW.offsetX),
    offsetY: numberOr(layer.shadowOffsetY ?? layer.effects?.shadow?.offsetY, DEFAULT_SHADOW.offsetY),
    opacity: numberOr(layer.shadowOpacity ?? layer.effects?.shadow?.opacity, DEFAULT_SHADOW.opacity)
  };
  const blur = numberOr(layer.blur ?? layer.effects?.blur, 0);
  const textStyle = layer.textStyle || {};
  const rawMaskMode = layer.maskMode ?? textStyle.maskMode;
  const maskMode = rawMaskMode === "knockout-text" || rawMaskMode === "show-text" ? rawMaskMode : "normal";
  const normalized = normalizeLayerEffects({
    ...layer,
    id: layer.id || createLayoutId(),
    type: normalizedType,
    x: numberOr(layer.x, 0),
    y: numberOr(layer.y, 0),
    width: numberOr(layer.width, 1),
    height: numberOr(layer.height, 1),
    zIndex: numberOr(layer.zIndex, 0),
    rotation: numberOr(layer.rotation ?? layer.transform?.rotation, 0),
    pivotX: numberOr(layer.pivotX ?? layer.transform?.pivotX, 0.5),
    pivotY: numberOr(layer.pivotY ?? layer.transform?.pivotY, 0.5),
    opacity: numberOr(layer.opacity ?? layer.transform?.opacity, 1),
    blur,
    shadowBlur: shadow.blur,
    shadowOffsetX: shadow.offsetX,
    shadowOffsetY: shadow.offsetY,
    shadowOpacity: shadow.opacity,
    fontSize: numberOr(layer.fontSize, normalizedType === "subtitle" ? 75 : 170),
    textAlign: ["left", "center", "right"].includes(String(layer.textAlign)) ? layer.textAlign : "center",
    maskMode,
    content: layer.content ?? "自定义文本",
    assetKind: layer.assetKind === "sticker" || Boolean(
      layer.stickerDataUrl || layer.stickerPath || layer.stickerUrl
    ) ? "sticker" : "source",
    stickerDataUrl: layer.stickerDataUrl,
    stickerPath: layer.stickerPath,
    stickerUrl: layer.stickerUrl,
    stickerName: layer.stickerName,
    stickerWidth: numberOr(layer.stickerWidth, 0),
    stickerHeight: numberOr(layer.stickerHeight, 0),
    sourceIndex: numberOr(layer.sourceIndex ?? layer.source?.slot, 1),
    fit: layer.fit || "cover",
    source: {
      kind: "slot",
      slot: numberOr(layer.sourceIndex ?? layer.source?.slot, 1)
    },
    maskPolygon: layer.maskPolygon,
    effects: {
      blur,
      shadow
    }
  });
  return normalized;
}
function normalizeTemplate(layout) {
  const canvas = layout?.canvas || layout?.document || {
    width: EDITOR_BASE_WIDTH,
    height: EDITOR_BASE_HEIGHT};
  const width = numberOr(canvas.width, EDITOR_BASE_WIDTH);
  const height = numberOr(canvas.height, EDITOR_BASE_HEIGHT);
  return {
    ...layout,
    schema: "mcr-template/v1",
    version: layout?.version || "1.0",
    canvas: {
      width,
      height,
      unit: "px"
    },
    document: {
      width,
      height,
      unit: "px"
    },
    background: layout?.background || {
      type: "blurred-image-color",
      imageSource: { kind: "slot", slot: 1 },
      colorSource: "auto",
      color: getThemeColor("--mcr-cover-auto-blend"),
      color2: getThemeColor("--mcr-cover-deep-gradient"),
      colorRatio: 0.8,
      opacity: 1,
      blur: 50,
      grain: 0.18,
      zIndex: 0
    },
    assets: layout?.assets || {},
    layers: (layout?.layers || []).map((layer) => normalizeTemplateLayer(layer)).filter(Boolean),
    computed: layout?.computed
  };
}

function escapeXml(value) {
  return String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&apos;");
}
function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}
function getImageHref(source, slot) {
  const image = source?.images.find((item) => item.slot === slot) || source?.images[slot - 1];
  if (!image) return "";
  const src = image.src || image.url || image.href || "";
  return typeof src === "string" ? src : "";
}
function getImageMeta(source, slot) {
  return source?.images.find((item) => item.slot === slot) || source?.images[slot - 1] || null;
}
function isStickerLayerLike(layer) {
  return layer.assetKind === "sticker" || Boolean(layer.stickerDataUrl || layer.stickerPath || layer.stickerUrl);
}
const dataUrlObjectUrlCache = /* @__PURE__ */ new Map();
function dataUrlToObjectUrl(dataUrl) {
  if (!dataUrl.startsWith("data:image/") || typeof window === "undefined" || typeof Blob === "undefined" || typeof URL === "undefined" || typeof atob === "undefined") {
    return dataUrl;
  }
  const cached = dataUrlObjectUrlCache.get(dataUrl);
  if (cached) return cached;
  const commaIndex = dataUrl.indexOf(",");
  if (commaIndex <= 0) return dataUrl;
  const header = dataUrl.slice(0, commaIndex);
  const encoded = dataUrl.slice(commaIndex + 1);
  const mime = header.match(/^data:([^;]+);base64$/)?.[1] || "image/png";
  try {
    const binary = atob(encoded);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    const objectUrl = URL.createObjectURL(new Blob([bytes], { type: mime }));
    dataUrlObjectUrlCache.set(dataUrl, objectUrl);
    return objectUrl;
  } catch {
    return dataUrl;
  }
}
function getStickerPathUrl(path) {
  const normalized = String(path || "").trim();
  return normalized ? `/api/v1/plugin/YahahaCoverStudio/saved_cover_image?file=${encodeURIComponent(normalized)}` : "";
}
function normalizePluginImageUrl(url) {
  const normalized = String(url || "").trim();
  if (!normalized) return "";
  if (normalized.startsWith("plugin/")) return `/api/v1/${normalized}`;
  if (normalized.startsWith("/plugin/")) return `/api/v1${normalized}`;
  return normalized;
}
function getLayerImageHref(layer, source) {
  if (isStickerLayerLike(layer) && layer.stickerDataUrl) {
    return dataUrlToObjectUrl(layer.stickerDataUrl);
  }
  if (isStickerLayerLike(layer) && layer.stickerUrl) {
    return normalizePluginImageUrl(layer.stickerUrl);
  }
  if (isStickerLayerLike(layer) && layer.stickerPath) {
    return getStickerPathUrl(layer.stickerPath);
  }
  const slot = Number(layer.source?.slot ?? layer.sourceIndex ?? 1);
  return getImageHref(source, slot);
}
function getLayerImageMeta(layer, source) {
  if (isStickerLayerLike(layer)) {
    return {
      width: Number(layer.stickerWidth || layer.width || 0),
      height: Number(layer.stickerHeight || layer.height || 0)
    };
  }
  const slot = Number(layer.source?.slot ?? layer.sourceIndex ?? 1);
  return getImageMeta(source, slot);
}
function getLayerTransform(layer) {
  const rotation = Number(layer.rotation ?? layer.transform?.rotation ?? 0);
  if (!rotation) return "";
  const pivotX = clamp(Number(layer.pivotX ?? layer.transform?.pivotX ?? 0.5), 0, 1);
  const pivotY = clamp(Number(layer.pivotY ?? layer.transform?.pivotY ?? 0.5), 0, 1);
  const cx = Number(layer.x || 0) + Number(layer.width || 0) * pivotX;
  const cy = Number(layer.y || 0) + Number(layer.height || 0) * pivotY;
  return ` transform="rotate(${rotation} ${cx} ${cy})"`;
}
function getPreserveAspectRatio(layer) {
  if (layer.fit === "contain") return "xMidYMid meet";
  if (layer.fit === "stretch") return "none";
  return "xMidYMid slice";
}
function getPlaceholderColor(slot) {
  const hue = (Math.max(1, slot) * 47 + 178) % 360;
  return {
    fill: `hsl(${hue} 70% 34%)`,
    stroke: `hsl(${hue} 92% 72%)`
  };
}
function renderImagePlaceholder(layer) {
  const slot = Number(layer.source?.slot ?? layer.sourceIndex ?? 1);
  const colors = getPlaceholderColor(slot);
  const radius = Math.max(0, Number(layer.radius || 0));
  const inset = Math.max(14, Math.min(Number(layer.width || 0), Number(layer.height || 0)) * 0.08);
  const lineOpacity = 0.36;
  return [
    `<rect x="${layer.x}" y="${layer.y}" width="${layer.width}" height="${layer.height}" rx="${radius}" ry="${radius}" fill="${colors.fill}" opacity="0.42" stroke="${colors.stroke}" stroke-width="4"/>`,
    `<path d="M ${Number(layer.x) + inset} ${Number(layer.y) + inset} L ${Number(layer.x) + Number(layer.width) - inset} ${Number(layer.y) + Number(layer.height) - inset} M ${Number(layer.x) + Number(layer.width) - inset} ${Number(layer.y) + inset} L ${Number(layer.x) + inset} ${Number(layer.y) + Number(layer.height) - inset}" stroke="${colors.stroke}" stroke-width="3" opacity="${lineOpacity}"/>`,
    `<circle cx="${Number(layer.x) + Number(layer.width) * 0.5}" cy="${Number(layer.y) + Number(layer.height) * 0.5}" r="${Math.max(10, Math.min(Number(layer.width || 0), Number(layer.height || 0)) * 0.075)}" fill="none" stroke="${colors.stroke}" stroke-width="4" opacity="0.5"/>`
  ].join("");
}
function getFittedImageFrame(layer, source) {
  const image = getLayerImageMeta(layer, source);
  const sourceWidth = Number(image?.width || 0);
  const sourceHeight = Number(image?.height || 0);
  const targetWidth = Math.max(1, Number(layer.width || 1));
  const targetHeight = Math.max(1, Number(layer.height || 1));
  const fit = layer.fit || "cover";
  if (!sourceWidth || !sourceHeight || fit === "stretch") {
    return {
      x: Number(layer.x || 0),
      y: Number(layer.y || 0),
      width: targetWidth,
      height: targetHeight,
      preserveAspectRatio: getPreserveAspectRatio(layer),
      needsClip: Number(layer.radius || 0) > 0
    };
  }
  const scale = fit === "contain" ? Math.min(targetWidth / sourceWidth, targetHeight / sourceHeight) : Math.max(targetWidth / sourceWidth, targetHeight / sourceHeight);
  const drawWidth = sourceWidth * scale;
  const drawHeight = sourceHeight * scale;
  const focusX = clamp(Number(layer.cropFocusX ?? 0.5), 0, 1);
  const focusY = clamp(Number(layer.cropFocusY ?? 0.5), 0, 1);
  const overflowX = Math.max(0, drawWidth - targetWidth);
  const overflowY = Math.max(0, drawHeight - targetHeight);
  const insetX = Math.max(0, targetWidth - drawWidth) / 2;
  const insetY = Math.max(0, targetHeight - drawHeight) / 2;
  return {
    x: Number(layer.x || 0) + insetX - overflowX * focusX,
    y: Number(layer.y || 0) + insetY - overflowY * focusY,
    width: drawWidth,
    height: drawHeight,
    preserveAspectRatio: "none",
    needsClip: fit === "cover" || Number(layer.radius || 0) > 0
  };
}
function getFilterId(layer) {
  const blur = Number(layer.blur ?? layer.effects?.blur ?? 0);
  if (!blur) return "";
  return `fx-${escapeXml(layer.id)}`;
}
function renderFilter(layer, canvasWidth, canvasHeight) {
  const id = getFilterId(layer);
  if (!id) return "";
  const blur = Math.max(0, Number(layer.blur ?? layer.effects?.blur ?? 0));
  const nodes = [];
  if (blur) {
    nodes.push(`<feGaussianBlur in="SourceGraphic" stdDeviation="${blur}" result="blurred"/>`);
    nodes.push('<feMerge><feMergeNode in="blurred"/></feMerge>');
  }
  return `<filter id="${id}" x="${-canvasWidth}" y="${-canvasHeight}" width="${canvasWidth * 3}" height="${canvasHeight * 3}" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">${nodes.join("")}</filter>`;
}
function getMaskPolygonPoints(maskPolygon, x, y, width, height) {
  if (!maskPolygon || !Array.isArray(maskPolygon.points)) return "";
  const units = maskPolygon.units || "relative";
  const points = maskPolygon.points.map((point) => {
    if (!Array.isArray(point) || point.length < 2) return null;
    const px = Number(point[0]);
    const py = Number(point[1]);
    if (!Number.isFinite(px) || !Number.isFinite(py)) return null;
    return units === "relative" ? `${x + px * width},${y + py * height}` : `${x + px},${y + py}`;
  }).filter(Boolean);
  return points.length >= 3 ? points.join(" ") : "";
}
function getLayerMaskPolygonPoints(layer) {
  return getMaskPolygonPoints(
    layer.maskPolygon,
    Number(layer.x || 0),
    Number(layer.y || 0),
    Number(layer.width || 0),
    Number(layer.height || 0)
  );
}
function getShadowStyle(layer) {
  const shadowBlur = Math.max(0, Number(layer.shadowBlur ?? layer.effects?.shadow?.blur ?? 0));
  const shadowOffsetX = Number(layer.shadowOffsetX ?? layer.effects?.shadow?.offsetX ?? 0);
  const shadowOffsetY = Number(layer.shadowOffsetY ?? layer.effects?.shadow?.offsetY ?? 0);
  const shadowOpacity = clamp(Number(layer.shadowOpacity ?? layer.effects?.shadow?.opacity ?? 0.28), 0, 1);
  if (!shadowBlur && !shadowOffsetX && !shadowOffsetY) return null;
  return {
    blur: shadowBlur,
    offsetX: shadowOffsetX,
    offsetY: shadowOffsetY,
    opacity: shadowOpacity,
    color: layer.effects?.shadow?.color || getThemeColor("--mcr-cover-shadow")
  };
}
function renderDefs(layers, canvasWidth, canvasHeight) {
  const filterDefs = [];
  const clipDefs = [];
  const visit = (layer) => {
    const filter = renderFilter(layer, canvasWidth, canvasHeight);
    if (filter) filterDefs.push(filter);
    if (layer.type === "image") {
      const image = layer;
      const polygonPoints = getLayerMaskPolygonPoints(image);
      if (polygonPoints) {
        clipDefs.push(`<clipPath id="clip-${escapeXml(image.id)}" clipPathUnits="userSpaceOnUse"><polygon points="${polygonPoints}"/></clipPath>`);
      } else if (Number(image.radius || 0) > 0 || (image.fit || "cover") === "cover") {
        const radius = Math.max(0, Number(image.radius || 0));
        clipDefs.push(`<clipPath id="clip-${escapeXml(image.id)}" clipPathUnits="userSpaceOnUse"><rect x="${image.x}" y="${image.y}" width="${image.width}" height="${image.height}" rx="${radius}" ry="${radius}"/></clipPath>`);
      }
    }
    if (layer.type === "group") {
      layer.children.forEach(visit);
    }
  };
  layers.forEach(visit);
  return `<defs>${filterDefs.join("")}${clipDefs.join("")}</defs>`;
}
function wrapText(text, fontSize, maxWidth) {
  const chars = Array.from(text || "");
  const lines = [];
  let current = "";
  for (const char of chars) {
    const next = current + char;
    if (!current || next.length * fontSize * 0.56 <= maxWidth) {
      current = next;
    } else {
      lines.push(current);
      current = char;
    }
  }
  if (current) lines.push(current);
  return lines.length ? lines : [""];
}
function getTextContent(layer, source) {
  if (isCustomTextLayer(layer)) {
    const fallback = layer.content || "";
    if ((layer.contentSource || "fixed") !== "library") return fallback;
    const customTexts = source?.custom_texts || {};
    const key = String(layer.contentKey || "").trim();
    if (key && customTexts[key]) return customTexts[key];
    for (const defaultKey of ["default", "text", "custom_text", "content"]) {
      if (customTexts[defaultKey]) return customTexts[defaultKey];
    }
    return fallback;
  }
  if (isMainTitleLayer(layer)) return source?.titles.zh || source?.library || "";
  return source?.titles.en || "";
}
function getFontFamily(layer, text) {
  return getTemplateFontFamilyStack(layer.fontFamily || "main_title", text);
}
function getTextMaskMode(layer) {
  return layer.maskMode === "knockout-text" || layer.maskMode === "show-text" ? layer.maskMode : "normal";
}
function renderTextShape(layer, source, fill, fillOpacity = 1) {
  const text = getTextContent(layer, source);
  if (!text) return "";
  const fontSize = Math.max(1, Number(layer.fontSize || 60));
  const lines = wrapText(text, fontSize, Math.max(1, Number(layer.width || 1)));
  const lineHeight = fontSize * 1.1;
  const totalHeight = lines.length * lineHeight;
  const startY = Number(layer.y || 0) + (Number(layer.height || 0) - totalHeight) / 2 + fontSize;
  const align = layer.textAlign === "left" || layer.textAlign === "right" ? layer.textAlign : "center";
  const x = align === "left" ? Number(layer.x || 0) : align === "right" ? Number(layer.x || 0) + Number(layer.width || 0) : Number(layer.x || 0) + Number(layer.width || 0) / 2;
  const textAnchor = align === "left" ? "start" : align === "right" ? "end" : "middle";
  const tspans = lines.map(
    (line, index) => `<tspan x="${x}" y="${startY + index * lineHeight}">${escapeXml(line)}</tspan>`
  ).join("");
  const family = getFontFamily(layer, text);
  const opacity = clamp(Number(layer.opacity ?? layer.transform?.opacity ?? 1), 0, 1) * clamp(fillOpacity, 0, 1);
  return `<text font-family="${family}" font-size="${fontSize}" font-weight="700" fill="${fill}" fill-opacity="${opacity}" text-anchor="${textAnchor}"${getLayerTransform(layer)}>${tspans}</text>`;
}
function hasTextMaskLayer(layers, mode) {
  return layers.some((layer) => {
    if (layer.type === "group") return hasTextMaskLayer(layer.children || [], mode);
    if (!isTextLayer(layer)) return false;
    const nextMode = getTextMaskMode(layer);
    return mode ? nextMode === mode : nextMode !== "normal";
  });
}
function renderTextMaskNodes(layers, source, mode) {
  return layers.map((layer) => {
    if (layer.type === "group") {
      const children = renderTextMaskNodes(layer.children || [], source, mode);
      if (!children) return "";
      const opacity = clamp(Number(layer.opacity ?? layer.transform?.opacity ?? 1), 0, 1);
      return `<g${getLayerTransform(layer)} opacity="${opacity}">${children}</g>`;
    }
    if (!isTextLayer(layer) || getTextMaskMode(layer) !== mode) return "";
    return renderTextShape(layer, source, mode === "show-text" ? "#ffffff" : "#000000");
  }).join("");
}
function renderTextMaskDef(layers, source, width, height) {
  if (!hasTextMaskLayer(layers)) return "";
  const hasShowText = hasTextMaskLayer(layers, "show-text");
  const base = hasShowText ? `<rect x="0" y="0" width="${width}" height="${height}" fill="#000000"/>` : `<rect x="0" y="0" width="${width}" height="${height}" fill="#ffffff"/>`;
  const showNodes = renderTextMaskNodes(layers, source, "show-text");
  const knockoutNodes = renderTextMaskNodes(layers, source, "knockout-text");
  return `<mask id="mcr-text-mask" maskUnits="userSpaceOnUse" x="0" y="0" width="${width}" height="${height}">${base}${showNodes}${knockoutNodes}</mask>`;
}
function resolveTemplateColor(colorSource, customColor, source, params, autoBlendColor) {
  if (colorSource === "none") return "";
  if (colorSource === "custom") {
    return customColor || params.customColor || autoBlendColor || getThemeColor("--mcr-cover-auto-blend");
  }
  if (colorSource === "config") {
    return source?.bg_color || customColor || autoBlendColor || getThemeColor("--mcr-cover-auto-blend");
  }
  return autoBlendColor || resolveBlendColor(source, { ...params, colorSource: "auto" }, autoBlendColor || getThemeColor("--mcr-cover-auto-blend"));
}
function getBackgroundColor(template, source, params, autoBlendColor) {
  const background = template.background;
  return resolveTemplateColor(
    background?.colorSource || params.colorSource || "auto",
    background?.color,
    source,
    params,
    autoBlendColor
  );
}
function renderGrainOverlay(width, height, grain) {
  const opacity = clamp(Number(grain || 0), 0, 1);
  if (!opacity) return "";
  return `<rect x="0" y="0" width="${width}" height="${height}" fill="${escapeXml(getThemeColor("--mcr-cover-grain"))}" filter="url(#mcr-film-grain)" opacity="${Math.min(0.45, opacity * 0.72)}" style="mix-blend-mode:overlay"/>`;
}
function renderBackground(template, source, params, width, height, options) {
  const backgroundConfig = template.background || { type: "blurred-image-color" };
  const baseColor = getBackgroundColor(template, source, params, options.autoBlendColor);
  const wrapBackground = (content) => backgroundConfig.maskPolygon ? `<g clip-path="url(#mcr-bg-mask)">${content}</g>` : content;
  const backgroundOpacity = clamp(Number(backgroundConfig.opacity ?? backgroundConfig.colorOpacity ?? 1), 0, 1);
  const wrapBackgroundLayer = (content) => {
    const maskedContent = wrapBackground(content);
    if (!maskedContent || backgroundOpacity <= 0) return "";
    if (backgroundOpacity >= 1) return maskedContent;
    return `<g opacity="${backgroundOpacity}">${maskedContent}</g>`;
  };
  if (backgroundConfig.type === "transparent") {
    return "";
  }
  if (backgroundConfig.type === "solid") {
    return wrapBackgroundLayer(`<rect x="0" y="0" width="${width}" height="${height}" fill="${escapeXml(baseColor)}"/>${renderGrainOverlay(width, height, Number(backgroundConfig.grain ?? 0))}`);
  }
  if (backgroundConfig.type === "gradient") {
    return wrapBackgroundLayer(`<rect x="0" y="0" width="${width}" height="${height}" fill="url(#mcr-bg-gradient)"/>${renderGrainOverlay(width, height, Number(backgroundConfig.grain ?? 0))}`);
  }
  const firstImage = getImageHref(source, Number(backgroundConfig.imageSource?.slot || 1));
  const overlayOpacity = clamp(Number(backgroundConfig.colorRatio ?? params.colorRatio ?? 0.8), 0, 1);
  const blur = Math.max(0, Number(backgroundConfig.blur ?? params.blur ?? 0));
  const pad = Math.max(width, height) * 0.06;
  return wrapBackgroundLayer([
    `<rect x="0" y="0" width="${width}" height="${height}" fill="${escapeXml(baseColor)}"/>`,
    firstImage ? `<g filter="url(#mcr-bg-blur)" style="filter: blur(${blur}px);"><image href="${escapeXml(firstImage)}" xlink:href="${escapeXml(firstImage)}" x="${-pad}" y="${-pad}" width="${width + pad * 2}" height="${height + pad * 2}" preserveAspectRatio="xMidYMid slice" opacity="0.72"/></g>` : "",
    `<rect x="0" y="0" width="${width}" height="${height}" fill="${escapeXml(baseColor)}" opacity="${overlayOpacity}"/>`,
    renderGrainOverlay(width, height, Number(backgroundConfig.grain ?? 0))
  ].join(""));
}
function renderImageLayer(layer, source, options) {
  const href = getLayerImageHref(layer, source);
  const filterId = getFilterId(layer);
  const hasPolygonMask = Boolean(getLayerMaskPolygonPoints(layer));
  const hasClip = hasPolygonMask || Number(layer.radius || 0) > 0 || (layer.fit || "cover") === "cover";
  const clipPath = hasClip ? ` clip-path="url(#clip-${escapeXml(layer.id)})"` : "";
  const filter = filterId ? ` filter="url(#${filterId})"` : "";
  const opacity = clamp(Number(layer.opacity ?? layer.transform?.opacity ?? 1), 0, 1);
  const pointer = options.interactive ? ` data-layer-id="${escapeXml(layer.id)}" style="cursor:pointer"` : "";
  const escapedHref = escapeXml(href);
  const fitted = getFittedImageFrame(layer, source);
  const shadow = getShadowStyle(layer);
  const shadowClipPath = hasPolygonMask ? ` clip-path="url(#clip-${escapeXml(layer.id)})"` : "";
  const shadowNode = shadow ? `<rect x="${Number(layer.x) + shadow.offsetX}" y="${Number(layer.y) + shadow.offsetY}" width="${layer.width}" height="${layer.height}" rx="${Math.max(0, Number(layer.radius || 0))}" ry="${Math.max(0, Number(layer.radius || 0))}" fill="${escapeXml(shadow.color)}" opacity="${shadow.opacity}" style="filter: blur(${shadow.blur}px);"${shadowClipPath}/>` : "";
  const fittedClipPath = fitted.needsClip || hasPolygonMask ? ` clip-path="url(#clip-${escapeXml(layer.id)})"` : clipPath;
  const placeholderNode = href ? "" : renderImagePlaceholder(layer);
  const imageNode = href ? `<image href="${escapedHref}" xlink:href="${escapedHref}" x="${fitted.x}" y="${fitted.y}" width="${fitted.width}" height="${fitted.height}" preserveAspectRatio="${fitted.preserveAspectRatio}"${fittedClipPath}/>` : "";
  const colorRatio = clamp(Number(layer.colorRatio ?? 0), 0, 1);
  const blendColor = resolveTemplateColor(
    layer.colorSource || "none",
    layer.color,
    source,
    { blur: 50, colorRatio: 0.8, colorSource: "auto", customColor: getThemeColor("--mcr-cover-auto-blend") },
    options.autoBlendColor
  );
  const blendNode = blendColor && colorRatio > 0 ? `<rect x="${layer.x}" y="${layer.y}" width="${layer.width}" height="${layer.height}" rx="${Math.max(0, Number(layer.radius || 0))}" ry="${Math.max(0, Number(layer.radius || 0))}" fill="${escapeXml(blendColor)}" opacity="${colorRatio}"${hasClip ? ` clip-path="url(#clip-${escapeXml(layer.id)})"` : ""}/>` : "";
  return `<g${pointer}${getLayerTransform(layer)} opacity="${opacity}"${filter}>${shadowNode}${placeholderNode}${imageNode}${blendNode}</g>`;
}
function renderTextLayer(layer, source, options) {
  if (getTextMaskMode(layer) !== "normal") {
    return options.interactive ? `<rect data-layer-id="${escapeXml(layer.id)}" x="${layer.x}" y="${layer.y}" width="${layer.width}" height="${layer.height}" fill="transparent" style="cursor:pointer"${getLayerTransform(layer)}/>` : "";
  }
  const text = getTextContent(layer, source);
  const fontSize = Math.max(1, Number(layer.fontSize || 60));
  const lines = wrapText(text, fontSize, Math.max(1, Number(layer.width || 1)));
  const lineHeight = fontSize * 1.1;
  const totalHeight = lines.length * lineHeight;
  const startY = Number(layer.y || 0) + (Number(layer.height || 0) - totalHeight) / 2 + fontSize;
  const align = layer.textAlign === "left" || layer.textAlign === "right" ? layer.textAlign : "center";
  const x = align === "left" ? Number(layer.x || 0) : align === "right" ? Number(layer.x || 0) + Number(layer.width || 0) : Number(layer.x || 0) + Number(layer.width || 0) / 2;
  const textAnchor = align === "left" ? "start" : align === "right" ? "end" : "middle";
  const filterId = getFilterId(layer);
  const filter = filterId ? ` filter="url(#${filterId})"` : "";
  const opacity = clamp(Number(layer.opacity ?? layer.transform?.opacity ?? 1), 0, 1);
  const pointer = options.interactive ? ` data-layer-id="${escapeXml(layer.id)}" style="cursor:pointer"` : "";
  const tspans = lines.map(
    (line, index) => `<tspan x="${x}" y="${startY + index * lineHeight}">${escapeXml(line)}</tspan>`
  ).join("");
  const shadow = getShadowStyle(layer);
  const shadowTspans = lines.map(
    (line, index) => `<tspan x="${x + (shadow?.offsetX || 0)}" y="${startY + index * lineHeight + (shadow?.offsetY || 0)}">${escapeXml(line)}</tspan>`
  ).join("");
  const family = getFontFamily(layer, text);
  const shadowNode = shadow ? `<text font-family="${family}" font-size="${fontSize}" font-weight="700" fill="${escapeXml(shadow.color)}" opacity="${shadow.opacity}" text-anchor="${textAnchor}" style="filter: blur(${shadow.blur}px);">${shadowTspans}</text>` : "";
  const textColor = resolveTemplateColor(
    layer.colorSource || "custom",
    layer.color || getThemeColor("--mcr-cover-text"),
    source,
    { blur: 50, colorRatio: 0.8, colorSource: "custom", customColor: getThemeColor("--mcr-cover-text") },
    getThemeColor("--mcr-cover-text")
  ) || getThemeColor("--mcr-cover-text");
  return `<g${pointer}${getLayerTransform(layer)} opacity="${opacity}"${filter}>${shadowNode}<text font-family="${family}" font-size="${fontSize}" font-weight="700" fill="${escapeXml(textColor)}" text-anchor="${textAnchor}">${tspans}</text></g>`;
}
function renderSelection(layer) {
  if (!layer) return "";
  return `<rect x="${layer.x}" y="${layer.y}" width="${layer.width}" height="${layer.height}" fill="none" stroke="${escapeXml(getThemeColor("--mcr-cover-selection-stroke"))}" stroke-width="4" stroke-dasharray="16 10" pointer-events="none"${getLayerTransform(layer)}/>`;
}
function renderLayer(layer, source, options) {
  if (layer.type === "group") {
    const group = layer;
    const opacity = clamp(Number(group.opacity ?? group.transform?.opacity ?? 1), 0, 1);
    const pointer = options.interactive ? ` data-layer-id="${escapeXml(group.id)}" style="cursor:pointer"` : "";
    return `<g${pointer}${getLayerTransform(group)} opacity="${opacity}">${[...group.children || []].sort((a, b) => (a.zIndex || 0) - (b.zIndex || 0)).map((child) => renderLayer(child, source, options)).join("")}</g>`;
  }
  if (isImageLayer(layer)) return renderImageLayer(layer, source, options);
  if (isTextLayer(layer)) return renderTextLayer(layer, source, options);
  return "";
}
function findLayer(layers, id) {
  if (!id) return void 0;
  for (const layer of layers) {
    if (layer.id === id) return layer;
    if (layer.type === "group") {
      const child = findLayer(layer.children || [], id);
      if (child) return child;
    }
  }
  return void 0;
}
function renderTemplateSvg(layout, source, params, options = {}) {
  const template = normalizeTemplate(layout);
  const width = template.canvas?.width || 1920;
  const height = template.canvas?.height || 1080;
  const background = renderBackground(template, source, params, width, height, options);
  const bgBlur = Math.max(0, Number(template.background?.blur ?? params.blur ?? 0));
  const gradientColor = getBackgroundColor(template, source, params, options.autoBlendColor);
  const gradientColor2 = template.background?.color2 || getThemeColor("--mcr-cover-deep-gradient");
  const filmGrainFilter = '<filter id="mcr-film-grain" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="17" result="noise"/><feColorMatrix in="noise" type="matrix" values="0.33 0.33 0.33 0 0 0.33 0.33 0.33 0 0 0.33 0.33 0.33 0 0 0 0 0 0.48 0" result="monoNoise"/><feComponentTransfer in="monoNoise"><feFuncR type="linear" slope="1.8" intercept="-0.38"/><feFuncG type="linear" slope="1.8" intercept="-0.38"/><feFuncB type="linear" slope="1.8" intercept="-0.38"/></feComponentTransfer></filter>';
  const backgroundMaskPoints = getMaskPolygonPoints(template.background?.maskPolygon, 0, 0, width, height);
  const backgroundMaskDef = backgroundMaskPoints ? `<clipPath id="mcr-bg-mask" clipPathUnits="userSpaceOnUse"><polygon points="${backgroundMaskPoints}"/></clipPath>` : "";
  const textMaskDef = renderTextMaskDef(template.layers, source, width, height);
  const defs = `<defs><linearGradient id="mcr-bg-gradient" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="${escapeXml(gradientColor)}"/><stop offset="100%" stop-color="${escapeXml(gradientColor2)}"/></linearGradient>${backgroundMaskDef}${textMaskDef}${filmGrainFilter}<filter id="mcr-bg-blur" x="${-width}" y="${-height}" width="${width * 3}" height="${height * 3}" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB"><feGaussianBlur in="SourceGraphic" stdDeviation="${bgBlur}"/></filter></defs>${renderDefs(template.layers, width, height)}`;
  const layers = [...template.layers].sort((a, b) => (a.zIndex || 0) - (b.zIndex || 0));
  const backgroundZIndex = Number(template.background?.zIndex ?? 0);
  const underBackgroundLayers = layers.filter((layer) => Number(layer.zIndex || 0) < backgroundZIndex);
  const overBackgroundLayers = layers.filter((layer) => Number(layer.zIndex || 0) >= backgroundZIndex);
  const selectedLayer = findLayer(layers, options.selectedLayerId);
  const body = `${underBackgroundLayers.map((layer) => renderLayer(layer, source, options)).join("")}${background}${overBackgroundLayers.map((layer) => renderLayer(layer, source, options)).join("")}`;
  const maskedBody = textMaskDef ? `<g mask="url(#mcr-text-mask)">${body}</g>` : body;
  return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 ${width} ${height}" width="100%" height="100%" overflow="hidden" role="img" data-template-schema="mcr-template/v1">${defs}${maskedBody}${renderSelection(selectedLayer)}</svg>`;
}

const {defineComponent:_defineComponent$3} = await importShared('vue');

const {normalizeClass:_normalizeClass$3,openBlock:_openBlock$3,createElementBlock:_createElementBlock$3} = await importShared('vue');

const _hoisted_1$3 = ["innerHTML"];
const {computed: computed$4} = await importShared('vue');
const _sfc_main$3 = /* @__PURE__ */ _defineComponent$3({
  __name: "SvgTemplatePreview",
  props: {
    template: {},
    source: {},
    params: {},
    selectedLayerId: {},
    interactive: { type: Boolean },
    autoBlendColor: {}
  },
  emits: ["select-layer", "layer-pointer-down", "background-click"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const svgMarkup = computed$4(
      () => renderTemplateSvg(props.template, props.source, props.params, {
        selectedLayerId: props.selectedLayerId,
        interactive: props.interactive,
        autoBlendColor: props.autoBlendColor
      })
    );
    const hasTextMaskLayer = computed$4(() => {
      const visit = (layers) => layers.some((layer) => {
        if (!layer) return false;
        if (layer.type === "group") return visit(layer.children || []);
        return ["main_title", "subtitle", "title_zh", "title_en", "text"].includes(String(layer.type || "")) && ["knockout-text", "show-text"].includes(String(layer.maskMode || "normal"));
      });
      return visit(props.template?.layers || []);
    });
    function onPreviewClick(event) {
      if (!props.interactive) return;
      const target = event.target;
      const layerNode = target?.closest?.("[data-layer-id]");
      const layerId = layerNode?.getAttribute("data-layer-id");
      if (layerId) {
        emit("select-layer", layerId);
      } else {
        emit("background-click");
      }
    }
    function onPreviewPointerDown(event) {
      if (!props.interactive || event.button > 0) return;
      const target = event.target;
      const layerNode = target?.closest?.("[data-layer-id]");
      const layerId = layerNode?.getAttribute("data-layer-id");
      if (layerId) {
        emit("layer-pointer-down", layerId, event);
      }
    }
    return (_ctx, _cache) => {
      return _openBlock$3(), _createElementBlock$3("div", {
        class: _normalizeClass$3(["mcr-svg-template-preview", {
          "mcr-svg-template-preview--interactive": __props.interactive,
          "mcr-svg-template-preview--transparent": __props.template?.background?.type === "transparent" || hasTextMaskLayer.value
        }]),
        onClick: onPreviewClick,
        onPointerdown: onPreviewPointerDown,
        innerHTML: svgMarkup.value
      }, null, 42, _hoisted_1$3);
    };
  }
});

const SvgTemplatePreview = /* @__PURE__ */ _export_sfc(_sfc_main$3, [["__scopeId", "data-v-71d983d2"]]);

/*!
 * pinia v3.0.4
 * (c) 2025 Eduardo San Martin Morote
 * @license MIT
 */
const {hasInjectionContext,inject,toRaw,watch: watch$3,unref,markRaw,effectScope,ref: ref$3,isRef,isReactive,getCurrentScope,onScopeDispose,getCurrentInstance,reactive: reactive$1,toRef,nextTick: nextTick$3,computed: computed$3,toRefs} = await importShared('vue');
let activePinia;
const setActivePinia = (pinia) => activePinia = pinia;
const piniaSymbol = (
  /* istanbul ignore next */
  Symbol()
);
function isPlainObject(o) {
  return o && typeof o === "object" && Object.prototype.toString.call(o) === "[object Object]" && typeof o.toJSON !== "function";
}
var MutationType;
(function(MutationType2) {
  MutationType2["direct"] = "direct";
  MutationType2["patchObject"] = "patch object";
  MutationType2["patchFunction"] = "patch function";
})(MutationType || (MutationType = {}));
function createPinia() {
  const scope = effectScope(true);
  const state = scope.run(() => ref$3({}));
  let _p = [];
  let toBeInstalled = [];
  const pinia = markRaw({
    install(app) {
      setActivePinia(pinia);
      pinia._a = app;
      app.provide(piniaSymbol, pinia);
      app.config.globalProperties.$pinia = pinia;
      toBeInstalled.forEach((plugin) => _p.push(plugin));
      toBeInstalled = [];
    },
    use(plugin) {
      if (!this._a) {
        toBeInstalled.push(plugin);
      } else {
        _p.push(plugin);
      }
      return this;
    },
    _p,
    // it's actually undefined here
    // @ts-expect-error
    _a: null,
    _e: scope,
    _s: /* @__PURE__ */ new Map(),
    state
  });
  return pinia;
}
const noop = () => {
};
function addSubscription(subscriptions, callback, detached, onCleanup = noop) {
  subscriptions.add(callback);
  const removeSubscription = () => {
    const isDel = subscriptions.delete(callback);
    isDel && onCleanup();
  };
  if (!detached && getCurrentScope()) {
    onScopeDispose(removeSubscription);
  }
  return removeSubscription;
}
function triggerSubscriptions(subscriptions, ...args) {
  subscriptions.forEach((callback) => {
    callback(...args);
  });
}
const fallbackRunWithContext = (fn) => fn();
const ACTION_MARKER = Symbol();
const ACTION_NAME = Symbol();
function mergeReactiveObjects(target, patchToApply) {
  if (target instanceof Map && patchToApply instanceof Map) {
    patchToApply.forEach((value, key) => target.set(key, value));
  } else if (target instanceof Set && patchToApply instanceof Set) {
    patchToApply.forEach(target.add, target);
  }
  for (const key in patchToApply) {
    if (!patchToApply.hasOwnProperty(key))
      continue;
    const subPatch = patchToApply[key];
    const targetValue = target[key];
    if (isPlainObject(targetValue) && isPlainObject(subPatch) && target.hasOwnProperty(key) && !isRef(subPatch) && !isReactive(subPatch)) {
      target[key] = mergeReactiveObjects(targetValue, subPatch);
    } else {
      target[key] = subPatch;
    }
  }
  return target;
}
const skipHydrateSymbol = (
  /* istanbul ignore next */
  Symbol()
);
function shouldHydrate(obj) {
  return !isPlainObject(obj) || !Object.prototype.hasOwnProperty.call(obj, skipHydrateSymbol);
}
const { assign } = Object;
function isComputed(o) {
  return !!(isRef(o) && o.effect);
}
function createOptionsStore(id, options, pinia, hot) {
  const { state, actions, getters } = options;
  const initialState = pinia.state.value[id];
  let store;
  function setup() {
    if (!initialState && true) {
      pinia.state.value[id] = state ? state() : {};
    }
    const localState = toRefs(pinia.state.value[id]);
    return assign(localState, actions, Object.keys(getters || {}).reduce((computedGetters, name) => {
      computedGetters[name] = markRaw(computed$3(() => {
        setActivePinia(pinia);
        const store2 = pinia._s.get(id);
        return getters[name].call(store2, store2);
      }));
      return computedGetters;
    }, {}));
  }
  store = createSetupStore(id, setup, options, pinia, hot, true);
  return store;
}
function createSetupStore($id, setup, options = {}, pinia, hot, isOptionsStore) {
  let scope;
  const optionsForPlugin = assign({ actions: {} }, options);
  const $subscribeOptions = { deep: true };
  let isListening;
  let isSyncListening;
  let subscriptions = /* @__PURE__ */ new Set();
  let actionSubscriptions = /* @__PURE__ */ new Set();
  let debuggerEvents;
  const initialState = pinia.state.value[$id];
  if (!isOptionsStore && !initialState && true) {
    pinia.state.value[$id] = {};
  }
  ref$3({});
  let activeListener;
  function $patch(partialStateOrMutator) {
    let subscriptionMutation;
    isListening = isSyncListening = false;
    if (typeof partialStateOrMutator === "function") {
      partialStateOrMutator(pinia.state.value[$id]);
      subscriptionMutation = {
        type: MutationType.patchFunction,
        storeId: $id,
        events: debuggerEvents
      };
    } else {
      mergeReactiveObjects(pinia.state.value[$id], partialStateOrMutator);
      subscriptionMutation = {
        type: MutationType.patchObject,
        payload: partialStateOrMutator,
        storeId: $id,
        events: debuggerEvents
      };
    }
    const myListenerId = activeListener = Symbol();
    nextTick$3().then(() => {
      if (activeListener === myListenerId) {
        isListening = true;
      }
    });
    isSyncListening = true;
    triggerSubscriptions(subscriptions, subscriptionMutation, pinia.state.value[$id]);
  }
  const $reset = isOptionsStore ? function $reset2() {
    const { state } = options;
    const newState = state ? state() : {};
    this.$patch(($state) => {
      assign($state, newState);
    });
  } : (
    /* istanbul ignore next */
    noop
  );
  function $dispose() {
    scope.stop();
    subscriptions.clear();
    actionSubscriptions.clear();
    pinia._s.delete($id);
  }
  const action = (fn, name = "") => {
    if (ACTION_MARKER in fn) {
      fn[ACTION_NAME] = name;
      return fn;
    }
    const wrappedAction = function() {
      setActivePinia(pinia);
      const args = Array.from(arguments);
      const afterCallbackSet = /* @__PURE__ */ new Set();
      const onErrorCallbackSet = /* @__PURE__ */ new Set();
      function after(callback) {
        afterCallbackSet.add(callback);
      }
      function onError(callback) {
        onErrorCallbackSet.add(callback);
      }
      triggerSubscriptions(actionSubscriptions, {
        args,
        name: wrappedAction[ACTION_NAME],
        store,
        after,
        onError
      });
      let ret;
      try {
        ret = fn.apply(this && this.$id === $id ? this : store, args);
      } catch (error) {
        triggerSubscriptions(onErrorCallbackSet, error);
        throw error;
      }
      if (ret instanceof Promise) {
        return ret.then((value) => {
          triggerSubscriptions(afterCallbackSet, value);
          return value;
        }).catch((error) => {
          triggerSubscriptions(onErrorCallbackSet, error);
          return Promise.reject(error);
        });
      }
      triggerSubscriptions(afterCallbackSet, ret);
      return ret;
    };
    wrappedAction[ACTION_MARKER] = true;
    wrappedAction[ACTION_NAME] = name;
    return wrappedAction;
  };
  const partialStore = {
    _p: pinia,
    // _s: scope,
    $id,
    $onAction: addSubscription.bind(null, actionSubscriptions),
    $patch,
    $reset,
    $subscribe(callback, options2 = {}) {
      const removeSubscription = addSubscription(subscriptions, callback, options2.detached, () => stopWatcher());
      const stopWatcher = scope.run(() => watch$3(() => pinia.state.value[$id], (state) => {
        if (options2.flush === "sync" ? isSyncListening : isListening) {
          callback({
            storeId: $id,
            type: MutationType.direct,
            events: debuggerEvents
          }, state);
        }
      }, assign({}, $subscribeOptions, options2)));
      return removeSubscription;
    },
    $dispose
  };
  const store = reactive$1(partialStore);
  pinia._s.set($id, store);
  const runWithContext = pinia._a && pinia._a.runWithContext || fallbackRunWithContext;
  const setupStore = runWithContext(() => pinia._e.run(() => (scope = effectScope()).run(() => setup({ action }))));
  for (const key in setupStore) {
    const prop = setupStore[key];
    if (isRef(prop) && !isComputed(prop) || isReactive(prop)) {
      if (!isOptionsStore) {
        if (initialState && shouldHydrate(prop)) {
          if (isRef(prop)) {
            prop.value = initialState[key];
          } else {
            mergeReactiveObjects(prop, initialState[key]);
          }
        }
        pinia.state.value[$id][key] = prop;
      }
    } else if (typeof prop === "function") {
      const actionValue = action(prop, key);
      setupStore[key] = actionValue;
      optionsForPlugin.actions[key] = prop;
    } else ;
  }
  assign(store, setupStore);
  assign(toRaw(store), setupStore);
  Object.defineProperty(store, "$state", {
    get: () => pinia.state.value[$id],
    set: (state) => {
      $patch(($state) => {
        assign($state, state);
      });
    }
  });
  pinia._p.forEach((extender) => {
    {
      assign(store, scope.run(() => extender({
        store,
        app: pinia._a,
        pinia,
        options: optionsForPlugin
      })));
    }
  });
  if (initialState && isOptionsStore && options.hydrate) {
    options.hydrate(store.$state, initialState);
  }
  isListening = true;
  isSyncListening = true;
  return store;
}
/*! #__NO_SIDE_EFFECTS__ */
// @__NO_SIDE_EFFECTS__
function defineStore(id, setup, setupOptions) {
  let options;
  const isSetupStore = typeof setup === "function";
  options = isSetupStore ? setupOptions : setup;
  function useStore(pinia, hot) {
    const hasContext = hasInjectionContext();
    pinia = // in test mode, ignore the argument provided as we can always retrieve a
    // pinia instance with getActivePinia()
    (pinia) || (hasContext ? inject(piniaSymbol, null) : null);
    if (pinia)
      setActivePinia(pinia);
    pinia = activePinia;
    if (!pinia._s.has(id)) {
      if (isSetupStore) {
        createSetupStore(id, setup, options, pinia);
      } else {
        createOptionsStore(id, options, pinia);
      }
    }
    const store = pinia._s.get(id);
    return store;
  }
  useStore.$id = id;
  return useStore;
}

const pinia = createPinia();
setActivePinia(pinia);
const useTemplateCanvasStore = defineStore("mcr-template-canvas", {
  state: () => ({
    selectedLayerId: null
  }),
  actions: {
    selectLayer(id) {
      this.selectedLayerId = id;
    },
    resetSelection() {
      this.selectedLayerId = null;
    }
  }
});

const {defineComponent:_defineComponent$2} = await importShared('vue');

const {createTextVNode:_createTextVNode$1,resolveComponent:_resolveComponent$1,withCtx:_withCtx$1,createVNode:_createVNode$1,createElementVNode:_createElementVNode$2,openBlock:_openBlock$2,createElementBlock:_createElementBlock$2,createCommentVNode:_createCommentVNode$2,renderList:_renderList$2,Fragment:_Fragment$2,createBlock:_createBlock$2,toDisplayString:_toDisplayString$2,withModifiers:_withModifiers$1,withKeys:_withKeys$1,normalizeClass:_normalizeClass$2,normalizeStyle:_normalizeStyle$2,renderSlot:_renderSlot,Teleport:_Teleport$1,unref:_unref$1} = await importShared('vue');

const _hoisted_1$2 = ["data-loading"];
const _hoisted_2$2 = { class: "mcr-sticker-library__header" };
const _hoisted_3$2 = { class: "mcr-sticker-library__actions" };
const _hoisted_4$2 = {
  key: 0,
  class: "mcr-sticker-library__empty"
};
const _hoisted_5$2 = {
  key: 1,
  class: "mcr-sticker-library__empty"
};
const _hoisted_6$2 = {
  key: 2,
  class: "mcr-sticker-library__grid"
};
const _hoisted_7$2 = ["title", "onClick", "onKeydown"];
const _hoisted_8$2 = { class: "mcr-sticker-item__thumb" };
const _hoisted_9$2 = ["src", "alt"];
const _hoisted_10$2 = { class: "mcr-sticker-item__name" };
const _hoisted_11$2 = ["title", "onClick", "onKeydown"];
const _hoisted_12$2 = { class: "mcr-layout-stage-wrap" };
const _hoisted_13$2 = {
  key: 0,
  class: "mcr-snap-guides",
  "aria-hidden": "true"
};
const _hoisted_14$2 = {
  key: 1,
  class: "mcr-polygon-overlay"
};
const _hoisted_15$2 = {
  class: "mcr-polygon-overlay__svg",
  "aria-hidden": "true"
};
const _hoisted_16$2 = ["points"];
const _hoisted_17$2 = ["x1", "x2"];
const _hoisted_18$2 = ["y1", "y2"];
const _hoisted_19$2 = ["onPointerdown", "onDblclick"];
const _hoisted_20$2 = { class: "mcr-inline-editor__actions" };
const _hoisted_21$2 = { class: "mcr-layout-footer-slot" };
const _hoisted_22$2 = ["data-mcr-theme"];
const _hoisted_23$2 = {
  class: "mcr-layer-list",
  role: "listbox",
  "aria-label": "图层列表"
};
const _hoisted_24$2 = ["onClick"];
const _hoisted_25$2 = { class: "mcr-layer-list__content" };
const _hoisted_26$2 = { class: "mcr-layer-list__name" };
const _hoisted_27$2 = ["title", "onClick"];
const _hoisted_28$2 = {
  key: 0,
  class: "mcr-parameter-layer-header"
};
const _hoisted_29$2 = { class: "mcr-layer-button__label" };
const _hoisted_30$2 = {
  key: 1,
  class: "mcr-layer-list-wrapper mcr-background-panel"
};
const _hoisted_31$2 = {
  key: 3,
  class: "mcr-polygon-actions"
};
const _hoisted_32$2 = {
  key: 2,
  class: "mcr-layout-bottom mt-4"
};
const _hoisted_33$2 = {
  class: "mcr-text-align-control",
  "aria-label": "文字排版"
};
const _hoisted_34$1 = ["title", "aria-label", "aria-pressed", "onClick"];
const _hoisted_35$1 = {
  class: "mcr-aspect-presets",
  "aria-label": "宽高比例预设"
};
const _hoisted_36$1 = ["onClick"];
const {computed: computed$2,nextTick: nextTick$2,onMounted: onMounted$2,onUnmounted: onUnmounted$1,ref: ref$2,watch: watch$2} = await importShared('vue');
const CANVAS_WIDTH = 1920;
const CANVAS_HEIGHT = 1080;
const LAYER_POPOVER_WIDTH = 204;
const LAYER_POPOVER_FALLBACK_HEIGHT = 252;
const FLOATING_LAYER_MARGIN = 12;
const SNAP_THRESHOLD = 18;
const _sfc_main$2 = /* @__PURE__ */ _defineComponent$2({
  __name: "CustomLayoutEditor",
  props: {
    modelValue: {},
    previewSource: {},
    params: {},
    embedded: { type: Boolean },
    autoSaveEnabled: { type: Boolean },
    floatingToolsVisible: { type: Boolean, default: true },
    theme: { default: "light" },
    api: {}
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const lockAspectRatio = ref$2(false);
    const cropModeEnabled = ref$2(false);
    const floatingLayerListCollapsed = ref$2(true);
    const floatingLayerListPosition = ref$2({ x: FLOATING_LAYER_MARGIN, y: 120 });
    const layerListButtonWrapEl = ref$2(null);
    const floatingLayerListEl = ref$2(null);
    const inlineTextEditor = ref$2({
      visible: false,
      layerId: "",
      value: "",
      x: 0,
      y: 0,
      width: 320
    });
    const customFontItems = ref$2([]);
    const fontFamilyItems = computed$2(() => [
      ...SEMANTIC_FONT_ITEMS,
      ...BUILTIN_FONT_ITEMS,
      ...customFontItems.value.map((item) => ({ title: `自定义 ${item.title}`, value: item.value }))
    ]);
    const backgroundTypeItems = [
      { title: "透明背景", value: "transparent" },
      { title: "纯色", value: "solid" },
      { title: "渐变色", value: "gradient" },
      { title: "模糊主图混合所选颜色", value: "blurred-image-color" }
    ];
    const backgroundColorSourceItems = [
      { title: "从主图自动取色", value: "auto" },
      { title: "手动指定", value: "custom" },
      { title: "配置指定", value: "config" }
    ];
    const layerColorSourceItems = [
      { title: "不混色", value: "none" },
      { title: "从主图自动取色", value: "auto" },
      { title: "手动指定", value: "custom" },
      { title: "配置指定", value: "config" }
    ];
    const textColorSourceItems = [
      { title: "跟随主图/主题", value: "auto" },
      { title: "手动指定", value: "custom" },
      { title: "配置指定", value: "config" }
    ];
    const textAlignItems = [
      { title: "靠左", value: "left", icon: "mdi-format-align-left" },
      { title: "居中", value: "center", icon: "mdi-format-align-center" },
      { title: "靠右", value: "right", icon: "mdi-format-align-right" }
    ];
    const textContentSourceItems = [
      { title: "固定文本", value: "fixed" },
      { title: "按媒体库配置", value: "library" }
    ];
    const textMaskModeItems = [
      { title: "普通文字", value: "normal" },
      { title: "镂空字体区域", value: "knockout-text" },
      { title: "仅显示字体覆盖范围", value: "show-text" }
    ];
    const imageFitItems = [
      { title: "Cover 裁切填满", value: "cover" },
      { title: "Contain 完整显示", value: "contain" },
      { title: "Stretch 拉伸", value: "stretch" }
    ];
    const aspectRatioPresets = [
      { label: "1:1", ratio: 1 },
      { label: "4:3", ratio: 4 / 3 },
      { label: "3:4", ratio: 3 / 4 },
      { label: "16:9", ratio: 16 / 9 },
      { label: "9:16", ratio: 9 / 16 },
      { label: "3:2", ratio: 3 / 2 },
      { label: "2:3", ratio: 2 / 3 },
      { label: "21:9", ratio: 21 / 9 }
    ];
    const internalLayout = ref$2(cloneLayout(props.modelValue));
    const templateCanvasStore = useTemplateCanvasStore();
    const selectedLayerId = computed$2({
      get: () => templateCanvasStore.selectedLayerId ?? null,
      set: (id) => templateCanvasStore.selectLayer(id)
    });
    const editingBackground = computed$2(() => !selectedLayerId.value);
    const floatingLayerListStyle = computed$2(() => ({
      left: `${floatingLayerListPosition.value.x}px`,
      top: `${floatingLayerListPosition.value.y}px`
    }));
    const polygonSnapGuide = ref$2({ x: null, y: null });
    const activePolygonContext = computed$2(() => {
      if (editingBackground.value && layout.value.background?.maskPolygon) {
        return {
          target: "background",
          x: 0,
          y: 0,
          width: CANVAS_WIDTH,
          height: CANVAS_HEIGHT,
          mask: layout.value.background.maskPolygon
        };
      }
      const layer = selectedLayer.value;
      if (layer && isImageLayer(layer) && layer.maskPolygon) {
        return {
          target: "layer",
          layerId: layer.id,
          x: layer.x,
          y: layer.y,
          width: layer.width,
          height: layer.height,
          mask: layer.maskPolygon
        };
      }
      return null;
    });
    function normalizePolygonPoint(point, context) {
      if (context.mask.units === "absolute") {
        return [
          Math.max(0, Math.min(1, (Number(point[0]) - context.x) / Math.max(1, context.width))),
          Math.max(0, Math.min(1, (Number(point[1]) - context.y) / Math.max(1, context.height)))
        ];
      }
      return [
        Math.max(0, Math.min(1, Number(point[0]))),
        Math.max(0, Math.min(1, Number(point[1])))
      ];
    }
    const activePolygonRelativePoints = computed$2(() => {
      const context = activePolygonContext.value;
      if (!context) return [];
      return (context.mask.points || []).filter((point) => Array.isArray(point) && point.length >= 2).map((point) => normalizePolygonPoint(point, context));
    });
    const polygonOverlayPoints = computed$2(() => {
      const context = activePolygonContext.value;
      if (!context) return [];
      return activePolygonRelativePoints.value.map((point, index) => ({
        index,
        x: (context.x + point[0] * context.width) * canvasScale.value,
        y: (context.y + point[1] * context.height) * canvasScale.value
      }));
    });
    const polygonOverlayPointString = computed$2(
      () => polygonOverlayPoints.value.map((point) => `${point.x},${point.y}`).join(" ")
    );
    watch$2(
      () => props.modelValue,
      (val) => {
        const nextLayout = cloneLayout(val);
        internalLayout.value = nextLayout;
        const currentId = selectedLayerId.value;
        const existsInNew = currentId && findLayerById(nextLayout.layers, currentId);
        if (!existsInNew) {
          selectedLayerId.value = null;
        }
      },
      { deep: true }
    );
    watch$2(
      () => props.previewSource?.images,
      () => {
        if (typeof window !== "undefined") {
          refreshImageRegistry();
        }
      },
      { deep: true, immediate: true }
    );
    watch$2(
      () => getEditableLayers(internalLayout.value.layers).filter((layer) => isImageLayer(layer)).map((layer) => `${layer.id}:${layer.assetKind || ""}:${layer.stickerDataUrl || ""}:${layer.stickerUrl || ""}:${layer.stickerPath || ""}`).join("|"),
      () => {
        if (typeof window !== "undefined") {
          refreshImageRegistry();
        }
      }
    );
    watch$2(
      () => props.previewSource?.font_faces,
      async (fontFaces) => {
        await Promise.all(
          Object.entries(fontFaces || {}).map(([key, url]) => ensureFontFace(getTemplateFontFaceName(key), url))
        );
      },
      { deep: true, immediate: true }
    );
    const layout = computed$2(() => internalLayout.value);
    const editableLayerList = computed$2(() => getEditableLayers(layout.value.layers));
    const editorRootEl = ref$2(null);
    const canvasEl = ref$2(null);
    const canvasPaneEl = ref$2(null);
    const layerActionsEl = ref$2(null);
    const sidePaneEl = ref$2(null);
    const stickerFileInputEl = ref$2(null);
    const canvasScale = ref$2(1);
    const canvasPaneDisplayHeight = ref$2(0);
    const imageRegistry = ref$2({});
    const stickerLibraryOpen = ref$2(false);
    const stickerLibraryLoading = ref$2(false);
    const stickerLibraryItems = ref$2([]);
    const transformerRef = ref$2(null);
    const layerNodeRegistry = /* @__PURE__ */ new Map();
    let canvasResizeObserver = null;
    let canvasPaneResizeObserver = null;
    let windowResizeAttached = false;
    const loadedFontUrls = /* @__PURE__ */ new Map();
    const defaultAutoBlendColor = computed$2(() => getThemeColor("--mcr-cover-auto-blend"));
    const defaultDeepGradientColor = computed$2(() => getThemeColor("--mcr-cover-deep-gradient"));
    const defaultTextColor = computed$2(() => "#ffffff");
    function ensureFontFace(name, url) {
      if (!url || typeof FontFace === "undefined" || typeof document === "undefined") {
        return Promise.resolve();
      }
      const cacheKey = `${name}:${url}`;
      const cached = loadedFontUrls.get(cacheKey);
      if (cached) return cached;
      const pending = new FontFace(name, `url(${url})`).load().then((font) => {
        document.fonts.add(font);
      }).catch((error) => {
        console.error(`load editor font face failed: ${name}`, error);
      }).then(() => void 0);
      loadedFontUrls.set(cacheKey, pending);
      return pending;
    }
    async function loadFontLibrary() {
      if (!props.api?.get) return;
      try {
        const resp = await props.api.get("plugin/YahahaCoverStudio/fonts");
        if (!resp || resp.code !== 0) {
          throw new Error(resp?.msg || "load fonts failed");
        }
        customFontItems.value = Array.isArray(resp.data?.custom) ? resp.data.custom : [];
        await Promise.all(
          customFontItems.value.map((item) => ensureFontFace(getTemplateFontFaceName(item.value), item.url || item.dataUrl))
        );
      } catch (error) {
        console.warn("load editor font library failed", error);
      }
    }
    function getEditableLayers(layers) {
      return layers.flatMap((layer) => layer.type === "group" ? [layer, ...getEditableLayers(layer.children || [])] : [layer]);
    }
    function findLayerById(layers, id) {
      if (!id) return null;
      for (const layer of layers) {
        if (layer.id === id) return layer;
        if (layer.type === "group") {
          const child = findLayerById(layer.children || [], id);
          if (child) return child;
        }
      }
      return null;
    }
    function updateLayerById(layers, id, updater) {
      for (let index = 0; index < layers.length; index += 1) {
        const layer = layers[index];
        if (layer.id === id) {
          const updated = updater(layer);
          layers[index] = updated ? normalizeLayerEffects(updated) : normalizeLayerEffects({ ...layer });
          return true;
        }
        if (layer.type === "group") {
          const group = layer;
          if (updateLayerById(group.children || [], id, updater)) {
            layers[index] = normalizeLayerEffects({ ...group, children: [...group.children || []] });
            return true;
          }
        }
      }
      return false;
    }
    function removeLayerById(layers, id) {
      const index = layers.findIndex((layer) => layer.id === id);
      if (index !== -1) {
        layers.splice(index, 1);
        return true;
      }
      for (let layerIndex = 0; layerIndex < layers.length; layerIndex += 1) {
        const layer = layers[layerIndex];
        if (layer.type !== "group") continue;
        const group = layer;
        if (removeLayerById(group.children || [], id)) {
          layers[layerIndex] = normalizeLayerEffects({ ...group, children: [...group.children || []] });
          return true;
        }
      }
      return false;
    }
    function updateLayout(mutator) {
      const next = cloneLayout(internalLayout.value);
      mutator(next);
      internalLayout.value = next;
      emit("update:modelValue", next);
    }
    function updateBackgroundString(key, value) {
      updateLayout((layout2) => {
        layout2.background = {
          type: "blurred-image-color",
          imageSource: { kind: "slot", slot: 1 },
          colorSource: "auto",
          color: editorBlendColor.value,
          color2: defaultDeepGradientColor.value,
          colorRatio: effectiveParams.value.colorRatio,
          opacity: 1,
          blur: effectiveParams.value.blur,
          grain: 0.18,
          zIndex: 0,
          ...layout2.background || {},
          [key]: value
        };
      });
    }
    function updateBackgroundNumeric(key, raw) {
      const num = typeof raw === "number" ? raw : Number(raw);
      if (Number.isNaN(num)) return;
      updateLayout((layout2) => {
        layout2.background = {
          type: "blurred-image-color",
          imageSource: { kind: "slot", slot: 1 },
          colorSource: "auto",
          color: editorBlendColor.value,
          color2: defaultDeepGradientColor.value,
          colorRatio: effectiveParams.value.colorRatio,
          opacity: 1,
          blur: effectiveParams.value.blur,
          grain: 0.18,
          zIndex: 0,
          ...layout2.background || {},
          [key]: num
        };
      });
    }
    const selectedLayer = computed$2(() => {
      return findLayerById(layout.value.layers, selectedLayerId.value);
    });
    const currentLayerButtonLabel = computed$2(() => selectedLayer.value ? layerLabel(selectedLayer.value) : "背景");
    computed$2(() => {
      const layer = selectedLayer.value;
      if (!layer) return "图层";
      if (layer.type === "group") return "图层组";
      if (isImageLayer(layer)) return layer.assetKind === "sticker" ? "贴图图层" : "图片图层";
      if (isCustomTextLayer(layer)) return "文本图层";
      return isMainTitleLayer(layer) ? "主标题图层" : "副标题图层";
    });
    const activeTitles = computed$2(() => props.previewSource?.titles || { zh: "", en: "" });
    const firstImage = computed$2(() => props.previewSource?.images?.[0] || null);
    const autoBlendColor = ref$2(getThemeColor("--mcr-cover-auto-blend"));
    const effectiveParams = computed$2(() => props.params || {
      blur: 50,
      colorRatio: 0.8,
      colorSource: "auto",
      customColor: defaultAutoBlendColor.value
    });
    const editorBlendColor = computed$2(() => resolveBlendColor(props.previewSource || null, effectiveParams.value, autoBlendColor.value));
    computed$2(() => buildBackgroundStyle(firstImage.value?.src, effectiveParams.value.blur));
    computed$2(() => buildOverlayStyle(editorBlendColor.value, effectiveParams.value.colorRatio));
    computed$2(() => ({
      transform: `scale(${canvasScale.value})`
    }));
    computed$2(() => ({
      width: CANVAS_WIDTH,
      height: CANVAS_HEIGHT
    }));
    const CANVAS_VERTICAL_SNAP_TARGETS = [0, CANVAS_WIDTH / 4, CANVAS_WIDTH / 2, CANVAS_WIDTH * 3 / 4, CANVAS_WIDTH];
    const CANVAS_HORIZONTAL_SNAP_TARGETS = [0, CANVAS_HEIGHT / 4, CANVAS_HEIGHT / 2, CANVAS_HEIGHT * 3 / 4, CANVAS_HEIGHT];
    const activeSnapGuides = ref$2({ vertical: [], horizontal: [] });
    const activeSnapGuideStyles = computed$2(() => ({
      vertical: activeSnapGuides.value.vertical.map((value) => ({
        value,
        position: `${value * canvasScale.value}px`
      })),
      horizontal: activeSnapGuides.value.horizontal.map((value) => ({
        value,
        position: `${value * canvasScale.value}px`
      }))
    }));
    function uniqueGuideValues(values) {
      return Array.from(new Set(
        values.filter((value) => Number.isFinite(Number(value))).map((value) => Math.round(value))
      ));
    }
    function snapAxisPosition(position, size, targets) {
      const anchors = [0, size / 2, size];
      let bestDelta = 0;
      let bestTarget = null;
      let bestDistance = Number.POSITIVE_INFINITY;
      for (const anchor of anchors) {
        const current = position + anchor;
        for (const target of targets) {
          const distance = Math.abs(current - target);
          if (distance <= SNAP_THRESHOLD && distance < bestDistance) {
            bestDistance = distance;
            bestDelta = target - current;
            bestTarget = target;
          }
        }
      }
      return {
        position: bestTarget === null ? position : position + bestDelta,
        guide: bestTarget
      };
    }
    function snapLayerPosition(x, y, layer) {
      const snapX = snapAxisPosition(x, Number(layer.width || 0), CANVAS_VERTICAL_SNAP_TARGETS);
      const snapY = snapAxisPosition(y, Number(layer.height || 0), CANVAS_HORIZONTAL_SNAP_TARGETS);
      activeSnapGuides.value = {
        vertical: uniqueGuideValues([snapX.guide]),
        horizontal: uniqueGuideValues([snapY.guide])
      };
      return {
        x: snapX.position,
        y: snapY.position
      };
    }
    function buildGuideLine(points) {
      return {
        points,
        stroke: getThemeRgba("--mcr-editor-snap-rgb", 0.92),
        strokeWidth: 2,
        dash: [10, 8],
        listening: false
      };
    }
    function findTextSnapTargets(layer) {
      if (isImageLayer(layer)) return { vertical: null, horizontal: null };
      const currentLeft = layer.x;
      const currentCenterX = layer.x + layer.width / 2;
      const currentRight = layer.x + layer.width;
      const currentTop = layer.y;
      const currentCenterY = layer.y + layer.height / 2;
      const currentBottom = layer.y + layer.height;
      let vertical = null;
      let horizontal = null;
      const candidates = layout.value.layers.filter((item) => item.id !== layer.id && !isImageLayer(item));
      for (const item of candidates) {
        const left = item.x;
        const centerX = item.x + item.width / 2;
        const right = item.x + item.width;
        const top = item.y;
        const centerY = item.y + item.height / 2;
        const bottom = item.y + item.height;
        if (!vertical) {
          if (Math.abs(currentCenterX - centerX) <= SNAP_THRESHOLD) vertical = buildGuideLine([centerX, 0, centerX, CANVAS_HEIGHT]);
          else if (Math.abs(currentLeft - left) <= SNAP_THRESHOLD) vertical = buildGuideLine([left, 0, left, CANVAS_HEIGHT]);
          else if (Math.abs(currentRight - right) <= SNAP_THRESHOLD) vertical = buildGuideLine([right, 0, right, CANVAS_HEIGHT]);
        }
        if (!horizontal) {
          if (Math.abs(currentCenterY - centerY) <= SNAP_THRESHOLD) horizontal = buildGuideLine([0, centerY, CANVAS_WIDTH, centerY]);
          else if (Math.abs(currentTop - top) <= SNAP_THRESHOLD) horizontal = buildGuideLine([0, top, CANVAS_WIDTH, top]);
          else if (Math.abs(currentBottom - bottom) <= SNAP_THRESHOLD) horizontal = buildGuideLine([0, bottom, CANVAS_WIDTH, bottom]);
        }
        if (vertical && horizontal) break;
      }
      return { vertical, horizontal };
    }
    const alignmentGuides = computed$2(() => {
      const layer = selectedLayer.value;
      if (!layer || isImageLayer(layer)) {
        return { vertical: null, horizontal: null };
      }
      const layerCenterX = layer.x + layer.width / 2;
      const layerCenterY = layer.y + layer.height / 2;
      const stageCenterX = CANVAS_WIDTH / 2;
      const stageCenterY = CANVAS_HEIGHT / 2;
      const ownVertical = Math.abs(layerCenterX - stageCenterX) <= SNAP_THRESHOLD ? buildGuideLine([stageCenterX, 0, stageCenterX, CANVAS_HEIGHT]) : null;
      const ownHorizontal = Math.abs(layerCenterY - stageCenterY) <= SNAP_THRESHOLD ? buildGuideLine([0, stageCenterY, CANVAS_WIDTH, stageCenterY]) : null;
      const peer = findTextSnapTargets(layer);
      return {
        vertical: ownVertical || peer.vertical,
        horizontal: ownHorizontal || peer.horizontal
      };
    });
    computed$2(() => Boolean(alignmentGuides.value.vertical || alignmentGuides.value.horizontal));
    const inlineEditorStyle = computed$2(() => ({
      left: `${inlineTextEditor.value.x * canvasScale.value}px`,
      top: `${inlineTextEditor.value.y * canvasScale.value}px`,
      width: `${inlineTextEditor.value.width * canvasScale.value}px`
    }));
    computed$2(() => ({
      rotateEnabled: true,
      enabledAnchors: [
        "top-left",
        "top-center",
        "top-right",
        "middle-left",
        "middle-right",
        "bottom-left",
        "bottom-center",
        "bottom-right"
      ],
      borderStroke: getThemeColor("--mcr-color-primary-container"),
      anchorStroke: getThemeColor("--mcr-color-primary-container"),
      anchorFill: getThemeColor("--mcr-color-surface-container-lowest"),
      anchorSize: 10,
      keepRatio: lockAspectRatio.value
    }));
    function updateCanvasScale() {
      const canvas = canvasEl.value;
      if (!canvas) return;
      const width = canvas.clientWidth || 1;
      canvasScale.value = width / CANVAS_WIDTH;
      canvasPaneDisplayHeight.value = canvasPaneEl.value?.clientHeight || canvas.clientHeight || Math.round(width * CANVAS_HEIGHT / CANVAS_WIDTH);
      positionFloatingLayerListNearToolbar();
    }
    const layoutSidePaneStyle = computed$2(() => canvasPaneDisplayHeight.value > 0 ? { height: `${canvasPaneDisplayHeight.value}px` } : void 0);
    function isScrollableContainer(el) {
      const style = window.getComputedStyle(el);
      return /(auto|scroll|overlay)/.test(style.overflowY) && el.scrollHeight > el.clientHeight + 2;
    }
    function captureEditorScrollSnapshot() {
      if (typeof window === "undefined") return [];
      const snapshot = [];
      const seen = /* @__PURE__ */ new Set();
      const root = editorRootEl.value;
      let current = root?.parentElement || null;
      while (current && current !== document.body && current !== document.documentElement) {
        if (isScrollableContainer(current) && !seen.has(current)) {
          seen.add(current);
          snapshot.push({ el: current, top: current.scrollTop, left: current.scrollLeft });
        }
        current = current.parentElement;
      }
      document.querySelectorAll("*").forEach((el) => {
        if (seen.has(el)) return;
        if (!isScrollableContainer(el)) return;
        seen.add(el);
        snapshot.push({ el, top: el.scrollTop, left: el.scrollLeft });
      });
      const documentScroller = document.scrollingElement;
      if (documentScroller && !seen.has(documentScroller)) {
        snapshot.push({ el: documentScroller, top: documentScroller.scrollTop, left: documentScroller.scrollLeft });
      }
      return snapshot;
    }
    function restoreEditorScrollSnapshot(snapshot) {
      for (const item of snapshot) {
        item.el.scrollTop = item.top;
        item.el.scrollLeft = item.left;
      }
    }
    function preserveEditorScrollAfter(callback) {
      const snapshot = captureEditorScrollSnapshot();
      callback();
      nextTick$2(() => {
        restoreEditorScrollSnapshot(snapshot);
        if (typeof window !== "undefined") {
          window.requestAnimationFrame(() => restoreEditorScrollSnapshot(snapshot));
          window.setTimeout(() => restoreEditorScrollSnapshot(snapshot), 120);
          window.setTimeout(() => restoreEditorScrollSnapshot(snapshot), 260);
        }
      });
    }
    function selectLayer(id) {
      preserveEditorScrollAfter(() => {
        selectedLayerId.value = id;
      });
      nextTick$2(() => attachTransformer());
    }
    function selectBackground() {
      preserveEditorScrollAfter(() => {
        selectedLayerId.value = null;
        cropModeEnabled.value = false;
      });
      nextTick$2(() => attachTransformer());
    }
    function closeFloatingLayerList() {
      floatingLayerListCollapsed.value = true;
      if (typeof window !== "undefined") {
        window.removeEventListener("click", onFloatingLayerListDocumentClick);
      }
    }
    function selectLayerFromLayerList(id) {
      selectLayer(id);
      closeFloatingLayerList();
    }
    function selectBackgroundFromLayerList() {
      selectBackground();
      closeFloatingLayerList();
    }
    function positionFloatingLayerListNearToolbar() {
      if (typeof window === "undefined") return;
      const anchor = layerListButtonWrapEl.value;
      const rect = anchor?.getBoundingClientRect();
      const width = LAYER_POPOVER_WIDTH;
      const popoverHeight = floatingLayerListEl.value?.offsetHeight ?? LAYER_POPOVER_FALLBACK_HEIGHT;
      const fallbackX = window.innerWidth - width - FLOATING_LAYER_MARGIN;
      const fallbackY = 96;
      const targetX = rect ? rect.right - width : fallbackX;
      const shouldOpenAbove = rect ? rect.bottom + 8 + popoverHeight > window.innerHeight - FLOATING_LAYER_MARGIN : false;
      const targetY = rect ? shouldOpenAbove ? rect.top - popoverHeight - 8 : rect.bottom + 8 : fallbackY;
      floatingLayerListPosition.value = {
        x: Math.max(FLOATING_LAYER_MARGIN, Math.min(window.innerWidth - width - FLOATING_LAYER_MARGIN, targetX)),
        y: Math.max(FLOATING_LAYER_MARGIN, Math.min(window.innerHeight - popoverHeight - FLOATING_LAYER_MARGIN, targetY))
      };
    }
    function onFloatingLayerListDocumentClick(event) {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (floatingLayerListEl.value?.contains(target) || layerListButtonWrapEl.value?.contains(target)) return;
      closeFloatingLayerList();
    }
    function getStickerPathUrl(path) {
      const normalized = String(path || "").trim();
      return normalized ? `/api/v1/plugin/YahahaCoverStudio/saved_cover_image?file=${encodeURIComponent(normalized)}` : "";
    }
    function normalizePluginImageUrl(url) {
      const normalized = String(url || "").trim();
      if (!normalized) return "";
      if (normalized.startsWith("plugin/")) return `/api/v1/${normalized}`;
      if (normalized.startsWith("/plugin/")) return `/api/v1${normalized}`;
      return normalized;
    }
    function getLayerStickerSrc(layer) {
      return layer.stickerDataUrl || normalizePluginImageUrl(layer.stickerUrl) || getStickerPathUrl(layer.stickerPath);
    }
    function getLayerPreviewText(layer) {
      if (isCustomTextLayer(layer)) {
        const fallback = layer.content || "未定义文本";
        if ((layer.contentSource || "fixed") !== "library") return fallback;
        const customTexts = props.previewSource?.custom_texts || {};
        const key = String(layer.contentKey || "").trim();
        if (key && customTexts[key]) return customTexts[key];
        for (const defaultKey of ["default", "text", "custom_text", "content"]) {
          if (customTexts[defaultKey]) return customTexts[defaultKey];
        }
        return fallback;
      }
      if (isMainTitleLayer(layer)) {
        return activeTitles.value.zh || "未定义主标题";
      }
      return activeTitles.value.en || "未定义副标题";
    }
    function layerLabel(layer) {
      if (layer.type === "group") {
        return "图层组";
      }
      if (isImageLayer(layer)) {
        if (layer.assetKind === "sticker") {
          const name = (layer.stickerName || "贴图").replace(/\.[a-z0-9]+$/i, "");
          return `贴图: ${name.slice(0, 10)}`;
        }
        return `图片 ${layer.sourceIndex}`;
      }
      if (isCustomTextLayer(layer)) {
        return `文本: ${getLayerPreviewText(layer).slice(0, 10)}`;
      }
      return isMainTitleLayer(layer) ? "主标题" : "副标题";
    }
    function layerListIcon(layer) {
      if (layer.type === "group") {
        return "mdi-layers-triple-outline";
      }
      if (isImageLayer(layer)) {
        if (layer.assetKind === "sticker") return "mdi-sticker-outline";
        return "mdi-image-outline";
      }
      if (isCustomTextLayer(layer)) {
        return "mdi-text-box-outline";
      }
      return isMainTitleLayer(layer) ? "mdi-format-title" : "mdi-subtitles-outline";
    }
    function cancelInlineTextEdit() {
      inlineTextEditor.value.visible = false;
    }
    function commitInlineTextEdit() {
      const { layerId, value } = inlineTextEditor.value;
      if (!layerId) {
        inlineTextEditor.value.visible = false;
        return;
      }
      updateLayout((layout2) => {
        const index = layout2.layers.findIndex((item) => item.id === layerId);
        if (index === -1) return;
        const layer = layout2.layers[index];
        if (!isCustomTextLayer(layer)) return;
        layout2.layers[index] = {
          ...layer,
          content: value
        };
      });
      inlineTextEditor.value.visible = false;
      nextTick$2(() => attachTransformer());
    }
    function attachTransformer() {
      const raw = transformerRef.value;
      const transformer = raw?.getNode?.() || raw?.node?.getNode?.() || raw?.node || raw;
      if (!transformer || typeof transformer.nodes !== "function") return;
      const selectedId = selectedLayerId.value;
      const node = selectedId ? layerNodeRegistry.get(selectedId) : null;
      transformer.nodes(node ? [node] : []);
      if (typeof transformer.getLayer === "function") {
        transformer.getLayer()?.batchDraw?.();
      }
    }
    function refreshImageRegistry() {
      const next = {};
      for (const image of props.previewSource?.images || []) {
        if (!image?.src) continue;
        const instance = new window.Image();
        instance.src = image.src;
        next[`slot:${image.slot}`] = instance;
      }
      for (const layer of getEditableLayers(layout.value.layers)) {
        if (!isImageLayer(layer)) continue;
        const stickerSrc = getLayerStickerSrc(layer);
        if (!stickerSrc) continue;
        const instance = new window.Image();
        instance.src = stickerSrc;
        next[`layer:${layer.id}`] = instance;
      }
      imageRegistry.value = next;
    }
    function createLayerId() {
      return `layer_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
    }
    function addImageLayer() {
      updateLayout((layout2) => {
        const existingImages = layout2.layers.filter((l) => l.type === "image");
        const nextIndex = (existingImages[existingImages.length - 1]?.sourceIndex ?? 0) + 1;
        const layer = normalizeLayerEffects({
          id: createLayerId(),
          type: "image",
          sourceIndex: nextIndex,
          x: CANVAS_WIDTH * 0.55,
          y: CANVAS_HEIGHT * 0.15,
          width: CANVAS_WIDTH * 0.35,
          height: CANVAS_HEIGHT * 0.7,
          rotation: 0,
          radius: 32,
          zIndex: layout2.layers.length + 1,
          fit: "cover",
          shadowBlur: 24,
          shadowOffsetX: 0,
          shadowOffsetY: 16,
          shadowOpacity: 0.22
        });
        layout2.layers.push(layer);
        selectedLayerId.value = layer.id;
      });
    }
    const stickerPathsInUse = computed$2(() => new Set(
      getEditableLayers(layout.value.layers).filter((layer) => isImageLayer(layer) && (layer.assetKind === "sticker" || Boolean(layer.stickerPath || layer.stickerUrl || layer.stickerDataUrl))).map((layer) => String(layer.stickerPath || "").trim()).filter(Boolean)
    ));
    async function loadStickerLibrary() {
      if (!props.api?.get) return;
      stickerLibraryLoading.value = true;
      try {
        const resp = await props.api.get("plugin/YahahaCoverStudio/stickers");
        if (!resp || resp.code !== 0) {
          throw new Error(resp?.msg || "load stickers failed");
        }
        const remoteItems = Array.isArray(resp.data) ? resp.data : [];
        const remotePaths = new Set(remoteItems.map((item) => item.path));
        const localOnlyItems = stickerLibraryItems.value.filter((item) => item.path.startsWith("memory:") && !remotePaths.has(item.path));
        stickerLibraryItems.value = [...localOnlyItems, ...remoteItems];
      } catch (error) {
        console.warn("load sticker library failed", error);
      } finally {
        stickerLibraryLoading.value = false;
      }
    }
    function toggleStickerLibrary() {
      stickerLibraryOpen.value = !stickerLibraryOpen.value;
      if (stickerLibraryOpen.value) {
        void loadStickerLibrary();
      }
    }
    function openStickerFilePicker() {
      stickerFileInputEl.value?.click();
    }
    function isStickerInUse(item) {
      return stickerPathsInUse.value.has(String(item.path || "").trim());
    }
    function removeStickerReferences(path) {
      const normalizedPath = String(path || "").trim();
      if (!normalizedPath) return;
      const filterLayers = (layers) => layers.map((layer) => {
        if (layer.type !== "group") return layer;
        return normalizeLayerEffects({
          ...layer,
          children: filterLayers(layer.children || [])
        });
      }).filter((layer) => {
        if (!isImageLayer(layer)) return true;
        return String(layer.stickerPath || "").trim() !== normalizedPath;
      });
      updateLayout((layout2) => {
        layout2.layers = filterLayers(layout2.layers);
        if (selectedLayer.value && isImageLayer(selectedLayer.value) && String(selectedLayer.value.stickerPath || "").trim() === normalizedPath) {
          selectedLayerId.value = null;
        }
      });
    }
    function upsertStickerLibraryItem(item) {
      const key = item.path || `memory:${item.name}:${Date.now()}`;
      const normalized = { ...item, path: key };
      stickerLibraryItems.value = [
        normalized,
        ...stickerLibraryItems.value.filter((candidate) => candidate.path !== key)
      ];
      return normalized;
    }
    function readStickerFile(file) {
      return new Promise((resolve, reject) => {
        if (!file.type.startsWith("image/")) {
          reject(new Error("not image"));
          return;
        }
        const reader = new FileReader();
        reader.onerror = () => reject(reader.error || new Error("read failed"));
        reader.onload = () => {
          const dataUrl = String(reader.result || "");
          if (!dataUrl) {
            reject(new Error("empty image"));
            return;
          }
          const image = new window.Image();
          image.onload = () => resolve({
            dataUrl,
            name: file.name || "贴图",
            width: Number(image.naturalWidth || image.width || 1),
            height: Number(image.naturalHeight || image.height || 1)
          });
          image.onerror = () => resolve({
            dataUrl,
            name: file.name || "贴图",
            width: 1,
            height: 1
          });
          image.src = dataUrl;
        };
        reader.readAsDataURL(file);
      });
    }
    function addStickerLayer(payload) {
      const sourceWidth = Math.max(1, payload.width || 1);
      const sourceHeight = Math.max(1, payload.height || 1);
      const sourceRatio = sourceWidth / sourceHeight;
      const targetMaxWidth = 360;
      const targetMaxHeight = 220;
      const targetRatio = targetMaxWidth / targetMaxHeight;
      const width = sourceRatio >= targetRatio ? targetMaxWidth : Math.max(96, targetMaxHeight * sourceRatio);
      const height = sourceRatio >= targetRatio ? Math.max(72, targetMaxWidth / sourceRatio) : targetMaxHeight;
      updateLayout((layout2) => {
        const maxZIndex = Math.max(0, ...getEditableLayers(layout2.layers).map((layer2) => Number(layer2.zIndex || 0)));
        const layer = normalizeLayerEffects({
          id: createLayerId(),
          type: "image",
          assetKind: "sticker",
          stickerDataUrl: payload.dataUrl,
          stickerPath: payload.path,
          stickerUrl: payload.url,
          stickerName: payload.name,
          stickerWidth: sourceWidth,
          stickerHeight: sourceHeight,
          sourceIndex: 1,
          source: { kind: "slot", slot: 1 },
          x: Math.round(CANVAS_WIDTH - width - 96),
          y: Math.round(CANVAS_HEIGHT - height - 88),
          width: Math.round(width),
          height: Math.round(height),
          rotation: 0,
          radius: 0,
          zIndex: maxZIndex + 1,
          fit: "contain",
          opacity: 0.92,
          shadowBlur: 14,
          shadowOffsetX: 0,
          shadowOffsetY: 8,
          shadowOpacity: 0.18
        });
        layout2.layers.push(layer);
        selectedLayerId.value = layer.id;
        cropModeEnabled.value = false;
      });
    }
    function addStickerFromLibrary(item) {
      addStickerLayer({
        dataUrl: item.dataUrl || "",
        name: item.name || "贴图",
        width: Number(item.width || 1),
        height: Number(item.height || 1),
        path: item.path,
        url: item.url || getStickerPathUrl(item.path)
      });
    }
    async function deleteStickerItem(item) {
      if (item.path.startsWith("memory:")) {
        stickerLibraryItems.value = stickerLibraryItems.value.filter((candidate) => candidate.path !== item.path);
        return;
      }
      if (!props.api?.post) return;
      try {
        const endpoint = `plugin/YahahaCoverStudio/delete_sticker?file=${encodeURIComponent(item.path)}`;
        const resp = await props.api.post(endpoint);
        if (!resp || resp.code !== 0) {
          throw new Error(resp?.msg || "delete sticker failed");
        }
        stickerLibraryItems.value = stickerLibraryItems.value.filter((candidate) => candidate.path !== item.path);
        removeStickerReferences(item.path);
      } catch (error) {
        console.warn("delete sticker failed", error);
      }
    }
    async function uploadStickerPayload(payload) {
      if (!props.api?.post) return payload;
      try {
        const resp = await props.api.post("plugin/YahahaCoverStudio/upload_sticker", {
          data_url: payload.dataUrl,
          name: payload.name,
          width: payload.width,
          height: payload.height
        });
        if (!resp || resp.code !== 0 || !resp.data?.stickerPath) {
          throw new Error(resp?.msg || "upload sticker failed");
        }
        return {
          dataUrl: resp.data.stickerDataUrl || payload.dataUrl,
          name: resp.data.stickerName || payload.name,
          width: Number(resp.data.stickerWidth || payload.width || 1),
          height: Number(resp.data.stickerHeight || payload.height || 1),
          path: resp.data.stickerPath,
          url: resp.data.stickerUrl || ""
        };
      } catch (error) {
        console.warn("upload sticker failed, fallback to local data url", error);
        return payload;
      }
    }
    async function addStickerFromFile(file) {
      try {
        const payload = await readStickerFile(file);
        const localItem = upsertStickerLibraryItem({
          name: payload.name,
          path: `memory:${Date.now()}:${payload.name}`,
          dataUrl: payload.dataUrl,
          width: payload.width,
          height: payload.height
        });
        const uploaded = await uploadStickerPayload(payload);
        if (uploaded.path) {
          stickerLibraryItems.value = stickerLibraryItems.value.filter((candidate) => candidate.path !== localItem.path);
          upsertStickerLibraryItem({
            name: uploaded.name,
            path: uploaded.path,
            url: uploaded.url,
            dataUrl: uploaded.dataUrl,
            width: uploaded.width,
            height: uploaded.height
          });
        }
        addStickerLayer(uploaded);
        if (stickerLibraryOpen.value) {
          void loadStickerLibrary();
        }
      } catch (error) {
        console.warn("add sticker failed", error);
      }
    }
    function onStickerFileInputChange(event) {
      const input = event.target;
      const file = input.files?.[0];
      input.value = "";
      if (file) {
        void addStickerFromFile(file);
      }
    }
    function isEditableTarget(target) {
      if (!(target instanceof HTMLElement)) return false;
      const tagName = target.tagName.toLowerCase();
      return tagName === "input" || tagName === "textarea" || target.isContentEditable;
    }
    function onEditorPaste(event) {
      if (typeof window === "undefined") return;
      const root = editorRootEl.value;
      if (!root) return;
      const active = document.activeElement;
      if (active instanceof HTMLElement && active !== document.body && !root.contains(active)) return;
      const file = Array.from(event.clipboardData?.items || []).find((item) => item.kind === "file" && item.type.startsWith("image/"))?.getAsFile();
      if (!file) return;
      if (isEditableTarget(event.target)) {
        event.preventDefault();
      }
      void addStickerFromFile(file);
    }
    function addZhTitleLayer() {
      updateLayout((layout2) => {
        const layer = normalizeLayerEffects({
          id: createLayerId(),
          type: "main_title",
          x: CANVAS_WIDTH * 0.05,
          y: CANVAS_HEIGHT * 0.2,
          width: CANVAS_WIDTH * 0.35,
          height: CANVAS_HEIGHT * 0.18,
          rotation: 0,
          radius: 0,
          zIndex: layout2.layers.length + 1,
          fontSize: 180,
          textAlign: "center",
          shadowBlur: 18,
          shadowOffsetX: 0,
          shadowOffsetY: 10,
          shadowOpacity: 0.24
        });
        layout2.layers.push(layer);
        selectedLayerId.value = layer.id;
      });
    }
    function addEnTitleLayer() {
      updateLayout((layout2) => {
        const layer = normalizeLayerEffects({
          id: createLayerId(),
          type: "subtitle",
          x: CANVAS_WIDTH * 0.05,
          y: CANVAS_HEIGHT * 0.45,
          width: CANVAS_WIDTH * 0.35,
          height: CANVAS_HEIGHT * 0.14,
          rotation: 0,
          radius: 0,
          zIndex: layout2.layers.length + 1,
          fontSize: 75,
          textAlign: "center",
          shadowBlur: 14,
          shadowOffsetX: 0,
          shadowOffsetY: 8,
          shadowOpacity: 0.2
        });
        layout2.layers.push(layer);
        selectedLayerId.value = layer.id;
      });
    }
    function addTextLayer() {
      updateLayout((layout2) => {
        const layer = createTextLayer({
          zIndex: layout2.layers.length + 1
        });
        layout2.layers.push(layer);
        selectedLayerId.value = layer.id;
      });
    }
    function removeLayer(id) {
      preserveEditorScrollAfter(() => {
        updateLayout((layout2) => {
          const before = getEditableLayers(layout2.layers);
          const index = before.findIndex((layer) => layer.id === id);
          if (!removeLayerById(layout2.layers, id)) return;
          const after = getEditableLayers(layout2.layers);
          if (!after.length) {
            selectedLayerId.value = null;
            return;
          }
          const nextIndex = Math.max(0, Math.min(index, after.length - 1));
          selectedLayerId.value = selectedLayerId.value === id ? after[nextIndex].id : selectedLayerId.value;
        });
      });
    }
    function removeLayerFromLayerList(id) {
      removeLayer(id);
    }
    function updateSelectedNumeric(key, raw) {
      const id = selectedLayerId.value;
      if (!id) return;
      const num = typeof raw === "number" ? raw : Number(raw);
      if (Number.isNaN(num)) return;
      updateLayout((layout2) => {
        updateLayerById(layout2.layers, id, (layer) => ({
          ...layer,
          [key]: num
        }));
      });
    }
    function updateSelectedString(key, value) {
      const id = selectedLayerId.value;
      if (!id) return;
      updateLayout((layout2) => {
        updateLayerById(layout2.layers, id, (layer) => ({
          ...layer,
          [key]: value
        }));
      });
    }
    function buildRectangleMask() {
      return {
        units: "relative",
        points: [
          [0, 0],
          [1, 0],
          [1, 1],
          [0, 1]
        ]
      };
    }
    function setActivePolygonPoints(points) {
      const context = activePolygonContext.value;
      if (!context) return;
      const mask = {
        units: "relative",
        points: points.map((point) => [
          Math.max(0, Math.min(1, point[0])),
          Math.max(0, Math.min(1, point[1]))
        ])
      };
      if (context.target === "background") {
        updateLayout((layout2) => {
          layout2.background = {
            type: "blurred-image-color",
            imageSource: { kind: "slot", slot: 1 },
            colorSource: "auto",
            color: editorBlendColor.value,
            color2: defaultDeepGradientColor.value,
            colorRatio: effectiveParams.value.colorRatio,
            blur: effectiveParams.value.blur,
            grain: 0.18,
            zIndex: 0,
            ...layout2.background || {},
            maskPolygon: mask
          };
        });
        return;
      }
      if (!context.layerId) return;
      updateLayout((layout2) => {
        updateLayerById(layout2.layers, context.layerId, (layer) => {
          if (!isImageLayer(layer)) return layer;
          return { ...layer, maskPolygon: mask };
        });
      });
    }
    function snapPolygonPoint(rawX, rawY, movingIndex) {
      const snapTargetsX = [0, 0.5, 1];
      const snapTargetsY = [0, 0.5, 1];
      activePolygonRelativePoints.value.forEach((point, index) => {
        if (index === movingIndex) return;
        snapTargetsX.push(point[0]);
        snapTargetsY.push(point[1]);
      });
      const threshold = 0.018;
      let x = Math.max(0, Math.min(1, rawX));
      let y = Math.max(0, Math.min(1, rawY));
      let guideX = null;
      let guideY = null;
      for (const target of snapTargetsX) {
        if (Math.abs(x - target) <= threshold) {
          x = target;
          guideX = target;
          break;
        }
      }
      for (const target of snapTargetsY) {
        if (Math.abs(y - target) <= threshold) {
          y = target;
          guideY = target;
          break;
        }
      }
      const context = activePolygonContext.value;
      polygonSnapGuide.value = context ? {
        x: guideX === null ? null : (context.x + guideX * context.width) * canvasScale.value,
        y: guideY === null ? null : (context.y + guideY * context.height) * canvasScale.value
      } : { x: null, y: null };
      return [x, y];
    }
    function addPolygonPoint() {
      const points = activePolygonRelativePoints.value;
      if (points.length < 2) return;
      let insertAt = 1;
      let longest = -1;
      for (let index = 0; index < points.length; index += 1) {
        const current = points[index];
        const next2 = points[(index + 1) % points.length];
        const distance = (next2[0] - current[0]) ** 2 + (next2[1] - current[1]) ** 2;
        if (distance > longest) {
          longest = distance;
          insertAt = index + 1;
        }
      }
      const prev = points[(insertAt - 1 + points.length) % points.length];
      const next = points[insertAt % points.length];
      const point = [
        (prev[0] + next[0]) / 2,
        (prev[1] + next[1]) / 2
      ];
      const updated = [...points];
      updated.splice(insertAt, 0, point);
      setActivePolygonPoints(updated);
    }
    function removePolygonPoint(index) {
      const points = [...activePolygonRelativePoints.value];
      if (points.length <= 3) return;
      points.splice(index, 1);
      setActivePolygonPoints(points);
    }
    function resetActivePolygon() {
      setActivePolygonPoints(buildRectangleMask().points);
    }
    function toggleBackgroundPolygon(enabled) {
      updateLayout((layout2) => {
        layout2.background = {
          type: "blurred-image-color",
          imageSource: { kind: "slot", slot: 1 },
          colorSource: "auto",
          color: editorBlendColor.value,
          color2: defaultDeepGradientColor.value,
          colorRatio: effectiveParams.value.colorRatio,
          blur: effectiveParams.value.blur,
          grain: 0.18,
          zIndex: 0,
          ...layout2.background || {},
          maskPolygon: enabled ? buildRectangleMask() : void 0
        };
      });
    }
    function toggleSelectedPolygon(enabled) {
      const id = selectedLayerId.value;
      if (!id) return;
      updateLayout((layout2) => {
        updateLayerById(layout2.layers, id, (layer) => {
          if (!isImageLayer(layer)) return layer;
          return {
            ...layer,
            maskPolygon: enabled ? buildRectangleMask() : void 0
          };
        });
      });
    }
    function onSizeSliderChange(key, raw) {
      const layer = selectedLayer.value;
      if (!layer) return;
      const value = Number(raw);
      if (Number.isNaN(value)) return;
      if (!lockAspectRatio.value || layer.width <= 0 || layer.height <= 0) {
        updateSelectedNumeric(key, value);
        return;
      }
      const aspect = layer.width / layer.height || 1;
      if (key === "width") {
        const nextWidth = Math.max(10, Math.min(value, CANVAS_WIDTH * 10));
        const nextHeight = nextWidth / aspect;
        updateLayout((layout2) => {
          updateLayerById(layout2.layers, layer.id, (current) => ({
            ...current,
            width: Math.round(nextWidth),
            height: Math.round(Math.min(nextHeight, CANVAS_HEIGHT * 10))
          }));
        });
      } else {
        const nextHeight = Math.max(10, Math.min(value, CANVAS_HEIGHT * 10));
        const nextWidth = nextHeight * aspect;
        updateLayout((layout2) => {
          updateLayerById(layout2.layers, layer.id, (current) => ({
            ...current,
            height: Math.round(nextHeight),
            width: Math.round(Math.min(nextWidth, CANVAS_WIDTH * 10))
          }));
        });
      }
    }
    function applySelectedAspectRatio(ratio) {
      const layer = selectedLayer.value;
      if (!layer) return;
      const safeRatio = Math.max(0.1, Number(ratio) || 1);
      const centerX = layer.x + layer.width / 2;
      const centerY = layer.y + layer.height / 2;
      let nextWidth = Math.max(10, Math.min(layer.width, CANVAS_WIDTH));
      let nextHeight = nextWidth / safeRatio;
      if (nextHeight > CANVAS_HEIGHT) {
        nextHeight = CANVAS_HEIGHT;
        nextWidth = nextHeight * safeRatio;
      }
      updateLayout((layout2) => {
        updateLayerById(layout2.layers, layer.id, (current) => ({
          ...current,
          x: Math.round(centerX - nextWidth / 2),
          y: Math.round(centerY - nextHeight / 2),
          width: Math.round(Math.min(nextWidth, CANVAS_WIDTH)),
          height: Math.round(Math.min(nextHeight, CANVAS_HEIGHT))
        }));
      });
    }
    function onSliderStart() {
    }
    function onSliderEnd() {
    }
    const dragState = ref$2(null);
    const polygonPointDrag = ref$2(null);
    function getPointerPosition(event) {
      if ("touches" in event) {
        const touch = event.touches[0];
        if (!touch) return null;
        return { clientX: touch.clientX, clientY: touch.clientY };
      }
      return { clientX: event.clientX, clientY: event.clientY };
    }
    function onPolygonPointMove(event) {
      const state = polygonPointDrag.value;
      const context = activePolygonContext.value;
      const canvas = canvasEl.value;
      if (!state || !context || !canvas) return;
      event.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const canvasX = (event.clientX - rect.left) / Math.max(1e-3, canvasScale.value);
      const canvasY = (event.clientY - rect.top) / Math.max(1e-3, canvasScale.value);
      const rawX = (canvasX - context.x) / Math.max(1, context.width);
      const rawY = (canvasY - context.y) / Math.max(1, context.height);
      const snapped = snapPolygonPoint(rawX, rawY, state.index);
      const points = [...activePolygonRelativePoints.value];
      points[state.index] = snapped;
      setActivePolygonPoints(points);
    }
    function stopPolygonPointDrag() {
      polygonPointDrag.value = null;
      polygonSnapGuide.value = { x: null, y: null };
      window.removeEventListener("pointermove", onPolygonPointMove);
      window.removeEventListener("pointerup", stopPolygonPointDrag);
    }
    function startPolygonPointDrag(index, event) {
      polygonPointDrag.value = { index };
      event.currentTarget instanceof HTMLElement && event.currentTarget.setPointerCapture?.(event.pointerId);
      window.addEventListener("pointermove", onPolygonPointMove);
      window.addEventListener("pointerup", stopPolygonPointDrag);
    }
    function toggleFloatingLayerList() {
      if (!floatingLayerListCollapsed.value) {
        closeFloatingLayerList();
        return;
      }
      positionFloatingLayerListNearToolbar();
      floatingLayerListCollapsed.value = false;
      nextTick$2(() => {
        positionFloatingLayerListNearToolbar();
        window.setTimeout(() => {
          window.addEventListener("click", onFloatingLayerListDocumentClick);
        }, 0);
      });
    }
    const onPointerMove = (event) => {
      const state = dragState.value;
      if (!state) return;
      event.preventDefault();
      const canvas = canvasEl.value;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      const point = getPointerPosition(event);
      if (!point) return;
      const dx = point.clientX - state.startX;
      const dy = point.clientY - state.startY;
      if (state.mode === "move" || state.mode === "resize") {
        const scaleX = CANVAS_WIDTH / rect.width;
        const scaleY = CANVAS_HEIGHT / rect.height;
        if (state.mode === "move") {
          const nextX = state.originX + dx * scaleX;
          const nextY = state.originY + dy * scaleY;
          updateLayout((layout2) => {
            updateLayerById(layout2.layers, state.layerId, (layer) => {
              const snapped = snapLayerPosition(nextX, nextY, layer);
              return {
                ...layer,
                x: Math.round(snapped.x),
                y: Math.round(snapped.y)
              };
            });
          });
        } else if (state.mode === "resize") {
          activeSnapGuides.value = { vertical: [], horizontal: [] };
          const originWidth = state.originWidth ?? 0;
          const originHeight = state.originHeight ?? 0;
          if (originWidth <= 0 || originHeight <= 0) return;
          const aspect = originWidth / originHeight || 1;
          let nextWidth;
          let nextHeight;
          if (!lockAspectRatio.value) {
            nextWidth = Math.max(10, originWidth + dx * scaleX);
            nextHeight = Math.max(10, originHeight + dy * scaleY);
          } else {
            const delta = Math.abs(dx * scaleX) > Math.abs(dy * scaleY) ? dx * scaleX : dy * scaleY;
            nextWidth = Math.max(10, originWidth + delta);
            nextHeight = Math.max(10, nextWidth / aspect);
          }
          updateLayout((layout2) => {
            updateLayerById(layout2.layers, state.layerId, (layer) => ({
              ...layer,
              width: Math.round(Math.min(nextWidth, CANVAS_WIDTH)),
              height: Math.round(Math.min(nextHeight, CANVAS_HEIGHT))
            }));
          });
        }
        return;
      }
      if (state.mode === "rotate") {
        activeSnapGuides.value = { vertical: [], horizontal: [] };
        const originRotation = state.originRotation ?? 0;
        const delta = dx * 0.2;
        const nextRotation = originRotation + delta;
        updateLayout((layout2) => {
          updateLayerById(layout2.layers, state.layerId, (layer) => ({
            ...layer,
            rotation: Math.round(nextRotation)
          }));
        });
      }
    };
    const onPointerUp = () => {
      dragState.value = null;
      activeSnapGuides.value = { vertical: [], horizontal: [] };
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("mousemove", onPointerMove);
      window.removeEventListener("mouseup", onPointerUp);
      window.removeEventListener("touchmove", onPointerMove);
      window.removeEventListener("touchend", onPointerUp);
    };
    function startPointerTracking() {
      window.addEventListener("pointermove", onPointerMove);
      window.addEventListener("pointerup", onPointerUp);
      window.addEventListener("mousemove", onPointerMove);
      window.addEventListener("mouseup", onPointerUp);
      window.addEventListener("touchmove", onPointerMove, { passive: false });
      window.addEventListener("touchend", onPointerUp);
    }
    function onLayerMouseDown(id, event) {
      event.preventDefault();
      const layer = findLayerById(layout.value.layers, id);
      if (!layer) return;
      const point = getPointerPosition(event);
      if (!point) return;
      dragState.value = {
        layerId: id,
        startX: point.clientX,
        startY: point.clientY,
        originX: layer.x,
        originY: layer.y,
        mode: "move"
      };
      selectedLayerId.value = id;
      startPointerTracking();
    }
    function onSvgLayerPointerDown(id, event) {
      onLayerMouseDown(id, event);
    }
    onUnmounted$1(() => {
      if (dragState.value) {
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("pointerup", onPointerUp);
        window.removeEventListener("mousemove", onPointerMove);
        window.removeEventListener("mouseup", onPointerUp);
        window.removeEventListener("touchmove", onPointerMove);
        window.removeEventListener("touchend", onPointerUp);
      }
      canvasResizeObserver?.disconnect();
      canvasPaneResizeObserver?.disconnect();
      if (windowResizeAttached) {
        window.removeEventListener("resize", updateCanvasScale);
      }
      if (typeof window !== "undefined") {
        window.removeEventListener("paste", onEditorPaste);
      }
      closeFloatingLayerList();
      stopPolygonPointDrag();
    });
    onMounted$2(() => {
      nextTick$2(() => {
        if (typeof window !== "undefined") {
          refreshImageRegistry();
        }
        updateCanvasScale();
        attachTransformer();
        if (canvasEl.value && typeof ResizeObserver !== "undefined") {
          canvasResizeObserver = new ResizeObserver(() => updateCanvasScale());
          canvasResizeObserver.observe(canvasEl.value);
          if (canvasPaneEl.value) {
            canvasPaneResizeObserver = new ResizeObserver(() => updateCanvasScale());
            canvasPaneResizeObserver.observe(canvasPaneEl.value);
          }
        } else {
          window.addEventListener("resize", updateCanvasScale);
          windowResizeAttached = true;
        }
        window.addEventListener("paste", onEditorPaste);
      });
      void loadFontLibrary();
    });
    watch$2(
      () => props.previewSource,
      () => {
        nextTick$2(() => updateCanvasScale());
      },
      { deep: true }
    );
    watch$2(
      () => firstImage.value?.src,
      async (src) => {
        if (!src) {
          autoBlendColor.value = defaultAutoBlendColor.value;
          return;
        }
        const extracted = await extractComfortableColor(src);
        autoBlendColor.value = extracted || defaultAutoBlendColor.value;
      },
      { immediate: true }
    );
    watch$2(selectedLayerId, () => {
      nextTick$2(() => attachTransformer());
    });
    watch$2(
      () => props.floatingToolsVisible,
      (visible) => {
        if (!visible) closeFloatingLayerList();
      }
    );
    return (_ctx, _cache) => {
      const _component_v_btn = _resolveComponent$1("v-btn");
      const _component_v_icon = _resolveComponent$1("v-icon");
      const _component_v_col = _resolveComponent$1("v-col");
      const _component_v_row = _resolveComponent$1("v-row");
      const _component_v_switch = _resolveComponent$1("v-switch");
      const _component_v_card = _resolveComponent$1("v-card");
      return _openBlock$2(), _createBlock$2(_component_v_card, {
        variant: "outlined",
        class: _normalizeClass$2(["mcr-layout-editor", { "mcr-layout-editor--embedded": __props.embedded }]),
        "data-mcr-theme": props.theme
      }, {
        default: _withCtx$1(() => [
          _createElementVNode$2("div", {
            ref_key: "editorRootEl",
            ref: editorRootEl,
            class: "mcr-layout-workbench"
          }, [
            _createElementVNode$2("div", {
              ref_key: "canvasPaneEl",
              ref: canvasPaneEl,
              class: "mcr-layout-canvas-pane"
            }, [
              _createElementVNode$2("div", {
                ref_key: "layerActionsEl",
                ref: layerActionsEl,
                class: "mcr-layer-actions mcr-layer-actions--canvas"
              }, [
                _createVNode$1(_component_v_btn, {
                  size: "small",
                  class: "mcr-button mcr-button--ghost",
                  "prepend-icon": "mdi-image-plus-outline",
                  onClick: addImageLayer
                }, {
                  default: _withCtx$1(() => [..._cache[49] || (_cache[49] = [
                    _createTextVNode$1(" 添加图片 ", -1)
                  ])]),
                  _: 1
                }),
                _createVNode$1(_component_v_btn, {
                  size: "small",
                  class: "mcr-button mcr-button--ghost",
                  "prepend-icon": "mdi-sticker-plus-outline",
                  onClick: toggleStickerLibrary
                }, {
                  default: _withCtx$1(() => [..._cache[50] || (_cache[50] = [
                    _createTextVNode$1(" 添加贴图 ", -1)
                  ])]),
                  _: 1
                }),
                _createVNode$1(_component_v_btn, {
                  size: "small",
                  class: "mcr-button mcr-button--ghost",
                  "prepend-icon": "mdi-format-title",
                  onClick: addZhTitleLayer
                }, {
                  default: _withCtx$1(() => [..._cache[51] || (_cache[51] = [
                    _createTextVNode$1(" 主标题 ", -1)
                  ])]),
                  _: 1
                }),
                _createVNode$1(_component_v_btn, {
                  size: "small",
                  class: "mcr-button mcr-button--ghost",
                  "prepend-icon": "mdi-subtitles-outline",
                  onClick: addEnTitleLayer
                }, {
                  default: _withCtx$1(() => [..._cache[52] || (_cache[52] = [
                    _createTextVNode$1(" 副标题 ", -1)
                  ])]),
                  _: 1
                }),
                _createVNode$1(_component_v_btn, {
                  size: "small",
                  class: "mcr-button mcr-button--ghost",
                  "prepend-icon": "mdi-text-box-plus-outline",
                  onClick: addTextLayer
                }, {
                  default: _withCtx$1(() => [..._cache[53] || (_cache[53] = [
                    _createTextVNode$1(" 添加文字 ", -1)
                  ])]),
                  _: 1
                }),
                _createElementVNode$2("input", {
                  ref_key: "stickerFileInputEl",
                  ref: stickerFileInputEl,
                  class: "mcr-sticker-file-input",
                  type: "file",
                  accept: "image/*",
                  onChange: onStickerFileInputChange
                }, null, 544)
              ], 512),
              stickerLibraryOpen.value ? (_openBlock$2(), _createElementBlock$2("div", {
                key: 0,
                class: "mcr-sticker-library",
                "data-loading": stickerLibraryLoading.value ? "true" : "false"
              }, [
                _createElementVNode$2("div", _hoisted_2$2, [
                  _cache[55] || (_cache[55] = _createElementVNode$2("div", null, [
                    _createElementVNode$2("div", { class: "mcr-sticker-library__title" }, "贴图库"),
                    _createElementVNode$2("div", { class: "mcr-sticker-library__hint" }, "选择已上传贴图，或上传新的本地图片。")
                  ], -1)),
                  _createElementVNode$2("div", _hoisted_3$2, [
                    _createVNode$1(_component_v_btn, {
                      size: "small",
                      class: "mcr-button mcr-button--ghost",
                      "prepend-icon": "mdi-upload-outline",
                      onClick: openStickerFilePicker
                    }, {
                      default: _withCtx$1(() => [..._cache[54] || (_cache[54] = [
                        _createTextVNode$1(" 上传 ", -1)
                      ])]),
                      _: 1
                    }),
                    _createVNode$1(_component_v_btn, {
                      size: "small",
                      icon: "mdi-close",
                      class: "mcr-button mcr-button--ghost mcr-sticker-library__close",
                      onClick: _cache[0] || (_cache[0] = ($event) => stickerLibraryOpen.value = false)
                    })
                  ])
                ]),
                stickerLibraryLoading.value ? (_openBlock$2(), _createElementBlock$2("div", _hoisted_4$2, " 加载贴图库... ")) : !stickerLibraryItems.value.length ? (_openBlock$2(), _createElementBlock$2("div", _hoisted_5$2, " 暂无贴图 ")) : (_openBlock$2(), _createElementBlock$2("div", _hoisted_6$2, [
                  (_openBlock$2(true), _createElementBlock$2(_Fragment$2, null, _renderList$2(stickerLibraryItems.value, (item) => {
                    return _openBlock$2(), _createElementBlock$2("div", {
                      key: item.path,
                      role: "button",
                      tabindex: "0",
                      class: "mcr-sticker-item",
                      title: item.name,
                      onClick: ($event) => addStickerFromLibrary(item),
                      onKeydown: [
                        _withKeys$1(_withModifiers$1(($event) => addStickerFromLibrary(item), ["prevent"]), ["enter"]),
                        _withKeys$1(_withModifiers$1(($event) => addStickerFromLibrary(item), ["prevent"]), ["space"])
                      ]
                    }, [
                      _createElementVNode$2("span", _hoisted_8$2, [
                        item.dataUrl || item.url ? (_openBlock$2(), _createElementBlock$2("img", {
                          key: 0,
                          src: item.dataUrl || item.url,
                          alt: item.name
                        }, null, 8, _hoisted_9$2)) : (_openBlock$2(), _createBlock$2(_component_v_icon, {
                          key: 1,
                          icon: "mdi-sticker-outline",
                          size: "24"
                        }))
                      ]),
                      _createElementVNode$2("span", _hoisted_10$2, _toDisplayString$2(item.name), 1),
                      _createElementVNode$2("button", {
                        type: "button",
                        class: _normalizeClass$2(["mcr-sticker-item__delete", { "mcr-sticker-item__delete--active": isStickerInUse(item) }]),
                        title: isStickerInUse(item) ? "删除贴图并移除当前方案中的引用" : "删除贴图",
                        onClick: _withModifiers$1(($event) => deleteStickerItem(item), ["stop", "prevent"]),
                        onKeydown: [
                          _withKeys$1(_withModifiers$1(($event) => deleteStickerItem(item), ["stop", "prevent"]), ["enter"]),
                          _withKeys$1(_withModifiers$1(($event) => deleteStickerItem(item), ["stop", "prevent"]), ["space"])
                        ]
                      }, [
                        _createVNode$1(_component_v_icon, {
                          icon: "mdi-trash-can-outline",
                          size: "15"
                        })
                      ], 42, _hoisted_11$2)
                    ], 40, _hoisted_7$2);
                  }), 128))
                ]))
              ], 8, _hoisted_1$2)) : _createCommentVNode$2("", true),
              _createElementVNode$2("div", _hoisted_12$2, [
                _createElementVNode$2("div", {
                  ref_key: "canvasEl",
                  ref: canvasEl,
                  class: "mcr-layout-canvas"
                }, [
                  _createVNode$1(SvgTemplatePreview, {
                    template: layout.value,
                    source: __props.previewSource || null,
                    params: effectiveParams.value,
                    "auto-blend-color": autoBlendColor.value,
                    "selected-layer-id": selectedLayerId.value,
                    interactive: "",
                    onSelectLayer: selectLayer,
                    onLayerPointerDown: onSvgLayerPointerDown,
                    onBackgroundClick: selectBackground
                  }, null, 8, ["template", "source", "params", "auto-blend-color", "selected-layer-id"]),
                  activeSnapGuideStyles.value.vertical.length || activeSnapGuideStyles.value.horizontal.length ? (_openBlock$2(), _createElementBlock$2("div", _hoisted_13$2, [
                    (_openBlock$2(true), _createElementBlock$2(_Fragment$2, null, _renderList$2(activeSnapGuideStyles.value.vertical, (guide) => {
                      return _openBlock$2(), _createElementBlock$2("span", {
                        key: `v-${guide.value}`,
                        class: "mcr-snap-guide mcr-snap-guide--vertical",
                        style: _normalizeStyle$2({ left: guide.position })
                      }, null, 4);
                    }), 128)),
                    (_openBlock$2(true), _createElementBlock$2(_Fragment$2, null, _renderList$2(activeSnapGuideStyles.value.horizontal, (guide) => {
                      return _openBlock$2(), _createElementBlock$2("span", {
                        key: `h-${guide.value}`,
                        class: "mcr-snap-guide mcr-snap-guide--horizontal",
                        style: _normalizeStyle$2({ top: guide.position })
                      }, null, 4);
                    }), 128))
                  ])) : _createCommentVNode$2("", true),
                  polygonOverlayPoints.value.length ? (_openBlock$2(), _createElementBlock$2("div", _hoisted_14$2, [
                    (_openBlock$2(), _createElementBlock$2("svg", _hoisted_15$2, [
                      _createElementVNode$2("polygon", {
                        points: polygonOverlayPointString.value,
                        class: "mcr-polygon-overlay__shape"
                      }, null, 8, _hoisted_16$2),
                      polygonSnapGuide.value.x !== null ? (_openBlock$2(), _createElementBlock$2("line", {
                        key: 0,
                        x1: polygonSnapGuide.value.x,
                        y1: "0",
                        x2: polygonSnapGuide.value.x,
                        y2: "100%",
                        class: "mcr-polygon-overlay__guide"
                      }, null, 8, _hoisted_17$2)) : _createCommentVNode$2("", true),
                      polygonSnapGuide.value.y !== null ? (_openBlock$2(), _createElementBlock$2("line", {
                        key: 1,
                        x1: "0",
                        y1: polygonSnapGuide.value.y,
                        x2: "100%",
                        y2: polygonSnapGuide.value.y,
                        class: "mcr-polygon-overlay__guide"
                      }, null, 8, _hoisted_18$2)) : _createCommentVNode$2("", true)
                    ])),
                    (_openBlock$2(true), _createElementBlock$2(_Fragment$2, null, _renderList$2(polygonOverlayPoints.value, (point) => {
                      return _openBlock$2(), _createElementBlock$2("button", {
                        key: point.index,
                        type: "button",
                        class: "mcr-polygon-anchor",
                        style: _normalizeStyle$2({ left: `${point.x}px`, top: `${point.y}px` }),
                        onPointerdown: _withModifiers$1(($event) => startPolygonPointDrag(point.index, $event), ["stop", "prevent"]),
                        onDblclick: _withModifiers$1(($event) => removePolygonPoint(point.index), ["stop", "prevent"])
                      }, [
                        _createElementVNode$2("span", null, _toDisplayString$2(point.index + 1), 1)
                      ], 44, _hoisted_19$2);
                    }), 128))
                  ])) : _createCommentVNode$2("", true),
                  inlineTextEditor.value.visible ? (_openBlock$2(), _createElementBlock$2("div", {
                    key: 2,
                    class: "mcr-inline-editor",
                    style: _normalizeStyle$2(inlineEditorStyle.value)
                  }, [
                    _createVNode$1(BlueprintField, {
                      modelValue: inlineTextEditor.value.value,
                      "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => inlineTextEditor.value.value = $event),
                      textarea: "",
                      rows: "2",
                      class: "mcr-inline-editor__field",
                      onKeydown: [
                        _withKeys$1(_withModifiers$1(commitInlineTextEdit, ["prevent"]), ["enter"]),
                        _withKeys$1(_withModifiers$1(cancelInlineTextEdit, ["prevent"]), ["esc"])
                      ]
                    }, null, 8, ["modelValue", "onKeydown"]),
                    _createElementVNode$2("div", _hoisted_20$2, [
                      _createVNode$1(_component_v_btn, {
                        size: "small",
                        class: "mcr-button mcr-button--ghost",
                        onClick: cancelInlineTextEdit
                      }, {
                        default: _withCtx$1(() => [..._cache[56] || (_cache[56] = [
                          _createTextVNode$1("取消", -1)
                        ])]),
                        _: 1
                      }),
                      _createVNode$1(_component_v_btn, {
                        size: "small",
                        class: "mcr-button mcr-button--primary",
                        onClick: commitInlineTextEdit
                      }, {
                        default: _withCtx$1(() => [..._cache[57] || (_cache[57] = [
                          _createTextVNode$1("确定", -1)
                        ])]),
                        _: 1
                      })
                    ])
                  ], 4)) : _createCommentVNode$2("", true)
                ], 512),
                _cache[58] || (_cache[58] = _createElementVNode$2("div", { class: "mcr-layout-editor-note mt-2" }, " SVG 画布按比例缩放显示，保存时仍使用真实像素坐标。 ", -1)),
                _renderSlot(_ctx.$slots, "canvas-meta", {}, void 0, true),
                _createElementVNode$2("div", _hoisted_21$2, [
                  _renderSlot(_ctx.$slots, "footer-actions", {}, void 0, true)
                ])
              ])
            ], 512),
            props.floatingToolsVisible && !floatingLayerListCollapsed.value ? (_openBlock$2(), _createBlock$2(_Teleport$1, {
              key: 0,
              to: "body"
            }, [
              _createElementVNode$2("div", {
                ref_key: "floatingLayerListEl",
                ref: floatingLayerListEl,
                class: "mcr-floating-layer-list",
                "data-mcr-theme": props.theme,
                style: _normalizeStyle$2(floatingLayerListStyle.value)
              }, [
                _createElementVNode$2("div", _hoisted_23$2, [
                  _createElementVNode$2("button", {
                    type: "button",
                    class: _normalizeClass$2(["mcr-layer-list__option", { "mcr-layer-list__option--active": editingBackground.value }]),
                    onPointerdown: _cache[2] || (_cache[2] = _withModifiers$1(() => {
                    }, ["prevent"])),
                    onClick: selectBackgroundFromLayerList
                  }, [
                    _createVNode$1(_component_v_icon, {
                      icon: "mdi-image-filter-hdr-outline",
                      size: "17"
                    }),
                    _cache[59] || (_cache[59] = _createElementVNode$2("span", { class: "mcr-layer-list__content" }, [
                      _createElementVNode$2("span", { class: "mcr-layer-list__name" }, "背景")
                    ], -1))
                  ], 34),
                  (_openBlock$2(true), _createElementBlock$2(_Fragment$2, null, _renderList$2(editableLayerList.value, (layer) => {
                    return _openBlock$2(), _createElementBlock$2("button", {
                      key: layer.id,
                      type: "button",
                      class: _normalizeClass$2(["mcr-layer-list__option", { "mcr-layer-list__option--active": layer.id === selectedLayerId.value }]),
                      onPointerdown: _cache[4] || (_cache[4] = _withModifiers$1(() => {
                      }, ["prevent"])),
                      onClick: ($event) => selectLayerFromLayerList(layer.id)
                    }, [
                      _createVNode$1(_component_v_icon, {
                        icon: layerListIcon(layer),
                        size: "17"
                      }, null, 8, ["icon"]),
                      _createElementVNode$2("span", _hoisted_25$2, [
                        _createElementVNode$2("span", _hoisted_26$2, _toDisplayString$2(layerLabel(layer)), 1)
                      ]),
                      _createElementVNode$2("span", {
                        role: "button",
                        tabindex: "-1",
                        class: "mcr-layer-list__delete",
                        title: `删除${layerLabel(layer)}`,
                        onPointerdown: _cache[3] || (_cache[3] = _withModifiers$1(() => {
                        }, ["stop", "prevent"])),
                        onClick: _withModifiers$1(($event) => removeLayerFromLayerList(layer.id), ["stop", "prevent"])
                      }, [
                        _createVNode$1(_component_v_icon, {
                          icon: "mdi-trash-can-outline",
                          size: "15"
                        })
                      ], 40, _hoisted_27$2)
                    ], 42, _hoisted_24$2);
                  }), 128))
                ])
              ], 12, _hoisted_22$2)
            ])) : _createCommentVNode$2("", true),
            _createElementVNode$2("aside", {
              ref_key: "sidePaneEl",
              ref: sidePaneEl,
              class: "mcr-layout-side-pane",
              style: _normalizeStyle$2(layoutSidePaneStyle.value)
            }, [
              props.floatingToolsVisible ? (_openBlock$2(), _createElementBlock$2("div", _hoisted_28$2, [
                _createElementVNode$2("span", {
                  ref_key: "layerListButtonWrapEl",
                  ref: layerListButtonWrapEl,
                  class: "mcr-layer-popover-anchor"
                }, [
                  _createVNode$1(_component_v_btn, {
                    size: "small",
                    class: "mcr-button mcr-button--ghost mcr-layer-button",
                    "prepend-icon": "mdi-layers-outline",
                    title: `当前图层：${currentLayerButtonLabel.value}`,
                    onClick: _withModifiers$1(toggleFloatingLayerList, ["stop"])
                  }, {
                    default: _withCtx$1(() => [
                      _createElementVNode$2("span", _hoisted_29$2, _toDisplayString$2(currentLayerButtonLabel.value), 1),
                      _createVNode$1(_component_v_icon, {
                        icon: "mdi-chevron-down",
                        size: "15",
                        class: "mcr-layer-button__chevron"
                      })
                    ]),
                    _: 1
                  }, 8, ["title"])
                ], 512)
              ])) : _createCommentVNode$2("", true),
              editingBackground.value ? (_openBlock$2(), _createElementBlock$2("div", _hoisted_30$2, [
                _createVNode$1(BlueprintSelect, {
                  "model-value": layout.value.background?.type || "blurred-image-color",
                  items: backgroundTypeItems,
                  label: "背景类型",
                  "onUpdate:modelValue": _cache[5] || (_cache[5] = (val) => updateBackgroundString("type", String(val || "blurred-image-color")))
                }, null, 8, ["model-value"]),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintSelect, {
                          "model-value": layout.value.background?.colorSource || "auto",
                          items: backgroundColorSourceItems,
                          label: "背景色来源",
                          "onUpdate:modelValue": _cache[6] || (_cache[6] = (val) => updateBackgroundString("colorSource", String(val || "auto")))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    }),
                    (layout.value.background?.colorSource || "auto") === "custom" ? (_openBlock$2(), _createBlock$2(_component_v_col, {
                      key: 0,
                      cols: "6"
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintField, {
                          "model-value": layout.value.background?.color || editorBlendColor.value,
                          type: "color",
                          label: "手动颜色",
                          "onUpdate:modelValue": _cache[7] || (_cache[7] = (val) => updateBackgroundString("color", String(val || defaultAutoBlendColor.value)))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })) : _createCommentVNode$2("", true),
                    layout.value.background?.type === "gradient" ? (_openBlock$2(), _createBlock$2(_component_v_col, {
                      key: 1,
                      cols: "6"
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintField, {
                          "model-value": layout.value.background?.color2 || defaultDeepGradientColor.value,
                          type: "color",
                          label: "渐变色",
                          "onUpdate:modelValue": _cache[8] || (_cache[8] = (val) => updateBackgroundString("color2", String(val || defaultDeepGradientColor.value)))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })) : _createCommentVNode$2("", true)
                  ]),
                  _: 1
                }),
                (layout.value.background?.type || "blurred-image-color") !== "transparent" ? (_openBlock$2(), _createBlock$2(BlueprintRange, {
                  key: 0,
                  "model-value": (layout.value.background?.opacity ?? 1) * 100,
                  min: 0,
                  max: 100,
                  step: 5,
                  label: "背景图层不透明度",
                  "onUpdate:modelValue": _cache[9] || (_cache[9] = (val) => updateBackgroundNumeric("opacity", Number(val) / 100))
                }, null, 8, ["model-value"])) : _createCommentVNode$2("", true),
                _createVNode$1(BlueprintRange, {
                  "model-value": layout.value.background?.zIndex ?? 0,
                  min: -20,
                  max: 20,
                  step: 1,
                  label: "背景层级",
                  "onUpdate:modelValue": _cache[10] || (_cache[10] = (val) => updateBackgroundNumeric("zIndex", val))
                }, null, 8, ["model-value"]),
                (layout.value.background?.type || "blurred-image-color") === "blurred-image-color" ? (_openBlock$2(), _createBlock$2(BlueprintRange, {
                  key: 1,
                  "model-value": layout.value.background?.colorRatio ?? effectiveParams.value.colorRatio,
                  min: 0,
                  max: 1,
                  step: 0.05,
                  label: "颜色混合",
                  "onUpdate:modelValue": _cache[11] || (_cache[11] = (val) => updateBackgroundNumeric("colorRatio", val))
                }, null, 8, ["model-value"])) : _createCommentVNode$2("", true),
                (layout.value.background?.type || "blurred-image-color") === "blurred-image-color" ? (_openBlock$2(), _createBlock$2(BlueprintRange, {
                  key: 2,
                  "model-value": layout.value.background?.blur ?? effectiveParams.value.blur,
                  min: 0,
                  max: 100,
                  step: 1,
                  label: "背景模糊",
                  "onUpdate:modelValue": _cache[12] || (_cache[12] = (val) => updateBackgroundNumeric("blur", val))
                }, null, 8, ["model-value"])) : _createCommentVNode$2("", true),
                _createVNode$1(BlueprintRange, {
                  "model-value": layout.value.background?.grain ?? 0,
                  min: 0,
                  max: 1,
                  step: 0.02,
                  label: "胶片颗粒",
                  "onUpdate:modelValue": _cache[13] || (_cache[13] = (val) => updateBackgroundNumeric("grain", val))
                }, null, 8, ["model-value"]),
                _createVNode$1(_component_v_switch, {
                  "model-value": Boolean(layout.value.background?.maskPolygon),
                  inset: "",
                  density: "compact",
                  "hide-details": "",
                  label: "背景多边形裁剪",
                  "onUpdate:modelValue": _cache[14] || (_cache[14] = (val) => toggleBackgroundPolygon(Boolean(val)))
                }, null, 8, ["model-value"]),
                layout.value.background?.maskPolygon ? (_openBlock$2(), _createElementBlock$2("div", _hoisted_31$2, [
                  _createVNode$1(_component_v_btn, {
                    size: "small",
                    class: "mcr-button mcr-button--ghost",
                    onClick: addPolygonPoint
                  }, {
                    default: _withCtx$1(() => [..._cache[60] || (_cache[60] = [
                      _createTextVNode$1("添加锚点", -1)
                    ])]),
                    _: 1
                  }),
                  _createVNode$1(_component_v_btn, {
                    size: "small",
                    class: "mcr-button mcr-button--ghost",
                    onClick: resetActivePolygon
                  }, {
                    default: _withCtx$1(() => [..._cache[61] || (_cache[61] = [
                      _createTextVNode$1("重置矩形", -1)
                    ])]),
                    _: 1
                  })
                ])) : _createCommentVNode$2("", true)
              ])) : _createCommentVNode$2("", true),
              selectedLayer.value ? (_openBlock$2(), _createElementBlock$2("div", _hoisted_32$2, [
                _createVNode$1(_component_v_row, { dense: "" }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": selectedLayer.value.x,
                          min: -CANVAS_WIDTH,
                          max: CANVAS_WIDTH,
                          step: 1,
                          label: "X",
                          "onUpdate:modelValue": _cache[15] || (_cache[15] = (val) => updateSelectedNumeric("x", val))
                        }, null, 8, ["model-value", "min"])
                      ]),
                      _: 1
                    }),
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": selectedLayer.value.y,
                          min: -CANVAS_HEIGHT,
                          max: CANVAS_HEIGHT,
                          step: 1,
                          label: "Y",
                          "onUpdate:modelValue": _cache[16] || (_cache[16] = (val) => updateSelectedNumeric("y", val))
                        }, null, 8, ["model-value", "min"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _unref$1(isImageLayer)(selectedLayer.value) && selectedLayer.value.assetKind !== "sticker" ? (_openBlock$2(), _createBlock$2(_component_v_col, {
                      key: 0,
                      cols: "12"
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintField, {
                          "model-value": selectedLayer.value.sourceIndex,
                          type: "number",
                          label: "素材索引",
                          "onUpdate:modelValue": _cache[17] || (_cache[17] = (val) => updateSelectedNumeric("sourceIndex", val))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })) : _createCommentVNode$2("", true),
                    _unref$1(isImageLayer)(selectedLayer.value) ? (_openBlock$2(), _createBlock$2(_component_v_col, {
                      key: 1,
                      cols: "12"
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintSelect, {
                          "model-value": selectedLayer.value.fit || "cover",
                          items: imageFitItems,
                          label: selectedLayer.value.assetKind === "sticker" ? "贴图适配" : "图片适配",
                          "onUpdate:modelValue": _cache[18] || (_cache[18] = (val) => updateSelectedString("fit", String(val || "cover")))
                        }, null, 8, ["model-value", "label"])
                      ]),
                      _: 1
                    })) : _createCommentVNode$2("", true)
                  ]),
                  _: 1
                }),
                _unref$1(isImageLayer)(selectedLayer.value) ? (_openBlock$2(), _createBlock$2(_component_v_row, {
                  key: 0,
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, {
                      cols: "12",
                      class: "d-flex align-center"
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(_component_v_switch, {
                          modelValue: cropModeEnabled.value,
                          "onUpdate:modelValue": _cache[19] || (_cache[19] = ($event) => cropModeEnabled.value = $event),
                          inset: "",
                          density: "compact",
                          "hide-details": "",
                          label: "画布裁剪模式"
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": (selectedLayer.value.cropFocusX ?? 0.5) * 100,
                          min: 0,
                          max: 100,
                          step: 1,
                          label: "裁剪焦点 X%",
                          "onUpdate:modelValue": _cache[20] || (_cache[20] = (val) => updateSelectedNumeric("cropFocusX", Number(val) / 100))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    }),
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": (selectedLayer.value.cropFocusY ?? 0.5) * 100,
                          min: 0,
                          max: 100,
                          step: 1,
                          label: "裁剪焦点 Y%",
                          "onUpdate:modelValue": _cache[21] || (_cache[21] = (val) => updateSelectedNumeric("cropFocusY", Number(val) / 100))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                })) : _createCommentVNode$2("", true),
                _unref$1(isImageLayer)(selectedLayer.value) ? (_openBlock$2(), _createBlock$2(_component_v_row, {
                  key: 1,
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintSelect, {
                          "model-value": selectedLayer.value.colorSource || "none",
                          items: layerColorSourceItems,
                          label: "图片混色来源",
                          "onUpdate:modelValue": _cache[22] || (_cache[22] = (val) => updateSelectedString("colorSource", String(val || "none")))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    }),
                    (selectedLayer.value.colorSource || "none") === "custom" ? (_openBlock$2(), _createBlock$2(_component_v_col, {
                      key: 0,
                      cols: "6"
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintField, {
                          "model-value": selectedLayer.value.color || editorBlendColor.value,
                          type: "color",
                          label: "混合颜色",
                          "onUpdate:modelValue": _cache[23] || (_cache[23] = (val) => updateSelectedString("color", String(val || defaultAutoBlendColor.value)))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })) : _createCommentVNode$2("", true),
                    (selectedLayer.value.colorSource || "none") !== "none" ? (_openBlock$2(), _createBlock$2(_component_v_col, {
                      key: 1,
                      cols: "12"
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": (selectedLayer.value.colorRatio ?? 0.8) * 100,
                          min: 0,
                          max: 100,
                          step: 5,
                          label: "混色强度",
                          "onUpdate:modelValue": _cache[24] || (_cache[24] = (val) => updateSelectedNumeric("colorRatio", Number(val) / 100))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })) : _createCommentVNode$2("", true),
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(_component_v_switch, {
                          "model-value": Boolean(selectedLayer.value.maskPolygon),
                          inset: "",
                          density: "compact",
                          "hide-details": "",
                          label: "多边形裁剪",
                          "onUpdate:modelValue": _cache[25] || (_cache[25] = (val) => toggleSelectedPolygon(Boolean(val)))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    }),
                    selectedLayer.value.maskPolygon ? (_openBlock$2(), _createBlock$2(_component_v_col, {
                      key: 2,
                      cols: "12",
                      class: "mcr-polygon-actions"
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(_component_v_btn, {
                          size: "small",
                          class: "mcr-button mcr-button--ghost",
                          onClick: addPolygonPoint
                        }, {
                          default: _withCtx$1(() => [..._cache[62] || (_cache[62] = [
                            _createTextVNode$1("添加锚点", -1)
                          ])]),
                          _: 1
                        }),
                        _createVNode$1(_component_v_btn, {
                          size: "small",
                          class: "mcr-button mcr-button--ghost",
                          onClick: resetActivePolygon
                        }, {
                          default: _withCtx$1(() => [..._cache[63] || (_cache[63] = [
                            _createTextVNode$1("重置矩形", -1)
                          ])]),
                          _: 1
                        })
                      ]),
                      _: 1
                    })) : _createCommentVNode$2("", true)
                  ]),
                  _: 1
                })) : _createCommentVNode$2("", true),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _unref$1(isCustomTextLayer)(selectedLayer.value) ? (_openBlock$2(), _createBlock$2(_component_v_col, {
                      key: 0,
                      cols: "12"
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintSelect, {
                          "model-value": selectedLayer.value.contentSource || "fixed",
                          items: textContentSourceItems,
                          label: "文本来源",
                          "onUpdate:modelValue": _cache[26] || (_cache[26] = (val) => updateSelectedString("contentSource", String(val || "fixed")))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })) : _createCommentVNode$2("", true),
                    _unref$1(isCustomTextLayer)(selectedLayer.value) && (selectedLayer.value.contentSource || "fixed") === "library" ? (_openBlock$2(), _createBlock$2(_component_v_col, {
                      key: 1,
                      cols: "12"
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintField, {
                          "model-value": selectedLayer.value.contentKey || "",
                          label: "配置文本键",
                          placeholder: "默认 default，可填 slogan / note 等",
                          "onUpdate:modelValue": _cache[27] || (_cache[27] = (val) => updateSelectedString("contentKey", String(val || "")))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })) : _createCommentVNode$2("", true),
                    _unref$1(isCustomTextLayer)(selectedLayer.value) ? (_openBlock$2(), _createBlock$2(_component_v_col, {
                      key: 2,
                      cols: "12"
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintField, {
                          "model-value": selectedLayer.value.content,
                          textarea: "",
                          rows: "2",
                          label: (selectedLayer.value.contentSource || "fixed") === "library" ? "备用文本内容" : "文本内容",
                          "onUpdate:modelValue": _cache[28] || (_cache[28] = (val) => updateSelectedString("content", String(val || "")))
                        }, null, 8, ["model-value", "label"])
                      ]),
                      _: 1
                    })) : _createCommentVNode$2("", true)
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _unref$1(isTextLayer)(selectedLayer.value) ? (_openBlock$2(), _createBlock$2(_component_v_col, {
                      key: 0,
                      cols: "12"
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintSelect, {
                          "model-value": selectedLayer.value.fontFamily || "main_title",
                          items: fontFamilyItems.value,
                          label: "字体族",
                          "onUpdate:modelValue": _cache[29] || (_cache[29] = (val) => updateSelectedString("fontFamily", String(val || "main_title")))
                        }, null, 8, ["model-value", "items"])
                      ]),
                      _: 1
                    })) : _createCommentVNode$2("", true),
                    _unref$1(isTextLayer)(selectedLayer.value) ? (_openBlock$2(), _createBlock$2(_component_v_col, {
                      key: 1,
                      cols: "12"
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": selectedLayer.value.fontSize,
                          min: 12,
                          max: 320,
                          step: 1,
                          label: "字体大小",
                          "onUpdate:modelValue": _cache[30] || (_cache[30] = (val) => updateSelectedNumeric("fontSize", val))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })) : _createCommentVNode$2("", true)
                  ]),
                  _: 1
                }),
                _unref$1(isTextLayer)(selectedLayer.value) ? (_openBlock$2(), _createBlock$2(_component_v_row, {
                  key: 2,
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createElementVNode$2("div", _hoisted_33$2, [
                          (_openBlock$2(), _createElementBlock$2(_Fragment$2, null, _renderList$2(textAlignItems, (item) => {
                            return _createElementVNode$2("button", {
                              key: item.value,
                              type: "button",
                              class: _normalizeClass$2(["mcr-text-align-button", { "mcr-text-align-button--active": (selectedLayer.value.textAlign || "center") === item.value }]),
                              title: item.title,
                              "aria-label": item.title,
                              "aria-pressed": (selectedLayer.value.textAlign || "center") === item.value,
                              onClick: ($event) => updateSelectedString("textAlign", item.value)
                            }, [
                              _createVNode$1(_component_v_icon, {
                                icon: item.icon,
                                size: "18"
                              }, null, 8, ["icon"])
                            ], 10, _hoisted_34$1);
                          }), 64))
                        ])
                      ]),
                      _: 1
                    }),
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintSelect, {
                          "model-value": selectedLayer.value.maskMode || "normal",
                          items: textMaskModeItems,
                          label: "文字镂空",
                          "onUpdate:modelValue": _cache[31] || (_cache[31] = (val) => updateSelectedString("maskMode", String(val || "normal")))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    }),
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintSelect, {
                          "model-value": selectedLayer.value.colorSource || "custom",
                          items: textColorSourceItems,
                          label: "文字颜色来源",
                          "onUpdate:modelValue": _cache[32] || (_cache[32] = (val) => updateSelectedString("colorSource", String(val || "custom")))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    }),
                    (selectedLayer.value.colorSource || "custom") === "custom" ? (_openBlock$2(), _createBlock$2(_component_v_col, {
                      key: 0,
                      cols: "12"
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintField, {
                          "model-value": selectedLayer.value.color || defaultTextColor.value,
                          type: "color",
                          label: "文字颜色",
                          "onUpdate:modelValue": _cache[33] || (_cache[33] = (val) => updateSelectedString("color", String(val || defaultTextColor.value)))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })) : _createCommentVNode$2("", true)
                  ]),
                  _: 1
                })) : _createCommentVNode$2("", true),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, {
                      cols: "12",
                      class: "d-flex align-center"
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(_component_v_switch, {
                          modelValue: lockAspectRatio.value,
                          "onUpdate:modelValue": _cache[34] || (_cache[34] = ($event) => lockAspectRatio.value = $event),
                          inset: "",
                          density: "compact",
                          "hide-details": "",
                          class: "mr-2",
                          label: "锁定宽高比例"
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    lockAspectRatio.value ? (_openBlock$2(), _createBlock$2(_component_v_col, {
                      key: 0,
                      cols: "12"
                    }, {
                      default: _withCtx$1(() => [
                        _createElementVNode$2("div", _hoisted_35$1, [
                          (_openBlock$2(), _createElementBlock$2(_Fragment$2, null, _renderList$2(aspectRatioPresets, (preset) => {
                            return _createElementVNode$2("button", {
                              key: preset.label,
                              type: "button",
                              class: "mcr-aspect-preset",
                              onPointerdown: _cache[35] || (_cache[35] = _withModifiers$1(() => {
                              }, ["prevent"])),
                              onClick: ($event) => applySelectedAspectRatio(preset.ratio)
                            }, _toDisplayString$2(preset.label), 41, _hoisted_36$1);
                          }), 64))
                        ])
                      ]),
                      _: 1
                    })) : _createCommentVNode$2("", true)
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": selectedLayer.value.width,
                          min: CANVAS_WIDTH * 0.1,
                          max: CANVAS_WIDTH,
                          step: 10,
                          label: "宽度",
                          onStart: onSliderStart,
                          onEnd: onSliderEnd,
                          onChange: _cache[36] || (_cache[36] = (val) => onSizeSliderChange("width", val))
                        }, null, 8, ["model-value", "min"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": selectedLayer.value.height,
                          min: CANVAS_HEIGHT * 0.1,
                          max: CANVAS_HEIGHT,
                          step: 10,
                          label: "高度",
                          onStart: onSliderStart,
                          onEnd: onSliderEnd,
                          onChange: _cache[37] || (_cache[37] = (val) => onSizeSliderChange("height", val))
                        }, null, 8, ["model-value", "min"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": (selectedLayer.value.opacity ?? 1) * 100,
                          min: 10,
                          max: 100,
                          step: 5,
                          label: "不透明度",
                          "onUpdate:modelValue": _cache[38] || (_cache[38] = (val) => updateSelectedNumeric("opacity", Number(val) / 100))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": selectedLayer.value.blur ?? 0,
                          min: 0,
                          max: 40,
                          step: 1,
                          label: "模糊",
                          "onUpdate:modelValue": _cache[39] || (_cache[39] = (val) => updateSelectedNumeric("blur", val))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": selectedLayer.value.shadowBlur ?? 0,
                          min: 0,
                          max: 60,
                          step: 1,
                          label: "阴影模糊",
                          "onUpdate:modelValue": _cache[40] || (_cache[40] = (val) => updateSelectedNumeric("shadowBlur", val))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": selectedLayer.value.shadowOffsetX ?? 0,
                          min: -200,
                          max: 200,
                          step: 1,
                          label: "阴影 X 偏移",
                          "onUpdate:modelValue": _cache[41] || (_cache[41] = (val) => updateSelectedNumeric("shadowOffsetX", val))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    }),
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": selectedLayer.value.shadowOffsetY ?? 0,
                          min: -200,
                          max: 200,
                          step: 1,
                          label: "阴影 Y 偏移",
                          "onUpdate:modelValue": _cache[42] || (_cache[42] = (val) => updateSelectedNumeric("shadowOffsetY", val))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": (selectedLayer.value.shadowOpacity ?? 0.28) * 100,
                          min: 0,
                          max: 100,
                          step: 5,
                          label: "阴影强度",
                          "onUpdate:modelValue": _cache[43] || (_cache[43] = (val) => updateSelectedNumeric("shadowOpacity", Number(val) / 100))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": selectedLayer.value.radius ?? 0,
                          min: 0,
                          max: 240,
                          step: 1,
                          label: "圆角",
                          "onUpdate:modelValue": _cache[44] || (_cache[44] = (val) => updateSelectedNumeric("radius", val))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": selectedLayer.value.zIndex,
                          min: -20,
                          max: Math.max(20, layout.value.layers.length + 2),
                          step: 1,
                          label: "层级 (zIndex)",
                          "onUpdate:modelValue": _cache[45] || (_cache[45] = (val) => updateSelectedNumeric("zIndex", val))
                        }, null, 8, ["model-value", "max"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": selectedLayer.value.rotation ?? 0,
                          min: -180,
                          max: 180,
                          step: 1,
                          label: "旋转角度",
                          "onUpdate:modelValue": _cache[46] || (_cache[46] = (val) => updateSelectedNumeric("rotation", val))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode$1(_component_v_row, {
                  dense: "",
                  class: "mt-1"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": (selectedLayer.value.pivotX ?? 0.5) * 100,
                          min: 0,
                          max: 100,
                          step: 5,
                          label: "旋转中心 X%",
                          "onUpdate:modelValue": _cache[47] || (_cache[47] = (val) => updateSelectedNumeric("pivotX", Number(val) / 100))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    }),
                    _createVNode$1(_component_v_col, { cols: "12" }, {
                      default: _withCtx$1(() => [
                        _createVNode$1(BlueprintRange, {
                          "model-value": (selectedLayer.value.pivotY ?? 0.5) * 100,
                          min: 0,
                          max: 100,
                          step: 5,
                          label: "旋转中心 Y%",
                          "onUpdate:modelValue": _cache[48] || (_cache[48] = (val) => updateSelectedNumeric("pivotY", Number(val) / 100))
                        }, null, 8, ["model-value"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                })
              ])) : _createCommentVNode$2("", true)
            ], 4)
          ], 512)
        ]),
        _: 3
      }, 8, ["class", "data-mcr-theme"]);
    };
  }
});

const CustomLayoutEditor = /* @__PURE__ */ _export_sfc(_sfc_main$2, [["__scopeId", "data-v-04cd3583"]]);

const {defineComponent:_defineComponent$1} = await importShared('vue');

const {createElementVNode:_createElementVNode$1,openBlock:_openBlock$1,createElementBlock:_createElementBlock$1,createCommentVNode:_createCommentVNode$1,createBlock:_createBlock$1,normalizeStyle:_normalizeStyle$1,renderList:_renderList$1,Fragment:_Fragment$1,toDisplayString:_toDisplayString$1,normalizeClass:_normalizeClass$1} = await importShared('vue');

const _hoisted_1$1 = { class: "simulation-shell" };
const _hoisted_2$1 = {
  key: 0,
  class: "simulation-empty"
};
const _hoisted_3$1 = {
  key: 0,
  class: "sim-custom-stage-shell"
};
const _hoisted_4$1 = { class: "sim-custom-stage" };
const _hoisted_5$1 = ["src", "alt"];
const _hoisted_6$1 = {
  key: 1,
  class: "sim-grid sim-grid-style-1"
};
const _hoisted_7$1 = { class: "sim-style-1-copy" };
const _hoisted_8$1 = { class: "sim-style-1-stage" };
const _hoisted_9$1 = { class: "sim-style-1-card sim-style-1-card-front" };
const _hoisted_10$1 = ["src", "alt"];
const _hoisted_11$1 = {
  key: 0,
  class: "sim-custom-stage-shell"
};
const _hoisted_12$1 = { class: "sim-custom-stage" };
const _hoisted_13$1 = ["src", "alt"];
const _hoisted_14$1 = { class: "sim-style-2-foreground" };
const _hoisted_15$1 = ["src", "alt"];
const _hoisted_16$1 = {
  key: 2,
  class: "sim-grid sim-grid-style-2"
};
const _hoisted_17$1 = { class: "sim-style-2-copy" };
const _hoisted_18$1 = {
  key: 0,
  class: "sim-custom-stage-shell"
};
const _hoisted_19$1 = { class: "sim-custom-stage" };
const _hoisted_20$1 = ["src", "alt"];
const _hoisted_21$1 = { class: "sim-style-3-header" };
const _hoisted_22$1 = { class: "sim-style-3-subtitle-row" };
const _hoisted_23$1 = { class: "sim-style-3-stage" };
const _hoisted_24$1 = ["src", "alt"];
const _hoisted_25$1 = {
  key: 0,
  class: "sim-custom-stage-shell"
};
const _hoisted_26$1 = { class: "sim-custom-stage" };
const _hoisted_27$1 = ["src", "alt"];
const _hoisted_28$1 = {
  key: 1,
  class: "sim-style-4-copy"
};
const _hoisted_29$1 = {
  key: 0,
  class: "sim-custom-stage-shell"
};
const _hoisted_30$1 = { class: "sim-custom-stage" };
const _hoisted_31$1 = ["src", "alt"];
const _hoisted_32$1 = {
  key: 1,
  class: "sim-custom-empty"
};
const _hoisted_33$1 = {
  key: 0,
  class: "sim-live-badge",
  "aria-label": "动态预览",
  title: "动态预览"
};
const {computed: computed$1,nextTick: nextTick$1,onMounted: onMounted$1,onUnmounted,ref: ref$1,watch: watch$1} = await importShared('vue');
const _sfc_main$1 = /* @__PURE__ */ _defineComponent$1({
  __name: "GeneratePreviewSimulation",
  props: {
    source: {},
    params: {}
  },
  setup(__props) {
    const props = __props;
    const styleBase = computed$1(() => props.source?.cover_style_base || "static_1");
    const variant = computed$1(() => props.source?.cover_style_variant || "static");
    const titles = computed$1(() => props.source?.titles || { zh: "", en: "" });
    const firstImage = computed$1(() => props.source?.images?.[0] || null);
    const autoBlendColor = ref$1(getThemeColor("--mcr-cover-auto-blend"));
    const previewStageEl = ref$1(null);
    const previewStageScale = ref$1(1);
    const loadedFontUrls = /* @__PURE__ */ new Map();
    const textMeasureCanvas = typeof document !== "undefined" ? document.createElement("canvas") : null;
    let previewStageResizeObserver = null;
    const sortedLayers = computed$1(() => {
      const layout = props.source?.custom_static_layout;
      return [...layout?.layers || []].sort((a, b) => (a.zIndex || 0) - (b.zIndex || 0));
    });
    const hasCustomLayout = computed$1(() => sortedLayers.value.length > 0);
    const shouldUseLayoutDrivenPresetStage = computed$1(
      () => hasCustomLayout.value && styleBase.value !== "custom_static"
    );
    const usesEditorLayoutPreview = computed$1(
      () => hasCustomLayout.value && (styleBase.value === "custom_static" || shouldUseLayoutDrivenPresetStage.value)
    );
    const style3Images = computed$1(() => {
      const sourceImages = props.source?.images || [];
      if (!sourceImages.length) return [];
      const style3Order = [3, 1, 5, 4, 2, 6, 9, 8, 7];
      return style3Order.map((slotNumber, index) => {
        const image = sourceImages[(slotNumber - 1) % sourceImages.length];
        return {
          ...image,
          key: `${image.slot}-${slotNumber}-${index}`,
          slot: slotNumber
        };
      });
    });
    const style3Columns = computed$1(() => [
      style3Images.value.slice(0, 3),
      style3Images.value.slice(3, 6),
      style3Images.value.slice(6, 9)
    ]);
    const documentSize = computed$1(() => getDocumentSize(props.source?.custom_static_layout));
    const backgroundStyle = computed$1(() => buildBackgroundStyle(firstImage.value?.src, props.params.blur));
    const fullBackgroundStyle = computed$1(() => buildBackgroundStyle(firstImage.value?.src, props.params.blur, true));
    const effectiveBlendColor = computed$1(() => {
      return resolveBlendColor(props.source, props.params, autoBlendColor.value);
    });
    const overlayStyle = computed$1(() => buildOverlayStyle(effectiveBlendColor.value, props.params.colorRatio));
    const canvasStyle = computed$1(() => ({
      backgroundColor: effectiveBlendColor.value
    }));
    const mainTitleStyle = computed$1(() => ({
      fontFamily: getPreviewFontFamily("main_title", titles.value.zh)
    }));
    const subtitleStyle = computed$1(() => ({
      fontFamily: getPreviewFontFamily("subtitle", titles.value.en)
    }));
    const previewStageFixedStyle = computed$1(() => ({
      transform: `scale(${previewStageScale.value})`,
      width: `${documentSize.value.width}px`,
      height: `${documentSize.value.height}px`,
      "--sim-main-image": firstImage.value?.src ? `url(${firstImage.value.src})` : "none"
    }));
    const style3BackgroundStyle = computed$1(() => {
      const base = effectiveBlendColor.value;
      return {
        background: `linear-gradient(90deg, ${hexToRgba(darkenHexColor(base, 0.08), 1)} 0%, ${hexToRgba(lightenHexColor(base, 0.24), 0.92)} 100%)`
      };
    });
    const style3AccentStyle = computed$1(() => ({
      background: lightenHexColor(effectiveBlendColor.value, 0.08)
    }));
    const style3SubtitleLines = computed$1(() => {
      const text = (titles.value.en || "UNTITLED").trim();
      if (!text) return ["UNTITLED"];
      const words = text.split(/\s+/).filter(Boolean);
      if (words.length <= 1) return [text];
      if (text.length <= 16 && words.length <= 3) return [text];
      let bestSplitIndex = 1;
      let bestScore = Number.POSITIVE_INFINITY;
      for (let index = 1; index < words.length; index += 1) {
        const first = words.slice(0, index).join(" ");
        const second = words.slice(index).join(" ");
        const balancePenalty = Math.abs(first.length - second.length);
        const midpointPenalty = Math.abs(index - words.length / 2) * 0.6;
        const score = balancePenalty + midpointPenalty;
        if (score < bestScore) {
          bestScore = score;
          bestSplitIndex = index;
        }
      }
      return [
        words.slice(0, bestSplitIndex).join(" "),
        words.slice(bestSplitIndex).join(" ")
      ];
    });
    function getCustomLayerText(layer) {
      if (isCustomTextLayer(layer)) {
        const fallback = layer.content || "未定义文本";
        if ((layer.contentSource || "fixed") !== "library") return fallback;
        const customTexts = props.source?.custom_texts || {};
        const key = String(layer.contentKey || "").trim();
        if (key && customTexts[key]) return customTexts[key];
        for (const defaultKey of ["default", "text", "custom_text", "content"]) {
          if (customTexts[defaultKey]) return customTexts[defaultKey];
        }
        return fallback;
      }
      if (layer.type === "main_title" || layer.type === "title_zh") {
        return titles.value.zh || "未定义主标题";
      }
      return titles.value.en || "未定义副标题";
    }
    function getLayerImage(sourceIndex) {
      return props.source?.images.find((image) => image.slot === sourceIndex);
    }
    function getStickerPathUrl(path) {
      const normalized = String(path || "").trim();
      return normalized ? `/api/v1/plugin/YahahaCoverStudio/saved_cover_image?file=${encodeURIComponent(normalized)}` : "";
    }
    function normalizePluginImageUrl(url) {
      const normalized = String(url || "").trim();
      if (!normalized) return "";
      if (normalized.startsWith("plugin/")) return `/api/v1/${normalized}`;
      if (normalized.startsWith("/plugin/")) return `/api/v1${normalized}`;
      return normalized;
    }
    function getLayerPreviewImage(layer) {
      const stickerSrc = layer.stickerDataUrl || normalizePluginImageUrl(layer.stickerUrl) || getStickerPathUrl(layer.stickerPath);
      if (layer.assetKind === "sticker" || stickerSrc) {
        return stickerSrc ? {
          src: stickerSrc,
          label: layer.stickerName || "sticker"
        } : void 0;
      }
      return getLayerImage(layer.sourceIndex);
    }
    watch$1(
      () => firstImage.value?.src,
      async (src) => {
        if (!src) {
          autoBlendColor.value = getThemeColor("--mcr-cover-auto-blend");
          return;
        }
        const extracted = await extractComfortableColor(src);
        autoBlendColor.value = extracted || getThemeColor("--mcr-cover-auto-blend");
      },
      { immediate: true }
    );
    function updatePreviewStageScale() {
      const stage = previewStageEl.value;
      if (!stage) return;
      if (usesEditorLayoutPreview.value) {
        previewStageScale.value = 1;
        return;
      }
      const width = stage.clientWidth || 1;
      const documentWidth = documentSize.value.width;
      previewStageScale.value = width / documentWidth;
    }
    function getLayerStyle(layer) {
      const normalized = normalizeLayerEffects(layer);
      const isImage = normalized.type === "image";
      return {
        ...getLayerFrameStyle(normalized),
        boxShadow: isImage ? getLayerShadowStyle(normalized) : "none",
        overflow: isImage ? "hidden" : "visible"
      };
    }
    function getImageStyle(layer) {
      const normalized = normalizeLayerEffects(layer);
      const imageLayer = normalized;
      const objectPositionX = Math.max(0, Math.min(100, (imageLayer.cropFocusX ?? 0.5) * 100));
      const objectPositionY = Math.max(0, Math.min(100, (imageLayer.cropFocusY ?? 0.5) * 100));
      return {
        borderRadius: `${Math.max(0, normalized.radius || 0)}px`,
        opacity: String(normalized.opacity ?? 1),
        objectPosition: `${objectPositionX}% ${objectPositionY}%`,
        filter: normalized.blur ? `blur(${Math.max(0, normalized.blur)}px)` : "none",
        ...getLayerTransformStyle(normalized)
      };
    }
    function getTitleStyle(layer) {
      const normalized = normalizeLayerEffects(layer);
      const measured = getMeasuredTextLayout(layer);
      const fontFamily = getPreviewFontFamily(normalized.fontFamily, getCustomLayerText(layer));
      return {
        fontFamily,
        fontSize: `${Math.max(12, measured?.font_size || layer.fontSize || 60)}px`,
        lineHeight: String(measured?.line_height ? measured.line_height / Math.max(1, measured.font_size) : 1.1),
        opacity: String(measured?.opacity ?? normalized.opacity ?? 1),
        filter: measured?.blur ?? normalized.blur ? `blur(${Math.max(0, measured?.blur ?? normalized.blur ?? 0)}px)` : "none",
        textShadow: (measured?.shadow.blur ?? normalized.shadowBlur) || (measured?.shadow.offset_x ?? normalized.shadowOffsetX) || (measured?.shadow.offset_y ?? normalized.shadowOffsetY) ? `${Math.round(measured?.shadow.offset_x ?? normalized.shadowOffsetX ?? 0)}px ${Math.round(measured?.shadow.offset_y ?? normalized.shadowOffsetY ?? 0)}px ${Math.max(0, Math.round(measured?.shadow.blur ?? normalized.shadowBlur ?? 0))}px rgba(var(--mcr-rgb-shadow), ${Math.max(0, Math.min(0.9, measured?.shadow.opacity ?? normalized.shadowOpacity ?? 0.28))})` : "none",
        ...getLayerTransformStyle(normalized)
      };
    }
    function getMeasuredTextLayout(layer) {
      const layout = props.source?.custom_static_layout;
      const textLayout = layout?.computed?.textLayout;
      return textLayout?.[layer.id] || null;
    }
    function measureTextWidth(text, layer) {
      const context = textMeasureCanvas?.getContext("2d");
      if (!context) {
        return text.length * Math.max(12, layer.fontSize || 60) * 0.55;
      }
      context.font = `700 ${Math.max(12, layer.fontSize || 60)}px ${getPreviewFontFamily(normalizeLayerEffects(layer).fontFamily, text)}`;
      return context.measureText(text).width;
    }
    function getWrappedLayerLines(layer) {
      const text = getCustomLayerText(layer);
      if (!text) return [""];
      const maxWidth = Math.max(1, layer.width);
      const lines = [];
      let current = "";
      for (const char of Array.from(text)) {
        const candidate = `${current}${char}`;
        if (!current || measureTextWidth(candidate, layer) <= maxWidth) {
          current = candidate;
          continue;
        }
        lines.push(current);
        current = char;
      }
      if (current) {
        lines.push(current);
      }
      return lines.length ? lines : [text];
    }
    function getMeasuredLayerLines(layer) {
      const measured = getMeasuredTextLayout(layer);
      if (measured?.lines?.length) {
        return measured.lines;
      }
      const fontSize = Math.max(12, layer.fontSize || 60);
      const lineHeight = fontSize * 1.1;
      const wrappedLines = getWrappedLayerLines(layer);
      const totalHeight = wrappedLines.length * lineHeight;
      const startY = layer.y + (layer.height - totalHeight) / 2;
      return wrappedLines.map((line, index) => {
        const lineWidth = measureTextWidth(line, layer);
        return {
          text: line,
          x: layer.x + (layer.width - lineWidth) / 2,
          y: startY + index * lineHeight,
          width: lineWidth,
          height: fontSize
        };
      });
    }
    function getMeasuredLineStyle(layer, index) {
      const measured = getMeasuredTextLayout(layer);
      const lines = getMeasuredLayerLines(layer);
      const line = lines[index];
      const frame = measured?.frame || {
        x: layer.x,
        y: layer.y
      };
      if (!line) {
        return {};
      }
      return {
        position: "absolute",
        left: "0",
        top: "0",
        transform: `translate(${Math.round(line.x - frame.x)}px, ${Math.round(line.y - frame.y)}px)`
      };
    }
    function ensureFontFace(name, url) {
      if (!url || typeof FontFace === "undefined" || typeof document === "undefined") {
        return Promise.resolve();
      }
      const cacheKey = `${name}:${url}`;
      const cached = loadedFontUrls.get(cacheKey);
      if (cached) return cached;
      const pending = new FontFace(name, `url(${url})`).load().then((font) => {
        document.fonts.add(font);
      }).catch((error) => {
        console.error(`load font face failed: ${name}`, error);
      }).then(() => void 0);
      loadedFontUrls.set(cacheKey, pending);
      return pending;
    }
    watch$1(
      () => props.source?.font_faces,
      async (fontFaces) => {
        await Promise.all(
          Object.entries(fontFaces || {}).map(([key, url]) => ensureFontFace(getTemplateFontFaceName(key), url))
        );
      },
      { deep: true, immediate: true }
    );
    watch$1(
      () => [styleBase.value, hasCustomLayout.value, props.source?.images?.length],
      () => {
        nextTick$1(() => updatePreviewStageScale());
      }
    );
    onMounted$1(() => {
      nextTick$1(() => {
        updatePreviewStageScale();
        if (previewStageEl.value && typeof ResizeObserver !== "undefined") {
          previewStageResizeObserver = new ResizeObserver(() => updatePreviewStageScale());
          previewStageResizeObserver.observe(previewStageEl.value);
        } else {
          window.addEventListener("resize", updatePreviewStageScale);
        }
      });
    });
    onUnmounted(() => {
      previewStageResizeObserver?.disconnect();
      window.removeEventListener("resize", updatePreviewStageScale);
    });
    return (_ctx, _cache) => {
      return _openBlock$1(), _createElementBlock$1("div", _hoisted_1$1, [
        !__props.source || !__props.source.images.length ? (_openBlock$1(), _createElementBlock$1("div", _hoisted_2$1, [..._cache[0] || (_cache[0] = [
          _createElementVNode$1("div", { class: "text-subtitle-2 mb-2" }, "暂无可用预览素材", -1),
          _createElementVNode$1("div", { class: "text-caption text-medium-emphasis" }, "请先配置媒体库或自定义图片目录。", -1)
        ])])) : (_openBlock$1(), _createElementBlock$1("div", {
          key: 1,
          class: "simulation-canvas",
          style: _normalizeStyle$1(canvasStyle.value)
        }, [
          _createElementVNode$1("div", {
            ref_key: "previewStageEl",
            ref: previewStageEl,
            class: _normalizeClass$1(["sim-stage-shell", { "sim-stage-shell--layout": usesEditorLayoutPreview.value }])
          }, [
            usesEditorLayoutPreview.value ? (_openBlock$1(), _createBlock$1(SvgTemplatePreview, {
              key: 0,
              class: "sim-layout-preview",
              template: __props.source?.custom_static_layout,
              source: __props.source,
              params: __props.params,
              "auto-blend-color": autoBlendColor.value
            }, null, 8, ["template", "source", "params", "auto-blend-color"])) : (_openBlock$1(), _createElementBlock$1("div", {
              key: 1,
              class: "sim-stage",
              style: _normalizeStyle$1(previewStageFixedStyle.value)
            }, [
              styleBase.value === "static_1" ? (_openBlock$1(), _createElementBlock$1(_Fragment$1, { key: 0 }, [
                _createElementVNode$1("div", {
                  class: "sim-bg",
                  style: _normalizeStyle$1(backgroundStyle.value)
                }, null, 4),
                _createElementVNode$1("div", {
                  class: "sim-overlay",
                  style: _normalizeStyle$1(overlayStyle.value)
                }, null, 4),
                shouldUseLayoutDrivenPresetStage.value ? (_openBlock$1(), _createElementBlock$1("div", _hoisted_3$1, [
                  _createElementVNode$1("div", _hoisted_4$1, [
                    (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(sortedLayers.value, (layer) => {
                      return _openBlock$1(), _createElementBlock$1("div", {
                        key: layer.id,
                        class: "sim-custom-layer",
                        style: _normalizeStyle$1(getLayerStyle(layer))
                      }, [
                        layer.type === "image" ? (_openBlock$1(), _createElementBlock$1(_Fragment$1, { key: 0 }, [
                          getLayerPreviewImage(layer)?.src ? (_openBlock$1(), _createElementBlock$1("img", {
                            key: 0,
                            class: "sim-custom-image",
                            src: getLayerPreviewImage(layer)?.src,
                            alt: getLayerPreviewImage(layer)?.label || `image-${layer.sourceIndex}`,
                            style: _normalizeStyle$1(getImageStyle(layer))
                          }, null, 12, _hoisted_5$1)) : _createCommentVNode$1("", true)
                        ], 64)) : layer.type === "main_title" || layer.type === "title_zh" ? (_openBlock$1(), _createElementBlock$1("div", {
                          key: 1,
                          class: "sim-custom-text sim-custom-text-zh",
                          style: _normalizeStyle$1(getTitleStyle(layer))
                        }, [
                          (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(getMeasuredLayerLines(layer), (line, index) => {
                            return _openBlock$1(), _createElementBlock$1("span", {
                              key: `${layer.id}-zh-${index}`,
                              class: "sim-custom-text-line",
                              style: _normalizeStyle$1(getMeasuredLineStyle(layer, index))
                            }, _toDisplayString$1(line.text), 5);
                          }), 128))
                        ], 4)) : (_openBlock$1(), _createElementBlock$1("div", {
                          key: 2,
                          class: "sim-custom-text sim-custom-text-en",
                          style: _normalizeStyle$1(getTitleStyle(layer))
                        }, [
                          (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(getMeasuredLayerLines(layer), (line, index) => {
                            return _openBlock$1(), _createElementBlock$1("span", {
                              key: `${layer.id}-text-${index}`,
                              class: "sim-custom-text-line",
                              style: _normalizeStyle$1(getMeasuredLineStyle(layer, index))
                            }, _toDisplayString$1(line.text), 5);
                          }), 128))
                        ], 4))
                      ], 4);
                    }), 128))
                  ])
                ])) : (_openBlock$1(), _createElementBlock$1("div", _hoisted_6$1, [
                  _createElementVNode$1("div", _hoisted_7$1, [
                    _createElementVNode$1("div", {
                      class: "sim-title-zh",
                      style: _normalizeStyle$1(mainTitleStyle.value)
                    }, _toDisplayString$1(titles.value.zh || "未配置中文标题"), 5),
                    _createElementVNode$1("div", {
                      class: "sim-title-en",
                      style: _normalizeStyle$1(subtitleStyle.value)
                    }, _toDisplayString$1(titles.value.en || "UNTITLED"), 5)
                  ]),
                  _createElementVNode$1("div", _hoisted_8$1, [
                    _cache[1] || (_cache[1] = _createElementVNode$1("div", { class: "sim-style-1-card sim-style-1-card-back" }, null, -1)),
                    _cache[2] || (_cache[2] = _createElementVNode$1("div", { class: "sim-style-1-card sim-style-1-card-mid" }, null, -1)),
                    _createElementVNode$1("div", _hoisted_9$1, [
                      _createElementVNode$1("img", {
                        class: "sim-main-image",
                        src: firstImage.value?.src,
                        alt: firstImage.value?.label || "preview image"
                      }, null, 8, _hoisted_10$1)
                    ])
                  ])
                ]))
              ], 64)) : styleBase.value === "static_2" ? (_openBlock$1(), _createElementBlock$1(_Fragment$1, { key: 1 }, [
                _createElementVNode$1("div", {
                  class: "sim-bg",
                  style: _normalizeStyle$1(backgroundStyle.value)
                }, null, 4),
                _createElementVNode$1("div", {
                  class: "sim-overlay",
                  style: _normalizeStyle$1(overlayStyle.value)
                }, null, 4),
                shouldUseLayoutDrivenPresetStage.value ? (_openBlock$1(), _createElementBlock$1("div", _hoisted_11$1, [
                  _createElementVNode$1("div", _hoisted_12$1, [
                    (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(sortedLayers.value, (layer) => {
                      return _openBlock$1(), _createElementBlock$1("div", {
                        key: layer.id,
                        class: "sim-custom-layer",
                        style: _normalizeStyle$1(getLayerStyle(layer))
                      }, [
                        layer.type === "image" ? (_openBlock$1(), _createElementBlock$1(_Fragment$1, { key: 0 }, [
                          getLayerPreviewImage(layer)?.src ? (_openBlock$1(), _createElementBlock$1("img", {
                            key: 0,
                            class: "sim-custom-image",
                            src: getLayerPreviewImage(layer)?.src,
                            alt: getLayerPreviewImage(layer)?.label || `image-${layer.sourceIndex}`,
                            style: _normalizeStyle$1(getImageStyle(layer))
                          }, null, 12, _hoisted_13$1)) : _createCommentVNode$1("", true)
                        ], 64)) : layer.type === "main_title" || layer.type === "title_zh" ? (_openBlock$1(), _createElementBlock$1("div", {
                          key: 1,
                          class: "sim-custom-text sim-custom-text-zh",
                          style: _normalizeStyle$1(getTitleStyle(layer))
                        }, [
                          (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(getMeasuredLayerLines(layer), (line, index) => {
                            return _openBlock$1(), _createElementBlock$1("span", {
                              key: `${layer.id}-zh-${index}`,
                              class: "sim-custom-text-line",
                              style: _normalizeStyle$1(getMeasuredLineStyle(layer, index))
                            }, _toDisplayString$1(line.text), 5);
                          }), 128))
                        ], 4)) : (_openBlock$1(), _createElementBlock$1("div", {
                          key: 2,
                          class: "sim-custom-text sim-custom-text-en",
                          style: _normalizeStyle$1(getTitleStyle(layer))
                        }, [
                          (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(getMeasuredLayerLines(layer), (line, index) => {
                            return _openBlock$1(), _createElementBlock$1("span", {
                              key: `${layer.id}-text-${index}`,
                              class: "sim-custom-text-line",
                              style: _normalizeStyle$1(getMeasuredLineStyle(layer, index))
                            }, _toDisplayString$1(line.text), 5);
                          }), 128))
                        ], 4))
                      ], 4);
                    }), 128))
                  ])
                ])) : (_openBlock$1(), _createElementBlock$1(_Fragment$1, { key: 1 }, [
                  _cache[3] || (_cache[3] = _createElementVNode$1("div", { class: "sim-style-2-shadow" }, null, -1)),
                  _createElementVNode$1("div", _hoisted_14$1, [
                    _createElementVNode$1("img", {
                      class: "sim-style-2-image",
                      src: firstImage.value?.src,
                      alt: firstImage.value?.label || "preview image"
                    }, null, 8, _hoisted_15$1)
                  ])
                ], 64)),
                !shouldUseLayoutDrivenPresetStage.value ? (_openBlock$1(), _createElementBlock$1("div", _hoisted_16$1, [
                  _createElementVNode$1("div", _hoisted_17$1, [
                    _createElementVNode$1("div", {
                      class: "sim-title-zh",
                      style: _normalizeStyle$1(mainTitleStyle.value)
                    }, _toDisplayString$1(titles.value.zh || "未配置中文标题"), 5),
                    _createElementVNode$1("div", {
                      class: "sim-title-en",
                      style: _normalizeStyle$1(subtitleStyle.value)
                    }, _toDisplayString$1(titles.value.en || "UNTITLED"), 5)
                  ])
                ])) : _createCommentVNode$1("", true)
              ], 64)) : styleBase.value === "static_3" ? (_openBlock$1(), _createElementBlock$1(_Fragment$1, { key: 2 }, [
                _createElementVNode$1("div", {
                  class: "sim-style-3-bg",
                  style: _normalizeStyle$1(style3BackgroundStyle.value)
                }, null, 4),
                shouldUseLayoutDrivenPresetStage.value ? (_openBlock$1(), _createElementBlock$1("div", _hoisted_18$1, [
                  _createElementVNode$1("div", _hoisted_19$1, [
                    (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(sortedLayers.value, (layer) => {
                      return _openBlock$1(), _createElementBlock$1("div", {
                        key: layer.id,
                        class: "sim-custom-layer",
                        style: _normalizeStyle$1(getLayerStyle(layer))
                      }, [
                        layer.type === "image" ? (_openBlock$1(), _createElementBlock$1(_Fragment$1, { key: 0 }, [
                          getLayerPreviewImage(layer)?.src ? (_openBlock$1(), _createElementBlock$1("img", {
                            key: 0,
                            class: "sim-custom-image",
                            src: getLayerPreviewImage(layer)?.src,
                            alt: getLayerPreviewImage(layer)?.label || `image-${layer.sourceIndex}`,
                            style: _normalizeStyle$1(getImageStyle(layer))
                          }, null, 12, _hoisted_20$1)) : _createCommentVNode$1("", true)
                        ], 64)) : layer.type === "main_title" || layer.type === "title_zh" ? (_openBlock$1(), _createElementBlock$1("div", {
                          key: 1,
                          class: "sim-custom-text sim-custom-text-zh",
                          style: _normalizeStyle$1(getTitleStyle(layer))
                        }, [
                          (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(getMeasuredLayerLines(layer), (line, index) => {
                            return _openBlock$1(), _createElementBlock$1("span", {
                              key: `${layer.id}-zh-${index}`,
                              class: "sim-custom-text-line",
                              style: _normalizeStyle$1(getMeasuredLineStyle(layer, index))
                            }, _toDisplayString$1(line.text), 5);
                          }), 128))
                        ], 4)) : (_openBlock$1(), _createElementBlock$1("div", {
                          key: 2,
                          class: "sim-custom-text sim-custom-text-en",
                          style: _normalizeStyle$1(getTitleStyle(layer))
                        }, [
                          (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(getMeasuredLayerLines(layer), (line, index) => {
                            return _openBlock$1(), _createElementBlock$1("span", {
                              key: `${layer.id}-text-${index}`,
                              class: "sim-custom-text-line",
                              style: _normalizeStyle$1(getMeasuredLineStyle(layer, index))
                            }, _toDisplayString$1(line.text), 5);
                          }), 128))
                        ], 4))
                      ], 4);
                    }), 128))
                  ])
                ])) : (_openBlock$1(), _createElementBlock$1(_Fragment$1, { key: 1 }, [
                  _createElementVNode$1("div", _hoisted_21$1, [
                    _createElementVNode$1("div", {
                      class: "sim-style-3-title",
                      style: _normalizeStyle$1(mainTitleStyle.value)
                    }, _toDisplayString$1(titles.value.zh || "未配置中文标题"), 5),
                    _createElementVNode$1("div", _hoisted_22$1, [
                      _createElementVNode$1("div", {
                        class: "sim-style-3-accent",
                        style: _normalizeStyle$1(style3AccentStyle.value)
                      }, null, 4),
                      _createElementVNode$1("div", {
                        class: "sim-style-3-subtitle",
                        style: _normalizeStyle$1(subtitleStyle.value)
                      }, [
                        (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(style3SubtitleLines.value, (line, index) => {
                          return _openBlock$1(), _createElementBlock$1("span", {
                            key: `style3-subtitle-${index}`,
                            class: "sim-style-3-subtitle-line"
                          }, _toDisplayString$1(line), 1);
                        }), 128))
                      ], 4)
                    ])
                  ]),
                  _createElementVNode$1("div", _hoisted_23$1, [
                    (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(style3Columns.value, (column, columnIndex) => {
                      return _openBlock$1(), _createElementBlock$1("div", {
                        key: `column-${columnIndex}`,
                        class: _normalizeClass$1(["sim-style-3-column", `sim-style-3-column-${columnIndex + 1}`])
                      }, [
                        (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(column, (image) => {
                          return _openBlock$1(), _createElementBlock$1("div", {
                            key: image.key,
                            class: "sim-style-3-item"
                          }, [
                            _createElementVNode$1("img", {
                              src: image.src,
                              alt: image.label || `image-${image.slot}`
                            }, null, 8, _hoisted_24$1)
                          ]);
                        }), 128))
                      ], 2);
                    }), 128))
                  ])
                ], 64))
              ], 64)) : styleBase.value === "static_4" ? (_openBlock$1(), _createElementBlock$1(_Fragment$1, { key: 3 }, [
                _createElementVNode$1("div", {
                  class: "sim-bg",
                  style: _normalizeStyle$1(fullBackgroundStyle.value)
                }, null, 4),
                _createElementVNode$1("div", {
                  class: "sim-overlay sim-overlay-strong",
                  style: _normalizeStyle$1(overlayStyle.value)
                }, null, 4),
                shouldUseLayoutDrivenPresetStage.value ? (_openBlock$1(), _createElementBlock$1("div", _hoisted_25$1, [
                  _createElementVNode$1("div", _hoisted_26$1, [
                    (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(sortedLayers.value, (layer) => {
                      return _openBlock$1(), _createElementBlock$1("div", {
                        key: layer.id,
                        class: "sim-custom-layer",
                        style: _normalizeStyle$1(getLayerStyle(layer))
                      }, [
                        layer.type === "image" ? (_openBlock$1(), _createElementBlock$1(_Fragment$1, { key: 0 }, [
                          getLayerPreviewImage(layer)?.src ? (_openBlock$1(), _createElementBlock$1("img", {
                            key: 0,
                            class: "sim-custom-image",
                            src: getLayerPreviewImage(layer)?.src,
                            alt: getLayerPreviewImage(layer)?.label || `image-${layer.sourceIndex}`,
                            style: _normalizeStyle$1(getImageStyle(layer))
                          }, null, 12, _hoisted_27$1)) : _createCommentVNode$1("", true)
                        ], 64)) : layer.type === "main_title" || layer.type === "title_zh" ? (_openBlock$1(), _createElementBlock$1("div", {
                          key: 1,
                          class: "sim-custom-text sim-custom-text-zh",
                          style: _normalizeStyle$1(getTitleStyle(layer))
                        }, [
                          (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(getMeasuredLayerLines(layer), (line, index) => {
                            return _openBlock$1(), _createElementBlock$1("span", {
                              key: `${layer.id}-zh-${index}`,
                              class: "sim-custom-text-line",
                              style: _normalizeStyle$1(getMeasuredLineStyle(layer, index))
                            }, _toDisplayString$1(line.text), 5);
                          }), 128))
                        ], 4)) : (_openBlock$1(), _createElementBlock$1("div", {
                          key: 2,
                          class: "sim-custom-text sim-custom-text-en",
                          style: _normalizeStyle$1(getTitleStyle(layer))
                        }, [
                          (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(getMeasuredLayerLines(layer), (line, index) => {
                            return _openBlock$1(), _createElementBlock$1("span", {
                              key: `${layer.id}-text-${index}`,
                              class: "sim-custom-text-line",
                              style: _normalizeStyle$1(getMeasuredLineStyle(layer, index))
                            }, _toDisplayString$1(line.text), 5);
                          }), 128))
                        ], 4))
                      ], 4);
                    }), 128))
                  ])
                ])) : (_openBlock$1(), _createElementBlock$1("div", _hoisted_28$1, [
                  _createElementVNode$1("div", {
                    class: "sim-title-zh sim-title-center",
                    style: _normalizeStyle$1(mainTitleStyle.value)
                  }, _toDisplayString$1(titles.value.zh || "未配置中文标题"), 5),
                  _createElementVNode$1("div", {
                    class: "sim-title-en sim-title-center",
                    style: _normalizeStyle$1(subtitleStyle.value)
                  }, _toDisplayString$1(titles.value.en || "UNTITLED"), 5)
                ]))
              ], 64)) : (_openBlock$1(), _createElementBlock$1(_Fragment$1, { key: 4 }, [
                _createElementVNode$1("div", {
                  class: "sim-bg",
                  style: _normalizeStyle$1(backgroundStyle.value)
                }, null, 4),
                _createElementVNode$1("div", {
                  class: "sim-overlay",
                  style: _normalizeStyle$1(overlayStyle.value)
                }, null, 4),
                hasCustomLayout.value ? (_openBlock$1(), _createElementBlock$1("div", _hoisted_29$1, [
                  _createElementVNode$1("div", _hoisted_30$1, [
                    (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(sortedLayers.value, (layer) => {
                      return _openBlock$1(), _createElementBlock$1("div", {
                        key: layer.id,
                        class: "sim-custom-layer",
                        style: _normalizeStyle$1(getLayerStyle(layer))
                      }, [
                        layer.type === "image" ? (_openBlock$1(), _createElementBlock$1(_Fragment$1, { key: 0 }, [
                          getLayerPreviewImage(layer)?.src ? (_openBlock$1(), _createElementBlock$1("img", {
                            key: 0,
                            class: "sim-custom-image",
                            src: getLayerPreviewImage(layer)?.src,
                            alt: getLayerPreviewImage(layer)?.label || `image-${layer.sourceIndex}`,
                            style: _normalizeStyle$1(getImageStyle(layer))
                          }, null, 12, _hoisted_31$1)) : _createCommentVNode$1("", true)
                        ], 64)) : layer.type === "main_title" || layer.type === "title_zh" ? (_openBlock$1(), _createElementBlock$1("div", {
                          key: 1,
                          class: "sim-custom-text sim-custom-text-zh",
                          style: _normalizeStyle$1(getTitleStyle(layer))
                        }, [
                          (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(getMeasuredLayerLines(layer), (line, index) => {
                            return _openBlock$1(), _createElementBlock$1("span", {
                              key: `${layer.id}-zh-${index}`,
                              class: "sim-custom-text-line",
                              style: _normalizeStyle$1(getMeasuredLineStyle(layer, index))
                            }, _toDisplayString$1(line.text), 5);
                          }), 128))
                        ], 4)) : (_openBlock$1(), _createElementBlock$1("div", {
                          key: 2,
                          class: "sim-custom-text sim-custom-text-en",
                          style: _normalizeStyle$1(getTitleStyle(layer))
                        }, [
                          (_openBlock$1(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(getMeasuredLayerLines(layer), (line, index) => {
                            return _openBlock$1(), _createElementBlock$1("span", {
                              key: `${layer.id}-text-${index}`,
                              class: "sim-custom-text-line",
                              style: _normalizeStyle$1(getMeasuredLineStyle(layer, index))
                            }, _toDisplayString$1(line.text), 5);
                          }), 128))
                        ], 4))
                      ], 4);
                    }), 128))
                  ])
                ])) : (_openBlock$1(), _createElementBlock$1("div", _hoisted_32$1, [..._cache[4] || (_cache[4] = [
                  _createElementVNode$1("div", { class: "text-subtitle-2 mb-2" }, "当前未配置自定义布局", -1),
                  _createElementVNode$1("div", { class: "text-caption text-medium-emphasis" }, "先在“自定义风格”页保存一个方案，再回到这里预览。", -1)
                ])]))
              ], 64))
            ], 4))
          ], 2),
          variant.value === "animated" ? (_openBlock$1(), _createElementBlock$1("div", _hoisted_33$1, [..._cache[5] || (_cache[5] = [
            _createElementVNode$1("span", {
              class: "sim-live-icon",
              "aria-hidden": "true"
            }, [
              _createElementVNode$1("span")
            ], -1)
          ])])) : _createCommentVNode$1("", true)
        ], 4))
      ]);
    };
  }
});

const GeneratePreviewSimulation = /* @__PURE__ */ _export_sfc(_sfc_main$1, [["__scopeId", "data-v-828b36ce"]]);

const DEFAULT_TIME_ZONE = "Asia/Shanghai";
const toDate = (value) => value instanceof Date ? value : new Date(typeof value === "number" && value < 1e12 ? value * 1e3 : value);
function formatDateTime(value, timeZone = DEFAULT_TIME_ZONE) {
  const date = toDate(value);
  if (Number.isNaN(date.getTime())) return "未知时间";
  return new Intl.DateTimeFormat("zh-CN", { timeZone, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false }).format(date).replaceAll("/", "-");
}
function formatTimelineTime(value, timeZone = DEFAULT_TIME_ZONE) {
  const date = toDate(value);
  if (Number.isNaN(date.getTime())) return "未知时间";
  const now = /* @__PURE__ */ new Date();
  const day = (item) => new Intl.DateTimeFormat("en-CA", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" }).format(item);
  const time = new Intl.DateTimeFormat("zh-CN", { timeZone, hour: "2-digit", minute: "2-digit", hour12: false }).format(date);
  if (day(date) === day(now)) return `今天 ${time}`;
  if (day(date) === day(new Date(now.getTime() - 864e5))) return `昨天 ${time}`;
  return `${new Intl.DateTimeFormat("zh-CN", { timeZone, month: "numeric", day: "numeric" }).format(date)} ${time}`;
}

const DB_NAME = "yahaha-cover-studio-cache";
const DB_VERSION = 1;
const STORE_NAME = "entries";
const PREVIEW_CACHE_SCHEMA = 2;
const HISTORY_CACHE_SCHEMA = 1;
const PREVIEW_MAX_ENTRIES = 30;
const HISTORY_MAX_ENTRIES = 8;
const PREVIEW_MAX_AGE = 7 * 24 * 60 * 60 * 1e3;
const HISTORY_MAX_AGE = 30 * 24 * 60 * 60 * 1e3;
const memory = /* @__PURE__ */ new Map();
let databasePromise = null;
function openDatabase() {
  if (databasePromise) return databasePromise;
  if (typeof indexedDB === "undefined") return Promise.resolve(null);
  databasePromise = new Promise((resolve) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) db.createObjectStore(STORE_NAME, { keyPath: "id" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => resolve(null);
  });
  return databasePromise;
}
async function readAll() {
  const db = await openDatabase();
  if (!db) return [...memory.values()];
  return new Promise((resolve) => {
    const request = db.transaction(STORE_NAME, "readonly").objectStore(STORE_NAME).getAll();
    request.onsuccess = () => resolve(Array.isArray(request.result) ? request.result : []);
    request.onerror = () => resolve([]);
  });
}
async function writeRecord(record) {
  memory.set(record.id, record);
  const db = await openDatabase();
  if (!db) return;
  await new Promise((resolve) => {
    const request = db.transaction(STORE_NAME, "readwrite").objectStore(STORE_NAME).put(record);
    request.onsuccess = () => resolve();
    request.onerror = () => resolve();
  });
}
async function deleteRecords(ids) {
  ids.forEach((id) => memory.delete(id));
  const db = await openDatabase();
  if (!db || !ids.length) return;
  await new Promise((resolve) => {
    const transaction = db.transaction(STORE_NAME, "readwrite");
    ids.forEach((id) => transaction.objectStore(STORE_NAME).delete(id));
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => resolve();
  });
}
async function prune(kind, maxEntries) {
  const records = (await readAll()).filter((item) => item.kind === kind).sort((a, b) => b.lastUsedAt - a.lastUsedAt);
  await deleteRecords(records.slice(maxEntries).map((item) => item.id));
}
function stableCacheSignature(value) {
  const normalize = (item) => {
    if (Array.isArray(item)) return [...item].map(normalize).sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b)));
    if (item && typeof item === "object") return Object.keys(item).sort().reduce((result, key) => {
      result[key] = normalize(item[key]);
      return result;
    }, {});
    return item ?? "";
  };
  const text = JSON.stringify(normalize(value));
  let hash = 2166136261;
  for (let index = 0; index < text.length; index += 1) hash = Math.imul(hash ^ text.charCodeAt(index), 16777619);
  return (hash >>> 0).toString(36);
}
async function getPreviewCache(baseKey, requiredItems) {
  const now = Date.now();
  const records = (await readAll()).filter((item) => item.kind === "preview" && item.schema === PREVIEW_CACHE_SCHEMA && item.baseKey === baseKey && item.capacity >= requiredItems && now - item.updatedAt <= PREVIEW_MAX_AGE).sort((a, b) => a.capacity - b.capacity || b.updatedAt - a.updatedAt);
  const match = records[0];
  if (!match) return null;
  match.lastUsedAt = now;
  memory.set(match.id, match);
  void writeRecord(match);
  return match.payload;
}
async function setPreviewCache(baseKey, requiredItems, payload) {
  const now = Date.now();
  await writeRecord({ id: `preview:v${PREVIEW_CACHE_SCHEMA}:${baseKey}:${requiredItems}`, kind: "preview", schema: PREVIEW_CACHE_SCHEMA, baseKey, capacity: requiredItems, updatedAt: now, lastUsedAt: now, payload });
  await prune("preview", PREVIEW_MAX_ENTRIES);
}
async function invalidatePreviewCache(baseKey) {
  const records = (await readAll()).filter((item) => item.kind === "preview" && (!baseKey || item.baseKey === baseKey));
  await deleteRecords(records.map((item) => item.id));
}
async function getHistoryCache(baseKey) {
  const now = Date.now();
  const id = `history:v${HISTORY_CACHE_SCHEMA}:${baseKey}`;
  const records = await readAll();
  const match = records.find((item) => item.id === id && item.schema === HISTORY_CACHE_SCHEMA && now - item.updatedAt <= HISTORY_MAX_AGE);
  if (!match) return null;
  match.lastUsedAt = now;
  memory.set(id, match);
  void writeRecord(match);
  return match.payload;
}
async function setHistoryCache(baseKey, payload) {
  const now = Date.now();
  await writeRecord({ id: `history:v${HISTORY_CACHE_SCHEMA}:${baseKey}`, kind: "history", schema: HISTORY_CACHE_SCHEMA, baseKey, capacity: Array.isArray(payload) ? payload.length : 1, updatedAt: now, lastUsedAt: now, payload });
  await prune("history", HISTORY_MAX_ENTRIES);
}

const images = {
  wx_code_dark: 'data:image/webp;base64,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',
  wx_code_light: 'data:image/webp;base64,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',
  avatar: 'data:image/webp;base64,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',
};

const {defineComponent:_defineComponent} = await importShared('vue');

const {createElementVNode:_createElementVNode,unref:_unref,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,resolveComponent:_resolveComponent,createBlock:_createBlock,createVNode:_createVNode,withModifiers:_withModifiers,normalizeClass:_normalizeClass,toDisplayString:_toDisplayString,normalizeStyle:_normalizeStyle,withCtx:_withCtx,mergeProps:_mergeProps,createTextVNode:_createTextVNode,vModelSelect:_vModelSelect,withDirectives:_withDirectives,withKeys:_withKeys,Transition:_Transition,renderList:_renderList,Fragment:_Fragment,vShow:_vShow,Teleport:_Teleport} = await importShared('vue');

const _hoisted_1 = ["data-mcr-theme"];
const _hoisted_2 = { class: "mcr-shell__header mcr-page-hero" };
const _hoisted_3 = { class: "mcr-shell__header-grid" };
const _hoisted_4 = { class: "mcr-shell__copy" };
const _hoisted_5 = { class: "mcr-page-title-row yh-brand-row" };
const _hoisted_6 = { class: "yh-avatar" };
const _hoisted_7 = ["src"];
const _hoisted_8 = { class: "blueprint-hero-actions" };
const _hoisted_9 = { class: "mcr-page-top-actions yh-top-actions" };
const _hoisted_10 = { class: "yh-avatar" };
const _hoisted_11 = ["src"];
const _hoisted_12 = ["title", "aria-label", "disabled"];
const _hoisted_13 = { class: "yh-run-content" };
const _hoisted_14 = {
  key: 0,
  class: "yh-run-text"
};
const _hoisted_15 = {
  key: 1,
  class: "yh-run-percent"
};
const _hoisted_16 = {
  class: "yh-preview-chips",
  "aria-label": "当前参数"
};
const _hoisted_17 = { key: 0 };
const _hoisted_18 = {
  role: "tablist",
  "aria-label": "页面切换",
  class: "mcr-page-tabs-track"
};
const _hoisted_19 = ["aria-selected", "disabled"];
const _hoisted_20 = ["aria-selected", "disabled"];
const _hoisted_21 = { class: "blueprint-panel-heading" };
const _hoisted_22 = { class: "mcr-panel__eyebrow" };
const _hoisted_23 = { class: "mcr-panel__title" };
const _hoisted_24 = ["disabled"];
const _hoisted_25 = { class: "mcr-editor-save-cluster" };
const _hoisted_26 = { class: "mcr-editor-split-save" };
const _hoisted_27 = ["disabled"];
const _hoisted_28 = ["aria-label", "title", "disabled"];
const _hoisted_29 = { class: "mcr-editor-save-mode" };
const _hoisted_30 = {
  key: 1,
  class: "blueprint-preview-frame"
};
const _hoisted_31 = {
  key: 2,
  class: "blueprint-meta-grid mcr-render-options"
};
const _hoisted_32 = { class: "mcr-render-option" };
const _hoisted_33 = ["disabled"];
const _hoisted_34 = { class: "mcr-render-option" };
const _hoisted_35 = { class: "yh-field-label" };
const _hoisted_36 = {
  key: 0,
  class: "yh-inline-lock-badge"
};
const _hoisted_37 = ["disabled"];
const _hoisted_38 = { value: "DateCreated" };
const _hoisted_39 = { class: "mcr-render-option" };
const _hoisted_40 = ["disabled"];
const _hoisted_41 = {
  key: 1,
  class: "mcr-render-option__value"
};
const _hoisted_42 = ["aria-expanded"];
const _hoisted_43 = { class: "mcr-collapsible-heading__title" };
const _hoisted_44 = { class: "mcr-panel__title" };
const _hoisted_45 = ["aria-pressed", "aria-disabled", "disabled", "onKeydown"];
const _hoisted_46 = {
  key: 0,
  class: "mcr-animated-parameter-panel"
};
const _hoisted_47 = { class: "mcr-animated-parameter-panel__header" };
const _hoisted_48 = { class: "mcr-animated-settings__grid" };
const _hoisted_49 = {
  key: 3,
  class: "mcr-note"
};
const _hoisted_50 = { class: "mcr-animated-parameter-panel__actions" };
const _hoisted_51 = ["aria-disabled", "tabindex", "onClick", "onKeydown"];
const _hoisted_52 = { class: "mcr-scheme-row__media" };
const _hoisted_53 = { class: "mcr-scheme-row__body" };
const _hoisted_54 = { key: 0 };
const _hoisted_55 = { key: 1 };
const _hoisted_56 = { class: "mcr-scheme-row__actions" };
const _hoisted_57 = {
  key: 0,
  class: "mcr-scheme-list__tail"
};
const _hoisted_58 = ["aria-expanded"];
const _hoisted_59 = { class: "mcr-collapsible-heading__title" };
const _hoisted_60 = { class: "mcr-panel__title" };
const _hoisted_61 = ["data-mcr-theme"];
const _hoisted_62 = ["onClick"];
const _hoisted_63 = ["onClick"];
const _hoisted_64 = ["data-mcr-theme"];
const _hoisted_65 = { class: "mcr-history-selection-count" };
const _hoisted_66 = ["disabled"];
const _hoisted_67 = ["disabled"];
const _hoisted_68 = ["disabled"];
const _hoisted_69 = ["disabled"];
const _hoisted_70 = ["disabled"];
const _hoisted_71 = {
  id: "mcr-history-list-content",
  class: "mcr-history-list-content"
};
const _hoisted_72 = {
  key: 0,
  class: "mcr-history-groups"
};
const _hoisted_73 = ["id"];
const _hoisted_74 = { class: "mcr-history-group__heading" };
const _hoisted_75 = { class: "mcr-history-group__title" };
const _hoisted_76 = ["aria-label", "onClick"];
const _hoisted_77 = ["src", "alt"];
const _hoisted_78 = {
  key: 0,
  class: "mcr-time-machine-stack__more"
};
const _hoisted_79 = { class: "mcr-history-card__media" };
const _hoisted_80 = ["aria-pressed", "aria-label", "disabled", "onClick"];
const _hoisted_81 = { class: "mcr-history-card__title" };
const _hoisted_82 = { class: "mcr-history-card__meta" };
const _hoisted_83 = {
  key: 1,
  class: "mcr-history-empty"
};
const _hoisted_84 = { class: "mcr-history-snapshot__header" };
const _hoisted_85 = { class: "mcr-history-snapshot__grid" };
const _hoisted_86 = ["aria-checked", "onClick", "onKeydown"];
const _hoisted_87 = ["src", "alt"];
const _hoisted_88 = { class: "mcr-history-snapshot__labels" };
const _hoisted_89 = ["title"];
const _hoisted_90 = ["title"];
const _hoisted_91 = {
  key: 0,
  class: "mcr-donation-profile"
};
const _hoisted_92 = ["src"];
const _hoisted_93 = {
  class: "mcr-donation-profile__crown",
  "aria-hidden": "true"
};
const _hoisted_94 = { class: "mcr-donation-title" };
const _hoisted_95 = { class: "mcr-donation-subtitle" };
const _hoisted_96 = {
  class: "mcr-donation-heart",
  "aria-hidden": "true"
};
const _hoisted_97 = {
  key: 2,
  class: "mcr-donation-stats"
};
const _hoisted_98 = { class: "mcr-donation-stat-card" };
const _hoisted_99 = { class: "mcr-donation-stat-card__top" };
const _hoisted_100 = { class: "mcr-donation-stat-icon mcr-donation-stat-icon--static" };
const _hoisted_101 = { class: "mcr-donation-stat-card" };
const _hoisted_102 = { class: "mcr-donation-stat-card__top" };
const _hoisted_103 = { class: "mcr-donation-stat-icon mcr-donation-stat-icon--dynamic" };
const _hoisted_104 = { class: "mcr-donation-stat-card" };
const _hoisted_105 = { class: "mcr-donation-stat-card__top" };
const _hoisted_106 = { class: "mcr-donation-stat-icon mcr-donation-stat-icon--history" };
const _hoisted_107 = { class: "mcr-donation-stat-card" };
const _hoisted_108 = { class: "mcr-donation-stat-card__top" };
const _hoisted_109 = { class: "mcr-donation-stat-icon mcr-donation-stat-icon--run" };
const _hoisted_110 = {
  key: 3,
  class: "mcr-donation-qr"
};
const _hoisted_111 = ["src"];
const _hoisted_112 = {
  key: 4,
  class: "mcr-donation-message"
};
const _hoisted_113 = { class: "mcr-donation-card__actions" };
const _hoisted_114 = {
  key: 5,
  class: "mcr-donation-footnote"
};
const {computed,nextTick,onBeforeUnmount,onMounted,reactive,ref,watch} = await importShared('vue');
const DONATION_ACK_STORAGE_KEY = "yahaha_supported";
const DONATION_LEGACY_ACK_STORAGE_KEY = "mcr-donation-acknowledged";
const DONATION_AVATAR_STORAGE_KEY = "yahaha_avatar_source";
const DONATION_RUN_COUNT_STORAGE_KEY = "yahaha_generation_run_count";
const HISTORY_CACHE_KEY = "all:newest";
const EDITOR_AUTO_SAVE_STORAGE_KEY = "mcr-editor-auto-save-enabled";
const _sfc_main = /* @__PURE__ */ _defineComponent({
  __name: "Page",
  props: {
    api: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ["action", "switch", "close"],
  setup(__props, { emit: __emit }) {
    const PRESET_STYLE_BASES = ["static_1", "static_2", "static_3", "static_4"];
    const props = __props;
    const emit = __emit;
    const controlDefaults = MCR_CONTROL_DEFAULTS;
    const pageTab = ref("generate-tab");
    const setupWarnings = ref([]);
    const pluginEnabled = ref(false);
    const styleVariant = ref("static");
    const coverStyleBase = ref("static_1");
    const previewMode = ref("frontend");
    const previewSource = ref(null);
    const backendPreview = ref(null);
    const donationDialog = ref(false);
    const donationAcknowledged = ref(false);
    const donationView = ref("overview");
    const donationAvatarSource = ref("developer");
    const donationExecutionCount = ref(0);
    const moviePilotAvatarUrl = ref("");
    const refreshingPreview = ref(false);
    const previewSourcesLoading = ref(false);
    const statusLoading = ref(false);
    const historyLoading = ref(false);
    const historyUpdating = ref(false);
    const showingCachedHistory = ref(false);
    const backendPreviewLoading = ref(false);
    const styleUpdating = ref(false);
    const layoutPersisting = ref(false);
    const generatingNow = ref(false);
    const previewCacheContext = ref({});
    let previewSourceRequestId = 0;
    const isGenerating = ref(false);
    const statusLoaded = ref(false);
    const previewBayEl = ref(null);
    const schemeListScrollEl = ref(null);
    const previewBayHeight = ref(0);
    const schemeListCollapsed = ref(false);
    const historyHeaderEl = ref(null);
    const historyListCollapsed = ref(false);
    const historyFloatingStyle = ref({
      left: "50%",
      top: "88px",
      transform: "translateX(-50%)"
    });
    const importTemplateInput = ref(null);
    const modeSwitchPulse = ref(false);
    const customStaticLayout = ref(null);
    const customTemplates = ref([]);
    const selectedCustomTemplateId = ref(null);
    const activeEditorTemplateId = ref(null);
    const presetStaticRenderMode = ref("layout");
    const animatedSettingsPanelOpen = ref(false);
    const animatedSettingsSaving = ref(false);
    const animatedSettingsBaseStyle = ref("static_1");
    const animatedSettingsByStyle = ref({});
    const customFontItems = ref([]);
    const posterSource = ref("backdrop");
    const sourceSortBy = ref("Random");
    const sourceSortLocked = ref(false);
    const imageCountMode = ref("auto");
    const imageCount = ref(9);
    const autoImageCount = ref(9);
    const staticResolution = ref("480p");
    const animationResolution = ref("320x180");
    const renderOptionsSaving = ref(false);
    const generationCurrent = ref(0);
    const generationTotal = ref(0);
    const generationLabel = ref("");
    const editorAutoSaveEnabled = ref(readEditorAutoSavePreference());
    const editorSaveStatus = ref("");
    const recentDownloadRegistry = /* @__PURE__ */ new Map();
    const animatedSettings = reactive({
      animationDuration: 8,
      animationFps: 24,
      animationFormat: "apng",
      animationScroll: "alternate",
      animationReduceColors: "medium",
      animated2ImageCount: 6,
      animated2DepartureType: "fly",
      mainTitleFontPreset: "chaohei",
      subtitleFontPreset: "EmblemaOne",
      customTextFontPreset: "EmblemaOne",
      mainTitleFontSize: 170,
      subtitleFontSize: 75,
      blurSize: 50,
      colorRatio: 0.8,
      titleScale: 1
    });
    const controlBayStyle = computed(
      () => previewBayHeight.value > 0 ? { "--mcr-scheme-panel-height": `${previewBayHeight.value}px` } : {}
    );
    const simulationParams = reactive({
      blur: 50,
      colorRatio: 0.8,
      colorSource: "auto",
      customColor: getThemeColor("--mcr-cover-auto-blend")
    });
    const history = ref([]);
    const historyGroupMode = ref("library");
    const restoringBatchId = ref("");
    const activeTimeRecordId = ref("");
    const historySnapshotDialog = ref(false);
    const selectedHistorySnapshot = ref(null);
    const restoreConfirmDialog = ref(false);
    const pendingHistoryRestore = ref(null);
    const historyStackLimit = ref(5);
    const historySortMode = ref("newest");
    const selectedHistoryPaths = ref([]);
    const donationAvatarIcon = computed(
      () => donationAvatarSource.value === "mp" ? "mdi-account-circle-outline" : "mdi-image-filter-hdr-outline"
    );
    const donationAvatarImage = computed(
      () => donationAvatarSource.value === "developer" ? images.avatar : moviePilotAvatarUrl.value
    );
    const donationQrImage = computed(() => isDark.value ? images.wx_code_dark : images.wx_code_light);
    const donationStaticSchemeCount = computed(() => PRESET_STYLE_BASES.length + getUserCustomTemplates(customTemplates.value).length);
    const donationDynamicSchemeCount = computed(() => PRESET_STYLE_BASES.length);
    computed(() => donationStaticSchemeCount.value + donationDynamicSchemeCount.value);
    const donationHistoryCount = computed(() => history.value.length || 0);
    const sourceSortDisabled = computed(() => controlsLocked.value || sourceSortLocked.value);
    ref(false);
    const isEditingLayout = ref(false);
    const controlsLocked = computed(() => isGenerating.value || generatingNow.value || !statusLoaded.value);
    const resourceSkeletonActive = computed(() => previewSourcesLoading.value || !statusLoaded.value);
    const backendBusy = computed(
      () => statusLoading.value || historyLoading.value || backendPreviewLoading.value || previewSourcesLoading.value || styleUpdating.value || layoutPersisting.value || animatedSettingsSaving.value || renderOptionsSaving.value || generatingNow.value
    );
    const backendBusyLabel = computed(() => {
      if (isGenerating.value) {
        if (generationTotal.value > 0) {
          return `正在生成 ${generationCurrent.value || 0}/${generationTotal.value}`;
        }
        return generationLabel.value || "正在生成";
      }
      if (generatingNow.value) return "正在执行";
      if (renderOptionsSaving.value) return "保存素材";
      if (animatedSettingsSaving.value) return "保存参数";
      if (layoutPersisting.value) return "保存布局";
      if (styleUpdating.value) return "切换方案";
      if (historyLoading.value) return "加载历史";
      if (backendPreviewLoading.value) return "渲染预览";
      if (previewSourcesLoading.value) return "加载素材";
      return "同步数据";
    });
    const prefersDark = ref(false);
    const hostThemeVersion = ref(0);
    let pageThemeMediaQuery = null;
    let pageThemeObserver = null;
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
    const styleItems = [
      { title: "风格 1", value: "static_1" },
      { title: "风格 2", value: "static_2" },
      { title: "风格 3", value: "static_3" },
      { title: "风格 4", value: "static_4" },
      { title: "自定义", value: "custom_static" }
    ];
    function getStyleTitle(value) {
      return styleItems.find((item) => item.value === value)?.title || value;
    }
    function stripPresetEditableSuffix(name) {
      return String(name || "").replace(/\s*可编辑布局$/u, "").trim();
    }
    function getPresetSchemeTitle(baseStyle, template) {
      return stripPresetEditableSuffix(template?.name || "") || getStyleTitle(baseStyle);
    }
    function normalizeCoverStyleBase(value) {
      if (value === "static_1" || value === "static_2" || value === "static_3" || value === "static_4" || value === "custom_static") {
        return value;
      }
      return "static_1";
    }
    function isPresetStaticStyle(value) {
      return PRESET_STYLE_BASES.includes(value);
    }
    function isSystemTemplate(template) {
      return Boolean(template?.system) || String(template?.id || "").startsWith("__preset_");
    }
    function normalizeTemplateList(templates) {
      if (!Array.isArray(templates)) return [];
      return templates.map((tpl) => ({
        ...tpl,
        layout: cloneLayout(tpl.layout)
      }));
    }
    function getTemplateById(id) {
      if (!id) return null;
      return customTemplates.value.find((tpl) => tpl.id === id) ?? null;
    }
    function getUserCustomTemplates(templates = customTemplates.value) {
      return templates.filter((tpl) => !isSystemTemplate(tpl));
    }
    function getStyleDefaultLayout(baseStyle) {
      if (isPresetStaticStyle(baseStyle)) {
        return createLayoutFromBuiltInStyle(baseStyle);
      }
      return createDefaultLayout();
    }
    function buildPresetTemplate(baseStyle) {
      return {
        id: `__preset_${baseStyle}`,
        name: getStyleTitle(baseStyle),
        layout: cloneLayout(getStyleDefaultLayout(baseStyle)),
        baseStyle,
        system: true
      };
    }
    function ensurePresetTemplate(baseStyle) {
      const templateId = `__preset_${baseStyle}`;
      const existing = getTemplateById(templateId);
      if (existing) return existing;
      const presetTemplate = buildPresetTemplate(baseStyle);
      customTemplates.value = [...customTemplates.value, presetTemplate];
      return presetTemplate;
    }
    function setEditorTemplate(templateId) {
      activeEditorTemplateId.value = templateId;
      const template = getTemplateById(templateId);
      customStaticLayout.value = template ? cloneLayout(template.layout) : null;
    }
    function setSelectedCustomTemplate(templateId) {
      selectedCustomTemplateId.value = templateId;
      setEditorTemplate(templateId);
    }
    function syncLayoutToTemplate(templateId, layout) {
      if (!templateId || !layout) return;
      const index = customTemplates.value.findIndex((tpl) => tpl.id === templateId);
      if (index === -1) return;
      const next = [...customTemplates.value];
      next[index] = {
        ...next[index],
        layout: cloneLayout(layout)
      };
      customTemplates.value = next;
    }
    function applyCustomTemplateState(templates, preferredCustomId) {
      customTemplates.value = normalizeTemplateList(templates);
      const userTemplates = getUserCustomTemplates(customTemplates.value);
      if (preferredCustomId && userTemplates.some((tpl) => tpl.id === preferredCustomId)) {
        selectedCustomTemplateId.value = preferredCustomId;
        return;
      }
      if (selectedCustomTemplateId.value && userTemplates.some((tpl) => tpl.id === selectedCustomTemplateId.value)) {
        return;
      }
      selectedCustomTemplateId.value = userTemplates[0]?.id ?? null;
    }
    function ensureCustomTemplateInitialized() {
      const userTemplates = getUserCustomTemplates();
      if (!userTemplates.length) {
        const id = createLayoutId();
        const template = {
          id,
          name: "自定义方案",
          layout: cloneLayout(customStaticLayout.value || createDefaultLayout()),
          baseStyle: "custom_static"
        };
        customTemplates.value = [...customTemplates.value, template];
        setSelectedCustomTemplate(id);
        return;
      }
      if (selectedCustomTemplateId.value && userTemplates.some((tpl) => tpl.id === selectedCustomTemplateId.value)) {
        setEditorTemplate(selectedCustomTemplateId.value);
        return;
      }
      setSelectedCustomTemplate(userTemplates[0].id);
    }
    const schemeListItems = computed(() => {
      const presetItems = PRESET_STYLE_BASES.map((baseStyle) => {
        const templateId = `__preset_${baseStyle}`;
        const template = getTemplateById(templateId) || void 0;
        return {
          id: templateId,
          kind: "preset",
          title: getPresetSchemeTitle(baseStyle, template),
          baseStyle,
          templateId,
          template
        };
      });
      const customItems = getUserCustomTemplates().map((template) => ({
        id: template.id,
        kind: "custom",
        title: template.name || "自定义方案",
        baseStyle: "custom_static",
        templateId: template.id,
        template
      }));
      return styleVariant.value === "animated" ? presetItems : [...presetItems, ...customItems];
    });
    const schemeListKey = computed(
      () => `${styleVariant.value}:${schemeListItems.value.map((item) => item.id).join("|")}`
    );
    function getReservedSchemeNames(ignoreId) {
      const names = /* @__PURE__ */ new Set();
      for (const baseStyle of PRESET_STYLE_BASES) {
        const presetId = `__preset_${baseStyle}`;
        if (presetId !== ignoreId) {
          names.add(getPresetSchemeTitle(baseStyle, getTemplateById(presetId)));
        }
      }
      for (const template of customTemplates.value) {
        if (template.id === ignoreId) continue;
        if (isSystemTemplate(template) && isPresetStaticStyle(template.baseStyle)) {
          names.add(getPresetSchemeTitle(template.baseStyle, template));
          continue;
        }
        if (template.name?.trim()) {
          names.add(template.name.trim());
        }
      }
      return names;
    }
    function getUniqueTemplateName(name, ignoreId) {
      const baseName = String(name || "").trim() || "自定义方案";
      const reserved = getReservedSchemeNames(ignoreId);
      if (!reserved.has(baseName)) return baseName;
      let index = 2;
      let nextName = `${baseName} ${index}`;
      while (reserved.has(nextName)) {
        index += 1;
        nextName = `${baseName} ${index}`;
      }
      return nextName;
    }
    function resolveSchemeTemplate(item, ensure = false) {
      if (item.kind === "preset") {
        const template = ensure && isPresetStaticStyle(item.baseStyle) ? ensurePresetTemplate(item.baseStyle) : getTemplateById(item.templateId) || buildPresetTemplate(item.baseStyle);
        return template ? {
          ...template,
          name: getPresetSchemeTitle(item.baseStyle, template),
          layout: cloneLayout(template.layout)
        } : null;
      }
      return getTemplateById(item.templateId);
    }
    let generationStatusTimer = null;
    let measureLayoutTimer = null;
    let measureLayoutApiAvailable = true;
    let measureLayoutRequestToken = 0;
    let lastCustomLayoutPersistAt = 0;
    let autoSaveLayoutTimer = null;
    let editorSaveStatusTimer = null;
    let autoSaveInFlight = false;
    let autoSaveQueued = false;
    let previewSourceReloadTimer = null;
    let syncingBackendState = false;
    let statusLoadPromise = null;
    let componentActive = false;
    let previewBayResizeObserver = null;
    let editorEnterScrollToken = 0;
    function updatePreviewBayHeight() {
      if (typeof window === "undefined") return;
      const el = previewBayEl.value;
      if (!el || isEditingLayout.value) {
        previewBayHeight.value = 0;
        return;
      }
      previewBayHeight.value = Math.round(el.getBoundingClientRect().height);
    }
    function isMobileViewport() {
      return typeof window !== "undefined" && window.matchMedia("(max-width: 959px)").matches;
    }
    function waitForAnimationFrame() {
      return new Promise((resolve) => {
        window.requestAnimationFrame(() => resolve());
      });
    }
    function isScrollableElement(el) {
      const style = window.getComputedStyle(el);
      const overflowY = style.overflowY;
      return /(auto|scroll|overlay)/.test(overflowY) && el.scrollHeight > el.clientHeight + 2;
    }
    function getScrollableAncestors(el) {
      const ancestors = [];
      let current = el.parentElement;
      while (current && current !== document.body && current !== document.documentElement) {
        if (isScrollableElement(current)) {
          ancestors.push(current);
        }
        current = current.parentElement;
      }
      return ancestors;
    }
    function alignElementInScroller(el, scroller, offset, behavior) {
      const targetRect = el.getBoundingClientRect();
      const scrollerRect = scroller.getBoundingClientRect();
      const nextTop = scroller.scrollTop + targetRect.top - scrollerRect.top - offset;
      scroller.scrollTo({
        top: Math.max(0, nextTop),
        behavior
      });
    }
    function alignElementInDocument(el, offset, behavior) {
      const targetRect = el.getBoundingClientRect();
      const nextTop = window.scrollY + targetRect.top - offset;
      window.scrollTo({
        top: Math.max(0, nextTop),
        behavior
      });
    }
    function alignEditorTitleToViewport(behavior) {
      const targetRoot = previewBayEl.value;
      if (!targetRoot) return;
      const heading = targetRoot.querySelector(".blueprint-panel-heading");
      const target = heading ?? targetRoot;
      const offset = 10;
      const scroller = getScrollableAncestors(target)[0];
      if (scroller) {
        alignElementInScroller(target, scroller, offset, behavior);
      }
      alignElementInDocument(target, offset, behavior);
    }
    async function scrollEditorIntoView() {
      const token = ++editorEnterScrollToken;
      await nextTick();
      if (typeof window === "undefined" || !isMobileViewport()) return;
      await waitForAnimationFrame();
      await waitForAnimationFrame();
      if (token !== editorEnterScrollToken) return;
      alignEditorTitleToViewport("smooth");
      const cancelDelayedAlignment = () => {
        editorEnterScrollToken += 1;
        window.removeEventListener("pointerdown", cancelDelayedAlignment, true);
      };
      window.addEventListener("pointerdown", cancelDelayedAlignment, true);
      window.setTimeout(() => {
        window.removeEventListener("pointerdown", cancelDelayedAlignment, true);
        if (token !== editorEnterScrollToken) return;
        alignEditorTitleToViewport("auto");
      }, 220);
    }
    async function normalizeSchemeListViewport() {
      await nextTick();
      if (typeof window === "undefined") return;
      window.requestAnimationFrame(() => {
        const el = schemeListScrollEl.value;
        if (el) {
          const maxScrollTop = Math.max(0, el.scrollHeight - el.clientHeight);
          if (el.scrollTop > maxScrollTop) {
            el.scrollTop = maxScrollTop;
          }
          if (maxScrollTop === 0) {
            el.scrollTop = 0;
          }
        }
        updatePreviewBayHeight();
      });
    }
    function cancelPendingLayoutMeasure() {
      measureLayoutRequestToken += 1;
      if (measureLayoutTimer !== null) {
        window.clearTimeout(measureLayoutTimer);
        measureLayoutTimer = null;
      }
    }
    function cancelPendingAutoSave() {
      if (autoSaveLayoutTimer !== null) {
        window.clearTimeout(autoSaveLayoutTimer);
        autoSaveLayoutTimer = null;
      }
      if (editorSaveStatusTimer !== null) {
        window.clearTimeout(editorSaveStatusTimer);
        editorSaveStatusTimer = null;
      }
    }
    function showEditorSaveStatus(text) {
      editorSaveStatus.value = text;
      if (editorSaveStatusTimer !== null) {
        window.clearTimeout(editorSaveStatusTimer);
      }
      editorSaveStatusTimer = window.setTimeout(() => {
        editorSaveStatus.value = "";
        editorSaveStatusTimer = null;
      }, 2400);
    }
    function toggleEditorAutoSave() {
      editorAutoSaveEnabled.value = !editorAutoSaveEnabled.value;
      showEditorSaveStatus(editorAutoSaveEnabled.value ? "已开启自动保存" : "已关闭自动保存");
    }
    function cancelPendingPreviewSourceReload() {
      if (previewSourceReloadTimer !== null) {
        window.clearTimeout(previewSourceReloadTimer);
        previewSourceReloadTimer = null;
      }
    }
    function shouldBlockLockedAction() {
      if (!controlsLocked.value) return false;
      if (!isGenerating.value) {
        void loadStatus();
      }
      return true;
    }
    function isStickerLayerLike(layer) {
      if (!layer || typeof layer !== "object") return false;
      return layer.assetKind === "sticker" || Boolean(layer.stickerDataUrl || layer.stickerPath || layer.stickerUrl);
    }
    function getLayoutMaxImageSourceIndex(layout) {
      const visit = (layers) => layers.reduce((maxIndex, layer) => {
        if (!layer || typeof layer !== "object") return maxIndex;
        const childMax = layer.type === "group" ? visit(layer.children || []) : 0;
        if (layer.type !== "image") return Math.max(maxIndex, childMax);
        if (isStickerLayerLike(layer)) return Math.max(maxIndex, childMax);
        const sourceIndex = Number(layer.sourceIndex ?? layer.source?.slot ?? 1);
        return Math.max(maxIndex, childMax, Number.isFinite(sourceIndex) ? sourceIndex : 1);
      }, 0);
      return Math.max(1, visit(layout?.layers || []));
    }
    function schedulePreviewSourceReloadForLayout(layout) {
      if (controlsLocked.value) return;
      const requiredItems = Math.max(1, getLayoutMaxImageSourceIndex(layout));
      const currentItems = previewSource.value?.images?.length || 0;
      if (requiredItems <= currentItems) return;
      cancelPendingPreviewSourceReload();
      previewSourceReloadTimer = window.setTimeout(() => {
        previewSourceReloadTimer = null;
        void loadPreviewSources(requiredItems);
      }, 240);
    }
    function scheduleAutoSaveCustomLayout() {
      if (controlsLocked.value) return;
      if (!editorAutoSaveEnabled.value) return;
      if (!showInlineLayoutEditor.value || !customStaticLayout.value || !activeEditorTemplateId.value) return;
      cancelPendingAutoSave();
      autoSaveLayoutTimer = window.setTimeout(() => {
        autoSaveLayoutTimer = null;
        void flushAutoSaveCustomLayout();
      }, 900);
    }
    function readEditorAutoSavePreference() {
      if (typeof window === "undefined") return true;
      return window.localStorage.getItem(EDITOR_AUTO_SAVE_STORAGE_KEY) !== "false";
    }
    async function flushAutoSaveCustomLayout() {
      if (controlsLocked.value) {
        cancelPendingAutoSave();
        autoSaveQueued = false;
        return;
      }
      if (!showInlineLayoutEditor.value || !customStaticLayout.value || !activeEditorTemplateId.value) return;
      if (autoSaveInFlight) {
        autoSaveQueued = true;
        return;
      }
      autoSaveInFlight = true;
      try {
        await persistCustomLayoutState();
        showEditorSaveStatus("已自动保存");
      } finally {
        autoSaveInFlight = false;
        if (autoSaveQueued) {
          autoSaveQueued = false;
          scheduleAutoSaveCustomLayout();
        }
      }
    }
    function startGenerationStatusPoller() {
      if (generationStatusTimer !== null) return;
      generationStatusTimer = window.setInterval(() => {
        if (!componentActive) return;
        void loadStatus();
      }, 2e3);
    }
    function stopGenerationStatusPoller() {
      if (generationStatusTimer === null) return;
      window.clearInterval(generationStatusTimer);
      generationStatusTimer = null;
    }
    async function refreshAfterGenerationComplete() {
      if (!componentActive) return;
      await loadPreviewSources();
      if (!componentActive) return;
      if (previewMode.value === "backend") {
        await loadBackendPreview();
      } else {
        backendPreview.value = null;
      }
    }
    async function measureCustomLayout(layout) {
      if (!layout || !measureLayoutApiAvailable) return null;
      try {
        const resp = await props.api.post("plugin/YahahaCoverStudio/measure_custom_static_layout", { layout });
        if (resp?.code === 0 && resp.data) {
          return cloneLayout(resp.data);
        }
      } catch (error) {
        const status = error?.response?.status;
        if (status === 404) {
          measureLayoutApiAvailable = false;
          console.warn("measure_custom_static_layout is unavailable on current backend, fallback to frontend layout preview");
          return null;
        }
        console.error("measureCustomLayout failed", error);
      }
      return null;
    }
    function mergeMeasuredLayout(baseLayout, measuredLayout) {
      const nextLayout = cloneLayout(baseLayout);
      if (measuredLayout?.computed) {
        nextLayout.computed = cloneLayout(measuredLayout).computed;
      } else {
        delete nextLayout.computed;
      }
      return nextLayout;
    }
    function scheduleMeasureCustomLayout(layout) {
      if (controlsLocked.value) return;
      measureLayoutRequestToken += 1;
      if (!layout) return;
      const requestToken = measureLayoutRequestToken;
      const snapshot = cloneLayout(layout);
      const templateId = activeEditorTemplateId.value;
      if (measureLayoutTimer !== null) {
        window.clearTimeout(measureLayoutTimer);
      }
      measureLayoutTimer = window.setTimeout(() => {
        measureLayoutTimer = null;
        void (async () => {
          const measured = await measureCustomLayout(snapshot);
          if (!measured) return;
          if (requestToken !== measureLayoutRequestToken) return;
          if (!customStaticLayout.value) return;
          if (activeEditorTemplateId.value !== templateId) return;
          const mergedLayout = mergeMeasuredLayout(customStaticLayout.value, measured);
          customStaticLayout.value = mergedLayout;
          syncLayoutToTemplate(templateId, mergedLayout);
        })();
      }, 180);
    }
    function hydrateEditorForCurrentStyle() {
      if (styleVariant.value !== "static") {
        activeEditorTemplateId.value = null;
        customStaticLayout.value = null;
        return;
      }
      if (isPresetStaticStyle(coverStyleBase.value)) {
        const presetTemplate = ensurePresetTemplate(coverStyleBase.value);
        setEditorTemplate(presetTemplate.id);
        scheduleMeasureCustomLayout(customStaticLayout.value);
        return;
      }
      if (coverStyleBase.value === "custom_static") {
        ensureCustomTemplateInitialized();
        scheduleMeasureCustomLayout(customStaticLayout.value);
        return;
      }
      activeEditorTemplateId.value = null;
      customStaticLayout.value = null;
    }
    const showInlineLayoutEditor = computed(
      () => styleVariant.value === "static" && (isPresetStaticStyle(coverStyleBase.value) || coverStyleBase.value === "custom_static")
    );
    const showPresetRenderStyleSelector = computed(
      () => showInlineLayoutEditor.value && isPresetStaticStyle(coverStyleBase.value)
    );
    const effectiveStaticRenderMode = computed(
      () => coverStyleBase.value === "custom_static" ? "layout" : presetStaticRenderMode.value
    );
    const useInlineLayoutForBackend = computed(
      () => showInlineLayoutEditor.value && effectiveStaticRenderMode.value === "layout" && !!customStaticLayout.value
    );
    const effectivePreviewSource = computed(() => {
      const source = previewSource.value;
      if (!source) return null;
      const shouldUseCurrentLayout = showInlineLayoutEditor.value && !!customStaticLayout.value && effectiveStaticRenderMode.value === "layout";
      return {
        ...source,
        cover_style_base: coverStyleBase.value,
        cover_style_variant: coverStyleBase.value === "custom_static" ? "static" : styleVariant.value,
        custom_static_layout: shouldUseCurrentLayout ? cloneLayout(customStaticLayout.value) : null
      };
    });
    const showMainPreviewSkeleton = computed(() => !effectivePreviewSource.value);
    const showStylePreviewSkeleton = computed(() => !previewSource.value);
    function getCustomCardLayout(templateId) {
      const template = templateId ? getTemplateById(templateId) : selectedCustomTemplateId.value ? getTemplateById(selectedCustomTemplateId.value) : getUserCustomTemplates()[0] || null;
      if (template && !isSystemTemplate(template)) {
        return cloneLayout(template.layout);
      }
      if (coverStyleBase.value === "custom_static" && customStaticLayout.value) {
        return cloneLayout(customStaticLayout.value);
      }
      return previewSource.value?.custom_static_layout ? cloneLayout(previewSource.value.custom_static_layout) : null;
    }
    function getPresetCardLayout(baseStyle) {
      if (!isPresetStaticStyle(baseStyle)) return null;
      const template = getTemplateById(`__preset_${baseStyle}`);
      return template ? cloneLayout(template.layout) : cloneLayout(getStyleDefaultLayout(baseStyle));
    }
    function buildSchemePreviewSource(item) {
      const source = previewSource.value;
      if (!source) return null;
      const layout = item.kind === "custom" ? getCustomCardLayout(item.templateId) : getPresetCardLayout(item.baseStyle);
      return {
        ...source,
        cover_style_base: item.baseStyle,
        cover_style_variant: item.kind === "custom" ? "static" : styleVariant.value,
        custom_static_layout: layout ? cloneLayout(layout) : null
      };
    }
    function isSchemeItemActive(item) {
      if (item.kind === "preset") {
        return coverStyleBase.value === item.baseStyle;
      }
      return coverStyleBase.value === "custom_static" && selectedCustomTemplateId.value === item.templateId;
    }
    async function openStyleEditor(baseStyle, variant = styleVariant.value) {
      if (shouldBlockLockedAction()) return;
      if (coverStyleBase.value !== baseStyle) {
        await setCoverStyle(baseStyle, variant);
      } else if (styleVariant.value !== variant) {
        await setCoverStyle(baseStyle, variant);
      }
      hydrateEditorForCurrentStyle();
      if (isPresetStaticStyle(baseStyle)) {
        presetStaticRenderMode.value = "layout";
      }
      const wasEditingLayout = isEditingLayout.value;
      isEditingLayout.value = true;
      if (!wasEditingLayout) {
        await scrollEditorIntoView();
      }
    }
    async function selectSchemeItem(item) {
      if (shouldBlockLockedAction()) return;
      animatedSettingsPanelOpen.value = false;
      if (item.kind === "custom") {
        await persistCurrentEditorState();
        setSelectedCustomTemplate(item.templateId);
        await setCoverStyle("custom_static");
        return;
      }
      await setCoverStyle(item.baseStyle);
    }
    async function editSchemeItem(item) {
      if (shouldBlockLockedAction()) return;
      if (item.kind === "custom") {
        await selectSchemeItem(item);
        hydrateEditorForCurrentStyle();
        const wasEditingLayout = isEditingLayout.value;
        isEditingLayout.value = true;
        if (!wasEditingLayout) {
          await scrollEditorIntoView();
        }
        return;
      }
      await openStyleEditor(item.baseStyle, "static");
    }
    function getAnimatedStyleKey(baseStyle) {
      if (baseStyle === "static_2") return "animated_2";
      if (baseStyle === "static_3") return "animated_3";
      if (baseStyle === "static_4") return "animated_4";
      return "animated_1";
    }
    function clampNumber(value, min, max, fallback) {
      const parsed = Number(value);
      if (!Number.isFinite(parsed)) return fallback;
      return Math.max(min, Math.min(max, Math.round(parsed)));
    }
    function clampFloat(value, min, max, fallback) {
      const parsed = Number(value);
      if (!Number.isFinite(parsed)) return fallback;
      return Math.max(min, Math.min(max, parsed));
    }
    function syncAnimatedSettings(data, baseStyle = animatedSettingsBaseStyle.value) {
      if (data?.animated_settings) {
        animatedSettingsByStyle.value = {
          ...animatedSettingsByStyle.value,
          ...data.animated_settings
        };
      }
      const styleKey = getAnimatedStyleKey(baseStyle);
      const styleSettings = animatedSettingsByStyle.value[styleKey];
      const source = styleSettings || data;
      if (!source) return;
      animatedSettings.animationDuration = clampNumber(source.animation_duration ?? animatedSettings.animationDuration, 1, 60, 8);
      animatedSettings.animationFps = clampNumber(source.animation_fps ?? animatedSettings.animationFps, 1, 60, 24);
      animatedSettings.animationFormat = source.animation_format === "gif" ? "gif" : "apng";
      animatedSettings.animationScroll = ["down", "up", "alternate", "alternate_reverse"].includes(String(source.animation_scroll)) ? source.animation_scroll : "alternate";
      animatedSettings.animationReduceColors = ["off", "medium", "strong"].includes(String(source.animation_reduce_colors)) ? source.animation_reduce_colors : "medium";
      animatedSettings.animated2ImageCount = clampNumber(source.animated_2_image_count ?? animatedSettings.animated2ImageCount, 3, 60, 6);
      animatedSettings.animated2DepartureType = ["fly", "fade", "crossfade"].includes(String(source.animated_2_departure_type)) ? source.animated_2_departure_type : "fly";
      animatedSettings.mainTitleFontPreset = String(source.main_title_font_preset || animatedSettings.mainTitleFontPreset || "chaohei");
      animatedSettings.subtitleFontPreset = String(source.subtitle_font_preset || animatedSettings.subtitleFontPreset || "EmblemaOne");
      animatedSettings.customTextFontPreset = String(source.custom_text_font_preset || animatedSettings.customTextFontPreset || animatedSettings.subtitleFontPreset || "EmblemaOne");
      animatedSettings.mainTitleFontSize = clampNumber(source.main_title_font_size ?? animatedSettings.mainTitleFontSize, 24, 320, 170);
      animatedSettings.subtitleFontSize = clampNumber(source.subtitle_font_size ?? animatedSettings.subtitleFontSize, 12, 220, 75);
      animatedSettings.blurSize = clampNumber(source.blur_size ?? animatedSettings.blurSize, 0, 100, 50);
      animatedSettings.colorRatio = clampFloat(source.color_ratio ?? animatedSettings.colorRatio, 0, 1, 0.8);
      animatedSettings.titleScale = clampFloat(source.title_scale ?? animatedSettings.titleScale, 0.2, 3, 1);
    }
    function syncRenderOptions(data) {
      if (!data) return;
      sourceSortLocked.value = Boolean(data.lock_latest_sort);
      posterSource.value = data.poster_source === "poster" || data.use_primary ? "poster" : "backdrop";
      sourceSortBy.value = ["Random", "DateCreated", "PremiereDate"].includes(String(data.sort_by)) ? data.sort_by : "Random";
      imageCountMode.value = data.image_count_mode === "fixed" ? "fixed" : "auto";
      imageCount.value = clampNumber(data.image_count ?? imageCount.value, 1, 60, 9);
      autoImageCount.value = clampNumber(data.auto_image_count ?? autoImageCount.value, 1, 60, 9);
      staticResolution.value = ["480p", "720p", "1080p"].includes(String(data.resolution)) ? String(data.resolution) : "480p";
      animationResolution.value = typeof data.animation_resolution === "string" && data.animation_resolution.trim() ? data.animation_resolution.trim() : "320x180";
    }
    async function saveRenderOptions() {
      if (shouldBlockLockedAction()) return;
      imageCount.value = clampNumber(imageCount.value, 1, 60, 9);
      renderOptionsSaving.value = true;
      try {
        const payload = {
          poster_source: posterSource.value,
          sort_by: sourceSortBy.value,
          image_count_mode: imageCountMode.value,
          image_count: imageCount.value,
          resolution: staticResolution.value
        };
        const resp = await props.api.post("plugin/YahahaCoverStudio/set_render_options", payload);
        if (resp && resp.code !== 0) {
          throw new Error(resp.msg || "save render options failed");
        }
        syncRenderOptions(resp?.data || payload);
        showEditorSaveStatus("已自动保存");
        backendPreview.value = null;
        await loadPreviewSources();
        if (previewMode.value === "backend") {
          await loadBackendPreview();
        }
      } catch (e) {
        console.error("save render options failed", e);
      } finally {
        renderOptionsSaving.value = false;
      }
    }
    async function openAnimatedSettings(item) {
      if (shouldBlockLockedAction()) return;
      if (item.kind !== "preset") return;
      animatedSettingsBaseStyle.value = item.baseStyle;
      syncAnimatedSettings(null, item.baseStyle);
      animatedSettingsPanelOpen.value = true;
      if (coverStyleBase.value !== item.baseStyle || styleVariant.value !== "animated") {
        await setCoverStyle(item.baseStyle, "animated");
      }
      syncAnimatedSettings(null, item.baseStyle);
    }
    async function saveAnimatedSettings() {
      if (shouldBlockLockedAction()) return;
      animatedSettingsSaving.value = true;
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
          title_scale: animatedSettings.titleScale
        };
        const resp = await props.api.post("plugin/YahahaCoverStudio/set_animated_settings", payload);
        if (resp && resp.code !== 0) {
          throw new Error(resp.msg || "save animated settings failed");
        }
        syncAnimatedSettings(resp?.data || payload, animatedSettingsBaseStyle.value);
        showEditorSaveStatus("已保存");
        backendPreview.value = null;
        await loadPreviewSources();
      } catch (e) {
        console.error("save animated settings failed", e);
      } finally {
        animatedSettingsSaving.value = false;
      }
    }
    computed(
      () => showInlineLayoutEditor.value && previewMode.value === "backend"
    );
    function resolveRequestedCoverStyle(baseStyle = coverStyleBase.value, variant = styleVariant.value) {
      if (baseStyle === "custom_static") return "custom_static";
      const suffix = baseStyle.split("_")[1] || "1";
      return variant === "animated" ? `animated_${suffix}` : `static_${suffix}`;
    }
    const previewModeLabel = computed(() => {
      if (showInlineLayoutEditor.value) {
        return effectiveStaticRenderMode.value === "layout" ? "可编辑画布预览" : "静态风格模拟预览";
      }
      return "前端模拟预览";
    });
    computed(() => {
      if (showInlineLayoutEditor.value) {
        return "静态风格已统一成可编辑画布，拖拽图层或在下方属性面板直接修改参数。";
      }
      return "仅用于快速调参，结果为浏览器模拟。";
    });
    computed(() => {
      if (coverStyleBase.value === "custom_static") {
        return "当前为自定义风格画布，图层参数直接在画布和下方属性面板中修改。";
      }
      return useInlineLayoutForBackend.value ? "当前预设风格已切到“当前布局”渲染；修改后仍可一键恢复回预设默认值。" : "当前预设风格仍按原始风格渲染；切到“当前布局”后才会按画布参数生成。";
    });
    computed(() => {
      if (coverStyleBase.value === "custom_static") {
        return "自定义风格继续保留方案能力，但不再单独拆一个页面；当前布局直接在本页保存和管理。";
      }
      return useInlineLayoutForBackend.value ? "当前保存的是该预设对应的可编辑布局，后端预览和生成都会按当前画布执行；恢复默认会回到该预设的初始布局。" : "当前保存的是该预设对应的可编辑布局；后端仍按原始风格生成，切到“当前布局”后才会使用这些参数。";
    });
    const currentStyleLabel = computed(() => {
      if (coverStyleBase.value === "custom_static") {
        return getTemplateById(selectedCustomTemplateId.value)?.name || "自定义方案";
      }
      const presetId = `__preset_${coverStyleBase.value}`;
      return isPresetStaticStyle(coverStyleBase.value) ? getPresetSchemeTitle(coverStyleBase.value, getTemplateById(presetId)) : getStyleTitle(coverStyleBase.value);
    });
    const currentVariantLabel = computed(() => styleVariant.value === "static" ? "静态" : "动态");
    const generationProgressLabel = computed(() => {
      if (generationTotal.value > 0) return `正在生成 ${generationCurrent.value || 0}/${generationTotal.value}`;
      return generationLabel.value || "正在生成";
    });
    const generationProgressPercent = computed(() => {
      if (generationTotal.value > 0) {
        const raw = Math.round(Math.max(0, generationCurrent.value || 0) / generationTotal.value * 100);
        return Math.max(0, Math.min(100, raw));
      }
      return isGenerating.value ? 12 : 0;
    });
    const runButtonProgressStyle = computed(() => ({
      "--yh-run-progress": `${generationProgressPercent.value}%`
    }));
    computed(
      () => isGenerating.value ? generationProgressLabel.value : "执行"
    );
    computed(
      () => isGenerating.value ? "mdi-stop-circle-outline" : "mdi-play-circle-outline"
    );
    computed(() => isGenerating.value ? "error" : "primary");
    const resetButtonLabel = computed(
      () => isPresetStaticStyle(coverStyleBase.value) ? "恢复预设默认" : "恢复基础默认"
    );
    const animatedFormatItems = [
      { title: "APNG", value: "apng" },
      { title: "GIF", value: "gif" }
    ];
    const dynamicFontItems = computed(() => [
      ...BUILTIN_FONT_ITEMS,
      ...customFontItems.value.map((item) => ({ title: `自定义 ${item.title}`, value: item.value }))
    ]);
    const animatedColorReduceItems = [
      { title: "关闭（保真优先）", value: "off" },
      { title: "中等压缩", value: "medium" },
      { title: "强压缩（体积最小）", value: "strong" }
    ];
    const animatedScrollItems = [
      { title: "向下", value: "down" },
      { title: "向上", value: "up" },
      { title: "交替（两边下/中间上）", value: "alternate" },
      { title: "交替反向（两边上/中间下）", value: "alternate_reverse" }
    ];
    const animatedDepartureItems = [
      { title: "旋转-飞出", value: "fly" },
      { title: "旋转-渐隐", value: "fade" },
      { title: "渐变", value: "crossfade" }
    ];
    const animatedSettingsTitle = computed(() => {
      const index = animatedSettingsBaseStyle.value.split("_")[1] || "1";
      return `动态方案 ${index} 配置`;
    });
    const showAnimatedImageCountSetting = computed(
      () => ["static_1", "static_2", "static_4"].includes(animatedSettingsBaseStyle.value)
    );
    const showAnimatedDepartureSetting = computed(() => animatedSettingsBaseStyle.value === "static_1");
    const showAnimatedScrollSetting = computed(() => animatedSettingsBaseStyle.value === "static_3");
    const animatedResolutionLabel = computed(() => animationResolution.value || "320x180");
    computed(() => previewSource.value?.titles || { zh: "", en: "" });
    const sourceModeLabel = computed(() => {
      const mode = previewSource.value?.source_mode;
      if (mode === "custom") return "自定义图片目录";
      if (mode === "cache") return "数据目录缓存海报";
      if (mode === "media_server") return "媒体服务器";
      return "未知";
    });
    computed(() => `${autoImageCount.value || activeImageCount.value || 1} 张`);
    computed(() => previewSource.value?.server || "--");
    computed(() => previewSource.value?.library || "--");
    const activeImageCount = computed(() => previewSource.value?.images?.length || 0);
    const historySortItems = [
      { title: "最新优先", value: "newest" },
      { title: "最早优先", value: "oldest" },
      { title: "名称排序", value: "name" }
    ];
    const sortedHistory = computed(() => {
      const items = [...history.value];
      if (historySortMode.value === "oldest") {
        return items.sort((a, b) => Number(a.mtime_ts || 0) - Number(b.mtime_ts || 0));
      }
      if (historySortMode.value === "name") {
        return items.sort((a, b) => (a.name || "").localeCompare(b.name || "", "zh-Hans-CN"));
      }
      return items.sort((a, b) => Number(b.mtime_ts || 0) - Number(a.mtime_ts || 0));
    });
    const groupedHistory = computed(() => {
      const groups = /* @__PURE__ */ new Map();
      for (const item of sortedHistory.value) {
        const key = historyGroupMode.value === "library" ? item.library || "未识别媒体库" : item.batch_id || item.date || "legacy";
        const title = historyGroupMode.value === "library" ? item.library || "未识别媒体库" : formatTimelineTime(item.created_at || item.mtime || item.date || "");
        if (!groups.has(key)) {
          groups.set(key, { key, title, items: [] });
        }
        groups.get(key)?.items.push(item);
      }
      return Array.from(groups.values());
    });
    let timeRecordObserver = null;
    let timeRecordClickLockUntil = 0;
    let timeMachineFrame = 0;
    function updateTimeMachineDepth() {
      historyStackLimit.value = isMobileViewport() ? 3 : 5;
      if (historyGroupMode.value !== "time-machine" || pageTab.value !== "history-tab") return;
      const center = window.innerHeight / 2;
      document.querySelectorAll(".mcr-history-group--time-machine").forEach((element) => {
        const rect = element.getBoundingClientRect();
        const distance = Math.min(1, Math.abs(rect.top + rect.height / 2 - center) / Math.max(center, 1));
        element.style.setProperty("--mcr-time-scale", String(1 - distance * 0.06));
        element.style.setProperty("--mcr-time-opacity", String(1 - distance * 0.38));
        element.style.setProperty("--mcr-time-shift", `${Math.round(distance * 10)}px`);
      });
    }
    function scheduleTimeMachineDepth() {
      if (timeMachineFrame) return;
      timeMachineFrame = window.requestAnimationFrame(() => {
        timeMachineFrame = 0;
        updateTimeMachineDepth();
      });
    }
    function observeTimeRecords() {
      timeRecordObserver?.disconnect();
      if (historyGroupMode.value !== "time-machine" || pageTab.value !== "history-tab") return;
      const elements = groupedHistory.value.map((group) => document.getElementById(`time-record-${group.key}`)).filter((item) => Boolean(item));
      if (!elements.length) return;
      activeTimeRecordId.value ||= groupedHistory.value[0]?.key || "";
      timeRecordObserver = new IntersectionObserver((entries) => {
        if (Date.now() < timeRecordClickLockUntil) return;
        if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 3) {
          activeTimeRecordId.value = groupedHistory.value.at(-1)?.key || activeTimeRecordId.value;
          return;
        }
        const center = window.innerHeight / 2;
        const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => Math.abs(a.boundingClientRect.top + a.boundingClientRect.height / 2 - center) - Math.abs(b.boundingClientRect.top + b.boundingClientRect.height / 2 - center));
        if (visible[0]?.target.id) activeTimeRecordId.value = visible[0].target.id.replace("time-record-", "");
      }, { rootMargin: "-32% 0px -32% 0px", threshold: [0, 0.1, 0.4] });
      elements.forEach((element) => timeRecordObserver?.observe(element));
    }
    watch([historyGroupMode, pageTab, groupedHistory], () => void nextTick(observeTimeRecords));
    watch([historyGroupMode, pageTab, groupedHistory], () => void nextTick(scheduleTimeMachineDepth));
    function scrollToTimeRecord(id) {
      timeRecordClickLockUntil = Date.now() + 1200;
      activeTimeRecordId.value = id;
      document.getElementById(`time-record-${id}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    function openHistorySnapshot(group) {
      const timestamp = group.items[0]?.created_at || group.items[0]?.mtime || group.items[0]?.date || "";
      selectedHistorySnapshot.value = { ...group, fullTitle: formatDateTime(timestamp) };
      historySnapshotDialog.value = true;
    }
    function closeHistorySnapshot() {
      historySnapshotDialog.value = false;
      selectedHistoryPaths.value = [];
    }
    function applySelectedHistorySnapshot() {
      if (!selectedHistorySnapshot.value) return;
      void restoreHistoryBatch(selectedHistorySnapshot.value.key, selectedHistorySnapshot.value.title);
    }
    function timeMachineCoverStyle(groupKey, index) {
      let seed = 0;
      for (const char of groupKey) seed = seed * 31 + char.charCodeAt(0) >>> 0;
      const offsets = [0, 36, 76, 118, 160];
      const rotations = [-1.4, 1.1, -0.6, 1.8, -1];
      const vertical = [2, -5, 6, -2, 4];
      const variant = (seed + index * 7) % 5;
      return {
        "--mcr-stack-x": `${offsets[index] || offsets.at(-1)}px`,
        "--mcr-stack-hover-x": `${Math.round((offsets[index] || offsets.at(-1) || 0) * 1.22)}px`,
        "--mcr-stack-y": `${vertical[variant]}px`,
        "--mcr-stack-r": `${rotations[variant]}deg`,
        "--mcr-stack-z": String(20 - index)
      };
    }
    async function restoreHistoryBatch(batchId, label = "") {
      if (!batchId || restoringBatchId.value) return;
      pendingHistoryRestore.value = { batchId, label };
      restoreConfirmDialog.value = true;
    }
    async function executeHistoryRestore() {
      const pending = pendingHistoryRestore.value;
      if (!pending || restoringBatchId.value) return;
      const { batchId } = pending;
      restoringBatchId.value = batchId;
      try {
        const resp = await props.api.post("plugin/YahahaCoverStudio/restore_history_batch", { batch_id: batchId });
        if (!resp || resp.code !== 0) throw new Error(resp?.msg || "恢复失败");
        restoreConfirmDialog.value = false;
        showEditorSaveStatus(`已回到此时：成功 ${resp.data?.restored || 0} 个，跳过 ${resp.data?.skipped || 0} 个，失败 ${resp.data?.failed || 0} 个`);
      } catch (error) {
        showEditorSaveStatus(error instanceof Error ? error.message : "恢复失败");
      } finally {
        restoringBatchId.value = "";
      }
    }
    const allHistorySelected = computed(
      () => history.value.length > 0 && selectedHistoryPaths.value.length === history.value.length
    );
    computed(
      () => useInlineLayoutForBackend.value ? "当前画布继续保持可编辑，下方结果按当前布局的后端真实链路返回。" : "当前画布继续保持可编辑，下方结果按当前所选原始风格的后端真实链路返回。"
    );
    computed(
      () => useInlineLayoutForBackend.value ? "按当前布局渲染" : "按原始风格渲染"
    );
    function getPersistedCustomTemplateId(templates) {
      const userTemplates = getUserCustomTemplates(templates);
      if (!userTemplates.length) return "";
      if (selectedCustomTemplateId.value && userTemplates.some((tpl) => tpl.id === selectedCustomTemplateId.value)) {
        return selectedCustomTemplateId.value;
      }
      return userTemplates[0]?.id || "";
    }
    function buildPersistPayload() {
      const templates = customTemplates.value.map((tpl) => {
        if (activeEditorTemplateId.value && tpl.id === activeEditorTemplateId.value && customStaticLayout.value) {
          return {
            ...tpl,
            layout: cloneLayout(customStaticLayout.value)
          };
        }
        return {
          ...tpl,
          layout: cloneLayout(tpl.layout)
        };
      });
      const normalizedTemplates = normalizeTemplateList(templates);
      const persistedCustomTemplateId = getPersistedCustomTemplateId(normalizedTemplates);
      const persistedCustomTemplate = persistedCustomTemplateId ? normalizedTemplates.find((tpl) => tpl.id === persistedCustomTemplateId) || null : null;
      return {
        active_id: persistedCustomTemplateId,
        layout: persistedCustomTemplate ? cloneLayout(persistedCustomTemplate.layout) : null,
        templates: normalizedTemplates
      };
    }
    async function persistCustomLayoutState() {
      if (isGenerating.value) return;
      layoutPersisting.value = true;
      const currentEditorId = activeEditorTemplateId.value;
      cancelPendingAutoSave();
      cancelPendingLayoutMeasure();
      lastCustomLayoutPersistAt = Date.now();
      const savedLayoutSnapshot = customStaticLayout.value ? cloneLayout(customStaticLayout.value) : null;
      const payload = buildPersistPayload();
      const localTemplates = normalizeTemplateList(payload.templates.map((tpl) => currentEditorId && savedLayoutSnapshot && tpl.id === currentEditorId ? { ...tpl, layout: cloneLayout(savedLayoutSnapshot) } : tpl));
      const localActiveId = payload.active_id;
      customTemplates.value = localTemplates;
      if (currentEditorId && savedLayoutSnapshot) {
        customStaticLayout.value = cloneLayout(savedLayoutSnapshot);
        syncLayoutToTemplate(currentEditorId, savedLayoutSnapshot);
      }
      try {
        const resp = await props.api.post("plugin/YahahaCoverStudio/set_custom_static_layout", payload);
        if (resp && resp.code !== 0) {
          throw new Error(resp.msg || "save failed");
        }
        const backendTemplates = normalizeTemplateList(resp?.data?.custom_static_layouts || []);
        const backendActiveId = resp?.data?.custom_static_active_id || localActiveId;
        const nextTemplates = backendTemplates.length ? backendTemplates : localTemplates;
        applyCustomTemplateState(
          nextTemplates,
          backendActiveId
        );
        const backendEditorTemplate = currentEditorId ? nextTemplates.find((tpl) => tpl.id === currentEditorId) : null;
        if (currentEditorId && backendEditorTemplate?.layout) {
          customStaticLayout.value = cloneLayout(backendEditorTemplate.layout);
          syncLayoutToTemplate(currentEditorId, backendEditorTemplate.layout);
          activeEditorTemplateId.value = currentEditorId;
        } else if (currentEditorId && savedLayoutSnapshot) {
          customStaticLayout.value = cloneLayout(savedLayoutSnapshot);
          syncLayoutToTemplate(currentEditorId, savedLayoutSnapshot);
          activeEditorTemplateId.value = currentEditorId;
        } else if (coverStyleBase.value === "custom_static" && selectedCustomTemplateId.value && getTemplateById(selectedCustomTemplateId.value)) {
          setEditorTemplate(selectedCustomTemplateId.value);
        }
      } catch (e) {
        console.error("persist custom layout failed", e);
      } finally {
        layoutPersisting.value = false;
      }
    }
    async function persistCurrentEditorState() {
      if (isGenerating.value) return;
      if (!showInlineLayoutEditor.value || !customStaticLayout.value || !activeEditorTemplateId.value) return;
      cancelPendingAutoSave();
      await persistCustomLayoutState();
    }
    async function restoreCurrentLayoutDefaults() {
      if (shouldBlockLockedAction()) return;
      const activeId = activeEditorTemplateId.value;
      if (!activeId) return;
      const activeTemplate = getTemplateById(activeId);
      const baseStyle = normalizeCoverStyleBase(
        activeTemplate?.baseStyle || (isPresetStaticStyle(coverStyleBase.value) ? coverStyleBase.value : "custom_static")
      );
      const nextLayout = cloneLayout(getStyleDefaultLayout(baseStyle));
      customStaticLayout.value = nextLayout;
      syncLayoutToTemplate(activeId, nextLayout);
      scheduleMeasureCustomLayout(nextLayout);
      backendPreview.value = null;
      await persistCustomLayoutState();
    }
    watch(previewMode, async (nextMode) => {
      if (nextMode !== "frontend") {
        previewMode.value = "frontend";
      }
    });
    watch(presetStaticRenderMode, async (nextMode, prevMode) => {
      if (nextMode === prevMode) return;
      if (controlsLocked.value) {
        presetStaticRenderMode.value = prevMode;
        return;
      }
      backendPreview.value = null;
      if (previewMode.value === "backend" && showPresetRenderStyleSelector.value) {
        await loadBackendPreview();
      }
    });
    watch(selectedCustomTemplateId, (nextId, prevId) => {
      if (nextId === prevId) return;
      if (controlsLocked.value && !syncingBackendState) {
        selectedCustomTemplateId.value = prevId;
        return;
      }
      if (coverStyleBase.value !== "custom_static") return;
      if (!nextId) {
        activeEditorTemplateId.value = null;
        customStaticLayout.value = null;
        return;
      }
      setEditorTemplate(nextId);
      backendPreview.value = null;
    });
    watch(
      () => schemeListItems.value.length,
      () => {
        void normalizeSchemeListViewport();
      },
      { flush: "post" }
    );
    watch(editorAutoSaveEnabled, (enabled) => {
      if (typeof window !== "undefined") {
        window.localStorage.setItem(EDITOR_AUTO_SAVE_STORAGE_KEY, enabled ? "true" : "false");
      }
      if (!enabled) {
        cancelPendingAutoSave();
        autoSaveQueued = false;
        editorSaveStatus.value = "";
      }
    });
    async function createTemplateFromCurrent() {
      if (shouldBlockLockedAction()) return;
      await persistCurrentEditorState();
      const id = createLayoutId();
      const template = {
        id,
        name: getUniqueTemplateName(`自定义方案 ${getUserCustomTemplates().length + 1}`),
        layout: cloneLayout(customStaticLayout.value || getStyleDefaultLayout(coverStyleBase.value)),
        baseStyle: "custom_static"
      };
      customTemplates.value = [...customTemplates.value, template];
      setSelectedCustomTemplate(id);
      backendPreview.value = null;
      await setCoverStyle("custom_static");
      await persistCustomLayoutState();
    }
    async function renameSchemeItem(item) {
      if (shouldBlockLockedAction()) return;
      const active = resolveSchemeTemplate(item, true);
      if (!active) return;
      const newName = window.prompt("请输入方案名称", item.title || active.name);
      if (!newName) return;
      const trimmedName = newName.trim();
      if (!trimmedName) return;
      const uniqueName = getUniqueTemplateName(trimmedName, active.id);
      customTemplates.value = customTemplates.value.map(
        (tpl) => tpl.id === active.id ? { ...tpl, name: uniqueName } : tpl
      );
      await persistCustomLayoutState();
    }
    function buildTemplateExportPayload(active) {
      return {
        schema: "mcr-custom-static-template/v1",
        exported_at: (/* @__PURE__ */ new Date()).toISOString(),
        template: {
          ...active,
          layout: cloneLayout(active.layout)
        }
      };
    }
    function stringifyTemplateExport(active) {
      return JSON.stringify(buildTemplateExportPayload(active), null, 2);
    }
    function downloadTextFile(filename, text, type = "application/json") {
      const blob = new Blob([text], { type });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    }
    async function writeClipboardText(text) {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        return;
      }
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      textarea.style.top = "0";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      const copied = document.execCommand("copy");
      textarea.remove();
      if (!copied) {
        throw new Error("clipboard unavailable");
      }
    }
    function getTemplateExportFileName(template) {
      const safeName = String(template.name || "custom-layout").replace(/[\\/:*?"<>|]+/g, "-").replace(/\s+/g, "-").replace(/^-+|-+$/g, "");
      return `${safeName || "custom-layout"}.json`;
    }
    function exportSchemeItemToFile(item) {
      if (shouldBlockLockedAction()) return;
      const active = resolveSchemeTemplate(item);
      if (!active) return;
      downloadTextFile(getTemplateExportFileName(active), stringifyTemplateExport(active));
    }
    async function exportSchemeItemToClipboard(item) {
      if (shouldBlockLockedAction()) return;
      const active = resolveSchemeTemplate(item);
      if (!active) return;
      const text = stringifyTemplateExport(active);
      try {
        await writeClipboardText(text);
        showEditorSaveStatus("方案已复制");
      } catch (e) {
        console.error("copy custom template failed", e);
        window.prompt("剪切板不可用，请手动复制方案 JSON", text);
      }
    }
    function triggerImportTemplate() {
      if (shouldBlockLockedAction()) return;
      importTemplateInput.value?.click();
    }
    async function importTemplateFromRaw(raw, fallbackName) {
      const parsed = JSON.parse(raw);
      const imported = parsed?.template || parsed;
      if (!imported?.layout?.layers || !Array.isArray(imported.layout.layers)) {
        throw new Error("invalid template file");
      }
      await persistCurrentEditorState();
      const id = createLayoutId();
      const importedName = String(imported.name || fallbackName || `导入方案 ${getUserCustomTemplates().length + 1}`);
      const template = {
        id,
        name: getUniqueTemplateName(importedName),
        layout: cloneLayout(imported.layout),
        baseStyle: "custom_static"
      };
      customTemplates.value = [...customTemplates.value, template];
      setSelectedCustomTemplate(id);
      backendPreview.value = null;
      await setCoverStyle("custom_static");
      await persistCustomLayoutState();
    }
    async function importTemplateFromClipboard() {
      if (shouldBlockLockedAction()) return;
      try {
        let raw = "";
        if (navigator.clipboard?.readText) {
          try {
            raw = await navigator.clipboard.readText();
          } catch (clipboardError) {
            console.warn("read clipboard failed, fallback to manual paste", clipboardError);
          }
        }
        if (!raw) {
          raw = window.prompt("粘贴方案 JSON") || "";
        }
        if (!raw.trim()) return;
        await importTemplateFromRaw(raw, `剪切板方案 ${getUserCustomTemplates().length + 1}`);
      } catch (e) {
        console.error("import custom template from clipboard failed", e);
      }
    }
    async function importTemplateFromFile(event) {
      if (shouldBlockLockedAction()) return;
      const input = event.target;
      const file = input.files?.[0];
      input.value = "";
      if (!file) return;
      try {
        const raw = await file.text();
        await importTemplateFromRaw(raw, file.name.replace(/\.json$/i, "") || `导入方案 ${getUserCustomTemplates().length + 1}`);
      } catch (e) {
        console.error("import custom template failed", e);
      }
    }
    async function deleteSchemeItem(item) {
      if (shouldBlockLockedAction()) return;
      if (item.kind !== "custom") return;
      const id = item.templateId;
      if (!id || isSystemTemplate(getTemplateById(id))) return;
      try {
        const resp = await props.api.post(`plugin/YahahaCoverStudio/delete_custom_static_template?id=${encodeURIComponent(id)}`);
        if (resp && resp.code !== 0) {
          throw new Error(resp.msg || "delete failed");
        }
        const incomingTemplates = normalizeTemplateList(resp?.data?.custom_static_layouts);
        applyCustomTemplateState(incomingTemplates, resp?.data?.custom_static_active_id || null);
        if (coverStyleBase.value === "custom_static" && !getUserCustomTemplates(customTemplates.value).length) {
          await setCoverStyle("static_1", "static");
        } else {
          hydrateEditorForCurrentStyle();
        }
        backendPreview.value = null;
        void normalizeSchemeListViewport();
      } catch (e) {
        console.error("delete custom template failed", e);
      }
    }
    function onLayoutUpdated(layoutValue) {
      if (shouldBlockLockedAction()) return;
      const nextLayout = cloneLayout(layoutValue);
      customStaticLayout.value = nextLayout;
      syncLayoutToTemplate(activeEditorTemplateId.value, nextLayout);
      schedulePreviewSourceReloadForLayout(nextLayout);
      scheduleMeasureCustomLayout(nextLayout);
      scheduleAutoSaveCustomLayout();
      backendPreview.value = null;
    }
    async function saveCustomLayoutNow() {
      if (shouldBlockLockedAction()) return;
      if (!showInlineLayoutEditor.value) return;
      if (!activeEditorTemplateId.value) {
        hydrateEditorForCurrentStyle();
      }
      if (!customStaticLayout.value) return;
      await persistCustomLayoutState();
      showEditorSaveStatus("已保存");
    }
    async function loadStatus() {
      if (statusLoadPromise) return statusLoadPromise;
      statusLoadPromise = loadStatusInner().finally(() => {
        statusLoadPromise = null;
      });
      return statusLoadPromise;
    }
    async function loadStatusInner() {
      statusLoading.value = true;
      try {
        const resp = await props.api.get("plugin/YahahaCoverStudio/status");
        if (!componentActive) return false;
        if (resp && resp.code === 0 && resp.data) {
          const data = resp.data;
          previewCacheContext.value = {
            mode: "plugin",
            servers: data.selected_servers || [],
            libraries: data.include_libraries || [],
            coversInput: data.covers_input || ""
          };
          const wasGenerating = isGenerating.value;
          const nextIsGenerating = Boolean(data.is_generating);
          setupWarnings.value = Array.isArray(data.warnings) ? data.warnings : [];
          pluginEnabled.value = Boolean(data.enabled);
          isGenerating.value = nextIsGenerating;
          generationCurrent.value = Number(data.generation_current || 0);
          generationTotal.value = Number(data.generation_total || 0);
          generationLabel.value = String(data.generation_label || "");
          statusLoaded.value = true;
          coverStyleBase.value = normalizeCoverStyleBase(data.cover_style_base);
          styleVariant.value = data.cover_style_variant === "animated" ? "animated" : "static";
          syncAnimatedSettings(data, coverStyleBase.value);
          syncRenderOptions(data);
          const shouldPreserveEditingLayout = isEditingLayout.value || lastCustomLayoutPersistAt > 0 && Date.now() - lastCustomLayoutPersistAt < 5e3;
          if (!nextIsGenerating && !shouldPreserveEditingLayout) {
            let incomingTemplates = normalizeTemplateList(data.custom_static_layouts);
            if (!incomingTemplates.length && data.custom_static_layout) {
              incomingTemplates = [
                {
                  id: createLayoutId(),
                  name: "自定义方案",
                  layout: cloneLayout(data.custom_static_layout),
                  baseStyle: "custom_static"
                }
              ];
            }
            syncingBackendState = true;
            try {
              applyCustomTemplateState(incomingTemplates, data.custom_static_active_id || null);
              hydrateEditorForCurrentStyle();
            } finally {
              syncingBackendState = false;
            }
          }
          if (isGenerating.value) {
            cancelPendingAutoSave();
            cancelPendingLayoutMeasure();
            cancelPendingPreviewSourceReload();
            autoSaveQueued = false;
            backendPreview.value = null;
            startGenerationStatusPoller();
          } else {
            stopGenerationStatusPoller();
          }
          if (wasGenerating && !isGenerating.value) {
            void refreshAfterGenerationComplete();
          }
          return true;
        } else if (resp && resp.code !== 0) {
          console.error("load status failed", resp.msg || resp);
        }
      } catch (e) {
        console.error("loadStatus failed", e);
      } finally {
        statusLoading.value = false;
      }
      return false;
    }
    function normalizeHistoryItems(items) {
      return items.map((item) => ({ ...item, src: item.src || item.url || "" }));
    }
    function previewRequestBaseKey() {
      return stableCacheSignature({
        ...previewCacheContext.value,
        posterSource: posterSource.value,
        sort: sourceSortBy.value,
        imageCountMode: imageCountMode.value
      });
    }
    async function loadHistory() {
      if (!history.value.length) {
        const cached = await getHistoryCache(HISTORY_CACHE_KEY);
        if (cached?.length) {
          history.value = normalizeHistoryItems(cached);
          showingCachedHistory.value = true;
        }
      }
      historyUpdating.value = true;
      historyLoading.value = true;
      try {
        const resp = await props.api.get("plugin/YahahaCoverStudio/history");
        if (resp && resp.code === 0 && Array.isArray(resp.data)) {
          history.value = normalizeHistoryItems(resp.data);
          showingCachedHistory.value = false;
          await setHistoryCache(HISTORY_CACHE_KEY, history.value);
          selectedHistoryPaths.value = selectedHistoryPaths.value.filter(
            (path) => resp.data?.some((item) => item.path === path)
          );
        } else if (resp && resp.code !== 0) {
          console.error("load history failed", resp.msg || resp);
        }
      } catch (e) {
        console.error("loadHistory failed", e);
      } finally {
        historyLoading.value = false;
        historyUpdating.value = false;
      }
    }
    async function loadPreviewSources(requiredItems, forceRefresh = false) {
      if (!componentActive) return false;
      if (isGenerating.value) {
        previewSourcesLoading.value = false;
        return false;
      }
      const capacity = Math.max(1, Number(requiredItems) || 9);
      const baseKey = previewRequestBaseKey();
      const requestId = ++previewSourceRequestId;
      if (!forceRefresh) {
        const cached = await getPreviewCache(baseKey, capacity);
        if (cached?.images?.length) {
          previewSource.value = cached;
          return true;
        }
      }
      previewSourcesLoading.value = !previewSource.value?.images?.length;
      try {
        const query = new URLSearchParams({ required_items: String(capacity) });
        if (forceRefresh) query.set("force_refresh", "true");
        const suffix = `?${query}`;
        const resp = await props.api.get(`plugin/YahahaCoverStudio/preview_sources${suffix}`);
        if (!componentActive) return false;
        if (requestId !== previewSourceRequestId) return true;
        if (resp?.code === 0) {
          if (resp.data?.images?.length) {
            previewSource.value = {
              ...resp.data,
              custom_static_layout: resp.data.custom_static_layout ? cloneLayout(resp.data.custom_static_layout) : resp.data.custom_static_layout
            };
            if (requestId !== previewSourceRequestId) return true;
            try {
              await setPreviewCache(baseKey, Math.max(capacity, previewSource.value.images.length), previewSource.value);
            } catch (cacheError) {
              console.warn("preview cache persistence failed", cacheError);
            }
          }
          return true;
        }
        if (resp) {
          console.error("load preview sources failed", resp.msg || resp);
        }
        return false;
      } catch (e) {
        console.error("loadPreviewSources failed", e);
        return false;
      } finally {
        if (componentActive) {
          if (requestId === previewSourceRequestId) previewSourcesLoading.value = false;
        }
      }
    }
    async function loadBackendPreview() {
      if (!componentActive) return;
      backendPreviewLoading.value = true;
      try {
        const payload = {
          style: coverStyleBase.value === "custom_static" ? "custom_static" : resolveRequestedCoverStyle()
        };
        if (showInlineLayoutEditor.value && customStaticLayout.value) {
          payload.layout = cloneLayout(customStaticLayout.value);
        }
        const resp = await props.api.post(
          "plugin/YahahaCoverStudio/preview",
          payload
        );
        if (!componentActive) return;
        if (resp && resp.code === 0 && resp.data?.src) {
          backendPreview.value = resp.data;
        } else {
          backendPreview.value = null;
          if (resp && resp.code !== 0) {
            console.error("load backend preview failed", resp.msg || resp);
          }
        }
      } catch (e) {
        backendPreview.value = null;
        console.error("loadBackendPreview failed", e);
      } finally {
        backendPreviewLoading.value = false;
      }
    }
    async function refreshCurrentPreview() {
      if (shouldBlockLockedAction()) return;
      refreshingPreview.value = true;
      try {
        try {
          await invalidatePreviewCache(previewRequestBaseKey());
        } catch (cacheError) {
          console.warn("preview cache invalidation failed", cacheError);
        }
        const refreshed = await loadPreviewSources(void 0, true);
        showEditorSaveStatus(refreshed ? "海报已刷新" : "刷新失败，继续使用当前海报");
        if (previewMode.value === "backend") {
          await loadBackendPreview();
        }
      } finally {
        refreshingPreview.value = false;
      }
    }
    async function setPageTab(tab) {
      if (shouldBlockLockedAction()) return;
      if (pageTab.value === "generate-tab" && tab !== "generate-tab") {
        await persistCurrentEditorState();
      }
      pageTab.value = tab;
      try {
        if (tab === "history-tab") {
          await loadHistory();
          return;
        }
        await loadStatus();
        if (isGenerating.value) return;
        await loadPreviewSources();
        if (previewMode.value === "backend") {
          await loadBackendPreview();
        }
      } catch (e) {
        console.error("set_page_tab failed", e);
      }
    }
    async function setCoverStyle(targetBase, targetVariant = styleVariant.value) {
      if (shouldBlockLockedAction()) return;
      styleUpdating.value = true;
      const previousBase = coverStyleBase.value;
      const previousVariant = styleVariant.value;
      try {
        await persistCurrentEditorState();
        if (targetBase === "custom_static") {
          ensureCustomTemplateInitialized();
          coverStyleBase.value = "custom_static";
          styleVariant.value = "static";
          await props.api.post("plugin/YahahaCoverStudio/set_cover_style?style=custom_static");
        } else {
          coverStyleBase.value = targetBase;
          styleVariant.value = targetVariant;
          const style = `${targetVariant}_${targetBase.split("_")[1]}`;
          await props.api.post(`plugin/YahahaCoverStudio/set_cover_style?style=${style}`);
        }
        showEditorSaveStatus("已自动保存");
        backendPreview.value = null;
        hydrateEditorForCurrentStyle();
      } catch (e) {
        coverStyleBase.value = previousBase;
        styleVariant.value = previousVariant;
        hydrateEditorForCurrentStyle();
        console.error("set_cover_style failed", e);
      } finally {
        styleUpdating.value = false;
      }
    }
    async function toggleStyleVariant() {
      if (shouldBlockLockedAction()) return;
      if (coverStyleBase.value === "custom_static") return;
      const previousVariant = styleVariant.value;
      const nextVariant = previousVariant === "static" ? "animated" : "static";
      animatedSettingsPanelOpen.value = false;
      styleUpdating.value = true;
      try {
        await persistCurrentEditorState();
        styleVariant.value = nextVariant;
        await props.api.post("plugin/YahahaCoverStudio/toggle_style_variant");
        showEditorSaveStatus("已自动保存");
        backendPreview.value = null;
        hydrateEditorForCurrentStyle();
      } catch (e) {
        styleVariant.value = previousVariant;
        hydrateEditorForCurrentStyle();
        console.error("toggle_style_variant failed", e);
      } finally {
        styleUpdating.value = false;
      }
    }
    function onModeSwitchClick() {
      if (shouldBlockLockedAction()) return;
      if (coverStyleBase.value === "custom_static") return;
      modeSwitchPulse.value = false;
      window.requestAnimationFrame(() => {
        modeSwitchPulse.value = true;
        window.setTimeout(() => {
          modeSwitchPulse.value = false;
        }, 360);
      });
      void toggleStyleVariant();
    }
    async function startGeneration() {
      if (!statusLoaded.value || isGenerating.value) return;
      generatingNow.value = true;
      try {
        const targetStyle = coverStyleBase.value === "custom_static" ? "custom_static" : resolveRequestedCoverStyle();
        const endpoint = `plugin/YahahaCoverStudio/start_generation?style=${encodeURIComponent(targetStyle)}`;
        if (showInlineLayoutEditor.value) {
          await persistCurrentEditorState();
        }
        cancelPendingAutoSave();
        cancelPendingLayoutMeasure();
        cancelPendingPreviewSourceReload();
        const resp = await props.api.post(endpoint);
        if (resp && resp.code !== 0) {
          throw new Error(resp.msg || "start_generation failed");
        }
        isGenerating.value = true;
        generationCurrent.value = 0;
        generationTotal.value = 0;
        generationLabel.value = "准备生成";
        incrementDonationExecutionCount();
        startGenerationStatusPoller();
        await loadStatus();
        emit("action");
      } catch (e) {
        console.error("start_generation failed", e);
      } finally {
        generatingNow.value = false;
      }
    }
    async function stopGeneration() {
      generatingNow.value = true;
      try {
        const resp = await props.api.post(
          "plugin/YahahaCoverStudio/stop_generation"
        );
        if (resp && resp.code !== 0) {
          throw new Error(resp.msg || "stop_generation failed");
        }
        await loadStatus();
      } catch (e) {
        console.error("stop_generation failed", e);
      } finally {
        generatingNow.value = false;
      }
    }
    async function handleGenerateAction() {
      if (!statusLoaded.value) {
        await loadStatus();
        return;
      }
      if (isGenerating.value) {
        await stopGeneration();
        return;
      }
      await startGeneration();
    }
    function toggleHistorySelection(item) {
      if (shouldBlockLockedAction()) return;
      if (selectedHistoryPaths.value.includes(item.path)) {
        selectedHistoryPaths.value = selectedHistoryPaths.value.filter((path) => path !== item.path);
        return;
      }
      selectedHistoryPaths.value = [...selectedHistoryPaths.value, item.path];
    }
    function toggleSelectAllHistory() {
      if (shouldBlockLockedAction()) return;
      selectedHistoryPaths.value = allHistorySelected.value ? [] : history.value.map((item) => item.path);
    }
    async function deleteSelectedCovers() {
      if (shouldBlockLockedAction()) return;
      const paths = [...selectedHistoryPaths.value];
      if (!paths.length) return;
      try {
        const resp = await props.api.post(
          "plugin/YahahaCoverStudio/delete_saved_covers",
          { files: paths }
        );
        if (resp && resp.code !== 0) {
          throw new Error(resp.msg || "delete selected covers failed");
        }
        history.value = history.value.filter((item) => !paths.includes(item.path));
        void setHistoryCache(HISTORY_CACHE_KEY, history.value);
        selectedHistoryPaths.value = [];
      } catch (e) {
        console.error("delete selected covers failed", e);
      }
    }
    function downloadBinaryPayload(payload, fallbackName) {
      if (!payload?.b64) {
        throw new Error("download payload missing");
      }
      const binary = window.atob(payload.b64);
      const bytes = new Uint8Array(binary.length);
      for (let index = 0; index < binary.length; index += 1) {
        bytes[index] = binary.charCodeAt(index);
      }
      const blob = new Blob([bytes], { type: payload.mime || "application/octet-stream" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const scrollX = window.scrollX;
      const scrollY = window.scrollY;
      anchor.href = url;
      anchor.download = payload.name || fallbackName;
      anchor.rel = "noopener";
      anchor.tabIndex = -1;
      anchor.style.position = "fixed";
      anchor.style.left = "-9999px";
      anchor.style.top = "0";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      window.requestAnimationFrame(() => {
        window.scrollTo(scrollX, scrollY);
      });
    }
    function confirmRecentDownload(paths) {
      const key = [...paths].sort().join("|");
      const now = Date.now();
      const last = recentDownloadRegistry.get(key) || 0;
      if (last && now - last < 3 * 60 * 1e3) {
        const confirmed = window.confirm("相同内容短时间内已经下载过，是否再次下载？");
        if (!confirmed) return false;
      }
      recentDownloadRegistry.set(key, now);
      return true;
    }
    async function fetchCoverPayload(path) {
      const resp = await props.api.get(`plugin/YahahaCoverStudio/download_saved_cover?file=${encodeURIComponent(path)}`);
      if (!resp || resp.code !== 0 || !resp.data?.b64) {
        throw new Error(resp?.msg || "download failed");
      }
      return resp.data;
    }
    async function downloadSelectedCoversZip() {
      if (shouldBlockLockedAction()) return;
      const paths = [...selectedHistoryPaths.value];
      if (!paths.length) return;
      if (!confirmRecentDownload(paths)) return;
      try {
        const resp = await props.api.post("plugin/YahahaCoverStudio/download_saved_covers", { files: paths });
        if (!resp || resp.code !== 0 || !resp.data?.b64) {
          throw new Error(resp?.msg || "batch download failed");
        }
        downloadBinaryPayload(resp.data, "covers.zip");
      } catch (e) {
        console.error("download selected covers zip failed", e);
      }
    }
    async function downloadSelectedCoversDirect() {
      if (shouldBlockLockedAction()) return;
      const paths = [...selectedHistoryPaths.value];
      if (!paths.length) return;
      if (!confirmRecentDownload(paths)) return;
      const items = paths.map((path) => history.value.find((item) => item.path === path)).filter(Boolean);
      try {
        for (const item of items) {
          downloadBinaryPayload(await fetchCoverPayload(item.path), item.name || "cover");
          await new Promise((resolve) => window.setTimeout(resolve, 120));
        }
      } catch (e) {
        console.error("download selected covers direct failed", e);
      }
    }
    function notifySwitch() {
      if (shouldBlockLockedAction()) return;
      emit("switch");
    }
    function notifyClose() {
      emit("close");
    }
    function openDonationDialog() {
      donationView.value = donationAcknowledged.value ? "overview" : "support";
      donationDialog.value = true;
      if (!history.value.length && !historyLoading.value) {
        void loadHistory();
      }
    }
    function selectMoviePilotAvatar() {
      setDonationAvatarSource(donationAvatarSource.value === "mp" ? "developer" : "mp");
    }
    function setDonationAvatarSource(source) {
      donationAvatarSource.value = source;
      if (typeof window !== "undefined") {
        window.localStorage.setItem(DONATION_AVATAR_STORAGE_KEY, source);
      }
      if (source === "mp" && !moviePilotAvatarUrl.value) {
        void discoverMoviePilotAvatar();
      }
    }
    function acknowledgeDonation() {
      donationAcknowledged.value = true;
      donationView.value = "overview";
      if (typeof window !== "undefined") {
        window.localStorage.setItem(DONATION_ACK_STORAGE_KEY, "1");
      }
    }
    function incrementDonationExecutionCount() {
      donationExecutionCount.value += 1;
      if (typeof window !== "undefined") {
        window.localStorage.setItem(DONATION_RUN_COUNT_STORAGE_KEY, String(donationExecutionCount.value));
      }
    }
    function normalizeMoviePilotAvatarUrl(value) {
      const raw = typeof value === "string" ? value.trim() : "";
      if (!raw) return "";
      if (raw.startsWith("data:image/")) return raw;
      if (/^https?:\/\//i.test(raw)) return raw;
      if (raw.startsWith("//")) return `${window.location.protocol}${raw}`;
      if (raw.startsWith("/")) return raw;
      if (/^(api|static|assets|avatar|user|profile)\//i.test(raw)) return `/${raw}`;
      return "";
    }
    function findAvatarInPayload(payload, depth = 0) {
      if (!payload || depth > 5) return "";
      if (typeof payload === "string") {
        const normalized = normalizeMoviePilotAvatarUrl(payload);
        if (!normalized) return "";
        const lower = normalized.toLowerCase();
        if (lower.includes("wx_code") || lower.includes("qrcode") || lower.includes("qr-code")) return "";
        if (normalized.startsWith("data:image/") || /\.(png|jpe?g|webp|gif|svg)(\?|#|$)/i.test(normalized) || /(avatar|headimg|profile|portrait|face)/i.test(normalized)) {
          return normalized;
        }
        return "";
      }
      if (Array.isArray(payload)) {
        for (const item of payload) {
          const found = findAvatarInPayload(item, depth + 1);
          if (found) return found;
        }
        return "";
      }
      if (typeof payload === "object") {
        const record = payload;
        const preferredKeys = [
          "avatar",
          "avatarUrl",
          "avatar_url",
          "headimgurl",
          "headImgUrl",
          "photo",
          "picture",
          "portrait",
          "face",
          "icon",
          "image"
        ];
        for (const key of preferredKeys) {
          const found = findAvatarInPayload(record[key], depth + 1);
          if (found) return found;
        }
        for (const [key, value] of Object.entries(record)) {
          if (!/(user|profile|account|avatar|photo|picture|portrait|face|icon|image)/i.test(key)) continue;
          const found = findAvatarInPayload(value, depth + 1);
          if (found) return found;
        }
      }
      return "";
    }
    function discoverMoviePilotAvatarFromDom() {
      if (typeof document === "undefined") return "";
      const selectors = [
        ".v-avatar img",
        '[class*="avatar" i] img',
        '[class*="user" i] img',
        '[class*="profile" i] img',
        'img[alt*="头像" i]',
        'img[title*="头像" i]'
      ];
      const imagesInDom = Array.from(document.querySelectorAll(selectors.join(",")));
      for (const image of imagesInDom) {
        if (image.closest(".mcr-page-shell")) continue;
        const src = normalizeMoviePilotAvatarUrl(image.currentSrc || image.src);
        if (src && findAvatarInPayload(src)) return src;
      }
      return "";
    }
    function discoverMoviePilotAvatarFromStorage() {
      if (typeof window === "undefined") return "";
      const stores = [window.localStorage, window.sessionStorage].filter(Boolean);
      for (const store of stores) {
        for (let index = 0; index < store.length; index += 1) {
          const key = store.key(index) || "";
          if (!/(user|profile|account|auth|login|avatar)/i.test(key)) continue;
          const value = store.getItem(key);
          if (!value) continue;
          const direct = findAvatarInPayload(value);
          if (direct) return direct;
          try {
            const parsed = JSON.parse(value);
            const found = findAvatarInPayload(parsed);
            if (found) return found;
          } catch {
          }
        }
      }
      const globalCandidates = [
        window.__INITIAL_STATE__,
        window.__APP_INITIAL_STATE__,
        window.__PINIA__,
        window.$pinia?.state?.value
      ];
      for (const candidate of globalCandidates) {
        const found = findAvatarInPayload(candidate);
        if (found) return found;
      }
      return "";
    }
    async function discoverMoviePilotAvatarFromApi() {
      if (typeof window === "undefined" || typeof fetch !== "function") return "";
      const endpoints = [
        "/api/v1/user/current",
        "/api/v1/user/info",
        "/api/v1/user",
        "/api/v1/auth/user",
        "/api/v1/users/current"
      ];
      for (const endpoint of endpoints) {
        try {
          const response = await fetch(endpoint, {
            credentials: "include",
            headers: { accept: "application/json" }
          });
          if (!response.ok) continue;
          const payload = await response.json();
          const found = findAvatarInPayload(payload);
          if (found) return found;
        } catch {
        }
      }
      return "";
    }
    async function discoverMoviePilotAvatar() {
      const fromDom = discoverMoviePilotAvatarFromDom();
      if (fromDom) {
        moviePilotAvatarUrl.value = fromDom;
        return;
      }
      const fromStorage = discoverMoviePilotAvatarFromStorage();
      if (fromStorage) {
        moviePilotAvatarUrl.value = fromStorage;
        return;
      }
      const fromApi = await discoverMoviePilotAvatarFromApi();
      if (fromApi) {
        moviePilotAvatarUrl.value = fromApi;
      }
    }
    function syncBackendStatusWhenVisible() {
      if (!componentActive) return;
      if (typeof document !== "undefined" && document.visibilityState !== "visible") return;
      void loadStatus();
    }
    function updateHistoryFloatingActionsPosition() {
      if (typeof window === "undefined") return;
      const stickyTop = Math.max(72, Math.min(112, window.innerHeight * 0.08));
      const headerRect = historyHeaderEl.value?.getBoundingClientRect();
      const preferredTop = headerRect ? headerRect.bottom + 12 : stickyTop;
      const top = Math.max(stickyTop, preferredTop);
      historyFloatingStyle.value = {
        left: "50%",
        top: `${Math.round(top)}px`,
        transform: "translateX(-50%)"
      };
    }
    watch(
      () => [selectedHistoryPaths.value.length, pageTab.value, history.length],
      () => {
        if (typeof window === "undefined") return;
        window.requestAnimationFrame(updateHistoryFloatingActionsPosition);
      }
    );
    watch(pageTab, (nextTab) => {
      if (nextTab !== "history-tab") {
        selectedHistoryPaths.value = [];
      }
    });
    watch(historySnapshotDialog, (open) => {
      if (!open) selectedHistoryPaths.value = [];
    });
    watch(isEditingLayout, () => {
      if (typeof window === "undefined") return;
      window.requestAnimationFrame(updatePreviewBayHeight);
    });
    async function loadFontLibrary() {
      try {
        const resp = await props.api.get("plugin/YahahaCoverStudio/fonts");
        if (!resp || resp.code !== 0) {
          throw new Error(resp?.msg || "load fonts failed");
        }
        customFontItems.value = Array.isArray(resp.data?.custom) ? resp.data.custom : [];
      } catch (error) {
        console.warn("load page font library failed", error);
      }
    }
    onMounted(async () => {
      componentActive = true;
      if (typeof window !== "undefined") {
        donationAcknowledged.value = window.localStorage.getItem(DONATION_ACK_STORAGE_KEY) === "1" || window.localStorage.getItem(DONATION_LEGACY_ACK_STORAGE_KEY) === "1";
        donationAvatarSource.value = window.localStorage.getItem(DONATION_AVATAR_STORAGE_KEY) === "mp" ? "mp" : "developer";
        donationExecutionCount.value = Math.max(0, Number(window.localStorage.getItem(DONATION_RUN_COUNT_STORAGE_KEY) || 0) || 0);
        void discoverMoviePilotAvatar();
        syncSystemTheme();
        pageThemeMediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
        pageThemeMediaQuery.addEventListener?.("change", syncSystemTheme);
        window.addEventListener("focus", syncBackendStatusWhenVisible);
        window.addEventListener("scroll", updateHistoryFloatingActionsPosition, true);
        window.addEventListener("resize", updateHistoryFloatingActionsPosition);
        window.addEventListener("resize", updatePreviewBayHeight);
        window.addEventListener("scroll", scheduleTimeMachineDepth, true);
        window.addEventListener("resize", scheduleTimeMachineDepth);
      }
      if (typeof ResizeObserver !== "undefined") {
        previewBayResizeObserver = new ResizeObserver(updatePreviewBayHeight);
        if (previewBayEl.value) {
          previewBayResizeObserver.observe(previewBayEl.value);
        }
      }
      if (typeof document !== "undefined") {
        pageThemeObserver = new MutationObserver(() => {
          hostThemeVersion.value += 1;
        });
        pageThemeObserver.observe(document.documentElement, {
          attributes: true,
          attributeFilter: ["class", "data-theme"]
        });
        if (document.body) {
          pageThemeObserver.observe(document.body, {
            attributes: true,
            attributeFilter: ["class", "data-theme"]
          });
        }
        document.addEventListener("visibilitychange", syncBackendStatusWhenVisible);
      }
      void loadFontLibrary();
      await loadStatus();
      if (isGenerating.value) return;
      await loadPreviewSources();
      window.requestAnimationFrame(updatePreviewBayHeight);
    });
    onBeforeUnmount(() => {
      timeRecordObserver?.disconnect();
      componentActive = false;
      if (typeof window !== "undefined") {
        pageThemeMediaQuery?.removeEventListener?.("change", syncSystemTheme);
        window.removeEventListener("focus", syncBackendStatusWhenVisible);
        window.removeEventListener("scroll", updateHistoryFloatingActionsPosition, true);
        window.removeEventListener("resize", updateHistoryFloatingActionsPosition);
        window.removeEventListener("resize", updatePreviewBayHeight);
        window.removeEventListener("scroll", scheduleTimeMachineDepth, true);
        window.removeEventListener("resize", scheduleTimeMachineDepth);
        if (timeMachineFrame) window.cancelAnimationFrame(timeMachineFrame);
      }
      if (typeof document !== "undefined") {
        document.removeEventListener("visibilitychange", syncBackendStatusWhenVisible);
      }
      pageThemeObserver?.disconnect();
      pageThemeObserver = null;
      previewBayResizeObserver?.disconnect();
      previewBayResizeObserver = null;
      pageThemeMediaQuery = null;
      stopGenerationStatusPoller();
      cancelPendingPreviewSourceReload();
      if (autoSaveLayoutTimer !== null) {
        window.clearTimeout(autoSaveLayoutTimer);
        autoSaveLayoutTimer = null;
        if (!controlsLocked.value) {
          void persistCustomLayoutState();
        }
      }
      if (measureLayoutTimer !== null) {
        window.clearTimeout(measureLayoutTimer);
        measureLayoutTimer = null;
      }
    });
    return (_ctx, _cache) => {
      const _component_v_icon = _resolveComponent("v-icon");
      const _component_v_btn = _resolveComponent("v-btn");
      const _component_v_tooltip = _resolveComponent("v-tooltip");
      const _component_v_list_item_title = _resolveComponent("v-list-item-title");
      const _component_v_list_item = _resolveComponent("v-list-item");
      const _component_v_list = _resolveComponent("v-list");
      const _component_v_menu = _resolveComponent("v-menu");
      const _component_v_window_item = _resolveComponent("v-window-item");
      const _component_v_btn_toggle = _resolveComponent("v-btn-toggle");
      const _component_v_img = _resolveComponent("v-img");
      const _component_v_card_text = _resolveComponent("v-card-text");
      const _component_v_card = _resolveComponent("v-card");
      const _component_v_col = _resolveComponent("v-col");
      const _component_v_row = _resolveComponent("v-row");
      const _component_v_window = _resolveComponent("v-window");
      const _component_v_defaults_provider = _resolveComponent("v-defaults-provider");
      const _component_v_dialog = _resolveComponent("v-dialog");
      _resolveComponent("v-spacer");
      _resolveComponent("v-card-title");
      _resolveComponent("v-divider");
      _resolveComponent("v-card-actions");
      return _openBlock(), _createElementBlock("div", {
        class: "mcr-shell mcr-page-shell",
        "data-mcr-theme": isDark.value ? "dark" : "light"
      }, [
        _cache[121] || (_cache[121] = _createElementVNode("div", { class: "mcr-shell__aurora" }, null, -1)),
        _cache[122] || (_cache[122] = _createElementVNode("div", { class: "mcr-shell__noise" }, null, -1)),
        _createVNode(_component_v_card, { class: "mcr-frame" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_defaults_provider, { defaults: _unref(controlDefaults) }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, { class: "mcr-frame__body" }, {
                  default: _withCtx(() => [
                    _createElementVNode("section", _hoisted_2, [
                      _createElementVNode("div", _hoisted_3, [
                        _createElementVNode("div", _hoisted_4, [
                          _createElementVNode("div", _hoisted_5, [
                            _createElementVNode("button", {
                              type: "button",
                              class: _normalizeClass(["mcr-logo-slot yh-avatar-wrap", { "mcr-logo-slot--donor": donationAcknowledged.value }]),
                              title: "赞赏支持",
                              "aria-label": "赞赏支持",
                              onClick: openDonationDialog
                            }, [
                              _createElementVNode("span", _hoisted_6, [
                                donationAvatarImage.value ? (_openBlock(), _createElementBlock("img", {
                                  key: 0,
                                  class: "yh-avatar__image",
                                  src: donationAvatarImage.value,
                                  alt: ""
                                }, null, 8, _hoisted_7)) : (_openBlock(), _createBlock(_component_v_icon, {
                                  key: 1,
                                  icon: donationAvatarIcon.value,
                                  size: "24"
                                }, null, 8, ["icon"]))
                              ]),
                              donationAcknowledged.value ? (_openBlock(), _createElementBlock("span", {
                                key: 0,
                                class: "yh-avatar-crown",
                                title: "切换为 MP 头像",
                                "aria-label": "切换为 MP 头像",
                                onClick: _withModifiers(selectMoviePilotAvatar, ["stop", "prevent"])
                              }, [
                                _createVNode(_component_v_icon, {
                                  icon: "mdi-crown",
                                  size: "24"
                                })
                              ])) : _createCommentVNode("", true)
                            ], 2),
                            _cache[52] || (_cache[52] = _createElementVNode("h1", {
                              class: "yh-brand-title",
                              "aria-label": "呀哈哈封面工坊 Yahaha Cover Studio"
                            }, [
                              _createElementVNode("span", {
                                class: "yh-brand-en-big",
                                "aria-hidden": "true"
                              }, [
                                _createElementVNode("span", { class: "yh-brand-en-pc" }, "Yahaha Cover Studio"),
                                _createElementVNode("span", { class: "yh-brand-en-mobile" }, [
                                  _createElementVNode("span", null, "Yahaha"),
                                  _createElementVNode("span", null, "CoverStudio")
                                ])
                              ]),
                              _createElementVNode("span", { class: "yh-brand-zh-overlap" }, [
                                _createElementVNode("span", { class: "yh-brand-zh-part" }, "呀哈哈"),
                                _createElementVNode("span", { class: "yh-brand-zh-part" }, "封面工坊")
                              ])
                            ], -1))
                          ])
                        ]),
                        _createElementVNode("div", _hoisted_8, [
                          _createElementVNode("div", _hoisted_9, [
                            _createElementVNode("button", {
                              type: "button",
                              class: _normalizeClass(["mcr-logo-slot yh-avatar-wrap yh-avatar-toolbar", { "mcr-logo-slot--donor": donationAcknowledged.value }]),
                              title: "赞赏支持",
                              "aria-label": "赞赏支持",
                              onClick: openDonationDialog
                            }, [
                              _createElementVNode("span", _hoisted_10, [
                                donationAvatarImage.value ? (_openBlock(), _createElementBlock("img", {
                                  key: 0,
                                  class: "yh-avatar__image",
                                  src: donationAvatarImage.value,
                                  alt: ""
                                }, null, 8, _hoisted_11)) : (_openBlock(), _createBlock(_component_v_icon, {
                                  key: 1,
                                  icon: donationAvatarIcon.value,
                                  size: "22"
                                }, null, 8, ["icon"]))
                              ]),
                              donationAcknowledged.value ? (_openBlock(), _createElementBlock("span", {
                                key: 0,
                                class: "yh-avatar-crown",
                                title: "切换为 MP 头像",
                                "aria-label": "切换为 MP 头像",
                                onClick: _withModifiers(selectMoviePilotAvatar, ["stop", "prevent"])
                              }, [
                                _createVNode(_component_v_icon, {
                                  icon: "mdi-crown",
                                  size: "20"
                                })
                              ])) : _createCommentVNode("", true)
                            ], 2),
                            _createElementVNode("button", {
                              type: "button",
                              class: _normalizeClass(["yh-run-btn", { "is-running": isGenerating.value }]),
                              style: _normalizeStyle(runButtonProgressStyle.value),
                              title: isGenerating.value ? generationProgressLabel.value : "生成封面",
                              "aria-label": isGenerating.value ? generationProgressLabel.value : "生成封面",
                              disabled: !statusLoaded.value || generatingNow.value,
                              onClick: handleGenerateAction
                            }, [
                              _cache[53] || (_cache[53] = _createElementVNode("span", {
                                class: "yh-run-progress",
                                "aria-hidden": "true"
                              }, null, -1)),
                              _createElementVNode("span", _hoisted_13, [
                                _createVNode(_component_v_icon, {
                                  icon: isGenerating.value ? "mdi-stop-circle-outline" : "mdi-play-circle-outline",
                                  size: "24"
                                }, null, 8, ["icon"]),
                                isGenerating.value ? (_openBlock(), _createElementBlock("span", _hoisted_14, "生成中")) : _createCommentVNode("", true),
                                isGenerating.value ? (_openBlock(), _createElementBlock("span", _hoisted_15, _toDisplayString(generationProgressPercent.value) + "%", 1)) : _createCommentVNode("", true)
                              ])
                            ], 14, _hoisted_12),
                            _createVNode(_component_v_btn, {
                              size: "small",
                              class: "mcr-button mcr-button--ghost mcr-button--dark-neutral yh-icon-btn",
                              icon: "",
                              title: "配置",
                              "aria-label": "配置",
                              disabled: controlsLocked.value,
                              onClick: notifySwitch
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_icon, {
                                  icon: "mdi-cog-outline",
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
                          _createElementVNode("div", _hoisted_16, [
                            _createElementVNode("span", {
                              class: _normalizeClass({ "is-disabled": !pluginEnabled.value })
                            }, "插件" + _toDisplayString(pluginEnabled.value ? "已启用" : "已停用"), 3),
                            _createElementVNode("span", null, _toDisplayString(currentStyleLabel.value), 1),
                            _createElementVNode("span", null, _toDisplayString(currentVariantLabel.value), 1),
                            _createElementVNode("span", null, _toDisplayString(sourceModeLabel.value), 1),
                            sourceSortLocked.value ? (_openBlock(), _createElementBlock("span", _hoisted_17, "最新入库排序已锁定")) : _createCommentVNode("", true),
                            backendBusy.value ? (_openBlock(), _createBlock(AsyncStatusDots, {
                              key: 1,
                              label: backendBusyLabel.value
                            }, null, 8, ["label"])) : _createCommentVNode("", true)
                          ]),
                          _createElementVNode("div", {
                            class: _normalizeClass(["mcr-page-tabs-shell", { "mcr-page-tabs-shell--history": pageTab.value === "history-tab" }])
                          }, [
                            _cache[56] || (_cache[56] = _createElementVNode("span", {
                              class: "mcr-page-tabs-indicator",
                              "aria-hidden": "true"
                            }, null, -1)),
                            _createElementVNode("div", _hoisted_18, [
                              _createElementVNode("button", {
                                type: "button",
                                role: "tab",
                                class: _normalizeClass(["mcr-page-tab-button", { "mcr-page-tab-button--active": pageTab.value === "generate-tab" }]),
                                "aria-selected": pageTab.value === "generate-tab",
                                disabled: controlsLocked.value,
                                onClick: _cache[0] || (_cache[0] = ($event) => setPageTab("generate-tab"))
                              }, [..._cache[54] || (_cache[54] = [
                                _createElementVNode("span", { class: "mcr-page-tabs-label" }, "封面生成", -1)
                              ])], 10, _hoisted_19),
                              _createElementVNode("button", {
                                type: "button",
                                role: "tab",
                                class: _normalizeClass(["mcr-page-tab-button", { "mcr-page-tab-button--active": pageTab.value === "history-tab" }]),
                                "aria-selected": pageTab.value === "history-tab",
                                disabled: controlsLocked.value,
                                onClick: _cache[1] || (_cache[1] = ($event) => setPageTab("history-tab"))
                              }, [..._cache[55] || (_cache[55] = [
                                _createElementVNode("span", { class: "mcr-page-tabs-label" }, "历史封面", -1)
                              ])], 10, _hoisted_20)
                            ])
                          ], 2)
                        ])
                      ])
                    ]),
                    _createVNode(_component_v_window, {
                      modelValue: pageTab.value,
                      "onUpdate:modelValue": _cache[36] || (_cache[36] = ($event) => pageTab.value = $event),
                      touch: false
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_window_item, { value: "generate-tab" }, {
                          default: _withCtx(() => [
                            _createElementVNode("div", {
                              class: _normalizeClass(["generate-layout blueprint-workbench", {
                                "blueprint-workbench--editing": isEditingLayout.value,
                                "blueprint-workbench--locked": controlsLocked.value
                              }])
                            }, [
                              _createElementVNode("section", {
                                ref_key: "previewBayEl",
                                ref: previewBayEl,
                                class: _normalizeClass(["blueprint-preview-bay", { "blueprint-preview-bay--locked": controlsLocked.value }])
                              }, [
                                _createElementVNode("div", _hoisted_21, [
                                  _createElementVNode("div", null, [
                                    _createElementVNode("div", _hoisted_22, _toDisplayString(isEditingLayout.value ? "Editor" : "Canvas"), 1),
                                    _createElementVNode("div", _hoisted_23, _toDisplayString(isEditingLayout.value ? "画布编辑" : previewModeLabel.value), 1)
                                  ]),
                                  !isEditingLayout.value ? (_openBlock(), _createBlock(_component_v_tooltip, {
                                    key: 0,
                                    text: "重新获取海报"
                                  }, {
                                    activator: _withCtx(({ props: tooltipProps }) => [
                                      _createElementVNode("button", _mergeProps(tooltipProps, {
                                        type: "button",
                                        class: ["mcr-preview-refresh", { "is-loading": refreshingPreview.value }],
                                        "aria-label": "重新获取海报",
                                        disabled: refreshingPreview.value || controlsLocked.value,
                                        onClick: refreshCurrentPreview
                                      }), [
                                        _createVNode(_component_v_icon, {
                                          icon: "mdi-refresh",
                                          size: "22"
                                        })
                                      ], 16, _hoisted_24)
                                    ]),
                                    _: 1
                                  })) : _createCommentVNode("", true)
                                ]),
                                isEditingLayout.value && customStaticLayout.value ? (_openBlock(), _createBlock(CustomLayoutEditor, {
                                  key: activeEditorTemplateId.value || coverStyleBase.value,
                                  "model-value": customStaticLayout.value,
                                  "preview-source": previewSource.value,
                                  params: simulationParams,
                                  "floating-tools-visible": pageTab.value === "generate-tab" && isEditingLayout.value,
                                  theme: isDark.value ? "dark" : "light",
                                  api: props.api,
                                  embedded: "",
                                  "onUpdate:modelValue": onLayoutUpdated
                                }, {
                                  "footer-actions": _withCtx(() => [
                                    _createElementVNode("span", _hoisted_25, [
                                      _createElementVNode("span", _hoisted_26, [
                                        _createElementVNode("button", {
                                          type: "button",
                                          class: "mcr-button mcr-button--primary mcr-editor-save-main",
                                          disabled: controlsLocked.value || !activeEditorTemplateId.value || !customStaticLayout.value,
                                          onClick: saveCustomLayoutNow
                                        }, " 保存方案 ", 8, _hoisted_27),
                                        _createElementVNode("button", {
                                          type: "button",
                                          class: "mcr-button mcr-button--primary mcr-editor-save-toggle",
                                          "aria-label": editorAutoSaveEnabled.value ? "自动保存已开启，点击关闭" : "自动保存已关闭，点击开启",
                                          title: editorAutoSaveEnabled.value ? "自动保存已开启，点击关闭" : "自动保存已关闭，点击开启",
                                          disabled: controlsLocked.value || !activeEditorTemplateId.value || !customStaticLayout.value,
                                          onClick: _withModifiers(toggleEditorAutoSave, ["stop"])
                                        }, [
                                          _createElementVNode("span", _hoisted_29, _toDisplayString(editorAutoSaveEnabled.value ? "AUTO" : "MANUAL"), 1)
                                        ], 8, _hoisted_28)
                                      ])
                                    ]),
                                    _createVNode(_component_v_btn, {
                                      size: "small",
                                      class: "mcr-button mcr-button--ghost mcr-button--dark-neutral",
                                      disabled: controlsLocked.value || !activeEditorTemplateId.value,
                                      onClick: restoreCurrentLayoutDefaults
                                    }, {
                                      default: _withCtx(() => [
                                        _createTextVNode(_toDisplayString(resetButtonLabel.value), 1)
                                      ]),
                                      _: 1
                                    }, 8, ["disabled"]),
                                    _createVNode(_component_v_btn, {
                                      size: "small",
                                      class: "mcr-button mcr-button--ghost mcr-button--dark-neutral",
                                      disabled: controlsLocked.value,
                                      onClick: _cache[2] || (_cache[2] = ($event) => isEditingLayout.value = false)
                                    }, {
                                      default: _withCtx(() => [..._cache[57] || (_cache[57] = [
                                        _createTextVNode(" 返回预览 ", -1)
                                      ])]),
                                      _: 1
                                    }, 8, ["disabled"])
                                  ]),
                                  _: 1
                                }, 8, ["model-value", "preview-source", "params", "floating-tools-visible", "theme", "api"])) : (_openBlock(), _createElementBlock("div", _hoisted_30, [
                                  showMainPreviewSkeleton.value ? (_openBlock(), _createElementBlock("div", {
                                    key: 0,
                                    class: _normalizeClass(["blueprint-skeleton blueprint-skeleton--preview", { "blueprint-skeleton--active": resourceSkeletonActive.value }]),
                                    "aria-label": "预览资源加载中"
                                  }, [..._cache[58] || (_cache[58] = [
                                    _createElementVNode("span", { class: "blueprint-skeleton__shape blueprint-skeleton__shape--visual" }, null, -1),
                                    _createElementVNode("span", { class: "blueprint-skeleton__shape blueprint-skeleton__shape--title" }, null, -1),
                                    _createElementVNode("span", { class: "blueprint-skeleton__shape blueprint-skeleton__shape--line" }, null, -1),
                                    _createElementVNode("span", { class: "blueprint-skeleton__shape blueprint-skeleton__shape--line-short" }, null, -1),
                                    _createElementVNode("span", { class: "blueprint-skeleton__shape blueprint-skeleton__shape--chip" }, null, -1)
                                  ])], 2)) : (_openBlock(), _createBlock(GeneratePreviewSimulation, {
                                    key: 1,
                                    source: effectivePreviewSource.value,
                                    params: simulationParams
                                  }, null, 8, ["source", "params"]))
                                ])),
                                !isEditingLayout.value ? (_openBlock(), _createElementBlock("div", _hoisted_31, [
                                  _createElementVNode("label", _hoisted_32, [
                                    _cache[60] || (_cache[60] = _createElementVNode("span", null, "海报来源", -1)),
                                    _withDirectives(_createElementVNode("select", {
                                      "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => posterSource.value = $event),
                                      disabled: controlsLocked.value,
                                      onChange: saveRenderOptions
                                    }, [..._cache[59] || (_cache[59] = [
                                      _createElementVNode("option", { value: "backdrop" }, "横版 Backdrop", -1),
                                      _createElementVNode("option", { value: "poster" }, "竖版 Poster", -1)
                                    ])], 40, _hoisted_33), [
                                      [_vModelSelect, posterSource.value]
                                    ])
                                  ]),
                                  _createElementVNode("label", _hoisted_34, [
                                    _createElementVNode("span", _hoisted_35, [
                                      _cache[61] || (_cache[61] = _createElementVNode("span", null, "封面来源排序", -1)),
                                      sourceSortLocked.value ? (_openBlock(), _createElementBlock("span", _hoisted_36, "已锁定")) : _createCommentVNode("", true)
                                    ]),
                                    _withDirectives(_createElementVNode("select", {
                                      "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => sourceSortBy.value = $event),
                                      disabled: sourceSortDisabled.value,
                                      onChange: saveRenderOptions
                                    }, [
                                      _cache[62] || (_cache[62] = _createElementVNode("option", { value: "Random" }, "随机", -1)),
                                      _createElementVNode("option", _hoisted_38, _toDisplayString(sourceSortLocked.value ? "最新入库（已锁定）" : "最新入库"), 1),
                                      _cache[63] || (_cache[63] = _createElementVNode("option", { value: "PremiereDate" }, "最新发行", -1))
                                    ], 40, _hoisted_37), [
                                      [_vModelSelect, sourceSortBy.value]
                                    ])
                                  ]),
                                  _createElementVNode("label", _hoisted_39, [
                                    _cache[65] || (_cache[65] = _createElementVNode("span", null, "分辨率", -1)),
                                    styleVariant.value === "static" ? _withDirectives((_openBlock(), _createElementBlock("select", {
                                      key: 0,
                                      "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => staticResolution.value = $event),
                                      disabled: controlsLocked.value,
                                      onChange: saveRenderOptions
                                    }, [..._cache[64] || (_cache[64] = [
                                      _createElementVNode("option", { value: "480p" }, "480p", -1),
                                      _createElementVNode("option", { value: "720p" }, "720p", -1),
                                      _createElementVNode("option", { value: "1080p" }, "1080p", -1)
                                    ])], 40, _hoisted_40)), [
                                      [_vModelSelect, staticResolution.value]
                                    ]) : (_openBlock(), _createElementBlock("span", _hoisted_41, _toDisplayString(animatedResolutionLabel.value), 1))
                                  ])
                                ])) : _createCommentVNode("", true)
                              ], 2),
                              !isEditingLayout.value ? (_openBlock(), _createElementBlock("aside", {
                                key: 0,
                                class: _normalizeClass(["blueprint-control-bay", { "blueprint-control-bay--collapsed": schemeListCollapsed.value }]),
                                style: _normalizeStyle(controlBayStyle.value)
                              }, [
                                _createElementVNode("div", {
                                  class: _normalizeClass(["blueprint-panel-heading mcr-collapsible-heading", { "mcr-collapsible-heading--collapsed": schemeListCollapsed.value }]),
                                  role: "button",
                                  tabindex: "0",
                                  "aria-expanded": !schemeListCollapsed.value,
                                  "aria-controls": "mcr-scheme-list-content",
                                  onClick: _cache[6] || (_cache[6] = ($event) => schemeListCollapsed.value = !schemeListCollapsed.value),
                                  onKeydown: [
                                    _cache[7] || (_cache[7] = _withKeys(_withModifiers(($event) => schemeListCollapsed.value = !schemeListCollapsed.value, ["prevent"]), ["enter"])),
                                    _cache[8] || (_cache[8] = _withKeys(_withModifiers(($event) => schemeListCollapsed.value = !schemeListCollapsed.value, ["prevent"]), ["space"]))
                                  ]
                                }, [
                                  _createElementVNode("div", _hoisted_43, [
                                    _cache[67] || (_cache[67] = _createElementVNode("div", { class: "mcr-panel__eyebrow" }, "Presets", -1)),
                                    _createElementVNode("div", _hoisted_44, [
                                      _cache[66] || (_cache[66] = _createTextVNode(" 封面方案 ", -1)),
                                      _createVNode(_component_v_icon, {
                                        icon: "mdi-chevron-up",
                                        size: "20",
                                        class: "mcr-collapsible-heading__icon",
                                        "aria-hidden": "true"
                                      })
                                    ])
                                  ]),
                                  _createVNode(_Transition, { name: "mcr-mode-switch" }, {
                                    default: _withCtx(() => [
                                      !schemeListCollapsed.value ? (_openBlock(), _createElementBlock("button", {
                                        key: 0,
                                        class: _normalizeClass(["blueprint-mode-toggle", {
                                          "blueprint-mode-toggle--animated": styleVariant.value === "animated",
                                          "blueprint-mode-toggle--disabled": controlsLocked.value || coverStyleBase.value === "custom_static",
                                          "blueprint-mode-toggle--pulse": modeSwitchPulse.value
                                        }]),
                                        type: "button",
                                        "aria-pressed": styleVariant.value === "animated",
                                        "aria-disabled": controlsLocked.value || coverStyleBase.value === "custom_static",
                                        disabled: controlsLocked.value || coverStyleBase.value === "custom_static",
                                        onClick: _withModifiers(onModeSwitchClick, ["stop"]),
                                        onKeydown: [
                                          _withKeys(_withModifiers(onModeSwitchClick, ["stop", "prevent"]), ["enter"]),
                                          _withKeys(_withModifiers(onModeSwitchClick, ["stop", "prevent"]), ["space"])
                                        ]
                                      }, [..._cache[68] || (_cache[68] = [
                                        _createElementVNode("span", { class: "blueprint-mode-option blueprint-mode-option--static" }, [
                                          _createElementVNode("span", null, "静态")
                                        ], -1),
                                        _createElementVNode("span", {
                                          class: "blueprint-mode-switch-track",
                                          "aria-hidden": "true"
                                        }, [
                                          _createElementVNode("span", { class: "blueprint-mode-thumb" })
                                        ], -1),
                                        _createElementVNode("span", { class: "blueprint-mode-option blueprint-mode-option--animated" }, [
                                          _createElementVNode("span", null, "动图")
                                        ], -1)
                                      ])], 42, _hoisted_45)) : _createCommentVNode("", true)
                                    ]),
                                    _: 1
                                  })
                                ], 42, _hoisted_42),
                                _createVNode(_Transition, { name: "mcr-list-collapse" }, {
                                  default: _withCtx(() => [
                                    _withDirectives(_createElementVNode("div", {
                                      id: "mcr-scheme-list-content",
                                      class: _normalizeClass(["mcr-scheme-list", { "mcr-scheme-list--animated": styleVariant.value === "animated" }]),
                                      "aria-label": "封面方案列表"
                                    }, [
                                      animatedSettingsPanelOpen.value ? (_openBlock(), _createElementBlock("div", _hoisted_46, [
                                        _createElementVNode("div", _hoisted_47, [
                                          _createElementVNode("button", {
                                            type: "button",
                                            class: "mcr-animated-parameter-panel__back",
                                            "aria-label": "返回动态方案列表",
                                            title: "返回动态方案列表",
                                            onClick: _cache[9] || (_cache[9] = ($event) => animatedSettingsPanelOpen.value = false)
                                          }, [
                                            _createVNode(_component_v_icon, {
                                              icon: "mdi-arrow-left",
                                              size: "18"
                                            })
                                          ]),
                                          _createElementVNode("div", null, [
                                            _cache[69] || (_cache[69] = _createElementVNode("span", null, "Motion Settings", -1)),
                                            _createElementVNode("strong", null, _toDisplayString(animatedSettingsTitle.value), 1)
                                          ])
                                        ]),
                                        _createElementVNode("div", _hoisted_48, [
                                          _createVNode(BlueprintSelect, {
                                            modelValue: animatedSettings.animationFormat,
                                            "onUpdate:modelValue": _cache[10] || (_cache[10] = ($event) => animatedSettings.animationFormat = $event),
                                            label: "输出格式",
                                            items: animatedFormatItems
                                          }, null, 8, ["modelValue"]),
                                          _createVNode(BlueprintSelect, {
                                            modelValue: animatedSettings.animationReduceColors,
                                            "onUpdate:modelValue": _cache[11] || (_cache[11] = ($event) => animatedSettings.animationReduceColors = $event),
                                            label: "颜色压缩",
                                            items: animatedColorReduceItems
                                          }, null, 8, ["modelValue"]),
                                          _createVNode(BlueprintSelect, {
                                            modelValue: animatedSettings.mainTitleFontPreset,
                                            "onUpdate:modelValue": _cache[12] || (_cache[12] = ($event) => animatedSettings.mainTitleFontPreset = $event),
                                            label: "主标题字体",
                                            items: dynamicFontItems.value
                                          }, null, 8, ["modelValue", "items"]),
                                          _createVNode(BlueprintSelect, {
                                            modelValue: animatedSettings.subtitleFontPreset,
                                            "onUpdate:modelValue": _cache[13] || (_cache[13] = ($event) => animatedSettings.subtitleFontPreset = $event),
                                            label: "副标题字体",
                                            items: dynamicFontItems.value
                                          }, null, 8, ["modelValue", "items"]),
                                          _createVNode(BlueprintRange, {
                                            modelValue: animatedSettings.mainTitleFontSize,
                                            "onUpdate:modelValue": _cache[14] || (_cache[14] = ($event) => animatedSettings.mainTitleFontSize = $event),
                                            label: "主标题字号",
                                            min: 24,
                                            max: 320,
                                            step: 1
                                          }, null, 8, ["modelValue"]),
                                          _createVNode(BlueprintRange, {
                                            modelValue: animatedSettings.subtitleFontSize,
                                            "onUpdate:modelValue": _cache[15] || (_cache[15] = ($event) => animatedSettings.subtitleFontSize = $event),
                                            label: "副标题字号",
                                            min: 12,
                                            max: 220,
                                            step: 1
                                          }, null, 8, ["modelValue"]),
                                          _createVNode(BlueprintRange, {
                                            modelValue: animatedSettings.titleScale,
                                            "onUpdate:modelValue": _cache[16] || (_cache[16] = ($event) => animatedSettings.titleScale = $event),
                                            label: "标题缩放",
                                            min: 0.2,
                                            max: 3,
                                            step: 0.05
                                          }, null, 8, ["modelValue"]),
                                          _createVNode(BlueprintRange, {
                                            modelValue: animatedSettings.blurSize,
                                            "onUpdate:modelValue": _cache[17] || (_cache[17] = ($event) => animatedSettings.blurSize = $event),
                                            label: "背景模糊",
                                            min: 0,
                                            max: 100,
                                            step: 1
                                          }, null, 8, ["modelValue"]),
                                          _createVNode(BlueprintRange, {
                                            modelValue: animatedSettings.colorRatio,
                                            "onUpdate:modelValue": _cache[18] || (_cache[18] = ($event) => animatedSettings.colorRatio = $event),
                                            label: "背景混色",
                                            min: 0,
                                            max: 1,
                                            step: 0.05
                                          }, null, 8, ["modelValue"]),
                                          _createVNode(BlueprintRange, {
                                            modelValue: animatedSettings.animationDuration,
                                            "onUpdate:modelValue": _cache[19] || (_cache[19] = ($event) => animatedSettings.animationDuration = $event),
                                            label: "动画时长",
                                            min: 1,
                                            max: 60,
                                            step: 1
                                          }, null, 8, ["modelValue"]),
                                          _createVNode(BlueprintRange, {
                                            modelValue: animatedSettings.animationFps,
                                            "onUpdate:modelValue": _cache[20] || (_cache[20] = ($event) => animatedSettings.animationFps = $event),
                                            label: "帧率",
                                            min: 1,
                                            max: 60,
                                            step: 1
                                          }, null, 8, ["modelValue"]),
                                          showAnimatedImageCountSetting.value ? (_openBlock(), _createBlock(BlueprintRange, {
                                            key: 0,
                                            modelValue: animatedSettings.animated2ImageCount,
                                            "onUpdate:modelValue": _cache[21] || (_cache[21] = ($event) => animatedSettings.animated2ImageCount = $event),
                                            label: "图片数量",
                                            min: 3,
                                            max: 60,
                                            step: 1
                                          }, null, 8, ["modelValue"])) : _createCommentVNode("", true),
                                          showAnimatedScrollSetting.value ? (_openBlock(), _createBlock(BlueprintSelect, {
                                            key: 1,
                                            modelValue: animatedSettings.animationScroll,
                                            "onUpdate:modelValue": _cache[22] || (_cache[22] = ($event) => animatedSettings.animationScroll = $event),
                                            label: "滚动方向",
                                            items: animatedScrollItems
                                          }, null, 8, ["modelValue"])) : _createCommentVNode("", true),
                                          showAnimatedDepartureSetting.value ? (_openBlock(), _createBlock(BlueprintSelect, {
                                            key: 2,
                                            modelValue: animatedSettings.animated2DepartureType,
                                            "onUpdate:modelValue": _cache[23] || (_cache[23] = ($event) => animatedSettings.animated2DepartureType = $event),
                                            label: "动画风格",
                                            items: animatedDepartureItems
                                          }, null, 8, ["modelValue"])) : _createCommentVNode("", true),
                                          animatedSettingsBaseStyle.value === "static_3" ? (_openBlock(), _createElementBlock("p", _hoisted_49, " 方案 3 使用固定九宫格滚动，素材数量按 9 张处理。 ")) : _createCommentVNode("", true)
                                        ]),
                                        _createElementVNode("div", _hoisted_50, [
                                          animatedSettingsSaving.value ? (_openBlock(), _createBlock(AsyncStatusDots, {
                                            key: 0,
                                            label: "保存参数"
                                          })) : _createCommentVNode("", true),
                                          _createVNode(_component_v_btn, {
                                            size: "small",
                                            class: "mcr-button mcr-button--primary mcr-button--apple-primary",
                                            disabled: animatedSettingsSaving.value,
                                            onClick: saveAnimatedSettings
                                          }, {
                                            default: _withCtx(() => [..._cache[70] || (_cache[70] = [
                                              _createTextVNode(" 保存参数 ", -1)
                                            ])]),
                                            _: 1
                                          }, 8, ["disabled"])
                                        ])
                                      ])) : (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [
                                        (_openBlock(), _createElementBlock("div", {
                                          key: schemeListKey.value,
                                          ref_key: "schemeListScrollEl",
                                          ref: schemeListScrollEl,
                                          class: "mcr-scheme-list__scroll"
                                        }, [
                                          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(schemeListItems.value, (item) => {
                                            return _openBlock(), _createElementBlock("div", {
                                              key: item.id,
                                              class: _normalizeClass(["mcr-scheme-row", {
                                                "mcr-scheme-row--active": isSchemeItemActive(item),
                                                "mcr-scheme-row--preset": item.kind === "preset"
                                              }])
                                            }, [
                                              _createElementVNode("div", {
                                                role: "button",
                                                class: _normalizeClass(["mcr-scheme-row__select", { "mcr-scheme-row__select--disabled": controlsLocked.value }]),
                                                "aria-disabled": controlsLocked.value ? "true" : "false",
                                                tabindex: controlsLocked.value ? -1 : 0,
                                                onClick: ($event) => !controlsLocked.value && selectSchemeItem(item),
                                                onKeydown: [
                                                  _withKeys(_withModifiers(($event) => !controlsLocked.value && selectSchemeItem(item), ["prevent"]), ["enter"]),
                                                  _withKeys(_withModifiers(($event) => !controlsLocked.value && selectSchemeItem(item), ["prevent"]), ["space"])
                                                ]
                                              }, [
                                                _createElementVNode("span", _hoisted_52, [
                                                  showStylePreviewSkeleton.value ? (_openBlock(), _createElementBlock("span", {
                                                    key: 0,
                                                    class: _normalizeClass(["blueprint-skeleton blueprint-skeleton--card", { "blueprint-skeleton--active": resourceSkeletonActive.value }]),
                                                    "aria-label": "方案预览资源加载中"
                                                  }, [..._cache[71] || (_cache[71] = [
                                                    _createElementVNode("span", { class: "blueprint-skeleton__shape blueprint-skeleton__shape--visual" }, null, -1),
                                                    _createElementVNode("span", { class: "blueprint-skeleton__shape blueprint-skeleton__shape--title" }, null, -1),
                                                    _createElementVNode("span", { class: "blueprint-skeleton__shape blueprint-skeleton__shape--line" }, null, -1),
                                                    _createElementVNode("span", { class: "blueprint-skeleton__shape blueprint-skeleton__shape--line-short" }, null, -1),
                                                    _createElementVNode("span", { class: "blueprint-skeleton__shape blueprint-skeleton__shape--chip" }, null, -1)
                                                  ])], 2)) : buildSchemePreviewSource(item) ? (_openBlock(), _createBlock(GeneratePreviewSimulation, {
                                                    key: 1,
                                                    source: buildSchemePreviewSource(item),
                                                    params: simulationParams
                                                  }, null, 8, ["source", "params"])) : _createCommentVNode("", true)
                                                ]),
                                                _createElementVNode("span", _hoisted_53, [
                                                  _createElementVNode("strong", null, _toDisplayString(item.title), 1),
                                                  styleVariant.value === "static" ? (_openBlock(), _createElementBlock("span", _hoisted_54, _toDisplayString(item.kind === "preset" ? "预设方案" : "自定义方案"), 1)) : (_openBlock(), _createElementBlock("span", _hoisted_55, _toDisplayString(animatedResolutionLabel.value), 1))
                                                ])
                                              ], 42, _hoisted_51),
                                              _createElementVNode("div", _hoisted_56, [
                                                styleVariant.value === "static" ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                                                  _createVNode(_component_v_btn, {
                                                    icon: "mdi-tune-variant",
                                                    size: "x-small",
                                                    variant: "text",
                                                    class: "mcr-scheme-row__icon",
                                                    disabled: controlsLocked.value,
                                                    title: "编辑方案",
                                                    onClick: _withModifiers(($event) => editSchemeItem(item), ["stop"])
                                                  }, null, 8, ["disabled", "onClick"]),
                                                  _createVNode(_component_v_btn, {
                                                    icon: "mdi-form-textbox",
                                                    size: "x-small",
                                                    variant: "text",
                                                    class: "mcr-scheme-row__icon",
                                                    disabled: controlsLocked.value,
                                                    title: "重命名",
                                                    onClick: _withModifiers(($event) => renameSchemeItem(item), ["stop"])
                                                  }, null, 8, ["disabled", "onClick"]),
                                                  _createVNode(_component_v_menu, {
                                                    location: "bottom end",
                                                    "close-on-content-click": true
                                                  }, {
                                                    activator: _withCtx(({ props: exportMenuProps }) => [
                                                      _createVNode(_component_v_btn, _mergeProps({ ref_for: true }, exportMenuProps, {
                                                        icon: "mdi-export-variant",
                                                        size: "x-small",
                                                        variant: "text",
                                                        class: "mcr-scheme-row__icon",
                                                        disabled: controlsLocked.value,
                                                        title: "导出方案",
                                                        onClick: _cache[24] || (_cache[24] = _withModifiers(() => {
                                                        }, ["stop"]))
                                                      }), null, 16, ["disabled"])
                                                    ]),
                                                    default: _withCtx(() => [
                                                      _createVNode(_component_v_list, {
                                                        class: "mcr-template-action-menu",
                                                        "data-mcr-theme": isDark.value ? "dark" : "light",
                                                        density: "compact"
                                                      }, {
                                                        default: _withCtx(() => [
                                                          _createVNode(_component_v_list_item, {
                                                            onClick: ($event) => exportSchemeItemToClipboard(item)
                                                          }, {
                                                            default: _withCtx(() => [
                                                              _createVNode(_component_v_list_item_title, null, {
                                                                default: _withCtx(() => [..._cache[72] || (_cache[72] = [
                                                                  _createTextVNode("复制到剪切板", -1)
                                                                ])]),
                                                                _: 1
                                                              })
                                                            ]),
                                                            _: 1
                                                          }, 8, ["onClick"]),
                                                          _createVNode(_component_v_list_item, {
                                                            onClick: ($event) => exportSchemeItemToFile(item)
                                                          }, {
                                                            default: _withCtx(() => [
                                                              _createVNode(_component_v_list_item_title, null, {
                                                                default: _withCtx(() => [..._cache[73] || (_cache[73] = [
                                                                  _createTextVNode("下载 JSON 文件", -1)
                                                                ])]),
                                                                _: 1
                                                              })
                                                            ]),
                                                            _: 1
                                                          }, 8, ["onClick"])
                                                        ]),
                                                        _: 2
                                                      }, 1032, ["data-mcr-theme"])
                                                    ]),
                                                    _: 2
                                                  }, 1024),
                                                  item.kind === "custom" ? (_openBlock(), _createBlock(_component_v_btn, {
                                                    key: 0,
                                                    icon: "mdi-trash-can-outline",
                                                    size: "x-small",
                                                    variant: "text",
                                                    class: "mcr-scheme-row__icon mcr-scheme-row__icon--danger",
                                                    disabled: controlsLocked.value,
                                                    title: "删除方案",
                                                    onClick: _withModifiers(($event) => deleteSchemeItem(item), ["stop"])
                                                  }, null, 8, ["disabled", "onClick"])) : _createCommentVNode("", true)
                                                ], 64)) : item.kind === "preset" ? (_openBlock(), _createBlock(_component_v_btn, {
                                                  key: 1,
                                                  icon: "mdi-tune-variant",
                                                  size: "x-small",
                                                  variant: "text",
                                                  class: "mcr-scheme-row__icon",
                                                  disabled: controlsLocked.value,
                                                  title: "配置动态方案",
                                                  onClick: _withModifiers(($event) => openAnimatedSettings(item), ["stop"])
                                                }, null, 8, ["disabled", "onClick"])) : _createCommentVNode("", true)
                                              ])
                                            ], 2);
                                          }), 128))
                                        ])),
                                        styleVariant.value === "static" ? (_openBlock(), _createElementBlock("div", _hoisted_57, [
                                          _createVNode(_component_v_btn, {
                                            size: "small",
                                            class: "mcr-button mcr-button--primary mcr-button--dark-neutral mcr-scheme-tail-button",
                                            "prepend-icon": "mdi-plus",
                                            disabled: controlsLocked.value,
                                            onClick: createTemplateFromCurrent
                                          }, {
                                            default: _withCtx(() => [..._cache[74] || (_cache[74] = [
                                              _createTextVNode(" 添加方案 ", -1)
                                            ])]),
                                            _: 1
                                          }, 8, ["disabled"]),
                                          _createVNode(_component_v_menu, {
                                            location: "bottom end",
                                            "close-on-content-click": true
                                          }, {
                                            activator: _withCtx(({ props: importMenuProps }) => [
                                              _createVNode(_component_v_btn, _mergeProps(importMenuProps, {
                                                size: "small",
                                                class: "mcr-button mcr-button--ghost mcr-button--dark-neutral mcr-scheme-tail-button",
                                                "prepend-icon": "mdi-import",
                                                disabled: controlsLocked.value
                                              }), {
                                                default: _withCtx(() => [..._cache[75] || (_cache[75] = [
                                                  _createTextVNode(" 导入方案 ", -1)
                                                ])]),
                                                _: 1
                                              }, 16, ["disabled"])
                                            ]),
                                            default: _withCtx(() => [
                                              _createVNode(_component_v_list, {
                                                class: "mcr-template-action-menu",
                                                "data-mcr-theme": isDark.value ? "dark" : "light",
                                                density: "compact"
                                              }, {
                                                default: _withCtx(() => [
                                                  _createVNode(_component_v_list_item, { onClick: importTemplateFromClipboard }, {
                                                    default: _withCtx(() => [
                                                      _createVNode(_component_v_list_item_title, null, {
                                                        default: _withCtx(() => [..._cache[76] || (_cache[76] = [
                                                          _createTextVNode("从剪切板导入", -1)
                                                        ])]),
                                                        _: 1
                                                      })
                                                    ]),
                                                    _: 1
                                                  }),
                                                  _createVNode(_component_v_list_item, { onClick: triggerImportTemplate }, {
                                                    default: _withCtx(() => [
                                                      _createVNode(_component_v_list_item_title, null, {
                                                        default: _withCtx(() => [..._cache[77] || (_cache[77] = [
                                                          _createTextVNode("从 JSON 文件导入", -1)
                                                        ])]),
                                                        _: 1
                                                      })
                                                    ]),
                                                    _: 1
                                                  })
                                                ]),
                                                _: 1
                                              }, 8, ["data-mcr-theme"])
                                            ]),
                                            _: 1
                                          }),
                                          _createElementVNode("input", {
                                            ref_key: "importTemplateInput",
                                            ref: importTemplateInput,
                                            type: "file",
                                            accept: "application/json,.json",
                                            class: "mcr-visually-hidden",
                                            onChange: importTemplateFromFile
                                          }, null, 544)
                                        ])) : _createCommentVNode("", true)
                                      ], 64))
                                    ], 2), [
                                      [_vShow, !schemeListCollapsed.value]
                                    ])
                                  ]),
                                  _: 1
                                })
                              ], 6)) : _createCommentVNode("", true)
                            ], 2)
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_window_item, { value: "history-tab" }, {
                          default: _withCtx(() => [
                            _createElementVNode("div", {
                              ref_key: "historyHeaderEl",
                              ref: historyHeaderEl,
                              class: _normalizeClass(["mcr-history-header mcr-collapsible-heading", { "mcr-collapsible-heading--collapsed": historyListCollapsed.value }]),
                              role: "button",
                              tabindex: "0",
                              "aria-expanded": !historyListCollapsed.value,
                              "aria-controls": "mcr-history-list-content",
                              onClick: _cache[29] || (_cache[29] = ($event) => historyListCollapsed.value = !historyListCollapsed.value),
                              onKeydown: [
                                _cache[30] || (_cache[30] = _withKeys(_withModifiers(($event) => historyListCollapsed.value = !historyListCollapsed.value, ["prevent"]), ["enter"])),
                                _cache[31] || (_cache[31] = _withKeys(_withModifiers(($event) => historyListCollapsed.value = !historyListCollapsed.value, ["prevent"]), ["space"]))
                              ]
                            }, [
                              _createElementVNode("div", _hoisted_59, [
                                _cache[79] || (_cache[79] = _createElementVNode("div", { class: "mcr-panel__eyebrow" }, "History", -1)),
                                _createElementVNode("div", _hoisted_60, [
                                  _cache[78] || (_cache[78] = _createTextVNode(" 历史封面 ", -1)),
                                  _createVNode(_component_v_icon, {
                                    icon: "mdi-chevron-up",
                                    size: "20",
                                    class: "mcr-collapsible-heading__icon",
                                    "aria-hidden": "true"
                                  }),
                                  backendBusy.value ? (_openBlock(), _createBlock(AsyncStatusDots, {
                                    key: 0,
                                    label: backendBusyLabel.value
                                  }, null, 8, ["label"])) : _createCommentVNode("", true)
                                ])
                              ]),
                              _createVNode(_Transition, { name: "mcr-heading-tools" }, {
                                default: _withCtx(() => [
                                  !historyListCollapsed.value ? (_openBlock(), _createElementBlock("div", {
                                    key: 0,
                                    class: "mcr-history-toolbar",
                                    onClick: _cache[27] || (_cache[27] = _withModifiers(() => {
                                    }, ["stop"])),
                                    onKeydown: _cache[28] || (_cache[28] = _withModifiers(() => {
                                    }, ["stop"]))
                                  }, [
                                    _createVNode(_component_v_btn_toggle, {
                                      modelValue: historyGroupMode.value,
                                      "onUpdate:modelValue": _cache[25] || (_cache[25] = ($event) => historyGroupMode.value = $event),
                                      mandatory: "",
                                      divided: "",
                                      density: "compact",
                                      class: "mcr-toggle mcr-history-toggle",
                                      disabled: controlsLocked.value
                                    }, {
                                      default: _withCtx(() => [
                                        _createVNode(_component_v_btn, {
                                          value: "library",
                                          class: _normalizeClass(["mcr-button mcr-button--ghost mcr-history-mode-button", { "mcr-history-mode-button--active": historyGroupMode.value === "library" }])
                                        }, {
                                          default: _withCtx(() => [..._cache[80] || (_cache[80] = [
                                            _createTextVNode("媒体库", -1)
                                          ])]),
                                          _: 1
                                        }, 8, ["class"]),
                                        _createVNode(_component_v_btn, {
                                          value: "time-machine",
                                          class: _normalizeClass(["mcr-button mcr-button--ghost mcr-history-mode-button", { "mcr-history-mode-button--active": historyGroupMode.value === "time-machine" }])
                                        }, {
                                          default: _withCtx(() => [..._cache[81] || (_cache[81] = [
                                            _createTextVNode("时光机", -1)
                                          ])]),
                                          _: 1
                                        }, 8, ["class"])
                                      ]),
                                      _: 1
                                    }, 8, ["modelValue", "disabled"]),
                                    _createVNode(BlueprintSelect, {
                                      modelValue: historySortMode.value,
                                      "onUpdate:modelValue": _cache[26] || (_cache[26] = ($event) => historySortMode.value = $event),
                                      items: historySortItems,
                                      class: "mcr-control mcr-history-sort",
                                      disabled: controlsLocked.value
                                    }, null, 8, ["modelValue", "disabled"])
                                  ], 32)) : _createCommentVNode("", true)
                                ]),
                                _: 1
                              })
                            ], 42, _hoisted_58),
                            (_openBlock(), _createBlock(_Teleport, { to: "body" }, [
                              pageTab.value === "history-tab" && historyGroupMode.value === "time-machine" && groupedHistory.value.length ? (_openBlock(), _createElementBlock("nav", {
                                key: 0,
                                class: "mcr-time-machine-timeline",
                                "data-mcr-theme": isDark.value ? "dark" : "light",
                                "aria-label": "历史时间轴"
                              }, [
                                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(groupedHistory.value, (group) => {
                                  return _openBlock(), _createElementBlock("button", {
                                    key: group.key,
                                    type: "button",
                                    class: _normalizeClass(["mcr-time-machine-node", { "is-active": activeTimeRecordId.value === group.key }]),
                                    onClick: ($event) => scrollToTimeRecord(group.key)
                                  }, [
                                    activeTimeRecordId.value === group.key ? (_openBlock(), _createElementBlock("span", {
                                      key: 0,
                                      class: "mcr-time-machine-restore",
                                      onClick: _withModifiers(($event) => restoreHistoryBatch(group.key, group.title), ["stop"])
                                    }, "回到此时", 8, _hoisted_63)) : _createCommentVNode("", true),
                                    _cache[82] || (_cache[82] = _createElementVNode("i", { "aria-hidden": "true" }, null, -1)),
                                    _createElementVNode("span", null, _toDisplayString(group.title), 1)
                                  ], 10, _hoisted_62);
                                }), 128))
                              ], 8, _hoisted_61)) : _createCommentVNode("", true)
                            ])),
                            (_openBlock(), _createBlock(_Teleport, { to: "body" }, [
                              historySnapshotDialog.value && selectedHistoryPaths.value.length ? (_openBlock(), _createElementBlock("div", {
                                key: 0,
                                class: "mcr-history-floating-actions",
                                "data-mcr-theme": isDark.value ? "dark" : "light",
                                style: { left: "50%", top: "84px", transform: "translateX(-50%)" },
                                role: "toolbar",
                                "aria-label": "历史封面批量操作"
                              }, [
                                _createElementVNode("span", _hoisted_65, "已选择 " + _toDisplayString(selectedHistoryPaths.value.length), 1),
                                _createElementVNode("button", {
                                  type: "button",
                                  class: "mcr-history-floating-button",
                                  disabled: controlsLocked.value || !history.value.length,
                                  onPointerdown: _cache[32] || (_cache[32] = _withModifiers(() => {
                                  }, ["prevent"])),
                                  onClick: _withModifiers(toggleSelectAllHistory, ["prevent", "stop"])
                                }, _toDisplayString(allHistorySelected.value ? "取消全选" : "全选"), 41, _hoisted_66),
                                _createElementVNode("button", {
                                  type: "button",
                                  class: "mcr-history-floating-button mcr-history-floating-button--primary",
                                  disabled: controlsLocked.value,
                                  onPointerdown: _cache[33] || (_cache[33] = _withModifiers(() => {
                                  }, ["prevent"])),
                                  onClick: _withModifiers(downloadSelectedCoversDirect, ["prevent", "stop"])
                                }, " 直接下载 ", 40, _hoisted_67),
                                _createElementVNode("button", {
                                  type: "button",
                                  class: "mcr-history-floating-button",
                                  disabled: controlsLocked.value,
                                  onPointerdown: _cache[34] || (_cache[34] = _withModifiers(() => {
                                  }, ["prevent"])),
                                  onClick: _withModifiers(downloadSelectedCoversZip, ["prevent", "stop"])
                                }, " 下载 ZIP ", 40, _hoisted_68),
                                _createElementVNode("button", {
                                  type: "button",
                                  class: "mcr-history-floating-button mcr-history-floating-button--primary",
                                  disabled: controlsLocked.value || !selectedHistorySnapshot.value,
                                  onClick: _withModifiers(applySelectedHistorySnapshot, ["prevent", "stop"])
                                }, "应用", 8, _hoisted_69),
                                _createElementVNode("button", {
                                  type: "button",
                                  class: "mcr-history-floating-button mcr-history-floating-button--danger",
                                  disabled: controlsLocked.value,
                                  onPointerdown: _cache[35] || (_cache[35] = _withModifiers(() => {
                                  }, ["prevent"])),
                                  onClick: _withModifiers(deleteSelectedCovers, ["prevent", "stop"])
                                }, " 删除 ", 40, _hoisted_70)
                              ], 8, _hoisted_64)) : _createCommentVNode("", true)
                            ])),
                            _createVNode(_Transition, { name: "mcr-list-collapse" }, {
                              default: _withCtx(() => [
                                _withDirectives(_createElementVNode("div", _hoisted_71, [
                                  history.value.length ? (_openBlock(), _createElementBlock("div", _hoisted_72, [
                                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(groupedHistory.value, (group) => {
                                      return _openBlock(), _createElementBlock("section", {
                                        key: group.key,
                                        class: _normalizeClass(["mcr-history-group", { "mcr-history-group--time-machine": historyGroupMode.value === "time-machine", "is-active": activeTimeRecordId.value === group.key }]),
                                        id: `time-record-${group.key}`
                                      }, [
                                        _createElementVNode("div", _hoisted_74, [
                                          _createElementVNode("div", _hoisted_75, [
                                            _createElementVNode("span", null, _toDisplayString(group.title), 1),
                                            _createElementVNode("strong", null, _toDisplayString(group.items.length), 1)
                                          ])
                                        ]),
                                        historyGroupMode.value === "time-machine" ? (_openBlock(), _createElementBlock("button", {
                                          key: 0,
                                          type: "button",
                                          class: "mcr-time-machine-stack",
                                          "aria-label": `查看 ${group.title} 的全部封面`,
                                          onClick: ($event) => openHistorySnapshot(group)
                                        }, [
                                          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(group.items.slice(0, historyStackLimit.value), (item, index) => {
                                            return _openBlock(), _createElementBlock("span", {
                                              key: item.path,
                                              class: "mcr-time-machine-stack__cover",
                                              style: _normalizeStyle(timeMachineCoverStyle(group.key, index))
                                            }, [
                                              _createElementVNode("img", {
                                                src: item.src || item.url || "",
                                                alt: item.library || item.name,
                                                loading: "lazy"
                                              }, null, 8, _hoisted_77),
                                              _createElementVNode("span", null, _toDisplayString(item.library || item.name), 1)
                                            ], 4);
                                          }), 128)),
                                          group.items.length > historyStackLimit.value ? (_openBlock(), _createElementBlock("span", _hoisted_78, "+" + _toDisplayString(group.items.length - historyStackLimit.value), 1)) : _createCommentVNode("", true)
                                        ], 8, _hoisted_76)) : (_openBlock(), _createBlock(_component_v_row, { key: 1 }, {
                                          default: _withCtx(() => [
                                            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(group.items, (item) => {
                                              return _openBlock(), _createBlock(_component_v_col, {
                                                key: item.path,
                                                cols: "12",
                                                sm: "6",
                                                md: "3"
                                              }, {
                                                default: _withCtx(() => [
                                                  _createVNode(_component_v_card, {
                                                    variant: "flat",
                                                    elevation: "0",
                                                    class: _normalizeClass(["mcr-panel mcr-history-card", { "mcr-history-card--selected": selectedHistoryPaths.value.includes(item.path) }])
                                                  }, {
                                                    default: _withCtx(() => [
                                                      _createElementVNode("div", _hoisted_79, [
                                                        _createVNode(_component_v_img, {
                                                          src: item.src,
                                                          "aspect-ratio": "16/9",
                                                          cover: "",
                                                          class: "mcr-history-card__image"
                                                        }, null, 8, ["src"]),
                                                        _createElementVNode("button", {
                                                          type: "button",
                                                          class: _normalizeClass(["mcr-history-card__check", { "mcr-history-card__check--active": selectedHistoryPaths.value.includes(item.path) }]),
                                                          "aria-pressed": selectedHistoryPaths.value.includes(item.path),
                                                          "aria-label": selectedHistoryPaths.value.includes(item.path) ? "取消选择封面" : "选择封面",
                                                          disabled: controlsLocked.value,
                                                          onClick: _withModifiers(($event) => toggleHistorySelection(item), ["stop"])
                                                        }, [..._cache[83] || (_cache[83] = [
                                                          _createElementVNode("span", {
                                                            class: "mcr-history-card__check-mark",
                                                            "aria-hidden": "true"
                                                          }, null, -1)
                                                        ])], 10, _hoisted_80),
                                                        _createElementVNode("div", _hoisted_81, _toDisplayString(item.library || item.name), 1)
                                                      ]),
                                                      _createVNode(_component_v_card_text, { class: "mcr-panel__body mcr-panel__body--tight" }, {
                                                        default: _withCtx(() => [
                                                          _createElementVNode("div", _hoisted_82, [
                                                            _createElementVNode("span", null, _toDisplayString(item.library || item.name), 1),
                                                            _createElementVNode("span", null, _toDisplayString(item.server || "Unknown"), 1)
                                                          ])
                                                        ]),
                                                        _: 2
                                                      }, 1024)
                                                    ]),
                                                    _: 2
                                                  }, 1032, ["class"])
                                                ]),
                                                _: 2
                                              }, 1024);
                                            }), 128))
                                          ]),
                                          _: 2
                                        }, 1024))
                                      ], 10, _hoisted_73);
                                    }), 128))
                                  ])) : (_openBlock(), _createElementBlock("div", _hoisted_83, [..._cache[84] || (_cache[84] = [
                                    _createTextVNode("还没有可以回到的时间", -1),
                                    _createElementVNode("br", null, null, -1),
                                    _createElementVNode("small", null, "生成并保存封面后，历史记录会显示在这里。", -1)
                                  ])]))
                                ], 512), [
                                  [_vShow, !historyListCollapsed.value]
                                ])
                              ]),
                              _: 1
                            })
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }, 8, ["modelValue"])
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }, 8, ["defaults"])
          ]),
          _: 1
        }),
        _createVNode(_component_v_dialog, {
          modelValue: restoreConfirmDialog.value,
          "onUpdate:modelValue": _cache[38] || (_cache[38] = ($event) => restoreConfirmDialog.value = $event),
          "max-width": "520",
          scrim: isDark.value ? "rgba(0,0,0,.66)" : "rgba(24,32,48,.34)"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              class: "mcr-history-restore-confirm",
              "data-mcr-theme": isDark.value ? "dark" : "light"
            }, {
              default: _withCtx(() => [
                _cache[87] || (_cache[87] = _createElementVNode("h3", null, "确定回到此时吗？", -1)),
                _createElementVNode("p", null, _toDisplayString(pendingHistoryRestore.value?.label), 1),
                _cache[88] || (_cache[88] = _createElementVNode("p", null, "将把该时间保存的封面重新应用到对应服务器媒体库。当前服务器上的封面会被替换，但历史记录不会被删除。", -1)),
                _createElementVNode("footer", null, [
                  _createVNode(_component_v_btn, {
                    class: "mcr-button mcr-button--ghost",
                    onClick: _cache[37] || (_cache[37] = ($event) => restoreConfirmDialog.value = false)
                  }, {
                    default: _withCtx(() => [..._cache[85] || (_cache[85] = [
                      _createTextVNode("取消", -1)
                    ])]),
                    _: 1
                  }),
                  _createVNode(_component_v_btn, {
                    class: "mcr-button mcr-button--primary",
                    loading: Boolean(restoringBatchId.value),
                    onClick: executeHistoryRestore
                  }, {
                    default: _withCtx(() => [..._cache[86] || (_cache[86] = [
                      _createTextVNode("回到此时", -1)
                    ])]),
                    _: 1
                  }, 8, ["loading"])
                ])
              ]),
              _: 1
            }, 8, ["data-mcr-theme"])
          ]),
          _: 1
        }, 8, ["modelValue", "scrim"]),
        _createVNode(_component_v_dialog, {
          modelValue: historySnapshotDialog.value,
          "onUpdate:modelValue": _cache[39] || (_cache[39] = ($event) => historySnapshotDialog.value = $event),
          "max-width": "1120",
          class: "mcr-history-snapshot-dialog",
          scrim: isDark.value ? "rgba(0,0,0,.66)" : "rgba(24,32,48,.34)"
        }, {
          default: _withCtx(() => [
            selectedHistorySnapshot.value ? (_openBlock(), _createBlock(_component_v_card, {
              key: 0,
              class: "mcr-history-snapshot",
              "data-mcr-theme": isDark.value ? "dark" : "light"
            }, {
              default: _withCtx(() => [
                _createElementVNode("header", _hoisted_84, [
                  _createElementVNode("div", null, [
                    _cache[89] || (_cache[89] = _createElementVNode("span", null, "History", -1)),
                    _cache[90] || (_cache[90] = _createElementVNode("h3", null, "此时的封面", -1)),
                    _createElementVNode("p", null, _toDisplayString(selectedHistorySnapshot.value.fullTitle), 1)
                  ]),
                  _createVNode(_component_v_btn, {
                    icon: "mdi-close",
                    variant: "text",
                    "aria-label": "关闭",
                    onClick: closeHistorySnapshot
                  })
                ]),
                _createElementVNode("div", _hoisted_85, [
                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(selectedHistorySnapshot.value.items, (item) => {
                    return _openBlock(), _createElementBlock("article", {
                      key: item.path,
                      class: _normalizeClass(["mcr-history-snapshot__item", { "is-selected": selectedHistoryPaths.value.includes(item.path) }]),
                      role: "checkbox",
                      "aria-checked": selectedHistoryPaths.value.includes(item.path),
                      tabindex: "0",
                      onClick: ($event) => toggleHistorySelection(item),
                      onKeydown: [
                        _withKeys(_withModifiers(($event) => toggleHistorySelection(item), ["prevent"]), ["enter"]),
                        _withKeys(_withModifiers(($event) => toggleHistorySelection(item), ["prevent"]), ["space"])
                      ]
                    }, [
                      _createElementVNode("img", {
                        src: item.src || item.url || "",
                        alt: item.library || item.name,
                        loading: "lazy"
                      }, null, 8, _hoisted_87),
                      _createElementVNode("div", _hoisted_88, [
                        _createElementVNode("span", {
                          title: item.library || item.name
                        }, _toDisplayString(item.library || item.name), 9, _hoisted_89),
                        _createElementVNode("span", {
                          title: item.server || "未知服务器"
                        }, _toDisplayString(item.server || "未知服务器"), 9, _hoisted_90)
                      ])
                    ], 42, _hoisted_86);
                  }), 128))
                ])
              ]),
              _: 1
            }, 8, ["data-mcr-theme"])) : _createCommentVNode("", true)
          ]),
          _: 1
        }, 8, ["modelValue", "scrim"]),
        _createVNode(_component_v_dialog, {
          modelValue: donationDialog.value,
          "onUpdate:modelValue": _cache[42] || (_cache[42] = ($event) => donationDialog.value = $event),
          "max-width": "460",
          class: "mcr-donation-dialog",
          scrim: "rgba(18, 24, 38, 0.42)"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              class: _normalizeClass(["mcr-donation-card", { "mcr-donation-card--dark": isDark.value }])
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, { class: "mcr-donation-card__body" }, {
                  default: _withCtx(() => [
                    donationView.value === "overview" ? (_openBlock(), _createElementBlock("div", _hoisted_91, [
                      _createElementVNode("div", {
                        class: _normalizeClass(["mcr-donation-profile__avatar", { "is-supported": donationAcknowledged.value }])
                      }, [
                        donationAvatarImage.value ? (_openBlock(), _createElementBlock("img", {
                          key: 0,
                          src: donationAvatarImage.value,
                          alt: ""
                        }, null, 8, _hoisted_92)) : (_openBlock(), _createBlock(_component_v_icon, {
                          key: 1,
                          icon: donationAvatarIcon.value,
                          size: "38"
                        }, null, 8, ["icon"])),
                        _createElementVNode("span", _hoisted_93, [
                          _createVNode(_component_v_icon, {
                            icon: "mdi-crown",
                            size: "26"
                          })
                        ])
                      ], 2),
                      _createElementVNode("h3", _hoisted_94, _toDisplayString(donationView.value === "support" ? "感谢您的支持" : "呀哈哈封面工坊"), 1),
                      _createElementVNode("div", _hoisted_95, _toDisplayString(donationView.value === "support" ? "Heartfelt giving" : "使用数据统计"), 1)
                    ])) : (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [
                      _createElementVNode("div", _hoisted_96, [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-heart-outline",
                          size: "30"
                        })
                      ]),
                      _cache[91] || (_cache[91] = _createElementVNode("h3", { class: "mcr-donation-title" }, "感谢您的支持", -1))
                    ], 64)),
                    donationView.value === "overview" ? (_openBlock(), _createElementBlock("div", _hoisted_97, [
                      _createElementVNode("div", _hoisted_98, [
                        _createElementVNode("div", _hoisted_99, [
                          _createElementVNode("span", _hoisted_100, [
                            _createVNode(_component_v_icon, {
                              icon: "mdi-view-grid-outline",
                              size: "20"
                            })
                          ]),
                          _cache[92] || (_cache[92] = _createElementVNode("small", null, "Active", -1))
                        ]),
                        _createElementVNode("strong", null, _toDisplayString(donationStaticSchemeCount.value), 1),
                        _cache[93] || (_cache[93] = _createElementVNode("span", null, "静态方案", -1))
                      ]),
                      _createElementVNode("div", _hoisted_101, [
                        _createElementVNode("div", _hoisted_102, [
                          _createElementVNode("span", _hoisted_103, [
                            _createVNode(_component_v_icon, {
                              icon: "mdi-lightning-bolt-outline",
                              size: "20"
                            })
                          ]),
                          _cache[94] || (_cache[94] = _createElementVNode("small", {
                            class: "mcr-donation-live-dot",
                            "aria-label": "动态方案可用"
                          }, null, -1))
                        ]),
                        _createElementVNode("strong", null, _toDisplayString(donationDynamicSchemeCount.value), 1),
                        _cache[95] || (_cache[95] = _createElementVNode("span", null, "动态方案", -1))
                      ]),
                      _createElementVNode("div", _hoisted_104, [
                        _createElementVNode("div", _hoisted_105, [
                          _createElementVNode("span", _hoisted_106, [
                            _createVNode(_component_v_icon, {
                              icon: "mdi-layers-outline",
                              size: "20"
                            })
                          ])
                        ]),
                        _createElementVNode("strong", null, _toDisplayString(donationHistoryCount.value), 1),
                        _cache[96] || (_cache[96] = _createElementVNode("span", null, "历史封面", -1))
                      ]),
                      _createElementVNode("div", _hoisted_107, [
                        _createElementVNode("div", _hoisted_108, [
                          _createElementVNode("span", _hoisted_109, [
                            _createVNode(_component_v_icon, {
                              icon: "mdi-play-circle-outline",
                              size: "20"
                            })
                          ])
                        ]),
                        _createElementVNode("strong", null, _toDisplayString(donationExecutionCount.value), 1),
                        _cache[97] || (_cache[97] = _createElementVNode("span", null, "执行次数", -1))
                      ])
                    ])) : _createCommentVNode("", true),
                    donationView.value === "support" ? (_openBlock(), _createElementBlock("div", _hoisted_110, [
                      _createElementVNode("img", {
                        class: "mcr-donation-qr__image",
                        src: donationQrImage.value,
                        alt: "赞赏码"
                      }, null, 8, _hoisted_111)
                    ])) : _createCommentVNode("", true),
                    donationView.value === "support" ? (_openBlock(), _createElementBlock("p", _hoisted_112, " 您的慷慨支持是我持续创作的动力。 ")) : _createCommentVNode("", true),
                    _createElementVNode("div", _hoisted_113, [
                      donationView.value === "support" ? (_openBlock(), _createBlock(_component_v_btn, {
                        key: 0,
                        class: "mcr-button mcr-button--ghost mcr-button--dark-neutral mcr-donation-soft-action",
                        onClick: _cache[40] || (_cache[40] = ($event) => donationDialog.value = false)
                      }, {
                        default: _withCtx(() => [..._cache[98] || (_cache[98] = [
                          _createTextVNode(" 下次一定！ ", -1)
                        ])]),
                        _: 1
                      })) : _createCommentVNode("", true),
                      donationView.value === "overview" ? (_openBlock(), _createBlock(_component_v_btn, {
                        key: 1,
                        class: "mcr-button mcr-button--primary mcr-button--apple-primary mcr-donation-continue-support",
                        onClick: _cache[41] || (_cache[41] = ($event) => donationView.value = "support")
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_icon, {
                            class: "mcr-donation-support-heart",
                            icon: "mdi-heart",
                            size: "20"
                          }),
                          _cache[99] || (_cache[99] = _createElementVNode("span", null, "继续支持", -1))
                        ]),
                        _: 1
                      })) : (_openBlock(), _createBlock(_component_v_btn, {
                        key: 2,
                        class: "mcr-button mcr-button--primary mcr-button--apple-primary mcr-donation-support-confirm",
                        onClick: acknowledgeDonation
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_icon, {
                            class: "mcr-donation-support-heart",
                            icon: "mdi-heart",
                            size: "20"
                          }),
                          _cache[100] || (_cache[100] = _createElementVNode("span", null, "已支持", -1))
                        ]),
                        _: 1
                      }))
                    ]),
                    donationView.value === "support" ? (_openBlock(), _createElementBlock("div", _hoisted_114, "HEARTFELT GIVING • LUMINOUS CHARITY")) : _createCommentVNode("", true)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }, 8, ["class"])
          ]),
          _: 1
        }, 8, ["modelValue"]),
        _createCommentVNode("", true),
        _createVNode(ViewportSaveToast, {
          message: editorSaveStatus.value,
          theme: isDark.value ? "dark" : "light"
        }, null, 8, ["message", "theme"])
      ], 8, _hoisted_1);
    };
  }
});

const Page = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-570cb546"]]);

export { Page as default };
