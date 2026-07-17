import { importShared } from './__federation_fn_import-ui-rev-20260718-01.js';

/* eslint-disable no-console */

// Utilities
const {warn} = await importShared('vue');

function consoleWarn(message) {
  warn(`Vuetify: ${message}`);
}
function consoleError(message) {
  warn(`Vuetify error: ${message}`);
}
function deprecate(original, replacement) {
  replacement = Array.isArray(replacement) ? replacement.slice(0, -1).map(s => `'${s}'`).join(', ') + ` or '${replacement.at(-1)}'` : `'${replacement}'`;
  warn(`[Vuetify UPGRADE] '${original}' is deprecated, use ${replacement} instead.`);
}

const IN_BROWSER = typeof window !== 'undefined';
const SUPPORTS_TOUCH = IN_BROWSER && ('ontouchstart' in window || window.navigator.maxTouchPoints > 0);
const SUPPORTS_MATCH_MEDIA = IN_BROWSER && 'matchMedia' in window && typeof window.matchMedia === 'function';
const PREFERS_REDUCED_MOTION = () => SUPPORTS_MATCH_MEDIA && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Utilities
const {camelize,capitalize,Comment,Fragment,isProxy,isReactive,isRef,isVNode,reactive: reactive$4,shallowRef: shallowRef$6,toRaw: toRaw$1,toRef: toRef$6,unref: unref$1,watchEffect: watchEffect$3} = await importShared('vue');
function getNestedValue(obj, path, fallback) {
  const last = path.length - 1;
  if (last < 0) return obj === undefined ? fallback : obj;
  for (let i = 0; i < last; i++) {
    if (obj == null) {
      return fallback;
    }
    obj = obj[path[i]];
  }
  if (obj == null) return fallback;
  return obj[path[last]] === undefined ? fallback : obj[path[last]];
}
function getObjectValueByPath(obj, path, fallback) {
  // credit: http://stackoverflow.com/questions/6491463/accessing-nested-javascript-objects-with-string-key#comment55278413_6491621
  if (obj == null || !path || typeof path !== 'string') return fallback;
  if (obj[path] !== undefined) return obj[path];
  path = path.replace(/\[(\w+)\]/g, '.$1'); // convert indexes to properties
  path = path.replace(/^\./, ''); // strip a leading dot
  return getNestedValue(obj, path.split('.'), fallback);
}
function createRange(length) {
  let start = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 0;
  return Array.from({
    length
  }, (v, k) => start + k);
}
function isObject(obj) {
  return obj !== null && typeof obj === 'object' && !Array.isArray(obj);
}
function isPlainObject(obj) {
  let proto;
  return obj !== null && typeof obj === 'object' && ((proto = Object.getPrototypeOf(obj)) === Object.prototype || proto === null);
}
function refElement(obj) {
  if (obj && '$el' in obj) {
    const el = obj.$el;
    if (el?.nodeType === Node.TEXT_NODE) {
      // Multi-root component, use the first element
      return el.nextElementSibling;
    }
    return el;
  }
  return obj;
}
function has(obj, key) {
  return key.every(k => obj.hasOwnProperty(k));
}
// Array of keys
function pick(obj, paths) {
  const found = {};
  for (const key of paths) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      found[key] = obj[key];
    }
  }
  return found;
}
function clamp(value) {
  let min = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 0;
  let max = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : 1;
  return Math.max(min, Math.min(max, value));
}
function padEnd(str, length) {
  let char = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : '0';
  return str + char.repeat(Math.max(0, length - str.length));
}
function padStart(str, length) {
  let char = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : '0';
  return char.repeat(Math.max(0, length - str.length)) + str;
}
function chunk(str) {
  let size = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 1;
  const chunked = [];
  let index = 0;
  while (index < str.length) {
    chunked.push(str.substr(index, size));
    index += size;
  }
  return chunked;
}
function mergeDeep() {
  let source = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
  let target = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};
  let arrayFn = arguments.length > 2 ? arguments[2] : undefined;
  const out = {};
  for (const key in source) {
    out[key] = source[key];
  }
  for (const key in target) {
    const sourceProperty = source[key];
    const targetProperty = target[key];

    // Only continue deep merging if
    // both properties are plain objects
    if (isPlainObject(sourceProperty) && isPlainObject(targetProperty)) {
      out[key] = mergeDeep(sourceProperty, targetProperty, arrayFn);
      continue;
    }
    if (arrayFn && Array.isArray(sourceProperty) && Array.isArray(targetProperty)) {
      out[key] = arrayFn(sourceProperty, targetProperty);
      continue;
    }
    out[key] = targetProperty;
  }
  return out;
}
function toKebabCase() {
  let str = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : '';
  if (toKebabCase.cache.has(str)) return toKebabCase.cache.get(str);
  const kebab = str.replace(/[^a-z]/gi, '-').replace(/\B([A-Z])/g, '-$1').toLowerCase();
  toKebabCase.cache.set(str, kebab);
  return kebab;
}
toKebabCase.cache = new Map();

/**
 * WCAG 3.0 APCA perceptual contrast algorithm from https://github.com/Myndex/SAPC-APCA
 * @licence https://www.w3.org/Consortium/Legal/2015/copyright-software-and-document
 * @see https://www.w3.org/WAI/GL/task-forces/silver/wiki/Visual_Contrast_of_Text_Subgroup
 */
// Types

// MAGICAL NUMBERS

// sRGB Conversion to Relative Luminance (Y)

// Transfer Curve (aka "Gamma") for sRGB linearization
// Simple power curve vs piecewise described in docs
// Essentially, 2.4 best models actual display
// characteristics in combination with the total method
const mainTRC = 2.4;
const Rco = 0.2126729; // sRGB Red Coefficient (from matrix)
const Gco = 0.7151522; // sRGB Green Coefficient (from matrix)
const Bco = 0.0721750; // sRGB Blue Coefficient (from matrix)

// For Finding Raw SAPC Contrast from Relative Luminance (Y)

// Constants for SAPC Power Curve Exponents
// One pair for normal text, and one for reverse
// These are the "beating heart" of SAPC
const normBG = 0.55;
const normTXT = 0.58;
const revTXT = 0.57;
const revBG = 0.62;

// For Clamping and Scaling Values

const blkThrs = 0.03; // Level that triggers the soft black clamp
const blkClmp = 1.45; // Exponent for the soft black clamp curve
const deltaYmin = 0.0005; // Lint trap
const scaleBoW = 1.25; // Scaling for dark text on light
const scaleWoB = 1.25; // Scaling for light text on dark
const loConThresh = 0.078; // Threshold for new simple offset scale
const loConFactor = 12.82051282051282; // = 1/0.078,
const loConOffset = 0.06; // The simple offset
const loClip = 0.001; // Output clip (lint trap #2)

function APCAcontrast(text, background) {
  // Linearize sRGB
  const Rtxt = (text.r / 255) ** mainTRC;
  const Gtxt = (text.g / 255) ** mainTRC;
  const Btxt = (text.b / 255) ** mainTRC;
  const Rbg = (background.r / 255) ** mainTRC;
  const Gbg = (background.g / 255) ** mainTRC;
  const Bbg = (background.b / 255) ** mainTRC;

  // Apply the standard coefficients and sum to Y
  let Ytxt = Rtxt * Rco + Gtxt * Gco + Btxt * Bco;
  let Ybg = Rbg * Rco + Gbg * Gco + Bbg * Bco;

  // Soft clamp Y when near black.
  // Now clamping all colors to prevent crossover errors
  if (Ytxt <= blkThrs) Ytxt += (blkThrs - Ytxt) ** blkClmp;
  if (Ybg <= blkThrs) Ybg += (blkThrs - Ybg) ** blkClmp;

  // Return 0 Early for extremely low ∆Y (lint trap #1)
  if (Math.abs(Ybg - Ytxt) < deltaYmin) return 0.0;

  // SAPC CONTRAST

  let outputContrast; // For weighted final values
  if (Ybg > Ytxt) {
    // For normal polarity, black text on white
    // Calculate the SAPC contrast value and scale

    const SAPC = (Ybg ** normBG - Ytxt ** normTXT) * scaleBoW;

    // NEW! SAPC SmoothScale™
    // Low Contrast Smooth Scale Rollout to prevent polarity reversal
    // and also a low clip for very low contrasts (lint trap #2)
    // much of this is for very low contrasts, less than 10
    // therefore for most reversing needs, only loConOffset is important
    outputContrast = SAPC < loClip ? 0.0 : SAPC < loConThresh ? SAPC - SAPC * loConFactor * loConOffset : SAPC - loConOffset;
  } else {
    // For reverse polarity, light text on dark
    // WoB should always return negative value.

    const SAPC = (Ybg ** revBG - Ytxt ** revTXT) * scaleWoB;
    outputContrast = SAPC > -loClip ? 0.0 : SAPC > -loConThresh ? SAPC - SAPC * loConFactor * loConOffset : SAPC + loConOffset;
  }
  return outputContrast * 100;
}

// Types

const delta = 0.20689655172413793; // 6÷29

const cielabForwardTransform = t => t > delta ** 3 ? Math.cbrt(t) : t / (3 * delta ** 2) + 4 / 29;
const cielabReverseTransform = t => t > delta ? t ** 3 : 3 * delta ** 2 * (t - 4 / 29);
function fromXYZ$1(xyz) {
  const transform = cielabForwardTransform;
  const transformedY = transform(xyz[1]);
  return [116 * transformedY - 16, 500 * (transform(xyz[0] / 0.95047) - transformedY), 200 * (transformedY - transform(xyz[2] / 1.08883))];
}
function toXYZ$1(lab) {
  const transform = cielabReverseTransform;
  const Ln = (lab[0] + 16) / 116;
  return [transform(Ln + lab[1] / 500) * 0.95047, transform(Ln), transform(Ln - lab[2] / 200) * 1.08883];
}

// Utilities
// For converting XYZ to sRGB
const srgbForwardMatrix = [[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.204, 1.0570]];

// Forward gamma adjust
const srgbForwardTransform = C => C <= 0.0031308 ? C * 12.92 : 1.055 * C ** (1 / 2.4) - 0.055;

// For converting sRGB to XYZ
const srgbReverseMatrix = [[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]];

// Reverse gamma adjust
const srgbReverseTransform = C => C <= 0.04045 ? C / 12.92 : ((C + 0.055) / 1.055) ** 2.4;
function fromXYZ(xyz) {
  const rgb = Array(3);
  const transform = srgbForwardTransform;
  const matrix = srgbForwardMatrix;

  // Matrix transform, then gamma adjustment
  for (let i = 0; i < 3; ++i) {
    // Rescale back to [0, 255]
    rgb[i] = Math.round(clamp(transform(matrix[i][0] * xyz[0] + matrix[i][1] * xyz[1] + matrix[i][2] * xyz[2])) * 255);
  }
  return {
    r: rgb[0],
    g: rgb[1],
    b: rgb[2]
  };
}
function toXYZ(_ref) {
  let {
    r,
    g,
    b
  } = _ref;
  const xyz = [0, 0, 0];
  const transform = srgbReverseTransform;
  const matrix = srgbReverseMatrix;

  // Rescale from [0, 255] to [0, 1] then adjust sRGB gamma to linear RGB
  r = transform(r / 255);
  g = transform(g / 255);
  b = transform(b / 255);

  // Matrix color space transform
  for (let i = 0; i < 3; ++i) {
    xyz[i] = matrix[i][0] * r + matrix[i][1] * g + matrix[i][2] * b;
  }
  return xyz;
}

// Utilities
const cssColorRe = /^(?<fn>(?:rgb|hsl)a?)\((?<values>.+)\)/;
const mappers = {
  rgb: (r, g, b, a) => ({
    r,
    g,
    b,
    a
  }),
  rgba: (r, g, b, a) => ({
    r,
    g,
    b,
    a
  }),
  hsl: (h, s, l, a) => HSLtoRGB({
    h,
    s,
    l,
    a
  }),
  hsla: (h, s, l, a) => HSLtoRGB({
    h,
    s,
    l,
    a
  }),
  hsv: (h, s, v, a) => HSVtoRGB({
    h,
    s,
    v,
    a
  }),
  hsva: (h, s, v, a) => HSVtoRGB({
    h,
    s,
    v,
    a
  })
};
function parseColor(color) {
  if (typeof color === 'number') {
    if (isNaN(color) || color < 0 || color > 0xFFFFFF) {
      // int can't have opacity
      consoleWarn(`'${color}' is not a valid hex color`);
    }
    return {
      r: (color & 0xFF0000) >> 16,
      g: (color & 0xFF00) >> 8,
      b: color & 0xFF
    };
  } else if (typeof color === 'string' && cssColorRe.test(color)) {
    const {
      groups
    } = color.match(cssColorRe);
    const {
      fn,
      values
    } = groups;
    const realValues = values.split(/,\s*|\s*\/\s*|\s+/).map((v, i) => {
      if (v.endsWith('%') ||
      // unitless slv are %
      i > 0 && i < 3 && ['hsl', 'hsla', 'hsv', 'hsva'].includes(fn)) {
        return parseFloat(v) / 100;
      } else {
        return parseFloat(v);
      }
    });
    return mappers[fn](...realValues);
  } else if (typeof color === 'string') {
    let hex = color.startsWith('#') ? color.slice(1) : color;
    if ([3, 4].includes(hex.length)) {
      hex = hex.split('').map(char => char + char).join('');
    } else if (![6, 8].includes(hex.length)) {
      consoleWarn(`'${color}' is not a valid hex(a) color`);
    }
    const int = parseInt(hex, 16);
    if (isNaN(int) || int < 0 || int > 0xFFFFFFFF) {
      consoleWarn(`'${color}' is not a valid hex(a) color`);
    }
    return HexToRGB(hex);
  } else if (typeof color === 'object') {
    if (has(color, ['r', 'g', 'b'])) {
      return color;
    } else if (has(color, ['h', 's', 'l'])) {
      return HSVtoRGB(HSLtoHSV(color));
    } else if (has(color, ['h', 's', 'v'])) {
      return HSVtoRGB(color);
    }
  }
  throw new TypeError(`Invalid color: ${color == null ? color : String(color) || color.constructor.name}\nExpected #hex, #hexa, rgb(), rgba(), hsl(), hsla(), object or number`);
}

