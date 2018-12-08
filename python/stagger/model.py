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
        self.revision = 0

        self._lock = _threading.Lock()
        self._modified = _threading.Event()
        self._save_thread = _SaveThread(self)

    def load(self):
        if not _os.path.exists(self.data_file):
            return

        with open(self.data_file, "r") as f:
            data = _json.load(f)

            assert "repos" in data, "No repos field in data"
            assert "revision" in data, "No revision field in data"

            for repo_id, repo_data in data["repos"].items():
                repo = _Repo(self, repo_id, **repo_data)
                self.repos[repo_id] = repo

            self.revision = data["revision"]

    def start(self):
        self._save_thread.start()

    def mark_modified(self):
        self.revision += 1
        self._modified.set()

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
            assert isinstance(repo, _Repo), repo
            repos[repo_id] = repo.data()

        return {
            "repos": repos,
            "revision": self.revision,
        }

    def json(self):
        return _json.dumps(self.data(), sort_keys=True)

    def put_repo(self, repo_id, repo_data):
        with self._lock:
            repo = _Repo(self, repo_id, **repo_data)
            self.repos[repo_id] = repo

            repo.mark_modified()

        self.app.amqp_server.fire_object_update(repo)

    def delete_repo(self, repo_id):
        with self._lock:
            del self.repos[repo_id]
            self.mark_modified()

    def put_branch(self, repo_id, branch_id, branch_data):
        with self._lock:
            repo = self.repos.get(repo_id)

            if repo is None:
                repo = _Repo(self, repo_id)
                self.repos[repo_id] = repo

            branch = _Branch(self, branch_id, repo, **branch_data)
            repo.branches[branch_id] = branch

            branch.mark_modified()

        self.app.amqp_server.fire_object_update(branch)
        self.app.amqp_server.fire_object_update(repo)

    def delete_branch(self, repo_id, branch_id):
        with self._lock:
            repo = self.repos[repo_id]

            del repo.branches[branch_id]

            repo.mark_modified()

        # XXX object update when child is removed?

    def put_tag(self, repo_id, branch_id, tag_id, tag_data):
        with self._lock:
            repo = self.repos.get(repo_id)

            if repo is None:
                repo = _Repo(self, repo_id)
                self.repos[repo_id] = repo

            branch = repo.branches.get(branch_id)

            if branch is None:
                branch = _Branch(self, branch_id, repo)
                repo.branches[branch_id] = branch

            tag = _Tag(self, tag_id, branch, **tag_data)
            branch.tags[tag_id] = tag

            tag.mark_modified()

        self.app.amqp_server.fire_object_update(tag)
        self.app.amqp_server.fire_object_update(branch)
        self.app.amqp_server.fire_object_update(repo)

    def delete_tag(self, repo_id, branch_id, tag_id):
        with self._lock:
            repo = self.repos[repo_id]
            branch = repo.branches[branch_id]

            del branch.tags[tag_id]

            branch.mark_modified()

    def put_artifact(self, repo_id, branch_id, tag_id, artifact_id, artifact_data):
        with self._lock:
            repo = self.repos.get(repo_id)

            if repo is None:
                repo = _Repo(self, repo_id)
                self.repos[repo_id] = repos

            branch = repo.branches.get(branch_id)

            if branch is None:
                branch = _Branch(self, branch_id)
                self.branches[branch_id] = branch

            tag = branch.tags.get(tag_id)

            if tag is None:
                tag = _Tag(self, tag_id, repo)
                branch.tags[tag_id] = tag

            artifact = _Artifact.create(self, artifact_id, tag, **artifact_data)
            tag.artifacts[artifact_id] = artifact

            artifact.mark_modified()

        self.app.amqp_server.fire_object_update(artifact)
        self.app.amqp_server.fire_object_update(tag)
        self.app.amqp_server.fire_object_update(branch)
        self.app.amqp_server.fire_object_update(repo)

    def delete_artifact(self, repo_id, branch_id, tag_id, artifact_id):
        with self._lock:
            repo = self.repos[repo_id]
            branch = repo.branches[branch_id]
            tag = branch.tags[tag_id]

            del tag.artifacts[artifact_id]

            tag.mark_modified()

