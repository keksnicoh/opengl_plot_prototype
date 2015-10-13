/**
 * vertex shader for line plotting
 * note that this shader does not transform into camera
 * space due the geometry shader needs original vertex
 * information.
 * @author Nicolas 'keksnicoh' Heimann
 */
#version /*{$VERSION$}*/

in          vec3 vertex_position;
out         vec4 fragment_color;

uniform     vec4 color;
uniform     float c_scale = 1;
uniform     float time;
uniform     mat3 mat_domain;

            vec4 point_color;
            float x;
            float y;
            float z;
            float c;
            vec3 transformed_vertex_position;

/*{$UNIFORMS$}*/

void main() {
    point_color = color;

    transformed_vertex_position = mat_domain * vertex_position;

    c = c_scale;
    x = transformed_vertex_position.x;
    y = transformed_vertex_position.y;
    z = transformed_vertex_position.z;

    /*{$KERNEL$}*/

    fragment_color = point_color;
    gl_Position = vec4(x, y, z, c/c_scale);
}