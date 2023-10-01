#!/bin/bash

mkdir -p ./certs

openssl genrsa -out ./certs/redis.key 2048
openssl req -new -x509 -days 365 -key ./certs/redis.key -out ./certs/redis.crt -subj "/CN=localhost"

