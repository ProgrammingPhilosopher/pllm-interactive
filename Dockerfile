FROM python:3.11

ARG UNAME
ARG UID
ARG GID
RUN groupadd -g $GID -o $UNAME && \
    groupadd -g 998 docker && \
    groupadd -g 999 docker2 && \
    useradd -m -u $UID -g $GID -G docker,docker2 -o -s /bin/bash $UNAME
USER $UNAME

# Install the required packages
RUN python -m pip install --upgrade pip && \
    pip install datetime==5.5 && \
    pip install python-dateutil==2.9.0.post0 && \
    pip install transformers==4.41.1 && \
    pip install accelerate==0.30.1 && \
    pip install requests==2.31.0 && \
    pip install docker==7.1.0 && \
    pip install ollama==0.2.0 && \
    pip install langchain==0.2.1 && \
    pip install langchain-openai==0.1.9 && \
    pip install langchain-community==0.2.1 && \
    pip install llama-index-llms-ollama==0.1.5 && \
    pip install jq==1.7.0 && \
    pip install pypi-json==0.4.0 && \
    pip install jsonschema==4.22.0 && \
    pip install load-dotenv==0.1.0 && \
    pip install pyyaml==6.0.1

ENTRYPOINT ["tail", "-f", "/dev/null"]
