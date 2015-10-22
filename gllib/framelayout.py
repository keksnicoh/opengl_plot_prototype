from gllib.controller import Controller
from gllib.renderer import window
from OpenGL.GL import * 
class FramelayoutController(Controller):

    def __init__(self, rows=None, camera=None):
        Controller.__init__(self, camera) 

        self.rows = list([LayoutRow(r) if type(r) is list else r for r in rows or []])
        self._prepared = False 
        self._frames = None
        self.on_keyboard.append(self.keyboard_callback)
    def init(self):
        Controller.init(self)
        self.camera.on_change_matrix.append(self.rescale_camera)


    def keyboard_callback(self, *args, **kwargs):
        for frame, column in self._frames:
            column.controller.keyboard_callback(*args, **kwargs)

    def rescale_camera(self, camera):
        self.calculate_absolute_values()
        for frame, column in self._frames:
            frame.modelview.set_position(*column.absolute_position)
            frame.update_modelview()

            frame.screensize = [column.absolute_width, column.absolute_height]
            frame.capture_size = [column.absolute_width, column.absolute_height]
            frame.update_camera(self.camera)
        self.cycle()
    def prepare(self):
        self._frames = []
        self.calculate_absolute_values()
        self.init_frames()

    def calculate_absolute_values(self):
        screensize = self.camera.screensize

        factor = self.camera.get_screen_factor()
        columns = []
        relative_rows = []
        relative_rows_percentage = 0
        used_height = 0
        for row in self.rows:
            height, rtype = row.get_height()
            if rtype == 0:
                used_height += height
                row.absolute_height = height
            elif rtype == 1:
                relative_rows.append(row)
                relative_rows_percentage += height
            relative_columns = []
            used_width = 0
            realtive_columns_percentage = 0 
            for column in row.columns:
                width, ctype = column.get_width()
                if ctype == 0:
                    used_width += width 
                    column.absolute_width = width
                else:
                    relative_columns.append(column)
                    realtive_columns_percentage += width
            if len(relative_columns) > 0:
                width_normalize = 1.0/realtive_columns_percentage
                available_width = screensize[0] - used_width
                for column in relative_columns:
                    width, ctype = column.get_width()
                    column.absolute_width = int(round(width_normalize * width * available_width, 0))
        if len(relative_rows) > 0:
            height_normalize = 1.0/relative_rows_percentage
            available_height = screensize[1] - used_height
            for row in relative_rows:
                height, rtype = row.get_height()
                row.absolute_height = int(round(height_normalize * height * available_height, 0))
        abs_y = 0
        for row in self.rows:
            abs_x = 0
            for column in row.columns:
                column.absolute_position = [abs_x, abs_y]
                column.absolute_height = row.absolute_height
                abs_x += column.absolute_width
            abs_y += row.absolute_height




    def init_frames(self):
        current_y = 0;
        for row in self.rows:
            if row.absolute_height is None:
                raise RuntimeError('internal error: absolute_height should not be None')
            current_x = 0
            for column in row.columns:
                if column.absolute_width is None:
                    raise RuntimeError('internal error: absolute_width should not be None')

                frame = window.Framebuffer(
                    camera=self.camera,
                    screensize=[column.absolute_width, column.absolute_height],
                    clear_color=column.clear_color
                )
                controller = column.controller

                self._frames.append((frame, column))
                frame.init()

                frame.modelview.set_position(*column.absolute_position)
                frame.update_modelview()

                current_x += column.absolute_width

                controller.camera = frame.inner_camera
                controller.init()
                controller.host_controller = self
            current_y += row.absolute_height
        self._prepared = True





    def run(self):
        if not self._prepared:
            self.prepare()

        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        
        for frame, column in self._frames:
            frame.use()
            column.controller.cycle()
            frame.unuse()
        
        for frame, co in self._frames:
            frame.render()

class LayoutRow():
    def __init__(self, columns, cheight=None):
        self.columns = list([c if isinstance(c, LayoutColumn) else LayoutColumn(c) for c in columns or []])
        self.cheight = cheight or '100%'
        self.absolute_height = None 

    def get_height(self):
        if type(self.cheight) is str:
            stripped = self.cheight.strip()
            if stripped[-1] == '%':
                return (float(stripped[:-1]), 1)
            else:
                raise ValueError('bad height')

        return (self.cheight, 0)

class LayoutColumn():
    def __init__(self, controller, cwidth=None, clear_color=None):
        self.cwidth = cwidth or '100%'
        self.controller = controller
        self.absolute_width = None
        self.clear_color = clear_color or [1,1,1,1]
        self.absolute_position = None
        self.absolute_height = None 
    def get_width(self):
        if type(self.cwidth) is str:
            stripped = self.cwidth.strip()
            if stripped[-1] == '%':
                return (float(stripped[:-1]), 1)
            else:
                raise ValueError('bad width')

        return (self.cwidth, 0)