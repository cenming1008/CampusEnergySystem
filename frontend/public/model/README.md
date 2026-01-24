# 3D 模型资源说明

本目录包含矿区能源管理系统使用的 3D 模型文件。

## 📦 模型列表

### 环境模型

- **mine_env.glb** - 矿区环境主场景模型
  - 包含矿区整体布局、地形、建筑等
  - 用于 MineScene 3D 场景展示

### 地面模型

- **floor1.glb** - 地面模型版本 1
- **floor2.glb** - 地面模型版本 2
- **floor21.glb** - 地面模型版本 2.1
  - 用于场景地面渲染
  - 可根据需要选择不同版本

### 墙体模型

- **wall.glb** - 墙体模型
  - 用于场景边界或建筑墙体渲染

### 设备模型

- **Fighter.glb** - 设备模型版本 1
- **Fighter1.glb** - 设备模型版本 2
  - 代表矿区中的能源设备、监控设备等
  - 可用于设备位置可视化

## 🎨 模型格式

- **格式**: glTF 2.0 Binary (.glb)
- **压缩**: 支持 Draco 压缩（需要 `/draco` 目录下的解码器）
- **纹理**: 嵌入式纹理

## 🔧 使用方式

在 Three.js 中加载模型：

```typescript
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader'

// 设置 Draco 解码器
const dracoLoader = new DRACOLoader()
dracoLoader.setDecoderPath('/draco/gltf/')

// 创建 glTF 加载器
const gltfLoader = new GLTFLoader()
gltfLoader.setDRACOLoader(dracoLoader)

// 加载模型
gltfLoader.load('/model/mine_env.glb', (gltf) => {
  scene.add(gltf.scene)
})
```

## 📝 注意事项

1. **模型优化**
   - 建议使用 Draco 压缩减小文件大小
   - 合理使用纹理分辨率
   - 控制模型面数

2. **版本管理**
   - 同一类型的多个版本（如 Fighter/Fighter1）用于 A/B 测试或渐进式升级
   - floor1/floor2/floor21 代表不同的地面设计方案

3. **性能优化**
   - 使用 `useLoader` 或懒加载方式加载大模型
   - 考虑使用 LOD（细节层次）技术
   - 及时清理不使用的模型资源

## 🔄 更新日志

- 2026-01-24: 初始模型集合
  - 添加 mine_env 矿区环境模型
  - 添加 floor 系列地面模型
  - 添加 Fighter 系列设备模型
  - 添加 wall 墙体模型

## 📐 模型规格建议

- **文件大小**: 单个模型建议 < 10MB（压缩后）
- **面数**: 场景模型 < 100K 面，设备模型 < 10K 面
- **纹理**: 使用 2K 或 4K 分辨率，根据重要性调整

## 🎯 未来计划

- [ ] 添加更多设备类型模型
- [ ] 优化现有模型文件大小
- [ ] 统一模型命名规范
- [ ] 添加模型预览图
