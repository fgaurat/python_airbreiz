#!/usr/bin/env bash
# Préparation express (formateur, la veille) : à lancer une fois GitLab démarré (page de connexion OK).
#   1. crée un runner d'instance et un token d'accès personnel pour root (console Rails, ~1 min)
#   2. enregistre le runner (exécuteur Docker, réseau gitlab_net, clone via http://gitlab:8080)
#   3. crée le groupe "formation"
# Le token d'accès est écrit dans .tokens (ignoré par git) pour les commandes API et les git push.
set -euo pipefail
cd "$(dirname "$0")"
API=http://localhost:8080/api/v4
PAT="glpat-formation-root-token-2026"

echo "== Attente de GitLab..."
until [ "$(curl -s -o /dev/null -w '%{http_code}' -m 5 http://localhost:8080/users/sign_in)" = "200" ]; do sleep 5; done

echo "== Création du runner et du token d'accès (console Rails, ~1 min)..."
RUNNER_TOKEN=$(docker exec gitlab gitlab-rails runner "
r = ::Ci::Runner.create!(runner_type: :instance_type, description: 'docker-runner-formation', run_untagged: true, tag_list: ['docker'])
u = User.find_by(username: 'root')
unless u.personal_access_tokens.find_by(name: 'formation')
  t = u.personal_access_tokens.create!(scopes: [:api, :write_repository, :read_repository], name: 'formation', expires_at: 60.days.from_now)
  t.set_token('$PAT'); t.save!
end
puts r.token
" 2>/dev/null | tail -1)
echo "RUNNER_TOKEN=$RUNNER_TOKEN" > .tokens
echo "PAT=$PAT" >> .tokens

echo "== Enregistrement du runner..."
./register-runner.sh "$RUNNER_TOKEN" | tail -1

echo "== Création du groupe 'formation'..."
curl -s -H "PRIVATE-TOKEN: $PAT" -X POST "$API/groups" -d name=formation -d path=formation -d visibility=private -o /dev/null -w "HTTP %{http_code}\n"

echo
echo "Prêt. Interface : http://localhost:8080  (root / voir .env)"
echo "Token d'accès (mot de passe pour git push en HTTP, login root) : $PAT"
echo "Exemple : git push http://root:$PAT@localhost:8080/formation/calculs.git main"
