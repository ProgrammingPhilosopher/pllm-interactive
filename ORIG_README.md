# PLLM

PLLM test using LLMs to fix Gists

## NOTE

Due to issues with ARM, unexpected errors may occur on ARM based systems. This is due to newer versions of modules having not been properly compiled for the available system.

This is a known issue in current ARM systems.

## Dependencies

- Ollama installed (https://ollama.com/)
  - gemma2
  - Other models if you want to try
- Docker

## Running Open Source

To run from command line:

```pipenv shell```

```pipenv install```

```cd src```

```python3 test_executor.py -f "./../local-test-gists/5780127/snippet.py" -m "gemma2" -b "http://localhost:11434" -t "0.7" -r "1"```

There is a .vscode/launch.json file for quick launching of tests. This is useful for debugging.

## Running OpenAI (LOL Open) Chat GPT
**NOTE: Currently unimplemented but can be re-implemented by uncommenting an import in ollama_helper_base.py**

It is possible to run the tool using the Chat GPT API. To do so, you simply specify the gpt model you wish to use, for example:
To run from command line:

```pipenv shell```

```pipenv install```

```cd src```

```python3 test_executor.py -f "./../local-test-gists/5780127/snippet.py" -m "gpt-4o-2024-05-13" -t "0.7" -r "0"```

Here we define the model `gpt-4o-2024-05-13` and set the range to 0 as we only want to test one instance. We have attempted to keep API polling down but please check your usage to ensure it's not over using.

### Parameters

- -f | --file - The location of the snippet to validate.
- -m | --model - The name of the model to use (must be downloaded with Ollama).
- -b | --base - The url to ollama, defaults to http://localhost:11434. Can be different if run in a container.
- -t | --temp - The model temp, defaults to 0.7 and used to give the model more freedom and expression in its response.
- -l | --loop - How many times we will loop to find a solution.
- -r | --range - The search range. Defaults to 0 where it only runs against one python version. If 1 is given then the range is 1 either side of the LLMs found version. For example: If the LLM chooses 3.6 and we have a range of 1 then we will have test runs on python [3.5, 3.6, 3.7].
- -v | Verbose logging of information.

### VS Code

Running in code, includes a launch.json file with the above parameters already set within it.

To run this, you need to ensure you're connect to the pip environment as installed above.

To do this, press Command+Shift+P. This will open a menu where you should choose 'Python select interpreter'. From this list, choose the pipenv shell environment with the relevant name.

You can now choose run without debug or run with debug from the run menu to be able to see more.

## Output

By default, test_executor.py generates a range of Dockerfiles. The range can be modified by changing the value of -r | --range.

It will also run for so many loops, with a default of 3. This can be modified via self.end_loop in test_executor.py.

The test outputs to the same folder as the gist it is evaluating. For example, the default in the vscode launch file, outputs to the same folder as the snippet.

In this folder it will create multiple Dockerfiles appended with the Python version as well as an output yaml file to give information on each test pass.

## Docker build

To build a local docker image, with which to run pip inside. This can be combined with the ollama-docker project, to be able to run ollama and pip inside a docker container.

***Build docker image***
```docker build --build-arg UID=$(id -u) --build-arg GID=$(id -g) --build-arg UNAME=$USER -f Dockerfile -t pllm:latest .```

## Experiment

### Results

Results for the PLLM tests are stored in `*pllm_results* ` and contains all 10 test runs.

pyego and readpy results from the experiments run for those are stored in their respective folders.

### Re-running PLLM data

To re-run the PLLM data, first start by starting up Ollama which can be easily done from a Docker instance.

Clone the Ollam docker repo to a location of choice

`git clone https://hub.docker.com/r/ollama/ollama`

Make a new Docker compose file in the ollama repo:

```
version: '3.8'

services:      
  ollama:
    volumes:
      - ./ollama/ollama:/root/.ollama
    container_name: ollama
    tty: true
    restart: unless-stopped
    image: ollama/ollama:0.3.12
    init: true
    ports:
      - 7869:11434
    environment:
      - OLLAMA_KEEP_ALIVE=24h
      - OLLAMA_HOST=0.0.0.0
    networks:
      - ollama-docker
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

networks:
  ollama-docker:
    external: false
```

Run this with docker compose to bring up the correct containers:

`docker compose -f <file_name>.yaml up -d`

This will launch the Ollama docker container and assign a network, so PLLM can also connect within the same docker network space.

Now run the following command from the root dir of the PLLM code:

```docker run -d --name pllm-5780127 --network ollama-docker_ollama-docker -v $(pwd):/code:rw -v /var/run/docker.sock:/var/run/docker.sock --entrypoint /bin/bash pllm:latest -c "cd /code/src && python test_executor.py -f '/code/local-test-gists/5780127/snippet.py' -m 'gemma2' -b 'http://ollama:11434' -l 10 -r 1"```

The above docker command will run a single snippet test. We Typically use the snippet ID in the container name for uniqueness. Note the snippet ID in the docker run command.

### Running all
If you want to run all the snippets then please use the `run_gists.sh`. This file is setup to loop through an entire folder of gists and execute simultaneously based on the number of docker containers allowed.

To run all the gists:

```cp -r pllm_results/hard-gists-l10-r1-1 pllm_results/hard-gists-new```

^^ Create a copy of a set

```bash folder_to_file.sh pllm_results/hard-gists-new```

Adds all the relevant snippet paths to the my_gists.csv file

```bash clean_dirs.sh```

Ensures all the folders are clean of old data, leaving just the snippets

```nohup bash run_gists.sh > gist_test_.out 2>&1 &```

As noted in the paper, we run this on a dedicated server. Running nohup allows this to be left to complete.