class AlignedLayout():
    def __init__(self, camera, min_screensize=(0.0, 0.0)):
        self.texts = []
        self._update_set = set()
        self._camera = camera 
        self._last_screensize = None
        self.min_screensize = min_screensize

    @property
    def camera(self):
        return self._camera

    @camera.setter
    def camera(self, camera):
        self._camera = camera
        for x in self.texts:
            self._update_set.add(x)

    def add_text(self, text, *args):
        obj = (text, args)
        self.texts.append(obj)
        self._update_set.add(obj)

    def update_layout(self):
        screensize = (
            max(self.min_screensize[0], self.camera.screensize[0]),
            max(self.min_screensize[1], self.camera.screensize[1]))

        if self._last_screensize != screensize:
            for x in self.texts:
                self._update_set.add(x)

        while len(self._update_set):
            text, modes = self._update_set.pop()

            for mode in modes:
                if type(mode) is str:
                    mode = (mode, )

                if mode[0] == 'x-center':
                    w, h = text.get_boxsize()
                    xc = float(screensize[0])/2.0 - float(w)/2.0
                    text.position = (xc, text.position[1])
                elif mode[0] == 'y-center':
                    w, h = text.get_boxsize()
                    yc = float(screensize[1])/2.0 + float(h)/2.0
                    text.position = (text.position[0], yc)
                elif mode[0] == 'bottom':
                    if len(mode) < 2:
                        mode = (mode[0], 0)
                    text.position = (text.position[0], screensize[1] - mode[1] - 20)


        self._last_screensize = screensize


