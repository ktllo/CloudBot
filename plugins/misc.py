"""
ping.py

Generates fun names using the textgen module.

Created By:
    - Bjorn Neergaard <https://github.com/neersighted>

Modified By:
    - Luke Rogers <https://github.com/lukeroge>

License:
    GPL v3
"""
import codecs
import os
import re
import subprocess

from cloudbot import hook



@hook.command("ping")
def ping(text, reply):
    return "Pong"

@hook.command("feed","feeds")
def feed(nick, action):
    action("takes a 3 pounds steak from "+nick+" and eat it");

@hook.command("boo")
def boo(nick, action):
    action("jumps");
