FROM python:3.9.10-slim-bullseye AS stage0

RUN apt update -y && apt install -y build-essential git
RUN pip install pipenv
RUN mkdir -p /root/.ssh/ && ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts

COPY ./ /hostthedocs/
WORKDIR /hostthedocs/
RUN --mount=type=ssh PIPENV_VENV_IN_PROJECT=1 pipenv install


# TODO go back to running with pipenv instead of python?
# TODO Or install in venv and copy to site-packages?
FROM python:3.9.10-slim-bullseye AS final

COPY --from=stage0 /hostthedocs/ /hostthedocs/
RUN pip install pipenv
WORKDIR /hostthedocs/