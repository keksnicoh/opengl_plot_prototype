#version 410

in vec3 vertex_position;
uniform mat4 mat_modelview;
uniform mat4 mat_camera;

void main() {
    gl_Position = mat_camera * mat_modelview * vec4(vertex_position, 1);
}