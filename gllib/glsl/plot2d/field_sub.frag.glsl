#version 410

in vec2 fragment_position;
out vec4 fragment_color;
uniform sampler2D tex1[1];
uniform sampler2D tex2[1];
uniform vec4 color1;
uniform vec4 color2;
void main() {
    if (fragment_position.x > 9) {}

    mediump vec4 color1 = texture(tex1[0], fragment_position);
    mediump vec4 color2 = texture(tex2[0], fragment_position);

    fragment_color = vec4(color1.rgb - color2.rgb, color1.a);
}