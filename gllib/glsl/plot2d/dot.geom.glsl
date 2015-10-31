/**
 * thick line geometry shader.
 * note that the geometry shader transforms the emitted verticies
 * into camera space. otherwise the line thickness will change due
 * to the used method to generate verticies.
 * @author Nicolas 'keksnicoh' Heimann 
 */
#version /*{$VERSION$}*/

layout (points)  in;
layout (triangle_strip)   out;
layout (max_vertices = 4) out;

out             vec4 color;
out             vec2 coord;
in              vec4 fragment_color[1];

uniform         mat4 mat_camera;
uniform         float width = 2;
uniform         float zoom = 1;          
uniform         vec2 initial_scaling = vec2(1,1);  

float l;
/**
 * calculates the normal of 2 vec2 
 */
vec2 n(vec2 x0, vec2 x1) 
{
    return normalize(vec2(x0.y-x1.y, x1.x-x0.x));
}

void main(void)
{
    l = width/initial_scaling[0]/zoom;
    // emit
    color = fragment_color[0];
    coord = vec2(0,1);
    gl_Position = mat_camera*(gl_in[0].gl_Position + vec4(-l, l, 0, 0));
    EmitVertex();
    color = fragment_color[0];
    coord = vec2(0,l);
    gl_Position = mat_camera*(gl_in[0].gl_Position + vec4(l, l, 0, 0));
    EmitVertex();
    color = fragment_color[0];
    coord = vec2(0,l);
    gl_Position = mat_camera*(gl_in[0].gl_Position + vec4(-l, -l, 0, 0));
    EmitVertex();
    color = fragment_color[0];
    coord = vec2(0,l);
    gl_Position = mat_camera*(gl_in[0].gl_Position + vec4(l, -l, 0, 0));
    EmitVertex();

    EndPrimitive();
}