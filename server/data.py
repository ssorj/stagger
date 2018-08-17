data = {
    "tags": {
        "rh-qpid-proton-j:master:untested": {
            "repository": "rh-qpid-proton-j",
            "repository_url": "http://git.host.prod.eng.bos.redhat.com/git/rh-qpid-proton-j.git",
            "branch": "master",
            "name": "untested",
            "commit": "cdd6d5dd515c631de008c7b2792cc8143b280970",
            "artifacts": {
                "library": {
                    "type": "maven",
                    "repository_url": "https://maven.repository.engineering.redhat.com/",
                    "group": "org.apache.qpid",
                    "artifact": "proton-j",
                    "version": "0.27.1.B1",
                },
            },
        },
        "rh-pooled-jms:master:tested": {
            "repository": "rh-pooled-jms",
            "repository_url": "http://git.host.prod.eng.bos.redhat.com/git/rh-qpid-proton-j.git",
            "branch": "master",
            "name": "tested",
            "commit": "cdd6d5dd515c631de008c7b2792cc8143b280970",
            "artifacts": {
                "library": {
                    "type": "maven",
                    "repository_url": "https://maven.repository.engineering.redhat.com/",
                    "group": "org.messaginghub",
                    "artifact": "pooled-jms",
                    "version": "1.0.4.B2",
                },
            },
        },
        "rh-qpid-jms:0.34.0-amq:tested": {
            "repository": "rh-qpid-jms",
            "repository_url": "http://git.host.prod.eng.bos.redhat.com/git/rh-qpid-jms.git",
            "branch": "0.34.0-amq",
            "name": "tested",
            "commit": "16dc03dc8075e6600342b1dcdcafc5d28b7ffde5",
            "artifacts": {
                "client-maven": {
                    "type": "maven",
                    "repository_url": "http://download-node-02.eng.bos.redhat.com/devel/candidates/amq/AMQ-CLIENTS-2.1.0/JMS-maven-repo/maven-repository",
                    "group": "org.apache.qpid",
                    "artifact": "qpid-jms-client",
                    "version": "0.34.0.redhat-00002",
                },
                "client-zip": {
                    "type": "file",
                    "url": "http://download-node-02.eng.bos.redhat.com/devel/candidates/amq/AMQ-CLIENTS-2.1.0/qpid-jms-0.34.0.redhat-00002-bin.zip",
                },
            },
        },
        "rh-qpid-dispatch:master:untested": {
            "repository": "rh-qpid-dispatch",
            "repository_url": "http://git.host.prod.eng.bos.redhat.com/git/rh-qpid-dispatch.git",
            "branch": "master",
            "name": "untested",
            "commit": "483b9293604063480d5f706edea18cb0a3e4c8b9",
            "artifacts": {
                "qpid-dispatch-router-el7-rpm": {
                    "type": "rpm",
                    "repository_url": "http://rhm.usersys.redhat.com/yum/packages/qpid-dispatch/el7/20180816.483b929/x86_64/",
                    "name": "qpid-dispatch-router",
                    "version": "1.4.0",
                    "release": "20180816.483b929.el7",
                },
                "container-image": {
                    "type": "container-image",
                    "registry_url": "https://registry.access.redhat.com",
                    "repository": "amq-interconnect-1",
                    "id": "8e996ec51141",
                },
            },
        },
        "rh-qpid-proton:master:untested": {
            "repository": "rh-qpid-proton",
            "repository_url": "http://git.host.prod.eng.bos.redhat.com/git/rh-qpid-proton.git",
            "branch": "master",
            "name": "untested",
            "commit": "803a47e",
            "artifacts": {
                "python-qpid-proton-el7-rpm": {
                    "type": "rpm",
                    "repository_url": "http://rhm.usersys.redhat.com/yum/packages/qpid-proton/el7/20180816.803a47e/x86_64/",
                    "name": "python-qpid-proton",
                    "version": "0.25.0",
                    "release": "20180816.803a47e.el7",
                },
                "qpid-proton-c-devel-el7-rpm": {
                    "type": "rpm",
                    "repository_url": "http://rhm.usersys.redhat.com/yum/packages/qpid-proton/el7/20180816.803a47e/x86_64/",
                    "name": "qpid-proton-c-devel",
                    "version": "0.25.0",
                    "release": "20180816.803a47e.el7",
                },
                "qpid-proton-cpp-devel-el7-rpm": {
                    "type": "rpm",
                    "repository_url": "http://rhm.usersys.redhat.com/yum/packages/qpid-proton/el7/20180816.803a47e/x86_64/",
                    "name": "qpid-proton-cpp-devel",
                    "version": "0.25.0",
                    "release": "20180816.803a47e.el7",
                },
            },
        },
    },
}
