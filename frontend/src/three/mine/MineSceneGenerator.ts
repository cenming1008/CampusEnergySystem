import * as THREE from 'three'

/**
 * 矿区场景生成器
 * 创建仿真的矿区3D场景，包括精细建筑、工业设备、道路等
 */
export class MineSceneGenerator {
  private scene: THREE.Scene
  private groups: Map<string, THREE.Group> = new Map()

  constructor(scene: THREE.Scene) {
    this.scene = scene
  }

  /**
   * 创建完整的矿区场景
   */
  createCompleteScene() {
    // 创建各个场景组
    this.createBuildings()
    this.createMinePit()
    this.createRoads()
    this.createIndustrialEquipment()
    this.createVehicles()
    this.createInfrastructure()
    
    return this.groups
  }

  /**
   * 创建精细化的工业建筑
   */
  private createBuildings() {
    const buildingsGroup = new THREE.Group()
    buildingsGroup.name = 'buildings'

    // 能源中心 - 带太阳能板屋顶
    const energyCenter = this.createEnergyCenter(-60, 0, 40)
    buildingsGroup.add(energyCenter)

    // 选矿车间 - 带传送带和烟囱
    const processingPlant = this.createProcessingPlant(50, 0, 20)
    buildingsGroup.add(processingPlant)

    // 智能仓储 - 带装卸平台
    const warehouse = this.createWarehouse(50, 0, 90)
    buildingsGroup.add(warehouse)

    // 综合办公楼 - 现代化建筑
    const officeBuilding = this.createOfficeBuilding(-60, 0, -50)
    buildingsGroup.add(officeBuilding)

    // 中控中心 - 带雷达和天线
    const controlCenter = this.createControlCenter(-10, 0, 0)
    buildingsGroup.add(controlCenter)

    this.scene.add(buildingsGroup)
    this.groups.set('buildings', buildingsGroup)
  }

  /**
   * 创建能源中心建筑
   */
  private createEnergyCenter(x: number, y: number, z: number): THREE.Group {
    const group = new THREE.Group()
    const width = 50
    const height = 25
    const depth = 40

    // 主建筑体
    const mainGeo = new THREE.BoxGeometry(width, height, depth)
    const mainMat = new THREE.MeshStandardMaterial({
      color: 0x26a269,
      roughness: 0.3,
      metalness: 0.7,
      emissive: new THREE.Color(0x26a269),
      emissiveIntensity: 0.1
    })
    const mainMesh = new THREE.Mesh(mainGeo, mainMat)
    mainMesh.position.set(x, height / 2, z)
    mainMesh.castShadow = true
    mainMesh.receiveShadow = true
    group.add(mainMesh)

    // 添加窗户
    const windowMat = new THREE.MeshStandardMaterial({
      color: 0x1a1a2e,
      emissive: new THREE.Color(0x4ade80),
      emissiveIntensity: 0.5,
      roughness: 0.1,
      metalness: 0.9
    })

    // 正面窗户
    for (let i = 0; i < 3; i++) {
      for (let j = 0; j < 2; j++) {
        const windowGeo = new THREE.PlaneGeometry(4, 3)
        const window = new THREE.Mesh(windowGeo, windowMat)
        window.position.set(
          x - width / 2 + 8 + i * 12,
          height / 2 - 5 + j * 8,
          z + depth / 2 + 0.1
        )
        window.rotation.y = Math.PI
        group.add(window)
      }
    }

    // 太阳能板屋顶
    const solarPanelGroup = new THREE.Group()
    for (let i = 0; i < 4; i++) {
      for (let j = 0; j < 3; j++) {
        const panelGeo = new THREE.BoxGeometry(8, 0.2, 6)
        const panelMat = new THREE.MeshStandardMaterial({
          color: 0x1a1a2e,
          metalness: 0.9,
          roughness: 0.1,
          emissive: new THREE.Color(0x4ade80),
          emissiveIntensity: 0.3
        })
        const panel = new THREE.Mesh(panelGeo, panelMat)
        panel.position.set(
          x - width / 2 + 10 + i * 10,
          height + 0.1,
          z - depth / 2 + 8 + j * 8
        )
        panel.rotation.x = -Math.PI / 6 // 倾斜角度
        solarPanelGroup.add(panel)
      }
    }
    group.add(solarPanelGroup)

    // 冷却塔
    const coolingTower = this.createCoolingTower(x + width / 2 + 5, height / 2, z)
    group.add(coolingTower)

    group.userData = { name: '能源中心', type: 'building' }
    return group
  }

