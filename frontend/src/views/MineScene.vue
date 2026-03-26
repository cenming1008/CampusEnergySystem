<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive, watch, computed } from 'vue'
import { storeToRefs } from 'pinia'
import * as THREE from 'three'
import { getDevices, type Device } from '@/api/device'
import { getAnalysis } from '@/api/telemetry'
import { useSocketStore } from '@/stores/useSocketStore'
import { useAuthStore } from '@/stores/useAuthStore'
import { ElMessage } from 'element-plus'
import { usePermissions } from '@/shared/composables/usePermissions'

interface SelectedBuildingInfo {
  name?: string
  type?: string
}

interface DeviceRealtimeSnapshot {
  power: number
  energy: number
  timestamp: Date
}

interface OrbitControlsLike {
  target: THREE.Vector3
  enableDamping: boolean
  dampingFactor: number
  maxPolarAngle: number
  minDistance: number
  maxDistance: number
  update(): void
}

interface PostProcessingComposerLike {
  addPass(pass: unknown): void
  render(): void
  setSize(width: number, height: number): void
  dispose(): void
}

interface Css2DRendererLike {
  domElement: HTMLElement
  setSize(width: number, height: number): void
  render(scene: THREE.Scene, camera: THREE.Camera): void
}

type Css2DObjectLike = THREE.Object3D & {
  position: THREE.Vector3
  removeFromParent(): THREE.Object3D
}

interface SceneGeneratorLike {
  createCompleteScene(): unknown
  getGroup(name: string): THREE.Group | undefined
  dispose?(): void
}

// --- WebSocket ---
const socketStore = useSocketStore()
const { latestMessage } = storeToRefs(socketStore)
const authStore = useAuthStore()
const { hasScopedAccess } = usePermissions()

// --- 状态 ---
const containerRef = ref<HTMLDivElement | null>(null)
const loading = ref(true)
const loadingProgress = ref(0)
const loadingText = ref('正在初始化场景...')
const deviceList = ref<Device[]>([])
const selectedBuilding = ref<SelectedBuildingInfo | null>(null)
const showInfoPanel = ref(false)
const currentTime = ref('')
const viewMode = ref<'overview' | 'pit'>('overview')
const assetBase = import.meta.env.BASE_URL
const sceneScopeHint = computed(() => {
  if (!authStore.locationScope) {
    return '当前数字孪生视图展示的是当前账号可访问的全部场景设备。'
  }
  return `当前数字孪生视图已按位置范围 ${authStore.locationScope} 过滤，仅显示授权设备与统计。`
})

// 实时数据
const realTimeStats = reactive({
  totalPower: 0,
  onlineDevices: 0,
  warningCount: 0,
  errorCount: 0,
  efficiency: 0
})

// 设备实时数据映射
const deviceRealTimeData = reactive<Map<number, DeviceRealtimeSnapshot>>(new Map())

// 设备标记
const deviceMarkers = ref<Array<{
  id: number
  deviceId: number
  name: string
  building: string
  position: THREE.Vector3
  status: 'normal' | 'warning' | 'error' | 'offline'
  power: number
  device?: Device
}>>([])

// Three.js 变量
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControlsLike
let composer: PostProcessingComposerLike
let labelRenderer: Css2DRendererLike
let animationId: number
let clock = new THREE.Clock()

// 模型加载器
let rgbeLoader: { loadAsync(url: string): Promise<THREE.Texture> }
let textureLoader: THREE.TextureLoader

// 场景对象
let groundMesh: THREE.Mesh | null = null
let sceneGenerator: SceneGeneratorLike | null = null
let timeIntervalId: ReturnType<typeof setInterval> | null = null
let dataRefreshIntervalId: ReturnType<typeof setInterval> | null = null

// 动态对象（用于动画）
const animatedObjects: Array<{
  object: THREE.Object3D
  animation: (time: number) => void
}> = []

// 标签对象
const labelObjects: Css2DObjectLike[] = []

