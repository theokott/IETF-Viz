# TODO:
#       Enumerations for type

class Reference:

    def __init__(self):
        self.source = ""
        self.target = ""
        self.type = -1

    def set_source(self, source):
        self.source = source

    def set_target(self, target):
        self.target = target

    def set_type(self, ref_type):
        self.type = ref_type
