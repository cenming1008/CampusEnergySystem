# 3D 模型资源说明

本目录**用于存放**园区能源管理系统 3D 场景所需的模型文件。  
**当前仓库中未包含任何 .glb 模型文件**，园区总览页面由代码程序化生成几何体（见 `src/three/mine/MineSceneGenerator.ts`），因此观感偏「方块化」。若要使用真实 3D 建模图，需自行准备模型并放入本目录。

📌 **如何获取与接入矿区/工业 3D 模型**：见 [矿区总览 3D 资源说明](../../../docs/02-功能使用/矿区总览3D资源说明.md)（推荐渠道、格式要求、接入方式）。

---

## 📦 建议放置的模型（可选）

按需准备并放入本目录后，在 `CampusScene.vue` 或 `MineSceneGenerator` 中用 GLTFLoader 加载即可。

### 环境模型

- **mine_env.glb** - 矿区环境主场景（整体布局、地形、建筑）
  - 若有此文件，可在场景初始化时优先加载，替代或补充程序化场景

### 地面/墙体（可选）

- **floor*.glb** / **wall.glb** - 地面、墙体模型，用于替换或补充程序化地面/围墙

### 设备模型

- **Fighter.glb**、**Fighter1.glb** 或自定义设备 .glb
  - 代表风机、泵、配电柜等，可放在设备标记位置做实例化展示

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

## 🔄 更新说明

- 当前未包含实际模型文件；上述列表为**建议命名与用途**。  
- 添加模型后，需在 `CampusScene.vue` 或 `MineSceneGenerator` 中编写加载逻辑，详见 [矿区总览 3D 资源说明](../../../docs/02-功能使用/矿区总览3D资源说明.md)。

## 📐 模型规格建议

- **文件大小**: 单个模型建议 < 10MB（压缩后）
- **面数**: 场景模型 < 100K 面，设备模型 < 10K 面
- **纹理**: 使用 2K 或 4K 分辨率，根据重要性调整

## 🎯 未来计划

- [ ] 添加更多设备类型模型
- [ ] 优化现有模型文件大小
- [ ] 统一模型命名规范
- [ ] 添加模型预览图
