#version 410

uniform vec4 color = vec4(1, 1, 1, 1);
in vec2 fragment_position;
uniform float mix_texture = 1;
out vec4 fragment_color;
uniform sampler2D tex[1];
void main() {

    fragment_color = mix(color, texture(tex[0], fragment_position),mix_texture);

}