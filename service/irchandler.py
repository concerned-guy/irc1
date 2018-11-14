import asyncore
import asynchat
import getpass
import re
import socket
from kivy.utils import escape_markup as escape

import os, sys
from os.path import abspath, dirname

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, script_path)

import bb

class IRCHandler(asynchat.async_chat):

    def __init__(self, host, port, nick, password=None, auth_nickserv=False,
                 script='', autojoin=[], map=None, **kwargs):
        asynchat.async_chat.__init__(self, map=map, **kwargs)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.host = host
        self.port = port
        self.nick = nick
        self.user = 'androiduser'
        self.autojoin = autojoin
        self.password = password
        self.auth_nickserv = auth_nickserv
        self.script = script
        self.channel = ''
        self.channels = ['']
        self.command_prefix = '/'
        self.list_names = False
        self.part_msg = 'Leaving to study for final exam.'
        self.set_terminator('\r\n')
        self.inbuf = ''
        self.outbufs = []
        self.unread = []
        self.old_channel = self.channel
        self.old_nick = self.nick
        if self.password and not self.auth_nickserv:
            self.send_srv('PASS %s' % password)
        self.send_srv('NICK %s' % self.nick)
        self.send_srv('USER %s %s %s :%s' % (self.user, 'localhost',
                                             self.host, self.user))
        
    def collect_incoming_data(self, data):
        self.inbuf += data
        
    def found_terminator(self):
        msg, self.inbuf = self.inbuf, ''
        self.parse_srv(msg.encode('ascii', 'ignore'))

    def writable(self):
        return len(self.outbufs) > 0
        
    def handle_write(self):
        msg = self.outbufs.pop(0) + '\n'
        self.push(msg)

    def send_srv(self, data):
        self.outbufs.append(data)

    def parse_srv(self, msg):
        usr, cmd = self.host, msg
        if not cmd:
            return
        if cmd[0] == ':':
            usr, cmd = (cmd[1:].split(' ', 1) + [''])[:2]
            if not cmd:
                return
            usr = usr.split('!')[0]
        cmd, par = (cmd.split(' ', 1) + [''])[:2]
        par, txt = (par.split(':', 1) + [''])[:2]
        par = par.rstrip()

        txt = re.sub(r'(http|ftp|https)://?[-a-zA-Z0-9@:%._+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_+.~#?&/=]*)', bb.url('\g<0>'), escape(txt))
        if cmd == 'PONG' or cmd == 'MODE':
            return
        if (cmd == '353' or cmd == '366') and not self.list_names:
            return
        if txt == '\x01VERSION\x01':
            return
        elif cmd == 'PING':
            self.send_srv(msg.replace('PING', 'PONG', 1))
        elif cmd == 'PRIVMSG':
            self.add_unread('%s: %s%s%s %s' % (bb.blue(par),
                                               bb.green('<'),
                                               usr,
                                               bb.green('>'),
                                               txt))
        elif cmd == 'JOIN':
            par = par or txt
            if usr == self.nick:
                self.add_unread('You have joined channel %s' % par)
                self.channels.append(par)
                self.channel = par
            else:
                self.add_unread('%s has joined '
                                'channel %s' % (bb.cyan(bb.bold(usr)), par))
        elif cmd == 'NICK':
            if usr == self.nick:
                self.add_unread('You are now known as %s' % txt)
                self.nick = txt
            else:
                self.add_unread('%s is now known as %s' % (usr, txt))
        elif cmd == 'NOTICE':
            self.add_unread('%s%s%s %s' % (bb.blue('-'),
                                           bb.purple(usr),
                                           bb.blue('-'),
                                           txt))
        elif cmd == 'PART':
            if usr == self.nick:
                self.add_unread('You have left channel %s' % par)
                if par == self.channel:
                    self.channel = self.channels[self.channels.index(par)-1]
                self.channels.remove(par)
            else:
                self.add_unread('%s has left channel %s' % (usr, par))
        elif cmd == 'QUIT':
            # self.add_unread('%s has quit %s%s%s' % (usr,
            #                                         bb.grey('('),
            #                                         txt,
            #                                         bb.grey(')')))
            pass
        elif cmd == 'TOPIC':
            self.add_unread('Topic for channel %s '
                            'is %s' % (bb.cyan(par), bb.cyan(txt)))
        elif cmd == '332':
            self.add_unread('Topic for channel %s is %s' %
                            (bb.cyan(par.split()[1]), bb.cyan(txt)))
        elif cmd == '353': # names list
            self.add_unread(bb.grey('* [%s] %s' % (par.split()[-1], txt)))
        elif cmd == 'KICK':
            if txt == self.nick:
                self.add_unread('You have been kicked from %s '
                                'by %s' % (par, bb.cyan(bb.bold(usr))))
            else:
                self.add_unread('%s has kicked %s '
                                'from %s' % (bb.cyan(bb.bold(usr)), txt, par))
        elif txt:
            self.add_unread(bb.grey('* %s' % txt))

        if cmd == '366': # end of names list
            self.list_names = False

        if cmd == '001': # welcome reply from sever
            if self.password and self.auth_nickserv:
                self.privmsg('NickServ', 'IDENTIFY %s' % self.password)
            if self.script:
                self.send_srv(self.script)
            for j in self.autojoin:
                self.join(j)

    def add_unread(self, msg):
        self.unread.append(msg)
        if len(self.unread) > 1024:
            self.unread = self.unread[-1024:]
        print msg
        
    def pop_unread(self):
        unread, self.unread = self.unread, []
        return unread

    def parse_in(self, msg):
        msg = msg.strip()
        if not msg:
            return
        msg = re.sub(r'\s+', ' ', msg)
        if msg[0] != self.command_prefix:
            self.privmsg(self.channel, msg)
            return
        if msg[1:5] == 'join':
            cmd, channel = (msg.split(' ', 1) + [''])[:2]
            self.join(channel)
        elif msg[1:5] == 'part':
            cmd, channel, txt = (msg.split(' ', 2) + ['', ''])[:3]
            self.part(channel, msg)
        elif msg[1:4] == 'msg':
            cmd, channel, txt = (msg.split(' ', 2) + ['', ''])[:3]
            if not channel:
                self.add_unread(bb.mute('Missing #<channel> name'))
                return
            self.privmsg(channel, txt)
            return
        elif msg[1:6] == 'names':
            self.list_names = True
            self.send_srv(msg[1:])
        else:
            self.send_srv(msg[1:])
        self.add_unread(msg)

    def join(self, channel):
        if not channel:
            self.add_unread(bb.mute('Missing #<channel> name'))
            return
        self.send_srv('JOIN %s' % channel)

    def part(self, channel, msg):
        if not channel:
            channel = self.channel
        if not msg:
            msg = self.part_msg
        self.send_srv('PART %s :%s' % (channel, msg))

    def privmsg(self, channel, msg):
        if not channel:
            self.add_unread(bb.mute('No channel joined. '
                                    'Try /join #<channel>'))
            return
        if not msg:
            self.add_unread(bb.mute('Missing text to send'))
            return
        self.add_unread('%s: %s%s%s %s' % (bb.blue(channel),
                                           bb.purple('<'),
                                           self.nick,
                                           bb.purple('>'),
                                           msg))
        self.send_srv('PRIVMSG %s :%s' % (channel, msg))

