import os
from google.appengine.dist import use_library
use_library('django', '1.2')

import logging
import cgi
import datetime
import sys
import wsgiref.handlers
import urlparse
import string

import stickynote
import sticklet_users

from django.utils import simplejson as json

from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import channel
from google.appengine.api import mail
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from webob.multidict import MultiDict, UnicodeMultiDict, NestedMultiDict, NoVars

class Note(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            note = stickynote.snModel(parent=stickynote.key(user.email()))
            note.author = user
            note.content = ""
            note.subject = "Sticklet"
            note.color = "#FFF79A"
            note.trash = 0
            note.is_list = 0
            note.shared_with_emails.append( user.email() )
            note.x = int ( self.request.get( 'x' ) )
            note.y = int ( self.request.get( 'y' ) )
            note.z = int ( self.request.get( 'z' ) )
            note.put()
            self.response.out.write(json.dumps(note.to_dict()))
            memcache.delete( user.user_id() + "_notes" )
            sentTo( note, [user.user_id()], self.request.get( 'from' ) )
        else:
            self.error(401)
            self.response.out.write("Not logged in.")

    def get(self):
        user = users.get_current_user()
        if user:
            note_query = memcache.get( user.user_id() + "_notes")
            if note_query is not None:
                self.response.out.write( note_query )
            else:    
                notes_query = stickynote.snModel.all().ancestor(
                    stickynote.key(user.email()))
                notes_query.filter( "trash = ", 0 ).order('z')

                min_z = 0
                arr = []
                for note in notes_query:
                    if note.z != min_z:
                        note.z = min_z
                        if user.email() not in note.shared_with_emails:
                            note.shared_with_emails.insert( 0, user.email() )
                        note.put()
                    arr.append ( note.to_dict() )
                    min_z = min_z + 1

                notes = json.dumps( arr )
                memcache.add( user.user_id() + "_notes", notes )
                self.response.out.write( notes )

        else:
            self.error( 401 )
            self.response.out.write( "Not logged in." )

    def put(self):
        user = users.get_current_user()
        if user:
            dict =  json.loads ( self.request.body )
            cur = ""
            for note in dict:
                db_n = stickynote.db.get( note['id'] )
                if db_n:
                    change = False
                    susers = [user.user_id()]
                    if 'content' in note:
                        db_n.content = note['content']
                        change = True
                    if 'subject' in note:
                        db_n.subject = note['subject']
                        change = True
                    if 'is_list' in note:
                        db_n.is_list = int(note['is_list'])
                        change = True
                    if db_n.author.user_id() == user.user_id():
                        if 'color' in note:
                            db_n.color = note['color']
                        if 'x' in note:
                            db_n.x = int(note['x'])
                        if 'y' in note:
                            db_n.y = int(note['y'])
                        if 'z' in note:
                            db_n.z = int(note['z'])
                    else:
                        if 'color' in note or 'x' in note or 'y' in note or 'z' in note:
                            for sd in db_n.shared_with:
                                p = json.loads( sd )
                                if p['id'] == user.user_id():
                                    if 'color' in note:
                                        p['color'] = note['color']
                                    if 'x' in note:
                                        p['x'] = int(note['x'])
                                    if 'y' in note:
                                        p['y'] = int(note['y'])
                                    if 'z' in note:
                                        p['z'] = int(note['z'])
                                    db_n.shared_with.remove( sd )
                                    db_n.shared_with.append( json.dumps( p ) )
                                    break
                    if change:
                        if db_n.author.user_id() not in susers:
                            susers.append( db_n.author.user_id() )
                        for u in db_n.shared_with:
                            v = json.loads( u )
                            i = v['id']
                            if i not in susers:
                                susers.append( i )

                    db_n.modify_date = datetime.datetime.now()
                    db_n.put()
                    cur = note['from']

                    sentTo( db_n, susers, cur )
                else:
                    self.error(400)
                    self.response.out.write ("Note for the given id does not exist.")

            memcache.delete( user.user_id() + "_notes")
            memcache.delete( user.user_id() + "_trash")
        else:
            self.error(401)
            self.response.out.write("Not logged in.")

class Trash(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            note_query = memcache.get( user.user_id() + "_trash")
            if note_query is not None:
                self.response.out.write( note_query )
            else:
                notes_query = stickynote.snModel.all().ancestor(
                    stickynote.key(user.email()))
                notes_query.filter ( "trash = ", 1 ).order('delete_date')

                arr = []
                for note in notes_query:
                    arr.append( note.to_dict() )

                trash = json.dumps( arr )
                self.response.out.write( trash )
                memcache.add( user.user_id() + "_trash", trash )

        else:
            self.error(401)
            self.response.out.write("Not logged in.")

    def put(self):
        user = users.get_current_user()
        if user:
            dict =  json.loads ( self.request.body )
            cur = ""
            for note in dict:
                db_n = stickynote.db.get( note['id'] )
                if db_n:
                    cur = note['from']
                    db_n.trash = 0
                    db_n.delete_date = None
                    db_n.put()
                    if user.user_id() == db_n.author.user_id():
                        susers = [user.user_id()]
                    else:
                        susers = [user.user_id(), db_n.author.user_id()]                    
                    for u in db_n.shared_with:
                        v = json.loads( u )
                        i = v['id']
                        if i not in susers:
                            susers.append( i )
                    sentTo( db_n, susers, cur )

            memcache.delete( user.user_id() + "_notes")
            memcache.delete( user.user_id() + "_trash")
        else:
            self.error(401)
            self.response.out.write("Not logged in.")

class Connect(webapp.RequestHandler):
    def post(self):
        client_id = self.request.get("from")
        #get current user isn't working...
        u_id = client_id.rpartition("-")[2].partition("_")[0]

        c_u = memcache.get ( u_id + "_user" )
        if c_u is None:
            c_u = sticklet_users.stickletUser.get_or_insert( u_id )

        if len( c_u.connections ) > 4:
            odd = c_u.connections.pop( 0 )
            channel.send_message( odd, json.dumps( ['error'] ) )

        c_u.connections.append( client_id )
        c_u.put()
        memcache.set( c_u.author.user_id() + "_user", c_u )

class Disconnect(webapp.RequestHandler):
    def post(self):
        client_id = self.request.get("from")
        #get current user isn't working...
        u_id = client_id.rpartition("-")[2].partition("_")[0]

        c_u = memcache.get( u_id + "_user" )
        if c_u is None:
            c_u = sticklet_users.stickletUser.get_or_insert( u_id )

        if client_id in c_u.connections:
            c_u.connections.remove( client_id )
        c_u.put()
        memcache.set( c_u.author.user_id() + "_user", c_u )
        

class Share(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            smail = json.loads ( self.request.body )
            add = sticklet_users.stickletUser.all()
            user_t = add.filter( "email =", smail['email'].lower() ).get()
            if user_t and user_t.author.user_id() != user.user_id():
                db_n = stickynote.db.get( smail['id'] )
                if db_n:
                    update = False
                    if smail['id'] not in user_t.has_shared:
                        user_t.has_shared.append( smail['id'] )
                        user_t.put()
                        memcache.set( user_t.author.user_id() + "_user", user_t )
                    if user_t.author.user_id() not in db_n.shared_with:
                        db_n.shared_with.append( json.dumps({"id" : user_t.author.user_id(),
                                                  "color" : db_n.color,
                                                  "x" : db_n.x,
                                                  "y" : db_n.y,
                                                  "z" : db_n.z})
                                                 )
                        update = True
                    if user_t.author.email().lower() not in db_n.shared_with_emails:
                        db_n.shared_with_emails.append( user_t.author.email().lower() )
                        update = True
                    if update:
                        db_n.put()
                        memcache.delete( db_n.author.user_id() + "_notes" )
                    if len(user_t.connections) == 0:
                        mail.send_mail( sender="Sticklet.com <admin@sticklet.com>",
                                        to=user_t.email,
                                        subject=user.nickname() + " has shared a sticklet with you!",
                                        body="Sign in to www.sticklet.com to view and collaborate on it!" )
                else:
                    self.error(400)
                    self.response.out.write("No such note.")
            else:
                if "gmail" in smail['email']:
                    mail.send_mail( sender="Sticklet.com <admin@sticklet.com>",
                                    to=smail['email'],
                                    subject=user.nickname() + " has shared a sticklet with you!",
                                    body="Sign in to www.sticklet.com with a your gmail account to view and collaborate on it!" )
        else:
            self.error(401)
            self.response.out.write("Not logged in.")

    def get(self):
        user = users.get_current_user()
        u = memcache.get( user.user_id() + "_user")
        updated = False
        if u is None:
            u = sticklet_users.stickletUser.get_by_key_name( user.user_id() )
            updated = True
        if u:
            arr = []
            for nos in u.has_shared:
                note = stickynote.db.get( nos )
                if note:
                    for js in note.shared_with:
                        d = json.loads( js )
                        if d['id'] == u.author.user_id():
                            dic = note.to_dict()
                            dic['color'] = d['color']
                            dic['x'] = d['x']
                            dic['y'] = d['y']
                            dic['z'] = d['z']
                            arr.append( dic )
                            break
                else:
                    u.has_shared.remove( nos )
                    u.put()
                    updated = True
            self.response.out.write( json.dumps( arr ) )
            if updated:
                memcache.set( user.user_id() + "_user", u )

def sentTo( note, susers, cur ):
    for up in susers:
        u = memcache.get( up + "_user")
        if u is None:
            u = sticklet_users.stickletUser.get_by_key_name( up )
            if u:
                if u.author is None:
                    u.author = user
                    u.email = string.lower(user.email())
                    u.put()
                memcache.set( up + "_user", u )
        if u:
            try:
                d = note['to_delete']
                db_n = note
            except:
                db_n = note.to_dict()
                if up != note.author.user_id():
                    for d in note.shared_with:
                        t = json.loads( d )
                        if t['id'] == up:
                            db_n['color'] = t['color']
                            db_n['x'] = t['x']
                            db_n['y'] = t['y']
                            db_n['z'] = t['z']
                            break

            cur = u.author.user_id() + "_chan_" + cur
            for con in u.connections:
                if con != cur:
                    channel.send_message( con, json.dumps( [db_n] ) )

application = webapp.WSGIApplication([
    ('/notes', Note),
    ('/notes/trash', Trash),
    ('/_ah/channel/connected/', Connect),
    ('/_ah/channel/disconnected/', Disconnect),
    ('/share', Share) ], debug=True)

def main():
        run_wsgi_app(application)

if __name__ == "__main__":
        main()
