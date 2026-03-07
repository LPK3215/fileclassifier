# FileClassifier React 前端

这是 FileClassifier 的 Web 前端项目。

## 功能

- 支持以“文件或文件夹”加载 Excel（文件夹模式会自动列出可选文件）
- 自动读取 Sheet 元数据与预览
- 查询条件支持 AND/OR、范围弹窗
- 右侧预览表支持：
  - 固定列
  - 拖拽列宽
  - 排序
  - 列筛选
- 执行复制流程并查看日志结果

## 技术栈

- React 18
- Vite 5

## 当前前端结构

```text
fileclassifier-react-ui/
├─ src/
│  ├─ components/                 # 界面组件
│  ├─ hooks/                      # 状态逻辑（条件/表格/分栏）
│  ├─ lib/                        # API 调用与公共工具
│  ├─ App.jsx                     # 页面编排层
│  ├─ main.jsx
│  └─ styles.css
├─ package.json
└─ vite.config.js
```

## 安装依赖

```powershell
npm install
```

## 启动开发服务器

```powershell
npm run dev
```

默认地址：`http://127.0.0.1:5173`

已配置代理（`vite.config.js`）：

- `/api` -> `http://127.0.0.1:8000`

## 构建

```powershell
npm run build
```

## 部署文档

见 [`DEPLOYMENT.md`](DEPLOYMENT.md)。

