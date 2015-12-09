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
uniform         float width = 0.002;
uniform         float zoom = 1;          
uniform         vec2 initial_scaling = vec2(1,1);  
uniform         vec2 initial_plane_scaling = vec2(1,1);  
                vec2 p[4]; // verticies
                vec2 t[2]; // tangents between 0-1, 2-3
                vec2 m[2];
                float l[2]; 

/**
 * calculates the normal of 2 vec2 
 */
vec2 na(vec2 x0, vec2 x1) 
{
    return normalize(vec2(x0.y-x1.y, x1.x-x0.x));
}
vec2 screen_space(vec4 vertex)
{
    return vec2( vertex.xy / vertex.w ).xy * 1;
}
vec2 v[3];
vec2 n[3];
void main(void)
{
    // prepare

    p[0] = screen_space(gl_in[0].gl_Position);
    p[1] = screen_space(gl_in[1].gl_Position);
    p[2] = screen_space(gl_in[2].gl_Position);
    p[3] = screen_space(gl_in[3].gl_Position);

    v[0] = (p[1]-p[0])/length(p[1]-p[0]);
    v[1] = (p[2]-p[1])/length(p[2]-p[1]);
    v[2] = (p[3]-p[2])/length(p[3]-p[2]);

    n[0] = vec2(-v[0].y, v[0].x);
    n[1] = vec2(-v[1].y, v[1].x);
    n[2] = vec2(-v[2].y, v[2].x);

    //t[0] = normalize(normalize(p[2]-p[1]) + normalize(p[1]-p[0]));
    //t[1] = normalize(normalize(p[3]-p[2]) + normalize(p[2]-p[1]));
    m[0] = (n[0]+n[1])/length(n[0]+n[1]);
    m[1] = (n[1]+n[2])/length(n[1]+n[2]);
   // m[1].x = 0;
    //m[1] = vec2(-t[0].y, t[1].x);
    l[0] = width/(0.0001+dot(m[0], n[1]));
    l[1] = width/(0.0001+dot(m[1], n[1]));
    float p = initial_plane_scaling.x/initial_plane_scaling.y;
    //m[0].x /= 1.0/p*initial_scaling.x/2;
    //m[0].y /= p*initial_scaling.y/2;
    //m[1].x /= 1.0/p*initial_scaling.x/2;
    //m[1].y /= p*initial_scaling.y/2;

    // emit
    color = fragment_color[0];
    coord = vec2(0,1);
    gl_Position = mat_camera*(gl_in[1].gl_Position) + vec4(-m[0]*l[0], 0, 0) ;
    EmitVertex();

    color = fragment_color[1];
    coord = vec2(0,0);
    gl_Position = mat_camera*(gl_in[1].gl_Position) + vec4(m[0]*l[0], 0,0) ;
    EmitVertex();

    color = fragment_color[2];
    coord = vec2(1,1);
    gl_Position = mat_camera*(gl_in[2].gl_Position) + vec4(-m[1].x*l[1],-m[1].y*l[1], 0,0) ;
    EmitVertex();

    color = fragment_color[3];
    coord = vec2(1,0);
    gl_Position = mat_camera*(gl_in[2].gl_Position) + vec4(m[1].x*l[1],m[1].y*l[1], 0,0) ;
    EmitVertex();

    EndPrimitive();
}