#version 410

uniform vec4 color = vec4(1, 1, 1, 1);
in vec2 fragment_position;

out vec4 fragment_color;
void main() {
    if (fragment_position.x == 0) {
        discard;
    }
    fragment_color = color;
}