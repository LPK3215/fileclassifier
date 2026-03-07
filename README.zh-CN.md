# FileClassifier 仓库说明

本仓库当前主线由两个项目组成：

- `fileclassifier-python-api`：后端 API 与核心匹配逻辑（Python/FastAPI）
- `fileclassifier-react-ui`：前端页面（React/Vite）

旧桌面端代码已归档到 `legacy/desktop-pyside6/`，不参与当前 Web 主流程。

## 目录结构

```text
.
├─ fileclassifier-python-api/
│  ├─ src/fileclassifier/
│  │  ├─ services/
│  │  └─ webapi/
│  │     ├─ app.py
│  │     ├─ schemas.py
│  │     └─ utils/
│  ├─ tests/
│  ├─ DEPLOYMENT.md
│  └─ README.md
├─ fileclassifier-react-ui/
│  ├─ src/
│  │  ├─ components/
│  │  ├─ hooks/
│  │  └─ lib/
│  ├─ DEPLOYMENT.md
│  └─ README.md
├─ scripts/
│  ├─ run_web_backend.ps1
│  ├─ run_web_frontend.ps1
│  ├─ run_desktop_backend.ps1
│  ├─ package_windows_desktop.ps1
│  └─ package_windows_desktop.config.json
├─ start_web.ps1
├─ stop_web.ps1
└─ start_desktop.ps1
```

## 快速启动（Windows）

在仓库根目录执行：

```powershell
.\start_web.ps1
```

关闭 `start_web.ps1` 拉起的前后端：

```powershell
.\stop_web.ps1
```

默认地址：

- 后端健康检查：`http://127.0.0.1:8000/api/health`
- 前端页面：`http://127.0.0.1:5173`

## 桌面模式（Windows）

单端口桌面启动（后端 + 已构建前端）：

```powershell
.\start_desktop.ps1
```

默认访问地址：

- `http://127.0.0.1:18080`

桌面运行时默认数据/日志目录：

- 优先：`<EXE目录>\workspace\{excel,input,output,logs}`
- 若 EXE 目录不可写：`%LOCALAPPDATA%\FileClassifier\workspace\{excel,input,output,logs}`
- 每次执行仍会在 `output` 下自动创建“按筛选条件命名”的子文件夹。

桌面配置文件（可选）：

- 路径：放在 EXE 同级目录，文件名 `fileclassifier.desktop.json`
- 作用：无需重新打包即可修改端口/主机/自动打开浏览器/运行目录
- 优先级：环境变量会覆盖配置文件
- 打包脚本会在 EXE 同级自动放置 `fileclassifier.desktop.json` 与 `fileclassifier.desktop.example.json`

## 打包 Windows 可执行文件

构建可双击运行的桌面可执行文件（默认 `onefile`）：

```powershell
.\scripts\package_windows_desktop.ps1
```

默认打包 UI 模式为 `console`（会显示一个可见黑框窗口，用于管理本地后端进程）。

可选模式：

```powershell
.\scripts\package_windows_desktop.ps1 -Mode onedir
```

可选 UI 模式：

```powershell
.\scripts\package_windows_desktop.ps1 -UiMode windowed
```

打包配置单一来源：

- `scripts/package_windows_desktop.config.json`
- 该文件集中维护打包参数和桌面配置模板
- `scripts/package_windows_desktop.ps1` 会逐条打印实际执行命令，方便审计

输出路径：

- `dist-windows\FileClassifierWeb.exe`（`onefile`）
- `dist-windows\FileClassifierWeb\FileClassifierWeb.exe`（`onedir`）

## 子项目文档

- 后端说明：[`fileclassifier-python-api/README.md`](fileclassifier-python-api/README.md)
- 后端部署：[`fileclassifier-python-api/DEPLOYMENT.md`](fileclassifier-python-api/DEPLOYMENT.md)
- 前端说明：[`fileclassifier-react-ui/README.md`](fileclassifier-react-ui/README.md)
- 前端部署：[`fileclassifier-react-ui/DEPLOYMENT.md`](fileclassifier-react-ui/DEPLOYMENT.md)
