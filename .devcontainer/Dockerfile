# Dependencies versions
ARG PYTHON_VERSION="3.7.10"

FROM python:${PYTHON_VERSION}-buster

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    apt-get install -y libffi-dev libssl-dev

# Install python development dependencies
ADD requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

RUN \
    # Install Docker CE CLI
    apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common lsb-release && \
    curl -fsSL https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]')/gpg | apt-key add - 2>/dev/null && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]') $(lsb_release -cs) stable" && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    # Clean up
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /tmp/* && \
    rm -rf /var/lib/apt/lists/*

# Customize bash
RUN \
    # Git command prompt
    git clone https://github.com/magicmonty/bash-git-prompt.git ~/.bash-git-prompt --depth=1 && \
    echo "if [ -f \"$HOME/.bash-git-prompt/gitprompt.sh\" ]; then GIT_PROMPT_ONLY_IN_REPO=1 && source $HOME/.bash-git-prompt/gitprompt.sh; fi" >> "/root/.bashrc" && \
    # Install bash completion
    apt-get update && \
    apt-get -y install bash-completion && \
    echo "source /usr/share/bash-completion/bash_completion" >> ~/.bashrc 