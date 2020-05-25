import asyncio
from asyncio import Task
from unittest.mock import MagicMock

from cloudbot.clients.irc import _IrcProtocol
from cloudbot.event import EventType


class TestLineParsing:
    def _filter_event(self, event):
        return {k: v for k, v in dict(event).items() if not callable(v)}

    def test_data_received(self):
        _, out, proto = self.make_proto()
        proto.data_received(
            b":server.host COMMAND this is :a command\r\n:server.host PRIVMSG me :hi\r\n"
        )

        assert out == [
            {
                "chan": None,
                "content": None,
                "content_raw": None,
                "db": None,
                "db_executor": None,
                "hook": None,
                "host": "",
                "irc_command": "COMMAND",
                "irc_ctcp_text": None,
                "irc_paramlist": ["this", "is", "a command"],
                "irc_prefix": "server.host",
                "irc_raw": ":server.host COMMAND this is :a command",
                "mask": "server.host",
                "nick": "server.host",
                "target": None,
                "type": EventType.other,
                "user": "",
            },
            {
                "chan": "server.host",
                "content": "hi",
                "content_raw": "hi",
                "db": None,
                "db_executor": None,
                "hook": None,
                "host": "",
                "irc_command": "PRIVMSG",
                "irc_ctcp_text": None,
                "irc_paramlist": ["me", "hi"],
                "irc_prefix": "server.host",
                "irc_raw": ":server.host PRIVMSG me :hi",
                "mask": "server.host",
                "nick": "server.host",
                "target": None,
                "type": EventType.message,
                "user": "",
            },
        ]

    def make_proto(self):
        conn = MagicMock()
        conn.nick = "me"
        conn.loop = conn.bot.loop = asyncio.get_event_loop_policy().new_event_loop()
        out = []

        def func(e):
            out.append(self._filter_event(e))

        conn.bot.process = func
        proto = _IrcProtocol(conn)
        return conn, out, proto

    def test_broken_line_doesnt_interrupt(self):
        _, out, proto = self.make_proto()
        proto.data_received(
            b":server.host COMMAND this is :a command\r\nPRIVMSG\r\n:server.host PRIVMSG me :hi\r\n"
        )

        assert out == [
            {
                "chan": None,
                "content": None,
                "content_raw": None,
                "db": None,
                "db_executor": None,
                "hook": None,
                "host": "",
                "irc_command": "COMMAND",
                "irc_ctcp_text": None,
                "irc_paramlist": ["this", "is", "a command"],
                "irc_prefix": "server.host",
                "irc_raw": ":server.host COMMAND this is :a command",
                "mask": "server.host",
                "nick": "server.host",
                "target": None,
                "type": EventType.other,
                "user": "",
            },
            {
                "chan": "server.host",
                "content": "hi",
                "content_raw": "hi",
                "db": None,
                "db_executor": None,
                "hook": None,
                "host": "",
                "irc_command": "PRIVMSG",
                "irc_ctcp_text": None,
                "irc_paramlist": ["me", "hi"],
                "irc_prefix": "server.host",
                "irc_raw": ":server.host PRIVMSG me :hi",
                "mask": "server.host",
                "nick": "server.host",
                "target": None,
                "type": EventType.message,
                "user": "",
            },
        ]

    def test_pong(self):
        conn, _, proto = self.make_proto()
        proto.data_received(b":server PING hi\r\n")

        conn.send.assert_called_with("PONG hi", log=False)

    def test_simple_cmd(self):
        _, _, proto = self.make_proto()
        event = proto.parse_line(":server.host COMMAND this is :a command")

        assert self._filter_event(event) == {
            "chan": None,
            "content": None,
            "content_raw": None,
            "db": None,
            "db_executor": None,
            "hook": None,
            "host": "",
            "irc_command": "COMMAND",
            "irc_ctcp_text": None,
            "irc_paramlist": ["this", "is", "a command"],
            "irc_prefix": "server.host",
            "irc_raw": ":server.host COMMAND this is :a command",
            "mask": "server.host",
            "nick": "server.host",
            "target": None,
            "type": EventType.other,
            "user": "",
        }

    def test_parse_privmsg(self):
        _, _, proto = self.make_proto()
        event = proto.parse_line(
            ":sender!user@host PRIVMSG #channel :this is a message"
        )

        assert self._filter_event(event) == {
            "chan": "#channel",
            "content": "this is a message",
            "content_raw": "this is a message",
            "db": None,
            "db_executor": None,
            "hook": None,
            "host": "host",
            "irc_command": "PRIVMSG",
            "irc_ctcp_text": None,
            "irc_paramlist": ["#channel", "this is a message"],
            "irc_prefix": "sender!user@host",
            "irc_raw": ":sender!user@host PRIVMSG #channel :this is a message",
            "mask": "sender!user@host",
            "nick": "sender",
            "target": None,
            "type": EventType.message,
            "user": "user",
        }

    def test_parse_privmsg_ctcp_action(self):
        _, _, proto = self.make_proto()
        event = proto.parse_line(
            ":sender!user@host PRIVMSG #channel :\1ACTION this is an action\1"
        )

        assert self._filter_event(event) == {
            "chan": "#channel",
            "content": "this is an action",
            "content_raw": "\x01ACTION this is an action\x01",
            "db": None,
            "db_executor": None,
            "hook": None,
            "host": "host",
            "irc_command": "PRIVMSG",
            "irc_ctcp_text": "ACTION this is an action",
            "irc_paramlist": ["#channel", "\x01ACTION this is an action\x01"],
            "irc_prefix": "sender!user@host",
            "irc_raw": ":sender!user@host PRIVMSG #channel :\x01ACTION this is an "
            "action\x01",
            "mask": "sender!user@host",
            "nick": "sender",
            "target": None,
            "type": EventType.action,
            "user": "user",
        }

    def test_parse_privmsg_ctcp_version(self):
        _, _, proto = self.make_proto()
        event = proto.parse_line(":sender!user@host PRIVMSG #channel :\1VERSION\1")

        assert self._filter_event(event) == {
            "chan": "#channel",
            "content": "\x01VERSION\x01",
            "content_raw": "\x01VERSION\x01",
            "db": None,
            "db_executor": None,
            "hook": None,
            "host": "host",
            "irc_command": "PRIVMSG",
            "irc_ctcp_text": "VERSION",
            "irc_paramlist": ["#channel", "\x01VERSION\x01"],
            "irc_prefix": "sender!user@host",
            "irc_raw": ":sender!user@host PRIVMSG #channel :\x01VERSION\x01",
            "mask": "sender!user@host",
            "nick": "sender",
            "target": None,
            "type": EventType.other,
            "user": "user",
        }

    def test_parse_privmsg_bad_ctcp(self):
        _, _, proto = self.make_proto()
        event = proto.parse_line(":sender!user@host PRIVMSG #channel :\1VERSION\1aa")

        assert self._filter_event(event) == {
            "chan": "#channel",
            "content": "\x01VERSION\x01aa",
            "content_raw": "\x01VERSION\x01aa",
            "db": None,
            "db_executor": None,
            "hook": None,
            "host": "host",
            "irc_command": "PRIVMSG",
            "irc_ctcp_text": None,
            "irc_paramlist": ["#channel", "\x01VERSION\x01aa"],
            "irc_prefix": "sender!user@host",
            "irc_raw": ":sender!user@host PRIVMSG #channel :\x01VERSION\x01aa",
            "mask": "sender!user@host",
            "nick": "sender",
            "target": None,
            "type": EventType.message,
            "user": "user",
        }

    def test_parse_no_prefix(self):
        _, _, proto = self.make_proto()
        event = proto.parse_line("SOMECMD thing")

        assert self._filter_event(event) == {
            "chan": None,
            "content": None,
            "content_raw": None,
            "db": None,
            "db_executor": None,
            "hook": None,
            "host": None,
            "irc_command": "SOMECMD",
            "irc_ctcp_text": None,
            "irc_paramlist": ["thing"],
            "irc_prefix": None,
            "irc_raw": "SOMECMD thing",
            "mask": None,
            "nick": None,
            "target": None,
            "type": EventType.other,
            "user": None,
        }

    def test_parse_pm_privmsg(self):
        _, _, proto = self.make_proto()
        event = proto.parse_line(":sender!user@host PRIVMSG me :this is a message")

        assert self._filter_event(event) == {
            "chan": "sender",
            "content": "this is a message",
            "content_raw": "this is a message",
            "db": None,
            "db_executor": None,
            "hook": None,
            "host": "host",
            "irc_command": "PRIVMSG",
            "irc_ctcp_text": None,
            "irc_paramlist": ["me", "this is a message"],
            "irc_prefix": "sender!user@host",
            "irc_raw": ":sender!user@host PRIVMSG me :this is a message",
            "mask": "sender!user@host",
            "nick": "sender",
            "target": None,
            "type": EventType.message,
            "user": "user",
        }