  /**
   * 创建选矿车间
   */
  private createProcessingPlant(x: number, y: number, z: number): THREE.Group {
    const group = new THREE.Group()
    const width = 80
    const height = 30
    const depth = 60

    // 主建筑体
    const mainGeo = new THREE.BoxGeometry(width, height, depth)
    const mainMat = new THREE.MeshStandardMaterial({
      color: 0xc64600,
      roughness: 0.4,
      metalness: 0.6
    })
    const mainMesh = new THREE.Mesh(mainGeo, mainMat)
    mainMesh.position.set(x, height / 2, z)
    mainMesh.castShadow = true
    mainMesh.receiveShadow = true
    group.add(mainMesh)

    // 烟囱
    const chimneyGeo = new THREE.CylinderGeometry(2, 2.5, 25, 16)
    const chimneyMat = new THREE.MeshStandardMaterial({
      color: 0x4a4a4a,
      roughness: 0.8,
      metalness: 0.2
    })
    const chimney = new THREE.Mesh(chimneyGeo, chimneyMat)
    chimney.position.set(x + width / 2 - 10, height + 12.5, z - depth / 2 + 10)
    chimney.castShadow = true
    group.add(chimney)

    // 烟囱顶部烟雾效果（使用简单的几何体模拟）
    const smokeGeo = new THREE.ConeGeometry(3, 8, 8)
    const smokeMat = new THREE.MeshStandardMaterial({
      color: 0x888888,
      transparent: true,
      opacity: 0.3,
      side: THREE.DoubleSide
    })
    const smoke = new THREE.Mesh(smokeGeo, smokeMat)
    smoke.position.set(x + width / 2 - 10, height + 25, z - depth / 2 + 10)
    smoke.rotation.x = Math.PI
    group.add(smoke)

    // 传送带入口
    const conveyorIn = this.createConveyorBelt(
      x - width / 2 - 15,
      height / 2 - 5,
      z,
      20,
      Math.PI / 2
    )
    group.add(conveyorIn)

    // 传送带出口
    const conveyorOut = this.createConveyorBelt(
      x + width / 2 + 15,
      height / 2 - 5,
      z,
      20,
      -Math.PI / 2
    )
    group.add(conveyorOut)

    // 工业窗户（高窗）
    const windowMat = new THREE.MeshStandardMaterial({
      color: 0x1a1a2e,
      emissive: new THREE.Color(0xff7800),
      emissiveIntensity: 0.4
    })
    for (let i = 0; i < 5; i++) {
      const windowGeo = new THREE.PlaneGeometry(6, 4)
      const window = new THREE.Mesh(windowGeo, windowMat)
      window.position.set(
        x - width / 2 + 10 + i * 12,
        height / 2 + 5,
        z + depth / 2 + 0.1
      )
      window.rotation.y = Math.PI
      group.add(window)
    }

    group.userData = { name: '选矿车间', type: 'building' }
    return group
  }

