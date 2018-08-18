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

import json as _json
import logging as _logging
import os as _os
import threading as _threading
import traceback as _traceback

_log = _logging.getLogger("data")

class Data:
    def __init__(self, file_path):
        self.file_path = file_path

        self.tags = dict()

        self.lock = _threading.Lock()
        self.modified = _threading.Event()

        self.save_thread = _SaveThread(self)

    def load(self):
        if not _os.path.exists(self.file_path):
            return

        with open(self.file_path, "r") as f:
            data = _json.load(f)

            assert "tags" in data, "No tags in data"

            for id, value in data["tags"].items():
                self.tags[id] = Tag(**value)

            #print(f"Loaded data from disk: {data}")

    def save(self):
        with self.lock:
            temp = f"{self.file_path}.temp"
            data = {
                "tags": self.tags,
            }

            #print(f"Saving data to disk: {data}")

            with open(temp, "w") as f:
                _json.dump(data, f, indent=4)

            _os.rename(temp, self.file_path)

    def put_tag(self, tag):
        with self.lock:
            self.tags[tag.id] = tag

        self.modified.set()

    def delete_tag(self, id):
        with self.lock:
            del self.tags[id]

        self.modified.set()

class DataError(Exception):
    pass

class _DataObject(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    _fields = ()

    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            name, value = self._process_field(name, value)
            setattr(self, name, value)

        self._check_fields()

    def _process_field(self, name, value):
        if name not in self._fields:
            raise DataError(f"Extra field '{name}'")

        return name, value

    def _check_fields(self):
        for name in self._fields:
            if name not in self:
                raise DataError(f"Missing field '{name}'")

class Tag(_DataObject):
    _fields = "repository", "repository_url", "branch", "name", "commit", "artifacts"

    def _process_field(self, name, value):
        if name not in self._fields:
            raise DataError(f"Extra field '{name}'")

        if name == "artifacts":
            artifacts = dict()

            for iname, ivalue in value.items():
                if "type" not in ivalue:
                    raise DataError(f"Artifact has no type field")

                cls = Artifact._subclasses_by_type[ivalue["type"]]
                artifacts[iname] = cls(**ivalue)

            return name, artifacts

        return name, value

    @property
    def id(self):
        return f"{self.repository}:{self.branch}:{self.name}"

class Artifact(_DataObject):
    _fields = "type"

class ContainerImageArtifact(Artifact):
    _fields = "type", "registry_url", "repository", "id"

class MavenArtifact(Artifact):
    _fields = "type", "repository_url", "group", "artifact", "version"

class FileArtifact(Artifact):
    _fields = "type", "url"

class RpmArtifact(Artifact):
    _fields = "type", "repository_url", "name", "version", "release"

Artifact._subclasses_by_type = {
    "container-image": ContainerImageArtifact,
    "maven": MavenArtifact,
    "file": FileArtifact,
    "rpm": RpmArtifact,
}

class _SaveThread(_threading.Thread):
    def __init__(self, data):
        super().__init__()

        self.data = data
        self.daemon = True

    def run(self):
        while self.data.modified.wait():
            try:
                self.data.save()
            except KeyboardInterrupt:
                raise
            except Exception:
                _traceback.print_exc()
            finally:
                self.data.modified.clear()
