#version /*{$VERSION$}*/

in float vertex_position;
uniform mat4 mat_camera;

void main() {
    gl_Position = vec4(0, vertex_position, 0, 1);
}