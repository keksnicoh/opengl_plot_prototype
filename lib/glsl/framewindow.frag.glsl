#version 410
uniform mat3 mat_texture;
in  vec2 frag_tex_coord;
out vec4 output_color;

uniform sampler2D tex[1];

void main() {
    output_color = texture(tex[0], (mat_texture*vec3(frag_tex_coord.x,frag_tex_coord.y,1)).xy);
}