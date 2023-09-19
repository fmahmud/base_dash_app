FROM python:3.9-slim-bookworm as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

FROM base AS python-deps

USER root
# Install pipenv and compilation dependencies
RUN pip install --upgrade pip
RUN pip install pipenv
RUN apt-get update && apt-get install -y libpq5 gcc

# Install python dependencies in /.venv
COPY ./Pipfile .
COPY ./Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

# Create and switch to a new user
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

FROM base AS runtime

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

COPY ./ ./

# delete temp.* files


RUN pip install ./*.whl
