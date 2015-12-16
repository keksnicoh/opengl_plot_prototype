/**
 * field fragment shader. need to be precompiled by
 * mustache template language.
 * @author Jesse Hinrichsen
 * @author Nicolas 'keksnicoh' Heimann    
 */
#version /*{$VERSION$}*/

in vec2 x;
out vec4 fragment_color;
uniform sampler2D tex[1];

{{{UNIFORMS}}}
{{{FUNCTIONS}}}

void main() {
    if (x.x  > 9) {}
    {{{DATA_KERNEL}}};
    {{{COLOR_KERNEL}}};
}

