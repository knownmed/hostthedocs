#! /usr/bin/env python3


# third-party packages
from doit.tools import Interactive, LongRunning
import doit
import sh


DOIT_CONFIG = {
    "backend": "sqlite3",
}


def task_version():
    return {
        "actions": [["python", "setup.py", "--version"]],
        "verbosity": 2,
    }


def task_nb():
    return {
        "actions": [LongRunning('PYTHONPATH="$(realpath ./src/)" jupyter notebook')],
        "verbosity": 2,
    }


def task_tag():
    return {
        "actions": ["git tag $(python setup.py --version) && git push --tags"],
        "verbosity": 2,
    }


def task_tags():
    return {
        "actions": ["git fetch --all && git tag"],
        "verbosity": 2,
    }


def task_install():
    return {
        "actions": ["pipenv install"],
        "verbosity": 2,
    }


def task_docker_auth():
    return {
        "actions": ["gcloud auth configure-docker"],
        "verbosity": 2,
    }


def name():
    return sh.python("setup.py", "--name").strip()


def version():
    return sh.python("setup.py", "--version").strip()


def docker_tag(version):
    return f"gcr.io/eng-knownmed/{name()}:{version}"


def docker_tags():
    return docker_tag(version()), docker_tag("latest")


def task_docker_build():
    tag, _ = docker_tags()
    return {
        "actions": [Interactive(f"DOCKER_BUILDKIT=1 docker build --ssh default . -f ./Dockerfile -t {tag}")],
        "verbosity": 2,
    }


def task_docker_tag():
    tag, latest = docker_tags()
    return {
        "actions": [f"docker tag {tag} {latest}"],
        "verbosity": 2,
    }


def task_docker_push():
    tag, latest = docker_tags()
    return {
        "actions": [Interactive(f"docker push {tag}"),
                    Interactive(f"docker push {latest}")],
        "task_dep": ["docker_auth"],
        "verbosity": 2,
    }


def task_docker_full():
    return {
        "actions": None,
        "task_dep": ["install", "docker_build", "docker_tag", "docker_push"],
        "verbosity": 2,
    }


def task_docker_tags():
    return {
        # TODO DRY
        "actions": [f"gcloud container images list-tags gcr.io/eng-knownmed/{name()}"],
        "verbosity": 2,
    }


def task_docker_prune():
    return {
        "actions": ["docker system prune"],
        "verbosity": 2,
    }


def task_build_lib():
    return {
        "actions": [["nbdev_build_lib"]],
        "verbosity": 2,
    }


def task_watch_docs():
    return {
        "actions": [LongRunning(f"pdoc --docformat=google ./src/knownmed/{name()}")],
        "verbosity": 2,
    }


def task_build_docs():
    return {
        "actions": [
            Interactive(f"rm -rf ./docs/{version()}/"),
            Interactive(f"pdoc -o ./docs/{version()}/ --docformat=google ./src/knownmed/{name()}/"),
            Interactive(f"zip -r ./docs/{version()}.zip ./docs/{version()}/*"),
        ],
        "verbosity": 2,
    }


def task_watch_build():
    return {
        "actions": [LongRunning("watchmedo shell-command --command='date && nbdev_build_lib' --patterns='*.ipynb' --wait --drop --recursive ./nbs")],
        "verbosity": 2,
    }


if __name__ == '__main__':
    doit.run(globals())