/** Converts HSVA to RGBA. Based on formula from https://en.wikipedia.org/wiki/HSL_and_HSV */
function HSVtoRGB(hsva) {
  const {
    h,
    s,
    v,
    a
  } = hsva;
  const f = n => {
    const k = (n + h / 60) % 6;
    return v - v * s * Math.max(Math.min(k, 4 - k, 1), 0);
  };
  const rgb = [f(5), f(3), f(1)].map(v => Math.round(v * 255));
  return {
    r: rgb[0],
    g: rgb[1],
    b: rgb[2],
    a
  };
}
function HSLtoRGB(hsla) {
  return HSVtoRGB(HSLtoHSV(hsla));
}
function HSLtoHSV(hsl) {
  const {
    h,
    s,
    l,
    a
  } = hsl;
  const v = l + s * Math.min(l, 1 - l);
  const sprime = v === 0 ? 0 : 2 - 2 * l / v;
  return {
    h,
    s: sprime,
    v,
    a
  };
}
function toHex(v) {
  const h = Math.round(v).toString(16);
  return ('00'.substr(0, 2 - h.length) + h).toUpperCase();
}
function RGBtoHex(_ref2) {
  let {
    r,
    g,
    b,
    a
  } = _ref2;
  return `#${[toHex(r), toHex(g), toHex(b), a !== undefined ? toHex(Math.round(a * 255)) : ''].join('')}`;
}
function HexToRGB(hex) {
  hex = parseHex(hex);
  let [r, g, b, a] = chunk(hex, 2).map(c => parseInt(c, 16));
  a = a === undefined ? a : a / 255;
  return {
    r,
    g,
    b,
    a
  };
}
function parseHex(hex) {
  if (hex.startsWith('#')) {
    hex = hex.slice(1);
  }
  hex = hex.replace(/([^0-9a-f])/gi, 'F');
  if (hex.length === 3 || hex.length === 4) {
    hex = hex.split('').map(x => x + x).join('');
  }
  if (hex.length !== 6) {
    hex = padEnd(padEnd(hex, 6), 8, 'F');
  }
  return hex;
}
function lighten(value, amount) {
  const lab = fromXYZ$1(toXYZ(value));
  lab[0] = lab[0] + amount * 10;
  return fromXYZ(toXYZ$1(lab));
}
function darken(value, amount) {
  const lab = fromXYZ$1(toXYZ(value));
  lab[0] = lab[0] - amount * 10;
  return fromXYZ(toXYZ$1(lab));
}

/**
 * Calculate the relative luminance of a given color
 * @see https://www.w3.org/TR/WCAG20/#relativeluminancedef
 */
function getLuma(color) {
  const rgb = parseColor(color);
  return toXYZ(rgb)[1];
}
function getForeground(color) {
  const blackContrast = Math.abs(APCAcontrast(parseColor(0), parseColor(color)));
  const whiteContrast = Math.abs(APCAcontrast(parseColor(0xffffff), parseColor(color)));

  // TODO: warn about poor color selections
  // const contrastAsText = Math.abs(APCAcontrast(colorVal, colorToInt(theme.colors.background)))
  // const minContrast = Math.max(blackContrast, whiteContrast)
  // if (minContrast < 60) {
  //   consoleInfo(`${key} theme color ${color} has poor contrast (${minContrast.toFixed()}%)`)
  // } else if (contrastAsText < 60 && !['background', 'surface'].includes(color)) {
  //   consoleInfo(`${key} theme color ${color} has poor contrast as text (${contrastAsText.toFixed()}%)`)
  // }

  // Prefer white text if both have an acceptable contrast ratio
  return whiteContrast > Math.min(blackContrast, 50) ? '#fff' : '#000';
}

// Types
// eslint-disable-line vue/prefer-import-from-vue

/**
 * Creates a factory function for props definitions.
 * This is used to define props in a composable then override
 * default values in an implementing component.
 *
 * @example Simplified signature
 * (props: Props) => (defaults?: Record<keyof props, any>) => Props
 *
 * @example Usage
 * const makeProps = propsFactory({
 *   foo: String,
 * })
 *
 * defineComponent({
 *   props: {
 *     ...makeProps({
 *       foo: 'a',
 *     }),
 *   },
 *   setup (props) {
 *     // would be "string | undefined", now "string" because a default has been provided
 *     props.foo
 *   },
 * }
 */

function propsFactory(props, source) {
  return defaults => {
    return Object.keys(props).reduce((obj, prop) => {
      const isObjectDefinition = typeof props[prop] === 'object' && props[prop] != null && !Array.isArray(props[prop]);
      const definition = isObjectDefinition ? props[prop] : {
        type: props[prop]
      };
      if (defaults && prop in defaults) {
        obj[prop] = {
          ...definition,
          default: defaults[prop]
        };
      } else {
        obj[prop] = definition;
      }
      if (source && !obj[prop].source) {
        obj[prop].source = source;
      }
      return obj;
    }, {});
  };
}

/**
 * Like `Partial<T>` but doesn't care what the value is
 */

// Copied from Vue

// Utilities
const {getCurrentInstance:_getCurrentInstance} = await importShared('vue');
function getCurrentInstance(name, message) {
  const vm = _getCurrentInstance();
  if (!vm) {
    throw new Error(`[Vuetify] ${name} ${'must be called from inside a setup function'}`);
  }
  return vm;
}
function getCurrentInstanceName() {
  let name = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : 'composables';
  const vm = getCurrentInstance(name).type;
  return toKebabCase(vm?.aliasName || vm?.name);
}

// Utilities
function injectSelf(key) {
  let vm = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : getCurrentInstance('injectSelf');
  const {
    provides
  } = vm;
  if (provides && key in provides) {
    // TS doesn't allow symbol as index type
    return provides[key];
  }
  return undefined;
}

// Utilities
const {computed: computed$8,inject: inject$8,provide: provide$3,ref: ref$5,shallowRef: shallowRef$5,unref,watchEffect: watchEffect$2} = await importShared('vue');
const DefaultsSymbol = Symbol.for('vuetify:defaults');
function createDefaults(options) {
  return ref$5(options);
}
function injectDefaults() {
  const defaults = inject$8(DefaultsSymbol);
  if (!defaults) throw new Error('[Vuetify] Could not find defaults instance');
  return defaults;
}
function propIsDefined(vnode, prop) {
  return vnode.props && (typeof vnode.props[prop] !== 'undefined' || typeof vnode.props[toKebabCase(prop)] !== 'undefined');
}
function internalUseDefaults() {
  let props = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
  let name = arguments.length > 1 ? arguments[1] : undefined;
  let defaults = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : injectDefaults();
  const vm = getCurrentInstance('useDefaults');
  name = name ?? vm.type.name ?? vm.type.__name;
  if (!name) {
    throw new Error('[Vuetify] Could not determine component name');
  }
  const componentDefaults = computed$8(() => defaults.value?.[props._as ?? name]);
  const _props = new Proxy(props, {
    get(target, prop) {
      const propValue = Reflect.get(target, prop);
      if (prop === 'class' || prop === 'style') {
        return [componentDefaults.value?.[prop], propValue].filter(v => v != null);
      }
      if (propIsDefined(vm.vnode, prop)) return propValue;
      const _componentDefault = componentDefaults.value?.[prop];
      if (_componentDefault !== undefined) return _componentDefault;
      const _globalDefault = defaults.value?.global?.[prop];
      if (_globalDefault !== undefined) return _globalDefault;
      return propValue;
    }
  });
  const _subcomponentDefaults = shallowRef$5();
  watchEffect$2(() => {
    if (componentDefaults.value) {
      const subComponents = Object.entries(componentDefaults.value).filter(_ref => {
        let [key] = _ref;
        return key.startsWith(key[0].toUpperCase());
      });
      _subcomponentDefaults.value = subComponents.length ? Object.fromEntries(subComponents) : undefined;
    } else {
      _subcomponentDefaults.value = undefined;
    }
  });
  function provideSubDefaults() {
    const injected = injectSelf(DefaultsSymbol, vm);
    provide$3(DefaultsSymbol, computed$8(() => {
      return _subcomponentDefaults.value ? mergeDeep(injected?.value ?? {}, _subcomponentDefaults.value) : injected?.value;
    }));
  }
  return {
    props: _props,
    provideSubDefaults
  };
}
function useDefaults() {
  let props = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
  let name = arguments.length > 1 ? arguments[1] : undefined;
  const {
    props: _props,
    provideSubDefaults
  } = internalUseDefaults(props, name);
  provideSubDefaults();
  return _props;
}

const {defineComponent:_defineComponent} = await importShared('vue');
// No props
// Object Props
// Implementation
function defineComponent(options) {
  options._setup = options._setup ?? options.setup;
  if (!options.name) {
    consoleWarn('The component is missing an explicit name, unable to generate default prop value');
    return options;
  }
  if (options._setup) {
    options.props = propsFactory(options.props ?? {}, options.name)();
    const propKeys = Object.keys(options.props).filter(key => key !== 'class' && key !== 'style');
    options.filterProps = function filterProps(props) {
      return pick(props, propKeys);
    };
    options.props._as = String;
    options.setup = function setup(props, ctx) {
      const defaults = injectDefaults();

      // Skip props proxy if defaults are not provided
      if (!defaults.value) return options._setup(props, ctx);
      const {
        props: _props,
        provideSubDefaults
      } = internalUseDefaults(props, props._as ?? options.name, defaults);
      const setupBindings = options._setup(_props, ctx);
      provideSubDefaults();
      return setupBindings;
    };
  }
  return options;
}

// No argument - simple default slot

// Generic constructor argument - generic props and slots

// Slots argument - simple slots

// Implementation
function genericComponent() {
  let exposeDefaults = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : true;
  return options => (exposeDefaults ? defineComponent : _defineComponent)(options);
}

// Adds a filterProps method to the component options

// https://github.com/vuejs/core/pull/10557

// not a vue Component

// Utilities
const {computed: computed$7,shallowRef: shallowRef$4,toValue: toValue$2,watch: watch$6} = await importShared('vue');

const easingPatterns = {
  linear: t => t,
  easeInQuad: t => t ** 2,
  easeOutQuad: t => t * (2 - t),
  easeInOutQuad: t => t < 0.5 ? 2 * t ** 2 : -1 + (4 - 2 * t) * t,
  easeInCubic: t => t ** 3,
  easeOutCubic: t => --t ** 3 + 1,
  easeInOutCubic: t => t < 0.5 ? 4 * t ** 3 : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1,
  easeInQuart: t => t ** 4,
  easeOutQuart: t => 1 - --t ** 4,
  easeInOutQuart: t => t < 0.5 ? 8 * t ** 4 : 1 - 8 * --t ** 4,
  easeInQuint: t => t ** 5,
  easeOutQuint: t => 1 + --t ** 5,
  easeInOutQuint: t => t < 0.5 ? 16 * t ** 5 : 1 + 16 * --t ** 5,
  instant: t => 1
};

// Utilities
const {computed: computed$6,inject: inject$7,toValue: toValue$1,createVNode:_createVNode,createElementVNode:_createElementVNode,mergeProps:_mergeProps,normalizeClass:_normalizeClass} = await importShared('vue');
const IconValue = [String, Function, Object, Array];
const IconSymbol = Symbol.for('vuetify:icons');
const makeIconProps = propsFactory({
  icon: {
    type: IconValue
  },
  // Could not remove this and use makeTagProps, types complained because it is not required
  tag: {
    type: [String, Object, Function],
    required: true
  }
}, 'icon');
genericComponent()({
  name: 'VComponentIcon',
  props: makeIconProps(),
  setup(props, _ref) {
    let {
      slots
    } = _ref;
    return () => {
      const Icon = props.icon;
      return _createVNode(props.tag, null, {
        default: () => [props.icon ? _createVNode(Icon, null, null) : slots.default?.()]
      });
    };
  }
});
const VSvgIcon = defineComponent({
  name: 'VSvgIcon',
  inheritAttrs: false,
  props: makeIconProps(),
  setup(props, _ref2) {
    let {
      attrs
    } = _ref2;
    return () => {
      return _createVNode(props.tag, _mergeProps(attrs, {
        "style": null
      }), {
        default: () => [_createElementVNode("svg", {
          "class": "v-icon__svg",
          "xmlns": "http://www.w3.org/2000/svg",
          "viewBox": "0 0 24 24",
          "role": "img",
          "aria-hidden": "true"
        }, [Array.isArray(props.icon) ? props.icon.map(path => Array.isArray(path) ? _createElementVNode("path", {
          "d": path[0],
          "fill-opacity": path[1]
        }, null) : _createElementVNode("path", {
          "d": path
        }, null)) : _createElementVNode("path", {
          "d": props.icon
        }, null)])]
      });
    };
  }
});
defineComponent({
  name: 'VLigatureIcon',
  props: makeIconProps(),
  setup(props) {
    return () => {
      return _createVNode(props.tag, null, {
        default: () => [props.icon]
      });
    };
  }
});
const VClassIcon = defineComponent({
  name: 'VClassIcon',
  props: makeIconProps(),
  setup(props) {
    return () => {
      return _createVNode(props.tag, {
        "class": _normalizeClass(props.icon)
      }, null);
    };
  }
});