  /**
   * 创建智能仓储
   */
  private createWarehouse(x: number, y: number, z: number): THREE.Group {
    const group = new THREE.Group()
    const width = 60
    const height = 20
    const depth = 40

    // 主建筑体
    const mainGeo = new THREE.BoxGeometry(width, height, depth)
    const mainMat = new THREE.MeshStandardMaterial({
      color: 0x613583,
      roughness: 0.5,
      metalness: 0.5
    })
    const mainMesh = new THREE.Mesh(mainGeo, mainMat)
    mainMesh.position.set(x, height / 2, z)
    mainMesh.castShadow = true
    mainMesh.receiveShadow = true
    group.add(mainMesh)

    // 装卸平台
    const platformGeo = new THREE.BoxGeometry(width + 10, 2, 15)
    const platformMat = new THREE.MeshStandardMaterial({
      color: 0x4a4a4a,
      roughness: 0.8
    })
    const platform = new THREE.Mesh(platformGeo, platformMat)
    platform.position.set(x, height / 2 - 1, z + depth / 2 + 7.5)
    platform.receiveShadow = true
    group.add(platform)

    // 仓库大门
    const doorGeo = new THREE.BoxGeometry(12, 15, 0.5)
    const doorMat = new THREE.MeshStandardMaterial({
      color: 0x2a2a2a,
      metalness: 0.8,
      roughness: 0.2
    })
    const door = new THREE.Mesh(doorGeo, doorMat)
    door.position.set(x, height / 2 - 2.5, z + depth / 2 + 0.25)
    group.add(door)

    // 屋顶通风设备
    for (let i = 0; i < 3; i++) {
      const ventGeo = new THREE.CylinderGeometry(1.5, 1.5, 2, 8)
      const ventMat = new THREE.MeshStandardMaterial({
        color: 0x888888,
        metalness: 0.7,
        roughness: 0.3
      })
      const vent = new THREE.Mesh(ventGeo, ventMat)
      vent.position.set(x - width / 2 + 15 + i * 15, height + 1, z)
      group.add(vent)
    }

    group.userData = { name: '智能仓储', type: 'building' }
    return group
  }

  /**
   * 创建综合办公楼
   */
  private createOfficeBuilding(x: number, y: number, z: number): THREE.Group {
    const group = new THREE.Group()
    const width = 45
    const height = 35
    const depth = 35

    // 主建筑体
    const mainGeo = new THREE.BoxGeometry(width, height, depth)
    const mainMat = new THREE.MeshStandardMaterial({
      color: 0x1a5fb4,
      roughness: 0.2,
      metalness: 0.8,
      emissive: new THREE.Color(0x1a5fb4),
      emissiveIntensity: 0.05
    })
    const mainMesh = new THREE.Mesh(mainGeo, mainMat)
    mainMesh.position.set(x, height / 2, z)
    mainMesh.castShadow = true
    mainMesh.receiveShadow = true
    group.add(mainMesh)

    // 玻璃幕墙效果（带窗户）
    const windowMat = new THREE.MeshStandardMaterial({
      color: 0x0a0a1a,
      transparent: true,
      opacity: 0.7,
      roughness: 0.1,
      metalness: 0.9,
      emissive: new THREE.Color(0x4a9eff),
      emissiveIntensity: 0.3
    })

    // 正面窗户网格
    for (let i = 0; i < 4; i++) {
      for (let j = 0; j < 3; j++) {
        const windowGeo = new THREE.PlaneGeometry(6, 7)
        const window = new THREE.Mesh(windowGeo, windowMat)
        window.position.set(
          x - width / 2 + 7 + i * 9,
          height / 2 - 10 + j * 10,
          z + depth / 2 + 0.1
        )
        window.rotation.y = Math.PI
        group.add(window)
      }
    }

    // 入口
    const entranceGeo = new THREE.BoxGeometry(8, 12, 3)
    const entranceMat = new THREE.MeshStandardMaterial({
      color: 0x2a2a2a,
      metalness: 0.9,
      roughness: 0.1
    })
    const entrance = new THREE.Mesh(entranceGeo, entranceMat)
    entrance.position.set(x, height / 2 - 11.5, z + depth / 2 + 1.5)
    group.add(entrance)

    group.userData = { name: '综合办公楼', type: 'building' }
    return group
  }

