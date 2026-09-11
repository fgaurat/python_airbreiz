#!/usr/bin/env bash
# Enregistre le runner Docker auprès de l'instance GitLab locale.
# Prérequis : un token d'authentification de runner (glrt-…) créé dans
#   Admin area > CI/CD > Runners > "New instance runner"  (cocher "Run untagged jobs")
# Usage : ./register-runner.sh glrt-xxxxxxxxxxxxxxxx
set -euo pipefail
TOKEN="${1:?Usage: $0 <runner-auth-token glrt-...>}"

docker exec gitlab-runner gitlab-runner register \
  --non-interactive \
  --url "http://gitlab:8080" \
  --clone-url "http://gitlab:8080" \
  --token "$TOKEN" \
  --executor "docker" \
  --docker-image "python:3.12-slim" \
  --docker-network-mode "gitlab_net" \
  --docker-pull-policy "if-not-present" \
  --description "docker-runner-formation"

echo "Runner enregistré. Vérification :"
docker exec gitlab-runner gitlab-runner verify
