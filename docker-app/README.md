# Yahaha Cover Studio Docker

独立 Docker 版媒体库封面生成器。它从当前 MoviePilot 插件的封面生成思路中拆出了一个不依赖 MoviePilot 的服务：

- 通过 Emby / Jellyfin API 获取媒体库、媒体项目、图片素材，并上传媒体库封面。
- 前端复用 MoviePilot 插件版 Vue / Vuetify 页面，并通过 Docker 兼容 API 适配运行。
- 支持使用本地 `data/input` 图片离线生成。
- 内置静态、动态和自定义画布兼容渲染，前端复用插件版 Vue 页面。
- 使用 `config.yaml` 管理服务器、标题映射和样式参数。
- 提供 Web API 和轻量 Web UI。

## 快速部署

```bash
cd /Users/liu/MoviePilot-Plugins/docker-app
cd frontend && npm ci && npm run build && cd ..
docker compose up -d --build
```

如果只是重启已构建镜像：

```bash
docker compose up -d --no-build
```

访问：

```text
http://localhost:8899
```

停止：

```bash
docker compose down
```

## 持久化目录

容器内固定数据目录为 `/app/data`，默认 compose 已挂载：

```yaml
volumes:
  - ./data/config.yaml:/app/data/config.yaml
  - ./data/fonts:/app/data/fonts
  - ./data/input:/app/data/input
  - ./data/output:/app/data/output
```

目录用途：

- `data/config.yaml`：应用配置。
- `data/fonts`：自定义字体目录，支持 `ttf` / `ttc` / `otf` 等 Pillow 可读取字体。
- `data/input`：本地图片素材。可直接放图片，也可按媒体库名建子目录。
- `data/output`：生成后的封面。

## 配置说明

默认配置位于 [data/config.yaml](/Users/liu/MoviePilot-Plugins/docker-app/data/config.yaml)。

```yaml
emby_url: "http://127.0.0.1:8096"
emby_api_key: "YOUR_EMBY_API_KEY"
jellyfin_url: ""
jellyfin_api_key: ""
mock_enabled: true
covers_input: /app/data/input
covers_output: /app/data/output
title_config:
  动漫:
    title: 动漫
    subtitle: Anime
    texts: {}
title_config_strict: false
style_config:
  style: single_1
  resolution: 1080p
  image_source: backdrop
  image_limit: 9
  background_color: "#6f8090"
  color_ratio: 0.78
  blur: 42
  font: ""
  main_font_size: 170
  subtitle_font_size: 76
  output_format: jpg
animation_duration: 8
animation_fps: 24
animation_format: apng
animation_resolution: 320x180
transfer_monitor: false
monitor_source: webhook
cron: ""
backup_cron: ""
backup_path: ""
api_token: "自动生成，建议不要留空"
```

字段说明：

- `emby_url` / `emby_api_key`：Emby 地址和 API Key。
- `jellyfin_url` / `jellyfin_api_key`：Jellyfin 地址和 API Key。
- `mock_enabled`：是否使用模拟媒体库。没有 Emby / Jellyfin 时建议设为 `true`。
- `covers_input`：本地素材目录，容器内建议保持 `/app/data/input`。
- `covers_output`：封面输出目录，容器内建议保持 `/app/data/output`。
- `title_config`：媒体库标题映射，键名必须和媒体库名称一致。
- `title_config_strict`：标题配置校验模式。`false` 为宽容模式，可兼容中文冒号、冒号后无空格和常见缩进错误；`true` 为标准 YAML 严格模式。
- `style_config.style`：`single_1`、`single_2`、`multi_1`、`static_4`、`custom_static` 或 `animated_1` ~ `animated_4`。
- `style_config.image_source`：`backdrop` 横图或 `poster` 竖图。
- `style_config.image_limit`：每个媒体库拉取图片数量。
- `style_config.font`：字体文件名或绝对路径。留空时自动使用容器内 Noto CJK / DejaVu 字体。
- `style_config.output_format`：`jpg` 或 `png`。
- `animation_format`：动态方案输出格式，支持 `apng` 或 `gif`。
- `animation_resolution`：动态方案固定分辨率，例如 `320x180`。
- `transfer_monitor` / `monitor_source`：开启媒体服务器 Webhook 入库监控时使用。Docker 版不依赖 MoviePilot，`monitor_source` 建议使用 `webhook`，也可填写 `emby` / `jellyfin` 作为提示。
- `cron`：5 位 cron 表达式，非空时 Docker 版会独立定时生成封面。
- `backup_cron`：5 位 cron 表达式，非空时 Docker 版会独立定时备份配置。
- `backup_path`：备份目录或 `.json/.yaml` 文件路径。相对路径会保存到 `/app/data` 下。
- `api_token`：Webhook Token。首次启动或配置为空时会自动生成随机字符串，Webhook 请求必须带 `?token=...`。

