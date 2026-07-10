# 呀哈哈封面工坊 / Yahaha Cover Studio

Yahaha Cover Studio 是新版媒体库封面生成工具，用于为 Emby / Jellyfin 媒体库生成静态或动态封面。新版在原「媒体库封面生成 / Media Cover Generator」基础上重做了 Vue 前端、可编辑画布、方案管理、历史封面和入库 Webhook 监控。

Designed by Yahaha Design.

## 版本说明

- 新版插件：`plugins.v2/yahahacoverstudio`
- 旧版插件：`plugins.v2/mediacovergenerator`
- 旧版留档分支：`legacy-media-cover-generator`
- 旧版留档 tag：`v1-legacy-media-cover-generator`
- 新版首次发布 tag：`v2.0.0`

旧版「媒体库封面生成 / Media Cover Generator」不会被删除；需要旧版时可切换到留档分支或 tag。

## MoviePilot 插件版

新版插件 ID 为 `YahahaCoverStudio`，配置前缀为 `yahaha_cover_studio_`，避免与旧版 `MediaCoverGenerator` 冲突。

主要能力：

- 静态封面与动态封面生成
- 可编辑静态布局方案
- 自定义方案导入、导出、删除和重命名
- 自定义贴图、字体、标题映射
- 历史封面浏览、下载和删除
- Emby / Jellyfin 媒体库素材读取
- Webhook 入库监控
- 配置备份与还原

前端构建目录：

```bash
cd mcg_frontend
npm install
npm run build
```

构建产物会输出到：

```text
plugins.v2/yahahacoverstudio/dist
```

## Docker 独立版

仓库中保留了独立 Docker 项目：

```bash
cd docker-app
docker compose up -d --build
```

默认访问地址：

```text
http://localhost:8899
```

Docker 版不依赖 MoviePilot，配置文件与数据目录位于：

```text
docker-app/data/
```

从 MoviePilot 插件迁移时，可参考 Docker 版 README，将标题映射、字体、贴图和输出目录迁移到 `docker-app/data`。

## Webhook

独立版建议使用：

```text
/api/webhook/?token=YAHAAHA_WEBHOOK_TOKEN&source=媒体服务器名
```

MoviePilot 插件版可在设置页配置 Webhook token 和媒体服务器来源。Emby 需要在通知中勾选「媒体库 -> 新媒体已添加」。不同媒体服务器可能发送 JSON、form-data 或表单字段，Yahaha Cover Studio 会尽量兼容常见格式。

## 发布分支策略

推荐结构：

- `main`：新版「呀哈哈封面工坊 / Yahaha Cover Studio」
- `legacy-media-cover-generator`：旧版「媒体库封面生成 / Media Cover Generator」
- `v1-legacy-media-cover-generator`：旧版留档 tag
- `v2.0.0`：新版首次发布 tag

本地整理完成后再推送：

```bash
git push origin legacy-media-cover-generator
git push origin yahaha-cover-studio
git push origin v1-legacy-media-cover-generator
git push origin v2.0.0
```

如需让新版成为默认分支，请先在 GitHub 上确认分支和 tag 均已备份，再合并或更新 `main`。
