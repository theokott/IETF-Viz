rx = 150
ry = 50
x_buffer = rx + 20
y_buffer = ry + 20
track_height = 150
track_title_length = 50
area_title_length = 150
date_y_offset = 35
date_x_offset = 70
doc_height = 75
scale_y_offset = 75

colours = ['#ff6666', '#ffb366', '#8cff66', '#66ffb3', '#66d9ff', '#6666ff', '#d966ff', '#ff66d9']
track_colours = ['#ffcccc', '#ffe6cc', '#d9ffcc', '#ccffe6', '#ccf2ff', '#ccccff', '#f2ccff', '#ffccf2']

class DrawingArea:
    def __init__(self, name):
        self.name = name
        self.groups = {}
        self.height = -1

    def add_group(self, group):
        self.groups[group.name] = group

    def adjust_height(self):
        total = 0

        for group in self.groups.values():
            total = total + group.height

        self.height = total

class DrawingGroup:
    def __init__(self, name):
        self.name = name
        self.documents = []
        self.height = -1

    def add_document(self, doc):
        self.documents.append(doc)

    def adjust_height(self):
        self.height = doc_height * len(self.documents)

class DrawingDoc:
    def __init__(self, doc, type):
        self.document = doc
        self.reference_type = type
        self.tooltip = ""

    def set_reference_type(self, type):
        self.reference_type = type

    def set_tooltip(self, tip):
        self.tooltip = tip