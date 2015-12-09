#version /*{$VERSION$}*/

in vec2 fragment_position;
out vec4 fragment_color;
uniform sampler2D tex[1];
/*{{{START_UNIFORMS}}}
{{{UNIFORMS}}}
{{{END_UNIFORMS}}}*/

/*{$FUNCTIONS$}*/

void main() {
    if (fragment_position.x > 9) {}
    fragment_color = texture(tex[0], fragment_position);
    /*{$COLOR_KERNEL$}*/
}

