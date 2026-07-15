<template>
  <v-card
    variant="outlined"
    class="mcr-layout-editor"
    :class="{ 'mcr-layout-editor--embedded': embedded }"
    :data-mcr-theme="props.theme"
  >
    <div ref="editorRootEl" class="mcr-layout-workbench">
      <div ref="canvasPaneEl" class="mcr-layout-canvas-pane">
      <div ref="layerActionsEl" class="mcr-layer-actions mcr-layer-actions--canvas">
        <v-btn size="small" class="mcr-button mcr-button--ghost" prepend-icon="mdi-image-plus-outline" @click="addImageLayer">
          添加图片
        </v-btn>
        <v-btn size="small" class="mcr-button mcr-button--ghost" prepend-icon="mdi-sticker-plus-outline" @click="toggleStickerLibrary">
          添加贴图
        </v-btn>
        <v-btn size="small" class="mcr-button mcr-button--ghost" prepend-icon="mdi-format-title" @click="addZhTitleLayer">
          主标题
        </v-btn>
        <v-btn size="small" class="mcr-button mcr-button--ghost" prepend-icon="mdi-subtitles-outline" @click="addEnTitleLayer">
          副标题
        </v-btn>
        <v-btn size="small" class="mcr-button mcr-button--ghost" prepend-icon="mdi-text-box-plus-outline" @click="addTextLayer">
          添加文字
        </v-btn>
        <input
          ref="stickerFileInputEl"
          class="mcr-sticker-file-input"
          type="file"
          accept="image/*"
          @change="onStickerFileInputChange"
        >
      </div>
      <div
        v-if="stickerLibraryOpen"
        class="mcr-sticker-library"
        :data-loading="stickerLibraryLoading ? 'true' : 'false'"
      >
        <div class="mcr-sticker-library__header">
          <div>
            <div class="mcr-sticker-library__title">贴图库</div>
            <div class="mcr-sticker-library__hint">选择已上传贴图，或上传新的本地图片。</div>
          </div>
          <div class="mcr-sticker-library__actions">
            <v-btn size="small" class="mcr-button mcr-button--ghost" prepend-icon="mdi-upload-outline" @click="openStickerFilePicker">
              上传
            </v-btn>
            <v-btn size="small" icon="mdi-close" class="mcr-button mcr-button--ghost mcr-sticker-library__close" @click="stickerLibraryOpen = false" />
          </div>
        </div>
        <div v-if="stickerLibraryLoading" class="mcr-sticker-library__empty">
          加载贴图库...
        </div>
        <div v-else-if="!stickerLibraryItems.length" class="mcr-sticker-library__empty">
          暂无贴图
        </div>
        <div v-else class="mcr-sticker-library__grid">
          <div
            v-for="item in stickerLibraryItems"
            :key="item.path"
            role="button"
            tabindex="0"
            class="mcr-sticker-item"
            :title="item.name"
            @click="addStickerFromLibrary(item)"
            @keydown.enter.prevent="addStickerFromLibrary(item)"
            @keydown.space.prevent="addStickerFromLibrary(item)"
          >
            <span class="mcr-sticker-item__thumb">
              <img v-if="item.dataUrl || item.url" :src="item.dataUrl || item.url" :alt="item.name">
              <v-icon v-else icon="mdi-sticker-outline" size="24" />
            </span>
            <span class="mcr-sticker-item__name">{{ item.name }}</span>
            <button
              type="button"
              class="mcr-sticker-item__delete"
              :class="{ 'mcr-sticker-item__delete--active': isStickerInUse(item) }"
              :title="isStickerInUse(item) ? '删除贴图并移除当前方案中的引用' : '删除贴图'"
              @click.stop.prevent="deleteStickerItem(item)"
              @keydown.enter.stop.prevent="deleteStickerItem(item)"
              @keydown.space.stop.prevent="deleteStickerItem(item)"
            >
              <v-icon icon="mdi-trash-can-outline" size="15" />
            </button>
          </div>
        </div>
      </div>

      <!-- 中间：画布区域 -->
      <div class="mcr-layout-stage-wrap">
        <div ref="canvasEl" class="mcr-layout-canvas">
          <SvgTemplatePreview
            :template="layout"
            :source="previewSource || null"
            :params="effectiveParams"
            :font-revision="fontRevision"
            :auto-blend-color="autoBlendColor"
            :selected-layer-id="selectedLayerId"
            interactive
            @select-layer="selectLayer"
            @layer-pointer-down="onSvgLayerPointerDown"
            @background-click="selectBackground"
          />
          <div
            v-if="activeSnapGuideStyles.vertical.length || activeSnapGuideStyles.horizontal.length"
            class="mcr-snap-guides"
            aria-hidden="true"
          >
            <span
              v-for="guide in activeSnapGuideStyles.vertical"
              :key="`v-${guide.value}`"
              class="mcr-snap-guide mcr-snap-guide--vertical"
              :style="{ left: guide.position }"
            />
            <span
              v-for="guide in activeSnapGuideStyles.horizontal"
              :key="`h-${guide.value}`"
              class="mcr-snap-guide mcr-snap-guide--horizontal"
              :style="{ top: guide.position }"
            />
          </div>
          <div v-if="polygonOverlayPoints.length" class="mcr-polygon-overlay">
            <svg class="mcr-polygon-overlay__svg" aria-hidden="true">
              <polygon
                :points="polygonOverlayPointString"
                class="mcr-polygon-overlay__shape"
              />
              <line
                v-if="polygonSnapGuide.x !== null"
                :x1="polygonSnapGuide.x"
                y1="0"
                :x2="polygonSnapGuide.x"
                y2="100%"
                class="mcr-polygon-overlay__guide"
              />
              <line
                v-if="polygonSnapGuide.y !== null"
                x1="0"
                :y1="polygonSnapGuide.y"
                x2="100%"
                :y2="polygonSnapGuide.y"
                class="mcr-polygon-overlay__guide"
              />
            </svg>
            <button
              v-for="point in polygonOverlayPoints"
              :key="point.index"
              type="button"
              class="mcr-polygon-anchor"
              :style="{ left: `${point.x}px`, top: `${point.y}px` }"
              @pointerdown.stop.prevent="startPolygonPointDrag(point.index, $event)"
              @dblclick.stop.prevent="removePolygonPoint(point.index)"
            >
              <span>{{ point.index + 1 }}</span>
            </button>
          </div>
          <div
            v-if="inlineTextEditor.visible"
            class="mcr-inline-editor"
            :style="inlineEditorStyle"
          >
            <BlueprintField
              v-model="inlineTextEditor.value"
              textarea
              rows="2"
              class="mcr-inline-editor__field"
              @keydown.enter.prevent="commitInlineTextEdit"
              @keydown.esc.prevent="cancelInlineTextEdit"
            />
            <div class="mcr-inline-editor__actions">
              <v-btn size="small" class="mcr-button mcr-button--ghost" @click="cancelInlineTextEdit">取消</v-btn>
              <v-btn size="small" class="mcr-button mcr-button--primary" @click="commitInlineTextEdit">确定</v-btn>
            </div>
          </div>
        </div>
        <div class="mcr-layout-editor-note mt-2">
          SVG 画布按比例缩放显示，保存时仍使用真实像素坐标。
        </div>
        <slot name="canvas-meta" />
        <div class="mcr-layout-footer-slot">
          <slot name="footer-actions" />
        </div>
      </div>

      </div>

      <Teleport v-if="props.floatingToolsVisible && !floatingLayerListCollapsed" to="body">
        <div
          ref="floatingLayerListEl"
          class="mcr-floating-layer-list"
          :data-mcr-theme="props.theme"
          :style="floatingLayerListStyle"
        >
          <div class="mcr-layer-list" role="listbox" aria-label="图层列表">
            <button
              type="button"
              class="mcr-layer-list__option"
              :class="{ 'mcr-layer-list__option--active': editingBackground }"
              @pointerdown.prevent
              @click="selectBackgroundFromLayerList"
            >
              <v-icon icon="mdi-image-filter-hdr-outline" size="17" />
              <span class="mcr-layer-list__content">
                <span class="mcr-layer-list__name">背景</span>
              </span>
            </button>
            <button
              v-for="layer in editableLayerList"
              :key="layer.id"
              type="button"
              class="mcr-layer-list__option"
              :class="{ 'mcr-layer-list__option--active': layer.id === selectedLayerId }"
              @pointerdown.prevent
              @click="selectLayerFromLayerList(layer.id)"
            >
              <v-icon :icon="layerListIcon(layer)" size="17" />
              <span class="mcr-layer-list__content">
                <span class="mcr-layer-list__name">{{ layerLabel(layer) }}</span>
              </span>
              <span
                role="button"
                tabindex="-1"
                class="mcr-layer-list__delete"
                :title="`删除${layerLabel(layer)}`"
                @pointerdown.stop.prevent
                @click.stop.prevent="removeLayerFromLayerList(layer.id)"
              >
                <v-icon icon="mdi-trash-can-outline" size="15" />
              </span>
            </button>
          </div>
        </div>
      </Teleport>

      <aside ref="sidePaneEl" class="mcr-layout-side-pane" :style="layoutSidePaneStyle">
        <div v-if="props.floatingToolsVisible" class="mcr-parameter-layer-header">
          <span ref="layerListButtonWrapEl" class="mcr-layer-popover-anchor">
          <v-btn
            size="small"
            class="mcr-button mcr-button--ghost mcr-layer-button"
            prepend-icon="mdi-layers-outline"
            :title="`当前图层：${currentLayerButtonLabel}`"
            @click.stop="toggleFloatingLayerList"
          >
            <span class="mcr-layer-button__label">{{ currentLayerButtonLabel }}</span>
            <v-icon icon="mdi-chevron-down" size="15" class="mcr-layer-button__chevron" />
          </v-btn>
          </span>
        </div>
      <div v-if="editingBackground" class="mcr-layer-list-wrapper mcr-background-panel">
        <BlueprintSelect
          :model-value="layout.background?.type || 'blurred-image-color'"
          :items="backgroundTypeItems"
          label="背景类型"
          @update:model-value="(val) => updateBackgroundString('type', String(val || 'blurred-image-color'))"
        />
        <v-row dense class="mt-1">
          <v-col cols="12">
            <BlueprintSelect
              :model-value="layout.background?.colorSource || 'auto'"
              :items="backgroundColorSourceItems"
              label="背景色来源"
              @update:model-value="(val) => updateBackgroundString('colorSource', String(val || 'auto'))"
            />
          </v-col>
          <v-col cols="6" v-if="(layout.background?.colorSource || 'auto') === 'custom'">
            <BlueprintField
              :model-value="layout.background?.color || editorBlendColor"
              type="color"
              label="手动颜色"
              @update:model-value="(val) => updateBackgroundString('color', String(val || defaultAutoBlendColor))"
            />
          </v-col>
          <v-col cols="6" v-if="layout.background?.type === 'gradient'">
            <BlueprintField
              :model-value="layout.background?.color2 || defaultDeepGradientColor"
              type="color"
              label="渐变色"
              @update:model-value="(val) => updateBackgroundString('color2', String(val || defaultDeepGradientColor))"
            />
          </v-col>
        </v-row>
        <BlueprintRange
          v-if="(layout.background?.type || 'blurred-image-color') !== 'transparent'"
          :model-value="(layout.background?.opacity ?? 1) * 100"
          :min="0"
          :max="100"
          :step="5"
          label="背景图层不透明度"
          @update:model-value="(val) => updateBackgroundNumeric('opacity', Number(val) / 100)"
        />
        <BlueprintRange
          :model-value="layout.background?.zIndex ?? 0"
          :min="-20"
          :max="20"
          :step="1"
          label="背景层级"
          @update:model-value="(val) => updateBackgroundNumeric('zIndex', val)"
        />
        <BlueprintRange
          v-if="(layout.background?.type || 'blurred-image-color') === 'blurred-image-color'"
          :model-value="layout.background?.colorRatio ?? effectiveParams.colorRatio"
          :min="0"
          :max="1"
          :step="0.05"
          label="颜色混合"
          @update:model-value="(val) => updateBackgroundNumeric('colorRatio', val)"
        />
        <BlueprintRange
          v-if="(layout.background?.type || 'blurred-image-color') === 'blurred-image-color'"
          :model-value="layout.background?.blur ?? effectiveParams.blur"
          :min="0"
          :max="100"
          :step="1"
          label="背景模糊"
          @update:model-value="(val) => updateBackgroundNumeric('blur', val)"
        />
        <BlueprintRange
          :model-value="layout.background?.grain ?? 0"
          :min="0"
          :max="1"
          :step="0.02"
          label="胶片颗粒"
          @update:model-value="(val) => updateBackgroundNumeric('grain', val)"
        />
        <v-switch
          :model-value="Boolean(layout.background?.maskPolygon)"
          inset
          density="compact"
          hide-details
          label="背景多边形裁剪"
          @update:model-value="(val) => toggleBackgroundPolygon(Boolean(val))"
        />
        <div v-if="layout.background?.maskPolygon" class="mcr-polygon-actions">
          <v-btn size="small" class="mcr-button mcr-button--ghost" @click="addPolygonPoint">添加锚点</v-btn>
          <v-btn size="small" class="mcr-button mcr-button--ghost" @click="resetActivePolygon">重置矩形</v-btn>
        </div>
      </div>

      <!-- 右侧：选中图层属性（适配手机，宽高/层级/旋转改为滑块） -->
      <div v-if="selectedLayer" class="mcr-layout-bottom mt-4">

      <v-row dense>
        <v-col cols="12">
          <BlueprintRange
            :model-value="selectedLayer.x"
            :min="-CANVAS_WIDTH"
            :max="CANVAS_WIDTH"
            :step="1"
            label="X"
            @update:model-value="(val) => updateSelectedNumeric('x', val)"
          />
        </v-col>
        <v-col cols="12">
          <BlueprintRange
            :model-value="selectedLayer.y"
            :min="-CANVAS_HEIGHT"
            :max="CANVAS_HEIGHT"
            :step="1"
            label="Y"
            @update:model-value="(val) => updateSelectedNumeric('y', val)"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1">
        <v-col cols="12" v-if="isImageLayer(selectedLayer) && selectedLayer.assetKind !== 'sticker'">
          <BlueprintField
            :model-value="selectedLayer.sourceIndex"
            type="number"
            label="素材索引"
            @update:model-value="(val) => updateSelectedNumeric('sourceIndex', val)"
          />
        </v-col>
        <v-col cols="12" v-if="isImageLayer(selectedLayer)">
          <BlueprintSelect
            :model-value="selectedLayer.fit || 'cover'"
            :items="imageFitItems"
            :label="selectedLayer.assetKind === 'sticker' ? '贴图适配' : '图片适配'"
            @update:model-value="(val) => updateSelectedString('fit', String(val || 'cover'))"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1" v-if="isImageLayer(selectedLayer)">
        <v-col cols="12" class="d-flex align-center">
          <v-switch
            v-model="cropModeEnabled"
            inset
            density="compact"
            hide-details
            label="画布裁剪模式"
          />
        </v-col>
        <v-col cols="12">
          <BlueprintRange
            :model-value="(selectedLayer.cropFocusX ?? 0.5) * 100"
            :min="0"
            :max="100"
            :step="1"
            label="裁剪焦点 X%"
            @update:model-value="(val) => updateSelectedNumeric('cropFocusX', Number(val) / 100)"
          />
        </v-col>
        <v-col cols="12">
          <BlueprintRange
            :model-value="(selectedLayer.cropFocusY ?? 0.5) * 100"
            :min="0"
            :max="100"
            :step="1"
            label="裁剪焦点 Y%"
            @update:model-value="(val) => updateSelectedNumeric('cropFocusY', Number(val) / 100)"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1" v-if="isImageLayer(selectedLayer)">
        <v-col cols="12">
          <BlueprintSelect
            :model-value="selectedLayer.colorSource || 'none'"
            :items="layerColorSourceItems"
            label="图片混色来源"
            @update:model-value="(val) => updateSelectedString('colorSource', String(val || 'none'))"
          />
        </v-col>
        <v-col cols="6" v-if="(selectedLayer.colorSource || 'none') === 'custom'">
          <BlueprintField
            :model-value="selectedLayer.color || editorBlendColor"
            type="color"
            label="混合颜色"
            @update:model-value="(val) => updateSelectedString('color', String(val || defaultAutoBlendColor))"
          />
        </v-col>
        <v-col cols="12" v-if="(selectedLayer.colorSource || 'none') !== 'none'">
          <BlueprintRange
            :model-value="(selectedLayer.colorRatio ?? 0.8) * 100"
            :min="0"
            :max="100"
            :step="5"
            label="混色强度"
            @update:model-value="(val) => updateSelectedNumeric('colorRatio', Number(val) / 100)"
          />
        </v-col>
        <v-col cols="12">
          <v-switch
            :model-value="Boolean(selectedLayer.maskPolygon)"
            inset
            density="compact"
            hide-details
            label="多边形裁剪"
            @update:model-value="(val) => toggleSelectedPolygon(Boolean(val))"
          />
        </v-col>
        <v-col cols="12" v-if="selectedLayer.maskPolygon" class="mcr-polygon-actions">
          <v-btn size="small" class="mcr-button mcr-button--ghost" @click="addPolygonPoint">添加锚点</v-btn>
          <v-btn size="small" class="mcr-button mcr-button--ghost" @click="resetActivePolygon">重置矩形</v-btn>
        </v-col>
      </v-row>

      <v-row dense class="mt-1">
        <v-col cols="12" v-if="isCustomTextLayer(selectedLayer)">
          <BlueprintSelect
            :model-value="selectedLayer.contentSource || 'fixed'"
            :items="textContentSourceItems"
            label="文本来源"
            @update:model-value="(val) => updateSelectedString('contentSource', String(val || 'fixed'))"
          />
        </v-col>
        <v-col cols="12" v-if="isCustomTextLayer(selectedLayer) && (selectedLayer.contentSource || 'fixed') === 'library'">
          <BlueprintField
            :model-value="selectedLayer.contentKey || ''"
            label="配置文本键"
            placeholder="默认 default，可填 slogan / note 等"
            @update:model-value="(val) => updateSelectedString('contentKey', String(val || ''))"
          />
        </v-col>
        <v-col cols="12" v-if="isCustomTextLayer(selectedLayer)">
          <BlueprintField
            :model-value="selectedLayer.content"
            textarea
            rows="2"
            :label="(selectedLayer.contentSource || 'fixed') === 'library' ? '备用文本内容' : '文本内容'"
            @update:model-value="(val) => updateSelectedString('content', String(val || ''))"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1">
        <v-col cols="12" v-if="isTextLayer(selectedLayer)">
          <BlueprintSelect
            :model-value="selectedLayer.fontFamily || 'main_title'"
            :items="fontFamilyItems"
            label="字体族"
            @update:model-value="(val) => updateSelectedString('fontFamily', String(val || 'main_title'))"
          />
        </v-col>
        <v-col cols="12" v-if="isTextLayer(selectedLayer)">
          <BlueprintRange
            :model-value="selectedLayer.fontSize"
            :min="12"
            :max="320"
            :step="1"
            label="字体大小"
            @update:model-value="(val) => updateSelectedNumeric('fontSize', val)"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1" v-if="isTextLayer(selectedLayer)">
        <v-col cols="12">
          <div class="mcr-text-align-control" aria-label="文字排版">
            <button
              v-for="item in textAlignItems"
              :key="item.value"
              type="button"
              class="mcr-text-align-button"
              :class="{ 'mcr-text-align-button--active': (selectedLayer.textAlign || 'center') === item.value }"
              :title="item.title"
              :aria-label="item.title"
              :aria-pressed="(selectedLayer.textAlign || 'center') === item.value"
              @click="updateSelectedString('textAlign', item.value)"
            >
              <v-icon :icon="item.icon" size="18" />
            </button>
          </div>
        </v-col>
        <v-col cols="12">
          <BlueprintSelect
            :model-value="selectedLayer.maskMode || 'normal'"
            :items="textMaskModeItems"
            label="文字镂空"
            @update:model-value="(val) => updateSelectedString('maskMode', String(val || 'normal'))"
          />
        </v-col>
        <v-col cols="12">
          <BlueprintSelect
            :model-value="selectedLayer.colorSource || 'custom'"
            :items="textColorSourceItems"
            label="文字颜色来源"
            @update:model-value="(val) => updateSelectedString('colorSource', String(val || 'custom'))"
          />
        </v-col>
        <v-col cols="12" v-if="(selectedLayer.colorSource || 'custom') === 'custom'">
          <BlueprintField
            :model-value="selectedLayer.color || defaultTextColor"
            type="color"
            label="文字颜色"
            @update:model-value="(val) => updateSelectedString('color', String(val || defaultTextColor))"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1">
        <v-col cols="12" class="d-flex align-center">
          <v-switch
            v-model="lockAspectRatio"
            inset
            density="compact"
            hide-details
            class="mr-2"
            label="锁定宽高比例"
          />
        </v-col>
        <v-col v-if="lockAspectRatio" cols="12">
          <div class="mcr-aspect-presets" aria-label="宽高比例预设">
            <button
              v-for="preset in aspectRatioPresets"
              :key="preset.label"
              type="button"
              class="mcr-aspect-preset"
              @pointerdown.prevent
              @click="applySelectedAspectRatio(preset.ratio)"
            >
              {{ preset.label }}
            </button>
          </div>
        </v-col>
      </v-row>

      <v-row dense class="mt-1">
        <v-col cols="12">
          <BlueprintRange
            :model-value="selectedLayer.width"
            :min="CANVAS_WIDTH * 0.1"
            :max="CANVAS_WIDTH"
            :step="10"
            label="宽度"
            @start="onSliderStart"
            @end="onSliderEnd"
            @change="(val) => onSizeSliderChange('width', val)"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1">
        <v-col cols="12">
          <BlueprintRange
            :model-value="selectedLayer.height"
            :min="CANVAS_HEIGHT * 0.1"
            :max="CANVAS_HEIGHT"
            :step="10"
            label="高度"
            @start="onSliderStart"
            @end="onSliderEnd"
            @change="(val) => onSizeSliderChange('height', val)"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1">
        <v-col cols="12">
          <BlueprintRange
            :model-value="(selectedLayer.opacity ?? 1) * 100"
            :min="10"
            :max="100"
            :step="5"
            label="不透明度"
            @update:model-value="(val) => updateSelectedNumeric('opacity', Number(val) / 100)"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1">
        <v-col cols="12">
          <BlueprintRange
            :model-value="selectedLayer.blur ?? 0"
            :min="0"
            :max="40"
            :step="1"
            label="模糊"
            @update:model-value="(val) => updateSelectedNumeric('blur', val)"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1">
        <v-col cols="12">
          <BlueprintRange
            :model-value="selectedLayer.shadowBlur ?? 0"
            :min="0"
            :max="60"
            :step="1"
            label="阴影模糊"
            @update:model-value="(val) => updateSelectedNumeric('shadowBlur', val)"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1">
        <v-col cols="12">
          <BlueprintRange
            :model-value="selectedLayer.shadowOffsetX ?? 0"
            :min="-200"
            :max="200"
            :step="1"
            label="阴影 X 偏移"
            @update:model-value="(val) => updateSelectedNumeric('shadowOffsetX', val)"
          />
        </v-col>
        <v-col cols="12">
          <BlueprintRange
            :model-value="selectedLayer.shadowOffsetY ?? 0"
            :min="-200"
            :max="200"
            :step="1"
            label="阴影 Y 偏移"
            @update:model-value="(val) => updateSelectedNumeric('shadowOffsetY', val)"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1">
        <v-col cols="12">
          <BlueprintRange
            :model-value="(selectedLayer.shadowOpacity ?? 0.28) * 100"
            :min="0"
            :max="100"
            :step="5"
            label="阴影强度"
            @update:model-value="(val) => updateSelectedNumeric('shadowOpacity', Number(val) / 100)"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1">
        <v-col cols="12">
          <BlueprintRange
            :model-value="selectedLayer.radius ?? 0"
            :min="0"
            :max="240"
            :step="1"
            label="圆角"
            @update:model-value="(val) => updateSelectedNumeric('radius', val)"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1">
        <v-col cols="12">
          <BlueprintRange
            :model-value="selectedLayer.zIndex"
            :min="-20"
            :max="Math.max(20, layout.layers.length + 2)"
            :step="1"
            label="层级 (zIndex)"
            @update:model-value="(val) => updateSelectedNumeric('zIndex', val)"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1">
        <v-col cols="12">
          <BlueprintRange
            :model-value="selectedLayer.rotation ?? 0"
            :min="-180"
            :max="180"
            :step="1"
            label="旋转角度"
            @update:model-value="(val) => updateSelectedNumeric('rotation', val)"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-1">
        <v-col cols="12">
          <BlueprintRange
            :model-value="(selectedLayer.pivotX ?? 0.5) * 100"
            :min="0"
            :max="100"
            :step="5"
            label="旋转中心 X%"
            @update:model-value="(val) => updateSelectedNumeric('pivotX', Number(val) / 100)"
          />
        </v-col>
        <v-col cols="12">
          <BlueprintRange
            :model-value="(selectedLayer.pivotY ?? 0.5) * 100"
            :min="0"
            :max="100"
            :step="5"
            label="旋转中心 Y%"
            @update:model-value="(val) => updateSelectedNumeric('pivotY', Number(val) / 100)"
          />
        </v-col>
      </v-row>

      </div>
      </aside>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import '../styles/figmaTheme.css'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type {
  CustomMeasuredTextLayout,
  CustomStaticLayout,
  CustomGroupLayer,
  CustomImageLayer,
  CustomTextLayer,
  CustomTitleLayer,
  PluginApi,
  PreviewSourcePayload,
  SimulationParams,
  TemplateLayer,
  TemplateMaskPolygon,
} from '../types/plugin'
import {
  cloneLayout,
  createTextLayer,
  getLayerShadowStyle,
  getTextLayerFontFamily,
  isCustomTextLayer,
  isImageLayer,
  isMainTitleLayer,
  isTextLayer,
  isTitleLayer,
  normalizeLayerEffects,
} from '../utils/customLayout'
import {
  buildBackgroundStyle,
  buildOverlayStyle,
  extractComfortableColor,
  getKonvaFontFamily,
  resolveBlendColor,
} from '../utils/renderSimulation'
import BlueprintField from './BlueprintField.vue'
import BlueprintRange from './BlueprintRange.vue'
import BlueprintSelect from './BlueprintSelect.vue'
import SvgTemplatePreview from './SvgTemplatePreview.vue'
import { useTemplateCanvasStore } from '../stores/templateCanvas'
import { BUILTIN_FONT_ITEMS, SEMANTIC_FONT_ITEMS } from '../constants/fonts'
import { getThemeColor, getThemeRgba } from '../utils/themeColors'
import { loadPreviewFontFaces } from '../services/fontPreview'

