# GitHub Actions 远程部署说明

> 让 `deploy.yml` 从“只构建镜像”升级为“把当前版本真正发布到远端试点服务器”。

---

## 1. 工作流做了什么

部署工作流会执行两段动作：

- 先构建并推送后端镜像，保留镜像产物
- 再把当前仓库打成发布包，通过 SSH 上传到远端服务器，并调用 `scripts/shell/deploy_prod.sh`

这样既保留镜像产物，也真正执行远端部署。

---

## 2. 需要配置的 GitHub Environment Secrets

建议在 `staging` 和 `production` 两个 Environment 下分别配置同名 secret：

- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_SSH_PRIVATE_KEY`
- `ENV_PROD_FILE`

其中：

- `DEPLOY_HOST`：远端服务器地址
- `DEPLOY_USER`：远端部署用户
- `DEPLOY_SSH_PRIVATE_KEY`：用于 SSH 登录的私钥
- `ENV_PROD_FILE`：完整 `.env.prod` 内容，多行 secret

---

## 3. 可选 GitHub Environment Variables

- `DEPLOY_PORT`
- `DEPLOY_PATH`

默认值：

- `DEPLOY_PORT=22`
- `DEPLOY_PATH=/opt/mine-energy-system`

---

## 4. 远端主机要求

- 已安装 Docker 与 Docker Compose
- 部署用户对目标目录有写权限
- 部署用户可执行 Docker 命令
- 防火墙、证书、域名已预先准备

---

## 5. 建议流程

1. 先在 `staging` 环境执行手动发布。
2. 验证 `pilot_smoke_test.sh`、备份恢复和通知通道。
3. 再切换到 `production` 环境执行正式发布。

---

## 6. 注意事项

- `ENV_PROD_FILE` 建议直接粘贴 `.env.prod` 全量内容，不要拆分成多个 secret。
- 远端部署目录会按 Git SHA 生成 `releases/<sha>`，并更新 `current` 软链接。
- `deploy_prod.sh` 仍是最后执行入口，因此发布前检查、备份与健康检查逻辑保持一致。
