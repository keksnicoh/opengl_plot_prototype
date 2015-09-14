from application import GlApplication, GlWindow
import controller
def cycle(self):
    print('AAA')

window = GlWindow(600, 600, 'main')
window.set_controller(controller.DebugController())


app = GlApplication()
app.windows.append(window)
#app.windows.append(window2)
app.run()