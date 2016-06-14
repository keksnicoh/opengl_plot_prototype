from gllib.util import Event
from gllib.renderer.shape import ShapeRenderer, ShapeInstance, Rectangle
from gllib.font import FontRenderer
from gllib.renderer.window import Framebuffer
class PlotterWidget():

    def attach(self, plotter):
        self.plotter = plotter

    def gl_init(self):
        pass

    def run(self):
        pass

    def draw(self):
        pass

class LegendWidget(PlotterWidget):
    INNER_SCALING = 8
    def __init__(self, *args, **kwargs):
        self.font_renderer = None
        self.graphs = []
        self.size = (400, 100)
        self.framebuffer = None
        self.shape_renderer = None
        self.position = (100, 100)
        self.grid = None
        self.plane = None
        self._render_frame = False
        self._is_clicked = False
        self._relative = (0, 0)

    def cursor(self, cursor):
        if self._is_clicked:
            self.position = (cursor[0] - self._relative[0], cursor[1] - self._relative[1])
            self.plane.position = self.position
    def mouse(self, cursor, button, action, mod):
        if not self._is_clicked:
            is_clicked = (
                cursor[0] > self.position[0] and cursor[0] < self.position[0] + self.size[0]
                and cursor[1] > self.position[1] and cursor[1] < self.position[1] + self.size[1])

            if is_clicked:
                if button == 0 and action == 1:
                    self._is_clicked = True
                    self._relative = (cursor[0] - self.position[0], cursor[1] - self.position[1])
                return False


        elif self._is_clicked and button == 0 and action == 0:
            self._is_clicked = False
            return False

    def gl_init(self):

        self.framebuffer = Framebuffer(
            self.plotter.camera,
            self.size,
            capture_size=(self.INNER_SCALING * self.size[0], self.INNER_SCALING * self.size[1]),
            clear_color=[1,1,1,1],
            multisampling = 8,
            blit_texture=True

        )
        self.framebuffer.init()
        self.framebuffer.inner_camera.set_scaling((self.size[0], self.size[1]))
        self.framebuffer.inner_camera.set_screensize((self.INNER_SCALING * self.size[0], self.INNER_SCALING * self.size[1]))
        self.font_renderer = FontRenderer()
        self.font_renderer.set_camera(self.framebuffer.inner_camera)
        self.font_renderer.init()

        self.shape_renderer = ShapeRenderer(self.plotter.camera)
        self.shape_renderer.shapes['default_rectangle'] = Rectangle()
        self.shape_renderer.gl_init()

        self.plane = ShapeInstance('default_rectangle', **{
            'size': self.size,
            'position': self.position,
            'border': {
                'size': 0,
                'color': [0,0,0,1]
            },
            'color': [1,1,1,0],
            'texture': self.framebuffer
        })
        self.shape_renderer.draw_instance(self.plane)

    def _create_shape(self):
        self.font_renderer.clear_texts()

        if len(self.graphs) == 0:
            self.size = (10, 10)
            self._render_frame = True
            return

        offsetx = 50
        yskip = 4
        maxx = 0
        y = 0
        self.grid = []
        gridy = 0
        for gid, graph in self.graphs.items():
            label = graph.label if hasattr(graph, 'label') and graph.label is not None else gid
            text = self.font_renderer.create_text(label, 12, (offsetx, y), enable_simple_tex=True)

            w, h = text.get_boxsize()

            self.grid.append([(0, gridy), (45, gridy + h)])
            gridy += h

            y += h + yskip
            maxx = max(maxx, w)

        self.size = (maxx + offsetx, y+3+yskip)
        self.plane.size = self.size

        self.framebuffer.screensize = self.size
        self.framebuffer.capture_size = (int(self.INNER_SCALING * self.size[0]), int(self.INNER_SCALING * self.size[1]))
        self.framebuffer.init()


        self.font_renderer.set_camera(self.framebuffer.inner_camera)

        self._render_frame = True

    def run(self):
        graphs = self.plotter.graphs
        if graphs != self.graphs:
            self.graphs = graphs
            self._create_shape()

    def update_camera(self):
        self.shape_renderer.update_camera()
    def draw(self):

        if self._render_frame:
            self.font_renderer.set_camera(self.framebuffer.inner_camera)


            self.framebuffer.use()

            self.font_renderer.render()


            for i, graph in enumerate(self.graphs.values()):

                graph.render_legend_graph(self.plotter, self.plotter._plotframe.camera, self.framebuffer.inner_camera, *self.grid[i])

            self.framebuffer.unuse()

            self._render_frame = False

        self.shape_renderer.render()