class DataError(Exception):
    pass

class _ModelObject:
    _child_vars = []

    def __init__(self, model, id, parent, path):
        self._model = model
        self._id = id
        self._parent = parent
        self._digest = None

        self.path = path

        if self.path is None:
            parent_path = None

            if self._parent is not None:
                parent_path = self._parent.path

            self.path = self._path_template.format(parent_path=parent_path, id=self._id)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path})"

    def data(self):
        fields = dict()

        for name, value in vars(self).items():
            if name.startswith("_"):
                continue

            if name in self._child_vars:
                value = self._child_data(value)

            fields[name] = value

        return fields

    def _child_data(self, children):
        data = dict()

        for child_id, child in children.items():
            data[child_id] = child.data()

        return data

    def json(self):
        return _json.dumps(self.data(), sort_keys=True)

    def mark_modified(self):
        self._compute_digest()
        self._model.mark_modified()

    def _compute_digest(self):
        self._digest = _binascii.crc32(self.json().encode("utf-8"))

        if self._parent is not None:
            self._parent._compute_digest()

class _Repo(_ModelObject):
    _path_template = "repos/{id}"
    _child_vars = ["branches"]

    def __init__(self, model, id, path=None, branches={}):
        super().__init__(model, id, None, path)

        self.branches = dict()

        for branch_id, branch_data in branches.items():
            branch = _Branch(self._model, branch_id, self, **branch_data)
            self.branches[branch_id] = branch

class _Branch(_ModelObject):
    _path_template = "{parent_path}/branches/{id}"
    _child_vars = ["tags"]

    def __init__(self, model, id, parent, path=None, tags={}):
        super().__init__(model, id, parent, path)

        self.tags = dict()

        for tag_id, tag_data in tags.items():
            tag = _Tag(self._model, tag_id, self, **tag_data)
            self.tags[tag_id] = tag

class _Tag(_ModelObject):
    _path_template = "{parent_path}/tags/{id}"
    _child_vars = ["artifacts"]

    def __init__(self, model, id, parent,
                 path=None, build_id=None, build_url=None, artifacts={}):
        super().__init__(model, id, parent, path)

        self.build_id = build_id
        self.build_url = build_url
        self.artifacts = dict()

        for artifact_id, artifact_data in artifacts.items():
            artifact = _Artifact.create(self._model, artifact_id, self, **artifact_data)
            self.artifacts[artifact_id] = artifact

class _Artifact(_ModelObject):
    _path_template = "{parent_path}/artifacts/{id}"

    @staticmethod
    def create(model, id, parent, **artifact_data):
        if "type" not in artifact_data:
            raise DataError("Artifact data has no type field")

        type = artifact_data["type"]
        cls = _Artifact._subclasses_by_type[type]
        obj = cls(model, id, parent, **artifact_data)

        return obj

    def __init__(self, model, id, parent, path, type):
        super().__init__(model, id, parent, path)

        self.type = type

class _ContainerArtifact(_Artifact):
    def __init__(self, model, id, parent,
                 path=None, type=None, registry_url=None, repository=None, image_id=None):
        super().__init__(model, id, parent, path, type)

        self.registry_url = registry_url
        self.repository = repository
        self.image_id = image_id

class _MavenArtifact(_Artifact):
    def __init__(self, model, id, parent,
                 path=None, type=None, repository_url=None, group_id=None, artifact_id=None,
                 version=None):
        super().__init__(model, id, parent, path, type)

        self.repository_url = repository_url
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.version = version

class _FileArtifact(_Artifact):
    def __init__(self, model, id, parent, path=None, type=None, url=None):
        super().__init__(model, id, parent, path, type)

        self.url = url

class _RpmArtifact(_Artifact):
    def __init__(self, model, id, parent,
                 path=None, type=None, repository_url=None, name=None, version=None,
                 release=None):
        super().__init__(model, id, parent, path, type)

        self.repository_url = repository_url
        self.name = name
        self.version = version
        self.release = release

_Artifact._subclasses_by_type = {
    "container": _ContainerArtifact,
    "maven": _MavenArtifact,
    "file": _FileArtifact,
    "rpm": _RpmArtifact,
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