type AnyLayer = TemplateLayer

type DragMode = 'move' | 'resize' | 'rotate'

interface StickerLibraryItem {
  name: string
  path: string
  url?: string
  dataUrl?: string
  width?: number
  height?: number
  size?: number
  mtime?: number
}

interface FontLibraryItem {
  title: string
  name: string
  value: string
  path?: string
  url?: string
  dataUrl?: string
  size?: number
  mtime?: number
}

const CANVAS_WIDTH = 1920
const CANVAS_HEIGHT = 1080
const LAYER_POPOVER_WIDTH = 204
const LAYER_POPOVER_FALLBACK_HEIGHT = 252
const FLOATING_LAYER_MARGIN = 12

const props = withDefaults(defineProps<{
  modelValue: CustomStaticLayout
  previewSource?: PreviewSourcePayload | null
  params?: SimulationParams
  embedded?: boolean
  autoSaveEnabled?: boolean
  floatingToolsVisible?: boolean
  theme?: 'light' | 'dark'
  api?: PluginApi
}>(), {
  floatingToolsVisible: true,
  theme: 'light',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: CustomStaticLayout): void
}>()

const lockAspectRatio = ref<boolean>(false)
const cropModeEnabled = ref<boolean>(false)
const floatingLayerListCollapsed = ref(true)
const floatingLayerListPosition = ref({ x: FLOATING_LAYER_MARGIN, y: 120 })
const layerListButtonWrapEl = ref<HTMLElement | null>(null)
const floatingLayerListEl = ref<HTMLElement | null>(null)
let sliderActive = false
const inlineTextEditor = ref({
  visible: false,
  layerId: '',
  value: '',
  x: 0,
  y: 0,
  width: 320,
})
const customFontItems = ref<FontLibraryItem[]>([])
const fontFamilyItems = computed(() => [
  ...SEMANTIC_FONT_ITEMS,
  ...BUILTIN_FONT_ITEMS,
  ...customFontItems.value.map((item) => ({ title: `自定义 ${item.title}`, value: item.value })),
])
const backgroundTypeItems = [
  { title: '透明背景', value: 'transparent' },
  { title: '纯色', value: 'solid' },
  { title: '渐变色', value: 'gradient' },
  { title: '模糊主图混合所选颜色', value: 'blurred-image-color' },
]
const backgroundColorSourceItems = [
  { title: '从主图自动取色', value: 'auto' },
  { title: '手动指定', value: 'custom' },
  { title: '配置指定', value: 'config' },
]
const layerColorSourceItems = [
  { title: '不混色', value: 'none' },
  { title: '从主图自动取色', value: 'auto' },
  { title: '手动指定', value: 'custom' },
  { title: '配置指定', value: 'config' },
]
const textColorSourceItems = [
  { title: '跟随主图/主题', value: 'auto' },
  { title: '手动指定', value: 'custom' },
  { title: '配置指定', value: 'config' },
]
const textAlignItems = [
  { title: '靠左', value: 'left', icon: 'mdi-format-align-left' },
  { title: '居中', value: 'center', icon: 'mdi-format-align-center' },
  { title: '靠右', value: 'right', icon: 'mdi-format-align-right' },
] as const
const textContentSourceItems = [
  { title: '固定文本', value: 'fixed' },
  { title: '按媒体库配置', value: 'library' },
] as const
const textMaskModeItems = [
  { title: '普通文字', value: 'normal' },
  { title: '镂空字体区域', value: 'knockout-text' },
  { title: '仅显示字体覆盖范围', value: 'show-text' },
] as const
const imageFitItems = [
  { title: 'Cover 裁切填满', value: 'cover' },
  { title: 'Contain 完整显示', value: 'contain' },
  { title: 'Stretch 拉伸', value: 'stretch' },
]
const aspectRatioPresets = [
  { label: '1:1', ratio: 1 },
  { label: '4:3', ratio: 4 / 3 },
  { label: '3:4', ratio: 3 / 4 },
  { label: '16:9', ratio: 16 / 9 },
  { label: '9:16', ratio: 9 / 16 },
  { label: '3:2', ratio: 3 / 2 },
  { label: '2:3', ratio: 2 / 3 },
  { label: '21:9', ratio: 21 / 9 },
]

const internalLayout = ref<CustomStaticLayout>(cloneLayout(props.modelValue))
const fontRevision = ref(0)

const templateCanvasStore = useTemplateCanvasStore()
const selectedLayerId = computed({
  get: () => templateCanvasStore.selectedLayerId ?? null,
  set: (id: string | null) => templateCanvasStore.selectLayer(id),
})
const editingBackground = computed(() => !selectedLayerId.value)
const floatingLayerListStyle = computed(() => ({
  left: `${floatingLayerListPosition.value.x}px`,
  top: `${floatingLayerListPosition.value.y}px`,
}))
const polygonSnapGuide = ref<{ x: number | null; y: number | null }>({ x: null, y: null })

interface PolygonContext {
  target: 'background' | 'layer'
  layerId?: string
  x: number
  y: number
  width: number
  height: number
  mask: TemplateMaskPolygon
}

const activePolygonContext = computed<PolygonContext | null>(() => {
  if (editingBackground.value && layout.value.background?.maskPolygon) {
    return {
      target: 'background',
      x: 0,
      y: 0,
      width: CANVAS_WIDTH,
      height: CANVAS_HEIGHT,
      mask: layout.value.background.maskPolygon,
    }
  }
  const layer = selectedLayer.value
  if (layer && isImageLayer(layer) && layer.maskPolygon) {
    return {
      target: 'layer',
      layerId: layer.id,
      x: layer.x,
      y: layer.y,
      width: layer.width,
      height: layer.height,
      mask: layer.maskPolygon,
    }
  }
  return null
})

function normalizePolygonPoint(point: [number, number], context: PolygonContext) {
  if (context.mask.units === 'absolute') {
    return [
      Math.max(0, Math.min(1, (Number(point[0]) - context.x) / Math.max(1, context.width))),
      Math.max(0, Math.min(1, (Number(point[1]) - context.y) / Math.max(1, context.height))),
    ] as [number, number]
  }
  return [
    Math.max(0, Math.min(1, Number(point[0]))),
    Math.max(0, Math.min(1, Number(point[1]))),
  ] as [number, number]
}

const activePolygonRelativePoints = computed(() => {
  const context = activePolygonContext.value
  if (!context) return [] as Array<[number, number]>
  return (context.mask.points || [])
    .filter((point) => Array.isArray(point) && point.length >= 2)
    .map((point) => normalizePolygonPoint(point, context))
})

const polygonOverlayPoints = computed(() => {
  const context = activePolygonContext.value
  if (!context) return [] as Array<{ index: number; x: number; y: number }>
  return activePolygonRelativePoints.value.map((point, index) => ({
    index,
    x: (context.x + point[0] * context.width) * canvasScale.value,
    y: (context.y + point[1] * context.height) * canvasScale.value,
  }))
})

const polygonOverlayPointString = computed(() =>
  polygonOverlayPoints.value.map((point) => `${point.x},${point.y}`).join(' '),
)

watch(
  () => props.modelValue,
  (val) => {
    const nextLayout = cloneLayout(val)
    internalLayout.value = nextLayout
    const currentId = selectedLayerId.value
    const existsInNew = currentId && findLayerById(nextLayout.layers, currentId)
    if (!existsInNew) {
      selectedLayerId.value = null
    }
  },
  { deep: true },
)

watch(
  () => props.previewSource?.images,
  () => {
    if (typeof window !== 'undefined') {
      refreshImageRegistry()
    }
  },
  { deep: true, immediate: true },
)

watch(
  () => getEditableLayers(internalLayout.value.layers)
    .filter((layer): layer is CustomImageLayer => isImageLayer(layer))
    .map((layer) => `${layer.id}:${layer.assetKind || ''}:${layer.stickerDataUrl || ''}:${layer.stickerUrl || ''}:${layer.stickerPath || ''}`)
    .join('|'),
  () => {
    if (typeof window !== 'undefined') {
      refreshImageRegistry()
    }
  },
)

watch(
  () => props.previewSource?.font_faces,
  async (fontFaces) => {
    await loadPreviewFontFaces(fontFaces)
    fontRevision.value += 1
  },
  { deep: true, immediate: true },
)

const layout = computed(() => internalLayout.value)
const editableLayerList = computed(() => getEditableLayers(layout.value.layers))

const editorRootEl = ref<HTMLElement | null>(null)
const canvasEl = ref<HTMLElement | null>(null)
const canvasPaneEl = ref<HTMLElement | null>(null)
const layerActionsEl = ref<HTMLElement | null>(null)
const sidePaneEl = ref<HTMLElement | null>(null)
const stickerFileInputEl = ref<HTMLInputElement | null>(null)
const canvasScale = ref(1)
const canvasPaneDisplayHeight = ref(0)
const imageRegistry = ref<Record<string, HTMLImageElement>>({})
const stickerLibraryOpen = ref(false)
const stickerLibraryLoading = ref(false)
const stickerLibraryItems = ref<StickerLibraryItem[]>([])
const transformerRef = ref<any>(null)
const layerNodeRegistry = new Map<string, any>()
let canvasResizeObserver: ResizeObserver | null = null
let canvasPaneResizeObserver: ResizeObserver | null = null
let windowResizeAttached = false
const defaultAutoBlendColor = computed(() => getThemeColor('--mcr-cover-auto-blend'))
const defaultDeepGradientColor = computed(() => getThemeColor('--mcr-cover-deep-gradient'))
const defaultTextColor = computed(() => '#ffffff')

async function loadFontLibrary() {
  if (!props.api?.get) return
  try {
    const resp = await props.api.get<{ code: number; data?: { custom?: FontLibraryItem[] }; msg?: string }>('plugin/YahahaCoverStudio/fonts')
    if (!resp || resp.code !== 0) {
      throw new Error(resp?.msg || 'load fonts failed')
    }
    customFontItems.value = Array.isArray(resp.data?.custom) ? resp.data.custom : []
  } catch (error) {
    console.warn('load editor font library failed', error)
  }
}

function getEditableLayers(layers: TemplateLayer[]): TemplateLayer[] {
  return layers.flatMap((layer) => (
    layer.type === 'group'
      ? [layer, ...getEditableLayers((layer as CustomGroupLayer).children || [])]
      : [layer]
  ))
}

function findLayerById(layers: TemplateLayer[], id?: string | null): TemplateLayer | null {
  if (!id) return null
  for (const layer of layers) {
    if (layer.id === id) return layer
    if (layer.type === 'group') {
      const child = findLayerById((layer as CustomGroupLayer).children || [], id)
      if (child) return child
    }
  }
  return null
}

function updateLayerById(layers: TemplateLayer[], id: string, updater: (layer: TemplateLayer) => TemplateLayer | void): boolean {
  for (let index = 0; index < layers.length; index += 1) {
    const layer = layers[index]
    if (layer.id === id) {
      const updated = updater(layer)
      layers[index] = updated ? normalizeLayerEffects(updated) : normalizeLayerEffects({ ...layer })
      return true
    }
    if (layer.type === 'group') {
      const group = layer as CustomGroupLayer
      if (updateLayerById(group.children || [], id, updater)) {
        layers[index] = normalizeLayerEffects({ ...group, children: [...(group.children || [])] })
        return true
      }
    }
  }
  return false
}

function removeLayerById(layers: TemplateLayer[], id: string): boolean {
  const index = layers.findIndex((layer) => layer.id === id)
  if (index !== -1) {
    layers.splice(index, 1)
    return true
  }
  for (let layerIndex = 0; layerIndex < layers.length; layerIndex += 1) {
    const layer = layers[layerIndex]
    if (layer.type !== 'group') continue
    const group = layer as CustomGroupLayer
    if (removeLayerById(group.children || [], id)) {
      layers[layerIndex] = normalizeLayerEffects({ ...group, children: [...(group.children || [])] })
      return true
    }
  }
  return false
}

function updateLayout(mutator: (layout: CustomStaticLayout) => void) {
  const next = cloneLayout(internalLayout.value)
  mutator(next)
  internalLayout.value = next
  emit('update:modelValue', next)
}

type BackgroundStringKey = 'type' | 'color' | 'color2' | 'colorSource'
type BackgroundNumericKey = 'colorRatio' | 'opacity' | 'blur' | 'grain' | 'zIndex'

function updateBackgroundString(key: BackgroundStringKey, value: string) {
  updateLayout((layout) => {
    layout.background = {
      type: 'blurred-image-color',
      imageSource: { kind: 'slot', slot: 1 },
      colorSource: 'auto',
      color: editorBlendColor.value,
      color2: defaultDeepGradientColor.value,
      colorRatio: effectiveParams.value.colorRatio,
      opacity: 1,
      blur: effectiveParams.value.blur,
      grain: 0.18,
      zIndex: 0,
      ...(layout.background || {}),
      [key]: value,
    }
  })
}

function updateBackgroundNumeric(key: BackgroundNumericKey, raw: string | number) {
  const num = typeof raw === 'number' ? raw : Number(raw)
  if (Number.isNaN(num)) return
  updateLayout((layout) => {
    layout.background = {
      type: 'blurred-image-color',
      imageSource: { kind: 'slot', slot: 1 },
      colorSource: 'auto',
      color: editorBlendColor.value,
      color2: defaultDeepGradientColor.value,
      colorRatio: effectiveParams.value.colorRatio,
      opacity: 1,
      blur: effectiveParams.value.blur,
      grain: 0.18,
      zIndex: 0,
      ...(layout.background || {}),
      [key]: num,
    }
  })
}

const selectedLayer = computed<AnyLayer | null>(() => {
  return findLayerById(layout.value.layers, selectedLayerId.value)
})
const currentLayerButtonLabel = computed(() => selectedLayer.value ? layerLabel(selectedLayer.value) : '背景')
const selectedLayerPanelTitle = computed(() => {
  const layer = selectedLayer.value
  if (!layer) return '图层'
  if (layer.type === 'group') return '图层组'
  if (isImageLayer(layer)) return layer.assetKind === 'sticker' ? '贴图图层' : '图片图层'
  if (isCustomTextLayer(layer)) return '文本图层'
  return isMainTitleLayer(layer) ? '主标题图层' : '副标题图层'
})

const activeTitles = computed(() => props.previewSource?.titles || { zh: '', en: '' })
const firstImage = computed(() => props.previewSource?.images?.[0] || null)
const autoBlendColor = ref(getThemeColor('--mcr-cover-auto-blend'))
const effectiveParams = computed<SimulationParams>(() => props.params || {
  blur: 50,
  colorRatio: 0.8,
  colorSource: 'auto',
  customColor: defaultAutoBlendColor.value,
})
const editorBlendColor = computed(() => resolveBlendColor(props.previewSource || null, effectiveParams.value, autoBlendColor.value))

const canvasBackgroundStyle = computed(() => buildBackgroundStyle(firstImage.value?.src, effectiveParams.value.blur))

const canvasOverlayStyle = computed(() => buildOverlayStyle(editorBlendColor.value, effectiveParams.value.colorRatio))
const canvasFixedStyle = computed(() => ({
  transform: `scale(${canvasScale.value})`,
}))
const stageConfig = computed(() => ({
  width: CANVAS_WIDTH,
  height: CANVAS_HEIGHT,
}))
const SNAP_THRESHOLD = 18
const CANVAS_VERTICAL_SNAP_TARGETS = [0, CANVAS_WIDTH / 4, CANVAS_WIDTH / 2, CANVAS_WIDTH * 3 / 4, CANVAS_WIDTH]
const CANVAS_HORIZONTAL_SNAP_TARGETS = [0, CANVAS_HEIGHT / 4, CANVAS_HEIGHT / 2, CANVAS_HEIGHT * 3 / 4, CANVAS_HEIGHT]

const activeSnapGuides = ref<{ vertical: number[]; horizontal: number[] }>({ vertical: [], horizontal: [] })
const activeSnapGuideStyles = computed(() => ({
  vertical: activeSnapGuides.value.vertical.map((value) => ({
    value,
    position: `${value * canvasScale.value}px`,
  })),
  horizontal: activeSnapGuides.value.horizontal.map((value) => ({
    value,
    position: `${value * canvasScale.value}px`,
  })),
}))

function uniqueGuideValues(values: Array<number | null | undefined>) {
  return Array.from(new Set(
    values
      .filter((value): value is number => Number.isFinite(Number(value)))
      .map((value) => Math.round(value)),
  ))
}

function snapAxisPosition(
  position: number,
  size: number,
  targets: number[],
) {
  const anchors = [0, size / 2, size]
  let bestDelta = 0
  let bestTarget: number | null = null
  let bestDistance = Number.POSITIVE_INFINITY

  for (const anchor of anchors) {
    const current = position + anchor
    for (const target of targets) {
      const distance = Math.abs(current - target)
      if (distance <= SNAP_THRESHOLD && distance < bestDistance) {
        bestDistance = distance
        bestDelta = target - current
        bestTarget = target
      }
    }
  }

  return {
    position: bestTarget === null ? position : position + bestDelta,
    guide: bestTarget,
  }
}

function snapLayerPosition(x: number, y: number, layer: TemplateLayer) {
  const snapX = snapAxisPosition(x, Number(layer.width || 0), CANVAS_VERTICAL_SNAP_TARGETS)
  const snapY = snapAxisPosition(y, Number(layer.height || 0), CANVAS_HORIZONTAL_SNAP_TARGETS)
  activeSnapGuides.value = {
    vertical: uniqueGuideValues([snapX.guide]),
    horizontal: uniqueGuideValues([snapY.guide]),
  }
  return {
    x: snapX.position,
    y: snapY.position,
  }
}

function buildGuideLine(points: number[]) {
  return {
    points,
    stroke: getThemeRgba('--mcr-editor-snap-rgb', 0.92),
    strokeWidth: 2,
    dash: [10, 8],
    listening: false,
  }
}

