# Nginx 证书目录

生产环境请将真实证书文件放到本目录，并使用以下固定文件名：

- `fullchain.pem`
- `privkey.pem`

当前 Nginx 生产配置已默认读取：

- `/etc/nginx/ssl/fullchain.pem`
- `/etc/nginx/ssl/privkey.pem`

部署前请确认：

- 证书 CN / SAN 覆盖 `TRUSTED_HOSTS` 中使用的域名
- 私钥权限已收紧
- 证书链完整可被浏览器和网关设备信任
