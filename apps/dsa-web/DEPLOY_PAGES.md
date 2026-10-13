# Web UI 的 GitHub Pages 构建说明

这个目录产出的是**纯静态**前端。GitHub Pages 只能托管静态文件,
因此这里发布的是界面本身,不含 Python 后端。

## 构建命令(与 `.github/workflows/deploy-pages.yml` 完全一致)

```bash
cd apps/dsa-web
npm ci
npm run build -- --base=./ --outDir=../../pages-dist
cp pages-dist/index.html pages-dist/404.html   # SPA 深链接回退
touch pages-dist/.nojekyll                      # 关闭 Jekyll 处理
```

## 两个关键点

1. **`--base=./` 必须保留**。默认 `base: '/'` 会生成绝对路径 `/assets/...`,
   发布到 `https://<user>.github.io/<repo>/` 这类子路径下会 404。
2. **后端地址**。前端读取构建期变量 `VITE_API_URL`:
   - 留空 = 同源请求(仅在同域有后端时可用)
   - 指向自建后端 = Pages 静态界面 + 远程 API

   设置位置:仓库 `Settings → Secrets and variables → Actions → Variables`。

## 本地预览产物

```bash
cd pages-dist
python -m http.server 8080
# 浏览器打开 http://127.0.0.1:8080/
```
