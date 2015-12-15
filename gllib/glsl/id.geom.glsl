
#version /*{$VERSION$}*/

layout (points)  in;
layout (triangle_strip)   out;
layout (max_vertices = 4) out;

out             vec2 coord;

uniform         mat4 mat_camera;

void main(void)
{

    coord = vec2(0,1);
    gl_Position = mat_camera*(gl_in[0].gl_Position + vec4(-1, 1, 0, 0));
    EmitVertex();

    coord = vec2(0,1);
    gl_Position = mat_camera*(gl_in[0].gl_Position + vec4(1, 1, 0, 0));
    EmitVertex();

    coord = vec2(0,1);
    gl_Position = mat_camera*(gl_in[0].gl_Position + vec4(-1, -1, 0, 0));
    EmitVertex();

    coord = vec2(0,1);
    gl_Position = mat_camera*(gl_in[0].gl_Position + vec4(1, -1, 0, 0));
    EmitVertex();

    EndPrimitive();
}