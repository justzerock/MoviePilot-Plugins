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

Docker 版不依赖 MoviePilot，可直接运行独立 Web UI。

使用 Docker Hub 镜像：

```bash
mkdir -p yahaha-cover-studio/data/{fonts,input,output}
touch yahaha-cover-studio/data/config.yaml
docker run -d \
  --name yahaha-cover-studio \
  -p 8899:8080 \
  -v "$PWD/yahaha-cover-studio/data/config.yaml:/app/data/config.yaml" \
  -v "$PWD/yahaha-cover-studio/data/fonts:/app/data/fonts" \
  -v "$PWD/yahaha-cover-studio/data/input:/app/data/input" \
  -v "$PWD/yahaha-cover-studio/data/output:/app/data/output" \
  --restart unless-stopped \
  justzerock/yahaha-cover-studio:latest
```

使用 Docker Compose：

```yaml
services:
  yahaha-cover-studio:
    image: justzerock/yahaha-cover-studio:latest
    container_name: yahaha-cover-studio
    ports:
      - "8899:8080"
    volumes:
      - ./data/config.yaml:/app/data/config.yaml
      - ./data/fonts:/app/data/fonts
      - ./data/input:/app/data/input
      - ./data/output:/app/data/output
    restart: unless-stopped
```

默认访问地址：

```text
http://localhost:8899
```

也可以使用 GHCR 镜像：

```text
ghcr.io/justzerock/yahaha-cover-studio:latest
```

完整部署说明见 [docker-app/README.md](/Users/liu/MoviePilot-Plugins/docker-app/README.md)。从 MoviePilot 插件迁移时，可参考 Docker 版 README，将标题映射、字体、贴图和输出目录迁移到 `docker-app/data`。

## Webhook

独立版建议使用：

```text
/api/webhook/?token=YAHAAHA_WEBHOOK_TOKEN&source=媒体服务器名
```

MoviePilot 插件版可在设置页配置 Webhook token 和媒体服务器来源。Emby 需要在通知中勾选「媒体库 -> 新媒体已添加」。不同媒体服务器可能发送 JSON、form-data 或表单字段，Yahaha Cover Studio 会尽量兼容常见格式。
