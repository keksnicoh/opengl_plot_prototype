#version 410

uniform vec4 color = vec4(1, 1, 1, 1);

out vec4 fragment_color;

void main() {
    fragment_color = color;
}