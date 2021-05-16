from src.model.drawing_objects.drawing_object import DrawingObject

class Breakline(DrawingObject):
    def __init__(self, x0, y0, x1, y1, group_tag):
        self.__init__(group_tag)
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1