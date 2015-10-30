#version /*{$VERSION$}*/

uniform sampler2D tex;
uniform vec4 color;
uniform bool debug = false;

in vec2 fragTexCoord;
out vec4 finalColor;

void main()
{
    if (debug) {
        finalColor = texture(tex, fragTexCoord);
        finalColor = 1-color*finalColor;
    }
    else {  
        finalColor = texture(tex, fragTexCoord);
        finalColor = color*finalColor;
    }
}
