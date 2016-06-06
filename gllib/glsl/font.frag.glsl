#version /*{$VERSION$}*/

in      vec2 tex_coord;
flat in float page_id;
in      vec4 color;
out     vec4 out_color;

uniform sampler2DArray tex;

float distance;
float width;
float edge;
float alpha;

void main()
{
    width = 0.45;
    edge = 0.07;
    distance = 1.0-texture(tex, vec3(tex_coord, page_id)).r/255;
    alpha = 1.0-smoothstep(width, width+edge, distance);
    out_color = vec4(color.x,color.y,color.z,color.a*alpha);
}