## Web API

- `GET /api/health`：健康检查。
- `GET /api/libraries`：获取 Emby / Jellyfin 媒体库列表。
- `POST /api/generate`：生成全部媒体库封面；未配置媒体服务器时使用本地 `data/input`。
- `POST /api/generate/{library_name}`：生成指定媒体库封面。
- `POST /api/upload/{library_name}`：上传最近生成的指定媒体库封面。
- `GET /api/config`：读取配置。
- `POST /api/config`：保存配置。
- `POST /api/webhook/`：接收 Emby / Jellyfin 新媒体 Webhook，并触发对应媒体库封面更新。兼容 JSON、`application/x-www-form-urlencoded` 和 `multipart/form-data`。
- `POST /api/v1/webhook`：旧兼容入口，建议新配置使用 `/api/webhook/`。
- `GET /api/webhook/example`：查看 Emby / Jellyfin Webhook 配置示例。

## 定时任务

Docker 版内置轻量调度器，不依赖 MoviePilot：

```yaml
cron: "0 4 * * *"          # 每天 04:00 生成封面
backup_cron: "30 4 * * *"  # 每天 04:30 备份配置
backup_path: "backups"     # 保存到 /app/data/backups
```

cron 使用 5 位格式：

```text
分钟 小时 日期 月份 星期
```

支持 `*`、`*/5`、`1,2,3`、`1-5` 这类常见写法。留空则关闭对应定时任务。

示例：

```bash
curl http://localhost:8899/api/health
curl -X POST http://localhost:8899/api/generate/动漫 -H 'Content-Type: application/json' -d '{"style":"multi_1"}'
curl -X POST http://localhost:8899/api/generate -H 'Content-Type: application/json' -d '{"library_name":"动漫","style":"animated_1"}'
```

## Emby / Jellyfin Webhook

Docker 版不依赖 MoviePilot 事件系统，可以直接接收媒体服务器 Webhook。推荐地址：

```text
http://你的Docker宿主机:8899/api/webhook/?token=YAHAAHA_WEBHOOK_TOKEN&source=emby
```

配置建议：

- `transfer_monitor: true`
- `monitor_source: webhook`
- `delay: 60` 可按媒体服务器扫描速度调整
- `lock_latest_sort: true` 时会自动使用最新入库排序
- `api_token` 会自动生成，必须和 URL 上的 `token` 一致

如果你通过反向代理访问 Docker 版，可以使用相对路径：

```text
/api/webhook/?token=YAHAAHA_WEBHOOK_TOKEN&source=媒体服务器名
```

`source` 必填，用于判断通知来自哪个媒体服务器；建议填写媒体服务器卡片名称，没有自定义名称时可使用 `emby` 或 `jellyfin`。

Emby 通知里勾选「媒体库 -> 新媒体已添加」。Emby 通知可选择 JSON 或 form-data；Docker 版都兼容。推荐 JSON 内容：

```json
{
  "Event": "library.new",
  "ServerName": "{{ServerName}}",
  "Item": {
    "Id": "{{ItemId}}",
    "Name": "{{Name}}",
    "LibraryId": "{{LibraryId}}",
    "LibraryName": "{{LibraryName}}",
    "Path": "{{Path}}"
  }
}
```

Jellyfin 通常需要安装 Webhook 插件，然后选择 Item Added / Item Created 事件。推荐 JSON 内容：

