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
uniform         mat4 mat_outer_camera;

uniform         float width = .25;

                vec2 p[4]; // verticies
                vec2 m[2];
                float l[2]; 
                vec2 v[3];
                vec2 n[3];

void main(void)
{
    // prepare  
    p[0] = (mat_camera*gl_in[0].gl_Position).xy;
    p[1] = (mat_camera*gl_in[1].gl_Position).xy;
    p[2] = (mat_camera*gl_in[2].gl_Position).xy;
    p[3] = (mat_camera*gl_in[3].gl_Position).xy;

    v[0] = (p[1]-p[0])/length(p[1]-p[0]);
    v[1] = (p[2]-p[1])/length(p[2]-p[1]);
    v[2] = (p[3]-p[2])/length(p[3]-p[2]);

    n[0] = vec2(-v[0].y, v[0].x);
    n[1] = vec2(-v[1].y, v[1].x);
    n[2] = vec2(-v[2].y, v[2].x);

    m[0] = vec2((n[0]+n[1]).x/length(n[0]+n[1]),(n[0]+n[1]).y/length(n[0]+n[1]));
    m[1] = vec2((n[1]+n[2]).x/length(n[1]+n[2]),(n[1]+n[2]).y/length(n[1]+n[2]));

    l[0] = 1.0/(0.0001+dot(m[0], n[1]));
    l[1] = 1.0/(0.0001+dot(m[1], n[1]));
    
    // emmit
    color = fragment_color[0];
    coord = vec2(0,1);
    gl_Position = mat_camera*(gl_in[1].gl_Position) + width*mat_outer_camera*vec4(-m[0].x*l[0],+m[0].y*l[0], 0, 0) ;
    EmitVertex();

    color = fragment_color[1];
    coord = vec2(0,0);
    gl_Position = mat_camera*(gl_in[1].gl_Position) + width*mat_outer_camera*vec4(m[0].x*l[0],-m[0].y*l[0], 0,0) ;
    EmitVertex();

    color = fragment_color[2];
    coord = vec2(1,1);
    gl_Position = mat_camera*(gl_in[2].gl_Position) + width*mat_outer_camera*vec4(-m[1].x*l[1],+m[1].y*l[1], 0,0) ;
    EmitVertex();

    color = fragment_color[3];
    coord = vec2(1,0);
    gl_Position = mat_camera*(gl_in[2].gl_Position) + width*mat_outer_camera*vec4(m[1].x*l[1],-m[1].y*l[1], 0,0) ;
    EmitVertex();

    EndPrimitive();
}