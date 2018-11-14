from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lib import osc
from kivy.utils import platform

from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.storage.dictstore import DictStore
from kivy.animation import Animation

from functools import partial

import os, sys
from os.path import abspath, dirname

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, script_path)

from screenmain import ScreenMain, ServerBox
from screenconversation import ScreenConversation, ChatLabel
from utils import pause_app, hook_keyboard

serviceport = 3000
activityport = 3001


class irc1App(App):
    def build(self):
        if platform == 'android':
            from android import AndroidService
            service = AndroidService('irc1\'s service', 'running')
            service.start('service started')
            self.service = service

        osc.init()
        oscid = osc.listen(ipAddr='127.0.0.1', port=activityport)
        osc.bind(oscid, self.main_api_callback, '/api/main')
        Clock.schedule_interval(lambda *x: osc.readQueue(oscid), 0.1)

        self.icon = 'icon.png'
	self.servers = DictStore('servers.db')
        self.msg_animation = Animation(opacity=1, transition='out_cubic')
        self.screenmain = ScreenMain()
        self.running = {}
        self.boxes = {}

        for name in sorted(dict(self.servers.find()).keys()):
            data = self.servers.get(name)
            box = ServerBox(name=name)
            self.boxes[name] = box
            self.screenmain.ids.servers.add_widget(box)

        manager = ScreenManager(transition=SlideTransition(duration=0.2))
        manager.add_widget(self.screenmain)
        return manager

    def go_back(self):
        name = self.root.current
        if name == 'ScreenMain':
            pause_app()
        else:
            self.root.transition.direction = 'right'
            self.root.current = 'ScreenMain'

    def init_connection(self, name):
        if name not in self.servers:
            return
        if name not in self.running:
            Animation(background_color=(0.1,1,0.1,1)).start(
                self.boxes[name].ids.servername)
            screen = ScreenConversation(name=name)
            data = self.servers.get(name)
            self.running[name] = screen
            self.root.add_widget(screen)
            screen.ids.nick.text = data['nick']
            osc.sendMsg('/api/main',
                        ['connect', name,
                         data['host'], data['port'], data['nick'],
                         data['password'], data['auth_nickserv'],
                         data['scripts']] + data['autojoin'],
                        port=serviceport)
        self.root.transition.direction = 'left'
        self.root.current = name

    def close_connection(self, name):
        osc.sendMsg('/api/main', ['disconnect', name], port=serviceport)
        if name not in self.running:
            return
        Animation(background_color=(1,1,1,1)).start(
            self.boxes[name].ids.servername)
        self.root.transition.direction = 'right'
        self.root.current = 'ScreenMain'
        self.root.remove_widget(self.running[name])
        del self.running[name]

    def disconnect_all(self):
        for name in sorted(dict(self.servers.find()).keys()):
            self.close_connection(name)

    def update_or_add_server(self, popup, name=''):
        host          = str(popup.ids.host.text).strip()
        port          = int(str(popup.ids.port.text).strip())
        nick          = str(popup.ids.nick.text).strip()
        password      = str(popup.ids.password.text)
        auth_nickserv = popup.ids.auth_nickserv.active
        scripts       = str(popup.ids.scripts.text).strip()
        autojoin      = str(popup.ids.autojoin.text).strip()
        autojoin      = autojoin.replace(',', ' ').split()
        data = {'host': host, 'port': port, 'nick': nick,
                'password': password, 'auth_nickserv': auth_nickserv,
                'scripts': scripts, 'autojoin': autojoin}

        if name:
            self.servers.put(name, **data)
            return

        name = '%s:%d' % (host, port)
        if self.servers.exists(name):
            return
        if not host or not port > 0 or not nick:
            return

        self.servers.put(name, **data)
        box = ServerBox(name=name)
        self.boxes[name] = box
        self.screenmain.ids.servers.add_widget(box)

    def del_server(self, serverbox):
        name = serverbox.name
        if self.servers.exists(name):
            self.servers.delete(name)
        del_animation = Animation(opacity=0, duration=0.2)
        del_animation.bind(
            on_complete=lambda *x: serverbox.parent.remove_widget(serverbox))
        del_animation.start(serverbox)
        del self.boxes[name]

    def log_msg(self, name, message):
        label = ChatLabel(text=message)
        self.running[name].ids.chatlog.add_widget(label)
        self.running[name].ids.chatscroll.scroll_to(label)
        if self.root.current == name:
            self.msg_animation.start(label)
        else:
            label.opacity = 1

    def send_msg(self, name, message):
        Clock.schedule_once(partial(self.input_focus, name), 0)
        osc.sendMsg('/api/main', ['send', name, message],
                    port=serviceport)

    def change_channel(self, name, channel):
        osc.sendMsg('/api/main', ['channel', name, channel],
                    port=serviceport)

    def main_api_callback(self, message, *args):
        print message[2:]
        if len(message) > 3:
            name = message[3]
            if name not in self.running:
                return
            if message[2] == 'nick':
                self.running[name].ids.nick.text = message[4]
            elif message[2] == 'channel':
                self.running[name].ids.channel.text = message[4] or 'No channel'
                self.running[name].ids.channel.values = [x or 'No channel'
                                                         for x in message[5:]]
            elif message[2] == 'check':
                osc.sendMsg('/api/main', ['unread', name], port=serviceport)
            elif message[2] == 'unread':
                for m in message[4:]:
                    self.log_msg(name, m)
                    
    def input_focus(self, name, dt):
        self.running[name].ids.message.focus = True

    def on_start(self):
        Window.softinput_mode = 'below_target'
        hook_keyboard()

    def on_pause(self):
        return True

    def on_resume(self):
        pass

    def on_stop(self):
        if platform == 'android':
            self.service.stop()

if __name__ == '__main__':
    irc1App().run()

