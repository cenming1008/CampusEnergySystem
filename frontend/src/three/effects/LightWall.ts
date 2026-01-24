import * as THREE from 'three'
import gsap from 'gsap'

// 光墙着色器
const vertexShader = `
varying vec3 vPosition;
uniform float uTime;

void main(){
    vec4 viewPosition = viewMatrix * modelMatrix * vec4(position,1);
    gl_Position = projectionMatrix * viewPosition;
    vPosition = position;
}
`

const fragmentShader = `
varying vec3 vPosition;
uniform vec3 uColor;
uniform float uHeight;

void main(){
   float strength = (vPosition.y+uHeight/2.0)/uHeight;
   gl_FragColor = vec4(uColor, 1.0 - strength);
}
`

export default class LightWall {
  mesh: THREE.Mesh
  geometry: THREE.CylinderGeometry
  material: THREE.ShaderMaterial

  constructor(
    radius = 5,
    height = 2,
    position = { x: 0, z: 0 },
    color = 0x00ff00
  ) {
    this.geometry = new THREE.CylinderGeometry(
      radius,
      radius,
      height,
      32,
      1,
      true
    )
    
    this.material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      transparent: true,
      side: THREE.DoubleSide,
      depthWrite: false,
      uniforms: {
        uHeight: { value: height },
        uColor: { value: new THREE.Color(color) },
        uTime: { value: 0 }
      }
    })

    this.mesh = new THREE.Mesh(this.geometry, this.material)
    this.mesh.position.set(position.x, height / 2, position.z)

    // 脉动动画
    gsap.to(this.mesh.scale, {
      x: 1.5,
      z: 1.5,
      duration: 1.5,
      ease: 'power1.inOut',
      repeat: -1,
      yoyo: true
    })
  }

  remove() {
    this.mesh.removeFromParent()
    this.material.dispose()
    this.geometry.dispose()
  }
}
