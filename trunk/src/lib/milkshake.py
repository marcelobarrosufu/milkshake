# -*- coding: utf-8 -*-
"""
Milkshake
Copyright (C) 2009  Marcelo Barros & Jose Antonio Oliveira

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.


Milkshake
Copyright (C) 2009  Marcelo Barros & Jose Antonio Oliveira
This program comes with ABSOLUTELY NO WARRANTY; for details see 
about box.
This is free software, and you are welcome to redistribute it
under certain conditions; see about box for details.
"""
from appuifw import *
from window import Application, Dialog
import pickle
import os
import e32
import sysinfo
from about import About
from taskutil import *
from settings import MSSettings, Config
import copy

__all__ = [ "Milkshake" ]
__author__ = "José Antonio (javsmo@gmail.com) and "
__author__ = __author__ + "Marcelo Barros de Almeida (marcelobarrosalmeida@gmail.com)"
__version__ = "alpha1"
__copyright__ = "Copyright (c) 2009- Javsmo/Marcelo"
__license__ = "GPLv3"

def display_in_browser(url):
    b = 'BrowserNG.exe'
    e32.start_exe(b, ' "4 %s"' %url, 1)

class Notepad(Dialog):
    def __init__(self, cbk, lst, pos, txt=u"",):
        menu = [(u"Save", self.close_app),
                (u"Discard", self.cancel_app)]
        self.lst = lst
        self.pos = pos
        body = Text(txt)
        body.color = (200,200,200)
        body.style = STYLE_BOLD
        Dialog.__init__(self, cbk, lst, body, menu)
    
class RTMSync():
    rtm = None
    api_key = u""
    secret= u""
    token=None
    def __init__(self, api_key, secret, token=None):
        self.rtm = rtm.RTM(api_key, secret, token)
        if (token == None):
            self.rtm_auth()
    
    def rtm_auth(self):
        appuifw.query(u"""You'll be redirected to browser to log on 
your Remember The Milk account. When you complete this authentication,
 please, close the browser to return to this application.""", "query")
        try:
            authURL = myRTM.getAuthURL()
            display_in_browser(authURL)
            self.token = myRTM.getToken()
        except:
            note(u"Authentication error", "error")
            self.token = None
    
    def get_lists(self):
        try:
            l = self.rtm.lists.getList()
            self.lists = [{"archived":l.archived, 
                          "deleted":l.deleted, 
                          "id":l.id, 
                          "locked":l.locked, 
                          "name":l.name, 
                          "position":l.position, 
                          "smart":l.smart, 
                          "sort_order":l.sort_order} for l in l.lists.list]
        except:
            note(u"Cannot download List data.", "error")
    
    def get_tasks(self, plist_id = None, pfilter=""):
        try:
            if (plist_id == None):
                t = self.rtm.tasks.getList(filter=pfilter)
            else:
                t = self.rtm.tasks.getList(list_id=plist_id, filter=pfilter)
            
            self.tasks[list_id] = [{"created":t.created, 
                                   "id":t.id, 
                                   "location_id":t.location_id, 
                                   "modified":t.modified, 
                                   "name":t.name, 
                                   "notes":t.notes, 
                                   "participants":t.participants, 
                                   "source":t.source, 
                                   "tags":t.tags, 
                                   "task":t.task, 
                                   "url":t.url} for t in t.tasks.list.taskseries]
        except:
            note(u"Cannot download Tasks.", "error")
    
