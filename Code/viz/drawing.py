class DrawingArea:
    def __init__(self, name):
        self.name = name
        self.groups = {}

    def add_group(self, group):
        self.groups[group.name] = group

class DrawingGroup:
    def __init__(self, name):
        self.name = name
        self.references = []

    def add_reference(self, doc):
        self.references.append(doc)


colours = ['#ff6666', '#ffb366', '#8cff66', '#66ffb3', '#66d9ff', '#6666ff', '#d966ff', '#ff66d9']
track_colours = ['#ffcccc', '#ffe6cc', '#d9ffcc', '#ccffe6', '#ccf2ff', '#ccccff', '#f2ccff', '#ffccf2']