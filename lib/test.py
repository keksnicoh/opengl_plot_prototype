from application import GlApplication, GlWindow
import controller

window = GlWindow(600, 600, 'main')
window.set_controller(controller.DebugController())
window2 = GlWindow(300, 300, 'main')
window2.set_controller(controller.DebugController())

app = GlApplication()
app.windows.append(window)
app.windows.append(window2)
app.run()