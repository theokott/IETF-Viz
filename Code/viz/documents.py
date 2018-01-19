# TODO:
#       Enumerations for type


class Reference:
    def __init__(self):
        self.id = -1
        self.source = ""
        self.target = ""
        self.type = -1
        self.group = ""

    def set_source(self, source):
        self.source = source

    def set_target(self, target):
        self.target = target

    def set_type(self, ref_type):
        self.type = ref_type

    def set_group(self, group):
        self.group = group


class RFC:
    def __init__(self, id):
        self.id = id
        self.draft_name = ""
        self.draft_url = ""
        self.group = ""
        self.area = ""
        self.title = ""

    def set_draft_name(self, name):
        self.draft_name = name

    def set_draft_url(self, url):
        self.draft_url = url

    def set_group(self, working_group):
        self.group = working_group

    def set_area(self, group_area):
        self.area = group_area

    def set_title(self, title):
        self.title = title
