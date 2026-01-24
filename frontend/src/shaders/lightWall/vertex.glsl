varying vec3 vPosition;

uniform float uTime;

void main(){
    vec4 viewPosition = viewMatrix * modelMatrix * vec4(position,1);
    gl_Position = projectionMatrix *  viewPosition;
    vPosition = position;
}
