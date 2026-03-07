# FileClassifier Python 后端

这是 FileClassifier 的后端项目，负责 Excel 查询预览、条件过滤、文件匹配与复制执行。

## 技术栈

- Python 3.10+
- FastAPI + Uvicorn
- pandas + openpyxl
- pytest + ruff

## 当前后端结构

```text
fileclassifier-python-api/
├─ src/fileclassifier/
│  ├─ services/                    # 业务逻辑（workflow/query/matcher/excel）
│  └─ webapi/
│     ├─ app.py                    # API 路由组装
│     ├─ schemas.py                # 请求/响应模型
│     └─ utils/
│        ├─ pathing.py             # 路径解析、Excel 文件扫描
│        ├─ system_io.py           # 系统目录/文件选择与打开
│        └─ serialization.py       # 数据序列化与条件转换
├─ tests/
├─ DEPLOYMENT.md
├─ start_web.py
└─ start_desktop.py
```

## 主要接口

- `GET /api/health`
- `GET /api/excel/files`
- `POST /api/excel/metadata`
- `POST /api/excel/preview`
- `POST /api/query/filter-preview`
- `POST /api/workflow/execute`
- `POST /api/system/pick-excel-file`（Excel 文件选择）
- `POST /api/system/pick-excel-source`（文件/文件夹统一选择）
- `POST /api/system/pick-directory`
- `POST /api/system/open-folder`

## 本地启动（Windows）

```powershell
python .\start_web.py
```

`start_web.py` 内已预置启动参数（`APP_HOST`、`APP_PORT`、`APP_RELOAD`、`APP_WORKERS`）。

默认健康检查地址：

- `http://127.0.0.1:8000/api/health`

桌面单端口模式：

```powershell
python .\start_desktop.py
```

桌面访问地址：

- `http://127.0.0.1:18080`

## 验证命令

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests scripts start_web.py start_desktop.py
```

## 部署文档

部署步骤见 [`DEPLOYMENT.md`](DEPLOYMENT.md)。