const {h} = await importShared('vue');


// Types

const aliases = {
  collapse: 'mdi-chevron-up',
  complete: 'mdi-check',
  cancel: 'mdi-close-circle',
  close: 'mdi-close',
  delete: 'mdi-close-circle',
  // delete (e.g. v-chip close)
  clear: 'mdi-close-circle',
  success: 'mdi-check-circle',
  info: 'mdi-information',
  warning: 'mdi-alert-circle',
  error: 'mdi-close-circle',
  prev: 'mdi-chevron-left',
  next: 'mdi-chevron-right',
  checkboxOn: 'mdi-checkbox-marked',
  checkboxOff: 'mdi-checkbox-blank-outline',
  checkboxIndeterminate: 'mdi-minus-box',
  delimiter: 'mdi-circle',
  // for carousel
  sortAsc: 'mdi-arrow-up',
  sortDesc: 'mdi-arrow-down',
  expand: 'mdi-chevron-down',
  menu: 'mdi-menu',
  subgroup: 'mdi-menu-down',
  dropdown: 'mdi-menu-down',
  radioOn: 'mdi-radiobox-marked',
  radioOff: 'mdi-radiobox-blank',
  edit: 'mdi-pencil',
  ratingEmpty: 'mdi-star-outline',
  ratingFull: 'mdi-star',
  ratingHalf: 'mdi-star-half-full',
  loading: 'mdi-cached',
  first: 'mdi-page-first',
  last: 'mdi-page-last',
  unfold: 'mdi-unfold-more-horizontal',
  file: 'mdi-paperclip',
  plus: 'mdi-plus',
  minus: 'mdi-minus',
  calendar: 'mdi-calendar',
  treeviewCollapse: 'mdi-menu-down',
  treeviewExpand: 'mdi-menu-right',
  tableGroupCollapse: 'mdi-chevron-down',
  tableGroupExpand: 'mdi-chevron-right',
  eyeDropper: 'mdi-eyedropper',
  upload: 'mdi-cloud-upload',
  color: 'mdi-palette',
  command: 'mdi-apple-keyboard-command',
  ctrl: 'mdi-apple-keyboard-control',
  space: 'mdi-keyboard-space',
  shift: 'mdi-apple-keyboard-shift',
  alt: 'mdi-apple-keyboard-option',
  enter: 'mdi-keyboard-return',
  arrowup: 'mdi-arrow-up',
  arrowdown: 'mdi-arrow-down',
  arrowleft: 'mdi-arrow-left',
  arrowright: 'mdi-arrow-right',
  backspace: 'mdi-backspace',
  play: 'mdi-play',
  pause: 'mdi-pause',
  fullscreen: 'mdi-fullscreen',
  fullscreenExit: 'mdi-fullscreen-exit',
  volumeHigh: 'mdi-volume-high',
  volumeMedium: 'mdi-volume-medium',
  volumeLow: 'mdi-volume-low',
  volumeOff: 'mdi-volume-variant-off',
  search: 'mdi-magnify'
};
const mdi = {
  // Not using mergeProps here, functional components merge props by default (?)
  component: props => h(VClassIcon, {
    ...props,
    class: 'mdi'
  })
};

// Composables
function genDefaults$3() {
  return {
    svg: {
      component: VSvgIcon
    },
    class: {
      component: VClassIcon
    }
  };
}
function createIcons(options) {
  const sets = genDefaults$3();
  const defaultSet = options?.defaultSet ?? 'mdi';
  if (defaultSet === 'mdi' && !sets.mdi) {
    sets.mdi = mdi;
  }
  return mergeDeep({
    defaultSet,
    sets,
    aliases: {
      ...aliases,
      /* eslint-disable max-len */
      vuetify: ['M8.2241 14.2009L12 21L22 3H14.4459L8.2241 14.2009Z', ['M7.26303 12.4733L7.00113 12L2 3H12.5261C12.5261 3 12.5261 3 12.5261 3L7.26303 12.4733Z', 0.6]],
      'vuetify-outline': 'svg:M7.26 12.47 12.53 3H2L7.26 12.47ZM14.45 3 8.22 14.2 12 21 22 3H14.45ZM18.6 5 12 16.88 10.51 14.2 15.62 5ZM7.26 8.35 5.4 5H9.13L7.26 8.35Z',
      'vuetify-play': ['m6.376 13.184-4.11-7.192C1.505 4.66 2.467 3 4.003 3h8.532l-.953 1.576-.006.01-.396.677c-.429.732-.214 1.507.194 2.015.404.503 1.092.878 1.869.806a3.72 3.72 0 0 1 1.005.022c.276.053.434.143.523.237.138.146.38.635-.25 2.09-.893 1.63-1.553 1.722-1.847 1.677-.213-.033-.468-.158-.756-.406a4.95 4.95 0 0 1-.8-.927c-.39-.564-1.04-.84-1.66-.846-.625-.006-1.316.27-1.693.921l-.478.826-.911 1.506Z', ['M9.093 11.552c.046-.079.144-.15.32-.148a.53.53 0 0 1 .43.207c.285.414.636.847 1.046 1.2.405.35.914.662 1.516.754 1.334.205 2.502-.698 3.48-2.495l.014-.028.013-.03c.687-1.574.774-2.852-.005-3.675-.37-.391-.861-.586-1.333-.676a5.243 5.243 0 0 0-1.447-.044c-.173.016-.393-.073-.54-.257-.145-.18-.127-.316-.082-.392l.393-.672L14.287 3h5.71c1.536 0 2.499 1.659 1.737 2.992l-7.997 13.996c-.768 1.344-2.706 1.344-3.473 0l-3.037-5.314 1.377-2.278.004-.006.004-.007.481-.831Z', 0.6]]
      /* eslint-enable max-len */
    }
  }, options);
}

// Utilities
const {effectScope: effectScope$1,onScopeDispose: onScopeDispose$3,watch: watch$5} = await importShared('vue');


// Types

function useToggleScope(source, fn) {
  let scope;
  function start() {
    scope = effectScope$1();
    scope.run(() => fn.length ? fn(() => {
      scope?.stop();
      start();
    }) : fn());
  }
  watch$5(source, active => {
    if (active && !scope) {
      start();
    } else if (!active) {
      scope?.stop();
      scope = undefined;
    }
  }, {
    immediate: true
  });
  onScopeDispose$3(() => {
    scope?.stop();
  });
}

const {computed: computed$5,ref: ref$4,toRaw,watch: watch$4} = await importShared('vue');
// Composables
function useProxiedModel(props, prop, defaultValue) {
  let transformIn = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : v => v;
  let transformOut = arguments.length > 4 && arguments[4] !== undefined ? arguments[4] : v => v;
  const vm = getCurrentInstance('useProxiedModel');
  const internal = ref$4(props[prop] !== undefined ? props[prop] : defaultValue);
  const kebabProp = toKebabCase(prop);
  const checkKebab = kebabProp !== prop;
  const isControlled = checkKebab ? computed$5(() => {
    void props[prop];
    return !!((vm.vnode.props?.hasOwnProperty(prop) || vm.vnode.props?.hasOwnProperty(kebabProp)) && (vm.vnode.props?.hasOwnProperty(`onUpdate:${prop}`) || vm.vnode.props?.hasOwnProperty(`onUpdate:${kebabProp}`)));
  }) : computed$5(() => {
    void props[prop];
    return !!(vm.vnode.props?.hasOwnProperty(prop) && vm.vnode.props?.hasOwnProperty(`onUpdate:${prop}`));
  });
  useToggleScope(() => !isControlled.value, () => {
    watch$4(() => props[prop], val => {
      internal.value = val;
    });
  });
  const model = computed$5({
    get() {
      const externalValue = props[prop];
      return transformIn(isControlled.value ? externalValue : internal.value);
    },
    set(internalValue) {
      const newValue = transformOut(internalValue);
      const value = toRaw(isControlled.value ? props[prop] : internal.value);
      if (value === newValue || transformIn(value) === internalValue) {
        return;
      }
      internal.value = newValue;
      vm?.emit(`update:${prop}`, newValue);
    }
  });
  Object.defineProperty(model, 'externalValue', {
    get: () => isControlled.value ? props[prop] : internal.value
  });
  return model;
}

const en = {
  badge: 'Badge',
  open: 'Open',
  close: 'Close',
  dismiss: 'Dismiss',
  confirmEdit: {
    ok: 'OK',
    cancel: 'Cancel'
  },
  dataIterator: {
    noResultsText: 'No matching records found',
    loadingText: 'Loading items...'
  },
  dataTable: {
    itemsPerPageText: 'Rows per page:',
    ariaLabel: {
      sortDescending: 'Sorted descending.',
      sortAscending: 'Sorted ascending.',
      sortNone: 'Not sorted.',
      activateNone: 'Activate to remove sorting.',
      activateDescending: 'Activate to sort descending.',
      activateAscending: 'Activate to sort ascending.'
    },
    sortBy: 'Sort by'
  },
  dataFooter: {
    itemsPerPageText: 'Items per page:',
    itemsPerPageAll: 'All',
    nextPage: 'Next page',
    prevPage: 'Previous page',
    firstPage: 'First page',
    lastPage: 'Last page',
    pageText: '{0}-{1} of {2}'
  },
  dateRangeInput: {
    divider: 'to'
  },
  datePicker: {
    itemsSelected: '{0} selected',
    range: {
      title: 'Select dates',
      header: 'Enter dates'
    },
    title: 'Select date',
    header: 'Enter date',
    input: {
      placeholder: 'Enter date'
    },
    ariaLabel: {
      previousMonth: 'Previous month',
      nextMonth: 'Next month',
      selectYear: 'Select year',
      previousYear: 'Previous year',
      nextYear: 'Next year',
      selectMonth: 'Select month',
      selectDate: '{0}',
      // Full date format
      currentDate: 'Today, {0}'
    }
  },
  noDataText: 'No data available',
  carousel: {
    prev: 'Previous visual',
    next: 'Next visual',
    ariaLabel: {
      delimiter: 'Carousel slide {0} of {1}'
    }
  },
  calendar: {
    moreEvents: '{0} more',
    today: 'Today'
  },
  input: {
    clear: 'Clear {0}',
    prependAction: '{0} prepended action',
    appendAction: '{0} appended action',
    otp: 'Please enter OTP character {0}'
  },
  fileInput: {
    counter: '{0} files',
    counterSize: '{0} files ({1} in total)'
  },
  fileUpload: {
    title: 'Drag and drop files here',
    divider: 'or',
    browse: 'Browse Files'
  },
  timePicker: {
    am: 'AM',
    pm: 'PM',
    title: 'Select Time',
    hour: 'Hour',
    minute: 'Minute',
    second: 'Second',
    notAllowed: 'Value is not allowed'
  },
  pagination: {
    ariaLabel: {
      root: 'Pagination Navigation',
      next: 'Next page',
      previous: 'Previous page',
      page: 'Go to page {0}',
      currentPage: 'Page {0}, Current page',
      first: 'First page',
      last: 'Last page'
    }
  },
  stepper: {
    next: 'Next',
    prev: 'Previous'
  },
  rating: {
    ariaLabel: {
      item: 'Rating {0} of {1}'
    }
  },
  loading: 'Loading...',
  infiniteScroll: {
    loadMore: 'Load more',
    empty: 'No more'
  },
  rules: {
    required: 'This field is required',
    email: 'Please enter a valid email',
    number: 'This field can only contain numbers',
    integer: 'This field can only contain integer values',
    capital: 'This field can only contain uppercase letters',
    maxLength: 'You must enter a maximum of {0} characters',
    minLength: 'You must enter a minimum of {0} characters',
    strictLength: 'The length of the entered field is invalid',
    exclude: 'The {0} character is not allowed',
    notEmpty: 'Please choose at least one value',
    pattern: 'Invalid format'
  },
  command: {
    search: 'Type a command or search...'
  },
  hotkey: {
    then: 'then',
    ctrl: 'Ctrl',
    command: 'Command',
    space: 'Space',
    shift: 'Shift',
    alt: 'Alt',
    enter: 'Enter',
    escape: 'Escape',
    upArrow: 'Up Arrow',
    downArrow: 'Down Arrow',
    leftArrow: 'Left Arrow',
    rightArrow: 'Right Arrow',
    backspace: 'Backspace',
    option: 'Option',
    plus: 'plus',
    shortcut: 'Keyboard shortcut: {0}',
    or: 'or'
  },
  video: {
    play: 'Play',
    pause: 'Pause',
    seek: 'Seek',
    volume: 'Volume',
    showVolume: 'Show volume control',
    mute: 'Mute',
    unmute: 'Unmute',
    enterFullscreen: 'Full screen',
    exitFullscreen: 'Exit full screen'
  },
  colorPicker: {
    ariaLabel: {
      eyedropper: 'Select color with eyedropper',
      hueSlider: 'Hue',
      alphaSlider: 'Alpha',
      redInput: 'Red value',
      greenInput: 'Green value',
      blueInput: 'Blue value',
      alphaInput: 'Alpha value',
      hueInput: 'Hue value',
      saturationInput: 'Saturation value',
      lightnessInput: 'Lightness value',
      hexInput: 'HEX value',
      hexaInput: 'HEX with alpha value',
      changeFormat: 'Change color format'
    }
  }
};

