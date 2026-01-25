FROM python:3.14-slim
ARG USER_NAME
ARG USER_ID
ARG GROUP_ID
ARG GROUP_NAME

COPY ./app/requirements.txt /tmp/requirements.txt
WORKDIR /app
RUN set -x && apt update && apt install -y \
    curl \
    sudo \
    git \
    awscli && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd -g ${GROUP_ID} ${GROUP_NAME} && \
    useradd -u ${USER_ID} -g ${GROUP_ID} -m ${USER_NAME} && \
    chown -R ${USER_NAME}:$(id -g) /app && \
    echo "${USER_NAME} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers.d/${USER_NAME} && \
    pip install --upgrade pip && pip install -r /tmp/requirements.txt
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt update && apt install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

RUN npm install -g yarn

