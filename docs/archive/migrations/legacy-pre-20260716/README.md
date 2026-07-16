# 20260716 之前的旧迁移链归档

这些 revision 仅用于历史追溯，已经移出 Alembic 活跃目录，不得再作为新数据库的建库路径。它们统一由静态根基线 `20260716_0001` 取代。

| Revision | 文件 | 原用途 | 已知问题 | 替代关系 |
| --- | --- | --- | --- | --- |
| `20260325_0001` | `20260325_0001_industrial_baseline.py` | 通过 ORM metadata 补建核心表和历史字段 | schema 依赖运行时模型且含在线数据库检查，无法确定性复现 | superseded by `20260716_0001` |
| `20260325_0002` | `20260325_0002_mqtt_retry_dead_letter.py` | 增加 MQTT 重试与死信字段 | 依赖在线列检查且 downgrade 不可执行 | superseded by `20260716_0001` |
| `20260412_0003` | `20260412_0003_add_reactive_power.py` | 增加通用能源数据无功功率字段 | offline SQL 会在 `fetchone()` 处失败 | superseded by `20260716_0001` |
| `20260412_0004` | `20260412_0004_add_svg_tables.py` | 建立 SVG 配置、遥测和资产档案表 | 依赖 information_schema 在线检查 | superseded by `20260716_0001` |
| `20260412_0005` | `20260412_0005_merge_svg_operations_profile.py` | 合并 SVG 配置到运维档案 | 混合数据搬迁和在线对象探测，不能离线生成 | superseded by `20260716_0001` |
| `20260414_0006` | `20260414_0006_unify_compensation_type_to_svg.py` | 保留补偿设备子类型迁移占位 | 空 revision 不提供有效 schema 契约 | superseded by `20260716_0001` |
| `20260414_0007` | `20260414_0007_add_device_subtype.py` | 增加设备子类型并迁移历史补偿设备 | 依赖在线 inspector 和历史数据更新 | superseded by `20260716_0001` |
| `20260423_0008` | `20260423_0008_drop_prediction.py` | 移除已下线预测表 | 依赖在线表检查且 downgrade 重建已废弃对象 | superseded by `20260716_0001` |
| `20260424_0009` | `20260424_0009_add_capacitor_bank_monitor_fields.py` | 增加电容补偿监控与参数字段 | 依赖在线表、列检查 | superseded by `20260716_0001` |
| `20260424_0010` | `20260424_0010_add_device_archive_status.py` | 增加设备档案完整状态 | 假设旧表存在，不可作为独立根迁移 | superseded by `20260716_0001` |
| `20260515_0011` | `20260515_0011_add_capacitor_bank_harmonic_spectrum.py` | 增加电容补偿谐波谱字段 | 依赖在线表、列检查 | superseded by `20260716_0001` |
