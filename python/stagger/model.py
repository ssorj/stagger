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

_log = _logging.getLogger("model")

class Model:
    def __init__(self, app, data_file):
        self.app = app
        self.data_file = data_file

        self.repos = dict()

        self._lock = _threading.Lock()
        self._modified = _threading.Event()
        self._save_thread = _SaveThread(self)

    def load(self):
        if not _os.path.exists(self.data_file):
            return

        with open(self.data_file, "r") as f:
            data = _json.load(f)

            assert "repos" in data, "No repos field in data"

            for repo_id, repo in data["repos"].items():
                self.repos[repo_id] = Repo(self, **repo)

    def start(self):
        self._save_thread.start()

    def save(self):
        with self._lock:
            temp = f"{self.data_file}.temp"
            data = self.data()

            with open(temp, "w") as f:
                _json.dump(data, f, sort_keys=True)

            _os.rename(temp, self.data_file)

    def data(self):
        repos = dict()

        for repo_id, repo in self.repos.items():
            assert isinstance(repo, Repo), repo
            repos[repo_id] = repo.data()

        return {"repos": repos}

    def json(self):
        return _json.dumps(self.data(), sort_keys=True)

    def put_repo(self, repo_id, repo_data):
        with self._lock:
            self.repos[repo_id] = Repo(self, **repo_data)

        self._modified.set()

    def delete_repo(self, repo_id):
        with self._lock:
            del self.repos[repo_id]

        self._modified.set()

    def put_tag(self, repo_id, tag_id, tag_data):
        with self._lock:
            repo = self.repos.get(repo_id)

            if repo is None:
                repo = Repo(self, tags={})
                self.repos[repo_id] = repo

            repo.tags[tag_id] = Tag(self, repo, **tag_data)
            repo._compute_digest()

        self._modified.set()

    def delete_tag(self, repo_id, tag_id):
        with self._lock:
            repo = self.repos[repo_id]
            del repo.tags[tag_id]
            repo._compute_digest()

        self._modified.set()

class DataError(Exception):
    pass

class _ModelObject:
    def __init__(self, model):
        self.model = model
        self.digest = None

    def data(self, exclude=[]):
        fields = dict()

        for name, value in vars(self).items():
            if name not in ("model", "digest") and name not in exclude:
                fields[name] = value

        return fields

    def json(self):
        return _json.dumps(self.data(), sort_keys=True)

    def _compute_digest(self):
        self.digest = _binascii.crc32(self.json().encode("utf-8"))

class Repo(_ModelObject):
    def __init__(self, model, tags={}):
        super().__init__(model)

        self.tags = dict()

        for tag_id, tag_data in tags.items():
            self.tags[tag_id] = Tag(self.model, self, **tag_data)

        self._compute_digest()

    def data(self):
        fields = super().data(exclude=["tags"])
        fields["tags"] = tags = dict()

        for tag_id, tag in self.tags.items():
            tags[tag_id] = tag.data()

        return fields

class Tag(_ModelObject):
    def __init__(self, model, repo, build_id=None, build_url=None, artifacts={}):
        super().__init__(model)

        self.repo = repo
        self.build_id = build_id
        self.build_url = build_url

        self.artifacts = dict()

        for artifact_id, artifact_data in artifacts.items():
            if "type" not in artifact_data:
                raise DataError(f"Artifact has no type field")

            cls = _Artifact._subclasses_by_type[artifact_data["type"]]
            self.artifacts[artifact_id] = cls(self.model, self, **artifact_data)

        self._compute_digest()

    def data(self):
        fields = super().data(exclude=["repo", "artifacts"])
        fields["artifacts"] = artifacts = dict()

        for artifact_id, artifact in self.artifacts.items():
            artifacts[artifact_id] = artifact.data()

        return fields

class _Artifact(_ModelObject):
    def __init__(self, model, tag, type=None):
        super().__init__(model)

        self.tag = tag
        self.type = type

    def data(self):
        return super().data(exclude=["tag"])

class ContainerImageArtifact(_Artifact):
    def __init__(self, model, tag, type=None, registry_url=None, repository=None, image_id=None):
        super().__init__(model, tag, type=type)

        self.registry_url = registry_url
        self.repository = repository
        self.image_id = image_id

        self._compute_digest()

class MavenArtifact(_Artifact):
    def __init__(self, model, tag, type=None, repository_url=None, group_id=None, artifact_id=None, version=None):
        super().__init__(model, tag, type=type)

        self.repository_url = repository_url
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.version = version

        self._compute_digest()

class FileArtifact(_Artifact):
    def __init__(self, model, tag, type=None, url=None):
        super().__init__(model, tag, type=type)

        self.url = url

        self._compute_digest()

class RpmArtifact(_Artifact):
    def __init__(self, model, tag, type=None, repository_url=None, name=None, version=None, release=None):
        super().__init__(model, tag, type=type)

        self.repository_url = repository_url
        self.name = name
        self.version = version
        self.release = release

        self._compute_digest()

_Artifact._subclasses_by_type = {
    "container-image": ContainerImageArtifact,
    "maven": MavenArtifact,
    "file": FileArtifact,
    "rpm": RpmArtifact,
}

class _SaveThread(_threading.Thread):
    def __init__(self, model):
        super().__init__()

        self.model = model
        self.daemon = True

    def run(self):
        while self.model._modified.wait():
            try:
                self.model.save()
            except keyboardinterrupt:
                raise
            except exception:
                _traceback.print_exc()
            finally:
                self.model._modified.clear()

if __name__ == "__main__":
    model = Model(None, "misc/data.json")
    model.load()
    print(model.json())