const {ref: ref$3,shallowRef: shallowRef$3,toRef: toRef$5,watch: watch$3} = await importShared('vue');
const LANG_PREFIX = '$vuetify.';
const replace = (str, params) => {
  return str.replace(/\{(\d+)\}/g, (match, index) => {
    return String(params[Number(index)]);
  });
};
const createTranslateFunction = (current, fallback, messages) => {
  return function (key) {
    for (var _len = arguments.length, params = new Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
      params[_key - 1] = arguments[_key];
    }
    if (!key.startsWith(LANG_PREFIX)) {
      return replace(key, params);
    }
    const shortKey = key.replace(LANG_PREFIX, '');
    const currentLocale = current.value && messages.value[current.value];
    const fallbackLocale = fallback.value && messages.value[fallback.value];
    let str = getObjectValueByPath(currentLocale, shortKey, null);
    if (!str) {
      consoleWarn(`Translation key "${key}" not found in "${current.value}", trying fallback locale`);
      str = getObjectValueByPath(fallbackLocale, shortKey, null);
    }
    if (!str) {
      consoleError(`Translation key "${key}" not found in fallback`);
      str = key;
    }
    if (typeof str !== 'string') {
      consoleError(`Translation key "${key}" has a non-string value`);
      str = key;
    }
    return replace(str, params);
  };
};
function createNumberFunction(current, fallback) {
  return (value, options) => {
    const numberFormat = new Intl.NumberFormat([current.value, fallback.value], options);
    return numberFormat.format(value);
  };
}
function inferDecimalSeparator(current, fallback) {
  const format = createNumberFunction(current, fallback);
  return format(0.1).includes(',') ? ',' : '.';
}
function useProvided(props, prop, provided) {
  const internal = useProxiedModel(props, prop, props[prop] ?? provided.value);

  // TODO: Remove when defaultValue works
  internal.value = props[prop] ?? provided.value;
  watch$3(provided, v => {
    if (props[prop] == null) {
      internal.value = provided.value;
    }
  });
  return internal;
}
function createProvideFunction(state) {
  return props => {
    const current = useProvided(props, 'locale', state.current);
    const fallback = useProvided(props, 'fallback', state.fallback);
    const messages = useProvided(props, 'messages', state.messages);
    return {
      name: 'vuetify',
      current,
      fallback,
      messages,
      decimalSeparator: toRef$5(() => inferDecimalSeparator(current, fallback)),
      t: createTranslateFunction(current, fallback, messages),
      n: createNumberFunction(current, fallback),
      provide: createProvideFunction({
        current,
        fallback,
        messages
      })
    };
  };
}
function createVuetifyAdapter(options) {
  const current = shallowRef$3(options?.locale ?? 'en');
  const fallback = shallowRef$3(options?.fallback ?? 'en');
  const messages = ref$3({
    en,
    ...options?.messages
  });
  return {
    name: 'vuetify',
    current,
    fallback,
    messages,
    decimalSeparator: toRef$5(() => options?.decimalSeparator ?? inferDecimalSeparator(current, fallback)),
    t: createTranslateFunction(current, fallback, messages),
    n: createNumberFunction(current, fallback),
    provide: createProvideFunction({
      current,
      fallback,
      messages
    })
  };
}

// Utilities
const {computed: computed$4,inject: inject$6,provide: provide$2,ref: ref$2,toRef: toRef$4} = await importShared('vue');
const LocaleSymbol = Symbol.for('vuetify:locale');
function isLocaleInstance(obj) {
  return obj.name != null;
}
function createLocale(options) {
  const i18n = options?.adapter && isLocaleInstance(options?.adapter) ? options?.adapter : createVuetifyAdapter(options);
  const rtl = createRtl(i18n, options);
  return {
    ...i18n,
    ...rtl
  };
}
function useLocale() {
  const locale = inject$6(LocaleSymbol);
  if (!locale) throw new Error('[Vuetify] Could not find injected locale instance');
  return locale;
}
function genDefaults$2() {
  return {
    af: false,
    ar: true,
    bg: false,
    ca: false,
    ckb: false,
    cs: false,
    de: false,
    el: false,
    en: false,
    es: false,
    et: false,
    fa: true,
    fi: false,
    fr: false,
    hr: false,
    hu: false,
    he: true,
    id: false,
    it: false,
    ja: false,
    km: false,
    ko: false,
    lv: false,
    lt: false,
    nl: false,
    no: false,
    pl: false,
    pt: false,
    ro: false,
    ru: false,
    sk: false,
    sl: false,
    srCyrl: false,
    srLatn: false,
    sv: false,
    th: false,
    tr: false,
    az: false,
    uk: false,
    vi: false,
    zhHans: false,
    zhHant: false
  };
}
function createRtl(i18n, options) {
  const rtl = ref$2(options?.rtl ?? genDefaults$2());
  const isRtl = computed$4(() => rtl.value[i18n.current.value] ?? false);
  return {
    isRtl,
    rtl,
    rtlClasses: toRef$4(() => `v-locale--is-${isRtl.value ? 'rtl' : 'ltr'}`)
  };
}
function useRtl() {
  const locale = inject$6(LocaleSymbol);
  if (!locale) throw new Error('[Vuetify] Could not find injected rtl instance');
  return {
    isRtl: locale.isRtl,
    rtlClasses: locale.rtlClasses
  };
}

