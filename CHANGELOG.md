# Changelog

## v2.0.10

- 修复双端预览素材缓存：重开页面复用已下载素材，手动刷新才重新获取媒体服务器海报。
- 修复 Docker 选择媒体库时因内部 `服务器:ID` 值造成缓存失效的问题，并提高插件端刷新稳定性。

## v2.0.9

- 修复 Docker 版刷新成功后仍被错误提示为失败的问题。

## v2.0.8

- 优化 Emby/Jellyfin 预览素材刷新：直接请求服务端缩略规格、复用连接并受控并发下载，减少大图传输与插件端等待。

## v2.0.7

- 修复插件强制刷新后媒体服务器海报出现浏览器破图的问题。
- 统一 Docker 与插件版的刷新结果提示，仅在本次请求真正失败时显示失败状态。

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
