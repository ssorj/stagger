# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

import collections as _collections
import os as _os
import logging as _logging
import proton as _proton
import proton.handlers as _handlers
import proton.reactor as _reactor
import uuid as _uuid
import shutil as _shutil
import subprocess as _subprocess
import sys as _sys
import tempfile as _tempfile
import threading as _threading

_log = _logging.getLogger("amqpserver")

class _AmqpServer(_threading.Thread):
    def __init__(self, app, host="0.0.0.0", port=5672):
        super().__init__()

        self.host = host
        self.port = port

        self.container = _reactor.Container(_Handler(self))

        self.events = _reactor.EventInjector()
        self.container.selectable(self.events)

        # XXX Replace this with orderly stop
        self.daemon = True

    def run(self):
        self.container.run()

    def fire_repo_update(self, repo):
        _log.info("Firing update for %s", repo)

        event = _reactor.ApplicationEvent("repo_update", subject=repo)
        self.events.trigger(event)

    def fire_tag_update(self, tag):
        _log.info("Firing update for %s", tag)

        event = _reactor.ApplicationEvent("tag_update", subject=tag)
        self.events.trigger(event)

    def fire_artifact_update(self, artifact):
        _log.info("Firing update for %s", artifact)

        event = _reactor.ApplicationEvent("artifact_update", subject=artifact)
        self.events.trigger(event)

class _Handler(_handlers.MessagingHandler):
    def __init__(self, server):
        super(_Handler, self).__init__()

        self.server = server
        self.subscriptions = dict()

    def on_start(self, event):
        interface = "{0}:{1}".format(self.server.host, self.server.port)

        self.acceptor = event.container.listen(interface)

        _log.info("Listening for connections on '%s'", interface)

    def on_connection_opening(self, event):
        # XXX I think this should happen automatically
        event.connection.container = event.container.container_id

    def on_connection_opened(self, event):
        _log.info("Opened connection from %s", event.connection)

    def on_connection_closed(self, event):
        _log.info("Closed connection from %s", event.connection)

    def on_disconnected(self, event):
        _log.info("Disconnected from %s", event.connection)

    def on_link_opening(self, event):
        if event.link.is_sender:
            assert event.link.remote_source.address is not None

            event.link.source.address = event.link.remote_source.address

            self.subscriptions[event.link.name] = event.link

    def on_link_closed(self, event):
        if event.link.is_sender:
            del self.subscriptions[event.link.name]

    def on_repo_update(self, event):
        repo = event.subject

        for sender in self.subscriptions.values():
            print(111, sender.source.address)
            print(222, repo.path)
            
            if sender.credit > 0 and sender.source.address == repo.path:
                _log.info("Sending update for %s", repo.path)
                sender.send(_proton.Message(repo.json()))

    # def on_tag_update(self, event):
    #     tag_id, tag = event.subject
    #     tag_path = 
