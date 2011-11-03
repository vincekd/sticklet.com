from google.appengine.ext import db

class StickyNoteModel(db.Model):
    author = db.UserProperty()
    content = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    subject = db.StringProperty()
    color = db.StringProperty()
    trash = db.IntegerProperty()
    shared_with = db.StringListProperty()
    shared_with_emails = db.StringListProperty()
    x = db.IntegerProperty()
    y = db.IntegerProperty()
    z = db.IntegerProperty()
    modify_date = db.DateTimeProperty()
    delete_date = db.DateTimeProperty()
    is_list = db.IntegerProperty()

class snModel(StickyNoteModel):
    def to_dict(self):
        return dict({
            "id": unicode(self.key()),
            "content" : self.content,
            "subject" : self.subject,
            "color" : self.color,
            "trash" : self.trash,
            "x" : self.x,
            "y" : self.y,
            "z" : self.z,
            "is_list" : self.is_list,
            "shared_emails" : self.shared_with_emails})

def key(email):
    return db.Key.from_path('StickyNote', email)
