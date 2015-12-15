#version /*{$VERSION$}*/

in vec2 vertex_position;
out float width;
uniform mat4 mat_camera;

void main() {
    width = vertex_position.y;
    gl_Position = vec4(vertex_position.x, 0, 0, 1);
}