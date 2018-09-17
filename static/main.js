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

        for (let repoId of Object.keys(this.state.data["repos"])) {
            let repoElem = gesso.createDiv(elem, "repo", repoId);
        }

        //this.renderHeader(elem);
        //this.renderBody(elem);
        //this.renderFooter(elem);

        gesso.replaceElement($("#content"), elem);
    }
}
