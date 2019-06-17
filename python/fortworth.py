import requests as _requests

from plano import *

_stagger_http_url = ENV.get("STAGGER_HTTP_URL")
_bodega_url = ENV.get("BODEGA_URL")

_yum_repo_config_template = """
[{repo}-{branch}-{build_id}]
name={repo}-{branch}-{build_id}
baseurl={yum_repo_url}
enabled=1
gpgcheck=0
skip_if_unavailable=1

# Yum repo install command:
#
# sudo curl {yum_repo_url}/config.txt -o /etc/yum.repos.d/{repo}.repo
"""

_global_maven_options = "-B -q"

class BuildData(object):
    def __init__(self, repo, branch, id, url=None):
        assert repo
        assert branch

        self.repo = repo
        self.branch = branch
        self.id = id
        self.url = url

def git_current_source_url(checkout_dir):
    with working_dir(checkout_dir):
        return call_for_stdout("git config --get remote.origin.url").strip()

def git_current_commit(checkout_dir):
    with working_dir(checkout_dir):
        return call_for_stdout("git rev-parse HEAD").strip()

def git_current_commit_url(checkout_dir):
    source_url = git_current_source_url(checkout_dir)
    commit = git_current_commit(checkout_dir)

    if source_url.startswith("https://github.com/"):
        try:
            party, repo = source_url[19:].split("/", 1)
        except IndexError:
            return

        if repo.endswith(".git"):
            repo = repo[0:-4]

        return "https://github.com/{0}/{1}/commit/{2}".format(party, repo, commit)

def git_current_branch(checkout_dir):
    with working_dir(checkout_dir):
        return call_for_stdout("git rev-parse --abbrev-ref HEAD").strip()

def git_make_archive(checkout_dir, output_dir, archive_stem):
    output_dir = get_absolute_path(output_dir)
    output_file = join(output_dir, "{0}.tar.gz".format(archive_stem))

    make_dir(output_dir)

    with working_dir(checkout_dir):
        call("git archive --output {0} --prefix {1}/ HEAD", output_file, archive_stem)

    return output_file

def stagger_get_data(service_url=_stagger_http_url):
    assert service_url

    url = "{0}/api/data".format(service_url)

    response = _requests.get(url)
    response.raise_for_status()

    return response.json()

def stagger_get_tag(repo, branch, tag, service_url=_stagger_http_url):
    assert service_url

    url = "{0}/api/repos/{1}/branches/{2}/tags/{3}".format(service_url, repo, branch, tag)

    response = _requests.get(url)
    response.raise_for_status()

    return response.json()

def stagger_put_tag(repo, branch, tag, tag_data, service_url=_stagger_http_url, dry_run=False):
    assert service_url

    url = "{0}/api/repos/{1}/branches/{2}/tags/{3}".format(service_url, repo, branch, tag)

    if dry_run:
        url += "?dry-run=1"

    response = _requests.put(url, json=tag_data)
    response.raise_for_status()

    return response.text

def stagger_get_artifact(repo, branch, tag, artifact, service_url=_stagger_http_url):
    assert service_url

    url = "{0}/api/repos/{1}/branches/{2}/tags/{3}/artifacts/{4}".format(service_url, repo, branch, tag, artifact)

    response = _requests.get(url)
    response.raise_for_status()

    return response.json()

def stagger_put_artifact(repo, branch, tag, artifact, artifact_data, service_url=_stagger_http_url, dry_run=False):
    assert service_url

    url = "{0}/api/repos/{1}/branches/{2}/tags/{3}/artifacts/{4}".format(service_url, repo, branch, tag, artifact)

    if dry_run:
        url += "?dry-run=1"

    response = _requests.put(url, json=artifact_data)
    response.raise_for_status()

    return response.text

def bodega_put_build(build_dir, build_data, service_url=_bodega_url):
    build_url = bodega_build_url(build_data, service_url=service_url)
    session = _requests.Session()

    for fs_path in find(build_dir):
        if is_dir(fs_path):
            continue

        relative_path = fs_path[len(build_dir) + 1:]
        request_url = "{0}/{1}".format(build_url, relative_path)

        if build_data.id is None:
            request_url += "?dry-run=1"

        with open(fs_path, "rb") as f:
            response = session.put(request_url, data=f)
            response.raise_for_status()

def bodega_build_exists(build_data, service_url=_bodega_url):
    build_url = bodega_build_url(build_data, service_url=service_url)

    response = _requests.get(build_url)

    return response.status_code == _requests.codes.ok

def bodega_build_url(build_data, service_url=_bodega_url):
    assert service_url
    return "{0}/{1}/{2}/{3}".format(service_url, build_data.repo, build_data.branch, build_data.id)

def rpm_make_yum_repo_config(build_data):
    repo = build_data.repo
    branch = build_data.branch
    build_id = build_data.id
    yum_repo_url = _yum_repo_url(build_data)

    return _yum_repo_config_template.lstrip().format(**locals())

def rpm_install_tag_packages(repo, branch, tag, *packages):
    tag_data = stagger_get_tag(repo, branch, tag)

    for package in packages:
        yum_repo_url = tag_data["artifacts"][package]["repository_url"]
        url = "{0}/config.txt".format(yum_repo_url)

        with temp_file() as f:
            http_get(url, output_file=f)
            call("sudo cp {0} {1}", f, "/etc/yum.repos.d/{0}.repo".format(repo))

        call("sudo yum -y install {0}", package)

def rpm_configure(input_spec_file, output_spec_file, source_dir, build_id, **substitutions):
    assert input_spec_file.endswith(".in"), input_spec_file
    assert is_dir(join(source_dir, ".git"))

    if build_id is None:
        build_id = 0

    commit = git_current_commit(source_dir)
    release = "0.{0}.{1}".format(build_id, commit[:8])

    configure_file(input_spec_file, output_spec_file, release=release, **substitutions)