```json
{
  "NotificationType": "ItemAdded",
  "ServerName": "{{ServerName}}",
  "ItemId": "{{ItemId}}",
  "ItemName": "{{Name}}",
  "LibraryId": "{{LibraryId}}",
  "LibraryName": "{{LibraryName}}",
  "Path": "{{Path}}"
}
```

Docker 版会尽量从 Webhook payload 中读取 `Item.LibraryName`、`Item.LibraryId`、`Item.Path`、`ItemId` 等字段定位媒体库；如果只收到 `ItemId`，会再查询媒体服务器反查所属媒体库。定位成功后会在后台生成并上传该媒体库封面。

## 从 MoviePilot 插件迁移

1. 保留原 MoviePilot 插件目录，不需要移动或删除任何插件文件。
2. 把原插件里的标题配置迁移到 `docker-app/data/config.yaml` 的 `title_config`：

```yaml
title_config:
  音乐:
    title: 音乐
    subtitle: Music
    texts:
      note: 随便听
```

3. 把自定义字体复制到 `docker-app/data/fonts`，然后在 `style_config.font` 中填写字体文件名。
4. 如果你使用自定义图片目录，可将图片复制到 `docker-app/data/input`：

```text
data/input/
  动漫/
    01.jpg
    02.jpg
  音乐/
    01.jpg
```

5. 原插件中的风格可按下面方式先迁移：

- 风格 1：`single_1`
- 风格 2：`single_2`
- 风格 3：`multi_1`
- 风格 4：`static_4`
- 动态风格：`animated_1` ~ `animated_4`
- 自定义静态画布：通过前端方案列表导入/编辑，保存后写入 `custom_static_layout` / `custom_static_layouts`

当前 Docker 版已经复用插件版 Vue UI，并提供自定义画布、贴图、字体、备份、历史封面和动态方案的独立兼容接口；少数复杂动画细节仍是轻量实现，会继续向插件版靠拢。

## 常见问题

### 没有媒体库

检查 `emby_url` / `emby_api_key` 或 `jellyfin_url` / `jellyfin_api_key` 是否保存成功，并确认容器能访问媒体服务器地址。

如果媒体服务器在宿主机上，Docker Desktop 通常可使用：

```text
http://host.docker.internal:8096
```

### 中文标题显示异常

镜像内已安装 `fonts-noto-cjk`。如果你想使用自己的字体，将字体放到 `data/fonts`，并在 `style_config.font` 填写字体文件名。

### 上传封面失败

确认 API Key 有修改媒体库图片的权限。也可以先只生成封面，在 `data/output` 中确认图片正常。

Docker 版会按输出文件扩展名上传正确的 `Content-Type`：

- `.jpg` / `.jpeg` -> `image/jpeg`
- `.png` / APNG -> `image/png`
- `.gif` -> `image/gif`
- `.webp` -> `image/webp`

如果媒体服务器不接受动图作为媒体库封面，可将动态方案格式改为 `gif` 或切回静态方案后上传。

### Mock 模式怎么用

可以。默认 `mock_enabled: true`，无需连接 Emby / Jellyfin，也会返回模拟媒体库并自动生成测试素材。调用：

```bash
curl http://localhost:8899/api/libraries
curl -X POST http://localhost:8899/api/generate -H 'Content-Type: application/json' -d '{}'
```

切换真实 Emby / Jellyfin 时，把 `mock_enabled` 改成 `false`，并填写对应服务器 URL 和 API Key。

### 清理缓存会删除什么

设置页的「清理图片缓存」只清理 Docker 数据目录内可重建的图片缓存和输出封面：

- 默认 `/app/data/input`：Emby / Jellyfin 预览素材缓存、mock 素材缓存。
- `/app/data/output`：生成结果缓存。

如果 `covers_input` 指向自定义图片目录，Docker 版会跳过该目录，避免误删用户素材。

「清理字体缓存」会清理 `/app/data/fonts` 中上传或下载的字体文件，并保留目录占位文件。

### 和 MoviePilot 插件是否互相影响

不会。该项目只新增 `docker-app/` 目录，不修改现有 MoviePilot 插件运行链路。