// Utilities
function weekInfo(locale) {
  // https://simplelocalize.io/data/locales/
  // then `new Intl.Locale(...).getWeekInfo()`
  const code = locale.slice(-2).toUpperCase();
  switch (true) {
    case locale === 'GB-alt-variant':
      {
        return {
          firstDay: 0,
          firstWeekSize: 4
        };
      }
    case locale === '001':
      {
        return {
          firstDay: 1,
          firstWeekSize: 1
        };
      }
    case `AG AS BD BR BS BT BW BZ CA CO DM DO ET GT GU HK HN ID IL IN JM JP KE
    KH KR LA MH MM MO MT MX MZ NI NP PA PE PH PK PR PY SA SG SV TH TT TW UM US
    VE VI WS YE ZA ZW`.includes(code):
      {
        return {
          firstDay: 0,
          firstWeekSize: 1
        };
      }
    case `AI AL AM AR AU AZ BA BM BN BY CL CM CN CR CY EC GE HR KG KZ LB LK LV
    MD ME MK MN MY NZ RO RS SI TJ TM TR UA UY UZ VN XK`.includes(code):
      {
        return {
          firstDay: 1,
          firstWeekSize: 1
        };
      }
    case `AD AN AT AX BE BG CH CZ DE DK EE ES FI FJ FO FR GB GF GP GR HU IE IS
    IT LI LT LU MC MQ NL NO PL RE RU SE SK SM VA`.includes(code):
      {
        return {
          firstDay: 1,
          firstWeekSize: 4
        };
      }
    case `AE AF BH DJ DZ EG IQ IR JO KW LY OM QA SD SY`.includes(code):
      {
        return {
          firstDay: 6,
          firstWeekSize: 1
        };
      }
    case code === 'MV':
      {
        return {
          firstDay: 5,
          firstWeekSize: 1
        };
      }
    case code === 'PT':
      {
        return {
          firstDay: 0,
          firstWeekSize: 4
        };
      }
    default:
      return null;
  }
}
function getWeekArray(date, locale, firstDayOfWeek) {
  const weeks = [];
  let currentWeek = [];
  const firstDayOfMonth = startOfMonth(date);
  const lastDayOfMonth = endOfMonth(date);
  const first = firstDayOfWeek ?? weekInfo(locale)?.firstDay ?? 0;
  const firstDayWeekIndex = (firstDayOfMonth.getDay() - first + 7) % 7;
  const lastDayWeekIndex = (lastDayOfMonth.getDay() - first + 7) % 7;
  for (let i = 0; i < firstDayWeekIndex; i++) {
    const adjacentDay = new Date(firstDayOfMonth);
    adjacentDay.setDate(adjacentDay.getDate() - (firstDayWeekIndex - i));
    currentWeek.push(adjacentDay);
  }
  for (let i = 1; i <= lastDayOfMonth.getDate(); i++) {
    const day = new Date(date.getFullYear(), date.getMonth(), i);

    // Add the day to the current week
    currentWeek.push(day);

    // If the current week has 7 days, add it to the weeks array and start a new week
    if (currentWeek.length === 7) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  }
  for (let i = 1; i < 7 - lastDayWeekIndex; i++) {
    const adjacentDay = new Date(lastDayOfMonth);
    adjacentDay.setDate(adjacentDay.getDate() + i);
    currentWeek.push(adjacentDay);
  }
  if (currentWeek.length > 0) {
    weeks.push(currentWeek);
  }
  return weeks;
}
function startOfWeek(date, locale, firstDayOfWeek) {
  let day = (firstDayOfWeek ?? weekInfo(locale)?.firstDay ?? 0) % 7;

  // prevent infinite loop
  if (![0, 1, 2, 3, 4, 5, 6].includes(day)) {
    consoleWarn('Invalid firstDayOfWeek, expected discrete number in range [0-6]');
    day = 0;
  }
  const d = new Date(date);
  while (d.getDay() !== day) {
    d.setDate(d.getDate() - 1);
  }
  return d;
}
function endOfWeek(date, locale) {
  const d = new Date(date);
  const lastDay = ((weekInfo(locale)?.firstDay ?? 0) + 6) % 7;
  while (d.getDay() !== lastDay) {
    d.setDate(d.getDate() + 1);
  }
  return d;
}
function startOfMonth(date) {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}
function endOfMonth(date) {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0);
}
function parseLocalDate(value) {
  const parts = value.split('-').map(Number);

  // new Date() uses local time zone when passing individual date component values
  return new Date(parts[0], parts[1] - 1, parts[2]);
}
const _YYYMMDD = /^([12]\d{3}-([1-9]|0[1-9]|1[0-2])-([1-9]|0[1-9]|[12]\d|3[01]))$/;
function date(value) {
  if (value == null) return new Date();
  if (value instanceof Date) return value;
  if (typeof value === 'string') {
    let parsed;
    if (_YYYMMDD.test(value)) {
      return parseLocalDate(value);
    } else {
      parsed = Date.parse(value);
    }
    if (!isNaN(parsed)) return new Date(parsed);
  }
  return null;
}
const sundayJanuarySecond2000 = new Date(2000, 0, 2);
function getWeekdays(locale, firstDayOfWeek, weekdayFormat) {
  const daysFromSunday = firstDayOfWeek ?? weekInfo(locale)?.firstDay ?? 0;
  return createRange(7).map(i => {
    const weekday = new Date(sundayJanuarySecond2000);
    weekday.setDate(sundayJanuarySecond2000.getDate() + daysFromSunday + i);
    return new Intl.DateTimeFormat(locale, {
      weekday: weekdayFormat ?? 'narrow'
    }).format(weekday);
  });
}
function format(value, formatString, locale, formats) {
  const newDate = date(value) ?? new Date();
  const customFormat = formats?.[formatString];
  if (typeof customFormat === 'function') {
    return customFormat(newDate, formatString, locale);
  }
  let options = {};
  switch (formatString) {
    case 'fullDate':
      options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      };
      break;
    case 'fullDateWithWeekday':
      options = {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      };
      break;
    case 'normalDate':
      const day = newDate.getDate();
      const month = new Intl.DateTimeFormat(locale, {
        month: 'long'
      }).format(newDate);
      return `${day} ${month}`;
    case 'normalDateWithWeekday':
      options = {
        weekday: 'short',
        day: 'numeric',
        month: 'short'
      };
      break;
    case 'shortDate':
      options = {
        month: 'short',
        day: 'numeric'
      };
      break;
    case 'year':
      options = {
        year: 'numeric'
      };
      break;
    case 'month':
      options = {
        month: 'long'
      };
      break;
    case 'monthShort':
      options = {
        month: 'short'
      };
      break;
    case 'monthAndYear':
      options = {
        month: 'long',
        year: 'numeric'
      };
      break;
    case 'monthAndDate':
      options = {
        month: 'long',
        day: 'numeric'
      };
      break;
    case 'weekday':
      options = {
        weekday: 'long'
      };
      break;
    case 'weekdayShort':
      options = {
        weekday: 'short'
      };
      break;
    case 'dayOfMonth':
      return new Intl.NumberFormat(locale).format(newDate.getDate());
    case 'hours12h':
      options = {
        hour: 'numeric',
        hour12: true
      };
      break;
    case 'hours24h':
      options = {
        hour: 'numeric',
        hour12: false
      };
      break;
    case 'minutes':
      options = {
        minute: 'numeric'
      };
      break;
    case 'seconds':
      options = {
        second: 'numeric'
      };
      break;
    case 'fullTime':
      options = {
        hour: 'numeric',
        minute: 'numeric'
      };
      break;
    case 'fullTime12h':
      options = {
        hour: 'numeric',
        minute: 'numeric',
        hour12: true
      };
      break;
    case 'fullTime24h':
      options = {
        hour: 'numeric',
        minute: 'numeric',
        hour12: false
      };
      break;
    case 'fullDateTime':
      options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric'
      };
      break;
    case 'fullDateTime12h':
      options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        hour12: true
      };
      break;
    case 'fullDateTime24h':
      options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        hour12: false
      };
      break;
    case 'keyboardDate':
      options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      };
      break;
    case 'keyboardDateTime':
      options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: 'numeric',
        minute: 'numeric'
      };
      return new Intl.DateTimeFormat(locale, options).format(newDate).replace(/, /g, ' ');
    case 'keyboardDateTime12h':
      options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: 'numeric',
        minute: 'numeric',
        hour12: true
      };
      return new Intl.DateTimeFormat(locale, options).format(newDate).replace(/, /g, ' ');
    case 'keyboardDateTime24h':
      options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: 'numeric',
        minute: 'numeric',
        hour12: false
      };
      return new Intl.DateTimeFormat(locale, options).format(newDate).replace(/, /g, ' ');
    default:
      options = customFormat ?? {
        timeZone: 'UTC',
        timeZoneName: 'short'
      };
  }
  return new Intl.DateTimeFormat(locale, options).format(newDate);
}
function toISO(adapter, value) {
  const date = adapter.toJsDate(value);
  const year = date.getFullYear();
  const month = padStart(String(date.getMonth() + 1), 2, '0');
  const day = padStart(String(date.getDate()), 2, '0');
  return `${year}-${month}-${day}`;
}
function parseISO(value) {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(year, month - 1, day);
}
function addMinutes(date, amount) {
  const d = new Date(date);
  d.setMinutes(d.getMinutes() + amount);
  return d;
}
function addHours(date, amount) {
  const d = new Date(date);
  d.setHours(d.getHours() + amount);
  return d;
}
function addDays(date, amount) {
  const d = new Date(date);
  d.setDate(d.getDate() + amount);
  return d;
}
function addWeeks(date, amount) {
  const d = new Date(date);
  d.setDate(d.getDate() + amount * 7);
  return d;
}
function addMonths(date, amount) {
  const d = new Date(date);
  d.setDate(1);
  d.setMonth(d.getMonth() + amount);
  return d;
}
function getYear(date) {
  return date.getFullYear();
}
function getMonth(date) {
  return date.getMonth();
}
function getWeek(date, locale, firstDayOfWeek, firstDayOfYear) {
  const weekInfoFromLocale = weekInfo(locale);
  const weekStart = firstDayOfWeek ?? weekInfoFromLocale?.firstDay ?? 0;
  const minWeekSize = weekInfoFromLocale?.firstWeekSize ?? 1;
  return firstDayOfYear !== undefined ? calculateWeekWithFirstDayOfYear(date, locale, weekStart, firstDayOfYear) : calculateWeekWithMinWeekSize(date, locale, weekStart, minWeekSize);
}
function calculateWeekWithFirstDayOfYear(date, locale, weekStart, firstDayOfYear) {
  const firstDayOfYearOffset = (7 + firstDayOfYear - weekStart) % 7;
  const currentWeekStart = startOfWeek(date, locale, weekStart);
  const currentWeekEnd = addDays(currentWeekStart, 6);
  function yearStartWeekdayOffset(year) {
    return (7 + new Date(year, 0, 1).getDay() - weekStart) % 7;
  }
  let year = getYear(currentWeekStart);
  if (year < getYear(currentWeekEnd) && yearStartWeekdayOffset(year + 1) <= firstDayOfYearOffset) {
    year++;
  }
  const yearStart = new Date(year, 0, 1);
  const offset = yearStartWeekdayOffset(year);
  const d1w1 = offset <= firstDayOfYearOffset ? addDays(yearStart, -offset) : addDays(yearStart, 7 - offset);
  return 1 + getDiff(endOfDay(currentWeekStart), startOfDay(d1w1), 'weeks');
}
function calculateWeekWithMinWeekSize(date, locale, weekStart, minWeekSize) {
  const currentWeekStart = startOfWeek(date, locale, weekStart);
  const currentWeekEnd = addDays(startOfWeek(date, locale, weekStart), 6);
  function firstWeekSize(year) {
    const yearStart = new Date(year, 0, 1);
    return 7 - getDiff(yearStart, startOfWeek(yearStart, locale, weekStart), 'days');
  }
  let year = getYear(currentWeekStart);
  if (year < getYear(currentWeekEnd) && firstWeekSize(year + 1) >= minWeekSize) {
    year++;
  }
  const yearStart = new Date(year, 0, 1);
  const size = firstWeekSize(year);
  const d1w1 = size >= minWeekSize ? addDays(yearStart, size - 7) : addDays(yearStart, size);
  return 1 + getDiff(endOfDay(currentWeekStart), startOfDay(d1w1), 'weeks');
}
function getDate(date) {
  return date.getDate();
}
function getNextMonth(date) {
  return new Date(date.getFullYear(), date.getMonth() + 1, 1);
}
function getPreviousMonth(date) {
  return new Date(date.getFullYear(), date.getMonth() - 1, 1);
}
function getHours(date) {
  return date.getHours();
}
function getMinutes(date) {
  return date.getMinutes();
}
function startOfYear(date) {
  return new Date(date.getFullYear(), 0, 1);
}
function endOfYear(date) {
  return new Date(date.getFullYear(), 11, 31);
}
function isWithinRange(date, range) {
  return isAfter(date, range[0]) && isBefore(date, range[1]);
}
function isValid(date) {
  const d = new Date(date);
  return d instanceof Date && !isNaN(d.getTime());
}
function isAfter(date, comparing) {
  return date.getTime() > comparing.getTime();
}
function isAfterDay(date, comparing) {
  return isAfter(startOfDay(date), startOfDay(comparing));
}
function isBefore(date, comparing) {
  return date.getTime() < comparing.getTime();
}
function isEqual(date, comparing) {
  return date.getTime() === comparing.getTime();
}
function isSameDay(date, comparing) {
  return date.getDate() === comparing.getDate() && date.getMonth() === comparing.getMonth() && date.getFullYear() === comparing.getFullYear();
}
function isSameMonth(date, comparing) {
  return date.getMonth() === comparing.getMonth() && date.getFullYear() === comparing.getFullYear();
}
function isSameYear(date, comparing) {
  return date.getFullYear() === comparing.getFullYear();
}
function getDiff(date, comparing, unit) {
  const d = new Date(date);
  const c = new Date(comparing);
  switch (unit) {
    case 'years':
      return d.getFullYear() - c.getFullYear();
    case 'quarters':
      return Math.floor((d.getMonth() - c.getMonth() + (d.getFullYear() - c.getFullYear()) * 12) / 4);
    case 'months':
      return d.getMonth() - c.getMonth() + (d.getFullYear() - c.getFullYear()) * 12;
    case 'weeks':
      return Math.floor((d.getTime() - c.getTime()) / (1000 * 60 * 60 * 24 * 7));
    case 'days':
      return Math.floor((d.getTime() - c.getTime()) / (1000 * 60 * 60 * 24));
    case 'hours':
      return Math.floor((d.getTime() - c.getTime()) / (1000 * 60 * 60));
    case 'minutes':
      return Math.floor((d.getTime() - c.getTime()) / (1000 * 60));
    case 'seconds':
      return Math.floor((d.getTime() - c.getTime()) / 1000);
    default:
      {
        return d.getTime() - c.getTime();
      }
  }
}
function setHours(date, count) {
  const d = new Date(date);
  d.setHours(count);
  return d;
}
function setMinutes(date, count) {
  const d = new Date(date);
  d.setMinutes(count);
  return d;
}
function setMonth(date, count) {
  const d = new Date(date);
  d.setMonth(count);
  return d;
}
function setDate(date, day) {
  const d = new Date(date);
  d.setDate(day);
  return d;
}
function setYear(date, year) {
  const d = new Date(date);
  d.setFullYear(year);
  return d;
}
function startOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate(), 0, 0, 0, 0);
}
function endOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate(), 23, 59, 59, 999);
}
class VuetifyDateAdapter {
  constructor(options) {
    this.locale = options.locale;
    this.formats = options.formats;
  }
  date(value) {
    return date(value);
  }
  toJsDate(date) {
    return date;
  }
  toISO(date) {
    return toISO(this, date);
  }
  parseISO(date) {
    return parseISO(date);
  }
  addMinutes(date, amount) {
    return addMinutes(date, amount);
  }
  addHours(date, amount) {
    return addHours(date, amount);
  }
  addDays(date, amount) {
    return addDays(date, amount);
  }
  addWeeks(date, amount) {
    return addWeeks(date, amount);
  }
  addMonths(date, amount) {
    return addMonths(date, amount);
  }
  getWeekArray(date, firstDayOfWeek) {
    const firstDay = firstDayOfWeek !== undefined ? Number(firstDayOfWeek) : undefined;
    return getWeekArray(date, this.locale, firstDay);
  }
  startOfWeek(date, firstDayOfWeek) {
    const firstDay = firstDayOfWeek !== undefined ? Number(firstDayOfWeek) : undefined;
    return startOfWeek(date, this.locale, firstDay);
  }
  endOfWeek(date) {
    return endOfWeek(date, this.locale);
  }
  startOfMonth(date) {
    return startOfMonth(date);
  }
  endOfMonth(date) {
    return endOfMonth(date);
  }
  format(date, formatString) {
    return format(date, formatString, this.locale, this.formats);
  }
  isEqual(date, comparing) {
    return isEqual(date, comparing);
  }
  isValid(date) {
    return isValid(date);
  }
  isWithinRange(date, range) {
    return isWithinRange(date, range);
  }
  isAfter(date, comparing) {
    return isAfter(date, comparing);
  }
  isAfterDay(date, comparing) {
    return isAfterDay(date, comparing);
  }
  isBefore(date, comparing) {
    return !isAfter(date, comparing) && !isEqual(date, comparing);
  }
  isSameDay(date, comparing) {
    return isSameDay(date, comparing);
  }
  isSameMonth(date, comparing) {
    return isSameMonth(date, comparing);
  }
  isSameYear(date, comparing) {
    return isSameYear(date, comparing);
  }
  setMinutes(date, count) {
    return setMinutes(date, count);
  }
  setHours(date, count) {
    return setHours(date, count);
  }
  setMonth(date, count) {
    return setMonth(date, count);
  }
  setDate(date, day) {
    return setDate(date, day);
  }
  setYear(date, year) {
    return setYear(date, year);
  }
  getDiff(date, comparing, unit) {
    return getDiff(date, comparing, unit);
  }
  getWeekdays(firstDayOfWeek, weekdayFormat) {
    const firstDay = firstDayOfWeek !== undefined ? Number(firstDayOfWeek) : undefined;
    return getWeekdays(this.locale, firstDay, weekdayFormat);
  }
  getYear(date) {
    return getYear(date);
  }
  getMonth(date) {
    return getMonth(date);
  }
  getWeek(date, firstDayOfWeek, firstDayOfYear) {
    const firstDay = firstDayOfWeek !== undefined ? Number(firstDayOfWeek) : undefined;
    const firstWeekStart = firstDayOfYear !== undefined ? Number(firstDayOfYear) : undefined;
    return getWeek(date, this.locale, firstDay, firstWeekStart);
  }
  getDate(date) {
    return getDate(date);
  }
  getNextMonth(date) {
    return getNextMonth(date);
  }
  getPreviousMonth(date) {
    return getPreviousMonth(date);
  }
  getHours(date) {
    return getHours(date);
  }
  getMinutes(date) {
    return getMinutes(date);
  }
  startOfDay(date) {
    return startOfDay(date);
  }
  endOfDay(date) {
    return endOfDay(date);
  }
  startOfYear(date) {
    return startOfYear(date);
  }
  endOfYear(date) {
    return endOfYear(date);
  }
}

const {inject: inject$5,reactive: reactive$3,watch: watch$2} = await importShared('vue');
const DateOptionsSymbol = Symbol.for('vuetify:date-options');
const DateAdapterSymbol = Symbol.for('vuetify:date-adapter');
function createDate(options, locale) {
  const _options = mergeDeep({
    adapter: VuetifyDateAdapter,
    locale: {
      af: 'af-ZA',
      // ar: '', # not the same value for all variants
      bg: 'bg-BG',
      ca: 'ca-ES',
      ckb: '',
      cs: 'cs-CZ',
      de: 'de-DE',
      el: 'el-GR',
      en: 'en-US',
      // es: '', # not the same value for all variants
      et: 'et-EE',
      fa: 'fa-IR',
      fi: 'fi-FI',
      // fr: '', #not the same value for all variants
      hr: 'hr-HR',
      hu: 'hu-HU',
      he: 'he-IL',
      id: 'id-ID',
      it: 'it-IT',
      ja: 'ja-JP',
      ko: 'ko-KR',
      lv: 'lv-LV',
      lt: 'lt-LT',
      nl: 'nl-NL',
      no: 'no-NO',
      pl: 'pl-PL',
      pt: 'pt-PT',
      ro: 'ro-RO',
      ru: 'ru-RU',
      sk: 'sk-SK',
      sl: 'sl-SI',
      srCyrl: 'sr-SP',
      srLatn: 'sr-SP',
      sv: 'sv-SE',
      th: 'th-TH',
      tr: 'tr-TR',
      az: 'az-AZ',
      uk: 'uk-UA',
      vi: 'vi-VN',
      zhHans: 'zh-CN',
      zhHant: 'zh-TW'
    }
  }, options);
  return {
    options: _options,
    instance: createInstance(_options, locale)
  };
}
function createInstance(options, locale) {
  const instance = reactive$3(typeof options.adapter === 'function'
  // eslint-disable-next-line new-cap
  ? new options.adapter({
    locale: options.locale[locale.current.value] ?? locale.current.value,
    formats: options.formats
  }) : options.adapter);
  watch$2(locale.current, value => {
    instance.locale = options.locale[value] ?? value ?? instance.locale;
  });
  return instance;
}
function useDate() {
  const options = inject$5(DateOptionsSymbol);
  if (!options) throw new Error('[Vuetify] Could not find injected date options');
  const locale = useLocale();
  return createInstance(options, locale);
}

