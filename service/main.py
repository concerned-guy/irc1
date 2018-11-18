import asyncore
import asynchat
import socket
import threading
import time
from kivy.lib import osc

import os, sys
from os.path import abspath, dirname

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, script_path)

from irchandler import IRCHandler

serviceport = 3000
activityport = 3001

running = {}
opened = {}


def init_server(name, host, port, nick="jrandom", password="",
                auth_nickserv=False, script="", *autojoin):
    if name in running:
        return
    map = {}
    kwargs = {"timeout": 1, "map": map}
    irc = IRCHandler(host, port, nick, password,
                     auth_nickserv, script, autojoin, map)
    thread = threading.Thread(target=asyncore.loop, kwargs=kwargs)
    thread.start()
    running[name] = (irc, thread)
    opened[name] = True

def disconnect_server(name):
    if not name in running:
        return
    irc, thread = running[name]
    irc.close()
    thread.join()
    del running[name]
    del opened[name]

def unread_server(name):
    if not name in running:
        return []
    irc, thread = running[name]
    return irc.pop_unread()

def send_server(name, message):
    if not name in running:
        return
    irc, thread = running[name]
    irc.parse_in(message)

def channel_server(name, channel):
    if not name in running:
        return
    irc, thread = running[name]
    if channel in irc.channels:
        irc.old_channel, irc.channel = channel, channel

def monitor_changes():
    if not running:
        return
    for name in running:
        irc, thread = running[name]
        if irc.old_nick != irc.nick:
            osc.sendMsg("/api/main", ["nick", name, irc.nick],
                        port = activityport)
            irc.old_nick = irc.nick
        if irc.old_channel != irc.channel or irc.old_channels != irc.channels:
            osc.sendMsg("/api/main",
                        ["channel", name, irc.channel] + irc.channels,
                        port=activityport)
            irc.old_channel = irc.channel
            irc.old_channels = irc.channels[:]
        if irc.unread and opened[name]:
            osc.sendMsg("/api/main", ["check", name], port=activityport)
            opened[name] = False

def main_api_callback(message, *args):
#    print message[2:]
    if len(message) > 3:
        name = message[3]
        if message[2] == "connect":
            init_server(name, *message[4:])
        elif message[2] == "disconnect":
            disconnect_server(name)
        elif message[2] == "unread":
            unread = unread_server(name)
            osc.sendMsg("/api/main", ["unread", name, unread],
                        port=activityport)
            opened[name] = True
        elif message[2] == "send":
            send_server(name, message[4])
        elif message[2] == "channel":
            channel_server(name, message[4])


if __name__ == "__main__":
    osc.init()
    oscid = osc.listen(ipAddr="127.0.0.1", port=serviceport)
    osc.bind(oscid, main_api_callback, "/api/main")
    while True:
        monitor_changes()
        osc.readQueue(oscid)
        time.sleep(0.1)

