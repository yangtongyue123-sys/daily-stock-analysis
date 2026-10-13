# 部署到 GitHub 云端(GitHub Pages)

## 0. 先说清楚一个硬限制

**GitHub Pages 只能托管静态文件(HTML/CSS/JS/JSON),不能运行 Python。**

这个项目 = React 前端(可静态化) + Python 分析后端(FastAPI + 数据抓取 + AI 分析 + SQLite),两者缺一不可。

所以本方案能部署的是:

| 能部到 Pages | 不能部到 Pages |
| --- | --- |
| `static/` 里的整套 Web 界面(50 文件 / 5.48MB) | `main.py` / `server.py`(Python 后端) |
| 股票代码自动补全索引 `stocks.index.json` | 行情抓取、AI 分析、SQLite 数据库 |
| 页面路由、主题、图表组件 | 任何 `/api/*` 接口 |

**实际效果**:Pages 上的界面能正常打开、能点,但因为拿不到 `/api/*` 数据,列表/报告会是空的,并提示接口请求失败。

> 如果你要的是「云端能真正算数据 + 推买卖信号」,那要走的不是 Pages,而是本项目自带的
> `.github/workflows/00-daily-analysis.yml`(在 GitHub 的服务器上跑分析并推送通知,免服务器)。
> 见本文第 6 节。

---

## 1. 已为你生成/改好的文件

| 文件 | 作用 |
| --- | --- |
| `.github/workflows/deploy-pages.yml` | **新增**。构建前端并发布到 GitHub Pages(已按子路径 `--base=./` 构建,含 SPA 404 回退) |
| `.gitignore` | 已存在,已忽略 `.env` / `data/` / `logs/` / `reports/` / `static/`,**不会把密钥和数据提交上去** |

发布策略说明:`deploy-pages.yml` 在 GitHub 的 runner 上执行 `npm ci` + `npm run build`,
产物输出到 `pages-dist/`,再由 `actions/deploy-pages` 发布。**本地不需要跑任何分析或回测。**

---

## 2. 前置条件(需要你自己完成的部分)

| 项 | 说明 |
| --- | --- |
| Git | **本机当前未安装 git**,需先安装(见下) |
| GitHub 账号 | 你自己的账号 |
| 一个空仓库 | 在 GitHub 网页上新建,例如 `daily-stock-analysis`,**不要**勾选 Add README |

安装 Git(任选一种):

```powershell
# 方式一:winget(Windows 10/11 自带)
winget install --id Git.Git -e --source winget

# 方式二:官网下载安装
# https://git-scm.com/download/win
```

装完**重开终端**验证:

```powershell
git --version
```

---

## 3. 完整部署命令

在项目根目录执行(把 `<你的用户名>` 和 `<仓库名>` 换成你自己的):

```powershell
cd E:\Work\Codex\DataAnalysis\daily_stock_analysis

# 3.1 初始化本地仓库并提交
git init
git add .
git commit -m "Deploy web UI to GitHub Pages"
git branch -M main

# 3.2 关联远程仓库
git remote add origin https://github.com/<你的用户名>/<仓库名>.git

# 3.3 推送(首次需要登录/授权,GitHub 现在用浏览器授权或 Personal Access Token)
git push -u origin main
```

> ⚠️ 如果 `git add .` 之后 `git status` 里看到了 `.env`,说明它没被忽略,**不要提交**。

---

## 4. 打开 GitHub Pages

1. 打开 `https://github.com/<你的用户名>/<仓库名>`
2. **Settings → Pages**
3. **Source** 选 **GitHub Actions**(不要选 Deploy from a branch)
4. 打开 **Actions** 标签,等 `Deploy Web UI to GitHub Pages` 跑完(约 2~4 分钟)
5. 在 Pages 页面顶部会显示访问地址

---

## 5. 访问链接

```
https://<你的用户名>.github.io/<仓库名>/
```

例如用户名 `zhangsan`、仓库 `daily-stock-analysis`:

```
https://zhangsan.github.io/daily-stock-analysis/
```

---

## 6. (可选)让界面真的有数据

Pages 上没有后端,界面会是空的。两条路:

### 路线 A:给前端指一个已部署好的后端

如果你在别的机器/云服务器上跑着本项目后端(`python main.py --serve-only`),
在 GitHub 仓库 **Settings → Secrets and variables → Actions → Variables** 新建:

| Name | Value |
| --- | --- |
| `VITE_API_URL` | 你的后端地址,例如 `https://api.example.com` |

然后重跑 Pages 工作流即可。**这只填一个网址,不是密钥。**

### 路线 B(推荐):用 GitHub Actions 每天在云端算,推送到你手机

本项目自带 `.github/workflows/00-daily-analysis.yml`,它可以在 GitHub 的服务器上
跑完整分析并把买卖信号推送出去,**完全不需要服务器,也不需要打开本机**。

启用前的两件事(都需要你自己在 GitHub 网页上手动添加,**我不索取任何密钥**):

1. **模型渠道** —— Settings → Secrets and variables → Actions → New repository secret
   你的 DeepSeek key 对应 secret 名:`DEEPSEEK_API_KEY`
2. **推送渠道**(至少一个)—— 同页面添加,例如企业微信:`WECHAT_WEBHOOK_URL`

加好后:Actions → `每日股票分析` → Run workflow。
自选股可通过仓库 Secret `STOCK_LIST`(如 `600519,300750`)设置。

> 具体 secret 名称清单见 `docs/DEPLOY.md` 的 "GitHub Actions 部署" 一节。