function findTextSnapTargets(layer: AnyLayer) {
  if (isImageLayer(layer)) return { vertical: null as any, horizontal: null as any }
  const currentLeft = layer.x
  const currentCenterX = layer.x + layer.width / 2
  const currentRight = layer.x + layer.width
  const currentTop = layer.y
  const currentCenterY = layer.y + layer.height / 2
  const currentBottom = layer.y + layer.height

  let vertical: any = null
  let horizontal: any = null

  const candidates = layout.value.layers.filter((item) => item.id !== layer.id && !isImageLayer(item))
  for (const item of candidates) {
    const left = item.x
    const centerX = item.x + item.width / 2
    const right = item.x + item.width
    const top = item.y
    const centerY = item.y + item.height / 2
    const bottom = item.y + item.height

    if (!vertical) {
      if (Math.abs(currentCenterX - centerX) <= SNAP_THRESHOLD) vertical = buildGuideLine([centerX, 0, centerX, CANVAS_HEIGHT])
      else if (Math.abs(currentLeft - left) <= SNAP_THRESHOLD) vertical = buildGuideLine([left, 0, left, CANVAS_HEIGHT])
      else if (Math.abs(currentRight - right) <= SNAP_THRESHOLD) vertical = buildGuideLine([right, 0, right, CANVAS_HEIGHT])
    }
    if (!horizontal) {
      if (Math.abs(currentCenterY - centerY) <= SNAP_THRESHOLD) horizontal = buildGuideLine([0, centerY, CANVAS_WIDTH, centerY])
      else if (Math.abs(currentTop - top) <= SNAP_THRESHOLD) horizontal = buildGuideLine([0, top, CANVAS_WIDTH, top])
      else if (Math.abs(currentBottom - bottom) <= SNAP_THRESHOLD) horizontal = buildGuideLine([0, bottom, CANVAS_WIDTH, bottom])
    }
    if (vertical && horizontal) break
  }
  return { vertical, horizontal }
}

const alignmentGuides = computed(() => {
  const layer = selectedLayer.value
  if (!layer || isImageLayer(layer)) {
    return { vertical: null, horizontal: null }
  }
  const layerCenterX = layer.x + layer.width / 2
  const layerCenterY = layer.y + layer.height / 2
  const stageCenterX = CANVAS_WIDTH / 2
  const stageCenterY = CANVAS_HEIGHT / 2
  const ownVertical = Math.abs(layerCenterX - stageCenterX) <= SNAP_THRESHOLD ? buildGuideLine([stageCenterX, 0, stageCenterX, CANVAS_HEIGHT]) : null
  const ownHorizontal = Math.abs(layerCenterY - stageCenterY) <= SNAP_THRESHOLD ? buildGuideLine([0, stageCenterY, CANVAS_WIDTH, stageCenterY]) : null
  const peer = findTextSnapTargets(layer)
  return {
    vertical: ownVertical || peer.vertical,
    horizontal: ownHorizontal || peer.horizontal,
  }
})
const showAlignmentGuides = computed(() => Boolean(alignmentGuides.value.vertical || alignmentGuides.value.horizontal))
const inlineEditorStyle = computed(() => ({
  left: `${inlineTextEditor.value.x * canvasScale.value}px`,
  top: `${inlineTextEditor.value.y * canvasScale.value}px`,
  width: `${inlineTextEditor.value.width * canvasScale.value}px`,
}))
const transformerConfig = computed(() => ({
  rotateEnabled: true,
  enabledAnchors: [
    'top-left',
    'top-center',
    'top-right',
    'middle-left',
    'middle-right',
    'bottom-left',
    'bottom-center',
    'bottom-right',
  ],
  borderStroke: getThemeColor('--mcr-color-primary-container'),
  anchorStroke: getThemeColor('--mcr-color-primary-container'),
  anchorFill: getThemeColor('--mcr-color-surface-container-lowest'),
  anchorSize: 10,
  keepRatio: lockAspectRatio.value,
}))

function updateCanvasScale() {
  const canvas = canvasEl.value
  if (!canvas) return
  const width = canvas.clientWidth || 1
  canvasScale.value = width / CANVAS_WIDTH
  canvasPaneDisplayHeight.value = canvasPaneEl.value?.clientHeight || canvas.clientHeight || Math.round(width * CANVAS_HEIGHT / CANVAS_WIDTH)
  positionFloatingLayerListNearToolbar()
}

const layoutSidePaneStyle = computed(() => (
  canvasPaneDisplayHeight.value > 0
    ? { height: `${canvasPaneDisplayHeight.value}px` }
    : undefined
))

type ScrollSnapshot = Array<{ el: HTMLElement; top: number; left: number }>

function isScrollableContainer(el: HTMLElement) {
  const style = window.getComputedStyle(el)
  return /(auto|scroll|overlay)/.test(style.overflowY) && el.scrollHeight > el.clientHeight + 2
}

function captureEditorScrollSnapshot(): ScrollSnapshot {
  if (typeof window === 'undefined') return []
  const snapshot: ScrollSnapshot = []
  const seen = new Set<HTMLElement>()
  const root = editorRootEl.value
  let current = root?.parentElement || null
  while (current && current !== document.body && current !== document.documentElement) {
    if (isScrollableContainer(current) && !seen.has(current)) {
      seen.add(current)
      snapshot.push({ el: current, top: current.scrollTop, left: current.scrollLeft })
    }
    current = current.parentElement
  }
  document.querySelectorAll<HTMLElement>('*').forEach((el) => {
    if (seen.has(el)) return
    if (!isScrollableContainer(el)) return
    seen.add(el)
    snapshot.push({ el, top: el.scrollTop, left: el.scrollLeft })
  })
  const documentScroller = document.scrollingElement as HTMLElement | null
  if (documentScroller && !seen.has(documentScroller)) {
    snapshot.push({ el: documentScroller, top: documentScroller.scrollTop, left: documentScroller.scrollLeft })
  }
  return snapshot
}

function restoreEditorScrollSnapshot(snapshot: ScrollSnapshot) {
  for (const item of snapshot) {
    item.el.scrollTop = item.top
    item.el.scrollLeft = item.left
  }
}

function preserveEditorScrollAfter(callback: () => void) {
  const snapshot = captureEditorScrollSnapshot()
  callback()
  nextTick(() => {
    restoreEditorScrollSnapshot(snapshot)
    if (typeof window !== 'undefined') {
      window.requestAnimationFrame(() => restoreEditorScrollSnapshot(snapshot))
      window.setTimeout(() => restoreEditorScrollSnapshot(snapshot), 120)
      window.setTimeout(() => restoreEditorScrollSnapshot(snapshot), 260)
    }
  })
}

function selectLayer(id: string) {
  preserveEditorScrollAfter(() => {
    selectedLayerId.value = id
  })
  nextTick(() => attachTransformer())
}

function selectBackground() {
  preserveEditorScrollAfter(() => {
    selectedLayerId.value = null
    cropModeEnabled.value = false
  })
  nextTick(() => attachTransformer())
}

function closeFloatingLayerList() {
  floatingLayerListCollapsed.value = true
  if (typeof window !== 'undefined') {
    window.removeEventListener('click', onFloatingLayerListDocumentClick)
  }
}

function selectLayerFromLayerList(id: string) {
  selectLayer(id)
  closeFloatingLayerList()
}

function selectBackgroundFromLayerList() {
  selectBackground()
  closeFloatingLayerList()
}

function positionFloatingLayerListNearToolbar() {
  if (typeof window === 'undefined') return
  const anchor = layerListButtonWrapEl.value
  const rect = anchor?.getBoundingClientRect()
  const width = LAYER_POPOVER_WIDTH
  const popoverHeight = floatingLayerListEl.value?.offsetHeight ?? LAYER_POPOVER_FALLBACK_HEIGHT
  const fallbackX = window.innerWidth - width - FLOATING_LAYER_MARGIN
  const fallbackY = 96
  const targetX = rect ? rect.right - width : fallbackX
  const shouldOpenAbove = rect ? rect.bottom + 8 + popoverHeight > window.innerHeight - FLOATING_LAYER_MARGIN : false
  const targetY = rect ? (shouldOpenAbove ? rect.top - popoverHeight - 8 : rect.bottom + 8) : fallbackY
  floatingLayerListPosition.value = {
    x: Math.max(FLOATING_LAYER_MARGIN, Math.min(window.innerWidth - width - FLOATING_LAYER_MARGIN, targetX)),
    y: Math.max(FLOATING_LAYER_MARGIN, Math.min(window.innerHeight - popoverHeight - FLOATING_LAYER_MARGIN, targetY)),
  }
}

function onFloatingLayerListDocumentClick(event: MouseEvent) {
  const target = event.target
  if (!(target instanceof Node)) return
  if (floatingLayerListEl.value?.contains(target) || layerListButtonWrapEl.value?.contains(target)) return
  closeFloatingLayerList()
}

const layerColorVars = [
  '--mcr-editor-layer-image-1',
  '--mcr-editor-layer-image-2',
  '--mcr-editor-layer-image-3',
  '--mcr-editor-layer-image-4',
  '--mcr-editor-layer-image-5',
  '--mcr-editor-layer-image-6',
  '--mcr-editor-layer-image-7',
]

function layerColor(layer: AnyLayer): string {
  if (isImageLayer(layer)) {
    const idx = Math.max(0, layer.sourceIndex - 1)
    return getThemeColor(layerColorVars[idx % layerColorVars.length], '--mcr-color-primary-container')
  }
  if (isCustomTextLayer(layer)) {
    const fontFamily = getTextLayerFontFamily(layer)
    if (fontFamily === 'subtitle') {
      return getThemeRgba('--mcr-rgb-secondary', 0.85)
    }
    if (fontFamily === 'custom_text') {
      return getThemeRgba('--mcr-rgb-tertiary-container', 0.88)
    }
    return getThemeRgba('--mcr-rgb-primary-container', 0.85)
  }
  if (isMainTitleLayer(layer)) {
    return getThemeRgba('--mcr-rgb-primary-container', 0.85)
  }
  if (layer.type === 'subtitle' || layer.type === 'title_en') {
    return getThemeRgba('--mcr-rgb-secondary', 0.85)
  }
  return getThemeRgba('--mcr-rgb-on-surface-variant', 0.8)
}

function layerStyle(layer: AnyLayer) {
  const normalized = normalizeLayerEffects(layer)

  return {
    left: `${layer.x}px`,
    top: `${layer.y}px`,
    width: `${layer.width}px`,
    height: `${layer.height}px`,
    zIndex: layer.zIndex,
    borderRadius: `${layer.radius ?? 0}px`,
    transform: `rotate(${layer.rotation ?? 0}deg)`,
    transformOrigin: `${(layer.pivotX ?? 0.5) * 100}% ${(layer.pivotY ?? 0.5) * 100}%`,
    boxShadow: getLayerShadowStyle(normalized),
  }
}

function layerContentStyle(layer: AnyLayer) {
  const normalized = normalizeLayerEffects(layer)
  const common = {
    opacity: String(normalized.opacity ?? 1),
    filter: normalized.blur ? `blur(${Math.max(0, normalized.blur)}px)` : 'none',
    borderRadius: `${layer.radius ?? 0}px`,
  }
  if (isImageLayer(layer)) {
    return common
  }
  const shadowY = Math.round(normalized.shadowOffsetY ?? 0)
  const shadowBlur = Math.max(0, Math.round(normalized.shadowBlur ?? 0))
  const shadowOpacity = Math.max(0, Math.min(0.9, normalized.shadowOpacity ?? 0.28))
  return {
    ...common,
    textShadow: `${Math.round(normalized.shadowOffsetX ?? 0)}px ${shadowY}px ${shadowBlur}px ${getThemeRgba('--mcr-cover-shadow-rgb', shadowOpacity)}`,
    fontSize: `${Math.max(12, layer.fontSize || 60)}px`,
  }
}

function getLayerImage(sourceIndex: number) {
  return props.previewSource?.images?.find((image) => image.slot === sourceIndex)
}

function getKonvaImage(sourceIndex: number) {
  return imageRegistry.value[`slot:${sourceIndex}`]
}

function getStickerPathUrl(path: string | undefined) {
  const normalized = String(path || '').trim()
  return normalized
    ? `/api/v1/plugin/YahahaCoverStudio/saved_cover_image?file=${encodeURIComponent(normalized)}`
    : ''
}

function normalizePluginImageUrl(url: string | undefined) {
  const normalized = String(url || '').trim()
  if (!normalized) return ''
  if (normalized.startsWith('plugin/')) return `/api/v1/${normalized}`
  if (normalized.startsWith('/plugin/')) return `/api/v1${normalized}`
  return normalized
}

function getLayerStickerSrc(layer: CustomImageLayer) {
  return layer.stickerDataUrl || normalizePluginImageUrl(layer.stickerUrl) || getStickerPathUrl(layer.stickerPath)
}

function getKonvaImageForLayer(layer: CustomImageLayer) {
  const stickerSrc = getLayerStickerSrc(layer)
  if (layer.assetKind === 'sticker' || stickerSrc) {
    return imageRegistry.value[`layer:${layer.id}`]
  }
  return getKonvaImage(layer.sourceIndex)
}

function getLayerPreviewText(layer: AnyLayer) {
  if (isCustomTextLayer(layer)) {
    const fallback = layer.content || '未定义文本'
    if ((layer.contentSource || 'fixed') !== 'library') return fallback
    const customTexts = props.previewSource?.custom_texts || {}
    const key = String(layer.contentKey || '').trim()
    if (key && customTexts[key]) return customTexts[key]
    for (const defaultKey of ['default', 'text', 'custom_text', 'content']) {
      if (customTexts[defaultKey]) return customTexts[defaultKey]
    }
    return fallback
  }
  if (isMainTitleLayer(layer)) {
    return activeTitles.value.zh || '未定义主标题'
  }
  return activeTitles.value.en || '未定义副标题'
}

function layerLabel(layer: AnyLayer): string {
  if (layer.type === 'group') {
    return '图层组'
  }
  if (isImageLayer(layer)) {
    if (layer.assetKind === 'sticker') {
      const name = (layer.stickerName || '贴图').replace(/\.[a-z0-9]+$/i, '')
      return `贴图: ${name.slice(0, 10)}`
    }
    return `图片 ${layer.sourceIndex}`
  }
  if (isCustomTextLayer(layer)) {
    return `文本: ${getLayerPreviewText(layer).slice(0, 10)}`
  }
  return isMainTitleLayer(layer) ? '主标题' : '副标题'
}

function layerListIcon(layer: AnyLayer): string {
  if (layer.type === 'group') {
    return 'mdi-layers-triple-outline'
  }
  if (isImageLayer(layer)) {
    if (layer.assetKind === 'sticker') return 'mdi-sticker-outline'
    return 'mdi-image-outline'
  }
  if (isCustomTextLayer(layer)) {
    return 'mdi-text-box-outline'
  }
  return isMainTitleLayer(layer) ? 'mdi-format-title' : 'mdi-subtitles-outline'
}

function onLayerDoubleClick(layer: AnyLayer) {
  const wasSameLayer = selectedLayerId.value === layer.id
  selectedLayerId.value = layer.id
  if (isImageLayer(layer)) {
    cropModeEnabled.value = wasSameLayer ? !cropModeEnabled.value : true
    nextTick(() => attachTransformer())
    return
  }

  if (!isCustomTextLayer(layer)) {
    nextTick(() => attachTransformer())
    return
  }
  openInlineTextEditor(layer)
}

function openInlineTextEditor(layer: CustomTextLayer) {
  inlineTextEditor.value = {
    visible: true,
    layerId: layer.id,
    value: layer.content || '',
    x: Math.max(8, layer.x * canvasScale.value),
    y: Math.max(8, layer.y * canvasScale.value),
    width: Math.max(220, Math.min(520, layer.width * canvasScale.value)),
  }
}

function cancelInlineTextEdit() {
  inlineTextEditor.value.visible = false
}

function commitInlineTextEdit() {
  const { layerId, value } = inlineTextEditor.value
  if (!layerId) {
    inlineTextEditor.value.visible = false
    return
  }
  updateLayout((layout) => {
    const index = layout.layers.findIndex((item) => item.id === layerId)
    if (index === -1) return
    const layer = layout.layers[index]
    if (!isCustomTextLayer(layer)) return
    layout.layers[index] = {
      ...layer,
      content: value,
    }
  })
  inlineTextEditor.value.visible = false
  nextTick(() => attachTransformer())
}

function getGroupConfig(layer: AnyLayer) {
  const normalized = normalizeLayerEffects(layer)
  const cropDragging = cropModeEnabled.value && selectedLayerId.value === layer.id && isImageLayer(layer)
  return {
    x: layer.x,
    y: layer.y,
    rotation: 0,
    opacity: normalized.opacity ?? 1,
    draggable: !cropDragging,
    width: layer.width,
    height: layer.height,
  }
}

function getSelectionRectConfig(layer: AnyLayer) {
  const color = layerColor(layer)
  return {
    x: 0,
    y: 0,
    width: layer.width,
    height: layer.height,
    stroke: color,
    strokeWidth: 3,
    dash: [12, 8],
    listening: false,
  }
}

function getMeasuredTextLayout(layer: AnyLayer): CustomMeasuredTextLayout | null {
  if (isImageLayer(layer)) return null
  const textLayout = layout.value.computed?.textLayout
  return (layer.id && textLayout?.[layer.id]) || null
}

function getMeasuredTextLines(layer: AnyLayer) {
  return getMeasuredTextLayout(layer)?.lines || []
}

function showMeasuredTextOverlay(layer: AnyLayer) {
  return !isImageLayer(layer) && selectedLayerId.value === layer.id && !!getMeasuredTextLayout(layer)
}

function getMeasuredTextFrameConfig(layer: AnyLayer) {
  const measured = getMeasuredTextLayout(layer)
  if (!measured) {
    return { x: 0, y: 0, width: 0, height: 0, listening: false }
  }
  return {
    x: 0,
    y: 0,
    width: measured.frame.width,
    height: measured.frame.height,
    stroke: getThemeRgba('--mcr-editor-measure-frame-rgb', 0.95),
    strokeWidth: 2,
    dash: [8, 6],
    listening: false,
  }
}

function getMeasuredTextLineBoxConfig(layer: AnyLayer, index: number) {
  const measured = getMeasuredTextLayout(layer)
  const line = measured?.lines?.[index]
  if (!measured || !line) {
    return { x: 0, y: 0, width: 0, height: 0, listening: false }
  }
  return {
    x: line.x - measured.frame.x,
    y: line.y - measured.frame.y,
    width: line.width,
    height: line.height,
    stroke: getThemeRgba('--mcr-editor-measure-line-rgb', 0.9),
    strokeWidth: 1,
    dash: [4, 4],
    listening: false,
  }
}

function getMeasuredTextBaselineConfig(layer: AnyLayer, index: number) {
  const measured = getMeasuredTextLayout(layer)
  const line = measured?.lines?.[index]
  if (!measured || !line) {
    return { points: [], listening: false }
  }
  const y = line.y - measured.frame.y + line.height
  return {
    points: [line.x - measured.frame.x, y, line.x - measured.frame.x + line.width, y],
    stroke: getThemeRgba('--mcr-editor-measure-baseline-rgb', 0.95),
    strokeWidth: 1,
    dash: [6, 4],
    listening: false,
  }
}

function showCropOverlay(layer: AnyLayer) {
  return cropModeEnabled.value && selectedLayerId.value === layer.id && isImageLayer(layer)
}

function getCropOverlayConfig(layer: CustomImageLayer) {
  return {
    x: 0,
    y: 0,
    width: layer.width,
    height: layer.height,
    fill: getThemeRgba('--mcr-editor-crop-fill-rgb', 0.18),
    listening: false,
  }
}

function getCropHintTextConfig(layer: CustomImageLayer) {
  return {
    x: 16,
    y: Math.max(12, layer.height - 42),
    width: Math.max(80, layer.width - 32),
    text: '拖动图片内容调整取景',
    fontSize: 20,
    fontStyle: 'bold',
    fill: getThemeRgba('--mcr-editor-crop-text-rgb', 0.95),
    stroke: getThemeRgba('--mcr-editor-crop-text-stroke-rgb', 0.35),
    strokeWidth: 1,
    listening: false,
    align: 'center',
  }
}

function getKonvaImageConfig(layer: CustomImageLayer) {
  const normalized = normalizeLayerEffects(layer)
  const image = getKonvaImageForLayer(layer)
  const crop = getKonvaImageCrop(layer)
  const cropDragging = cropModeEnabled.value && selectedLayerId.value === layer.id
  const placement = cropDragging ? getKonvaImagePlacement(layer) : null
  const pivotX = Math.max(0, Math.min(1, layer.pivotX ?? 0.5))
  const pivotY = Math.max(0, Math.min(1, layer.pivotY ?? 0.5))
  return {
    x: placement ? placement.x : layer.width * pivotX,
    y: placement ? placement.y : layer.height * pivotY,
    image,
    width: placement ? placement.width : layer.width,
    height: placement ? placement.height : layer.height,
    offsetX: placement ? 0 : layer.width * pivotX,
    offsetY: placement ? 0 : layer.height * pivotY,
    crop: placement ? undefined : crop,
    rotation: placement ? 0 : layer.rotation ?? 0,
    cornerRadius: Math.max(0, layer.radius || 0),
    opacity: normalized.opacity ?? 1,
    draggable: cropDragging,
  }
}

function getKonvaImageClipGroupConfig(layer: CustomImageLayer) {
  return {
    x: 0,
    y: 0,
    clipX: 0,
    clipY: 0,
    clipWidth: layer.width,
    clipHeight: layer.height,
  }
}

function getKonvaImageCrop(layer: CustomImageLayer) {
  const image = getKonvaImageForLayer(layer)
  if (!image) return undefined

  const sourceWidth = Number(image.width || 0)
  const sourceHeight = Number(image.height || 0)
  const targetWidth = Math.max(1, Number(layer.width || 1))
  const targetHeight = Math.max(1, Number(layer.height || 1))
  if (!sourceWidth || !sourceHeight || !targetWidth || !targetHeight) {
    return undefined
  }

  const sourceRatio = sourceWidth / sourceHeight
  const targetRatio = targetWidth / targetHeight
  const cropFocusX = Math.max(0, Math.min(1, Number(layer.cropFocusX ?? 0.5)))
  const cropFocusY = Math.max(0, Math.min(1, Number(layer.cropFocusY ?? 0.5)))

  if (sourceRatio > targetRatio) {
    const cropWidth = sourceHeight * targetRatio
    const cropX = (sourceWidth - cropWidth) * cropFocusX
    return {
      x: Math.max(0, cropX),
      y: 0,
      width: Math.max(1, cropWidth),
      height: sourceHeight,
    }
  }

  const cropHeight = sourceWidth / targetRatio
  const cropY = (sourceHeight - cropHeight) * cropFocusY
  return {
    x: 0,
    y: Math.max(0, cropY),
    width: sourceWidth,
    height: Math.max(1, cropHeight),
  }
}

function getKonvaImagePlacement(layer: CustomImageLayer) {
  const image = getKonvaImageForLayer(layer)
  if (!image) {
    return {
      x: 0,
      y: 0,
      width: layer.width,
      height: layer.height,
    }
  }

  const sourceWidth = Number(image.width || 0)
  const sourceHeight = Number(image.height || 0)
  const targetWidth = Math.max(1, Number(layer.width || 1))
  const targetHeight = Math.max(1, Number(layer.height || 1))
  if (!sourceWidth || !sourceHeight) {
    return {
      x: 0,
      y: 0,
      width: targetWidth,
      height: targetHeight,
    }
  }

  const scale = Math.max(targetWidth / sourceWidth, targetHeight / sourceHeight)
  const drawWidth = sourceWidth * scale
  const drawHeight = sourceHeight * scale
  const cropFocusX = Math.max(0, Math.min(1, Number(layer.cropFocusX ?? 0.5)))
  const cropFocusY = Math.max(0, Math.min(1, Number(layer.cropFocusY ?? 0.5)))
  return {
    x: -(drawWidth - targetWidth) * cropFocusX,
    y: -(drawHeight - targetHeight) * cropFocusY,
    width: drawWidth,
    height: drawHeight,
  }
}

