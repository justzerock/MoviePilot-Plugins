# Changelog

## v2.0.6

- 修复 Docker 与插件版的封面素材缓存刷新，强制重新获取服务器图片。
- 清理图片缓存不再误删已生成封面与历史记录。

## v2.0.1

- 新增按生成批次浏览与恢复服务器封面的“时光机”。
- 精简历史封面配置，统一为所有批次保留上限。
- 优化标题配置工具栏、设置页阴影和浮动分组导航。

## v2.0.0

- 更名为「呀哈哈封面工坊 / Yahaha Cover Studio」。
- 新增独立插件 ID `YahahaCoverStudio`，避免与旧版 `MediaCoverGenerator` 冲突。
- 新增 Vue 3 + Vite module-federation 前端。
- 新增静态方案编辑、方案导入导出、历史封面、贴图、字体库、标题映射和备份还原能力。
- 新增 Webhook 入库监控与 Docker 独立版。
- 旧版「媒体库封面生成 / Media Cover Generator」已保留在 `legacy-media-cover-generator` 分支和 `v1-legacy-media-cover-generator` tag。

## v1 legacy

- 旧版插件名称：媒体库封面生成 / Media Cover Generator。
- 旧版插件 ID：`MediaCoverGenerator`。
- 旧版目录：`plugins.v2/mediacovergenerator`。