// Utilities
const {computed: computed$3,inject: inject$4,onScopeDispose: onScopeDispose$2,reactive: reactive$2,shallowRef: shallowRef$2,toRef: toRef$3,toRefs,watchEffect: watchEffect$1} = await importShared('vue');

const DisplaySymbol = Symbol.for('vuetify:display');
const defaultDisplayOptions = {
  mobileBreakpoint: 'lg',
  thresholds: {
    xs: 0,
    sm: 600,
    md: 960,
    lg: 1280,
    xl: 1920,
    xxl: 2560
  }
};
const parseDisplayOptions = function () {
  let options = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : defaultDisplayOptions;
  return mergeDeep(defaultDisplayOptions, options);
};
function getClientWidth(ssr) {
  return IN_BROWSER && !ssr ? window.innerWidth : typeof ssr === 'object' && ssr.clientWidth || 0;
}
function getClientHeight(ssr) {
  return IN_BROWSER && !ssr ? window.innerHeight : typeof ssr === 'object' && ssr.clientHeight || 0;
}
function getPlatform(ssr) {
  const userAgent = IN_BROWSER && !ssr ? window.navigator.userAgent : 'ssr';
  function match(regexp) {
    return Boolean(userAgent.match(regexp));
  }
  const android = match(/android/i);
  const ios = match(/iphone|ipad|ipod/i);
  const cordova = match(/cordova/i);
  const electron = match(/electron/i);
  const chrome = match(/chrome/i);
  const edge = match(/edge/i);
  const firefox = match(/firefox/i);
  const opera = match(/opera/i);
  const win = match(/win/i);
  const mac = match(/mac/i);
  const linux = match(/linux/i);
  return {
    android,
    ios,
    cordova,
    electron,
    chrome,
    edge,
    firefox,
    opera,
    win,
    mac,
    linux,
    touch: SUPPORTS_TOUCH,
    ssr: userAgent === 'ssr'
  };
}
function createDisplay(options, ssr) {
  const {
    thresholds,
    mobileBreakpoint
  } = parseDisplayOptions(options);
  const height = shallowRef$2(getClientHeight(ssr));
  const platform = shallowRef$2(getPlatform(ssr));
  const state = reactive$2({});
  const width = shallowRef$2(getClientWidth(ssr));
  function updateSize() {
    height.value = getClientHeight();
    width.value = getClientWidth();
  }
  function update() {
    updateSize();
    platform.value = getPlatform();
  }

  // eslint-disable-next-line max-statements
  watchEffect$1(() => {
    const xs = width.value < thresholds.sm;
    const sm = width.value < thresholds.md && !xs;
    const md = width.value < thresholds.lg && !(sm || xs);
    const lg = width.value < thresholds.xl && !(md || sm || xs);
    const xl = width.value < thresholds.xxl && !(lg || md || sm || xs);
    const xxl = width.value >= thresholds.xxl;
    const name = xs ? 'xs' : sm ? 'sm' : md ? 'md' : lg ? 'lg' : xl ? 'xl' : 'xxl';
    const breakpointValue = typeof mobileBreakpoint === 'number' ? mobileBreakpoint : thresholds[mobileBreakpoint];
    const mobile = width.value < breakpointValue;
    state.xs = xs;
    state.sm = sm;
    state.md = md;
    state.lg = lg;
    state.xl = xl;
    state.xxl = xxl;
    state.smAndUp = !xs;
    state.mdAndUp = !(xs || sm);
    state.lgAndUp = !(xs || sm || md);
    state.xlAndUp = !(xs || sm || md || lg);
    state.smAndDown = !(md || lg || xl || xxl);
    state.mdAndDown = !(lg || xl || xxl);
    state.lgAndDown = !(xl || xxl);
    state.xlAndDown = !xxl;
    state.name = name;
    state.height = height.value;
    state.width = width.value;
    state.mobile = mobile;
    state.mobileBreakpoint = mobileBreakpoint;
    state.platform = platform.value;
    state.thresholds = thresholds;
  });
  if (IN_BROWSER) {
    window.addEventListener('resize', updateSize, {
      passive: true
    });
    onScopeDispose$2(() => {
      window.removeEventListener('resize', updateSize);
    }, true);
  }
  return {
    ...toRefs(state),
    update,
    ssr: !!ssr
  };
}
function useDisplay() {
  let props = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {
    mobile: null
  };
  let name = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : getCurrentInstanceName();
  const display = inject$4(DisplaySymbol);
  if (!display) throw new Error('Could not find Vuetify display injection');
  const mobile = computed$3(() => {
    if (props.mobile) {
      return true;
    } else if (typeof props.mobileBreakpoint === 'number') {
      return display.width.value < props.mobileBreakpoint;
    } else if (props.mobileBreakpoint) {
      return display.width.value < display.thresholds.value[props.mobileBreakpoint];
    } else if (props.mobile === null) {
      return display.mobile.value;
    } else {
      return false;
    }
  });
  const displayClasses = toRef$3(() => {
    if (!name) return {};
    return {
      [`${name}--mobile`]: mobile.value
    };
  });
  return {
    ...display,
    displayClasses,
    mobile
  };
}

// Utilities
const {inject: inject$3,toRef: toRef$2} = await importShared('vue');
const GoToSymbol = Symbol.for('vuetify:goto');
function genDefaults$1() {
  return {
    container: undefined,
    duration: 300,
    layout: false,
    offset: 0,
    easing: 'easeInOutCubic',
    patterns: easingPatterns
  };
}
function getContainer(el) {
  return getTarget(el) ?? (document.scrollingElement || document.body);
}
function getTarget(el) {
  return typeof el === 'string' ? document.querySelector(el) : refElement(el);
}
function getOffset(target, horizontal, rtl) {
  if (typeof target === 'number') return horizontal && rtl ? -target : target;
  let el = getTarget(target);
  let totalOffset = 0;
  while (el) {
    totalOffset += horizontal ? el.offsetLeft : el.offsetTop;
    el = el.offsetParent;
  }
  return totalOffset;
}
function createGoTo(options, locale) {
  return {
    rtl: locale.isRtl,
    options: mergeDeep(genDefaults$1(), options)
  };
}
async function scrollTo(_target, _options, horizontal, goTo) {
  const property = horizontal ? 'scrollLeft' : 'scrollTop';
  const options = mergeDeep(goTo?.options ?? genDefaults$1(), _options);
  const rtl = goTo?.rtl.value;
  const target = (typeof _target === 'number' ? _target : getTarget(_target)) ?? 0;
  const container = options.container === 'parent' && target instanceof HTMLElement ? target.parentElement : getContainer(options.container);
  const ease = PREFERS_REDUCED_MOTION() ? options.patterns.instant : typeof options.easing === 'function' ? options.easing : options.patterns[options.easing];
  if (!ease) throw new TypeError(`Easing function "${options.easing}" not found.`);
  let targetLocation;
  if (typeof target === 'number') {
    targetLocation = getOffset(target, horizontal, rtl);
  } else {
    targetLocation = getOffset(target, horizontal, rtl) - getOffset(container, horizontal, rtl);
    if (options.layout) {
      const styles = window.getComputedStyle(target);
      const layoutOffset = styles.getPropertyValue('--v-layout-top');
      if (layoutOffset) targetLocation -= parseInt(layoutOffset, 10);
    }
  }
  targetLocation += options.offset;
  targetLocation = clampTarget(container, targetLocation, !!rtl, !!horizontal);
  const startLocation = container[property] ?? 0;
  if (targetLocation === startLocation) return Promise.resolve(targetLocation);
  const startTime = performance.now();
  return new Promise(resolve => requestAnimationFrame(function step(currentTime) {
    const timeElapsed = currentTime - startTime;
    const progress = timeElapsed / options.duration;
    const location = Math.floor(startLocation + (targetLocation - startLocation) * ease(clamp(progress, 0, 1)));
    container[property] = location;

    // Allow for some jitter if target time has elapsed
    if (progress >= 1 && Math.abs(location - container[property]) < 10) {
      return resolve(targetLocation);
    } else if (progress > 2) {
      // The target might not be reachable
      consoleWarn('Scroll target is not reachable');
      return resolve(container[property]);
    }
    requestAnimationFrame(step);
  }));
}
function useGoTo() {
  let _options = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
  const goToInstance = inject$3(GoToSymbol);
  const {
    isRtl
  } = useRtl();
  if (!goToInstance) throw new Error('[Vuetify] Could not find injected goto instance');
  const goTo = {
    ...goToInstance,
    // can be set via VLocaleProvider
    rtl: toRef$2(() => goToInstance.rtl.value || isRtl.value)
  };
  async function go(target, options) {
    return scrollTo(target, mergeDeep(_options, options), false, goTo);
  }
  go.horizontal = async (target, options) => {
    return scrollTo(target, mergeDeep(_options, options), true, goTo);
  };
  return go;
}

/**
 * Clamp target value to achieve a smooth scroll animation
 * when the value goes outside the scroll container size
 */
function clampTarget(container, value, rtl, horizontal) {
  const {
    scrollWidth,
    scrollHeight
  } = container;
  const [containerWidth, containerHeight] = container === document.scrollingElement ? [window.innerWidth, window.innerHeight] : [container.offsetWidth, container.offsetHeight];
  let min;
  let max;
  if (horizontal) {
    if (rtl) {
      min = -(scrollWidth - containerWidth);
      max = 0;
    } else {
      min = 0;
      max = scrollWidth - containerWidth;
    }
  } else {
    min = 0;
    max = scrollHeight + -containerHeight;
  }
  return clamp(value, min, max);
}

// Utilities
const {computed: computed$2,getCurrentScope,inject: inject$2,onScopeDispose: onScopeDispose$1,provide: provide$1,ref: ref$1,shallowRef: shallowRef$1,toRef: toRef$1,watch: watch$1,watchEffect} = await importShared('vue');
const ThemeSymbol = Symbol.for('vuetify:theme');
function genDefaults() {
  return {
    defaultTheme: 'light',
    prefix: 'v-',
    variations: {
      colors: [],
      lighten: 0,
      darken: 0
    },
    themes: {
      light: {
        dark: false,
        colors: {
          background: '#FFFFFF',
          surface: '#FFFFFF',
          'surface-bright': '#FFFFFF',
          'surface-light': '#EEEEEE',
          'surface-variant': '#424242',
          'on-surface-variant': '#EEEEEE',
          primary: '#1867C0',
          'primary-darken-1': '#1F5592',
          secondary: '#48A9A6',
          'secondary-darken-1': '#018786',
          error: '#B00020',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FB8C00'
        },
        variables: {
          'border-color': '#000000',
          'border-opacity': 0.12,
          'high-emphasis-opacity': 0.87,
          'medium-emphasis-opacity': 0.60,
          'disabled-opacity': 0.38,
          'idle-opacity': 0.04,
          'hover-opacity': 0.04,
          'focus-opacity': 0.12,
          'selected-opacity': 0.08,
          'activated-opacity': 0.12,
          'pressed-opacity': 0.12,
          'dragged-opacity': 0.08,
          'theme-kbd': '#EEEEEE',
          'theme-on-kbd': '#000000',
          'theme-code': '#F5F5F5',
          'theme-on-code': '#000000'
        }
      },
      dark: {
        dark: true,
        colors: {
          background: '#121212',
          surface: '#212121',
          'surface-bright': '#ccbfd6',
          'surface-light': '#424242',
          'surface-variant': '#c8c8c8',
          'on-surface-variant': '#000000',
          primary: '#2196F3',
          'primary-darken-1': '#277CC1',
          secondary: '#54B6B2',
          'secondary-darken-1': '#48A9A6',
          error: '#CF6679',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FB8C00'
        },
        variables: {
          'border-color': '#FFFFFF',
          'border-opacity': 0.12,
          'high-emphasis-opacity': 1,
          'medium-emphasis-opacity': 0.70,
          'disabled-opacity': 0.50,
          'idle-opacity': 0.10,
          'hover-opacity': 0.04,
          'focus-opacity': 0.12,
          'selected-opacity': 0.08,
          'activated-opacity': 0.12,
          'pressed-opacity': 0.16,
          'dragged-opacity': 0.08,
          'theme-kbd': '#424242',
          'theme-on-kbd': '#FFFFFF',
          'theme-code': '#343434',
          'theme-on-code': '#CCCCCC'
        }
      }
    },
    stylesheetId: 'vuetify-theme-stylesheet',
    scoped: false,
    unimportant: false,
    utilities: true
  };
}
function parseThemeOptions() {
  let options = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : genDefaults();
  const defaults = genDefaults();
  if (!options) return {
    ...defaults,
    isDisabled: true
  };
  const themes = {};
  for (const [key, theme] of Object.entries(options.themes ?? {})) {
    const defaultTheme = theme.dark || key === 'dark' ? defaults.themes?.dark : defaults.themes?.light;
    themes[key] = mergeDeep(defaultTheme, theme);
  }
  return mergeDeep(defaults, {
    ...options,
    themes
  });
}
function createCssClass(lines, selector, content, scope) {
  lines.push(`${getScopedSelector(selector, scope)} {\n`, ...content.map(line => `  ${line};\n`), '}\n');
}
function genCssVariables(theme, prefix) {
  const lightOverlay = theme.dark ? 2 : 1;
  const darkOverlay = theme.dark ? 1 : 2;
  const variables = [];
  for (const [key, value] of Object.entries(theme.colors)) {
    const rgb = parseColor(value);
    variables.push(`--${prefix}theme-${key}: ${rgb.r},${rgb.g},${rgb.b}`);
    if (!key.startsWith('on-')) {
      variables.push(`--${prefix}theme-${key}-overlay-multiplier: ${getLuma(value) > 0.18 ? lightOverlay : darkOverlay}`);
    }
  }
  for (const [key, value] of Object.entries(theme.variables)) {
    const color = typeof value === 'string' && value.startsWith('#') ? parseColor(value) : undefined;
    const rgb = color ? `${color.r}, ${color.g}, ${color.b}` : undefined;
    variables.push(`--${prefix}${key}: ${rgb ?? value}`);
  }
  return variables;
}
function genVariation(name, color, variations) {
  const object = {};
  if (variations) {
    for (const variation of ['lighten', 'darken']) {
      const fn = variation === 'lighten' ? lighten : darken;
      for (const amount of createRange(variations[variation], 1)) {
        object[`${name}-${variation}-${amount}`] = RGBtoHex(fn(parseColor(color), amount));
      }
    }
  }
  return object;
}
function genVariations(colors, variations) {
  if (!variations) return {};
  let variationColors = {};
  for (const name of variations.colors) {
    const color = colors[name];
    if (!color) continue;
    variationColors = {
      ...variationColors,
      ...genVariation(name, color, variations)
    };
  }
  return variationColors;
}
function genOnColors(colors) {
  const onColors = {};
  for (const color of Object.keys(colors)) {
    if (color.startsWith('on-') || colors[`on-${color}`]) continue;
    const onColor = `on-${color}`;
    const colorVal = parseColor(colors[color]);
    onColors[onColor] = getForeground(colorVal);
  }
  return onColors;
}
function getScopedSelector(selector, scope) {
  if (!scope) return selector;
  const scopeSelector = `:where(${scope})`;
  return selector === ':root' ? scopeSelector : `${scopeSelector} ${selector}`;
}
function upsertStyles(id, cspNonce, styles) {
  const styleEl = getOrCreateStyleElement(id, cspNonce);
  if (!styleEl) return;
  styleEl.innerHTML = styles;
}
function getOrCreateStyleElement(id, cspNonce) {
  if (!IN_BROWSER) return null;
  let style = document.getElementById(id);
  if (!style) {
    style = document.createElement('style');
    style.id = id;
    style.type = 'text/css';
    if (cspNonce) style.setAttribute('nonce', cspNonce);
    document.head.appendChild(style);
  }
  return style;
}

