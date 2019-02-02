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
import logging as _logging
import proton as _proton
import proton.handlers as _handlers
import proton.reactor as _reactor
import threading as _threading

_log = _logging.getLogger("amqpserver")

class AmqpServer(_threading.Thread):
    def __init__(self, app, host="", port=5672):
        super().__init__()

        self.host = host
        self.port = port

        self.container = _reactor.Container(MessagingHandler(self))
        self.container.container_id = f"stagger-{self.container.container_id}"

        self.events = _reactor.EventInjector()
        self.container.selectable(self.events)

        self.daemon = True

    def run(self):
        self.container.run()

    def fire_object_update(self, obj):
        _log.info("Firing update for %s", obj)

        event = _reactor.ApplicationEvent("object_update", subject=obj)
        self.events.trigger(event)

class MessagingHandler(_handlers.MessagingHandler):
    def __init__(self, server):
        super().__init__()

        self.server = server
        self.subscriptions = _collections.defaultdict(dict)

    def on_start(self, event):
        interface = "{0}:{1}".format(self.server.host, self.server.port)

        event.container.listen(interface)

        _log.info("Listening for connections on '%s'", interface)

    def on_connection_opening(self, event):
        event.connection.container = event.container.container_id

    def on_link_opening(self, event):
        if event.link.is_sender:
            assert event.link.remote_source.address is not None

            address = event.link.remote_source.address
            event.link.source.address = address

            self.subscriptions[address][event.link.name] = event.link

    def on_link_closing(self, event):
        if event.link.is_sender:
            address = event.link.source.address
            del self.subscriptions[address][event.link.name]

    def on_object_update(self, event):
        obj = event.subject

        _log.info("Sending updates for %s", obj)

        message = _proton.Message()
        message.content_type = "application/json"
        message.inferred = True
        message.body = obj.json().encode("utf-8")

        for sender in self.subscriptions[obj.event_path].values():
            if sender.credit > 0:
                sender.send(message)
