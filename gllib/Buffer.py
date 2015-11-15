class VertexBuffer():
    pass

class VertexArray():
    def __init__(attributes=None):
        self.attributes = []

    def enable_attribute(self, attribute, vertex_buffer):
        pass


vao = VertexArray(VertexBuffer(1000))
vao.enable_attribute(program.attributes['vertex_data'], VertexBuffer(1000))
vao['vertex_data'].buffer_data(np.array([]))


object_renderer = o
renderer_id = object_renderer.add_object(Rectangle(100, 200))
object_renderer.get_object(renderer_id).set_texture(Texture(...))
object_renderer.add_object()
