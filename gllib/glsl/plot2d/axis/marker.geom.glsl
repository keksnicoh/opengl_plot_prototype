#version /*{$VERSION$}*/

layout (points)  in;
layout (triangle_strip)   out;
layout (max_vertices = 4) out;

uniform         mat4 mat_camera;
uniform         mat4 mat_outer_camera;

uniform float border = 2;

void main(void)
{
 

    gl_Position = mat_camera*(gl_in[0].gl_Position + vec4(-10, 0,0, 0)) + mat_outer_camera*vec4(0, border, 0, 0);
    EmitVertex();

    gl_Position = mat_camera*(gl_in[0].gl_Position + vec4(10, 0,0, 0)) + mat_outer_camera*vec4(0, border, 0, 0);
    EmitVertex();

    gl_Position = mat_camera*(gl_in[0].gl_Position + vec4(-10, 0,0, 0)) + mat_outer_camera*vec4(0, -border, 0, 0);
    EmitVertex();

    gl_Position = mat_camera*(gl_in[0].gl_Position + vec4(10, 0,0, 0)) + mat_outer_camera*vec4(0, -border, 0, 0);
    EmitVertex();

    EndPrimitive();
}