function getKonvaImageFallbackConfig(layer: CustomImageLayer) {
  return {
    x: 0,
    y: 0,
    width: layer.width,
    height: layer.height,
    fill: getThemeRgba('--mcr-editor-crop-fill-rgb', 0.45),
    cornerRadius: Math.max(0, layer.radius || 0),
    stroke: getThemeColor('--mcr-editor-layer-image-3'),
    strokeWidth: 2,
  }
}

function getKonvaTextConfig(layer: CustomTitleLayer | CustomTextLayer) {
  fontRevision.value
  const normalized = normalizeLayerEffects(layer)
  const fontFamily = getTextLayerFontFamily(layer)
  const isSubtitle = !isMainTitleLayer(layer)
  const pivotX = Math.max(0, Math.min(1, layer.pivotX ?? 0.5))
  const pivotY = Math.max(0, Math.min(1, layer.pivotY ?? 0.5))
  return {
    x: layer.width * pivotX,
    y: layer.height * pivotY,
    offsetX: layer.width * pivotX,
    offsetY: layer.height * pivotY,
    width: layer.width,
    height: layer.height,
    rotation: layer.rotation ?? 0,
    text: getLayerPreviewText(layer),
    fill: getThemeColor('--mcr-cover-text'),
    align: layer.textAlign || 'center',
    verticalAlign: 'middle',
    fontSize: Math.max(12, layer.fontSize || 60),
    fontStyle: 'bold',
    fontFamily: getKonvaFontFamily(fontFamily, getLayerPreviewText(layer)),
    lineHeight: 1.1,
    letterSpacing: isSubtitle ? 3 : 0,
    wrap: 'char',
    textTransform: isSubtitle ? 'uppercase' : 'none',
    shadowColor: getThemeRgba('--mcr-cover-shadow-rgb', Math.max(0, Math.min(0.9, normalized.shadowOpacity ?? 0.28))),
    shadowBlur: Math.max(0, normalized.shadowBlur ?? 0),
    shadowOffsetX: Math.round(normalized.shadowOffsetX ?? 0),
    shadowOffsetY: Math.round(normalized.shadowOffsetY ?? 0),
    opacity: normalized.opacity ?? 1,
  }
}

function onKonvaDragEnd(id: string, event: any) {
  const target = event?.target
  if (!target) return
  updateLayout((layout) => {
    const index = layout.layers.findIndex((layer) => layer.id === id)
    if (index === -1) return
    const layer = layout.layers[index]
    let x = Number(target.x?.() ?? 0)
    let y = Number(target.y?.() ?? 0)
    if (!isImageLayer(layer)) {
      const centerX = x + layer.width / 2
      const centerY = y + layer.height / 2
      const stageCenterX = CANVAS_WIDTH / 2
      const stageCenterY = CANVAS_HEIGHT / 2
      if (Math.abs(centerX - stageCenterX) <= SNAP_THRESHOLD) {
        x = stageCenterX - layer.width / 2
      }
      if (Math.abs(centerY - stageCenterY) <= SNAP_THRESHOLD) {
        y = stageCenterY - layer.height / 2
      }
      for (const item of layout.layers) {
        if (item.id === layer.id || isImageLayer(item)) continue
        const left = item.x
        const right = item.x + item.width
        const midX = item.x + item.width / 2
        const top = item.y
        const bottom = item.y + item.height
        const midY = item.y + item.height / 2
        const currentLeft = x
        const currentRight = x + layer.width
        const currentMidX = x + layer.width / 2
        const currentTop = y
        const currentBottom = y + layer.height
        const currentMidY = y + layer.height / 2
        if (Math.abs(currentMidX - midX) <= SNAP_THRESHOLD) x = midX - layer.width / 2
        else if (Math.abs(currentLeft - left) <= SNAP_THRESHOLD) x = left
        else if (Math.abs(currentRight - right) <= SNAP_THRESHOLD) x = right - layer.width
        if (Math.abs(currentMidY - midY) <= SNAP_THRESHOLD) y = midY - layer.height / 2
        else if (Math.abs(currentTop - top) <= SNAP_THRESHOLD) y = top
        else if (Math.abs(currentBottom - bottom) <= SNAP_THRESHOLD) y = bottom - layer.height
      }
      target.x(x)
      target.y(y)
    }
    const nextLayer = layer as any
    nextLayer.x = Math.round(x)
    nextLayer.y = Math.round(y)
    layout.layers[index] = { ...nextLayer }
  })
}

function setLayerNodeRef(id: string, node: any) {
  const instance = node?.getNode ? node.getNode() : node
  if (instance) {
    layerNodeRegistry.set(id, instance)
  } else {
    layerNodeRegistry.delete(id)
  }
}

function attachTransformer() {
  const raw = transformerRef.value
  const transformer =
    raw?.getNode?.()
    || raw?.node?.getNode?.()
    || raw?.node
    || raw
  if (!transformer || typeof transformer.nodes !== 'function') return
  const selectedId = selectedLayerId.value
  const node = selectedId ? layerNodeRegistry.get(selectedId) : null
  transformer.nodes(node ? [node] : [])
  if (typeof transformer.getLayer === 'function') {
    transformer.getLayer()?.batchDraw?.()
  }
}

function onKonvaTransformEnd(id: string, event: any) {
  const target = event?.target
  if (!target) return
  const scaleX = Number(target.scaleX?.() ?? 1)
  const scaleY = Number(target.scaleY?.() ?? 1)
  const rotation = Number(target.rotation?.() ?? 0)
  const x = Number(target.x?.() ?? 0)
  const y = Number(target.y?.() ?? 0)
  const width = Math.max(10, Math.round((Number(target.width?.() ?? 0) || 0) * scaleX))
  const height = Math.max(10, Math.round((Number(target.height?.() ?? 0) || 0) * scaleY))

  updateLayout((layout) => {
    const index = layout.layers.findIndex((layer) => layer.id === id)
    if (index === -1) return
    const layer = layout.layers[index] as any
    layer.x = Math.round(x)
    layer.y = Math.round(y)
    layer.width = width
    layer.height = height
    layer.rotation = Math.round(rotation)
    layout.layers[index] = { ...layer }
  })

  target.scaleX(1)
  target.scaleY(1)
  target.width(width)
  target.height(height)
  nextTick(() => attachTransformer())
}

function onKonvaImageCropDrag(id: string, event: any) {
  if (!cropModeEnabled.value) return
  const target = event?.target
  if (!target) return
  updateLayout((layout) => {
    const index = layout.layers.findIndex((layer) => layer.id === id)
    if (index === -1) return
    const layer = layout.layers[index]
    if (!isImageLayer(layer)) return
    const image = getKonvaImageForLayer(layer)
    if (!image) return
    const sourceWidth = Number(image.width || 0)
    const sourceHeight = Number(image.height || 0)
    const targetWidth = Math.max(1, Number(layer.width || 1))
    const targetHeight = Math.max(1, Number(layer.height || 1))
    if (!sourceWidth || !sourceHeight) return
    const scale = Math.max(targetWidth / sourceWidth, targetHeight / sourceHeight)
    const drawWidth = sourceWidth * scale
    const drawHeight = sourceHeight * scale
    const overflowX = Math.max(0, drawWidth - targetWidth)
    const overflowY = Math.max(0, drawHeight - targetHeight)
    const x = Math.min(0, Math.max(-overflowX, Number(target.x?.() ?? 0)))
    const y = Math.min(0, Math.max(-overflowY, Number(target.y?.() ?? 0)))
    target.x(x)
    target.y(y)
    const nextLayer = { ...layer } as CustomImageLayer
    nextLayer.cropFocusX = overflowX > 0 ? Math.max(0, Math.min(1, -x / overflowX)) : 0.5
    nextLayer.cropFocusY = overflowY > 0 ? Math.max(0, Math.min(1, -y / overflowY)) : 0.5
    layout.layers[index] = nextLayer
  })
}

function refreshImageRegistry() {
  const next: Record<string, HTMLImageElement> = {}
  for (const image of props.previewSource?.images || []) {
    if (!image?.src) continue
    const instance = new window.Image()
    instance.src = image.src
    next[`slot:${image.slot}`] = instance
  }
  for (const layer of getEditableLayers(layout.value.layers)) {
    if (!isImageLayer(layer)) continue
    const stickerSrc = getLayerStickerSrc(layer)
    if (!stickerSrc) continue
    const instance = new window.Image()
    instance.src = stickerSrc
    next[`layer:${layer.id}`] = instance
  }
  imageRegistry.value = next
}

function createLayerId() {
  return `layer_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`
}

function addImageLayer() {
  updateLayout((layout) => {
    const existingImages = layout.layers.filter((l) => l.type === 'image') as CustomImageLayer[]
    const nextIndex = (existingImages[existingImages.length - 1]?.sourceIndex ?? 0) + 1
    const layer = normalizeLayerEffects({
      id: createLayerId(),
      type: 'image',
      sourceIndex: nextIndex,
      x: CANVAS_WIDTH * 0.55,
      y: CANVAS_HEIGHT * 0.15,
      width: CANVAS_WIDTH * 0.35,
      height: CANVAS_HEIGHT * 0.7,
      rotation: 0,
      radius: 32,
      zIndex: layout.layers.length + 1,
      fit: 'cover',
      shadowBlur: 24,
      shadowOffsetX: 0,
      shadowOffsetY: 16,
      shadowOpacity: 0.22,
    } as CustomImageLayer)
    layout.layers.push(layer)
    selectedLayerId.value = layer.id
  })
}

const stickerPathsInUse = computed(() => new Set(
  getEditableLayers(layout.value.layers)
    .filter((layer): layer is CustomImageLayer => isImageLayer(layer) && (layer.assetKind === 'sticker' || Boolean(layer.stickerPath || layer.stickerUrl || layer.stickerDataUrl)))
    .map((layer) => String(layer.stickerPath || '').trim())
    .filter(Boolean),
))

async function loadStickerLibrary() {
  if (!props.api?.get) return
  stickerLibraryLoading.value = true
  try {
    const resp = await props.api.get<{ code: number; data?: StickerLibraryItem[]; msg?: string }>('plugin/YahahaCoverStudio/stickers')
    if (!resp || resp.code !== 0) {
      throw new Error(resp?.msg || 'load stickers failed')
    }
    const remoteItems = Array.isArray(resp.data) ? resp.data : []
    const remotePaths = new Set(remoteItems.map((item) => item.path))
    const localOnlyItems = stickerLibraryItems.value.filter((item) => item.path.startsWith('memory:') && !remotePaths.has(item.path))
    stickerLibraryItems.value = [...localOnlyItems, ...remoteItems]
  } catch (error) {
    console.warn('load sticker library failed', error)
  } finally {
    stickerLibraryLoading.value = false
  }
}

function toggleStickerLibrary() {
  stickerLibraryOpen.value = !stickerLibraryOpen.value
  if (stickerLibraryOpen.value) {
    void loadStickerLibrary()
  }
}

function openStickerFilePicker() {
  stickerFileInputEl.value?.click()
}

function isStickerInUse(item: StickerLibraryItem) {
  return stickerPathsInUse.value.has(String(item.path || '').trim())
}

function removeStickerReferences(path: string) {
  const normalizedPath = String(path || '').trim()
  if (!normalizedPath) return
  const filterLayers = (layers: TemplateLayer[]): TemplateLayer[] => layers
    .map((layer) => {
      if (layer.type !== 'group') return layer
      return normalizeLayerEffects({
        ...layer,
        children: filterLayers((layer as CustomGroupLayer).children || []),
      } as CustomGroupLayer)
    })
    .filter((layer) => {
      if (!isImageLayer(layer)) return true
      return String(layer.stickerPath || '').trim() !== normalizedPath
    })
  updateLayout((layout) => {
    layout.layers = filterLayers(layout.layers)
    if (selectedLayer.value && isImageLayer(selectedLayer.value) && String(selectedLayer.value.stickerPath || '').trim() === normalizedPath) {
      selectedLayerId.value = null
    }
  })
}

function upsertStickerLibraryItem(item: StickerLibraryItem) {
  const key = item.path || `memory:${item.name}:${Date.now()}`
  const normalized = { ...item, path: key }
  stickerLibraryItems.value = [
    normalized,
    ...stickerLibraryItems.value.filter((candidate) => candidate.path !== key),
  ]
  return normalized
}

function readStickerFile(file: File): Promise<{
  dataUrl: string
  name: string
  width: number
  height: number
}> {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith('image/')) {
      reject(new Error('not image'))
      return
    }
    const reader = new FileReader()
    reader.onerror = () => reject(reader.error || new Error('read failed'))
    reader.onload = () => {
      const dataUrl = String(reader.result || '')
      if (!dataUrl) {
        reject(new Error('empty image'))
        return
      }
      const image = new window.Image()
      image.onload = () => resolve({
        dataUrl,
        name: file.name || '贴图',
        width: Number(image.naturalWidth || image.width || 1),
        height: Number(image.naturalHeight || image.height || 1),
      })
      image.onerror = () => resolve({
        dataUrl,
        name: file.name || '贴图',
        width: 1,
        height: 1,
      })
      image.src = dataUrl
    }
    reader.readAsDataURL(file)
  })
}

function addStickerLayer(payload: {
  dataUrl: string
  name: string
  width: number
  height: number
  path?: string
  url?: string
}) {
  const sourceWidth = Math.max(1, payload.width || 1)
  const sourceHeight = Math.max(1, payload.height || 1)
  const sourceRatio = sourceWidth / sourceHeight
  const targetMaxWidth = 360
  const targetMaxHeight = 220
  const targetRatio = targetMaxWidth / targetMaxHeight
  const width = sourceRatio >= targetRatio ? targetMaxWidth : Math.max(96, targetMaxHeight * sourceRatio)
  const height = sourceRatio >= targetRatio ? Math.max(72, targetMaxWidth / sourceRatio) : targetMaxHeight
  updateLayout((layout) => {
    const maxZIndex = Math.max(0, ...getEditableLayers(layout.layers).map((layer) => Number(layer.zIndex || 0)))
    const layer = normalizeLayerEffects({
      id: createLayerId(),
      type: 'image',
      assetKind: 'sticker',
      stickerDataUrl: payload.dataUrl,
      stickerPath: payload.path,
      stickerUrl: payload.url,
      stickerName: payload.name,
      stickerWidth: sourceWidth,
      stickerHeight: sourceHeight,
      sourceIndex: 1,
      source: { kind: 'slot', slot: 1 },
      x: Math.round(CANVAS_WIDTH - width - 96),
      y: Math.round(CANVAS_HEIGHT - height - 88),
      width: Math.round(width),
      height: Math.round(height),
      rotation: 0,
      radius: 0,
      zIndex: maxZIndex + 1,
      fit: 'contain',
      opacity: 0.92,
      shadowBlur: 14,
      shadowOffsetX: 0,
      shadowOffsetY: 8,
      shadowOpacity: 0.18,
    } as CustomImageLayer)
    layout.layers.push(layer)
    selectedLayerId.value = layer.id
    cropModeEnabled.value = false
  })
}

function addStickerFromLibrary(item: StickerLibraryItem) {
  addStickerLayer({
    dataUrl: item.dataUrl || '',
    name: item.name || '贴图',
    width: Number(item.width || 1),
    height: Number(item.height || 1),
    path: item.path,
    url: item.url || getStickerPathUrl(item.path),
  })
}

async function deleteStickerItem(item: StickerLibraryItem) {
  if (item.path.startsWith('memory:')) {
    stickerLibraryItems.value = stickerLibraryItems.value.filter((candidate) => candidate.path !== item.path)
    return
  }
  if (!props.api?.post) return
  try {
    const endpoint = `plugin/YahahaCoverStudio/delete_sticker?file=${encodeURIComponent(item.path)}`
    const resp = await props.api.post<{ code: number; msg?: string }>(endpoint)
    if (!resp || resp.code !== 0) {
      throw new Error(resp?.msg || 'delete sticker failed')
    }
    stickerLibraryItems.value = stickerLibraryItems.value.filter((candidate) => candidate.path !== item.path)
    removeStickerReferences(item.path)
  } catch (error) {
    console.warn('delete sticker failed', error)
  }
}

async function uploadStickerPayload(payload: {
  dataUrl: string
  name: string
  width: number
  height: number
}) {
  if (!props.api?.post) return payload
  try {
    const resp = await props.api.post<{
      code: number
      msg?: string
      data?: {
        stickerDataUrl?: string
        stickerPath?: string
        stickerUrl?: string
        stickerName?: string
        stickerWidth?: number
        stickerHeight?: number
      }
    }>('plugin/YahahaCoverStudio/upload_sticker', {
      data_url: payload.dataUrl,
      name: payload.name,
      width: payload.width,
      height: payload.height,
    })
    if (!resp || resp.code !== 0 || !resp.data?.stickerPath) {
      throw new Error(resp?.msg || 'upload sticker failed')
    }
    return {
      dataUrl: resp.data.stickerDataUrl || payload.dataUrl,
      name: resp.data.stickerName || payload.name,
      width: Number(resp.data.stickerWidth || payload.width || 1),
      height: Number(resp.data.stickerHeight || payload.height || 1),
      path: resp.data.stickerPath,
      url: resp.data.stickerUrl || '',
    }
  } catch (error) {
    console.warn('upload sticker failed, fallback to local data url', error)
    return payload
  }
}

async function addStickerFromFile(file: File) {
  try {
    const payload = await readStickerFile(file)
    const localItem = upsertStickerLibraryItem({
      name: payload.name,
      path: `memory:${Date.now()}:${payload.name}`,
      dataUrl: payload.dataUrl,
      width: payload.width,
      height: payload.height,
    })
    const uploaded = await uploadStickerPayload(payload)
    if (uploaded.path) {
      stickerLibraryItems.value = stickerLibraryItems.value.filter((candidate) => candidate.path !== localItem.path)
      upsertStickerLibraryItem({
        name: uploaded.name,
        path: uploaded.path,
        url: uploaded.url,
        dataUrl: uploaded.dataUrl,
        width: uploaded.width,
        height: uploaded.height,
      })
    }
    addStickerLayer(uploaded)
    if (stickerLibraryOpen.value) {
      void loadStickerLibrary()
    }
  } catch (error) {
    console.warn('add sticker failed', error)
  }
}

function onStickerFileInputChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (file) {
    void addStickerFromFile(file)
  }
}

function isEditableTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) return false
  const tagName = target.tagName.toLowerCase()
  return tagName === 'input' || tagName === 'textarea' || target.isContentEditable
}

function onEditorPaste(event: ClipboardEvent) {
  if (typeof window === 'undefined') return
  const root = editorRootEl.value
  if (!root) return
  const active = document.activeElement
  if (active instanceof HTMLElement && active !== document.body && !root.contains(active)) return
  const file = Array.from(event.clipboardData?.items || [])
    .find((item) => item.kind === 'file' && item.type.startsWith('image/'))
    ?.getAsFile()
  if (!file) return
  if (isEditableTarget(event.target)) {
    event.preventDefault()
  }
  void addStickerFromFile(file)
}

function addZhTitleLayer() {
  updateLayout((layout) => {
    const layer = normalizeLayerEffects({
      id: createLayerId(),
      type: 'main_title',
      x: CANVAS_WIDTH * 0.05,
      y: CANVAS_HEIGHT * 0.2,
      width: CANVAS_WIDTH * 0.35,
      height: CANVAS_HEIGHT * 0.18,
      rotation: 0,
      radius: 0,
      zIndex: layout.layers.length + 1,
      fontSize: 180,
      textAlign: 'center',
      shadowBlur: 18,
      shadowOffsetX: 0,
      shadowOffsetY: 10,
      shadowOpacity: 0.24,
    } as CustomTitleLayer)
    layout.layers.push(layer)
    selectedLayerId.value = layer.id
  })
}

function addEnTitleLayer() {
  updateLayout((layout) => {
    const layer = normalizeLayerEffects({
      id: createLayerId(),
      type: 'subtitle',
      x: CANVAS_WIDTH * 0.05,
      y: CANVAS_HEIGHT * 0.45,
      width: CANVAS_WIDTH * 0.35,
      height: CANVAS_HEIGHT * 0.14,
      rotation: 0,
      radius: 0,
      zIndex: layout.layers.length + 1,
      fontSize: 75,
      textAlign: 'center',
      shadowBlur: 14,
      shadowOffsetX: 0,
      shadowOffsetY: 8,
      shadowOpacity: 0.2,
    } as CustomTitleLayer)
    layout.layers.push(layer)
    selectedLayerId.value = layer.id
  })
}

function addTextLayer() {
  updateLayout((layout) => {
    const layer = createTextLayer({
      zIndex: layout.layers.length + 1,
    })
    layout.layers.push(layer)
    selectedLayerId.value = layer.id
  })
}

function removeSelectedLayer() {
  const id = selectedLayerId.value
  if (!id) return
  removeLayer(id)
}

function removeLayer(id: string) {
  preserveEditorScrollAfter(() => {
    updateLayout((layout) => {
      const before = getEditableLayers(layout.layers)
      const index = before.findIndex((layer) => layer.id === id)
      if (!removeLayerById(layout.layers, id)) return
      const after = getEditableLayers(layout.layers)
      if (!after.length) {
        selectedLayerId.value = null
        return
      }

      const nextIndex = Math.max(0, Math.min(index, after.length - 1))
      selectedLayerId.value = selectedLayerId.value === id ? after[nextIndex].id : selectedLayerId.value
    })
  })
}

function removeLayerFromLayerList(id: string) {
  removeLayer(id)
}

type NumericKey =
  | 'x'
  | 'y'
  | 'width'
  | 'height'
  | 'radius'
  | 'zIndex'
  | 'rotation'
  | 'fontSize'
  | 'pivotX'
  | 'pivotY'
  | 'sourceIndex'
  | 'cropFocusX'
  | 'cropFocusY'
  | 'opacity'
  | 'blur'
  | 'shadowBlur'
  | 'shadowOffsetX'
  | 'shadowOffsetY'
  | 'shadowOpacity'
  | 'colorRatio'

type StringKey = 'content' | 'contentSource' | 'contentKey' | 'fontFamily' | 'fit' | 'colorSource' | 'color' | 'textAlign' | 'maskMode'

