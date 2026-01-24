import * as THREE from 'three'
import gsap from 'gsap'

export default class FlyLine {
  group: THREE.Group
  line: THREE.Line
  flyPoints: THREE.Points

  constructor(
    startPoint: THREE.Vector3,
    endPoint: THREE.Vector3,
    color = 0x00ffff,
    height = 30
  ) {
    this.group = new THREE.Group()

    // 计算控制点（贝塞尔曲线）
    const midPoint = new THREE.Vector3(
      (startPoint.x + endPoint.x) / 2,
      height,
      (startPoint.z + endPoint.z) / 2
    )

    // 创建曲线
    const curve = new THREE.QuadraticBezierCurve3(startPoint, midPoint, endPoint)
    const curvePoints = curve.getPoints(100)

    // 底线
    const lineGeometry = new THREE.BufferGeometry().setFromPoints(curvePoints)
    const lineMaterial = new THREE.LineBasicMaterial({
      color,
      transparent: true,
      opacity: 0.3
    })
    this.line = new THREE.Line(lineGeometry, lineMaterial)
    this.group.add(this.line)

    // 飞行粒子
    const flyGeometry = new THREE.BufferGeometry()
    const flyCount = 30
    const positions = new Float32Array(flyCount * 3)
    const sizes = new Float32Array(flyCount)
    
    for (let i = 0; i < flyCount; i++) {
      positions[i * 3] = curvePoints[0].x
      positions[i * 3 + 1] = curvePoints[0].y
      positions[i * 3 + 2] = curvePoints[0].z
      sizes[i] = (flyCount - i) * 0.1
    }

    flyGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    flyGeometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))

    const flyMaterial = new THREE.PointsMaterial({
      color,
      size: 3,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      sizeAttenuation: true
    })

    this.flyPoints = new THREE.Points(flyGeometry, flyMaterial)
    this.group.add(this.flyPoints)

    // 动画
    let progress = { value: 0 }
    gsap.to(progress, {
      value: 1,
      duration: 2,
      ease: 'none',
      repeat: -1,
      onUpdate: () => {
        const positions = this.flyPoints.geometry.attributes.position.array as Float32Array
        for (let i = 0; i < flyCount; i++) {
          const index = Math.floor((progress.value * 100 + i * 2) % 100)
          const point = curvePoints[index] || curvePoints[0]
          positions[i * 3] = point.x
          positions[i * 3 + 1] = point.y
          positions[i * 3 + 2] = point.z
        }
        this.flyPoints.geometry.attributes.position.needsUpdate = true
      }
    })
  }

  remove() {
    this.group.removeFromParent()
    this.line.geometry.dispose()
    ;(this.line.material as THREE.Material).dispose()
    this.flyPoints.geometry.dispose()
    ;(this.flyPoints.material as THREE.Material).dispose()
  }
}
