# Creates docker container that runs HCP Pipeline algorithms
# Maintainer: Amy Hegarty (amy.hegarty@colorado.edu)
#

FROM ubuntu:focal as base
#
LABEL maintainer="Amy Hegarty <amy.hegarty@colorado.edu>"

RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           bc \
           curl \
           ca-certificates\
           dc \
           file \
           libfontconfig1 \
           libfreetype6 \
           libgl1-mesa-dev \
           libgl1-mesa-dri \
           libglu1-mesa-dev \
           libgomp1 \
           libice6 \
           libxcursor1 \
           libxft2 \
           libxinerama1 \
           libxrandr2 \
           libxrender1 \
           libxt6 \
           sudo \
           wget \
           software-properties-common \
           dirmngr \
           ed \
           less \
           locales \
           vim-tiny \
           gpg-agent \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

######################################################
# FLYWHEEL GEAR STUFF...

USER root
RUN adduser --disabled-password --gecos "Flywheel User" flywheel

ENV USER="flywheel"

# Add poetry oversight.
RUN apt-get update &&\
    apt-get install -y --no-install-recommends \
	 git \
     zip \
    software-properties-common &&\
	add-apt-repository -y 'ppa:deadsnakes/ppa' &&\
	apt-get update && \
	apt-get install -y --no-install-recommends python3.9\
    python3.9-dev \
	python3.9-venv \
	python3-pip &&\
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install poetry based on their preferred method. pip install is finnicky.
# Designate the install location, so that you can find it in Docker.
ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.1.6 \
    # make poetry install to this location
    POETRY_HOME="/opt/poetry" \
    # do not ask any interactive questions
    POETRY_NO_INTERACTION=1 \
    VIRTUAL_ENV=/opt/venv
RUN python3.9 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python3.9 -m pip install --upgrade pip && \
    ln -sf /usr/bin/python3.9 /opt/venv/bin/python3
ENV PATH="$POETRY_HOME/bin:$PATH"

# get-poetry respects ENV
RUN curl -sSL https://install.python-poetry.org | python3 - ;\
    ln -sf ${POETRY_HOME}/lib/poetry/_vendor/py3.9 ${POETRY_HOME}/lib/poetry/_vendor/py3.8; \
    chmod +x "$POETRY_HOME/bin/poetry"

# Installing main dependencies
ARG FLYWHEEL=/flywheel/v0
COPY pyproject.toml poetry.lock $FLYWHEEL/
WORKDIR $FLYWHEEL
RUN poetry install --no-root --no-dev

## Installing the current project (most likely to change, above layer can be cached)
## Note: poetry requires a README.md to install the current project
COPY run.py manifest.json README.md $FLYWHEEL/
COPY fw_gear_tedana $FLYWHEEL/fw_gear_tedana
COPY utils $FLYWHEEL/utils

# Configure entrypoint
RUN chmod a+x $FLYWHEEL/run.py && \
    echo "tedana" > /etc/hostname && \
    rm -rf $HOME/.npm

ENTRYPOINT ["poetry","run","python","/flywheel/v0/run.py"]