let OrbitControlsCtor: new (camera: THREE.Camera, domElement: HTMLElement) => OrbitControlsLike
let EffectComposerCtor: new (renderer: THREE.WebGLRenderer) => PostProcessingComposerLike
let RenderPassCtor: new (scene: THREE.Scene, camera: THREE.Camera) => unknown
let UnrealBloomPassCtor: new (resolution: THREE.Vector2, strength: number, radius: number, threshold: number) => unknown
let OutputPassCtor: new () => unknown
let RGBELoaderCtor: new () => { loadAsync(url: string): Promise<THREE.Texture> }
let CSS2DRendererCtor: new () => Css2DRendererLike
let CSS2DObjectCtor: new (element: HTMLElement) => Css2DObjectLike
let MineSceneGeneratorCtor: new (scene: THREE.Scene) => SceneGeneratorLike
let activeCameraAnimation = 0

const loadSceneRuntime = async () => {
  if (OrbitControlsCtor) return

  const [
    controlsModule,
    effectComposerModule,
    renderPassModule,
    bloomPassModule,
    outputPassModule,
    rgbeModule,
    css2dModule,
    mineModule,
  ] = await Promise.all([
    import('three/examples/jsm/controls/OrbitControls.js'),
    import('three/examples/jsm/postprocessing/EffectComposer.js'),
    import('three/examples/jsm/postprocessing/RenderPass.js'),
    import('three/examples/jsm/postprocessing/UnrealBloomPass.js'),
    import('three/examples/jsm/postprocessing/OutputPass.js'),
    import('three/examples/jsm/loaders/RGBELoader.js'),
    import('three/examples/jsm/renderers/CSS2DRenderer.js'),
    import('@/three/mine'),
  ])

  OrbitControlsCtor = controlsModule.OrbitControls
  EffectComposerCtor = effectComposerModule.EffectComposer
  RenderPassCtor = renderPassModule.RenderPass
  UnrealBloomPassCtor = bloomPassModule.UnrealBloomPass
  OutputPassCtor = outputPassModule.OutputPass
  RGBELoaderCtor = rgbeModule.RGBELoader
  CSS2DRendererCtor = css2dModule.CSS2DRenderer
  CSS2DObjectCtor = css2dModule.CSS2DObject
  MineSceneGeneratorCtor = mineModule.MineSceneGenerator
}

const easeOutCubic = (value: number) => 1 - Math.pow(1 - value, 3)

const animateVector3 = (
  vector: THREE.Vector3,
  target: THREE.Vector3,
  durationMs = 1500,
  onUpdate?: () => void
) => {
  const animationId = ++activeCameraAnimation
  const start = vector.clone()
  const startedAt = performance.now()

  const step = (timestamp: number) => {
    if (animationId !== activeCameraAnimation) return

    const progress = Math.min((timestamp - startedAt) / durationMs, 1)
    vector.lerpVectors(start, target, easeOutCubic(progress))
    onUpdate?.()

    if (progress < 1) {
      requestAnimationFrame(step)
    }
  }

  requestAnimationFrame(step)
}

const animateCameraView = (
  cameraTarget: THREE.Vector3,
  controlsTarget: THREE.Vector3
) => {
  animateVector3(camera.position, cameraTarget, 1500)
  animateVector3(controls.target, controlsTarget, 1500, () => controls.update())
}

