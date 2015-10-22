from OpenGL.GL import *

def simple_texture(size, format=GL_RGBA, internalFormat=None, parameters=[
    (GL_TEXTURE_MAG_FILTER, GL_LINEAR),
    (GL_TEXTURE_MIN_FILTER, GL_LINEAR)
]):
    """
    creates a simple texture an
    returns its gl_id
    """
    id = glGenTextures(1);

    if internalFormat is None:
        internalFormat = format

    glBindTexture(GL_TEXTURE_2D, id);
    glTexImage2D(GL_TEXTURE_2D, 0, format, size[0], size[1], 0, internalFormat, GL_UNSIGNED_BYTE, None);
    for parameter in parameters:
        glTexParameterf(GL_TEXTURE_2D, *parameter)

    glBindTexture(GL_TEXTURE_2D, 0);
    return id
