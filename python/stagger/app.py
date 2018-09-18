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

import os as _os

from .model import *
from .httpserver import *

class Application:
    def __init__(self, home, data_dir=None, http_port=None):
        self.home = home
        self.data_dir = data_dir
        self.http_port = http_port

        if self.data_dir is None:
            self.data_dir = _os.path.join(self.home, "data")

        if self.http_port is None:
            self.http_port = 8080

        self.model = None

    def run(self):
        assert self.model is None

        if not _os.path.exists(self.data_dir):
            _os.makedirs(self.data_dir)

        data_file = _os.path.join(self.data_dir, "data.json")
            
        self.model = Model(self, data_file)
        self.model.load()
        self.model.start()

        server = HttpServer(self, port=self.http_port)
        server.run()

if __name__ == "__main__":
    app = Application(_os.getcwd())
    app.run()
