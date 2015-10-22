#version 410
uniform mat3 mat_texture;
in  vec2 frag_tex_coord;
out vec4 output_color;

uniform sampler2D tex[1];
uniform float border = 1;
uniform float mix_debug = 0;
uniform vec4 color_debug = vec4(0,0,0,0);
void main() {
    output_color = mix(
        texture(tex[0], (mat_texture*vec3(frag_tex_coord.x,frag_tex_coord.y,1)).xy),
        color_debug,
        mix_debug
    );
}