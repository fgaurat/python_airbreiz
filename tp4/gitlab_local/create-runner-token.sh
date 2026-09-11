#!/usr/bin/env bash
# Variante "tout automatique" : crée un runner d'instance via la console Rails
# et affiche son token (glrt-…). Prend ~1 min. Alternative à l'interface web.
set -euo pipefail
docker exec gitlab gitlab-rails runner '
  r = ::Ci::Runner.create!(runner_type: :instance_type, description: "docker-runner-formation", run_untagged: true, tag_list: ["docker"])
  puts r.token
'
