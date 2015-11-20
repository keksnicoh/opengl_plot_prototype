#version 410
uniform mat3 mat_texture;
in  vec2 frag_tex_coord;
out vec4 output_color;

uniform sampler2DMS tex[1];
uniform float border = 1;
uniform float mix_debug = 0;
uniform vec4 color_debug = vec4(0,0,0,0);
uniform int u_samples = 1;
ivec2 coord;
vec2 tex_size;
vec4 color;

void main() {
    tex_size = textureSize(tex[0]);
    coord = ivec2(tex_size*(mat_texture*vec3(frag_tex_coord.x,frag_tex_coord.y, 1)).xy);
    coord.x = coord.x%int(tex_size.x);
    coord.y = coord.y%int(tex_size.y);
    color = vec4(0.0);
    
    for (int i = 0; i < u_samples; i++) {
        color += texelFetch(tex[0], coord, i);
    }
    color /= float(u_samples);


    output_color = mix(
        color,
        color_debug,
        mix_debug
    );
}