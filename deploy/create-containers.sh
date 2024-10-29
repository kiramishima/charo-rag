#!/bin/bash

docker build -t ollama-server -f images/ollama.Dockerfile .

docker build -t charo-app -f images/app.Dockerfile .