def rpm_build(spec_file, source_dir, build_dir, build_data):
    records = call_for_stdout("rpm -q --qf '%{{name}}-%{{version}}\n' --specfile {0}", spec_file)
    archive_stem = records.split()[0]
    rpms_dir = join(build_dir, "RPMS")
    dist_dir = make_dir(join(build_dir, "dist"))
    yum_repo_dir = join(dist_dir, "repo")
    yum_repo_config = rpm_make_yum_repo_config(build_data)
    yum_repo_file = join(yum_repo_dir, "config.txt")

    git_make_archive(source_dir, join(build_dir, "SOURCES"), archive_stem)
    call("rpmbuild -D '_topdir {0}' -ba {1}", get_absolute_path(build_dir), spec_file)
    copy(rpms_dir, yum_repo_dir)
    call("createrepo {0}", yum_repo_dir)
    write(yum_repo_file, yum_repo_config)

def rpm_publish(spec_file, source_dir, build_dir, build_data, tag):
    # Skip developer test builds
    if build_data.id is None:
        return

    if not bodega_build_exists(build_data):
        bodega_put_build(join(build_dir, "dist"), build_data)

    tag_data = _rpm_make_tag_data(spec_file, source_dir, build_data)

    stagger_put_tag(build_data.repo, build_data.branch, tag, tag_data)

def _rpm_make_tag_data(spec_file, source_dir, build_data):
    records = call_for_stdout("rpm -q --qf '%{{name}},%{{version}},%{{release}}\n' --specfile {0}", spec_file)
    artifacts = dict()

    for record in records.split():
        name, version, release = record.split(",")

        artifact = {
            "type": "rpm",
            "repository_url": _yum_repo_url(build_data),
            "name": name,
            "version": version,
            "release": release,
        }

        artifacts[name] = artifact

    tag = {
        "build_id": build_data.id,
        "build_url": build_data.url,
        "commit_id": git_current_commit(source_dir),
        "commit_url": git_current_commit_url(source_dir),
        "artifacts": artifacts,
    }

    return tag

# mvn versions:use-dep-version -Dincludes=junit:junit -DdepVersion=1.0 -DforceVersion=true

def maven_build(source_dir, build_dir, build_data, repo_urls=[], properties={}):
    maven_repo_dir = get_absolute_path(join(build_dir, "repo"))
    settings_file = _make_settings_file(repo_urls)

    with working_dir(source_dir):
        commit_id = git_current_commit(".")
        version = call_for_stdout("mvn {0} -Dexec.executable=echo -Dexec.args='${{project.version}}' --non-recursive exec:exec", _global_maven_options)
        version = version.strip()
        version = version.replace("SNAPSHOT", "{0}.{1}".format(build_data.id, commit_id[:8]))

        call("mvn {0} -DnewVersion={1} versions:set", _global_maven_options, version)

        options = [
            "-U",
            "-DskipTests",
            "-Dmaven.repo.local={0}".format(maven_repo_dir),
            "-gs", settings_file,
        ]

        for name, value in properties.items():
            options.append("-D{0}={1}".format(name, value))

        call("mvn {0} {1} install", _global_maven_options, " ".join(options))

def _make_settings_file(repo_urls):
    repos = list()

    for i, url in enumerate(repo_urls):
        repos.append("<repository><id>repo-{0}</id><url>{1}</url></repository>".format(i, url))

    repos = "".join(repos)

    xml = """
    <settings>
      <profiles>
        <profile>
          <id>main</id>
          <repositories>
            {repos}
          </repositories>
        </profile>
      </profiles>
      <activeProfiles>
        <activeProfile>main</activeProfile>
      </activeProfiles>
    </settings>
    """

    xml = xml.strip().format(**locals())

    return write(make_temp_file(), xml)

def maven_publish(source_dir, build_dir, build_data, tag):
    # Skip developer test builds
    if build_data.id is None:
        return

    if not bodega_build_exists(build_data):
        bodega_put_build(build_dir, build_data)

    tag_data = _maven_make_tag_data(source_dir, build_dir, build_data)

    stagger_put_tag(build_data.repo, build_data.branch, tag, tag_data)

def _maven_make_tag_data(source_dir, build_dir, build_data):
    maven_repo_dir = get_absolute_path(join(build_dir, "repo"))
    artifacts = dict()

    with working_dir(source_dir):
        records = call_for_stdout("mvn {0} -Dmaven.repo.local={1} -Dexec.executable=echo -Dexec.args='${{project.groupId}},${{project.artifactId}},${{project.version}}' exec:exec",
                                  _global_maven_options, maven_repo_dir)

    for record in records.split():
        group_id, artifact_id, version = record.split(",")

        artifact = {
            "type": "maven",
            "repository_url": _maven_repo_url(build_data),
            "group_id": group_id,
            "artifact_id": artifact_id,
            "version": version,
        }

        artifacts[artifact_id] = artifact

    data = {
        "build_id": build_data.id,
        "build_url": build_data.url,
        "commit_id": git_current_commit(source_dir),
        "commit_url": git_current_commit_url(source_dir),
        "artifacts": artifacts,
    }

    return data

def _yum_repo_url(build_data, service_url=_bodega_url):
    assert service_url
    return "{0}/repo".format(bodega_build_url(build_data, service_url=service_url))

def _maven_repo_url(build_data, service_url=_bodega_url):
    assert service_url
    return "{0}/repo".format(bodega_build_url(build_data, service_url=service_url))
