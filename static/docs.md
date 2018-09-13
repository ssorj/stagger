# Stagger

A service for tagging software builds and describing the resulting
build artifacts.  A Stagger tag binds a well-known name to a concrete,
installable version of your software.

## Source repos

A source repo is a named container for tags corresponding to a
particular source code repository.

A repo is identified by an arbitrary ID.  I recommend using a name
that matches the referenced repository.

<pre>
<b>GET /api/repos/&lt;repo-id&gt;</b>
<b>PUT /api/repos/&lt;repo-id&gt;</b>

{
    "tags": {
        "&lt;tag-id&gt;": { /* Tag fields */ },
        "&lt;tag-id&gt;": { /* Tag fields */ },
        "&lt;tag-id&gt;": { /* Tag fields */ }
    }
}
</pre>

<pre>
<b>GET /api/repos</b>

{
    "&lt;repo-id&gt;": { /* Repo fields */ },
    "&lt;repo-id&gt;": { /* Repo fields */ },
    "&lt;repo-id&gt;": { /* Repo fields */ }
}
</pre>

<pre>
<b>DELETE /api/repos/&lt;repo-id&gt;</b>
</pre>

## Build tags

A build tag is a stable name representing a build with a particular
status, such as "untested", "tested", or "released".

A tag is identified by an arbitrary ID.  The tag ID is meant for use
in the context of multiple repos and branches, so it is important
to qualify it.  I recommend IDs of the form
<code>&lt;source-repo-branch&gt;-&lt;status&gt;</code>.

A tag contains a set of named artifacts.

<pre>
<b>GET /api/repos/&lt;repo-id&gt;/tags/&lt;tag-id&gt;</b>
<b>PUT /api/repos/&lt;repo-id&gt;/tags/&lt;tag-id&gt;</b>

{
    "build_id": "&lt;build-id&gt;",
    "build_url": "&lt;build-url&gt;",
    "artifacts": {
        "&lt;artifact-id&gt;": { /* Artifact fields */ },
        "&lt;artifact-id&gt;": { /* Artifact fields */ },
        "&lt;artifact-id&gt;": { /* Artifact fields */ }
    }
}
</pre>

<pre>
<b>GET /api/repos/&lt;repo-id&gt;/tags</b>

{
    "&lt;tag-id&gt;": { /* Tag fields */ },
    "&lt;tag-id&gt;": { /* Tag fields */ },
    "&lt;tag-id&gt;": { /* Tag fields */ }
}
</pre>

<pre>
<b>DELETE /api/repos/&lt;repo-id&gt;/tags/&lt;tag-id&gt;</b>
</pre>

## Build artifacts

A build artifact holds the details to required to get and install one
of the build outputs, such as Maven artifacts or container images.
Different artifact types have different fields.

<pre>
<b>GET /api/repos/&lt;repo-id&gt;/tags/&lt;tag-id&gt;/artifacts/&lt;artifact-id&gt;</b>

{
    "type": "&lt;artifact-type&gt;",
    /* Type-specific fields */
}
</pre>

<pre>
<b>GET /api/repos/&lt;repo-id&gt;/tags/&lt;tag-id&gt;/artifacts</b>

{
    "&lt;artifact-id&gt;": { /* Artifact fields */ },
    "&lt;artifact-id&gt;": { /* Artifact fields */ },
    "&lt;artifact-id&gt;": { /* Artifact fields */ }
}
</pre>

An artifact is identified by an arbitrary ID.  I suggest some
conventions for these below.

### Arbitrary files

I recommend IDs of the form
<code>&lt;file-name&gt;-&lt;file-type&gt;</code> (but without any
unstable version part), as in <code>amq-broker-zip</code>.

<pre>
{
    "type": "file",
    "url": "&lt;file-url&gt;"
}
</pre>

### Container images

I recommend IDs of the form
<code>&lt;repository-name&gt;-container</code>, as in
<code>amq-interconnect-container</code>.

<pre>
{
    "type": "container",
    "registry_url": "&lt;container-registry-url&gt;",
    "repository": "&lt;repository-name&gt;",
    "image_id": "&lt;image-id&gt;"
}
</pre>

### Maven artifacts

I recommend IDs of the form
<code>&lt;maven-artifact-id&gt;-maven</code>, as in
<code>qpid-jms-client-maven</code>.

<pre>
{
    "type": "maven",
    "repository_url": "&lt;maven-repo-url&gt;",
    "group_id": "&lt;maven-group-id&gt;",
    "artifact_id": "&lt;maven-artifact-id&gt;",
    "version": "&lt;maven-version&gt;"
}
</pre>

### RPM packages

I recommend IDs of the form
<code>&lt;package-name&gt;-&lt;dist&gt;-rpm</code>, as in
<code>qpid-proton-cpp-devel-el7-rpm</code>.

<pre>
{
    "type": "rpm",
    "repository_url": "&lt;package-repo-url&gt;",
    "name": "&lt;package-name&gt;",
    "version": "&lt;package-version&gt;"
    "release": "&lt;package-release&gt;",
}
</pre>
