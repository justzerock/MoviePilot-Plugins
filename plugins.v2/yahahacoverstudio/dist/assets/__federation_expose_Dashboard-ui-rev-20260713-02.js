import { importShared } from './__federation_fn_import-ui-rev-20260713-02.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-ui-rev-20260713-02.js';

const {defineComponent:_defineComponent} = await importShared('vue');

const {createElementVNode:_createElementVNode,createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,vShow:_vShow,withDirectives:_withDirectives,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,mergeProps:_mergeProps,createElementBlock:_createElementBlock} = await importShared('vue');

const _hoisted_1 = {
  class: "dashboard-widget",
  "data-mcr-theme": ""
};
const _hoisted_2 = { class: "mcr-shell mcr-dashboard-shell" };
const _hoisted_3 = { class: "dashboard-head" };
const _hoisted_4 = { class: "dashboard-drag" };
const _hoisted_5 = { class: "dashboard-meta" };
const _hoisted_6 = { class: "dashboard-meta__item" };
const _hoisted_7 = { class: "dashboard-meta__item" };
const _hoisted_8 = { class: "dashboard-meta__item" };
const _sfc_main = /* @__PURE__ */ _defineComponent({
  __name: "Dashboard",
  props: {
    config: {
      type: Object,
      default: () => ({})
    },
    allowRefresh: {
      type: Boolean,
      default: true
    },
    api: {
      type: Object,
      default: () => ({})
    }
  },
  setup(__props) {
    const props = __props;
    async function generateNow() {
      try {
        await props.api.post("plugin/YahahaCoverStudio/generate_now");
      } catch (e) {
        console.error("dashboard generate_now failed", e);
      }
    }
    return (_ctx, _cache) => {
      const _component_v_icon = _resolveComponent("v-icon");
      const _component_v_btn = _resolveComponent("v-btn");
      const _component_v_card_text = _resolveComponent("v-card-text");
      const _component_v_card = _resolveComponent("v-card");
      const _component_v_hover = _resolveComponent("v-hover");
      return _openBlock(), _createElementBlock("div", _hoisted_1, [
        _createVNode(_component_v_hover, null, {
          default: _withCtx(({ isHovering, props: hoverProps }) => [
            _createElementVNode("div", _hoisted_2, [
              _cache[7] || (_cache[7] = _createElementVNode("div", { class: "mcr-shell__aurora" }, null, -1)),
              _cache[8] || (_cache[8] = _createElementVNode("div", { class: "mcr-shell__noise" }, null, -1)),
              _createVNode(_component_v_card, _mergeProps(hoverProps, { class: "mcr-frame" }), {
                default: _withCtx(() => [
                  _createVNode(_component_v_card_text, { class: "mcr-frame__body" }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_3, [
                        _cache[1] || (_cache[1] = _createElementVNode("div", null, [
                          _createElementVNode("div", { class: "mcr-kicker" }, "Dashboard Widget"),
                          _createElementVNode("div", { class: "dashboard-title" }, "呀哈哈封面工坊")
                        ], -1)),
                        _withDirectives(_createElementVNode("div", _hoisted_4, [
                          _createVNode(_component_v_icon, { class: "cursor-move" }, {
                            default: _withCtx(() => [..._cache[0] || (_cache[0] = [
                              _createTextVNode("mdi-drag", -1)
                            ])]),
                            _: 1
                          })
                        ], 512), [
                          [_vShow, isHovering]
                        ])
                      ]),
                      _createElementVNode("div", _hoisted_5, [
                        _createElementVNode("div", _hoisted_6, [
                          _cache[2] || (_cache[2] = _createElementVNode("span", null, "服务器", -1)),
                          _createElementVNode("strong", null, _toDisplayString(__props.config.selected_servers?.length || 0), 1)
                        ]),
                        _createElementVNode("div", _hoisted_7, [
                          _cache[3] || (_cache[3] = _createElementVNode("span", null, "风格", -1)),
                          _createElementVNode("strong", null, _toDisplayString(__props.config.cover_style_base || "static_1"), 1)
                        ]),
                        _createElementVNode("div", _hoisted_8, [
                          _cache[4] || (_cache[4] = _createElementVNode("span", null, "模式", -1)),
                          _createElementVNode("strong", null, _toDisplayString(__props.config.cover_style_variant || "static"), 1)
                        ])
                      ]),
                      _cache[6] || (_cache[6] = _createElementVNode("div", { class: "dashboard-note" }, " 当前卡片只暴露最常用的生成入口，详情参数仍在插件主面板中维护。 ", -1)),
                      __props.allowRefresh ? (_openBlock(), _createBlock(_component_v_btn, {
                        key: 0,
                        class: "mcr-button mcr-button--primary dashboard-action",
                        "prepend-icon": "mdi-play-circle-outline",
                        onClick: generateNow
                      }, {
                        default: _withCtx(() => [..._cache[5] || (_cache[5] = [
                          _createTextVNode(" 立即生成封面 ", -1)
                        ])]),
                        _: 1
                      })) : _createCommentVNode("", true)
                    ]),
                    _: 2
                  }, 1024)
                ]),
                _: 2
              }, 1040)
            ])
          ]),
          _: 1
        })
      ]);
    };
  }
});

const Dashboard = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-73973e7e"]]);

export { Dashboard as default };
