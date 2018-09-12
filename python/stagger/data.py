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

import binascii as _binascii
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

            for repo_id, repo in data["repos"].items():
                self.repos[repo_id] = Repo(**repo)

    def save(self):
        with self._lock:
            temp = f"{self.file_path}.temp"
            data = self.data()

            with open(temp, "w") as f:
                _json.dump(data, f, indent=4)

            _os.rename(temp, self.file_path)

    def data(self):
        repos = dict()

        for repo_id, repo in self.repos.items():
            assert isinstance(repo, Repo), repo

            repos[repo_id] = repo.data()

        return {"repos": repos}

    def json(self):
        return _json.dumps(self.data(), sort_keys=True, indent=4)

    def put_repo(self, repo_id, repo_data):
        with self._lock:
            self.repos[repo_id] = Repo(**repo_data)

        self._modified.set()

    def delete_repo(self, repo_id):
        with self._lock:
            del self.repos[repo_id]

        self._modified.set()

    def put_tag(self, repo_id, tag_id, tag_data):
        with self._lock:
            repo = self.repos.get(repo_id)

            if repo is None:
                repo = Repo(tags={})
                self.repos[repo_id] = repo

            repo.tags[tag_id] = Tag(repo, **tag_data)

        self._modified.set()

    def delete_tag(self, repo_id, tag_id):
        with self._lock:
            del self.repos[repo_id].tags[tag_id]

        self._modified.set()

class DataError(Exception):
    pass

class _DataObject:
    def data(self, exclude=[]):
        fields = dict()

        for name, value in vars(self).items():
            if name in exclude:
                continue

            fields[name] = value

        return fields

    def json(self):
        return _json.dumps(self.data(), sort_keys=True)

    def digest(self):
        return _binascii.crc32(self.json().encode("utf-8"))

class Repo(_DataObject):
    def __init__(self, tags={}):
        super().__init__()

        self.tags = dict()

        for tag_id, tag_data in tags.items():
            self.tags[tag_id] = Tag(self, **tag_data)

    def data(self):
        fields = super().data(exclude=["tags"])
        fields["tags"] = tags = dict()

        for tag_id, tag in self.tags.items():
            tags[tag_id] = tag.data()

        return fields

class Tag(_DataObject):
    def __init__(self, repo, build_id=None, build_url=None, artifacts={}):
        super().__init__()

        self.repo = repo
        self.build_id = build_id
        self.build_url = build_url

        self.artifacts = dict()

        for artifact_id, artifact_data in artifacts.items():
            if "type" not in artifact_data:
                raise DataError(f"Artifact has no type field")

            cls = Artifact._subclasses_by_type[artifact_data["type"]]
            self.artifacts[artifact_id] = cls(self, **artifact_data)

    def data(self):
        fields = super().data(exclude=["repo", "artifacts"])
        fields["artifacts"] = artifacts = dict()

        for artifact_id, artifact in self.artifacts.items():
            artifacts[artifact_id] = artifact.data()

        return fields

class Artifact(_DataObject):
    def __init__(self, tag, type=None):
        super().__init__()

        self.tag = tag
        self.type = type

    def data(self):
        return super().data(exclude=["tag"])

class ContainerImageArtifact(Artifact):
    def __init__(self, tag, type=None, registry_url=None, repository=None, image_id=None):
        super().__init__(tag, type=type)

        self.registry_url = registry_url
        self.repository = repository
        self.image_id = image_id

class MavenArtifact(Artifact):
    def __init__(self, tag, type=None, repository_url=None, group_id=None, artifact_id=None, version=None):
        super().__init__(tag, type=type)

        self.repository_url = repository_url
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.version = version

class FileArtifact(Artifact):
    def __init__(self, tag, type=None, url=None):
        super().__init__(tag, type=type)

        self.url = url

class RpmArtifact(Artifact):
    def __init__(self, tag, type=None, repository_url=None, name=None, version=None, release=None):
        super().__init__(tag, type=type)

        self.repository_url = repository_url
        self.name = name
        self.version = version
        self.release = release

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
            except keyboardinterrupt:
                raise
            except exception:
                _traceback.print_exc()
            finally:
                self.data._modified.clear()

if __name__ == "__main__":
    data = Data("misc/data.json")
    data.load()
    print(data.json())
