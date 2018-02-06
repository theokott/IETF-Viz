class DrawingArea:
    def __init__(self, name):
        self.name = name
        self.groups = {}

    def add_group(self, group):
        self.groups[group.name] = group

class DrawingGroup:
    def __init__(self, name):
        self.name = name
        self.documents = []

    def add_document(self, doc):
        self.documents.append(doc)

class DrawingDoc:
    def __init__(self, doc, type):
        self.document = doc
        self.reference_type = type
        self.tooltip = ""

    def set_reference_type(self, type):
        self.reference_type = type

    def set_tooltip(self, tip):
        self.tooltip = tip

colours = ['#ff6666', '#ffb366', '#8cff66', '#66ffb3', '#66d9ff', '#6666ff', '#d966ff', '#ff66d9']
track_colours = ['#ffcccc', '#ffe6cc', '#d9ffcc', '#ccffe6', '#ccf2ff', '#ccccff', '#f2ccff', '#ffccf2']