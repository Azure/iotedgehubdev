# Dependencies versions
ARG PYTHON_VERSION="3.9.10"

# see https://hub.docker.com/_/python/?tab=tag
FROM python:${PYTHON_VERSION}-buster

# Dependencies versions
ARG AZURE_CLI_VERSION="2.34.1-1~buster"

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential apt-utils && \
    apt-get install -y libffi-dev libssl-dev vim sudo && \
    apt-get upgrade -y

# Install python development dependencies
ADD requirements.txt /tmp/
RUN \
    python -m pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

RUN \
    # Install the Azure CLI and IoT extension
    apt-get install -y ca-certificates curl apt-transport-https lsb-release gnupg && \
    curl -sL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null && \
    echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/azure-cli.list && \
    apt-get update && apt-get install -y azure-cli=${AZURE_CLI_VERSION} && \
    az extension add --name azure-iot --system && \
    az extension update --name azure-iot && \
    # Install Docker CE CLI
    apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common lsb-release && \
    curl -fsSL https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]')/gpg | apt-key add - 2>/dev/null && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]') $(lsb_release -cs) stable" && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    # Install bash completion
    apt-get update && \
    apt-get -y install bash-completion && \
    # Clean up
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /tmp/* && \
    rm -rf /var/lib/apt/lists/*

# setup and use the user 'vscode'
RUN \
    useradd -m -s /bin/bash -g users -G sudo -p U6aMy0wojraho vscode && \
    echo "vscode  ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER vscode
RUN \
    git clone https://github.com/magicmonty/bash-git-prompt.git $HOME/.bash-git-prompt --depth=1 && \
    echo "\n# setup GIT prompt and completion\nif [ -f \"$HOME/.bash-git-prompt/gitprompt.sh\" ]; then\n  GIT_PROMPT_ONLY_IN_REPO=1 && source $HOME/.bash-git-prompt/gitprompt.sh;\nfi" >> $HOME/.bashrc && \
    echo "source /usr/share/bash-completion/bash_completion" >> $HOME/.bashrc && \
    echo "\n# add local python programs to PATH\nexport PATH=$PATH:$HOME/.local/bin\n" >> $HOME/.bashrc && \
    # enable some useful aliases
    sed -i -e "s/#alias/alias/" $HOME/.bashrc && \
    echo "\n# skip sudo for docker commands\nalias docker='sudo docker'" >> $HOME/.bashrc
