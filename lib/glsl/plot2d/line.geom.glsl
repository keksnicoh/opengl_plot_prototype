/**
 * thick line geometry shader.
 * note that the geometry shader transforms the emitted verticies
 * into camera space. otherwise the line thickness will change due
 * to the used method to generate verticies.
 * @author Nicolas 'keksnicoh' Heimann 
 */
#version /*{$VERSION$}*/

layout (lines_adjacency)  in;
layout (triangle_strip)   out;
layout (max_vertices = 4) out;

out             vec4 color;
out             vec2 coord;
in              vec4 fragment_color[4];

uniform         mat4 mat_camera;
uniform         float width = 0.02;
uniform         vec2 plotplane_screensize;
                
                vec2 p[4]; // verticies
                vec2 t[2]; // tangents between 0-1, 2-3
                vec2 m[2];
                float l[2]; 

/**
 * calculates the normal of 2 vec2 
 */
vec2 n(vec2 x0, vec2 x1) 
{
    return normalize(vec2(x0.y-x1.y, x1.x-x0.x));
}

void main(void)
{
    // prepare
    p[0] = gl_in[0].gl_Position.xy;
    p[1] = gl_in[1].gl_Position.xy;
    p[2] = gl_in[2].gl_Position.xy;
    p[3] = gl_in[3].gl_Position.xy;
    t[0] = normalize(normalize(p[2]-p[1]) + normalize(p[1]-p[0]));
    t[1] = normalize(normalize(p[3]-p[2]) + normalize(p[2]-p[1]));
    m[0] = vec2(-t[0].y, t[0].x);
    m[1] = vec2(-t[1].y, t[1].x);
    l[0] = width/dot(m[0], n(p[0], p[1]));
    l[1] = width/dot(m[1], n(p[1], p[2]));

    // emit
    color = fragment_color[0];
    coord = vec2(0,1);
    gl_Position = mat_camera*(gl_in[1].gl_Position + vec4(-m[0]*l[0], 0, 0)) ;
    EmitVertex();

    color = fragment_color[1];
    coord = vec2(0,0);
    gl_Position = mat_camera*(gl_in[1].gl_Position + vec4(m[0]*l[0], 0,0)) ;
    EmitVertex();

    color = fragment_color[2];
    coord = vec2(1,1);
    gl_Position = mat_camera*(gl_in[2].gl_Position + vec4(-m[1]*l[1], 0,0)) ;
    EmitVertex();

    color = fragment_color[3];
    coord = vec2(1,0);
    gl_Position = mat_camera*(gl_in[2].gl_Position + vec4(m[1]*l[1], 0,0)) ;
    EmitVertex();

    EndPrimitive();
}