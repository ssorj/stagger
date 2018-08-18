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

var transom = {
    getDescendant: function(elem, path) {
        var names = path.split(".");
        var node = elem;

        for (var i = 0; i < names.length; i++) {
            var elems = node.getElementsByTagName(names[i]);

            if (elems.length === 0) {
                return null;
            }

            node = elems[0];
        }

        return node;
    },

    getHeadings: function() {
        var tags = ["h", "h1", "h2", "h3", "h4", "h5", "h6"];
        var headings = [];

        for (var i = 0; i < tags.length; i++) {
            var tag = tags[i];
            var elems = document.getElementsByTagName(tag);

            for (var j = 0; j < elems.length; j++) {
                var elem = elems[j];
                headings.push(elem);
            }
        }

        return headings;
    },

    addHeadingAnchors: function() {
        console.log("Adding heading anchors");

        var headings = transom.getHeadings();

        for (var i = 0; i < headings.length; i++) {
            var heading = headings[i];
            var id = heading.id;

            if (!id) {
                var docbookAnchor = transom.getDescendant(heading, "a");

                if (docbookAnchor) {
                    id = docbookAnchor.id;
                }
            }

            if (!id) {
                continue;
            }

            var anchor = document.createElement("a");
            anchor.className = "heading-link";
            anchor.href = "#" + id;

            var text = document.createTextNode("\u00a7");
            anchor.appendChild(text);

            heading.appendChild(anchor);
        }
    },

    updateHeadingSelection: function() {
        var hash = window.location.hash;

        if (!hash) {
            return;
        }

        console.log("Updating the selected heading");

        /* Clear any existing selections */

        var headings = transom.getHeadings();

        for (var i = 0; i < headings.length; i++) {
            var heading = headings[i];

            if (heading.className === "selected") {
                heading.className = "";
            }
        }

        /* Mark the current selection */

        var elem = document.getElementById(hash.substring(1));

        if (!elem) {
            return;
        }

        elem.className = "selected";
    }
}

window.addEventListener("load", transom.updateHeadingSelection);
window.addEventListener("load", transom.addHeadingAnchors);
window.addEventListener("hashchange", transom.updateHeadingSelection);
