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

        self.repos = dict()

        self._lock = _threading.Lock()
        self._modified = _threading.Event()

        self.save_thread = _SaveThread(self)

    def load(self):
        if not _os.path.exists(self.file_path):
            return

        with open(self.file_path, "r") as f:
            data = _json.load(f)

            assert "repos" in data, "No repos field in data"

            for id, value in data["repos"].items():
                self.repos[id] = Repo(**value)

    def save(self):
        with self._lock:
            temp = f"{self.file_path}.temp"
            data = {
                "repos": self.repos,
            }

            with open(temp, "w") as f:
                _json.dump(data, f, indent=4)

            _os.rename(temp, self.file_path)

    def put_repo(self, repo_id, repo):
        with self._lock:
            self.repos[repo_id] = repo

        self._modified.set()

    def delete_repo(self, repo_id):
        with self._lock:
            del self.repos[repo_id]

        self._modified.set()

    def put_tag(self, repo_id, tag_id, tag):
        with self._lock:
            repo = self.repos.get(repo_id)

            if repo is None:
                repo = Repo(tags={})
                self.repos[repo_id] = repo

            repo.tags[tag_id] = tag

        self._modified.set()

    def delete_tag(self, repo_id, tag_id):
        with self._lock:
            del self.repos[repo_id].tags[tag_id]

        self._modified.set()

class DataError(Exception):
    pass

class _DataObject(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    _fields = []

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

class Repo(_DataObject):
    _fields = ["tags"]

    def _process_field(self, name, value):
        if name not in self._fields:
            raise DataError(f"Extra field '{name}'")

        if name == "tags":
            return name, {k: Tag(**v) for k, v in value.items()}

        return name, value

class Tag(_DataObject):
    _fields = ["build_id", "build_url", "artifacts"]

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

class Artifact(_DataObject):
    _fields = "type"

class ContainerImageArtifact(Artifact):
    _fields = "type", "registry_url", "repository", "image_id"

class MavenArtifact(Artifact):
    _fields = "type", "repository_url", "group_id", "artifact_id", "version"

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
        while self.data._modified.wait():
            try:
                self.data.save()
            except KeyboardInterrupt:
                raise
            except Exception:
                _traceback.print_exc()
            finally:
                self.data._modified.clear()
