#! /bin/bash
# Bash script to run through the gists in gist2run.txt

docker rm $(docker ps -a | grep 'pllm-' | awk '{ print $1 }')
docker rmi $(docker images | grep 'test/pllm' | awk '{ print $3 }')
docker rmi $(docker images | grep 'none' | awk '{ print $3 }')

# Remove only those that have been around for more than 30 minutes
docker images --format '{{.Repository}} {{.Tag}} {{.ID}} {{.CreatedAt}}' | grep '<none>' | while read repo tag id created_at rest; do created_at=$(echo "$created_at $rest" | cut -d' ' -f1-2); [ $(($(date +%s) - $(date -d "$created_at" +%s))) -gt 1800 ] && docker rmi "$id"; done

exec < 'my_gists.csv'

while IFS= read -r location
do
  echo $location
  folder="$(echo $location | rev | cut -d'/' -f1 | rev )"
  echo $folder

  # Wait, to ensure we don't have more than 5 processes running at a time
  echo $(docker ps -f status=running | grep -o pllm- | wc -l)
  while [ $(docker ps -f status=running | grep -o pllm- | wc -l) -ge 5 ];
  do
    echo 'waiting for processes to finish'
    sleep 60
    docker rm $(docker ps -a | grep 'pllm-' | awk '{ print $1 }')
    docker rm $(docker ps -a | grep 'test/pllm' | awk '{ print $1 }')
    docker images --format '{{.Repository}} {{.Tag}} {{.ID}} {{.CreatedAt}}' | grep 'none' | while read repo tag id created_at rest; do created_at=$(echo "$created_at $rest" | cut -d' ' -f1-2); [ $(($(date +%s) - $(date -d "$created_at" +%s))) -gt 300 ] && docker rmi "$id"; done
    docker images --format '{{.Repository}} {{.Tag}} {{.ID}} {{.CreatedAt}}' | grep 'test/pllm' | while read repo tag id created_at rest; do created_at=$(echo "$created_at $rest" | cut -d' ' -f1-2); [ $(($(date +%s) - $(date -d "$created_at" +%s))) -gt 1800 ] && docker rmi "$id"; done
  done
  docker run -d --name pllm-$folder --network ollama-docker_ollama-docker -v $(pwd):/code:rw -v /var/run/docker.sock:/var/run/docker.sock --entrypoint /bin/bash pllm:sept -c "cd /code/src && python test_executor.py -f '/code/$location/snippet.py' -m 'gemma2' -b 'http://ollama:11434' -l 10 -r 1"
  sleep 3
done

docker rm $(docker ps -a | grep 'pllm-' | awk '{ print $1 }')
docker rm $(docker ps -a | grep 'test/pllm' | awk '{ print $1 }')
docker images --format '{{.Repository}} {{.Tag}} {{.ID}} {{.CreatedAt}}' | grep 'none' | while read repo tag id created_at rest; do created_at=$(echo "$created_at $rest" | cut -d' ' -f1-2); [ $(($(date +%s) - $(date -d "$created_at" +%s))) -gt 300 ] && docker rmi "$id"; done
docker images --format '{{.Repository}} {{.Tag}} {{.ID}} {{.CreatedAt}}' | grep 'test/pllm' | while read repo tag id created_at rest; do created_at=$(echo "$created_at $rest" | cut -d' ' -f1-2); [ $(($(date +%s) - $(date -d "$created_at" +%s))) -gt 1800 ] && docker rmi "$id"; done