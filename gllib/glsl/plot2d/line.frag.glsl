/**
 * fragment shader
 * @author Nicolas 'keksnicoh' Heimann 
 */
#version /*{$VERSION$}*/

out             vec4 output_color;
in              vec4 color;
in              vec2 coord;


void main() 
{
    output_color = color;  
    if (coord.y < 1) {
    }

}