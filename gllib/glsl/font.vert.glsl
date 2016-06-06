#version /*{$VERSION$}*/

uniform mat4 mat_camera;


in float glyph_rot;
out float geom_glyph_rot;

in vec4 glyph_color;
out vec4 geom_glyph_color;

in float glyph_size;
out float geom_glyph_size;

in int fntobj;
out int geom_fntobj;

in vec2 vertex_position;

void main()
{
    geom_glyph_size = glyph_size;
    geom_fntobj = fntobj;
    geom_glyph_rot = glyph_rot;
    geom_glyph_color = glyph_color;
    gl_Position = vec4(vertex_position, 0, 1);
}