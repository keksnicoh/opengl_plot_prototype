#version 410

in vec2 vertex_position;
in vec2 texture_coords;
out vec2 fragment_position;
uniform mat4 mat_modelview;
uniform mat4 mat_camera;

void main() {
    gl_Position = mat_camera * mat_modelview * vec4(vertex_position, 0, 1);
    fragment_position = texture_coords;
}