  /**
   * 创建中控中心
   */
  private createControlCenter(x: number, y: number, z: number): THREE.Group {
    const group = new THREE.Group()
    const width = 30
    const height = 18
    const depth = 25

    // 主建筑体
    const mainGeo = new THREE.BoxGeometry(width, height, depth)
    const mainMat = new THREE.MeshStandardMaterial({
      color: 0xa51d2d,
      roughness: 0.3,
      metalness: 0.7,
      emissive: new THREE.Color(0xa51d2d),
      emissiveIntensity: 0.2
    })
    const mainMesh = new THREE.Mesh(mainGeo, mainMat)
    mainMesh.position.set(x, height / 2, z)
    mainMesh.castShadow = true
    mainMesh.receiveShadow = true
    group.add(mainMesh)

    // 雷达天线
    const radarGeo = new THREE.ConeGeometry(2, 6, 8)
    const radarMat = new THREE.MeshStandardMaterial({
      color: 0x00ffff,
      metalness: 0.9,
      roughness: 0.1,
      emissive: new THREE.Color(0x00ffff),
      emissiveIntensity: 0.5
    })
    const radar = new THREE.Mesh(radarGeo, radarMat)
    radar.position.set(x, height + 3, z)
    group.add(radar)

    // 通信天线
    for (let i = 0; i < 4; i++) {
      const antennaGeo = new THREE.CylinderGeometry(0.1, 0.1, 8, 8)
      const antennaMat = new THREE.MeshStandardMaterial({
        color: 0x888888,
        metalness: 0.9
      })
      const antenna = new THREE.Mesh(antennaGeo, antennaMat)
      antenna.position.set(
        x - width / 2 + 5 + i * 6,
        height + 4,
        z - depth / 2 + 5
      )
      group.add(antenna)
    }

    // 监控摄像头
    const cameraGeo = new THREE.SphereGeometry(0.8, 8, 8)
    const cameraMat = new THREE.MeshStandardMaterial({
      color: 0x1a1a2e,
      metalness: 0.9,
      roughness: 0.1
    })
    const camera = new THREE.Mesh(cameraGeo, cameraMat)
    camera.position.set(x + width / 2 - 1, height / 2 + 5, z)
    group.add(camera)

    group.userData = { name: '中控中心', type: 'building' }
    return group
  }

  /**
   * 创建冷却塔
   */
  private createCoolingTower(x: number, y: number, z: number): THREE.Group {
    const group = new THREE.Group()
    
    // 塔体（双曲线型）
    const towerGeo = new THREE.CylinderGeometry(3, 5, 12, 16)
    const towerMat = new THREE.MeshStandardMaterial({
      color: 0xcccccc,
      roughness: 0.6,
      metalness: 0.3
    })
    const tower = new THREE.Mesh(towerGeo, towerMat)
    tower.position.set(x, y + 6, z)
    tower.castShadow = true
    group.add(tower)

    // 顶部
    const topGeo = new THREE.CylinderGeometry(3.5, 3, 1, 16)
    const top = new THREE.Mesh(topGeo, towerMat)
    top.position.set(x, y + 12.5, z)
    group.add(top)

    return group
  }

  /**
   * 创建传送带
   */
  private createConveyorBelt(
    x: number,
    y: number,
    z: number,
    length: number,
    rotation: number
  ): THREE.Group {
    const group = new THREE.Group()

    // 传送带主体
    const beltGeo = new THREE.BoxGeometry(length, 1, 3)
    const beltMat = new THREE.MeshStandardMaterial({
      color: 0x4a4a4a,
      roughness: 0.7,
      metalness: 0.3
    })
    const belt = new THREE.Mesh(beltGeo, beltMat)
    belt.position.set(x + length / 2 * Math.cos(rotation), y, z + length / 2 * Math.sin(rotation))
    belt.rotation.y = rotation
    belt.castShadow = true
    belt.receiveShadow = true
    group.add(belt)

    // 支撑架
    for (let i = 0; i < 3; i++) {
      const supportGeo = new THREE.BoxGeometry(0.3, 2, 0.3)
      const support = new THREE.Mesh(supportGeo, beltMat)
      support.position.set(
        x + (length / 4) * (i + 1) * Math.cos(rotation),
        y - 1,
        z + (length / 4) * (i + 1) * Math.sin(rotation)
      )
      group.add(support)
    }

    group.userData = { type: 'conveyor', length, rotation }
    return group
  }