class Milkshake(Application):
    MSDEFDIR = u""
    MSDBNAME = u""
    MSVERSION = u"0.0.4"
    APIKEY = u"c1a983bba360889c5089d5ccf1a94e4a"
    SECRET = u"67b5855d779f0d37"
    def __init__(self,path=u"e:\\python"):
        Milkshake.MSDEFDIR = path
        Milkshake.MSDBNAME = os.path.join(path,u"milkshake.bin")
        app.screen = 'normal'
        app.directional_pad = False
        self.last_task_list = None
        self.list_mngr = ListManager()
        self.config = Config()
        self.load_cfg()    
        self.main_menu = [(u"Syncronize ...",self.sync_dlg),
                            (u"Settings ...",self.settings_dlg),
                            (u"Save",self.save_cfg),
                            (u"About", self.about_ms),
                            (u"Exit", self.close_app) ]
        Application.__init__(self, u"Milkshake", Listbox([(u"",u"")],lambda:None), [])
        self.update_lists()

    def update_lists(self,lst=None,pos=None):
        if not self.config['use_tabs']:
            menu = [(u"Lists ...", self.list_menu)]+self.main_menu
            self.set_ui(u"Milkshake", Listbox(self.get_task_list_list(),self.list_menu), menu)
        else:
            app_data = []
            menu = [(u"Lists ...", self.list_menu),
                            (u"Tasks ...",self.task_menu)] + self.main_menu
            for lst in self.list_mngr.keys():
                # set filter for done tasks
                self.show_done_tasks(lst,self.config['show_done'])
                app_data.append((lst,Listbox(self.get_task_list(lst),self.task_menu),[])) 
            self.set_ui(u"Milkshake", app_data, menu)
        self.refresh()

    def get_def_task_list_mngr(self):
        lst = ListManager()
        lst[u"Default"] = TaskList()
        return lst

    def get_task_list_list(self):
        lst = []
        for k in self.list_mngr.keys():
            if self.config['single_row']:
                lst.append(k)
            else:
                n = len(self.list_mngr[k])
                if n > 1:
                    m = u"%d tasks" % n
                elif n == 1:
                    m = u"%d task" % n
                else:
                    m = u"No tasks"
                lst.append((k,m))
        return lst

    def get_def_task_list(self):
        if self.config['single_row']:
            return [ u"Press select to add tasks" ]
        else:
            return [ (u"Press select to add tasks",u"") ]
    def get_icon(self,tsk):
        if tsk["perc_done"] >= 100:
            icon = u"[X] "
        else:
            icon = u"[  ] "
        return icon

    def get_task_list(self,lst):
        if self.list_mngr[lst]:
            if self.config['single_row']:
                lst = [self.get_icon(tskn) + tskn["name"] for tskn in self.list_mngr[lst] ]
            else:
                lst = [(self.get_icon(tskn) + tskn["name"],u"") for tskn in self.list_mngr[lst]]
        else:
            lst = self.get_def_task_list()
        return lst

    def load_cfg(self):
        try:
            f = open(Milkshake.MSDBNAME,"rb")
            version = pickle.load(f)
            self.list_mngr.load(f)
            self.config.load(f)
            f.close()
        except Exception, e:
            if os.path.exists(Milkshake.MSDBNAME):
                note(u"Impossible to load config from " +
                     Milkshake.MSDBNAME +
                     u". " + unicode(str(e)),"error")
            self.list_mngr = self.get_def_task_list_mngr()

    def save_cfg(self):
        try:
            f = open(Milkshake.MSDBNAME,"wb")
            pickle.dump(Milkshake.MSVERSION,f)
            self.list_mngr.save(f)
            self.config.save(f)
            f.close()
        except Exception, e:
            note(u"Impossible to save config to file " +
                 Milkshake.MSDBNAME +
                 u". " + unicode(str(e)),"error")

    def get_current_task_list(self):
        if self.config['use_tabs']:
            lst = lst = self.tab_title
        else:
            if self.last_task_list is None:
                n = app.body.current()
                lst = self.list_mngr.keys()[n]
            else:
                lst = self.last_task_list
        return lst

    def list_menu(self):
        lst = self.get_current_task_list()
        menu = []
        if not self.config['use_tabs']:
            menu += [(u"Show tasks",self.edit_task_list)]
        menu += [(u"New",self.new_list),
                (u"Rename",self.ren_list),
                (u"Delete",self.del_list)]
        op = popup_menu([m[0] for m in menu],u"List menu:")
        if op is not None:
            menu[op][1](lst)

    def task_menu(self):
        lst = self.get_current_task_list()
        n = app.body.current()
        if self.list_mngr[lst]:
            menu = [(u"Edit",self.edit_task),
                    (u"New",self.new_task),
                    (u"Rename",self.ren_task),
                    (u"Delete",self.del_task)]
            if len(self.list_mngr.keys()) > 1:
                menu.append((u"Move",self.move_task))
            if self.list_mngr[lst][n]["perc_done"] < 100:
                    menu.append((u"Mark as done",self.done_task))
            else:
                    menu.append((u"Mark as not done",self.undone_task))
        else:
            menu = [(u"New",self.new_task)]
        op = popup_menu([m[0] for m in menu],u"Tasks menu:")
        if op is not None:
            menu[op][1](lst,n)
        
    def sync_dlg(self):
        note(u"Soon as possible ! Please, wait.","info")

    def edit_task_list(self,lst):
        # only valid in non tabbed mode or recursive call
        if self.config['use_tabs'] or self.last_task_list:
            raise Exception
        self.last_task_list = lst
        def cbk():
            self.last_task_list = None
            self.update_lists()
        # create a new UI using Listbox 
        self.global_menu = [(u"Tasks ...",self.task_menu),(u"Close",cbk)]
        # set filter for done tasks
        self.show_done_tasks(lst,self.config['show_done'])
        self.body = Listbox(self.get_task_list(self.last_task_list),self.task_menu)
        self.title = self.last_task_list
        self.exit_handler = cbk
        self.refresh()

    def new_list(self,lst):
        nlst = query(u"List name:","text",lst)
        if nlst is not None:
            if nlst in self.list_mngr.keys():
                note(u"This list name already exists !","error")
            else:
                self.list_mngr[nlst] = TaskList()
                self.update_lists()

    def del_list(self,lst):
        msg = u"Delete " + lst + u" ?"
        op = popup_menu([u"No", u"Yes"],msg)
        if op is not None:
            if op:
                del self.list_mngr[lst]
                if not self.list_mngr:
                    self.list_mngr = self.get_def_task_list_mngr()
                self.update_lists()

    def ren_list(self,lst):
        nlst = query(u"List name:","text",lst)
        if nlst is not None:
            self.list_mngr[nlst] = self.list_mngr[lst]
            del self.list_mngr[lst]
            self.update_lists()

    def new_task(self,lst,n):
        tsk = query(u"Task name:","text",u"")
        if tsk is not None:
            self.list_mngr[lst].append(Task(name=tsk))
            lb = self.get_task_list(lst)
            app.body.set_list(lb,len(lb)-1)
            
    def del_task(self,lst,n):
        msg = u"Delete " + self.list_mngr[lst][n]["name"] + u" ?"
        op = popup_menu([u"No", u"Yes"],msg)
        if op is not None:
            if op:
                del self.list_mngr[lst][n]
                lb = self.get_task_list(lst)
                n = max(n - 1,0)
                app.body.set_list(lb,n)

    def ren_task(self,lst,n):
        tsk = query(u"Task name:","text",self.list_mngr[lst][n]["name"])
        if tsk is not None:
            self.list_mngr[lst][n]["name"] = tsk
            lb = self.get_task_list(lst)
            app.body.set_list(lb,app.body.current())

    def edit_task(self,lst,pos):
        def cbk():
            if not self.dlg.cancel:
                self.list_mngr[self.dlg.lst][self.dlg.pos]["note"] = self.dlg.body.get()
            self.dlg = None
            self.refresh()
        self.dlg = Notepad(cbk,lst,pos,self.list_mngr[lst][pos]["note"])
        self.dlg.run()

    def move_task(self,lst,n):
        glst = [k for k in self.list_mngr.keys() if k != lst ]
        op = popup_menu(glst,u"To list:")
        if op is not None:
            nlst = glst[op] 
            self.list_mngr[nlst].append(self.list_mngr[lst][n])
            del self.list_mngr[lst][n]
            if self.config['use_tabs']:
                self.update_lists()
            else:
                lb = self.get_task_list(lst)
                n = max(n - 1,0)
                app.body.set_list(lb,n)

    def settings_dlg(self):
        def cbk():
            if not self.dlg.cancel:
                # do we have copy contructor in python ?
                for k in self.config.keys():
                    self.config[k] = self.dlg.config[k]
            self.update_lists()
            return True
        self.dlg = MSSettings(cbk,copy.deepcopy(self.config))
        self.dlg.run()
        
    def show_done_tasks(self,lst,show):
        if show:
            self.list_mngr[lst].set_filter(lambda t: True)
        else:
            self.list_mngr[lst].set_filter(lambda t: t['perc_done'] < 100)
            
    def done_undone_task(self,lst,n,p):
        self.list_mngr[lst][n]['perc_done'] = p
        self.list_mngr[lst].update_filter()
        lb = self.get_task_list(lst)
        app.body.set_list(lb,n)
        #note(lst+(u":%d"%len(lb)),"info")

    def done_task(self,lst,n):
        self.done_undone_task(lst,n,100)

    def undone_task(self,lst,n):
        self.done_undone_task(lst,n,0)

    def update_ms(self): pass
    
    def about_ms(self):
        def cbk():
            self.refresh()
            return True
        self.dlg = About(cbk,Milkshake.MSVERSION)
        self.dlg.run()
    
    def close_app(self):
        ny = popup_menu( [u"Yes", u"No"], u"Leave milkshake ?" )
        if ny is not None:
            if ny == 0:
                self.save_cfg()
                Application.close_app(self)
                
if __name__ == "__main__":
    import sys
    sys.path.append(u"e:\\python")
    ms = Milkshake(u"e:\\python")
    ms.run()