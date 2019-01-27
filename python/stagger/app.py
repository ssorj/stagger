#
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

import logging as _logging
import os as _os
import threading as _threading
import time as _time

from .amqpserver import AmqpServer
from .httpserver import HttpServer
from .model import Model

class Application:
    def __init__(self, home, data_dir=None, amqp_port=5672, http_port=8080):
        self.home = home
        self.data_dir = data_dir
        self.amqp_port = amqp_port
        self.http_port = http_port

        if self.data_dir is None:
            self.data_dir = _os.path.join(self.home, "data")

        data_file = _os.path.join(self.data_dir, "data.json")

        self.model = Model(self, data_file)
        self.amqp_server = AmqpServer(self, port=self.amqp_port)
        self.http_server = HttpServer(self, port=self.http_port)

    def run(self):
        _logging.basicConfig(level=_logging.DEBUG)

        if not _os.path.exists(self.data_dir):
            _os.makedirs(self.data_dir)

        self.model.load()
        self.model.start()

        self.amqp_server.start()
        self.http_server.run()

if __name__ == "__main__":
    app = Application(_os.getcwd())
    app.run()
