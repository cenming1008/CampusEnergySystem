# 纹理资源说明

本目录包含 3D 场景使用的纹理和环境贴图。

## 📦 资源列表

### HDR 环境贴图

- **023.hdr** - HDR 环境贴图 1
- **2k.hdr** - 2K 分辨率 HDR 环境贴图

## 🎨 用途说明

### HDR 环境贴图

HDR (High Dynamic Range) 环境贴图用于实现基于物理的真实光照效果：

- **环境光照**: 为场景提供全局光照
- **反射效果**: 金属和玻璃材质的环境反射
- **背景天空**: 可选用作场景背景

## 🔧 使用方式

在 Three.js 中使用 HDR 环境贴图：

```typescript
import { RGBELoader } from 'three/examples/jsm/loaders/RGBELoader'

// 加载 HDR 环境贴图
const rgbeLoader = new RGBELoader()
rgbeLoader.load('/textures/2k.hdr', (texture) => {
  texture.mapping = THREE.EquirectangularReflectionMapping
  
  // 设置场景环境
  scene.environment = texture
  // 可选：设置场景背景
  scene.background = texture
})
```

## 📝 文件格式

- **格式**: HDR (Radiance RGBE)
- **映射**: 等距柱状投影 (Equirectangular)
- **用途**: PBR 材质环境光照

## 🎯 选择建议

### 023.hdr
- 适用于需要特定光照效果的场景
- 根据场景需求选择

### 2k.hdr
- 2K 分辨率（2048x1024）
- 平衡画质和性能
- 推荐用于大多数场景

## 🔄 性能优化

1. **分辨率选择**
   - 桌面端: 2K-4K
   - 移动端: 1K-2K
   
2. **加载优化**
   - 使用加载管理器
   - 显示加载进度
   - 错误处理

3. **内存管理**
   - 及时清理不使用的纹理
   - 使用 `texture.dispose()`

## 📐 规格说明

| 文件名 | 分辨率 | 大小 | 用途 |
|--------|--------|------|------|
| 023.hdr | - | - | 环境光照 |
| 2k.hdr | 2048x1024 | - | 环境光照 |

## 🎯 未来计划

- [ ] 添加更多环境贴图选项
- [ ] 提供不同时间段的光照（白天/黄昏/夜晚）
- [ ] 添加纹理预览图
- [ ] 优化文件大小
