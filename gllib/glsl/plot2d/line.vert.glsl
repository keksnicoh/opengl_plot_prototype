/**
 * vertex shader for line plotting
 * note that this shader does not transform into camera
 * space due the geometry shader needs original vertex
 * information.
 * @author Nicolas 'keksnicoh' Heimann
 */
#version /*{$VERSION$}*/

{{{VBO_IN}}}

out         vec4 fragment_color;

uniform     vec4 color;
uniform     float c_scale = 1;
uniform     float time;
uniform     mat3 mat_domain;
uniform     vec2 range;
uniform     vec2 shift;

            vec4 point_color;
            float x;
            float y;
            float z;
            float c;
            vec3 transformed_vertex_position;
            
{{{UNIFORMS}}}

// if color_scheme has glsl_functions attribute
// one should substitute it here
{{{COLOR_FUNCTIONS}}}

void main() {
    point_color = color;

    {{{TRANSFORMATIONS}}} 

    c = c_scale;

    {{{DATA_LAYOUT}}}

    /*{$KERNEL$}*/

    {{{COLOR_SCHEME}}}

    gl_Position = vec4(x+shift.x, y+shift.y, 0, c/c_scale);
}