from gllib.application import GlApplication, GlWindow
from gllib.controller import Controller 
from gllib.renderer.font import FontRenderer, Text, AbsoluteLayout, FloatingLayout
import os
FONT_RESOURCES_DIR = os.path.dirname(os.path.abspath(__file__))+'/../resources/fonts'
from PIL import ImageFont
from OpenGL.GL import *

import numpy



class MyCoolController(Controller):
	def __init__(self, camera=None):
		Controller.__init__(self, camera)

	def init(self):
		print('ich habe init gemacht')
		self.on_pre_cycle.append(self.prepare)
		ft = ImageFont.truetype (FONT_RESOURCES_DIR+"/arial.ttf", 30)

		self.font_renderer = FontRenderer(self.camera, ft)
		self.font_renderer.init()
		
		abs_layout = AbsoluteLayout()
		abs_layout.set_position(20, 50)
		text = abs_layout.add_text("TEXT", x=10, y=10, font=ft)
		abs_layout.add_text(text, x=30, y=30)
		abs_layout.add_text(text, x=100, y=30)

		text2 = abs_layout.add_text("Noch ein text", 10, 200)

		#float_layout = FloatingLayout()
		#float_layout.add_text(text, float=Text.FLOAT_RIGHT)

		self.font_renderer.layouts['absolute'] = abs_layout
		#self.font_renderer.layouts['floating'] = float_layout
		
		#self.font_renderer.add_aligned_text("something", alignment=Text.RIGHT)
		#, (0,0), ImageFont.truetype(FONT_RESOURCES_DIR+"/arial.ttf", 12))
		#self.font_renderer.append_text("sadfsf", text)
		Controller.init(self)

	def prepare(self):
		#print('ich mach prepare')
		pass
		#	text = self.font_renderer.add_text('blablabla', [0,0])
		#	self.font_renderer.add_text('blalal', [text.x, 0])  # PREPARE
		#	self.font_renderer.add_text_right_of('blallla', text)

		#	text = (id 0..n, properties, ICH KENNE FONTRENDERER)
		#	text.set_text('BLALALALA') -> font_render.text_updated(text)

		#	# self.on_text_updated = Event()
		#	# self.on_tect_updated.append(self._text_updated) 
		#	#
		#	# def _text_updated(self, text):
		#	#    self.update_text(id, 'text', pos)


	def run(self):
		#print('RUNRUNRU')
		glClearColor(*[1,1,1,1])
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
		#self.font_renderer.modelview.translate(1,1)
		self.font_renderer.modelview_updated()
		self.font_renderer.render()
		#
		# if self._front
		#
		#


app = GlApplication()
GlApplication.DEBUG = False
window = GlWindow(400, 400)
app.windows.append(window)
window.set_controller(MyCoolController())

app.run()

