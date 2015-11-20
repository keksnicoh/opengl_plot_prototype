#version 410

in vec2 vertex_position;
in vec2 texture_position;
out vec2 fragment_position;
uniform mat3 mat_domain;
uniform mat4 mat_camera;
uniform float zoom;
void main() {
    fragment_position = texture_position;
    gl_Position = mat_camera * vec4(mat_domain * vec3(vertex_position.xy, 1), 1);
}