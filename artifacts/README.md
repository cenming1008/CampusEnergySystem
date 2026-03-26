# artifacts 目录说明

该目录用于存放不应直接写入源码目录的验收产物与运行证据。

## 推荐子目录

- `artifacts/pilot/`：试点 readiness、发布演练、恢复演练证据
- `artifacts/load/`：压测原始报告和基线判定结果

## 建议做法

- 每次试点演练使用独立时间戳目录
- 原始 JSON 与 Markdown 结论同时保留
- 不要把敏感 `.env.prod`、私钥或备份明文放进该目录
