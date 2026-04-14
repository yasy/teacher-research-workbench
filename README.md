# Teacher Research Workbench

面向中国教师科研训练与写作加速场景的 AIGC 科研写作工作台。

## 系统定位

- 不是一键代写平台
- 是“选题 -> 文献 -> 写作 -> 润色导出”的人机协同工作台
- 适用于中小学教师、职业院校教师、本科高校教师
- 当前版本以本地运行和最小闭环为主，不引入数据库和 SaaS 多租户设计

## 当前主流程

1. 选题助手  
   生成 TopicCard，确定正式选题。
2. 文献工作台  
   上传 PDF，做本地预处理，再进行 AI 文献分析。
3. 写作工作台  
   先确定写作依据，再补充材料，再按论文部分逐块搭建。
4. 润色与导出  
   对整篇项目中的各模块内容做优化，并导出 Markdown / DOCX。
5. 设置  
   在页面内直接配置模型 Provider、Base URL、Model、API Key，并管理项目保存/加载。

## 运行前准备

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

如果你在命令行里遇到 `streamlit: command not found`，通常是因为当前 Python 虚拟环境没有激活。  
Windows PowerShell 例如：

```powershell
.venv\Scripts\Activate.ps1
streamlit run app.py
```

WSL / bash 例如：

```bash
source .venv/bin/activate
streamlit run app.py
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，至少填写以下字段：

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=
LLM_API_KEY=your_api_key_here
LLM_MODEL=your_model_name_here
```

也可以在系统启动后直接到“设置”页面里填写并保存。

## 当前支持的模型配置方式

### 方式 A：设置页直接配置

在“设置”页面中可以直接：

- 选择模型服务商
- 填写或修改 Base URL
- 选择或填写模型名称
- 填写 API Key
- 保存后立即在当前进程中生效

当前内置支持的 Provider：

- `openai_compatible`
- `siliconflow`
- `groq`

### 方式 B：手动编辑 `.env`

常见示例：

```env
LLM_PROVIDER=siliconflow
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_API_KEY=your_siliconflow_key
LLM_MODEL=Qwen/Qwen2.5-72B-Instruct
```

```env
LLM_PROVIDER=groq
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=your_groq_key
LLM_MODEL=llama-3.3-70b-versatile
```

## 环境变量说明

- `LLM_PROVIDER`：当前支持 `openai_compatible`、`siliconflow`、`groq`
- `LLM_BASE_URL`：OpenAI-compatible 接口地址
- `LLM_API_KEY`：模型平台 API Key
- `LLM_MODEL`：模型名称
- `UPLOADS_DIR`：上传文件目录，默认 `data/uploads`
- `OUTPUTS_DIR`：导出文件目录，默认 `data/outputs`
- `CACHE_DIR`：缓存目录，默认 `data/cache`

## 文献处理说明

- 浏览器上传现在支持一次多选多个 PDF
- Windows 文件选择框中可使用 `Ctrl` / `Shift` 一次选择多篇
- 若浏览器上传出现红色 `400`，可改用“本地路径加入”
- 系统会优先做本地 PDF 预处理，再进入 AI 分析
- 对中文论文会优先尝试 `PyMuPDF` 提取，尽量避免 `PyPDF2` 乱码结果

## 写作工作台说明

写作工作台不是一次性吐全文，而是按论文编写 SOP 搭建：

1. 确定本次写作依据
2. 补充本次写作材料
3. 选择本次要写的论文部分
4. 生成并编辑这一部分
5. 查看整篇论文进度

系统会把每个已生成部分保存到 `writing_assets`，后续润色与导出读取的是整篇项目，而不是最后一次生成结果。

## 启动方式

```bash
streamlit run app.py
```

默认入口：

- `app.py`

## Docker

构建镜像：

```bash
docker build -t teacher-research-workbench .
```

运行：

```bash
docker compose up --build
```

默认暴露 `8501` 端口，并挂载本地 `data/` 目录保存上传和导出文件。

## 发布前自检建议

发布前至少检查以下项目：

1. 设置页能成功保存 Provider / Model / API Key
2. 文献工作台可一次多选多个 PDF
3. 中文论文不会明显落回 `basic_python` 乱码链路
4. 写作工作台五阶段可顺序走通
5. 润色与导出能看到整篇项目模块，而不是单模块

## GitHub 开源发布建议

建议直接把当前项目目录整理为 GitHub 仓库，不要再额外维护一份“手工同步目录”。

### 首次发布前

1. 确认 `.gitignore` 已生效，避免提交以下本地内容：
   - `.env`
   - `data/uploads/`
   - `data/outputs/`
   - `data/cache/`
   - `data/projects/`
2. 再次确认仓库中没有真实 API Key。
3. 保留 `.env.example` 作为用户配置模板。
4. 保留 `LICENSE`、`CONTRIBUTING.md`、`SECURITY.md` 作为开源协作基础文件。

### 用户首次使用

用户必须使用**自己的** API Key。

可选两种方式：

1. 复制 `.env.example` 为 `.env` 后自行填写
2. 启动系统后，在“设置”页面中填写自己的：
   - Provider
   - Base URL
   - Model
   - API Key

### 推送到 GitHub

```bash
git init
git add .
git commit -m "Initial open-source release"
git branch -M main
git remote add origin https://github.com/<your-name>/<repo-name>.git
git push -u origin main
```

### 后续版本同步

以后直接在这个 GitHub 仓库目录中继续开发，不需要再新建一个同步文件夹。

每次更新后执行：

```bash
git status
git add .
git commit -m "Describe your change"
git push
```