// --- 初始化 ---
const initScene = async () => {
  if (!containerRef.value) return
  await loadSceneRuntime()

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  // 创建场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0a0a1a)
  scene.fog = new THREE.Fog(0x0a0a1a, 200, 800)

  // 创建相机
  camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 2000)
  camera.position.set(180, 140, 160)
  camera.lookAt(0, -10, -20)

  // 创建渲染器
  renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
    powerPreference: 'high-performance',
    logarithmicDepthBuffer: true
  })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.0
  containerRef.value.appendChild(renderer.domElement)

  // CSS2D 标签渲染器
  labelRenderer = new CSS2DRendererCtor()
  labelRenderer.setSize(width, height)
  labelRenderer.domElement.style.position = 'absolute'
  labelRenderer.domElement.style.top = '0'
  labelRenderer.domElement.style.pointerEvents = 'none'
  containerRef.value.appendChild(labelRenderer.domElement)

  // 后期处理
  setupPostProcessing()

  // 控制器
  controls = new OrbitControlsCtor(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.maxPolarAngle = Math.PI / 2.1
  controls.minDistance = 50
  controls.maxDistance = 500
  controls.target.set(0, -10, -20)

  rgbeLoader = new RGBELoaderCtor()
  textureLoader = new THREE.TextureLoader()

  // 创建场景元素
  loadingText.value = '加载灯光环境...'
  loadingProgress.value = 10
  createLights()
  await loadEnvironment()

  loadingText.value = '创建矿区地形...'
  loadingProgress.value = 20
  await createGround()

  loadingText.value = '生成仿真场景...'
  loadingProgress.value = 30
  sceneGenerator = new MineSceneGeneratorCtor(scene)
  sceneGenerator.createCompleteScene()
  
  // 获取生成的组用于后续操作
  loadingText.value = '添加场景标签...'
  loadingProgress.value = 45
  addBuildingLabels()
  
  loadingText.value = '初始化动态效果...'
  loadingProgress.value = 50
  setupAnimations()

  loadingText.value = '加载设备数据...'
  loadingProgress.value = 70
  await loadDevicesFromBackend()

  loadingText.value = '创建特效...'
  loadingProgress.value = 85

  loadingText.value = '完成!'
  loadingProgress.value = 100

  // 事件监听
  window.addEventListener('resize', onResize)
  renderer.domElement.addEventListener('click', onClick)

  loading.value = false
  animate()

  updateTime()
  timeIntervalId = setInterval(updateTime, 1000)

  startDataRefresh()
}

const setupPostProcessing = () => {
  composer = new EffectComposerCtor(renderer)

  const renderPass = new RenderPassCtor(scene, camera)
  composer.addPass(renderPass)

  const bloomPass = new UnrealBloomPassCtor(
    new THREE.Vector2(window.innerWidth, window.innerHeight),
    0.8, 0.3, 0.9
  )
  composer.addPass(bloomPass)

  const outputPass = new OutputPassCtor()
  composer.addPass(outputPass)
}

const loadEnvironment = async () => {
  const candidates = [`${assetBase}textures/2k.hdr`, `${assetBase}textures/023.hdr`]
  for (const url of candidates) {
    try {
      const texture = await rgbeLoader.loadAsync(url)
      texture.mapping = THREE.EquirectangularReflectionMapping
      scene.environment = texture
      return
    } catch (_e) {
      continue
    }
  }
  // HDR 环境加载失败，回退到默认环境
}

const createLights = () => {
  // 环境光
  const ambient = new THREE.AmbientLight(0x6b6b6b, 0.6)
  scene.add(ambient)

  // 主光源
  const mainLight = new THREE.DirectionalLight(0xfff1e0, 1.0)
  mainLight.position.set(160, 220, 120)
  mainLight.castShadow = true
  mainLight.shadow.mapSize.width = 4096
  mainLight.shadow.mapSize.height = 4096
  mainLight.shadow.camera.near = 10
  mainLight.shadow.camera.far = 500
  mainLight.shadow.camera.left = -150
  mainLight.shadow.camera.right = 150
  mainLight.shadow.camera.top = 150
  mainLight.shadow.camera.bottom = -150
  scene.add(mainLight)

  // 补光
  const fillLight = new THREE.DirectionalLight(0xc9d1d9, 0.3)
  fillLight.position.set(-120, 80, -140)
  scene.add(fillLight)
}

const createGround = async () => {
  const groundGeo = new THREE.CircleGeometry(260, 96)
  let groundMat: THREE.MeshStandardMaterial
  try {
    const groundTex = await textureLoader.loadAsync(`${assetBase}textures/mine/ground_diff.jpg`)
    groundTex.wrapS = THREE.RepeatWrapping
    groundTex.wrapT = THREE.RepeatWrapping
    groundTex.repeat.set(8, 8)
    groundTex.anisotropy = 8
    groundMat = new THREE.MeshStandardMaterial({
      map: groundTex,
      color: 0xb3a387,
      roughness: 0.9,
      metalness: 0.05
    })
  } catch (_e) {
    groundMat = new THREE.MeshStandardMaterial({
      color: 0x4a5d4a,
      roughness: 0.9,
      metalness: 0.05
    })
  }
  groundMesh = new THREE.Mesh(groundGeo, groundMat)
  groundMesh.rotation.x = -Math.PI / 2
  groundMesh.receiveShadow = true
  scene.add(groundMesh)
}

