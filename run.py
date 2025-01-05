#!/usr/bin/env python3
"""boilerplate taken from Slixmpp (https://codeberg.org/poezio/slixmpp)"""

import logging
import re
import os
from getpass import getpass
from argparse import ArgumentParser
from plugins.yt import yt_link_preview, x_link_preview
from dotenv import load_dotenv

import slixmpp

yt = re.compile(
    r"(?:(?:https?:)?\/\/)?(?:(?:(?:www|m(?:usic)?)\.)?youtu(?:\.be|be\.com)\/(?:shorts\/|live\/|v\/|e(?:mbed)?\/|watch(?:\/|\?(?:\S+=\S+&)*v=)|oembed\?url=https?%3A\/\/(?:www|m(?:usic)?)\.youtube\.com\/watch\?(?:\S+=\S+&)*v%3D|attribution_link\?(?:\S+=\S+&)*u=(?:\/|%2F)watch(?:\?|%3F)v(?:=|%3D))?|www\.youtube-nocookie\.com\/embed\/)([\w-]{11})[\?&#]?\S*"
)
xcom = re.compile(
    r"(?:https?:\/\/)(?:www\.)?(?:fixup)?x\.com\/(?:\w{1,20})\/status\/\d{1,25}"
)
tco = re.compile(r"\shttps:\/\/t.co\/\w+$")
load_dotenv()


class MUCBot(slixmpp.ClientXMPP):
    """
    A simple Slixmpp bot
    """

    def __init__(self, jid, password, room, nick):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)

        # The groupchat_message event is triggered whenever a message
        # stanza is received from any chat room. If you also also
        # register a handler for the 'message' event, MUC messages
        # will be processed by both handlers.
        self.add_event_handler("groupchat_message", self.muc_message)

    async def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        await self.get_roster()
        self.send_presence()
        self.plugin["xep_0045"].join_muc(
            self.room,
            self.nick,
            # If a room password is needed, use:
            # password=the_room_password,
        )

    def muc_message(self, msg):
        """
        Process incoming message stanzas from any chat room. Be aware
        that if you also have any handlers for the 'message' event,
        message stanzas may be processed by both handlers, so check
        the 'type' attribute when using a 'message' event handler.

        Whenever the bot's nickname is mentioned, respond to
        the message.

        IMPORTANT: Always check that a message is not from yourself,
                   otherwise you will create an infinite loop responding
                   to your own messages.

        This handler will reply to messages that mention
        the bot's nickname.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        if msg["mucnick"] != self.nick and not msg["replace"].get("id"):
            video_id = yt.findall(msg["body"])
            tweet = xcom.findall(msg["body"])
            if self.nick in msg["body"]:
                self.send_message(
                    mto=msg["from"].bare,
                    mbody="%s: umu" % msg["mucnick"],
                    mtype="groupchat",
                )
            elif video_id:
                self.send_message(
                    mto=msg["from"].bare,
                    mbody=yt_link_preview(video_id[0]),
                    mtype="groupchat",
                )
            elif tweet:
                tweet_with_video = x_link_preview(tweet[0])
                if tweet_with_video:
                    self.send_message(
                        mto=msg["from"].bare,
                        mbody=tco.sub("", tweet_with_video),
                        mtype="groupchat",
                    )
        # bot admin commands
        elif msg["mucnick"] == os.getenv("OWNER"):
            if msg["body"] == "RELOAD":
                # TODO importlib.reload()
                pass
            if msg["body"] == "SHUTDOWN":
                raise SystemExit()


if __name__ == "__main__":
    # Setup the command line arguments.
    parser = ArgumentParser()

    # Output verbosity options.
    parser.add_argument(
        "-q",
        "--quiet",
        help="set logging to ERROR",
        action="store_const",
        dest="loglevel",
        const=logging.ERROR,
        default=logging.INFO,
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="set logging to DEBUG",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.INFO,
    )

    # JID and password options.
    parser.add_argument("-j", "--jid", dest="jid", help="JID to use")
    parser.add_argument("-p", "--password", dest="password", help="password to use")
    parser.add_argument("-r", "--room", dest="room", help="MUC room to join")
    parser.add_argument("-n", "--nick", dest="nick", help="MUC nickname")

    args = parser.parse_args()

    # Setup logging.
    logging.basicConfig(level=args.loglevel, format="%(levelname)-8s %(message)s")

    args.jid = os.getenv("JID")
    args.room = os.getenv("ROOM")
    args.nick = os.getenv("NICK")

    if args.jid is None:
        args.jid = input("Username: ")
    if args.password is None:
        args.password = getpass("Password: ")
    if args.room is None:
        args.room = input("MUC room: ")
    if args.nick is None:
        args.nick = input("MUC nickname: ")

    # Setup the MUCBot and register plugins. Note that while plugins may
    # have interdependencies, the order in which you register them does
    # not matter.
    xmpp = MUCBot(args.jid, args.password, args.room, args.nick)
    xmpp.register_plugin("xep_0030")  # Service Discovery
    xmpp.register_plugin("xep_0045")  # Multi-User Chat
    xmpp.register_plugin("xep_0199")  # XMPP Ping
    xmpp.register_plugin("xep_0308")  # Last Message Correction

    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp.connect()
    xmpp.process()
