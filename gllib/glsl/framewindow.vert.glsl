#version 410
in  vec2 vertex_position;
in  vec2 text_coord;
out vec2 frag_tex_coord;

uniform mat4 mat_camera;
uniform mat4 mat_modelview; 

void main() {
    frag_tex_coord = text_coord;
    gl_Position = mat_camera*mat_modelview*vec4(vertex_position, 0, 1); 
}