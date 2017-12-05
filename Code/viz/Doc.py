class RFC:

    def __init__(self, id):
        self.id = id
        self.draft_name = ""
        self.draft_url = ""

    def set_draft_name(self, name):
        self.draft_name = name

    def set_draft_url(self, url):
        self.draft_url = url