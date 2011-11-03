from google.appengine.ext import db

class stickletUser(db.Model):
    author = db.UserProperty()
    email = db.EmailProperty()
    has_shared = db.StringListProperty()
    connections = db.StringListProperty()
