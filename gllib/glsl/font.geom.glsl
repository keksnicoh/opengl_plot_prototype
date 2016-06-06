#version /*{$VERSION$}*/

struct glyph {
  vec4 pos;
  vec4 size;
  vec4 offset;
  float page;
  float xadvance;
  
  float c;
};
layout (std140) uniform ubo_font_objects
{ 
    glyph glyphs[$n$];
};

layout (points)  in;
layout (triangle_strip)   out;
layout (max_vertices = 4) out;

in       float geom_glyph_size[1];
in       int   geom_fntobj[1];
in       float geom_glyph_rot[1];
in       vec4  geom_glyph_color[1];
out      vec2  tex_coord;
out      vec4  color;
flat out float page_id;

uniform float  fontsize_real;
uniform mat4   mat_camera;
uniform vec2   tex_scale;

float xwidth;
float ywidth;
float yfactor;
vec4 pos;
float sizefactor;
mat4 glyph_rotation;

float xo, yo;

glyph current;
void main(void)
{
    glyph_rotation[0] = vec4(cos(geom_glyph_rot[0]),-sin(geom_glyph_rot[0]),0,0);
    glyph_rotation[1] = vec4(sin(geom_glyph_rot[0]),cos(geom_glyph_rot[0]),0,0);
    glyph_rotation[2] = vec4(0,0,1,0);
    glyph_rotation[3] = vec4(0,0,0,1);

    current = glyphs[geom_fntobj[0]];
    sizefactor = geom_glyph_size[0]/fontsize_real;

    xo = sizefactor*current.offset.x;
    yo = sizefactor*current.offset.y;
    xwidth = sizefactor*current.size.x;
    ywidth = sizefactor*current.size.y;

    // lower left - to upper left
    gl_Position = mat_camera*(gl_in[0].gl_Position + glyph_rotation*vec4(xo, ywidth+yo,0,0));
    tex_coord = vec2(tex_scale.x*current.pos.x,tex_scale.x*(current.pos.y+current.size.y));
    color=geom_glyph_color[0];
    page_id=current.page;
    EmitVertex();

    // upper left - to upper right
    gl_Position = mat_camera*(gl_in[0].gl_Position + glyph_rotation*vec4(xwidth+xo, ywidth+yo,0,0));
    tex_coord = vec2(tex_scale.x*(current.pos.x+current.size.x),tex_scale.x*(current.pos.y+current.size.y));
    color=geom_glyph_color[0];
    page_id=current.page;
    EmitVertex();

    // upper right - to lower left
    gl_Position = mat_camera*(gl_in[0].gl_Position + glyph_rotation*vec4(xo, yo, 0,0));
    tex_coord = vec2(tex_scale.x*current.pos.x, tex_scale.x*current.pos.y);
    color=geom_glyph_color[0];
    page_id=current.page;
    EmitVertex();

    // lower left - to lower right
    gl_Position = mat_camera*(gl_in[0].gl_Position + glyph_rotation*vec4(xwidth+xo, yo, 0,0));
    tex_coord = vec2(tex_scale.x*(current.pos.x+current.size.x), tex_scale.x*current.pos.y);
    color=geom_glyph_color[0];
    page_id=current.page;
    EmitVertex();

    EndPrimitive();
}