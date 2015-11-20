#version 410

in vec2 fragment_position;
out vec4 fragment_color;
uniform sampler2D tex[1];

void main() {
    if (fragment_position.x > 9) {}
    fragment_color = texture(tex[0], fragment_position);
}