function updateSelectedNumeric(key: NumericKey, raw: string | number) {
  const id = selectedLayerId.value
  if (!id) return
  const num = typeof raw === 'number' ? raw : Number(raw)
  if (Number.isNaN(num)) return
  updateLayout((layout) => {
    updateLayerById(layout.layers, id, (layer) => ({
      ...(layer as any),
      [key]: num,
    }))
  })
}

function updateSelectedString(key: StringKey, value: string) {
  const id = selectedLayerId.value
  if (!id) return
  updateLayout((layout) => {
    updateLayerById(layout.layers, id, (layer) => ({
      ...(layer as any),
      [key]: value,
    }))
  })
}

function buildTrapezoidMask(bottomRatio: number) {
  const ratio = Math.max(0.2, Math.min(1, Number(bottomRatio) || 1))
  const inset = (1 - ratio) / 2
  return {
    units: 'relative' as const,
    points: [
      [0, 0],
      [1, 0],
      [1 - inset, 1],
      [inset, 1],
    ] as Array<[number, number]>,
  }
}

function buildRectangleMask() {
  return {
    units: 'relative' as const,
    points: [
      [0, 0],
      [1, 0],
      [1, 1],
      [0, 1],
    ] as Array<[number, number]>,
  }
}

function setActivePolygonPoints(points: Array<[number, number]>) {
  const context = activePolygonContext.value
  if (!context) return
  const mask = {
    units: 'relative' as const,
    points: points.map((point) => [
      Math.max(0, Math.min(1, point[0])),
      Math.max(0, Math.min(1, point[1])),
    ] as [number, number]),
  }
  if (context.target === 'background') {
    updateLayout((layout) => {
      layout.background = {
        type: 'blurred-image-color',
        imageSource: { kind: 'slot', slot: 1 },
        colorSource: 'auto',
        color: editorBlendColor.value,
        color2: defaultDeepGradientColor.value,
        colorRatio: effectiveParams.value.colorRatio,
        blur: effectiveParams.value.blur,
        grain: 0.18,
        zIndex: 0,
        ...(layout.background || {}),
        maskPolygon: mask,
      }
    })
    return
  }
  if (!context.layerId) return
  updateLayout((layout) => {
    updateLayerById(layout.layers, context.layerId as string, (layer) => {
      if (!isImageLayer(layer)) return layer
      return { ...layer, maskPolygon: mask }
    })
  })
}

function snapPolygonPoint(rawX: number, rawY: number, movingIndex: number) {
  const snapTargetsX = [0, 0.5, 1]
  const snapTargetsY = [0, 0.5, 1]
  activePolygonRelativePoints.value.forEach((point, index) => {
    if (index === movingIndex) return
    snapTargetsX.push(point[0])
    snapTargetsY.push(point[1])
  })
  const threshold = 0.018
  let x = Math.max(0, Math.min(1, rawX))
  let y = Math.max(0, Math.min(1, rawY))
  let guideX: number | null = null
  let guideY: number | null = null
  for (const target of snapTargetsX) {
    if (Math.abs(x - target) <= threshold) {
      x = target
      guideX = target
      break
    }
  }
  for (const target of snapTargetsY) {
    if (Math.abs(y - target) <= threshold) {
      y = target
      guideY = target
      break
    }
  }
  const context = activePolygonContext.value
  polygonSnapGuide.value = context
    ? {
        x: guideX === null ? null : (context.x + guideX * context.width) * canvasScale.value,
        y: guideY === null ? null : (context.y + guideY * context.height) * canvasScale.value,
      }
    : { x: null, y: null }
  return [x, y] as [number, number]
}

function addPolygonPoint() {
  const points = activePolygonRelativePoints.value
  if (points.length < 2) return
  let insertAt = 1
  let longest = -1
  for (let index = 0; index < points.length; index += 1) {
    const current = points[index]
    const next = points[(index + 1) % points.length]
    const distance = ((next[0] - current[0]) ** 2) + ((next[1] - current[1]) ** 2)
    if (distance > longest) {
      longest = distance
      insertAt = index + 1
    }
  }
  const prev = points[(insertAt - 1 + points.length) % points.length]
  const next = points[insertAt % points.length]
  const point: [number, number] = [
    (prev[0] + next[0]) / 2,
    (prev[1] + next[1]) / 2,
  ]
  const updated = [...points]
  updated.splice(insertAt, 0, point)
  setActivePolygonPoints(updated)
}

function removePolygonPoint(index: number) {
  const points = [...activePolygonRelativePoints.value]
  if (points.length <= 3) return
  points.splice(index, 1)
  setActivePolygonPoints(points)
}

function resetActivePolygon() {
  setActivePolygonPoints(buildRectangleMask().points)
}

function getBackgroundTrapezoidBottomRatio() {
  const points = layout.value.background?.maskPolygon?.points
  if (!points || points.length < 4) return 1
  const bottomLeft = Number(points[3]?.[0] ?? 0)
  const bottomRight = Number(points[2]?.[0] ?? 1)
  return Math.max(0.2, Math.min(1, bottomRight - bottomLeft))
}

function toggleBackgroundPolygon(enabled: boolean) {
  updateLayout((layout) => {
    layout.background = {
      type: 'blurred-image-color',
      imageSource: { kind: 'slot', slot: 1 },
      colorSource: 'auto',
      color: editorBlendColor.value,
      color2: defaultDeepGradientColor.value,
      colorRatio: effectiveParams.value.colorRatio,
      blur: effectiveParams.value.blur,
      grain: 0.18,
      zIndex: 0,
      ...(layout.background || {}),
      maskPolygon: enabled ? buildRectangleMask() : undefined,
    }
  })
}

function updateBackgroundTrapezoidBottom(ratio: number) {
  updateLayout((layout) => {
    layout.background = {
      type: 'blurred-image-color',
      imageSource: { kind: 'slot', slot: 1 },
      colorSource: 'auto',
      color: editorBlendColor.value,
      color2: defaultDeepGradientColor.value,
      colorRatio: effectiveParams.value.colorRatio,
      blur: effectiveParams.value.blur,
      grain: 0.18,
      zIndex: 0,
      ...(layout.background || {}),
      maskPolygon: buildTrapezoidMask(ratio),
    }
  })
}

function getSelectedTrapezoidBottomRatio(layer: CustomImageLayer) {
  const points = layer.maskPolygon?.points
  if (!points || points.length < 4) return 1
  const bottomLeft = Number(points[3]?.[0] ?? 0)
  const bottomRight = Number(points[2]?.[0] ?? 1)
  return Math.max(0.2, Math.min(1, bottomRight - bottomLeft))
}

function toggleSelectedPolygon(enabled: boolean) {
  const id = selectedLayerId.value
  if (!id) return
  updateLayout((layout) => {
    updateLayerById(layout.layers, id, (layer) => {
      if (!isImageLayer(layer)) return layer
      return {
        ...layer,
        maskPolygon: enabled ? buildRectangleMask() : undefined,
      }
    })
  })
}

function updateSelectedTrapezoidBottom(ratio: number) {
  const id = selectedLayerId.value
  if (!id) return
  updateLayout((layout) => {
    updateLayerById(layout.layers, id, (layer) => {
      if (!isImageLayer(layer)) return layer
      return {
        ...layer,
        maskPolygon: buildTrapezoidMask(ratio),
      }
    })
  })
}

function onSizeSliderChange(key: 'width' | 'height', raw: number) {
  const layer = selectedLayer.value
  if (!layer) return
  const value = Number(raw)
  if (Number.isNaN(value)) return

  if (!lockAspectRatio.value || layer.width <= 0 || layer.height <= 0) {
    updateSelectedNumeric(key, value)
    return
  }

  const aspect = layer.width / layer.height || 1

  if (key === 'width') {
    const nextWidth = Math.max(10, Math.min(value, CANVAS_WIDTH * 10))
    const nextHeight = nextWidth / aspect
    updateLayout((layout) => {
      updateLayerById(layout.layers, layer.id, (current) => ({
        ...(current as any),
        width: Math.round(nextWidth),
        height: Math.round(Math.min(nextHeight, CANVAS_HEIGHT * 10)),
      }))
    })
  } else {
    const nextHeight = Math.max(10, Math.min(value, CANVAS_HEIGHT * 10))
    const nextWidth = nextHeight * aspect
    updateLayout((layout) => {
      updateLayerById(layout.layers, layer.id, (current) => ({
        ...(current as any),
        height: Math.round(nextHeight),
        width: Math.round(Math.min(nextWidth, CANVAS_WIDTH * 10)),
      }))
    })
  }
}

function applySelectedAspectRatio(ratio: number) {
  const layer = selectedLayer.value
  if (!layer) return
  const safeRatio = Math.max(0.1, Number(ratio) || 1)
  const centerX = layer.x + layer.width / 2
  const centerY = layer.y + layer.height / 2
  let nextWidth = Math.max(10, Math.min(layer.width, CANVAS_WIDTH))
  let nextHeight = nextWidth / safeRatio
  if (nextHeight > CANVAS_HEIGHT) {
    nextHeight = CANVAS_HEIGHT
    nextWidth = nextHeight * safeRatio
  }
  updateLayout((layout) => {
    updateLayerById(layout.layers, layer.id, (current) => ({
      ...(current as any),
      x: Math.round(centerX - nextWidth / 2),
      y: Math.round(centerY - nextHeight / 2),
      width: Math.round(Math.min(nextWidth, CANVAS_WIDTH)),
      height: Math.round(Math.min(nextHeight, CANVAS_HEIGHT)),
    }))
  })
}

function onSliderStart() {
  sliderActive = true
}

function onSliderEnd() {
  sliderActive = false
}

interface DragState {
  layerId: string
  startX: number
  startY: number
  originX: number
  originY: number
  mode: DragMode
  originWidth?: number
  originHeight?: number
  originRotation?: number
}

const dragState = ref<DragState | null>(null)
const polygonPointDrag = ref<{ index: number } | null>(null)

function getPointerPosition(event: MouseEvent | TouchEvent): { clientX: number; clientY: number } | null {
  if ('touches' in event) {
    const touch = event.touches[0]
    if (!touch) return null
    return { clientX: touch.clientX, clientY: touch.clientY }
  }
  return { clientX: event.clientX, clientY: event.clientY }
}

function onPolygonPointMove(event: PointerEvent) {
  const state = polygonPointDrag.value
  const context = activePolygonContext.value
  const canvas = canvasEl.value
  if (!state || !context || !canvas) return
  event.preventDefault()
  const rect = canvas.getBoundingClientRect()
  const canvasX = (event.clientX - rect.left) / Math.max(0.001, canvasScale.value)
  const canvasY = (event.clientY - rect.top) / Math.max(0.001, canvasScale.value)
  const rawX = (canvasX - context.x) / Math.max(1, context.width)
  const rawY = (canvasY - context.y) / Math.max(1, context.height)
  const snapped = snapPolygonPoint(rawX, rawY, state.index)
  const points = [...activePolygonRelativePoints.value]
  points[state.index] = snapped
  setActivePolygonPoints(points)
}

function stopPolygonPointDrag() {
  polygonPointDrag.value = null
  polygonSnapGuide.value = { x: null, y: null }
  window.removeEventListener('pointermove', onPolygonPointMove)
  window.removeEventListener('pointerup', stopPolygonPointDrag)
}

function startPolygonPointDrag(index: number, event: PointerEvent) {
  polygonPointDrag.value = { index }
  event.currentTarget instanceof HTMLElement && event.currentTarget.setPointerCapture?.(event.pointerId)
  window.addEventListener('pointermove', onPolygonPointMove)
  window.addEventListener('pointerup', stopPolygonPointDrag)
}

function toggleFloatingLayerList() {
  if (!floatingLayerListCollapsed.value) {
    closeFloatingLayerList()
    return
  }
  positionFloatingLayerListNearToolbar()
  floatingLayerListCollapsed.value = false
  nextTick(() => {
    positionFloatingLayerListNearToolbar()
    window.setTimeout(() => {
      window.addEventListener('click', onFloatingLayerListDocumentClick)
    }, 0)
  })
}

const onPointerMove = (event: MouseEvent | TouchEvent) => {
  const state = dragState.value
  if (!state) return
  event.preventDefault()
  const canvas = canvasEl.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  if (!rect.width || !rect.height) return

  const point = getPointerPosition(event)
  if (!point) return

  const dx = point.clientX - state.startX
  const dy = point.clientY - state.startY

  if (state.mode === 'move' || state.mode === 'resize') {
    const scaleX = CANVAS_WIDTH / rect.width
    const scaleY = CANVAS_HEIGHT / rect.height

    if (state.mode === 'move') {
      const nextX = state.originX + dx * scaleX
      const nextY = state.originY + dy * scaleY

      updateLayout((layout) => {
        updateLayerById(layout.layers, state.layerId, (layer) => {
          const snapped = snapLayerPosition(nextX, nextY, layer)
          return {
            ...(layer as any),
            x: Math.round(snapped.x),
            y: Math.round(snapped.y),
          }
        })
      })
    } else if (state.mode === 'resize') {
      activeSnapGuides.value = { vertical: [], horizontal: [] }
      const originWidth = state.originWidth ?? 0
      const originHeight = state.originHeight ?? 0
      if (originWidth <= 0 || originHeight <= 0) return

      const aspect = originWidth / originHeight || 1

      let nextWidth: number
      let nextHeight: number

      if (!lockAspectRatio.value) {
        nextWidth = Math.max(10, originWidth + dx * scaleX)
        nextHeight = Math.max(10, originHeight + dy * scaleY)
      } else {
        const delta = Math.abs(dx * scaleX) > Math.abs(dy * scaleY) ? dx * scaleX : dy * scaleY
        nextWidth = Math.max(10, originWidth + delta)
        nextHeight = Math.max(10, nextWidth / aspect)
      }

      updateLayout((layout) => {
        updateLayerById(layout.layers, state.layerId, (layer) => ({
          ...(layer as any),
          width: Math.round(Math.min(nextWidth, CANVAS_WIDTH)),
          height: Math.round(Math.min(nextHeight, CANVAS_HEIGHT)),
        }))
      })
    }

    return
  }

  // 旋转模式：根据水平位移调整角度
  if (state.mode === 'rotate') {
    activeSnapGuides.value = { vertical: [], horizontal: [] }
    const originRotation = state.originRotation ?? 0
    const delta = dx * 0.2 // 每移动 5px 大约 1 度
    const nextRotation = originRotation + delta

    updateLayout((layout) => {
      updateLayerById(layout.layers, state.layerId, (layer) => ({
        ...(layer as any),
        rotation: Math.round(nextRotation),
      }))
    })
  }
}

const onPointerUp = () => {
  dragState.value = null
  activeSnapGuides.value = { vertical: [], horizontal: [] }
  window.removeEventListener('pointermove', onPointerMove as any)
  window.removeEventListener('pointerup', onPointerUp)
  window.removeEventListener('mousemove', onPointerMove as any)
  window.removeEventListener('mouseup', onPointerUp)
  window.removeEventListener('touchmove', onPointerMove as any)
  window.removeEventListener('touchend', onPointerUp)
}

function startPointerTracking() {
  window.addEventListener('pointermove', onPointerMove as any)
  window.addEventListener('pointerup', onPointerUp)
  window.addEventListener('mousemove', onPointerMove as any)
  window.addEventListener('mouseup', onPointerUp)
  window.addEventListener('touchmove', onPointerMove as any, { passive: false } as any)
  window.addEventListener('touchend', onPointerUp)
}

function onLayerMouseDown(id: string, event: MouseEvent | TouchEvent) {
  event.preventDefault()
  const layer = findLayerById(layout.value.layers, id)
  if (!layer) return
  const point = getPointerPosition(event)
  if (!point) return
  dragState.value = {
    layerId: id,
    startX: point.clientX,
    startY: point.clientY,
    originX: layer.x,
    originY: layer.y,
    mode: 'move',
  }
  selectedLayerId.value = id
  startPointerTracking()
}

function onSvgLayerPointerDown(id: string, event: PointerEvent) {
  onLayerMouseDown(id, event)
}

function onLayerResizeStart(id: string, event: MouseEvent | TouchEvent) {
  event.preventDefault()
  const layer = findLayerById(layout.value.layers, id)
  if (!layer) return
  const point = getPointerPosition(event)
  if (!point) return
  dragState.value = {
    layerId: id,
    startX: point.clientX,
    startY: point.clientY,
    originX: layer.x,
    originY: layer.y,
    originWidth: layer.width,
    originHeight: layer.height,
    mode: 'resize',
  }
  selectedLayerId.value = id
  startPointerTracking()
}

function onLayerRotateStart(id: string, event: MouseEvent | TouchEvent) {
  event.preventDefault()
  const layer = findLayerById(layout.value.layers, id)
  if (!layer) return
  const point = getPointerPosition(event)
  if (!point) return
  dragState.value = {
    layerId: id,
    startX: point.clientX,
    startY: point.clientY,
    originX: layer.x,
    originY: layer.y,
    originRotation: layer.rotation ?? 0,
    mode: 'rotate',
  }
  selectedLayerId.value = id
  startPointerTracking()
}

function onLayerTouchMove(id: string, event: TouchEvent) {
  if (sliderActive) {
    event.preventDefault()
    event.stopPropagation()
    return
  }
  onPointerMove(event)
}

function onLayerTouchEnd(event: TouchEvent) {
  onPointerUp()
}

function changeSelectedZIndex(delta: number) {
  const id = selectedLayerId.value
  if (!id) return
  updateLayout((layout) => {
    updateLayerById(layout.layers, id, (layer) => ({
      ...(layer as any),
      zIndex: Math.max(0, (Number(layer.zIndex) || 0) + delta),
    }))
  })
}

onUnmounted(() => {
  if (dragState.value) {
    window.removeEventListener('pointermove', onPointerMove as any)
    window.removeEventListener('pointerup', onPointerUp)
    window.removeEventListener('mousemove', onPointerMove as any)
    window.removeEventListener('mouseup', onPointerUp)
    window.removeEventListener('touchmove', onPointerMove as any)
    window.removeEventListener('touchend', onPointerUp)
  }
  canvasResizeObserver?.disconnect()
  canvasPaneResizeObserver?.disconnect()
  if (windowResizeAttached) {
    window.removeEventListener('resize', updateCanvasScale)
  }
  if (typeof window !== 'undefined') {
    window.removeEventListener('paste', onEditorPaste)
  }
  closeFloatingLayerList()
  stopPolygonPointDrag()
})

onMounted(() => {
  nextTick(() => {
    if (typeof window !== 'undefined') {
      refreshImageRegistry()
    }
    updateCanvasScale()
    attachTransformer()
    if (canvasEl.value && typeof ResizeObserver !== 'undefined') {
      canvasResizeObserver = new ResizeObserver(() => updateCanvasScale())
      canvasResizeObserver.observe(canvasEl.value)
      if (canvasPaneEl.value) {
        canvasPaneResizeObserver = new ResizeObserver(() => updateCanvasScale())
        canvasPaneResizeObserver.observe(canvasPaneEl.value)
      }
    } else {
      window.addEventListener('resize', updateCanvasScale)
      windowResizeAttached = true
    }
    window.addEventListener('paste', onEditorPaste)
  })
  void loadFontLibrary()
})

watch(
  () => props.previewSource,
  () => {
    nextTick(() => updateCanvasScale())
  },
  { deep: true },
)

watch(
  () => firstImage.value?.src,
  async (src) => {
    if (!src) {
      autoBlendColor.value = defaultAutoBlendColor.value
      return
    }
    const extracted = await extractComfortableColor(src)
    autoBlendColor.value = extracted || defaultAutoBlendColor.value
  },
  { immediate: true },
)

watch(selectedLayerId, () => {
  nextTick(() => attachTransformer())
})

watch(
  () => props.floatingToolsVisible,
  (visible) => {
    if (!visible) closeFloatingLayerList()
  },
)
</script>

<style scoped>
.mcr-layout-editor {
  --v-theme-surface: var(--mcr-v-theme-surface);
  --v-theme-surface-variant: var(--mcr-v-theme-surface-variant);
  --v-theme-on-surface: var(--mcr-v-theme-on-surface);
  --v-theme-on-surface-variant: var(--mcr-v-theme-on-surface-variant);
  --v-theme-primary: var(--mcr-v-theme-primary);
  --v-theme-on-primary: var(--mcr-v-theme-on-primary);
  padding: 18px;
  border-radius: 18px !important;
  background: var(--mcr-color-surface-container-low) !important;
  background-color: var(--mcr-color-surface-container-low) !important;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.78) !important;
  box-shadow: 0 18px 44px rgba(var(--mcr-rgb-shadow), 0.08), 0 2px 10px rgba(var(--mcr-rgb-shadow), 0.05) !important;
  color: var(--mcr-color-on-surface);
}

.mcr-layout-editor :deep(.v-card__underlay),
.mcr-layout-editor :deep(.v-field__underlay),
.mcr-layout-editor :deep(.v-field__loader),
.mcr-layout-editor :deep(.v-input__details),
.mcr-layout-editor :deep(.v-card-item),
.mcr-layout-editor :deep(.v-card-text) {
  background: transparent !important;
  background-color: transparent !important;
}

:global(.v-overlay__content .mcr-layout-editor.v-card:not(.bg-primary)),
:global(.v-overlay__content .mcr-layout-editor .v-card:not(.bg-primary)),
:global(.v-overlay__content .mcr-layout-side-pane),
:global(.v-overlay__content .mcr-layout-bottom),
:global(.v-overlay__content .mcr-layer-list-wrapper) {
  backdrop-filter: none !important;
  background-color: var(--mcr-color-surface-container-lowest) !important;
  color: var(--mcr-color-on-surface) !important;
}

.mcr-layout-editor--embedded {
  padding: 0;
  background: transparent !important;
  border: 0 !important;
  border-radius: 0 !important;
}

.mcr-layout-workbench {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(360px, 0.65fr);
  gap: 18px;
  align-items: start;
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
}

.mcr-layout-canvas-pane,
.mcr-layout-side-pane {
  min-width: 0;
  padding: 14px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.96) !important;
  background-image: none !important;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.82);
  border-radius: 18px;
  box-shadow: 0 14px 30px rgba(var(--mcr-rgb-shadow), 0.08);
}

.mcr-layout-stage-wrap {
  width: 100%;
}