// createMinePit 已移至 MineSceneGenerator

// 设置动画效果
const setupAnimations = () => {
  if (!sceneGenerator) return

  const vehiclesGroup = sceneGenerator.getGroup('vehicles')
  if (vehiclesGroup) {
    // 矿卡移动动画
    vehiclesGroup.children.forEach((truck: THREE.Object3D, index: number) => {
      if (truck.userData.type === 'truck') {
        const startPos = truck.position.clone()
        animatedObjects.push({
          object: truck,
          animation: (time: number) => {
            // 矿卡沿着道路移动
            const speed = 0.5
            const radius = 30 + index * 10
            truck.position.x = startPos.x + Math.cos(time * speed) * radius
            truck.position.z = startPos.z + Math.sin(time * speed) * radius
            truck.rotation.y = time * speed + Math.PI / 2
          }
        })
      }
    })
  }

  const equipmentGroup = sceneGenerator.getGroup('equipment')
  if (equipmentGroup) {
    // 挖掘机臂摆动
    equipmentGroup.children.forEach((equipment: THREE.Object3D) => {
      if (equipment.userData.type === 'excavator') {
        const arm = equipment.children.find((child: THREE.Object3D) => 
          child instanceof THREE.Mesh && child.geometry.type === 'BoxGeometry'
        )
        if (arm) {
          animatedObjects.push({
            object: arm,
            animation: (time: number) => {
              arm.rotation.z = -Math.PI / 6 + Math.sin(time * 0.5) * 0.3
            }
          })
        }
      }
    })
  }

  // 传送带旋转动画
  const equipment = sceneGenerator.getGroup('equipment')
  if (equipment) {
    equipment.traverse((child: THREE.Object3D) => {
      if (child.userData.type === 'conveyor') {
        animatedObjects.push({
          object: child,
          animation: (time: number) => {
            // 传送带上的纹理移动效果
            if (child instanceof THREE.Mesh && child.material instanceof THREE.MeshStandardMaterial) {
              // 可以通过修改UV来实现传送带移动效果
            }
          }
        })
      }
    })
  }

  // 雷达旋转
  const buildings = sceneGenerator.getGroup('buildings')
  if (buildings) {
    buildings.traverse((child: THREE.Object3D) => {
      if (child.userData.name === '中控中心') {
        const radar = child.children.find((c: THREE.Object3D) => 
          c instanceof THREE.Mesh && c.geometry.type === 'ConeGeometry'
        )
        if (radar) {
          animatedObjects.push({
            object: radar,
            animation: (time: number) => {
              radar.rotation.y = time * 2
            }
          })
        }
      }
    })
  }
}

const addBuildingLabels = () => {
  const labels = [
    { text: '露天矿区', pos: new THREE.Vector3(0, 20, -20), color: '#d1b68b' },
    { text: '能源中心', pos: new THREE.Vector3(-60, 35, 40), color: '#33d17a' },
    { text: '选矿车间', pos: new THREE.Vector3(50, 40, 20), color: '#ff7800' },
    { text: '智能仓储', pos: new THREE.Vector3(50, 30, 90), color: '#9d7fbf' },
    { text: '综合办公楼', pos: new THREE.Vector3(-60, 45, -50), color: '#3584e4' },
    { text: '中控中心', pos: new THREE.Vector3(-10, 28, 0), color: '#e01b24' }
  ]

  labels.forEach(label => {
    const div = document.createElement('div')
    div.className = 'scene-label'
    div.innerHTML = `
      <div class="label-content">
        <span class="label-dot" style="background: ${label.color}"></span>
        <span class="label-text">${label.text}</span>
      </div>
    `
    const labelObj = new CSS2DObjectCtor(div)
    labelObj.position.copy(label.pos)
    scene.add(labelObj)
    labelObjects.push(labelObj)
  })
}