  /**
   * 创建矿坑（增强版）
   */
  private createMinePit() {
    const pitGroup = new THREE.Group()
    pitGroup.name = 'minePit'

    const levels = 7
    const topRadius = 180
    const bottomRadius = 45
    const totalDepth = 70
    const stepHeight = totalDepth / levels
    const stepSize = (topRadius - bottomRadius) / levels

    // 创建台阶
    for (let i = 0; i < levels; i++) {
      const rTop = topRadius - i * stepSize
      const rBottom = topRadius - (i + 1) * stepSize
      const geo = new THREE.CylinderGeometry(rTop, rBottom, stepHeight, 64, 1, true)
      geo.translate(0, -(i * stepHeight + stepHeight / 2), 0)

      const mat = new THREE.MeshStandardMaterial({
        color: 0x8b7a5e,
        roughness: 0.95,
        metalness: 0.05,
        side: THREE.DoubleSide
      })
      const mesh = new THREE.Mesh(geo, mat)
      mesh.castShadow = true
      mesh.receiveShadow = true
      pitGroup.add(mesh)
    }

    // 底部
    const floorGeo = new THREE.CircleGeometry(bottomRadius, 64)
    floorGeo.rotateX(-Math.PI / 2)
    floorGeo.translate(0, -totalDepth, 0)
    const floorMat = new THREE.MeshStandardMaterial({
      color: 0x7a6a53,
      roughness: 0.9,
      metalness: 0.05
    })
    const floorMesh = new THREE.Mesh(floorGeo, floorMat)
    floorMesh.receiveShadow = true
    pitGroup.add(floorMesh)

    pitGroup.position.set(0, 0, -20)
    this.scene.add(pitGroup)
    this.groups.set('minePit', pitGroup)
  }

  /**
   * 创建道路系统
   */
  private createRoads() {
    const roadsGroup = new THREE.Group()
    roadsGroup.name = 'roads'

    // 矿坑内螺旋道路
    const roadMat = new THREE.MeshStandardMaterial({
      color: 0x4a4a4a,
      roughness: 0.9,
      metalness: 0.1
    })

    for (let i = 0; i < 6; i++) {
      const radius = 150 - i * 20
      const angle = (i * Math.PI) / 3
      const roadGeo = new THREE.BoxGeometry(12, 0.5, 40)
      const road = new THREE.Mesh(roadGeo, roadMat)
      road.position.set(
        Math.cos(angle) * radius,
        -i * 10 - 5,
        -20 + Math.sin(angle) * radius
      )
      road.rotation.y = angle + Math.PI / 2
      road.receiveShadow = true
      roadsGroup.add(road)
    }

    // 地面连接道路
    const groundRoads = [
      { start: [-60, 0, 40], end: [-10, 0, 0], width: 8 },
      { start: [50, 0, 20], end: [-10, 0, 0], width: 8 },
      { start: [50, 0, 90], end: [50, 0, 20], width: 8 },
      { start: [-60, 0, -50], end: [-60, 0, 40], width: 8 }
    ]

    groundRoads.forEach(road => {
      const dx = road.end[0] - road.start[0]
      const dz = road.end[2] - road.start[2]
      const length = Math.sqrt(dx * dx + dz * dz)
      const angle = Math.atan2(dz, dx)

      const roadGeo = new THREE.BoxGeometry(length, 0.3, road.width)
      const roadMesh = new THREE.Mesh(roadGeo, roadMat)
      roadMesh.position.set(
        road.start[0] + dx / 2,
        0.15,
        road.start[2] + dz / 2
      )
      roadMesh.rotation.y = angle
      roadMesh.receiveShadow = true
      roadsGroup.add(roadMesh)

      // 道路标线
      const lineGeo = new THREE.BoxGeometry(length, 0.1, 0.3)
      const lineMat = new THREE.MeshStandardMaterial({ color: 0xffff00 })
      const line = new THREE.Mesh(lineGeo, lineMat)
      line.position.set(
        road.start[0] + dx / 2,
        0.2,
        road.start[2] + dz / 2
      )
      line.rotation.y = angle
      roadsGroup.add(line)
    })

    this.scene.add(roadsGroup)
    this.groups.set('roads', roadsGroup)
  }

  /**
   * 创建工业设备
   */
  private createIndustrialEquipment() {
    const equipmentGroup = new THREE.Group()
    equipmentGroup.name = 'equipment'

    // 挖掘机（简化版）
    const excavator = this.createExcavator(0, -30, -20)
    equipmentGroup.add(excavator)

    // 破碎机
    const crusher = this.createCrusher(30, -25, -15)
    equipmentGroup.add(crusher)

    // 传送带系统
    const conveyorSystem = this.createConveyorSystem()
    equipmentGroup.add(conveyorSystem)

    this.scene.add(equipmentGroup)
    this.groups.set('equipment', equipmentGroup)
  }

