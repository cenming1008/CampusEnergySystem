import * as THREE from 'three'
import gsap from 'gsap'

export default class AlarmSprite {
  sprite: THREE.Sprite
  canvas: HTMLCanvasElement

  constructor(
    text: string,
    position: THREE.Vector3,
    status: 'normal' | 'warning' | 'error' = 'normal'
  ) {
    this.canvas = document.createElement('canvas')
    this.canvas.width = 256
    this.canvas.height = 128
    
    this.updateContent(text, status)

    const texture = new THREE.CanvasTexture(this.canvas)
    const material = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthTest: false
    })

    this.sprite = new THREE.Sprite(material)
    this.sprite.position.copy(position)
    this.sprite.scale.set(20, 10, 1)

    // 悬浮动画
    gsap.to(this.sprite.position, {
      y: position.y + 2,
      duration: 1.5,
      ease: 'power1.inOut',
      repeat: -1,
      yoyo: true
    })
  }

  updateContent(text: string, status: 'normal' | 'warning' | 'error') {
    const ctx = this.canvas.getContext('2d')!
    ctx.clearRect(0, 0, 256, 128)

    // 背景色
    const colors = {
      normal: 'rgba(0, 255, 136, 0.85)',
      warning: 'rgba(255, 170, 0, 0.85)',
      error: 'rgba(255, 51, 85, 0.85)'
    }

    ctx.fillStyle = colors[status]
    ctx.beginPath()
    ctx.roundRect(0, 0, 256, 128, 12)
    ctx.fill()

    // 边框
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.roundRect(2, 2, 252, 124, 10)
    ctx.stroke()

    // 文字
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 24px Microsoft YaHei'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(text, 128, 64)

    // 更新纹理
    if (this.sprite) {
      const texture = (this.sprite.material as THREE.SpriteMaterial).map
      if (texture) texture.needsUpdate = true
    }
  }

  remove() {
    this.sprite.removeFromParent()
    ;(this.sprite.material as THREE.SpriteMaterial).map?.dispose()
    ;(this.sprite.material as THREE.SpriteMaterial).dispose()
  }
}
