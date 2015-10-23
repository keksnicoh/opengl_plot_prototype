#version /*{$VERSION$}*/

uniform sampler2D tex;
uniform vec4 color;

in vec2 fragTexCoord;
out vec4 finalColor;

void main()
{
    finalColor = texture(tex, fragTexCoord);
    finalColor = color*finalColor;
}