// Composables
function createTheme(options) {
  const parsedOptions = parseThemeOptions(options);
  const _name = shallowRef$1(parsedOptions.defaultTheme);
  const themes = ref$1(parsedOptions.themes);
  const systemName = shallowRef$1('light');
  const name = computed$2({
    get() {
      return _name.value === 'system' ? systemName.value : _name.value;
    },
    set(val) {
      _name.value = val;
    }
  });
  const computedThemes = computed$2(() => {
    const acc = {};
    for (const [name, original] of Object.entries(themes.value)) {
      const colors = {
        ...original.colors,
        ...genVariations(original.colors, parsedOptions.variations)
      };
      acc[name] = {
        ...original,
        colors: {
          ...colors,
          ...genOnColors(colors)
        }
      };
    }
    return acc;
  });
  const current = toRef$1(() => computedThemes.value[name.value]);
  const isSystem = toRef$1(() => _name.value === 'system');
  const styles = computed$2(() => {
    const lines = [];
    const important = parsedOptions.unimportant ? '' : ' !important';
    const scoped = parsedOptions.scoped ? parsedOptions.prefix : '';
    if (current.value?.dark) {
      createCssClass(lines, ':root', ['color-scheme: dark'], parsedOptions.scope);
    }
    createCssClass(lines, ':root', genCssVariables(current.value, parsedOptions.prefix), parsedOptions.scope);
    for (const [themeName, theme] of Object.entries(computedThemes.value)) {
      createCssClass(lines, `.${parsedOptions.prefix}theme--${themeName}`, [`color-scheme: ${theme.dark ? 'dark' : 'normal'}`, ...genCssVariables(theme, parsedOptions.prefix)], parsedOptions.scope);
    }
    if (parsedOptions.utilities) {
      const bgLines = [];
      const fgLines = [];
      const colors = new Set(Object.values(computedThemes.value).flatMap(theme => Object.keys(theme.colors)));
      for (const key of colors) {
        if (key.startsWith('on-')) {
          createCssClass(fgLines, `.${key}`, [`color: rgb(var(--${parsedOptions.prefix}theme-${key}))${important}`], parsedOptions.scope);
        } else {
          createCssClass(bgLines, `.${scoped}bg-${key}`, [`--${parsedOptions.prefix}theme-overlay-multiplier: var(--${parsedOptions.prefix}theme-${key}-overlay-multiplier)`, `background-color: rgb(var(--${parsedOptions.prefix}theme-${key}))${important}`, `color: rgb(var(--${parsedOptions.prefix}theme-on-${key}))${important}`], parsedOptions.scope);
          createCssClass(fgLines, `.${scoped}text-${key}`, [`color: rgb(var(--${parsedOptions.prefix}theme-${key}))${important}`], parsedOptions.scope);
          createCssClass(fgLines, `.${scoped}border-${key}`, [`--${parsedOptions.prefix}border-color: var(--${parsedOptions.prefix}theme-${key})`], parsedOptions.scope);
        }
      }
      if (parsedOptions.layers) {
        lines.push('@layer background {\n', ...bgLines.map(v => `  ${v}`), '}\n', '@layer foreground {\n', ...fgLines.map(v => `  ${v}`), '}\n');
      } else {
        lines.push(...bgLines, ...fgLines);
      }
    }
    let final = lines.map((str, i) => i === 0 ? str : `    ${str}`).join('');
    if (parsedOptions.layers) {
      final = '@layer vuetify.theme {\n' + lines.map(v => `  ${v}`).join('') + '\n}';
    }
    return final;
  });
  const themeClasses = toRef$1(() => parsedOptions.isDisabled ? undefined : `${parsedOptions.prefix}theme--${name.value}`);
  const themeNames = toRef$1(() => Object.keys(computedThemes.value));
  if (SUPPORTS_MATCH_MEDIA) {
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    function updateSystemName() {
      systemName.value = media.matches ? 'dark' : 'light';
    }
    updateSystemName();
    media.addEventListener('change', updateSystemName, {
      passive: true
    });
    if (getCurrentScope()) {
      onScopeDispose$1(() => {
        media.removeEventListener('change', updateSystemName);
      });
    }
  }
  function install(app) {
    if (parsedOptions.isDisabled) return;
    const head = app._context.provides.usehead;
    if (head) {
      function getHead() {
        return {
          style: [{
            textContent: styles.value,
            id: parsedOptions.stylesheetId,
            nonce: parsedOptions.cspNonce || false
          }]
        };
      }
      if (head.push) {
        const entry = head.push(getHead);
        if (IN_BROWSER) {
          watch$1(styles, () => {
            entry.patch(getHead);
          });
        }
      } else {
        if (IN_BROWSER) {
          head.addHeadObjs(toRef$1(getHead));
          watchEffect(() => head.updateDOM());
        } else {
          head.addHeadObjs(getHead());
        }
      }
    } else {
      if (IN_BROWSER) {
        watch$1(styles, updateStyles, {
          immediate: true
        });
      } else {
        updateStyles();
      }
      function updateStyles() {
        upsertStyles(parsedOptions.stylesheetId, parsedOptions.cspNonce, styles.value);
      }
    }
  }
  function change(themeName) {
    if (themeName !== 'system' && !themeNames.value.includes(themeName)) {
      consoleWarn(`Theme "${themeName}" not found on the Vuetify theme instance`);
      return;
    }
    name.value = themeName;
  }
  function cycle() {
    let themeArray = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : themeNames.value;
    const currentIndex = themeArray.indexOf(name.value);
    const nextIndex = currentIndex === -1 ? 0 : (currentIndex + 1) % themeArray.length;
    change(themeArray[nextIndex]);
  }
  function toggle() {
    let themeArray = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : ['light', 'dark'];
    cycle(themeArray);
  }
  const globalName = new Proxy(name, {
    get(target, prop) {
      return Reflect.get(target, prop);
    },
    set(target, prop, val) {
      if (prop === 'value') {
        deprecate(`theme.global.name.value = ${val}`, `theme.change('${val}')`);
      }
      return Reflect.set(target, prop, val);
    }
  });
  return {
    install,
    change,
    cycle,
    toggle,
    isDisabled: parsedOptions.isDisabled,
    isSystem,
    name,
    themes,
    current,
    computedThemes,
    prefix: parsedOptions.prefix,
    themeClasses,
    styles,
    global: {
      name: globalName,
      current
    }
  };
}
function useTheme() {
  getCurrentInstance('useTheme');
  const theme = inject$2(ThemeSymbol, null);
  if (!theme) throw new Error('Could not find Vuetify theme injection');
  return theme;
}

const {computed: computed$1,inject: inject$1,onActivated,onBeforeUnmount,onDeactivated,onMounted,provide,reactive: reactive$1,ref,shallowRef,toRef,useId} = await importShared('vue');
const VuetifyLayoutKey = Symbol.for('vuetify:layout');
function useLayout() {
  const layout = inject$1(VuetifyLayoutKey);
  if (!layout) throw new Error('[Vuetify] Could not find injected layout');
  return {
    getLayoutItem: layout.getLayoutItem,
    mainRect: layout.mainRect,
    mainStyles: layout.mainStyles
  };
}

/**
 * Centralized key alias mapping for consistent key normalization across the hotkey system.
 *
 * This maps various user-friendly aliases to canonical key names that match
 * KeyboardEvent.key values (in lowercase) where possible.
 */
const keyAliasMap = {
  // Modifier aliases (from vue-use, other libraries, and current implementation)
  control: 'ctrl',
  command: 'cmd',
  option: 'alt',
  // Arrow key aliases (common abbreviations)
  up: 'arrowup',
  down: 'arrowdown',
  left: 'arrowleft',
  right: 'arrowright',
  // Other common key aliases
  esc: 'escape',
  spacebar: ' ',
  space: ' ',
  return: 'enter',
  del: 'delete',
  // Symbol aliases (existing from hotkey-parsing.ts)
  plus: '+',
  slash: '/',
  underscore: '_',
  minus: '-',
  hyphen: '-'
};

/**
 * Normalizes a key string to its canonical form using the alias map.
 *
 * @param key - The key string to normalize
 * @returns The canonical key name in lowercase
 */
function normalizeKey(key) {
  const lowerKey = key.toLowerCase();
  return keyAliasMap[lowerKey] || lowerKey;
}

// Utilities

/**
 * Splits a single combination string into individual key parts.
 *
 * A combination is a set of keys that must be pressed simultaneously.
 * e.g. `ctrl+k`, `shift--`
 */
function splitKeyCombination(combination) {
  let isInternal = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : false;
  const emptyResult = {
    keys: [],
    separators: []
  };
  if (!combination) {
    if (!isInternal) consoleWarn('Invalid hotkey combination: empty string provided');
    return emptyResult;
  }

  // --- VALIDATION ---

  const hasInvalidLeadingSeparator = combination.length > 1 &&
  // Starts with a single separator followed by a non-separator character (e.g. '+a', '_a')
  ['+', '/', '_'].some(v => combination.startsWith(v)) && !['++', '//', '__'].some(v => combination.startsWith(v));
  const hasInvalidStructure = hasInvalidLeadingSeparator ||
  // Disallow literal +, / or _ keys (they are delimiters)
  combination.includes('++') || combination.includes('//') || combination.includes('__') || combination === '+' || combination === '/' || combination === '_' ||
  // Ends with a separator that is not part of a doubled literal

  combination.length > 1 && (combination.endsWith('+') || combination.endsWith('/') || combination.endsWith('_')) && combination.at(-2) !== combination.at(-1) ||
  // Stand-alone doubled separators (dangling)
  combination === '++' || combination === '//' || combination === '--' || combination === '__';
  if (hasInvalidStructure) {
    if (!isInternal) consoleWarn(`Invalid hotkey combination: "${combination}" has invalid structure`);
    return emptyResult;
  }
  const keys = [];
  const separators = [];
  let buffer = '';
  const flushBuffer = separator => {
    if (buffer) {
      separator && separators.push(separator);
      keys.push(normalizeKey(buffer));
      buffer = '';
    }
  };
  for (let i = 0; i < combination.length; i++) {
    const char = combination[i];
    const nextChar = combination[i + 1];
    if (['+', '/', '_', '-'].includes(char)) {
      if (char === nextChar) {
        flushBuffer(char);
        keys.push(char);
        i++;
      } else if (['+', '/', '_'].includes(char)) {
        flushBuffer(char);
      } else {
        buffer += char;
      }
    } else {
      buffer += char;
    }
  }
  flushBuffer();

  // Within a combination, `-` is only valid as a literal key (e.g., `ctrl+-`).
  // `-` cannot be part of a longer key name within a combination.
  const hasInvalidMinus = keys.some(key => key.length > 1 && key.includes('-') && key !== '--');
  if (hasInvalidMinus) {
    if (!isInternal) consoleWarn(`Invalid hotkey combination: "${combination}" has invalid structure`);
    return emptyResult;
  }
  if (keys.length === 0 && combination) {
    return {
      keys: [normalizeKey(combination)],
      separators
    };
  }
  return {
    keys,
    separators
  };
}

