"""
@author Nicolas 'keksnicoh' Heimann <nicolas.heimann@gmail.com>
"""
from .controller import Controller
from .util import CommandQueue, signal
from .camera import Camera2d

from OpenGL.GL import *
from glfw import *
from termcolor import colored
import logging 
import sys
class GlApplication():
    """
    initializes opengl & glfw. handles glfw windows
    and route events to windows
    """
    def __init__(self):
        """general window configuration"""
        self.exit     = False
        self.windows  = []

        GlApplication._dbg("init GLFW", '...')
        self.initGlfw()
        GlApplication._dbg("load {}".format(colored('OPENGL_CORE_PROFILE 4.10', 'red')), '...')
        self.initGlCoreProfile()

        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)
        
    def initGlCoreProfile(self):
        """
        setup opengl 4.1
        """
        glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
        glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 1);
        glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
        glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

    def run(self):
        """
        runs the application 
        """
        # initialize windows

        pos_x = 50
        pos_y = 150
        for window in self.windows:
            GlApplication._dbg('initialize glfw window', '...')
            window.init_glfw()
            window.set_position(pos_x, pos_y)
            pos_x += window.width + 10

        GlApplication._dbg('  + Vendor             {}'.format(colored(glGetString(GL_VENDOR), 'cyan')))
        GlApplication._dbg('  + Opengl version     {}'.format(colored(glGetString(GL_VERSION), 'cyan')))
        GlApplication._dbg('  + GLSL Version       {}'.format(colored(glGetString(GL_SHADING_LANGUAGE_VERSION), 'cyan')))
        GlApplication._dbg('  + Renderer           {}'.format(colored(glGetString(GL_RENDERER), 'cyan')))
        GlApplication._dbg('  + GLFW3              {}'.format(colored(glfwGetVersion(), 'cyan')))
        GlApplication._dbg("application is ready to use.", 'OK')
        
        for window in self.windows:
            window.make_context()
            window.init()

        # main cycle
        while self.active():
            glfwPollEvents()
            for window in self.windows:
                window.make_context()
                if window.active():
                    window.event_queue()
                    window.cycle()
                else:
                    GlApplication._dbg('close window', '...')
                    window.destroy()
                    self.windows.remove(window)
                    GlApplication._dbg('window closed', 'OK')

        self.terminate()

    def initGlfw(self):
        """initialize glfw"""
        if not glfwInit(): 
            raise RuntimeError('glfw.Init() error')

    def active(self):
        if self.exit:
            return False
        if not len(self.windows):
            return False
        if not self.windows[0].active():
            return False 
        return True

    def terminate(self):
        GlApplication._dbg("shutdown", '...')
        glfwTerminate()
        GlApplication._dbg("goodbye", 'OK')


    @classmethod
    def _dbg(cls, text, state=None):
        if state is not None:
            if state == 'OK':   state = colored(state, 'green')
            if state == 'FAIL': state = colored(state, 'red')
            if state == '...':  state = colored(state, 'yellow')

            text = '[{}] {}'.format(state, text)
        print(text)

class GlWindow():
    """
    glfw window wrapper. 

    a window must have a controller, all events will be redirected
    into the given controller. a GlWindow does not render something,
    it is the adapter between a Controller and Glfw. 
    """
    def __init__(self, width, height, title='no title'):
        """
        basic state initialization.
        """
        self.width = width
        self.height = height
        self.title = title 
        self.x = 0
        self.y = 0

        self.controller = Controller(Camera2d((width, height)))
        self.event_queue = CommandQueue()

        self._glfw_window = None
        self._glfw_initialized = False
        self._active = True
        
    def init_glfw(self):
        """
        glfw initialization.
        """
        self._glfw_window = glfwCreateWindow(self.width, self.height, self.title)
        if not self._glfw_window:
            raise RuntimeError('glfw.CreateWindow() error')
        self._glfw_initialized = True

    def init(self):
        """
        initializes controller and events 
        """
        self.controller.init()
        glfwMakeContextCurrent(self._glfw_window)
        glfwSetScrollCallback(self._glfw_window, self.event_queue.queue(self.scroll_callback))
        glfwSetMouseButtonCallback(self._glfw_window, self.event_queue.queue(self.mouse_callback))
        glfwSetWindowSizeCallback(self._glfw_window, self.resize_callback)

    def set_controller(self, controller):
        """
        sets a controller. if controller has no camera
        this method will configure the camera of the last 
        controller
        """
        # inizialize camera if not camera is configured yet
        if controller.camera is None:
            controller.camera = self.controller.camera

        # link on_post_cycle with swapping glfw
        controller.on_post_render.append(self.swap)
        self.controller = controller

    def resize_callback(self, win, width, height):
        self.event_queue.queue(self.resize_callback)
        self.make_context()
        self.controller.camera.set_screensize((width, height))
    
    def swap(self):
        glfwSwapBuffers(self._glfw_window)

    def set_position(self, x, y):
        glfwSetWindowPos(self._glfw_window, int(x), int(y))
        self.x = x
        self.y = y

    def make_context(self):
        glfwMakeContextCurrent(self._glfw_window)
        
    def cycle(self):
        self.controller.cycle()

    def destroy(self):
        self.controller.on_destroy()
        glfwDestroyWindow(self._glfw_window)

    def active(self):
        return self._active and not glfwWindowShouldClose(self._glfw_window)

    def scroll_callback(self, win, bla, scrolled):
        print('scrolled', win, bla, scrolled)

    def mouse_callback(self, win, button, action, mod):
        print('mouse', win, button, action, mod)

    def onKeyboard(self, win, key, scancode, action, mods):
        print('keyboard', win, key, scancode, action, mods)