// --- 视图控制 ---
const showOverview = () => {
  viewMode.value = 'overview'
  animateCameraView(
    new THREE.Vector3(180, 140, 160),
    new THREE.Vector3(0, -10, -20)
  )
}

const focusPit = () => {
  viewMode.value = 'pit'
  animateCameraView(
    new THREE.Vector3(0, 140, -60),
    new THREE.Vector3(0, -30, -20)
  )
}

// --- 数据加载 ---
const loadDevicesFromBackend = async () => {
  try {
    const devices = await getDevices()
    deviceList.value = devices

    deviceMarkers.value = []
    let markerIndex = 0

    devices.forEach((device: Device) => {
      // 根据设备类型分配位置
      let pos = new THREE.Vector3()

      if (device.device_type === 'solar' || device.device_type === 'storage') {
        pos.set(-60 + (markerIndex % 3) * 10, 30, 40 + Math.floor(markerIndex / 3) * 8)
      } else if (device.name.includes('破碎') || device.name.includes('球磨')) {
        pos.set(50 + (markerIndex % 4) * 8, 35, 20 + Math.floor(markerIndex / 4) * 8)
      } else {
        pos.set(-10 + (markerIndex % 3) * 8, 22, (markerIndex % 2) * 8)
      }

      deviceMarkers.value.push({
        id: markerIndex + 1,
        deviceId: device.id ?? markerIndex + 1,
        name: device.name,
        building: device.device_type,
        position: pos,
        status: device.is_active ? 'normal' : 'offline',
        power: 0,
        device
      })
      markerIndex++
    })

    await loadAllDeviceData()
  } catch {
    ElMessage.error('加载设备数据失败')
  }
}

const loadAllDeviceData = async () => {
  let totalPower = 0
  let onlineCount = 0
  let warningCount = 0
  let errorCount = 0

  for (const marker of deviceMarkers.value) {
    try {
      const analysis = await getAnalysis(marker.deviceId)
      marker.power = Math.abs(analysis.current_power || 0)
      totalPower += marker.power

      if (!marker.device?.is_active) {
        marker.status = 'offline'
      } else if (analysis.current_power === 0 && marker.device?.device_type === 'load') {
        marker.status = 'warning'
        warningCount++
      } else {
        marker.status = 'normal'
        onlineCount++
      }

      deviceRealTimeData.set(marker.deviceId, {
        power: analysis.current_power,
        energy: analysis.today_energy,
        timestamp: new Date()
      })
    } catch (e) {
      marker.status = 'error'
      errorCount++
    }
  }

  realTimeStats.totalPower = Math.round(totalPower)
  realTimeStats.onlineDevices = onlineCount
  realTimeStats.warningCount = warningCount
  realTimeStats.errorCount = errorCount
  realTimeStats.efficiency = deviceMarkers.value.length > 0 
    ? Math.round((onlineCount / deviceMarkers.value.length) * 100) 
    : 0
}

const startDataRefresh = () => {
  dataRefreshIntervalId = setInterval(loadAllDeviceData, 30000)
}

// --- 动画循环 ---
const animate = () => {
  animationId = requestAnimationFrame(animate)
  const time = clock.getElapsedTime()

  controls.update()

  // 更新动态对象动画
  animatedObjects.forEach(({ object, animation }) => {
    animation(time)
  })

  composer.render()
  labelRenderer.render(scene, camera)
}

// --- 事件处理 ---
const onResize = () => {
  if (!containerRef.value) return
  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
  composer.setSize(width, height)
  labelRenderer.setSize(width, height)
}

