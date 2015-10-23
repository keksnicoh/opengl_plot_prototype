#version /*{$VERSION$}*/
uniform mat4 mat_modelview;
uniform mat4 mat_camera;

in vec2 vertex_position;
in vec2 vertex_texcoord;
out vec2 fragTexCoord;

void main()
{
    fragTexCoord = vertex_texcoord;
    gl_Position = mat_camera * mat_modelview * vec4(vertex_position, 0.0, 1.0);
}