  /**
   * 创建挖掘机
   */
  private createExcavator(x: number, y: number, z: number): THREE.Group {
    const group = new THREE.Group()

    // 底盘
    const chassisGeo = new THREE.BoxGeometry(8, 3, 6)
    const chassisMat = new THREE.MeshStandardMaterial({
      color: 0xff6600,
      roughness: 0.6,
      metalness: 0.4
    })
    const chassis = new THREE.Mesh(chassisGeo, chassisMat)
    chassis.position.set(x, y + 1.5, z)
    chassis.castShadow = true
    group.add(chassis)

    // 驾驶室
    const cabGeo = new THREE.BoxGeometry(3, 2.5, 2.5)
    const cab = new THREE.Mesh(cabGeo, chassisMat)
    cab.position.set(x + 2, y + 3.25, z)
    group.add(cab)

    // 臂
    const armGeo = new THREE.BoxGeometry(1, 1, 12)
    const arm = new THREE.Mesh(armGeo, chassisMat)
    arm.position.set(x + 3, y + 2.5, z)
    arm.rotation.z = -Math.PI / 6
    group.add(arm)

    // 挖斗
    const bucketGeo = new THREE.BoxGeometry(2, 1.5, 2)
    const bucket = new THREE.Mesh(bucketGeo, chassisMat)
    bucket.position.set(x + 6, y + 1, z)
    group.add(bucket)

    group.userData = { type: 'excavator' }
    return group
  }

  /**
   * 创建破碎机
   */
  private createCrusher(x: number, y: number, z: number): THREE.Group {
    const group = new THREE.Group()

    // 主体
    const mainGeo = new THREE.CylinderGeometry(3, 3, 8, 16)
    const mainMat = new THREE.MeshStandardMaterial({
      color: 0x666666,
      roughness: 0.7,
      metalness: 0.3
    })
    const main = new THREE.Mesh(mainGeo, mainMat)
    main.position.set(x, y + 4, z)
    main.castShadow = true
    group.add(main)

    // 进料口
    const inletGeo = new THREE.BoxGeometry(4, 2, 4)
    const inlet = new THREE.Mesh(inletGeo, mainMat)
    inlet.position.set(x, y + 8, z)
    group.add(inlet)

    group.userData = { type: 'crusher' }
    return group
  }

  /**
   * 创建传送带系统
   */
  private createConveyorSystem(): THREE.Group {
    const group = new THREE.Group()

    // 从矿坑到选矿车间的传送带
    const conveyor1 = this.createConveyorBelt(0, -20, -20, 60, Math.PI / 4)
    group.add(conveyor1)

    const conveyor2 = this.createConveyorBelt(42, -15, 2, 30, 0)
    group.add(conveyor2)

    return group
  }

  /**
   * 创建车辆
   */
  private createVehicles() {
    const vehiclesGroup = new THREE.Group()
    vehiclesGroup.name = 'vehicles'

    // 矿卡（简化版）
    for (let i = 0; i < 3; i++) {
      const truck = this.createMiningTruck(
        -30 + i * 20,
        -25 + i * 5,
        -20 - i * 10
      )
      vehiclesGroup.add(truck)
    }

    this.scene.add(vehiclesGroup)
    this.groups.set('vehicles', vehiclesGroup)
  }

  /**
   * 创建矿卡
   */
  private createMiningTruck(x: number, y: number, z: number): THREE.Group {
    const group = new THREE.Group()

    // 车头
    const cabGeo = new THREE.BoxGeometry(4, 3, 3)
    const cabMat = new THREE.MeshStandardMaterial({
      color: 0xff6600,
      roughness: 0.5,
      metalness: 0.5
    })
    const cab = new THREE.Mesh(cabGeo, cabMat)
    cab.position.set(x, y + 1.5, z)
    cab.castShadow = true
    group.add(cab)

    // 货箱
    const cargoGeo = new THREE.BoxGeometry(8, 4, 5)
    const cargoMat = new THREE.MeshStandardMaterial({
      color: 0x888888,
      roughness: 0.7,
      metalness: 0.3
    })
    const cargo = new THREE.Mesh(cargoGeo, cargoMat)
    cargo.position.set(x - 2, y + 2, z)
    cargo.castShadow = true
    group.add(cargo)

    // 车轮
    const wheelGeo = new THREE.CylinderGeometry(1, 1, 1.5, 16)
    const wheelMat = new THREE.MeshStandardMaterial({
      color: 0x1a1a1a,
      roughness: 0.9
    })

    const wheelPositions = [
      [x + 1.5, y, z - 1.5],
      [x + 1.5, y, z + 1.5],
      [x - 3.5, y, z - 1.5],
      [x - 3.5, y, z + 1.5],
      [x - 6.5, y, z - 1.5],
      [x - 6.5, y, z + 1.5]
    ]

    wheelPositions.forEach(pos => {
      const wheel = new THREE.Mesh(wheelGeo, wheelMat)
      wheel.position.set(pos[0], pos[1], pos[2])
      wheel.rotation.z = Math.PI / 2
      wheel.castShadow = true
      group.add(wheel)
    })

    group.userData = { type: 'truck' }
    return group
  }

