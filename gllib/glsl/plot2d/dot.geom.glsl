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
uniform         vec2 initial_plane_scaling = vec2(1,1);  

uniform mat4 mat_outer_camera;
uniform         mat4 mat_camera;
uniform float width;

void main(void)
{
    // emit
    color = fragment_color[0];
    coord = vec2(0,1);
    gl_Position = mat_camera*(gl_in[0].gl_Position) + mat_outer_camera*vec4(-width, width, 0, 0);
    EmitVertex();
    color = fragment_color[0];
    coord = vec2(0,1);
    gl_Position = mat_camera*(gl_in[0].gl_Position) + mat_outer_camera*vec4(width, width, 0, 0);
    EmitVertex();
    color = fragment_color[0];
    coord = vec2(0,1);
    gl_Position = mat_camera*(gl_in[0].gl_Position) + mat_outer_camera*vec4(-width, -width, 0, 0);
    EmitVertex();
    color = fragment_color[0];
    coord = vec2(0,1);
    gl_Position = mat_camera*(gl_in[0].gl_Position) + mat_outer_camera*vec4(width, -width, 0, 0);
    EmitVertex();

    EndPrimitive();
}