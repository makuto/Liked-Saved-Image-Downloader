#!/bin/bash
mkdir certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout certificates/liked_saved_server.crt.key -out certificates/liked_saved_server.crt.pem