.mcr-layout-side-pane {
  --mcr-editor-text: var(--mcr-color-on-surface);
  --mcr-editor-cyan: var(--mcr-color-primary-container);
  --mcr-editor-cyan-soft: rgba(var(--mcr-rgb-primary-container), 0.16);
  --mcr-editor-orange: var(--mcr-color-tertiary);
  --mcr-editor-orange-soft: rgba(var(--mcr-rgb-tertiary), 0.14);
  --mcr-editor-delete: var(--mcr-color-error);
  --v-theme-primary: var(--mcr-v-theme-primary);
  --v-theme-on-primary: var(--mcr-v-theme-on-primary);
  --v-theme-surface: var(--mcr-v-theme-surface);
  --v-theme-surface-variant: var(--mcr-v-theme-surface-variant);
  --v-theme-on-surface: var(--mcr-v-theme-on-surface);
  --v-theme-on-surface-variant: var(--mcr-v-theme-on-surface-variant);
  --v-medium-emphasis-opacity: 0.92;
  max-height: none;
  overflow: auto;
  background-color: rgba(var(--mcr-rgb-surface-container-lowest), 0.96) !important;
  color: var(--mcr-editor-text) !important;
  scrollbar-color: rgba(var(--mcr-rgb-primary-container), 0.48) rgba(var(--mcr-rgb-surface-container-highest), 0.8);
}

.mcr-layout-side-pane :deep(*) {
  color: inherit;
}

.mcr-layout-heading {
  font-size: 12px;
  line-height: 1;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--mcr-editor-cyan);
  text-shadow: 0 0 10px rgba(var(--mcr-rgb-primary-container), 0.32);
}

.mcr-layout-top-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.mcr-layer-list-wrapper {
  flex: 1 1 180px;
  min-width: 160px;
  color: var(--mcr-editor-text) !important;
}

.mcr-background-panel {
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(var(--mcr-rgb-primary-container), 0.28);
}

.mcr-layer-actions {
  flex: 1 1 200px;
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 6px;
}

.mcr-layer-actions--canvas {
  flex: initial;
  justify-content: flex-start;
  align-items: center;
  margin-bottom: 12px;
  position: relative;
  z-index: 3;
}

.mcr-sticker-file-input {
  position: fixed;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.mcr-sticker-library {
  margin: -2px 0 12px;
  padding: 12px;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.72);
  border-radius: 16px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.96);
  color: var(--mcr-color-on-surface);
  box-shadow: 0 12px 28px rgba(var(--mcr-rgb-shadow), 0.08);
}

.mcr-sticker-library__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.mcr-sticker-library__title {
  color: var(--mcr-color-on-surface);
  font-size: 14px;
  font-weight: 760;
  line-height: 1.25;
}

.mcr-sticker-library__hint {
  margin-top: 2px;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.72);
  font-size: 12px;
  line-height: 1.35;
}

.mcr-sticker-library__actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 6px;
}

.mcr-sticker-library__close {
  width: 32px !important;
  height: 32px !important;
}

.mcr-sticker-library__empty {
  display: grid;
  min-height: 78px;
  place-items: center;
  border: 1px dashed rgba(var(--mcr-rgb-outline-variant), 0.68);
  border-radius: 12px;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.72);
  font-size: 13px;
}

.mcr-sticker-library__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(84px, 1fr));
  gap: 8px;
  max-height: 210px;
  overflow: auto;
  padding-right: 2px;
}

.mcr-sticker-item {
  position: relative;
  display: grid;
  gap: 6px;
  min-width: 0;
  padding: 7px;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.58);
  border-radius: 12px;
  background: rgba(var(--mcr-rgb-surface-container-low), 0.86);
  color: var(--mcr-color-on-surface);
  cursor: pointer;
  transition:
    border-color 160ms ease,
    background-color 160ms ease,
    transform 160ms ease;
}

.mcr-sticker-item:hover {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.72);
  background: rgba(var(--mcr-rgb-primary-container), 0.10);
  transform: translateY(-1px);
}

.mcr-sticker-item__thumb {
  display: grid;
  width: 100%;
  aspect-ratio: 1;
  place-items: center;
  overflow: hidden;
  border-radius: 10px;
  background:
    linear-gradient(45deg, rgba(var(--mcr-rgb-outline-variant), 0.20) 25%, transparent 25%),
    linear-gradient(-45deg, rgba(var(--mcr-rgb-outline-variant), 0.20) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, rgba(var(--mcr-rgb-outline-variant), 0.20) 75%),
    linear-gradient(-45deg, transparent 75%, rgba(var(--mcr-rgb-outline-variant), 0.20) 75%),
    rgba(var(--mcr-rgb-surface-container-lowest), 0.82);
  background-position: 0 0, 0 6px, 6px -6px, -6px 0;
  background-size: 12px 12px;
}

.mcr-sticker-item__thumb img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.mcr-sticker-item__name {
  min-width: 0;
  overflow: hidden;
  color: rgba(var(--mcr-rgb-on-surface), 0.88);
  font-size: 11px;
  font-weight: 650;
  line-height: 1.2;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcr-sticker-item__delete {
  position: absolute;
  top: 6px;
  right: 6px;
  display: grid;
  width: 26px;
  height: 26px;
  place-items: center;
  border: 1px solid rgba(var(--mcr-rgb-error), 0.30);
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.88);
  color: var(--mcr-color-error);
  opacity: 0;
  box-shadow: 0 6px 16px rgba(var(--mcr-rgb-shadow), 0.14);
  transition: opacity 160ms ease, transform 160ms ease;
}

.mcr-sticker-item:hover .mcr-sticker-item__delete,
.mcr-sticker-item:focus-visible .mcr-sticker-item__delete {
  opacity: 1;
}

.mcr-sticker-item__delete--active {
  border-color: rgba(var(--mcr-rgb-error), 0.52);
  background: rgba(var(--mcr-rgb-error-container), 0.88);
  color: var(--mcr-color-on-error-container);
}

@media (hover: none) {
  .mcr-sticker-item__delete {
    opacity: 1;
  }
}

.mcr-layer-popover-anchor {
  display: flex;
  width: 100%;
  min-width: 0;
}

.mcr-parameter-layer-header {
  position: sticky;
  top: 0;
  z-index: 8;
  display: flex;
  justify-content: flex-start;
  margin: -2px 0 14px;
  padding: 2px 0 10px;
}

.mcr-layer-actions :deep(.mcr-layer-button) {
  width: 166px;
  max-width: 166px;
  min-width: 166px;
}

.mcr-layer-actions :deep(.mcr-layer-button),
.mcr-parameter-layer-header :deep(.mcr-layer-button) {
  border: 1px solid rgba(var(--mcr-rgb-tertiary-container), 0.90) !important;
  background:
    linear-gradient(135deg, rgba(var(--mcr-rgb-tertiary-container), 0.30), rgba(var(--mcr-rgb-primary-container), 0.14)),
    rgba(var(--mcr-rgb-surface-container-lowest), 0.94) !important;
  color: var(--mcr-layer-button-foreground, var(--mcr-color-tertiary)) !important;
  box-shadow:
    inset 0 0 0 1px rgba(var(--mcr-rgb-surface-container-lowest), 0.50),
    0 8px 18px rgba(var(--mcr-rgb-shadow), 0.10),
    0 0 18px rgba(var(--mcr-rgb-tertiary-container), 0.18) !important;
}

.mcr-parameter-layer-header :deep(.mcr-layer-button) {
  width: 100%;
  max-width: none;
  min-width: 0;
}

.mcr-layer-actions :deep(.mcr-layer-button .v-btn__content),
.mcr-parameter-layer-header :deep(.mcr-layer-button .v-btn__content) {
  width: 100%;
  min-width: 0;
  justify-content: flex-start;
  gap: 6px;
}

.mcr-layer-actions :deep(.mcr-layer-button .v-btn__prepend),
.mcr-parameter-layer-header :deep(.mcr-layer-button .v-btn__prepend) {
  margin-inline-end: 4px;
  color: var(--mcr-layer-button-foreground, var(--mcr-color-tertiary));
}

.mcr-layer-button__label {
  display: block;
  min-width: 0;
  flex: 1 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: left;
  font-weight: 850;
}

.mcr-layer-button__chevron {
  flex: 0 0 auto;
  margin-left: auto;
  opacity: 0.78;
}

.mcr-text-align-control {
  display: inline-grid;
  grid-template-columns: repeat(3, 40px);
  gap: 4px;
  padding: 4px;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.70);
  border-radius: 12px;
  background: var(--mcr-color-surface-container-low);
}

.mcr-text-align-button {
  display: grid;
  width: 40px;
  height: 34px;
  place-items: center;
  padding: 0;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--mcr-color-on-surface-variant);
  cursor: pointer;
  transition: background-color 160ms ease, color 160ms ease, box-shadow 160ms ease;
}

.mcr-text-align-button:hover {
  color: var(--mcr-color-primary);
  background: var(--mcr-color-surface-container);
}

.mcr-text-align-button--active {
  color: var(--mcr-color-on-primary);
  background: var(--mcr-color-primary);
  box-shadow: 0 5px 14px rgba(var(--mcr-rgb-primary), 0.20);
}

.mcr-floating-layer-list {
  position: fixed;
  z-index: 2400;
  width: min(204px, calc(100% - 24px));
  overflow: hidden;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.74);
  border-radius: 14px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.92);
  box-shadow: 0 18px 42px rgba(var(--mcr-rgb-shadow), 0.14);
  backdrop-filter: blur(18px);
}

.mcr-floating-layer-list .mcr-layer-list {
  max-height: 232px;
  border: 0;
  border-radius: 14px;
  box-shadow: none;
}

.mcr-layer-list__option {
  display: flex;
  width: 100%;
  min-height: 34px;
  min-width: 0;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border: 0;
  background: transparent;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.88);
  cursor: pointer;
  font: inherit;
  text-align: left;
}

.mcr-layer-list__option:hover {
  background: rgba(var(--mcr-rgb-primary-container), 0.08);
}

.mcr-layer-list__option--active {
  background: rgba(var(--mcr-rgb-primary-fixed), 0.42);
  color: var(--mcr-color-primary);
  box-shadow: inset 3px 0 0 var(--mcr-color-primary-container);
}

.mcr-layer-list__option > .v-icon {
  flex: 0 0 18px;
  opacity: 0.82;
}

.mcr-layer-list__content {
  display: flex;
  min-width: 0;
  flex: 1 1 auto;
  align-items: center;
  gap: 6px;
  line-height: 1.15;
}

.mcr-layer-list__name {
  min-width: 0;
  flex: 1 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcr-layer-list__delete {
  display: inline-flex;
  flex: 0 0 auto;
  width: 24px;
  height: 24px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.62);
  cursor: pointer;
}

.mcr-layer-list__delete:hover {
  background: rgba(var(--mcr-rgb-error-container), 0.16);
  color: var(--mcr-color-error);
}

.mcr-aspect-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.mcr-aspect-preset {
  min-height: 30px;
  padding: 0 10px;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.72);
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-surface-container-high), 0.42);
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.88);
  cursor: pointer;
  font-size: 11px;
  font-weight: 800;
}

.mcr-aspect-preset:hover {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.82);
  color: var(--mcr-color-primary);
}

.mcr-layer-actions :deep(.v-btn),
.mcr-layout-footer-slot :deep(.v-btn) {
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.46) !important;
  background: rgba(var(--mcr-rgb-primary-container), 0.09) !important;
  color: var(--mcr-color-primary-fixed) !important;
  box-shadow: 0 0 12px rgba(var(--mcr-rgb-primary-container), 0.12);
}

.mcr-layer-actions :deep(.mcr-button--danger),
.mcr-layout-footer-slot :deep(.mcr-button--danger) {
  border-color: rgba(var(--mcr-rgb-error-container), 0.72) !important;
  background: var(--mcr-color-error) !important;
  color: var(--mcr-color-surface) !important;
  box-shadow: 0 0 14px rgba(var(--mcr-rgb-error-container), 0.24);
}

.mcr-layout-canvas {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background:
    linear-gradient(rgba(var(--mcr-rgb-primary-container), 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--mcr-rgb-primary-container), 0.1) 1px, transparent 1px),
    var(--mcr-color-surface);
  background-size: 100px 100px;
  overflow: visible;
  isolation: isolate;
  contain: layout style;
  border-radius: 0;
  border: 1px solid rgba(var(--mcr-rgb-primary-fixed-dim), 0.56);
  box-shadow: 0 0 20px rgba(var(--mcr-rgb-primary-container), 0.12);
  touch-action: none;
}

.mcr-layout-canvas :deep(.mcr-svg-template-preview) {
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
}

.mcr-snap-guides {
  position: absolute;
  inset: 0;
  z-index: 34;
  pointer-events: none;
  overflow: visible;
}

.mcr-snap-guide {
  position: absolute;
  display: block;
  background: rgba(var(--mcr-rgb-primary), 0.92);
  box-shadow: 0 0 0 1px rgba(var(--mcr-rgb-surface), 0.48), 0 0 12px rgba(var(--mcr-rgb-primary), 0.28);
}

.mcr-snap-guide--vertical {
  top: 0;
  bottom: 0;
  width: 1.5px;
  transform: translateX(-50%);
}

.mcr-snap-guide--horizontal {
  left: 0;
  right: 0;
  height: 1.5px;
  transform: translateY(-50%);
}

.mcr-polygon-overlay {
  position: absolute;
  inset: 0;
  z-index: 40;
  pointer-events: none;
  overflow: visible;
}

.mcr-polygon-overlay__svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}

.mcr-polygon-overlay__shape {
  fill: rgba(var(--mcr-rgb-primary-container), 0.10);
  stroke: var(--mcr-color-primary-container);
  stroke-width: 2;
  stroke-dasharray: 8 6;
}

.mcr-polygon-overlay__guide {
  stroke: var(--mcr-color-tertiary-container);
  stroke-width: 1.5;
  stroke-dasharray: 6 5;
}

.mcr-polygon-anchor {
  position: absolute;
  z-index: 42;
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 2px solid var(--mcr-color-primary-container);
  border-radius: 999px;
  background: var(--mcr-color-surface-container-lowest);
  color: var(--mcr-color-primary);
  cursor: grab;
  font: inherit;
  font-size: 10px;
  font-weight: 800;
  pointer-events: auto;
  transform: translate(-50%, -50%);
  box-shadow: 0 4px 14px rgba(var(--mcr-rgb-shadow), 0.18), 0 0 0 3px rgba(var(--mcr-rgb-surface-container-lowest), 0.86);
}

.mcr-polygon-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mcr-layout-editor-note {
  color: rgba(var(--mcr-rgb-primary-fixed-dim), 0.78);
  font-size: 12px;
  line-height: 1.5;
}

.mcr-layout-canvas-fixed {
  position: absolute;
  inset: 0;
  width: 1920px;
  height: 1080px;
  transform-origin: top left;
}

.mcr-layout-canvas-bg {
  position: absolute;
  inset: 0;
}

.mcr-layout-canvas-overlay {
  position: absolute;
  inset: 0;
}

.mcr-inline-editor {
  position: absolute;
  z-index: 4;
  padding: 10px;
  border-radius: 0;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.95);
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.58);
}

.mcr-inline-editor__field {
  min-width: 220px;
}

.mcr-inline-editor__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.mcr-layer {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--mcr-charcoal, var(--mcr-color-on-surface));
  font-weight: 600;
  cursor: move;
  box-shadow: 0 2px 6px rgba(var(--mcr-rgb-shadow), 0.18);
  transition: box-shadow 0.15s ease, transform 0.15s ease;
  overflow: visible;
}

.mcr-layer--selected {
  box-shadow: 0 0 0 2px var(--mcr-charcoal, var(--mcr-color-on-surface)), 0 2px 6px rgba(var(--mcr-rgb-shadow), 0.18);
}

.mcr-layer-label {
  font-size: 1.4rem;
  text-shadow: 0 1px 2px rgba(var(--mcr-rgb-surface-container-lowest), 0.6);
  color: var(--mcr-color-surface-container-lowest);
}

.mcr-layer-label--fallback {
  padding: 8px 10px;
  border-radius: 6px;
  background: rgba(var(--mcr-rgb-on-surface), 0.55);
}

.mcr-layer-image,
.mcr-layer-text {
  width: 100%;
  height: 100%;
  display: block;
}

.mcr-layer-image {
  object-fit: cover;
  pointer-events: none;
}

.mcr-layer-text {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4%;
  color: var(--mcr-color-surface-container-lowest);
  text-align: center;
  font-weight: 600;
  line-height: 1.08;
  pointer-events: none;
  word-break: break-word;
}

.mcr-layer-text--subtitle {
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.mcr-layer-list {
  max-height: 240px;
  overflow-y: auto;
  border-radius: 0;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.86);
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.38);
  box-shadow: 0 0 14px rgba(var(--mcr-rgb-primary-container), 0.08);
}

.mcr-layer-list :deep(.v-list-item) {
  color: var(--mcr-editor-cyan-soft) !important;
}

.mcr-layer-list :deep(.v-list-item--active) {
  background: rgba(var(--mcr-rgb-tertiary), 0.14) !important;
  color: var(--mcr-editor-orange) !important;
  box-shadow: inset 3px 0 0 rgba(var(--mcr-rgb-tertiary), 0.82), 0 0 12px rgba(var(--mcr-rgb-tertiary-container), 0.14);
}

.mcr-layout-side-pane :deep(.v-field) {
  min-height: 62px;
  --v-field-padding-top: 24px;
  --v-field-padding-bottom: 7px;
  --v-field-input-padding-top: 24px;
  --v-field-input-padding-bottom: 7px;
  background: rgba(var(--mcr-rgb-on-surface), 0.94) !important;
  background-color: rgba(var(--mcr-rgb-on-surface), 0.94) !important;
  border-radius: 0;
  color: var(--mcr-color-on-surface) !important;
  box-shadow:
    inset 0 0 0 1px rgba(var(--mcr-rgb-surface-container-lowest), 0.38),
    0 0 12px rgba(var(--mcr-rgb-primary-container), 0.08);
}

.mcr-layout-side-pane :deep(.v-field--active),
.mcr-layout-side-pane :deep(.v-field--focused),
.mcr-layout-side-pane :deep(.v-field--dirty) {
  background: rgba(var(--mcr-rgb-primary-fixed), 0.97) !important;
  background-color: rgba(var(--mcr-rgb-primary-fixed), 0.97) !important;
}

.mcr-layout-side-pane :deep(.v-field__overlay) {
  background-color: transparent !important;
  opacity: 1 !important;
}

.mcr-layout-side-pane :deep(.v-field__append-inner),
.mcr-layout-side-pane :deep(.v-field__prepend-inner),
.mcr-layout-side-pane :deep(.v-icon) {
  color: var(--mcr-color-primary) !important;
  opacity: 1 !important;
}

.mcr-layout-side-pane :deep(.v-input),
.mcr-layout-side-pane :deep(.v-input__control),
.mcr-layout-side-pane :deep(.v-field__field),
.mcr-layout-side-pane :deep(.v-selection-control),
.mcr-layout-side-pane :deep(.v-slider),
.mcr-layout-side-pane :deep(.v-slider__container) {
  color: var(--mcr-color-on-surface) !important;
}

.mcr-layout-side-pane :deep(.v-field__input),
.mcr-layout-side-pane :deep(.v-field__input input),
.mcr-layout-side-pane :deep(.v-field input),
.mcr-layout-side-pane :deep(.v-field textarea),
.mcr-layout-side-pane :deep(.v-select__selection),
.mcr-layout-side-pane :deep(.v-select__selection-text),
.mcr-layout-side-pane :deep(.v-list-item-title),
.mcr-layout-side-pane :deep(.v-switch__label),
.mcr-layout-side-pane :deep(.v-selection-control .v-label),
.mcr-layout-side-pane :deep(.v-slider.v-input),
.mcr-layout-side-pane :deep(.v-slider-thumb__label),
.mcr-layout-side-pane :deep(input),
.mcr-layout-side-pane :deep(textarea) {
  color: var(--mcr-color-on-surface) !important;
  -webkit-text-fill-color: var(--mcr-color-on-surface) !important;
}

.mcr-layout-side-pane :deep(.v-field__input) {
  min-height: 60px;
  padding: 25px 12px 7px !important;
  line-height: 1.25;
}

.mcr-layout-side-pane :deep(.v-field textarea.v-field__input),
.mcr-layout-side-pane :deep(textarea) {
  min-height: 76px;
  padding-top: 27px !important;
  line-height: 1.35;
}

.mcr-layout-side-pane :deep(.v-select .v-field__input) {
  min-height: 60px;
  padding: 25px 34px 7px 12px !important;
}

.mcr-layout-side-pane :deep(.v-field-label),
.mcr-layout-side-pane :deep(.v-field-label--floating) {
  position: absolute !important;
  top: 7px !important;
  right: 12px !important;
  left: 12px !important;
  max-width: calc(100% - 24px) !important;
  height: auto !important;
  overflow: hidden;
  color: var(--mcr-color-primary) !important;
  font-size: 11px !important;
  line-height: 1.15 !important;
  text-overflow: ellipsis;
  white-space: nowrap;
  opacity: 1 !important;
  transform: none !important;
  transform-origin: left top !important;
  pointer-events: none;
}

.mcr-layout-side-pane :deep(.v-label.v-field-label) {
  margin: 0 !important;
}

.mcr-layout-side-pane :deep(.v-select__selection-text) {
  overflow: hidden;
  color: var(--mcr-color-on-surface) !important;
  text-overflow: ellipsis;
  white-space: nowrap;
  -webkit-text-fill-color: var(--mcr-color-on-surface) !important;
}

:global(.v-overlay__content .v-list.mcr-layer-list),
:global(.v-overlay__content .v-list) {
  background-color: var(--mcr-color-surface-container-lowest) !important;
  color: var(--mcr-color-primary-container) !important;
}

:global(.v-overlay__content .v-list .v-list-item),
:global(.v-overlay__content .v-list .v-list-item-title),
:global(.v-overlay__content .v-list .v-list-item__content),
:global(.v-overlay__content .v-select__content .v-list-item),
:global(.v-overlay__content .v-select__content .v-list-item-title) {
  color: var(--mcr-color-primary-container) !important;
  -webkit-text-fill-color: var(--mcr-color-primary-container) !important;
}

:global(.v-overlay__content .v-list .v-list-item--active),
:global(.v-overlay__content .v-list .v-list-item--active .v-list-item-title) {
  background-color: rgba(var(--mcr-rgb-primary-container), 0.16) !important;
  color: var(--mcr-color-tertiary) !important;
  -webkit-text-fill-color: var(--mcr-color-tertiary) !important;
}

.mcr-layout-side-pane :deep(.v-field__outline) {
  color: rgba(var(--mcr-rgb-primary-container), 0.7) !important;
}

.mcr-layout-side-pane :deep(.v-label),
.mcr-layout-side-pane :deep(.v-field-label),
.mcr-layout-side-pane :deep(.v-field-label--floating),
.mcr-layout-side-pane :deep(.v-slider-track__tick-label),
.mcr-layout-side-pane :deep(.v-input__details) {
  color: var(--mcr-color-primary) !important;
  opacity: 1 !important;
}

.mcr-layout-side-pane :deep(.v-messages__message),
.mcr-layout-side-pane :deep(.v-slider__label),
.mcr-layout-side-pane :deep(.v-selection-control__wrapper + .v-label) {
  color: rgba(var(--mcr-rgb-primary-fixed), 0.92) !important;
  opacity: 1 !important;
}

