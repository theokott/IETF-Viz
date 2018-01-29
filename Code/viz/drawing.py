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