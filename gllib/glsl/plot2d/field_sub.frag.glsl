#version 410

in vec2 fragment_position;
out vec4 fragment_color;
uniform sampler2D tex1[1];
uniform sampler2D tex2[1];
uniform vec4 color1;
uniform vec4 color2;
void main() {
    if (fragment_position.x > 9) {}

    mediump vec4 color1 = texture(tex1[0], vec2(fragment_position.x, fragment_position.y));
    mediump vec4 color2 = texture(tex2[0], vec2(fragment_position.x, fragment_position.y));

    fragment_color = 10*vec4(color1.rgb - color2.rgb, color1.a);
}