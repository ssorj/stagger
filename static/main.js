/*
 *
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 *
 */

"use strict";

const gesso = new Gesso();

class Stagger {
    constructor() {
        this.state = {
            query: {
            },
            data: null,
            dataFetchState: null,
            renderTime: null,
        };

        window.addEventListener("statechange", (event) => {
            this.renderPage();
        });

        window.addEventListener("load", (event) => {
            if (window.location.search) {
                this.state.query = gesso.parseQueryString(window.location.search);
            }

            this.state.dataFetchState = gesso.fetchPeriodically("/api/data", (data) => {
                this.state.data = data;
                window.dispatchEvent(new Event("statechange"));
            });

            //window.setInterval(() => { this.checkFreshness }, 60 * 1000);
        });

        window.addEventListener("popstate", (event) => {
            this.state.query = event.state;
            window.dispatchEvent(new Event("statechange"));
        });
    }

    renderPage() {
        console.log("Rendering page");

        this.state.renderTime = new Date().getTime();

        let elem = gesso.createDiv(null, "#content");
        let repos = this.state.data["repos"];

        for (let repoId of Object.keys(repos)) {
            let repo = repos[repoId];
            let repoDataUrl = `/pretty.html?url=/api/repos/${repoId}`
            let repoElem = gesso.createDiv(elem, "repo");

            gesso.createDiv(repoElem, "repo-id", repoId);
            gesso.createLink(repoElem, repoDataUrl,
                             {"text": "Data", "class": "repo-data"});

            for (let tagId of Object.keys(repo["tags"])) {
                let tag = repo["tags"][tagId];
                let tagDataUrl = `/pretty.html?url=/api/repos/${repoId}/tags/${tagId}`
                let tagElem = gesso.createDiv(repoElem, "tag");

                gesso.createDiv(tagElem, "tag-id", tagId);
                gesso.createLink(tagElem, tagDataUrl,
                                 {"text": "Data", "class": "tag-data"});
                gesso.createLink(tagElem, tag["build_url"],
                                 {"text": tag["build_id"], "class": "tag-build"});

                for (let artifactId of Object.keys(tag["artifacts"])) {
                    let artifact = tag["artifacts"][artifactId];
                    let artifactDataUrl = `/pretty.html?url=/api/repos/${repoId}/tags/${tagId}/artifacts/${artifactId}`
                    let artifactElem = gesso.createDiv(tagElem, "artifact");

                    let artifactUrl = artifactDataUrl;
                    let coords;

                    switch (artifact["type"]) {
                    case "container":
                        coords = `${artifact["repository"]}/${artifact["image_id"]}`;
                        artifactUrl = artifact["registry_url"];
                        break;
                    case "file":
                        coords = artifact["url"];
                        artifactUrl = artifact["url"];
                    case "maven":
                        coords = `${artifact["group_id"]}:${artifact["artifact_id"]}:${artifact["version"]}`;
                        artifactUrl = artifact["repository_url"];
                        break;
                    case "rpm":
                        coords = `${artifact["name"]}-${artifact["version"]}-${artifact["release"]}`;
                        artifactUrl = artifact["repository_url"];
                        break;
                    }

                    gesso.createDiv(artifactElem, "artifact-id", artifactId);
                    gesso.createLink(artifactElem, artifactDataUrl,
                                     {"text": "Data", "class": "artifact-data"});
                    gesso.createLink(artifactElem, artifactUrl,
                                     {"text": coords, "class": "artifact-coords"});
                }
            }
        }

        gesso.replaceElement($("#content"), elem);
    }
}
