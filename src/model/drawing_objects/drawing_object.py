import uuid


class DrawingObject:
    def __init__(self, group_tag):
        self.group_tag = group_tag
        self.unique_tag = str(uuid.uuid4())
        self.unique_text_tag = self.unique_tag+'_text'

    def get_tags(self):
        return (self.group_tag, self.unique_tag)

    def get_text_tags(self):
        return (self.group_tag, self.unique_text_tag)