.mcr-layout-side-pane :deep(.v-slider-track__fill) {
  background: var(--mcr-color-primary-container) !important;
  box-shadow: 0 0 10px rgba(var(--mcr-rgb-primary-container), 0.32);
}

.mcr-layout-side-pane :deep(.v-slider-track__background),
.mcr-layout-side-pane :deep(.v-slider-track__tick) {
  background: rgba(var(--mcr-rgb-primary-container), 0.28) !important;
}

.mcr-layout-side-pane :deep(.v-selection-control__input),
.mcr-layout-side-pane :deep(.v-switch__track),
.mcr-layout-side-pane :deep(.v-slider-thumb__label) {
  color: var(--mcr-color-primary-container) !important;
}

.mcr-layout-side-pane :deep(.v-switch__track) {
  background: rgba(var(--mcr-rgb-on-surface), 0.72) !important;
  color: var(--mcr-editor-cyan) !important;
  box-shadow: 0 0 10px rgba(var(--mcr-rgb-primary-container), 0.32);
}

.mcr-layout-side-pane :deep(.v-slider-thumb__surface) {
  background: var(--mcr-editor-orange) !important;
  color: var(--mcr-color-surface) !important;
  box-shadow: 0 0 14px rgba(var(--mcr-rgb-tertiary-container), 0.45);
}

.mcr-layout-side-pane :deep(.v-switch__thumb) {
  background: var(--mcr-editor-cyan) !important;
  color: var(--mcr-color-surface) !important;
  box-shadow: 0 0 14px rgba(var(--mcr-rgb-primary-container), 0.45);
}

.mcr-layout-footer-slot {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.mcr-layout-bottom {
  padding-top: 14px;
  border-top: 1px solid rgba(var(--mcr-rgb-primary-container), 0.26);
}

:global(.v-overlay__content .v-card.mcr-layout-editor:not(.bg-primary)),
:global(.v-overlay__content .mcr-layout-editor.v-card:not(.bg-primary)),
:global(.v-overlay__content .mcr-page-shell .mcr-layout-editor.v-card:not(.bg-primary)),
:global(.v-overlay__content .mcr-layout-editor .v-card:not(.bg-primary)),
:global(.v-overlay__content .mcr-layout-editor .v-sheet),
:global(.v-overlay__content .mcr-layout-editor .v-list),
:global(.v-overlay__content .mcr-layout-editor .v-row),
:global(.v-overlay__content .mcr-layout-editor .v-col),
:global(.v-overlay__content .mcr-layout-editor .v-input),
:global(.v-overlay__content .mcr-layout-editor .v-field),
:global(.v-overlay__content .mcr-layout-editor .v-field__field),
:global(.v-overlay__content .mcr-layout-editor .v-field__overlay),
:global(.v-overlay__content .mcr-layout-workbench),
:global(.v-overlay__content .mcr-layout-canvas-pane),
:global(.v-overlay__content .mcr-layout-side-pane),
:global(.v-overlay__content .mcr-layout-bottom),
:global(.v-overlay__content .mcr-layer-list-wrapper) {
  backdrop-filter: none !important;
  background-color: var(--mcr-color-surface-container-lowest) !important;
  background-image: none !important;
  color: var(--mcr-color-on-surface) !important;
}

:global(.v-overlay__content .mcr-layout-editor .v-card__underlay),
:global(.v-overlay__content .mcr-layout-editor .v-field__overlay),
:global(.v-overlay__content .mcr-layout-editor .v-field__underlay) {
  background-color: transparent !important;
  opacity: 0 !important;
}

:global(.v-overlay__content .mcr-layout-editor .v-label),
:global(.v-overlay__content .mcr-layout-editor .v-field-label),
:global(.v-overlay__content .mcr-layout-editor .v-slider__label),
:global(.v-overlay__content .mcr-layout-editor .v-slider-track__tick-label),
:global(.v-overlay__content .mcr-layout-editor .v-selection-control .v-label),
:global(.v-overlay__content .mcr-layout-editor .v-select__selection-text),
:global(.v-overlay__content .mcr-layout-editor .v-icon) {
  color: var(--mcr-color-primary-container) !important;
  opacity: 1 !important;
}

:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field__field) {
  min-height: 62px !important;
  background-color: rgba(var(--mcr-rgb-on-surface), 0.94) !important;
  color: var(--mcr-color-on-surface) !important;
}

:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field__overlay),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field__underlay) {
  background-color: transparent !important;
  opacity: 0 !important;
}

:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field__input),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field input),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field textarea),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-select__selection-text) {
  color: var(--mcr-color-on-surface) !important;
  -webkit-text-fill-color: var(--mcr-color-on-surface) !important;
}

:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field__input) {
  min-height: 60px !important;
  padding: 25px 12px 7px !important;
}

:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-select .v-field__input) {
  padding: 25px 34px 7px 12px !important;
}

:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-label),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field-label),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-input__details) {
  color: var(--mcr-color-primary) !important;
  opacity: 1 !important;
}

:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field-label),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field-label--floating) {
  top: 7px !important;
  right: 12px !important;
  left: 12px !important;
  max-width: calc(100% - 24px) !important;
  height: auto !important;
  overflow: hidden;
  font-size: 11px !important;
  line-height: 1.15 !important;
  text-overflow: ellipsis;
  white-space: nowrap;
  transform: none !important;
}

.mcr-layout-side-pane :deep(.v-slider .v-slider-track__fill),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-slider .v-slider-track__fill) {
  background:
    linear-gradient(90deg, rgba(var(--mcr-rgb-primary-container), 0.96), rgba(var(--mcr-rgb-primary-fixed-dim), 0.98)) !important;
  border-color: var(--mcr-color-primary-container) !important;
  opacity: 1 !important;
  box-shadow:
    0 0 10px rgba(var(--mcr-rgb-primary-container), 0.42),
    0 0 20px rgba(var(--mcr-rgb-primary-container), 0.16) !important;
}

.mcr-layout-side-pane :deep(.v-slider .v-slider-track__background),
.mcr-layout-side-pane :deep(.v-slider .v-slider-track__track),
.mcr-layout-side-pane :deep(.v-slider .v-slider-track__tick),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-slider .v-slider-track__background),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-slider .v-slider-track__track),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-slider .v-slider-track__tick) {
  background-color: rgba(var(--mcr-rgb-primary-fixed), 0.32) !important;
  border-color: rgba(var(--mcr-rgb-primary-fixed), 0.32) !important;
  opacity: 1 !important;
}

.mcr-layout-side-pane :deep(.v-slider .v-slider-thumb__surface),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-slider .v-slider-thumb__surface) {
  background-color: var(--mcr-color-primary-fixed) !important;
  border: 2px solid var(--mcr-color-primary-container) !important;
  color: var(--mcr-color-surface) !important;
  box-shadow:
    0 0 0 4px rgba(var(--mcr-rgb-primary-container), 0.16),
    0 0 16px rgba(var(--mcr-rgb-primary-container), 0.56) !important;
}

.mcr-layout-side-pane :deep(.v-slider .v-slider-thumb__label),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-slider .v-slider-thumb__label) {
  background-color: var(--mcr-color-primary-fixed) !important;
  color: var(--mcr-color-on-surface) !important;
}

.mcr-layer-handle {
  position: absolute;
  width: 12px;
  height: 12px;
  background-color: var(--mcr-off-white, var(--mcr-color-surface-container-lowest));
  border: 2px solid var(--mcr-charcoal, var(--mcr-color-on-surface));
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(var(--mcr-rgb-shadow), 0.2);
}

.mcr-layer-handle--resize {
  right: -7px;
  bottom: -7px;
  cursor: se-resize;
}

.mcr-layer-handle--rotate {
  top: -16px;
  left: 50%;
  transform: translateX(-50%);
  cursor: grab;
}

@media (max-width: 959px) {
  .mcr-layout-editor {
    padding: 12px;
  }

  .mcr-layout-editor--embedded {
    padding: 0;
  }

  .mcr-layout-workbench {
    grid-template-columns: 1fr;
  }

  .mcr-layout-side-pane {
    height: auto !important;
    max-height: none;
  }
}

/* Light Emby Studio editor skin. This only changes surfaces and controls; canvas math stays unchanged. */
.mcr-layout-editor {
  --mcr-editor-bg: var(--mcr-color-surface-container-low);
  --mcr-editor-surface: var(--mcr-color-surface-container-lowest);
  --mcr-editor-surface-soft: var(--mcr-color-surface);
  --mcr-editor-track: var(--mcr-color-surface-container-highest);
  --mcr-editor-text: var(--mcr-color-on-surface);
  --mcr-editor-muted: var(--mcr-color-on-surface-variant);
  --mcr-editor-cyan: var(--mcr-color-primary-container);
  --mcr-editor-cyan-soft: var(--mcr-color-primary);
  --mcr-editor-orange: var(--mcr-color-tertiary-container);
  --mcr-editor-orange-soft: var(--mcr-color-tertiary);
  --mcr-editor-delete: var(--mcr-color-error);
  --v-theme-primary: var(--mcr-v-theme-primary);
  --v-theme-on-primary: var(--mcr-v-theme-on-primary);
  --v-theme-surface: var(--mcr-v-theme-surface);
  --v-theme-surface-variant: var(--mcr-v-theme-surface-variant);
  --v-theme-on-surface: var(--mcr-v-theme-on-surface);
  --v-theme-on-surface-variant: var(--mcr-v-theme-on-surface-variant);
  padding: 18px;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.78) !important;
  border-radius: 18px !important;
  background: var(--mcr-editor-bg) !important;
  background-color: var(--mcr-editor-bg) !important;
  color: var(--mcr-editor-text) !important;
  box-shadow: 0 18px 44px rgba(var(--mcr-rgb-shadow), 0.08), 0 2px 10px rgba(var(--mcr-rgb-shadow), 0.05) !important;
}

.mcr-layout-editor--embedded {
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
}

.mcr-layout-workbench,
:global(.v-overlay__content .mcr-layout-workbench) {
  background: transparent !important;
  background-color: transparent !important;
}

.mcr-layout-canvas-pane,
.mcr-layout-side-pane,
:global(.v-overlay__content .mcr-layout-canvas-pane),
:global(.v-overlay__content .mcr-layout-side-pane),
:global(.v-overlay__content .mcr-layout-bottom),
:global(.v-overlay__content .mcr-layer-list-wrapper) {
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.78) !important;
  border-radius: 18px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.94) !important;
  background-color: rgba(var(--mcr-rgb-surface-container-lowest), 0.94) !important;
  color: var(--mcr-editor-text) !important;
  box-shadow: 0 14px 30px rgba(var(--mcr-rgb-shadow), 0.08) !important;
}

.mcr-layout-side-pane {
  scrollbar-color: rgba(var(--mcr-rgb-primary-container), 0.48) rgba(var(--mcr-rgb-surface-container-highest), 0.8);
}

.mcr-layout-heading,
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-heading) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.72) !important;
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0.14em;
  text-shadow: none !important;
}

.mcr-background-panel,
.mcr-layout-bottom {
  border-color: rgba(var(--mcr-rgb-surface-container-highest), 0.86) !important;
}

.mcr-layout-canvas {
  border: 1px solid rgba(var(--mcr-rgb-surface-container-lowest), 0.74) !important;
  border-radius: 22px;
  overflow: visible !important;
  contain: layout style !important;
  background:
    linear-gradient(rgba(var(--mcr-rgb-primary), 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--mcr-rgb-primary), 0.035) 1px, transparent 1px),
    var(--mcr-color-surface-container-lowest) !important;
  background-size: 24px 24px, 24px 24px, cover !important;
  box-shadow: 0 1px 2px rgba(var(--mcr-rgb-shadow), 0.07), 0 18px 42px rgba(var(--mcr-rgb-shadow), 0.12) !important;
}

.mcr-layout-editor-note {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.62) !important;
}

.mcr-layer-actions :deep(.v-btn),
.mcr-layout-footer-slot :deep(.v-btn) {
  border: 1px solid var(--mcr-button-border) !important;
  border-radius: 12px !important;
  background: var(--mcr-button-white) !important;
  color: var(--mcr-button-muted) !important;
  -webkit-text-fill-color: var(--mcr-button-muted) !important;
  box-shadow: var(--mcr-button-shadow) !important;
}

.mcr-layer-actions :deep(.v-btn:hover),
.mcr-layout-footer-slot :deep(.v-btn:hover) {
  border-color: rgba(var(--color-rgb-primary), 0.20) !important;
  background: var(--mcr-button-white) !important;
  color: var(--color-primary) !important;
  -webkit-text-fill-color: var(--color-primary) !important;
  box-shadow: var(--mcr-button-shadow-hover) !important;
  transform: translateY(-1px);
}

.mcr-layer-actions :deep(.mcr-button--primary),
.mcr-layout-footer-slot :deep(.mcr-button--primary) {
  border-color: var(--mcr-button-border) !important;
  background: var(--mcr-button-white) !important;
  color: var(--color-primary) !important;
  -webkit-text-fill-color: var(--color-primary) !important;
  box-shadow: var(--mcr-button-shadow) !important;
}

.mcr-layer-actions :deep(.mcr-button--danger),
.mcr-layout-footer-slot :deep(.mcr-button--danger) {
  border-color: rgba(var(--color-rgb-danger), 0.18) !important;
  background: var(--mcr-button-white) !important;
  color: var(--color-danger) !important;
  -webkit-text-fill-color: var(--color-danger) !important;
  box-shadow: var(--mcr-button-shadow) !important;
}

.mcr-layer-list,
:global(.v-overlay__content .v-list.mcr-layer-list) {
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.82) !important;
  border-radius: 14px;
  background: var(--mcr-color-surface) !important;
  color: var(--mcr-editor-text) !important;
  box-shadow: none !important;
}

.mcr-layer-list :deep(.v-list-item),
.mcr-layer-list :deep(.v-list-item-title),
:global(.v-overlay__content .mcr-layout-editor .v-list .v-list-item),
:global(.v-overlay__content .mcr-layout-editor .v-list .v-list-item-title),
:global(.v-overlay__content .mcr-layout-editor .v-select__content .v-list-item),
:global(.v-overlay__content .mcr-layout-editor .v-select__content .v-list-item-title) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.88) !important;
  -webkit-text-fill-color: rgba(var(--mcr-rgb-on-surface-variant), 0.88) !important;
}

.mcr-layer-list :deep(.v-list-item--active),
.mcr-layer-list :deep(.v-list-item--active .v-list-item-title),
:global(.v-overlay__content .mcr-layout-editor .v-list .v-list-item--active),
:global(.v-overlay__content .mcr-layout-editor .v-list .v-list-item--active .v-list-item-title) {
  background: rgba(var(--mcr-rgb-primary-fixed), 0.42) !important;
  color: var(--mcr-color-primary) !important;
  -webkit-text-fill-color: var(--mcr-color-primary) !important;
  box-shadow: inset 3px 0 0 var(--mcr-color-primary-container) !important;
}

:global(.v-overlay__content .v-list),
:global(.v-overlay__content .v-select__content .v-list) {
  background: var(--mcr-color-surface-container-lowest) !important;
  background-color: var(--mcr-color-surface-container-lowest) !important;
  color: var(--mcr-editor-text, var(--mcr-color-on-surface)) !important;
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.82);
  box-shadow: 0 18px 44px rgba(var(--mcr-rgb-shadow), 0.12);
}

:global(.v-overlay__content .v-list .v-list-item),
:global(.v-overlay__content .v-list .v-list-item-title),
:global(.v-overlay__content .v-list .v-list-item__content),
:global(.v-overlay__content .v-select__content .v-list-item),
:global(.v-overlay__content .v-select__content .v-list-item-title) {
  color: rgba(var(--mcr-rgb-surface-container-low), 0.86) !important;
  -webkit-text-fill-color: rgba(var(--mcr-rgb-surface-container-low), 0.86) !important;
}

:global(.v-overlay__content .v-list .v-list-item--active),
:global(.v-overlay__content .v-list .v-list-item--active .v-list-item-title) {
  background-color: rgba(var(--mcr-rgb-primary-fixed), 0.42) !important;
  color: var(--mcr-color-primary) !important;
  -webkit-text-fill-color: var(--mcr-color-primary) !important;
}

.mcr-inline-editor {
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.82) !important;
  border-radius: 14px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.96) !important;
  box-shadow: 0 16px 34px rgba(var(--mcr-rgb-shadow), 0.14);
}

.mcr-layout-side-pane :deep(.v-field),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field__field) {
  min-height: 56px !important;
  --v-field-padding-top: 21px;
  --v-field-padding-bottom: 7px;
  --v-field-input-padding-top: 21px;
  --v-field-input-padding-bottom: 7px;
  border-radius: 12px !important;
  background: var(--mcr-color-surface-container-lowest) !important;
  background-color: var(--mcr-color-surface-container-lowest) !important;
  color: var(--mcr-editor-text) !important;
  box-shadow: none !important;
}

.mcr-layout-side-pane :deep(.v-field--active),
.mcr-layout-side-pane :deep(.v-field--focused),
.mcr-layout-side-pane :deep(.v-field--dirty) {
  background: var(--mcr-color-surface-container-lowest) !important;
  background-color: var(--mcr-color-surface-container-lowest) !important;
}

.mcr-layout-side-pane :deep(.v-field__outline) {
  color: rgba(var(--mcr-rgb-outline-variant), 0.78) !important;
}

.mcr-layout-side-pane :deep(.v-field--focused .v-field__outline) {
  color: rgba(var(--mcr-rgb-primary-container), 0.72) !important;
}

.mcr-layout-side-pane :deep(.v-field__overlay),
.mcr-layout-side-pane :deep(.v-field__underlay),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field__overlay),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field__underlay) {
  background-color: transparent !important;
  opacity: 0 !important;
}

.mcr-layout-side-pane :deep(.v-field__append-inner),
.mcr-layout-side-pane :deep(.v-field__prepend-inner),
.mcr-layout-side-pane :deep(.v-icon),
:global(.v-overlay__content .mcr-layout-editor .v-icon) {
  color: var(--mcr-color-primary) !important;
  opacity: 1 !important;
}

.mcr-layout-side-pane :deep(.v-input),
.mcr-layout-side-pane :deep(.v-input__control),
.mcr-layout-side-pane :deep(.v-field__field),
.mcr-layout-side-pane :deep(.v-selection-control),
.mcr-layout-side-pane :deep(.v-slider),
.mcr-layout-side-pane :deep(.v-slider__container) {
  color: var(--mcr-editor-text) !important;
}

.mcr-layout-side-pane :deep(.v-field__input),
.mcr-layout-side-pane :deep(.v-field__input input),
.mcr-layout-side-pane :deep(.v-field input),
.mcr-layout-side-pane :deep(.v-field textarea),
.mcr-layout-side-pane :deep(.v-select__selection),
.mcr-layout-side-pane :deep(.v-select__selection-text),
.mcr-layout-side-pane :deep(.v-list-item-title),
.mcr-layout-side-pane :deep(.v-switch__label),
.mcr-layout-side-pane :deep(.v-selection-control .v-label),
.mcr-layout-side-pane :deep(.v-slider.v-input),
.mcr-layout-side-pane :deep(input),
.mcr-layout-side-pane :deep(textarea),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field__input),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field input),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field textarea),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-select__selection-text) {
  color: var(--mcr-editor-text) !important;
  -webkit-text-fill-color: var(--mcr-editor-text) !important;
}

.mcr-layout-side-pane :deep(.v-field__input),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field__input) {
  min-height: 56px !important;
  padding: 23px 12px 7px !important;
  line-height: 1.25;
}

.mcr-layout-side-pane :deep(.v-field textarea.v-field__input),
.mcr-layout-side-pane :deep(textarea) {
  min-height: 76px !important;
  padding-top: 25px !important;
}

.mcr-layout-side-pane :deep(.v-select .v-field__input),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-select .v-field__input) {
  min-height: 56px !important;
  padding: 23px 34px 7px 12px !important;
}

.mcr-layout-side-pane :deep(.v-label),
.mcr-layout-side-pane :deep(.v-field-label),
.mcr-layout-side-pane :deep(.v-field-label--floating),
.mcr-layout-side-pane :deep(.v-slider-track__tick-label),
.mcr-layout-side-pane :deep(.v-input__details),
:global(.v-overlay__content .mcr-layout-editor .v-label),
:global(.v-overlay__content .mcr-layout-editor .v-field-label),
:global(.v-overlay__content .mcr-layout-editor .v-slider__label),
:global(.v-overlay__content .mcr-layout-editor .v-slider-track__tick-label),
:global(.v-overlay__content .mcr-layout-editor .v-selection-control .v-label) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.70) !important;
  opacity: 1 !important;
}

.mcr-layout-side-pane :deep(.v-field-label),
.mcr-layout-side-pane :deep(.v-field-label--floating),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field-label),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-field-label--floating) {
  top: 7px !important;
  right: 12px !important;
  left: 12px !important;
  max-width: calc(100% - 24px) !important;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.70) !important;
  font-size: 11px !important;
  font-weight: 750;
  letter-spacing: 0.02em;
  transform: none !important;
}

.mcr-layout-side-pane :deep(.v-messages__message),
.mcr-layout-side-pane :deep(.v-slider__label),
.mcr-layout-side-pane :deep(.v-selection-control__wrapper + .v-label) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.58) !important;
}

.mcr-layout-side-pane :deep(.v-slider .v-slider-track__fill),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-slider .v-slider-track__fill) {
  background: var(--mcr-color-primary-container) !important;
  border-color: var(--mcr-color-primary-container) !important;
  box-shadow: none !important;
}

.mcr-layout-side-pane :deep(.v-slider .v-slider-track__background),
.mcr-layout-side-pane :deep(.v-slider .v-slider-track__track),
.mcr-layout-side-pane :deep(.v-slider .v-slider-track__tick),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-slider .v-slider-track__background),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-slider .v-slider-track__track),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-slider .v-slider-track__tick) {
  background-color: rgba(var(--mcr-rgb-surface-container-highest), 0.88) !important;
  border-color: rgba(var(--mcr-rgb-surface-container-highest), 0.88) !important;
}

.mcr-layout-side-pane :deep(.v-slider .v-slider-thumb__surface),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-slider .v-slider-thumb__surface) {
  background-color: var(--mcr-color-surface-container-lowest) !important;
  border: 4px solid var(--mcr-color-primary-container) !important;
  color: var(--mcr-color-primary) !important;
  box-shadow: 0 2px 8px rgba(var(--mcr-rgb-shadow), 0.16) !important;
}

.mcr-layout-side-pane :deep(.v-slider .v-slider-thumb__label),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-slider .v-slider-thumb__label) {
  background-color: var(--mcr-color-primary) !important;
  color: var(--mcr-color-surface-container-lowest) !important;
  -webkit-text-fill-color: var(--mcr-color-surface-container-lowest) !important;
}