  /**
   * 创建基础设施
   */
  private createInfrastructure() {
    const infraGroup = new THREE.Group()
    infraGroup.name = 'infrastructure'

    // 路灯
    const lampPositions = [
      [-60, 0, 40], [50, 0, 20], [50, 0, 90],
      [-60, 0, -50], [-10, 0, 0]
    ]

    lampPositions.forEach(pos => {
      const lamp = this.createStreetLamp(pos[0], pos[1], pos[2])
      infraGroup.add(lamp)
    })

    // 围栏
    const fence = this.createFence()
    infraGroup.add(fence)

    this.scene.add(infraGroup)
    this.groups.set('infrastructure', infraGroup)
  }

  /**
   * 创建路灯
   */
  private createStreetLamp(x: number, y: number, z: number): THREE.Group {
    const group = new THREE.Group()

    // 灯杆
    const poleGeo = new THREE.CylinderGeometry(0.2, 0.2, 8, 8)
    const poleMat = new THREE.MeshStandardMaterial({
      color: 0x666666,
      metalness: 0.8,
      roughness: 0.2
    })
    const pole = new THREE.Mesh(poleGeo, poleMat)
    pole.position.set(x, y + 4, z)
    group.add(pole)

    // 灯头
    const lampGeo = new THREE.SphereGeometry(0.8, 8, 8)
    const lampMat = new THREE.MeshStandardMaterial({
      color: 0xffffaa,
      emissive: new THREE.Color(0xffffaa),
      emissiveIntensity: 1.0
    })
    const lamp = new THREE.Mesh(lampGeo, lampMat)
    lamp.position.set(x, y + 8, z)
    group.add(lamp)

    return group
  }

  /**
   * 创建围栏
   */
  private createFence(): THREE.Group {
    const group = new THREE.Group()

    const fenceMat = new THREE.MeshStandardMaterial({
      color: 0x888888,
      metalness: 0.7,
      roughness: 0.3
    })

    // 围栏柱子
    const postGeo = new THREE.CylinderGeometry(0.3, 0.3, 2, 8)
    const postPositions = [
      [-80, 1, 50], [70, 1, 50], [70, 1, -60], [-80, 1, -60]
    ]

    postPositions.forEach(pos => {
      const post = new THREE.Mesh(postGeo, fenceMat)
      post.position.set(pos[0], pos[1], pos[2])
      group.add(post)
    })

    // 围栏横杆
    const railGeo = new THREE.BoxGeometry(150, 0.2, 0.2)
    for (let i = 0; i < 2; i++) {
      const rail = new THREE.Mesh(railGeo, fenceMat)
      rail.position.set(-5, 0.5 + i * 0.8, 50)
      group.add(rail)

      const rail2 = new THREE.Mesh(railGeo, fenceMat)
      rail2.position.set(-5, 0.5 + i * 0.8, -60)
      rail2.rotation.y = Math.PI / 2
      group.add(rail2)
    }

    return group
  }

  /**
   * 获取场景组
   */
  getGroup(name: string): THREE.Group | undefined {
    return this.groups.get(name)
  }

  /**
   * 清理场景
   */
  dispose() {
    this.groups.forEach(group => {
      group.traverse(child => {
        if (child instanceof THREE.Mesh) {
          child.geometry.dispose()
          if (Array.isArray(child.material)) {
            child.material.forEach(mat => mat.dispose())
          } else {
            child.material.dispose()
          }
        }
      })
      this.scene.remove(group)
    })
    this.groups.clear()
  }
}