const onClick = (event: MouseEvent) => {
  if (!containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  const mouse = new THREE.Vector2(
    ((event.clientX - rect.left) / rect.width) * 2 - 1,
    -((event.clientY - rect.top) / rect.height) * 2 + 1
  )

  const raycaster = new THREE.Raycaster()
  raycaster.setFromCamera(mouse, camera)

  const meshes: THREE.Mesh[] = []
  scene.traverse(child => {
    if (child instanceof THREE.Mesh && child.userData.type === 'building') {
      meshes.push(child)
    }
  })

  const intersects = raycaster.intersectObjects(meshes)
  if (intersects.length > 0) {
    const obj = intersects[0].object
    selectedBuilding.value = obj.userData as SelectedBuildingInfo
    showInfoPanel.value = true
  }
}

const updateTime = () => {
  currentTime.value = new Date().toLocaleString('zh-CN')
}

const resetView = () => {
  showOverview()
}

// --- WebSocket ---
watch(latestMessage, (msg) => {
  if (msg?.type === 'telemetry_update') {
    const data = msg.data
    if (data?.device_id == null) return
    const marker = deviceMarkers.value.find(m => m.deviceId === data.device_id)
    if (marker) {
      marker.power = Math.abs(data.power || 0)
      marker.status = data.power === 0 ? 'warning' : 'normal'
      realTimeStats.totalPower = deviceMarkers.value.reduce((sum, m) => sum + m.power, 0)
    }
  }
})

// --- 生命周期 ---
onMounted(async () => {
  socketStore.connect()
  await initScene()
})

onUnmounted(() => {
  if (timeIntervalId) clearInterval(timeIntervalId)
  if (dataRefreshIntervalId) clearInterval(dataRefreshIntervalId)

  window.removeEventListener('resize', onResize)
  renderer?.domElement?.removeEventListener('click', onClick)
  if (animationId) cancelAnimationFrame(animationId)

  labelObjects.forEach(l => l.removeFromParent())

  sceneGenerator?.dispose?.()
  animatedObjects.length = 0

  controls?.update?.()
  if (controls && 'dispose' in controls) (controls as any).dispose()
  composer?.dispose()
  renderer?.dispose()
})
</script>

<template>
  <div class="mine-scene-page">
    <!-- 加载界面 -->
    <div
      v-if="loading"
      class="loading-overlay"
    >
      <div class="loading-content">
        <div class="loading-logo">
          <div class="logo-ring" />
          <div class="logo-ring" />
          <div class="logo-ring" />
          <span class="logo-icon">⛏️</span>
        </div>
        <div class="loading-text">
          {{ loadingText }}
        </div>
        <div class="loading-bar">
          <div
            class="loading-progress"
            :style="{ width: loadingProgress + '%' }"
          />
        </div>
        <div class="loading-percent">
          {{ loadingProgress }}%
        </div>
      </div>
    </div>

    <!-- 3D场景 -->
    <div
      ref="containerRef"
      class="scene-container"
    />

    <!-- 顶部状态栏 -->
    <div class="top-bar">
      <div class="bar-left">
        <div class="system-title">
          <div class="title-icon">
            ⛏️
          </div>
          <div class="title-text">
            <span class="main-title">矿区数字孪生监控平台</span>
            <span class="sub-time">{{ currentTime }}</span>
          </div>
        </div>
        <el-tag
          v-if="hasScopedAccess"
          size="small"
          type="warning"
          effect="dark"
          class="scope-tag"
        >
          范围受限视图
        </el-tag>
      </div>
      <div class="bar-center">
        <div class="stat-item">
          <div class="stat-icon power">
            ⚡
          </div>
          <div class="stat-data">
            <span class="stat-value">{{ realTimeStats.totalPower.toFixed(1) }}</span>
            <span class="stat-unit">kW</span>
          </div>
          <span class="stat-label">总功率</span>
        </div>
        <div class="stat-item">
          <div class="stat-icon online">
            ✅
          </div>
          <div class="stat-data">
            <span class="stat-value success">{{ realTimeStats.onlineDevices }}</span>
          </div>
          <span class="stat-label">在线设备</span>
        </div>
        <div
          v-if="realTimeStats.warningCount > 0"
          class="stat-item"
        >
          <div class="stat-icon warning">
            ⚠️
          </div>
          <div class="stat-data">
            <span class="stat-value warn">{{ realTimeStats.warningCount }}</span>
          </div>
          <span class="stat-label">警告</span>
        </div>
        <div class="stat-item">
          <div class="stat-icon efficiency">
            📊
          </div>
          <div class="stat-data">
            <span class="stat-value">{{ realTimeStats.efficiency }}%</span>
          </div>
          <span class="stat-label">运行效率</span>
        </div>
      </div>
      <div class="bar-right">
        <el-button
          type="primary"
          size="small"
          @click="resetView"
        >
          重置视角
        </el-button>
      </div>
    </div>

    <!-- 左侧视图控制 -->
    <div class="view-controls">
      <div class="control-title">
        🎮 视图控制
      </div>
      <div class="control-buttons">
        <button 
          class="control-btn" 
          :class="{ active: viewMode === 'overview' }"
          @click="showOverview"
        >
          <span class="btn-icon">🏭</span>
          <span class="btn-text">矿区全景</span>
        </button>
        <button 
          class="control-btn" 
          :class="{ active: viewMode === 'pit' }"
          @click="focusPit"
        >
          <span class="btn-icon">⛏️</span>
          <span class="btn-text">矿坑视角</span>
        </button>
      </div>
    </div>

    <!-- 右侧设备列表 -->
    <div class="device-panel">
      <div class="panel-header">
        <span class="panel-title">📍 实时监控</span>
        <span class="device-count">{{ deviceMarkers.length }} 台设备</span>
      </div>
      <div class="device-list">
        <div 
          v-for="m in deviceMarkers.slice(0, 10)" 
          :key="m.id" 
          class="device-item"
          :class="m.status"
        >
          <div
            class="device-status-dot"
            :class="m.status"
          />
          <div class="device-info">
            <div class="device-name">
              {{ m.name }}
            </div>
            <div class="device-power">
              {{ m.power.toFixed(1) }} kW
            </div>
          </div>
        </div>
      </div>
      <div class="status-legend">
        <div class="legend-item">
          <span class="dot normal" />正常
        </div>
        <div class="legend-item">
          <span class="dot warning" />警告
        </div>
        <div class="legend-item">
          <span class="dot error" />故障
        </div>
        <div class="legend-item">
          <span class="dot offline" />离线
        </div>
      </div>
    </div>

    <!-- 底部信息 -->
    <div class="bottom-info">
      <div class="info-item info-item--scope">
        <span class="info-icon">🧭</span>
        <span class="info-text">{{ sceneScopeHint }}</span>
      </div>
      <div class="info-item">
        <span class="info-icon">🔄</span>
        <span class="info-text">数据刷新间隔: 30秒</span>
      </div>
      <div class="info-item">
        <span class="info-icon">🌐</span>
        <span class="info-text">WebSocket: {{ socketStore.isConnected ? '已连接' : '未连接' }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mine-scene-page {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  background: #0a0a1a;
}

.scene-container {
  width: 100%;
  height: 100%;
}

/* 加载界面 */
.loading-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-content {
  text-align: center;
}

.loading-logo {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 30px;
}

.logo-ring {
  position: absolute;
  inset: 0;
  border: 3px solid transparent;
  border-top-color: #00ffff;
  border-radius: 50%;
  animation: spin 1.5s linear infinite;
}

.logo-ring:nth-child(2) {
  inset: 10px;
  border-top-color: #ff00ff;
  animation-duration: 2s;
  animation-direction: reverse;
}

.logo-ring:nth-child(3) {
  inset: 20px;
  border-top-color: #00ff88;
  animation-duration: 2.5s;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.logo-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 40px;
}

.loading-text {
  color: #00ffff;
  font-size: 18px;
  margin-bottom: 20px;
  letter-spacing: 2px;
}

.loading-bar {
  width: 300px;
  height: 6px;
  background: rgba(0, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
  margin: 0 auto 10px;
}

.loading-progress {
  height: 100%;
  background: linear-gradient(90deg, #00ffff, #00ff88);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.loading-percent {
  color: #64748b;
  font-size: 14px;
}

/* 顶部状态栏 */
.top-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 80px;
  background: linear-gradient(180deg, rgba(0, 20, 40, 0.95) 0%, transparent 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  z-index: 10;
}

.system-title {
  display: flex;
  align-items: center;
  gap: 15px;
}

.title-icon {
  font-size: 36px;
  filter: drop-shadow(0 0 10px rgba(0, 255, 255, 0.5));
}

.title-text {
  display: flex;
  flex-direction: column;
}

.main-title {
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(90deg, #00ffff, #00ff88, #ff00ff);
  background-size: 200% 100%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: gradient 3s ease infinite;
  letter-spacing: 3px;
}

@keyframes gradient {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.sub-time {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}

.bar-center {
  display: flex;
  gap: 25px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 20px;
  background: rgba(0, 255, 255, 0.05);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 12px;
  min-width: 100px;
}

.stat-icon {
  font-size: 24px;
  margin-bottom: 5px;
}

.stat-data {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #00ffff;
}

.stat-value.success { color: #00ff88; }
.stat-value.warn { color: #ffaa00; }
.stat-value.error { color: #ff3355; }

.stat-unit {
  font-size: 12px;
  color: #64748b;
}

.stat-label {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

/* 左侧视图控制 */
.view-controls {
  position: absolute;
  top: 100px;
  left: 20px;
  width: 180px;
  background: rgba(0, 20, 40, 0.9);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 16px;
  padding: 20px;
  backdrop-filter: blur(10px);
}

.control-title {
  font-size: 14px;
  font-weight: 600;
  color: #00ffff;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(0, 255, 255, 0.2);
}

.control-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 15px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #fff;
  cursor: pointer;
  transition: all 0.3s ease;
}

.control-btn:hover {
  background: rgba(0, 255, 255, 0.1);
  border-color: rgba(0, 255, 255, 0.3);
  transform: translateX(5px);
}

.control-btn.active {
  background: rgba(0, 255, 255, 0.2);
  border-color: #00ffff;
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
}

.btn-icon {
  font-size: 18px;
}

.btn-text {
  font-size: 13px;
}

/* 右侧设备面板 */
.device-panel {
  position: absolute;
  top: 100px;
  right: 20px;
  width: 260px;
  background: rgba(0, 20, 40, 0.9);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 16px;
  padding: 20px;
  backdrop-filter: blur(10px);
  max-height: calc(100vh - 180px);
  overflow-y: auto;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(0, 255, 255, 0.2);
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #00ffff;
}

.device-count {
  font-size: 11px;
  color: #64748b;
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.device-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 10px;
  border-left: 3px solid transparent;
  transition: all 0.3s ease;
}

.device-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.device-item.normal { border-left-color: #00ff88; }
.device-item.warning { border-left-color: #ffaa00; }
.device-item.error { border-left-color: #ff3355; }
.device-item.offline { border-left-color: #666666; }

.device-status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.device-status-dot.normal { background: #00ff88; box-shadow: 0 0 10px #00ff88; }
.device-status-dot.warning { background: #ffaa00; box-shadow: 0 0 10px #ffaa00; }
.device-status-dot.error { background: #ff3355; box-shadow: 0 0 10px #ff3355; }
.device-status-dot.offline { background: #666666; animation: none; }

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.device-info {
  flex: 1;
  min-width: 0;
}

.device-name {
  font-size: 12px;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.device-power {
  font-size: 14px;
  font-weight: 600;
  color: #00ffff;
  margin-top: 2px;
}

.status-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  color: #64748b;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot.normal { background: #00ff88; }
.dot.warning { background: #ffaa00; }
.dot.error { background: #ff3355; }
.dot.offline { background: #666666; }

/* 底部信息 */
.bottom-info {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(0, 20, 40, 0.8);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 20px;
}

.scope-tag {
  margin-left: 12px;
}

.info-item--scope {
  max-width: 560px;
}

.info-icon {
  font-size: 14px;
}

.info-text {
  font-size: 12px;
  color: #64748b;
}

/* 场景标签样式（会被注入到CSS2DRenderer） */
:deep(.scene-label) {
  pointer-events: none;
}

:deep(.label-content) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(0, 20, 40, 0.9);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 20px;
  backdrop-filter: blur(5px);
}

:deep(.label-dot) {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

:deep(.label-text) {
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
}

/* 滚动条样式 */
.device-panel::-webkit-scrollbar {
  width: 4px;
}

.device-panel::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 2px;
}

.device-panel::-webkit-scrollbar-thumb {
  background: rgba(0, 255, 255, 0.3);
  border-radius: 2px;
}
</style>