.mcr-layout-side-pane :deep(.v-switch__track) {
  background: var(--mcr-color-surface-container-highest) !important;
  color: var(--mcr-color-primary-container) !important;
  box-shadow: none !important;
}

.mcr-layout-side-pane :deep(.v-selection-control--dirty .v-switch__track) {
  background: var(--mcr-color-primary-container) !important;
}

.mcr-layout-side-pane :deep(.v-switch__thumb) {
  background: var(--mcr-color-surface-container-lowest) !important;
  color: var(--mcr-color-primary) !important;
  box-shadow: 0 2px 8px rgba(var(--mcr-rgb-shadow), 0.18) !important;
}

.mcr-layer-handle {
  background-color: var(--mcr-color-surface-container-lowest);
  border-color: var(--mcr-color-primary);
}

/* Final studio skin for the parameter pane. It overrides the legacy blueprint rules above. */
.mcr-layout-side-pane,
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane) {
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.78) !important;
  border-radius: 18px !important;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.96) !important;
  color: var(--mcr-color-on-surface) !important;
  box-shadow: 0 14px 30px rgba(var(--mcr-rgb-shadow), 0.08) !important;
}

.mcr-background-panel,
.mcr-layout-bottom,
.mcr-layer-list-wrapper,
.mcr-layout-side-pane :deep(.v-card),
.mcr-layout-side-pane :deep(.v-sheet),
.mcr-layout-side-pane :deep(.v-expansion-panels),
.mcr-layout-side-pane :deep(.v-expansion-panel),
.mcr-layout-side-pane :deep(.v-expansion-panel-title),
.mcr-layout-side-pane :deep(.v-expansion-panel-text),
:global(.v-overlay__content .mcr-layout-editor .mcr-background-panel),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-bottom),
:global(.v-overlay__content .mcr-layout-editor .mcr-layer-list-wrapper) {
  border-color: rgba(var(--mcr-rgb-surface-container-highest), 0.82) !important;
  background: var(--mcr-color-surface-container-lowest) !important;
  background-color: var(--mcr-color-surface-container-lowest) !important;
  color: var(--mcr-color-on-surface) !important;
  box-shadow: none !important;
}

.mcr-layout-side-pane :deep(.mcr-blueprint-field),
.mcr-layout-side-pane :deep(.mcr-blueprint-select),
.mcr-layout-side-pane :deep(.mcr-blueprint-range) {
  color: var(--mcr-color-on-surface) !important;
  font-family: inherit !important;
}

.mcr-layout-side-pane :deep(.blueprint-range),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .blueprint-range) {
  margin-block: 4px 8px !important;
}

.mcr-layout-side-pane :deep(.v-row:has(.blueprint-range)),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-row:has(.blueprint-range)) {
  margin-top: 0 !important;
  margin-bottom: 0 !important;
}

.mcr-layout-side-pane :deep(.v-col:has(.blueprint-range)),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-col:has(.blueprint-range)) {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

.mcr-layout-side-pane :deep(.mcr-blueprint-field__control),
.mcr-layout-side-pane :deep(.mcr-blueprint-select__control),
.mcr-layout-side-pane :deep(.mcr-blueprint-select__multi-option),
:global(.v-overlay__content .mcr-layout-editor .mcr-blueprint-field__control),
:global(.v-overlay__content .mcr-layout-editor .mcr-blueprint-select__control),
:global(.v-overlay__content .mcr-layout-editor .mcr-blueprint-select__multi-option) {
  min-height: 42px !important;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.70) !important;
  border-radius: 12px !important;
  background: var(--mcr-color-surface-container-lowest) !important;
  background-image: none !important;
  color: var(--mcr-color-on-surface) !important;
  -webkit-text-fill-color: var(--mcr-color-on-surface) !important;
  box-shadow: none !important;
  font-family: inherit !important;
}

.mcr-layout-side-pane :deep(.mcr-blueprint-field__control:focus),
.mcr-layout-side-pane :deep(.mcr-blueprint-select__control:focus) {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.74) !important;
  box-shadow: 0 0 0 4px rgba(var(--mcr-rgb-primary-container), 0.11) !important;
}

.mcr-layout-side-pane :deep(.mcr-blueprint-select__multi-option--active) {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.72) !important;
  background: rgba(var(--mcr-rgb-primary-fixed), 0.38) !important;
  color: var(--mcr-color-on-primary-fixed-variant) !important;
  -webkit-text-fill-color: var(--mcr-color-on-primary-fixed-variant) !important;
  box-shadow: inset 3px 0 0 var(--mcr-color-primary-container) !important;
}

.mcr-layout-side-pane :deep(.v-selection-control__input),
.mcr-layout-side-pane :deep(.v-checkbox .v-selection-control__input),
.mcr-layout-side-pane :deep(.v-radio .v-selection-control__input) {
  color: var(--mcr-color-primary-container) !important;
}

.mcr-layout-side-pane :deep(.v-switch__track),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-switch__track) {
  background: var(--mcr-color-surface-container-highest) !important;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.72) !important;
  color: var(--mcr-color-primary-container) !important;
  opacity: 1 !important;
  box-shadow: none !important;
}

.mcr-layout-side-pane :deep(.v-selection-control--dirty .v-switch__track),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-selection-control--dirty .v-switch__track) {
  background: var(--mcr-color-primary-container) !important;
  border-color: var(--mcr-color-primary-container) !important;
}

.mcr-layout-side-pane :deep(.v-switch__thumb),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .v-switch__thumb) {
  background: var(--mcr-color-surface-container-lowest) !important;
  color: var(--mcr-color-primary) !important;
  box-shadow: 0 2px 8px rgba(var(--mcr-rgb-shadow), 0.18) !important;
}

.mcr-layout-side-pane :deep(.v-btn-toggle),
.mcr-layout-side-pane :deep(.v-btn-group) {
  border-color: rgba(var(--mcr-rgb-surface-container-highest), 0.78) !important;
  background: var(--mcr-color-surface) !important;
  box-shadow: none !important;
}

.mcr-layout-side-pane :deep(.v-btn),
.mcr-layer-actions :deep(.v-btn),
.mcr-layout-footer-slot :deep(.v-btn) {
  border-radius: 12px !important;
  font-family: inherit !important;
  letter-spacing: 0 !important;
  text-transform: none !important;
}

:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor),
html.dark .mcr-layout-editor,
.v-theme--dark .mcr-layout-editor {
  --mcr-editor-bg: var(--mcr-color-surface);
  --mcr-editor-surface: var(--mcr-color-surface-container-low);
  --mcr-editor-surface-soft: var(--mcr-color-surface-container);
  --mcr-editor-track: var(--mcr-color-surface-container-highest);
  --mcr-editor-text: var(--mcr-color-on-surface);
  --mcr-editor-muted: var(--mcr-color-on-surface-variant);
  --mcr-editor-cyan: var(--mcr-color-primary-container);
  --mcr-editor-cyan-soft: var(--mcr-color-primary);
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.86) !important;
  background: var(--mcr-color-surface) !important;
  color: var(--mcr-color-on-surface) !important;
  box-shadow: 0 18px 44px rgba(var(--mcr-rgb-shadow), 0.34) !important;
}

:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-side-pane),
:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-canvas-pane),
:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-bottom),
:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layer-list-wrapper),
html.dark .mcr-layout-side-pane,
html.dark .mcr-layout-canvas-pane,
html.dark .mcr-layout-bottom,
html.dark .mcr-layer-list-wrapper,
.v-theme--dark .mcr-layout-side-pane,
.v-theme--dark .mcr-layout-canvas-pane,
.v-theme--dark .mcr-layout-bottom,
.v-theme--dark .mcr-layer-list-wrapper {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.86) !important;
  background: rgba(var(--mcr-rgb-surface-container-low), 0.92) !important;
  color: var(--mcr-color-on-surface) !important;
  box-shadow: 0 18px 44px rgba(var(--mcr-rgb-shadow), 0.32) !important;
}

:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor .mcr-blueprint-field__control),
:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor .mcr-blueprint-select__control),
:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor .mcr-blueprint-select__multi-option),
html.dark .mcr-layout-editor :deep(.mcr-blueprint-field__control),
html.dark .mcr-layout-editor :deep(.mcr-blueprint-select__control),
html.dark .mcr-layout-editor :deep(.mcr-blueprint-select__multi-option),
.v-theme--dark .mcr-layout-editor :deep(.mcr-blueprint-field__control),
.v-theme--dark .mcr-layout-editor :deep(.mcr-blueprint-select__control),
.v-theme--dark .mcr-layout-editor :deep(.mcr-blueprint-select__multi-option) {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.92) !important;
  background: var(--mcr-color-surface-container-lowest) !important;
  color: var(--mcr-color-on-surface) !important;
  -webkit-text-fill-color: var(--mcr-color-on-surface) !important;
}

:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor .mcr-blueprint-select__multi-option--active),
html.dark .mcr-layout-editor :deep(.mcr-blueprint-select__multi-option--active),
.v-theme--dark .mcr-layout-editor :deep(.mcr-blueprint-select__multi-option--active) {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.72) !important;
  background: rgba(var(--mcr-rgb-primary-container), 0.14) !important;
  color: var(--mcr-color-primary) !important;
  -webkit-text-fill-color: var(--mcr-color-primary) !important;
  box-shadow: inset 3px 0 0 var(--mcr-color-primary-container) !important;
}

:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor .v-field),
:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor .v-list),
html.dark .mcr-layout-editor :deep(.v-field),
html.dark .mcr-layout-editor :deep(.v-list),
.v-theme--dark .mcr-layout-editor :deep(.v-field),
.v-theme--dark .mcr-layout-editor :deep(.v-list) {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.92) !important;
  background: var(--mcr-color-surface-container-lowest) !important;
  color: var(--mcr-color-on-surface) !important;
}

:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor .v-switch__track),
html.dark .mcr-layout-editor :deep(.v-switch__track),
.v-theme--dark .mcr-layout-editor :deep(.v-switch__track) {
  background: var(--mcr-color-surface-container-highest) !important;
  border-color: var(--mcr-color-outline-variant) !important;
}

:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor .v-selection-control--dirty .v-switch__track),
html.dark .mcr-layout-editor :deep(.v-selection-control--dirty .v-switch__track),
.v-theme--dark .mcr-layout-editor :deep(.v-selection-control--dirty .v-switch__track) {
  background: var(--mcr-color-primary-container) !important;
  border-color: var(--mcr-color-primary-container) !important;
}

/* Hard reset for the old blueprint editor shell. These selectors intentionally target
   the exact structural classes that were still carrying grid-blue backgrounds. */
.mcr-layout-editor,
:global(.v-overlay__content .mcr-layout-editor) {
  --v-theme-primary: var(--mcr-v-theme-primary);
  --v-theme-on-primary: var(--mcr-v-theme-on-primary);
  --v-theme-surface: var(--mcr-v-theme-surface);
  --v-theme-surface-variant: var(--mcr-v-theme-surface-variant);
  --v-theme-on-surface: var(--mcr-v-theme-on-surface);
  --v-theme-on-surface-variant: var(--mcr-v-theme-on-surface-variant);
  background: var(--mcr-color-surface-container-low) !important;
  background-color: var(--mcr-color-surface-container-low) !important;
  color: var(--mcr-color-on-surface) !important;
}

.mcr-layout-editor--embedded,
.mcr-layout-workbench,
:global(.v-overlay__content .mcr-layout-workbench) {
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
}

.mcr-layout-canvas-pane,
.mcr-layout-side-pane,
:global(.v-overlay__content .mcr-layout-canvas-pane),
:global(.v-overlay__content .mcr-layout-side-pane) {
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.82) !important;
  border-radius: 18px !important;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.96) !important;
  background-color: rgba(var(--mcr-rgb-surface-container-lowest), 0.96) !important;
  background-image: none !important;
  color: var(--mcr-color-on-surface) !important;
  box-shadow: 0 14px 30px rgba(var(--mcr-rgb-shadow), 0.08) !important;
}

.mcr-layout-canvas,
:global(.v-overlay__content .mcr-layout-canvas) {
  border: 1px solid rgba(var(--mcr-rgb-surface-container-highest), 0.86) !important;
  border-radius: 22px !important;
  overflow: visible !important;
  contain: layout style !important;
  background: var(--mcr-color-surface-container-lowest) !important;
  background-image: none !important;
  box-shadow: 0 1px 2px rgba(var(--mcr-rgb-shadow), 0.07), 0 18px 42px rgba(var(--mcr-rgb-shadow), 0.12) !important;
}

.mcr-layout-heading,
.mcr-layout-editor-note,
:global(.v-overlay__content .mcr-layout-heading),
:global(.v-overlay__content .mcr-layout-editor-note) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.72) !important;
  font-family: 'Geist', 'Be Vietnam Pro', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei',
    ui-sans-serif, system-ui, sans-serif !important;
  letter-spacing: 0.02em !important;
  text-transform: none !important;
  text-shadow: none !important;
}

.mcr-layout-side-pane :deep(.v-field),
.mcr-layout-side-pane :deep(.v-list),
.mcr-layout-side-pane :deep(.v-selection-control),
.mcr-layout-side-pane :deep(.v-slider),
:global(.v-overlay__content .mcr-layout-editor .v-field),
:global(.v-overlay__content .mcr-layout-editor .v-list),
:global(.v-overlay__content .mcr-layout-editor .v-selection-control),
:global(.v-overlay__content .mcr-layout-editor .v-slider) {
  color: var(--mcr-color-on-surface) !important;
  font-family: 'Geist', 'Be Vietnam Pro', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei',
    ui-sans-serif, system-ui, sans-serif !important;
}

.mcr-layout-side-pane :deep(.v-field),
:global(.v-overlay__content .mcr-layout-editor .v-field) {
  border-radius: 12px !important;
  background: var(--mcr-color-surface-container-lowest) !important;
  background-color: var(--mcr-color-surface-container-lowest) !important;
  box-shadow: none !important;
}

.mcr-layout-side-pane :deep(.v-field__input),
.mcr-layout-side-pane :deep(.v-select__selection-text),
.mcr-layout-side-pane :deep(.v-label),
.mcr-layout-side-pane :deep(.v-field-label),
.mcr-layout-side-pane :deep(input),
.mcr-layout-side-pane :deep(textarea),
:global(.v-overlay__content .mcr-layout-editor .v-field__input),
:global(.v-overlay__content .mcr-layout-editor .v-select__selection-text),
:global(.v-overlay__content .mcr-layout-editor .v-label),
:global(.v-overlay__content .mcr-layout-editor .v-field-label) {
  color: var(--mcr-color-on-surface) !important;
  -webkit-text-fill-color: var(--mcr-color-on-surface) !important;
}

:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor),
:global(.v-overlay__content .mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor) {
  --v-theme-primary: var(--mcr-v-theme-primary);
  --v-theme-on-primary: var(--mcr-v-theme-on-primary);
  --v-theme-surface: var(--mcr-v-theme-surface);
  --v-theme-surface-variant: var(--mcr-v-theme-surface-variant);
  --v-theme-on-surface: var(--mcr-v-theme-on-surface);
  --v-theme-on-surface-variant: var(--mcr-v-theme-on-surface-variant);
  background: var(--mcr-color-surface) !important;
  background-color: var(--mcr-color-surface) !important;
  color: var(--mcr-color-on-surface) !important;
}

:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-workbench) {
  background: transparent !important;
  background-image: none !important;
}

:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-canvas-pane),
:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-side-pane) {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.92) !important;
  background: rgba(var(--mcr-rgb-surface-container-low), 0.94) !important;
  background-color: rgba(var(--mcr-rgb-surface-container-low), 0.94) !important;
  background-image: none !important;
  color: var(--mcr-color-on-surface) !important;
  box-shadow: 0 18px 44px rgba(var(--mcr-rgb-shadow), 0.34) !important;
}

:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-canvas) {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.92) !important;
  background: var(--mcr-color-surface-container-lowest) !important;
  background-image: none !important;
  box-shadow: 0 18px 44px rgba(var(--mcr-rgb-shadow), 0.36) !important;
}

:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-heading),
:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor-note) {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.72) !important;
}

:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor .v-field),
:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor .v-list) {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.92) !important;
  background: var(--mcr-color-surface-container-lowest) !important;
  background-color: var(--mcr-color-surface-container-lowest) !important;
  color: var(--mcr-color-on-surface) !important;
}

:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor .v-field__input),
:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor .v-select__selection-text),
:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor .v-label),
:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor .v-field-label),
:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor input),
:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-editor textarea) {
  color: var(--mcr-color-on-surface) !important;
  -webkit-text-fill-color: var(--mcr-color-on-surface) !important;
}

@media (prefers-color-scheme: dark) {
  .mcr-layout-editor {
    --v-theme-primary: var(--mcr-v-theme-primary);
    --v-theme-on-primary: var(--mcr-v-theme-on-primary);
    --v-theme-surface: var(--mcr-v-theme-surface);
    --v-theme-surface-variant: var(--mcr-v-theme-surface-variant);
    --v-theme-on-surface: var(--mcr-v-theme-on-surface);
    --v-theme-on-surface-variant: var(--mcr-v-theme-on-surface-variant);
    background: var(--mcr-color-surface) !important;
    background-color: var(--mcr-color-surface) !important;
    color: var(--mcr-color-on-surface) !important;
  }

  .mcr-layout-workbench {
    background: transparent !important;
    background-image: none !important;
  }

  .mcr-layout-canvas-pane,
  .mcr-layout-side-pane {
    border-color: rgba(var(--mcr-rgb-outline-variant), 0.92) !important;
    background: rgba(var(--mcr-rgb-surface-container-low), 0.94) !important;
    background-color: rgba(var(--mcr-rgb-surface-container-low), 0.94) !important;
    background-image: none !important;
    color: var(--mcr-color-on-surface) !important;
    box-shadow: 0 18px 44px rgba(var(--mcr-rgb-shadow), 0.34) !important;
  }

  .mcr-layout-canvas {
    border-color: rgba(var(--mcr-rgb-outline-variant), 0.92) !important;
    background: var(--mcr-color-surface-container-lowest) !important;
    background-image: none !important;
    box-shadow: 0 18px 44px rgba(var(--mcr-rgb-shadow), 0.36) !important;
  }

  .mcr-layout-heading,
  .mcr-layout-editor-note {
    color: rgba(var(--mcr-rgb-on-surface-variant), 0.72) !important;
  }

  .mcr-layout-side-pane :deep(.v-field),
  .mcr-layout-side-pane :deep(.v-list) {
    border-color: rgba(var(--mcr-rgb-outline-variant), 0.92) !important;
    background: var(--mcr-color-surface-container-lowest) !important;
    background-color: var(--mcr-color-surface-container-lowest) !important;
    color: var(--mcr-color-on-surface) !important;
  }

  .mcr-layout-side-pane :deep(.v-field__input),
  .mcr-layout-side-pane :deep(.v-select__selection-text),
  .mcr-layout-side-pane :deep(.v-label),
  .mcr-layout-side-pane :deep(.v-field-label),
  .mcr-layout-side-pane :deep(input),
  .mcr-layout-side-pane :deep(textarea) {
    color: var(--mcr-color-on-surface) !important;
    -webkit-text-fill-color: var(--mcr-color-on-surface) !important;
  }
}

@media (max-width: 959px) {
  .mcr-layout-editor {
    padding: 12px;
  }

  .mcr-layout-editor--embedded {
    padding: 0;
  }

  .mcr-layout-workbench {
    grid-template-columns: 1fr;
  }

  .mcr-layout-side-pane {
    height: auto !important;
    max-height: none;
  }
}

/* Large paragraph-style layer heading with a soft fade into the controls below. */
.mcr-layout-side-pane .mcr-background-panel,
.mcr-layout-side-pane .mcr-layout-bottom,
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .mcr-background-panel),
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .mcr-layout-bottom) {
  position: relative;
}

.mcr-layout-side-pane .mcr-layout-heading,
:global(.v-overlay__content .mcr-layout-editor .mcr-layout-side-pane .mcr-layout-heading) {
  position: relative;
  display: block;
  width: fit-content;
  max-width: 100%;
  margin: 0 0 -3px !important;
  padding: 0 2px 7px 0;
  overflow: hidden;
  background: linear-gradient(
    180deg,
    rgba(var(--color-rgb-text-main, 24, 32, 51), 0.90) 0%,
    rgba(var(--color-rgb-text-secondary, 75, 88, 124), 0.62) 58%,
    rgba(var(--color-rgb-text-muted, 138, 150, 184), 0) 100%
  );
  color: transparent !important;
  font-size: clamp(30px, 3vw, 40px) !important;
  font-weight: 900 !important;
  line-height: 1 !important;
  letter-spacing: 0 !important;
  text-overflow: ellipsis;
  white-space: nowrap;
  pointer-events: none;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent !important;
}

:global(.mcr-page-shell[data-mcr-theme="dark"] .mcr-layout-side-pane .mcr-layout-heading),
html.dark .mcr-layout-side-pane .mcr-layout-heading,
.v-theme--dark .mcr-layout-side-pane .mcr-layout-heading {
  background: linear-gradient(
    180deg,
    rgba(244, 247, 251, 0.90) 0%,
    rgba(199, 208, 227, 0.58) 58%,
    rgba(135, 148, 173, 0) 100%
  );
  color: transparent !important;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent !important;
}

.mcr-floating-layer-list[data-mcr-theme="dark"] {
  border-color: rgba(230, 236, 245, 0.12);
  background: rgba(23, 32, 51, 0.98);
  color: #d4dbe8;
  box-shadow: 0 20px 46px rgba(0, 0, 0, 0.34);
}

.mcr-floating-layer-list[data-mcr-theme="dark"] .mcr-layer-list {
  background: transparent;
}

.mcr-floating-layer-list[data-mcr-theme="dark"] .mcr-layer-list__option {
  color: #c7d0e3;
}

.mcr-floating-layer-list[data-mcr-theme="dark"] .mcr-layer-list__option:hover {
  background: rgba(110, 162, 255, 0.10);
  color: #f4f7fb;
}

.mcr-floating-layer-list[data-mcr-theme="dark"] .mcr-layer-list__option--active {
  background: rgba(110, 162, 255, 0.16);
  color: #8db5ff;
  box-shadow: inset 3px 0 0 #0a84ff;
}

.mcr-floating-layer-list[data-mcr-theme="dark"] .mcr-layer-list__delete {
  color: #9ba8bf;
}

.mcr-floating-layer-list[data-mcr-theme="dark"] .mcr-layer-list__delete:hover {
  background: rgba(255, 133, 133, 0.14);
  color: #ff9d9d;
}

.mcr-layout-editor[data-mcr-theme="dark"] {
  --mcr-layer-button-foreground: #b9c8df;
}
</style>