/**
 * Splits a hotkey string into its constituent combination groups.
 *
 * A sequence is a series of combinations that must be pressed in order.
 * e.g. `a-b`, `ctrl+k-p`
 */
function splitKeySequence(str) {
  if (!str) {
    consoleWarn('Invalid hotkey sequence: empty string provided');
    return [];
  }

  // A sequence is invalid if it starts or ends with a separator,
  // unless it is part of a combination (e.g., `shift+-`).
  const hasInvalidStart = str.startsWith('-') && str !== '-' && !['---', '--+'].includes(str);
  const hasInvalidEnd = str.endsWith('-') && !str.endsWith('+-') && !str.endsWith('_-') && str !== '-' && str !== '---';
  if (hasInvalidStart || hasInvalidEnd) {
    consoleWarn(`Invalid hotkey sequence: "${str}" contains invalid combinations`);
    return [];
  }
  const result = [];
  let buffer = '';
  let i = 0;
  while (i < str.length) {
    const char = str[i];
    if (char === '-') {
      // Determine if this hyphen is part of the current combination
      const prevChar = str[i - 1];
      const prevPrevChar = i > 1 ? str[i - 2] : undefined;
      const precededBySeparator = ['+', '_'].includes(prevChar) && !['+', '/'].includes(prevPrevChar ?? '');
      if (precededBySeparator) {
        // Treat as part of the combination (e.g., 'ctrl+-')
        buffer += char;
        i++;
      } else {
        // Treat as sequence separator
        if (buffer) {
          result.push(buffer);
          buffer = '';
        } else {
          // Empty buffer means we have a literal '-' key
          result.push('-');
        }
        i++;
      }
    } else {
      buffer += char;
      i++;
    }
  }

  // Add final buffer if it exists
  if (buffer) {
    result.push(buffer);
  }

  // Collapse runs of '-' so that every second '-' is removed
  const collapsed = [];
  let minusCount = 0;
  for (const part of result) {
    if (part === '-') {
      if (minusCount % 2 === 0) collapsed.push('-');
      minusCount++;
    } else {
      minusCount = 0;
      collapsed.push(part);
    }
  }

  // Validate that each part of the sequence is a valid combination
  const areAllValid = collapsed.every(s => splitKeyCombination(s, true).keys.length > 0);
  if (!areAllValid) {
    consoleWarn(`Invalid hotkey sequence: "${str}" contains invalid combinations`);
    return [];
  }
  return collapsed;
}

const {onScopeDispose,toValue,watch} = await importShared('vue');
function useHotkey(keys, callback) {
  let options = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : {};
  if (!IN_BROWSER) return function () {};
  const {
    event = 'keydown',
    inputs = false,
    preventDefault = true,
    sequenceTimeout = 1000
  } = options;
  const isMac = navigator?.userAgent?.includes('Macintosh') ?? false;
  let timeout = 0;
  let keyGroups;
  let isSequence = false;
  let groupIndex = 0;
  function isInputFocused() {
    if (toValue(inputs)) return false;
    const activeElement = document.activeElement;
    return activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA' || activeElement.isContentEditable || activeElement.contentEditable === 'true');
  }
  function resetSequence() {
    groupIndex = 0;
    clearTimeout(timeout);
  }
  function handler(e) {
    const group = keyGroups[groupIndex];
    if (!group || isInputFocused()) return;
    if (!matchesKeyGroup(e, group, isMac)) {
      if (isSequence) resetSequence();
      return;
    }
    if (toValue(preventDefault)) e.preventDefault();
    if (!isSequence) {
      callback(e);
      return;
    }
    clearTimeout(timeout);
    groupIndex++;
    if (groupIndex === keyGroups.length) {
      callback(e);
      resetSequence();
      return;
    }
    timeout = window.setTimeout(resetSequence, toValue(sequenceTimeout));
  }
  function cleanup() {
    window.removeEventListener(toValue(event), handler);
    clearTimeout(timeout);
  }
  watch(() => toValue(keys), newKeys => {
    cleanup();
    if (newKeys) {
      const groups = splitKeySequence(newKeys.toLowerCase());
      isSequence = groups.length > 1;
      keyGroups = groups;
      resetSequence();
      window.addEventListener(toValue(event), handler);
    }
  }, {
    immediate: true
  });

  // Watch for changes in the event type to re-register the listener
  watch(() => toValue(event), (newEvent, oldEvent) => {
    if (oldEvent && keyGroups && keyGroups.length > 0) {
      window.removeEventListener(oldEvent, handler);
      window.addEventListener(newEvent, handler);
    }
  });
  onScopeDispose(cleanup, true);
  return cleanup;
}
function matchesKeyGroup(e, group, isMac) {
  const {
    modifiers,
    actualKey
  } = parseKeyGroup(group);
  const expectCtrl = modifiers.ctrl || !isMac && (modifiers.cmd || modifiers.meta);
  const expectMeta = isMac && (modifiers.cmd || modifiers.meta);
  return e.ctrlKey === expectCtrl && e.metaKey === expectMeta && e.shiftKey === modifiers.shift && e.altKey === modifiers.alt && e.key.toLowerCase() === actualKey?.toLowerCase();
}
function parseKeyGroup(group) {
  const MODIFIERS = ['ctrl', 'shift', 'alt', 'meta', 'cmd'];

  // Use the shared combination splitting logic
  const {
    keys: parts
  } = splitKeyCombination(group.toLowerCase());

  // If the combination is invalid, return empty result
  if (parts.length === 0) {
    return {
      modifiers: Object.fromEntries(MODIFIERS.map(m => [m, false])),
      actualKey: undefined
    };
  }
  const modifiers = Object.fromEntries(MODIFIERS.map(m => [m, false]));
  let actualKey;
  for (const part of parts) {
    if (MODIFIERS.includes(part)) {
      modifiers[part] = true;
    } else {
      actualKey = part;
    }
  }
  return {
    modifiers,
    actualKey
  };
}

// Utilities
const {computed} = await importShared('vue');
const defaultDelimiters = /[-!$%^&*()_+|~=`{}[\]:";'<>?,./\\ ]/;
const presets = {
  'credit-card': '#### - #### - #### - ####',
  date: '##/##/####',
  'date-time': '##/##/#### ##:##',
  'iso-date': '####-##-##',
  'iso-date-time': '####-##-## ##:##',
  phone: '(###) ### - ####',
  social: '###-##-####',
  time: '##:##',
  'time-with-seconds': '##:##:##'
};
const defaultTokens = {
  '#': {
    pattern: /[0-9]/
  },
  A: {
    pattern: /[A-Z]/i,
    convert: v => v.toUpperCase()
  },
  a: {
    pattern: /[a-z]/i,
    convert: v => v.toLowerCase()
  },
  N: {
    pattern: /[0-9A-Z]/i,
    convert: v => v.toUpperCase()
  },
  n: {
    pattern: /[0-9a-z]/i,
    convert: v => v.toLowerCase()
  },
  X: {
    pattern: defaultDelimiters
  }
};
function useMask(props) {
  const mask = computed(() => {
    if (typeof props.mask === 'string') {
      if (props.mask in presets) return presets[props.mask];
      return props.mask;
    }
    return props.mask?.mask ?? '';
  });
  const tokens = computed(() => {
    return {
      ...defaultTokens,
      ...(isObject(props.mask) ? props.mask.tokens : null)
    };
  });
  function isMask(char) {
    return char in tokens.value;
  }
  function maskValidates(mask, char) {
    if (char == null || !isMask(mask)) return false;
    const item = tokens.value[mask];
    if (item.pattern) return item.pattern.test(char);
    return item.test(char);
  }
  function convert(mask, char) {
    const item = tokens.value[mask];
    return item.convert ? item.convert(char) : char;
  }
  function maskText(text) {
    const trimmedText = text?.trim().replace(/\s+/g, ' ');
    if (trimmedText == null) return '';
    if (!mask.value.length || !trimmedText.length) return trimmedText;
    let textIndex = 0;
    let maskIndex = 0;
    let newText = '';
    while (maskIndex < mask.value.length) {
      const mchar = mask.value[maskIndex];
      const tchar = trimmedText[textIndex];

      // Escaped character in mask, the next mask character is inserted
      if (mchar === '\\') {
        newText += mask.value[maskIndex + 1];
        maskIndex += 2;
        continue;
      }
      if (!isMask(mchar)) {
        newText += mchar;
        if (tchar === mchar) {
          textIndex++;
        }
      } else if (maskValidates(mchar, tchar)) {
        newText += convert(mchar, tchar);
        textIndex++;
      } else {
        break;
      }
      maskIndex++;
    }
    return newText;
  }
  function unmaskText(text) {
    if (text == null) return null;
    if (!mask.value.length || !text.length) return text;
    let textIndex = 0;
    let maskIndex = 0;
    let newText = '';
    while (true) {
      const mchar = mask.value[maskIndex];
      const tchar = text[textIndex];
      if (tchar == null) break;
      if (mchar == null) {
        newText += tchar;
        textIndex++;
        continue;
      }

      // Escaped character in mask, skip the next input character
      if (mchar === '\\') {
        if (tchar === mask.value[maskIndex + 1]) {
          textIndex++;
        }
        maskIndex += 2;
        continue;
      }
      if (maskValidates(mchar, tchar)) {
        // masked char
        newText += tchar;
        textIndex++;
        maskIndex++;
        continue;
      } else if (mchar !== tchar) {
        // input doesn't match mask, skip forward until it does
        while (true) {
          const mchar = mask.value[maskIndex++];
          if (mchar == null || maskValidates(mchar, tchar)) break;
        }
        continue;
      }
      textIndex++;
      maskIndex++;
    }
    return newText;
  }
  function isValid(text) {
    if (!text) return false;
    return unmaskText(text) === unmaskText(maskText(text));
  }
  function isComplete(text) {
    if (!text) return false;
    const maskedText = maskText(text);
    return maskedText.length === mask.value.length && isValid(text);
  }
  return {
    isValid,
    isComplete,
    mask: maskText,
    unmask: unmaskText
  };
}

const {effectScope,nextTick,reactive} = await importShared('vue');
function createVuetify() {
  let vuetify = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : {};
  const {
    blueprint,
    ...rest
  } = vuetify;
  const options = mergeDeep(blueprint, rest);
  const {
    aliases = {},
    components = {},
    directives = {}
  } = options;
  const scope = effectScope();
  return scope.run(() => {
    const defaults = createDefaults(options.defaults);
    const display = createDisplay(options.display, options.ssr);
    const theme = createTheme(options.theme);
    const icons = createIcons(options.icons);
    const locale = createLocale(options.locale);
    const date = createDate(options.date, locale);
    const goTo = createGoTo(options.goTo, locale);
    function install(app) {
      for (const key in directives) {
        app.directive(key, directives[key]);
      }
      for (const key in components) {
        app.component(key, components[key]);
      }
      for (const key in aliases) {
        app.component(key, defineComponent({
          ...aliases[key],
          name: key,
          aliasName: aliases[key].name
        }));
      }
      const appScope = effectScope();
      appScope.run(() => {
        theme.install(app);
      });
      app.onUnmount(() => appScope.stop());
      app.provide(DefaultsSymbol, defaults);
      app.provide(DisplaySymbol, display);
      app.provide(ThemeSymbol, theme);
      app.provide(IconSymbol, icons);
      app.provide(LocaleSymbol, locale);
      app.provide(DateOptionsSymbol, date.options);
      app.provide(DateAdapterSymbol, date.instance);
      app.provide(GoToSymbol, goTo);
      if (IN_BROWSER && options.ssr) {
        if (app.$nuxt) {
          app.$nuxt.hook("app:suspense:resolve", () => {
            display.update();
          });
        } else {
          const {
            mount
          } = app;
          app.mount = function() {
            const vm = mount(...arguments);
            nextTick(() => display.update());
            app.mount = mount;
            return vm;
          };
        }
      }
      {
        app.mixin({
          computed: {
            $vuetify() {
              return reactive({
                defaults: inject.call(this, DefaultsSymbol),
                display: inject.call(this, DisplaySymbol),
                theme: inject.call(this, ThemeSymbol),
                icons: inject.call(this, IconSymbol),
                locale: inject.call(this, LocaleSymbol),
                date: inject.call(this, DateAdapterSymbol)
              });
            }
          }
        });
      }
    }
    function unmount() {
      scope.stop();
    }
    return {
      install,
      unmount,
      defaults,
      display,
      theme,
      icons,
      locale,
      date,
      goTo
    };
  });
}
const version = "3.12.3";
createVuetify.version = version;
function inject(key) {
  const vm = this.$;
  const provides = vm.parent?.provides ?? vm.vnode.appContext?.provides;
  if (provides && key in provides) {
    return provides[key];
  }
}

export { createVuetify, useDate, useDefaults, useDisplay, useGoTo, useHotkey, useLayout, useLocale, useMask, useRtl, useTheme, version };
