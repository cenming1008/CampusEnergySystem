import * as THREE from 'three'
import gsap from 'gsap'

// 雷达扫描着色器
const vertexShader = `
varying vec2 vUv;
void main(){
    vec4 viewPosition = viewMatrix * modelMatrix * vec4(position,1);
    gl_Position = projectionMatrix * viewPosition;
    vUv = uv;
}
`

const fragmentShader = `
varying vec2 vUv;
uniform float uTime;
uniform vec3 uColor;

mat2 rotate2d(float _angle){
    return mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle));
}

void main(){
    vec2 newUv = rotate2d(uTime*6.28)*(vUv-0.5);
    newUv = newUv + 0.5;

    float distanceToCenter = distance(newUv,vec2(0.5));
    float strength = step(0.5,distanceToCenter);
    strength = 1.0 - strength;
    
    float angle = atan(newUv.x-0.5,newUv.y-0.5);
    angle = angle + 3.14;
    angle = angle / 6.28;

    gl_FragColor = vec4(uColor, angle*strength);
}
`

export default class LightRadar {
  mesh: THREE.Mesh
  geometry: THREE.PlaneGeometry
  material: THREE.ShaderMaterial

  constructor(radius = 10, position = { x: 0, z: 0 }, color = '#00ffff') {
    this.geometry = new THREE.PlaneGeometry(1, 1)
    
    this.material = new THREE.ShaderMaterial({
      uniforms: {
        uColor: { value: new THREE.Color(color) },
        uTime: { value: 0 }
      },
      vertexShader,
      fragmentShader,
      transparent: true,
      side: THREE.DoubleSide,
      depthWrite: false
    })

    this.mesh = new THREE.Mesh(this.geometry, this.material)
    this.mesh.position.set(position.x, 0.5, position.z)
    this.mesh.rotation.x = -Math.PI / 2
    this.mesh.scale.set(radius, radius, 1)

    // 旋转动画
    gsap.to(this.mesh.rotation, {
      z: -Math.PI * 2,
      ease: 'none',
      repeat: -1,
      duration: 2
    })
  }

  remove() {
    this.mesh.removeFromParent()
    this.material.dispose()
    this.geometry.dispose()
  }
}
