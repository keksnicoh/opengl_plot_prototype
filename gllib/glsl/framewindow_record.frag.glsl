#version 410
in  vec2 frag_tex_coord;
out vec4 output_color;
uniform sampler2D tex[1];
void main() {

    output_color = texture(tex[0], frag_tex_coord);

}