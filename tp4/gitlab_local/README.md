# GitLab en local (Docker)

> Dossier déplacé depuis `formation-gitlab/tp00_gitlab_local` le 10/09/2026.
> Le projet Compose garde son nom `tp00_gitlab_local` (clé `name:`) pour
> réutiliser les volumes existants. Les TP11/TP12 cités ci-dessous sont ceux
> de la formation GitLab d'origine ; pour ce projet, voir `../README.md`.

Démarrage rapide, GitLab déjà installé :

```bash
docker compose up -d                    # 3 à 5 min avant que la page réponde
docker compose ps                       # gitlab (healthy), gitlab-runner
```

## En une phrase

En dix minutes de préparation (et cinq minutes de démarrage), on dispose d'un GitLab CE
complet sur son poste, avec un runner Docker, pour dérouler les TP11 et TP12 sans dépendre
d'un GitLab d'entreprise ni d'Internet pendant la formation.

## Objectifs pédagogiques

Ce TP est d'abord un **TP formateur** (à faire la veille). Fait avec les stagiaires, il permet de :

- comprendre les trois briques : l'application GitLab, le runner, l'exécuteur (ici Docker) ;
- savoir enregistrer un runner et lire sa configuration (`config.toml`) ;
- savoir où GitLab range ses données (volumes) et comment repartir de zéro ;
- distinguer l'URL vue du navigateur, l'URL vue du runner et l'URL vue des jobs.

## Prérequis

- Docker Desktop (ou équivalent) démarré, **au moins 6 Go de RAM alloués à Docker**
  (Docker Desktop > Settings > Resources). Mac Apple Silicon et Intel, Linux, Windows/WSL2 : l'image
  `gitlab/gitlab-ce` existe en `amd64` et `arm64`.
- 10 Go de disque libres (image ≈ 3,7 Go décompressée).
- Ports 8080 et 2222 libres.

## Fichiers

| Fichier | Rôle |
|---|---|
| `docker-compose.yml` | GitLab CE + GitLab Runner, sur un réseau Docker `gitlab_net` |
| `.env` | `GITLAB_HOST` (nom d'hôte dans les URLs) et `GITLAB_ROOT_PASSWORD` |
| `register-runner.sh` | Enregistre le runner (exécuteur Docker) à partir d'un token `glrt-…` |
| `create-runner-token.sh` | Variante : crée le runner et son token en ligne de commande (console Rails, ~1 min) |
| `setup-formation.sh` | **Préparation express** : runner + token d'accès root + groupe `formation`, sans un clic (~2 min) |
| `.tokens` | (généré, ignoré par git) token du runner et token d'accès `root` à réutiliser dans les commandes |

## Mise en route

```bash
cd gitlab_local
docker compose pull          # une fois, ~4 Go
docker compose up -d
docker compose logs -f gitlab | grep -m1 "gitlab Reconfigured"   # ~3 à 5 min au premier démarrage
```

Version express (tout ce qui suit, sans clic) : `./setup-formation.sh`, puis passer directement à
« Premier projet et première pipeline ».

Puis ouvrir http://localhost:8080 et se connecter avec `root` / le mot de passe de `.env`
(`Formation2026!` par défaut). Tant que la page renvoie une erreur 502, GitLab démarre encore ;
`docker ps` affiche `(health: starting)` puis `(healthy)`.

### Enregistrer le runner

1. Dans GitLab : **Admin area** (icône en bas à gauche, ou `http://localhost:8080/admin`) >
   **CI/CD** > **Runners** > **New instance runner**.
2. Cocher **Run untagged jobs**, laisser le reste, **Create runner**.
3. Copier le token affiché (`glrt-…` ou `glrtr-…`, visible une seule fois) puis :

```bash
./register-runner.sh glrt-xxxxxxxxxxxxxxxxxxxx
```

Le script enregistre un runner avec l'exécuteur `docker`, l'image par défaut `python:3.12-slim`,
et deux réglages indispensables en local :

- `--docker-network-mode gitlab_net` : les conteneurs de job sont attachés au réseau de Compose ;
- `--clone-url http://gitlab:8080` : les jobs clonent le dépôt via le nom de service Docker, pas via
  `localhost` (qui, vu depuis un conteneur, désigne le conteneur lui-même).

Vérifier dans **Admin area > CI/CD > Runners** : le runner apparaît en vert (« online »).

Variante sans clic (utile pour reconstruire l'environnement) :

```bash
./register-runner.sh "$(./create-runner-token.sh | tail -1)"
```

### Premier projet et première pipeline

1. **Create group** `formation`, puis **New project > Create blank project** `calculs`
   (visibilité Private, décocher « Initialize repository with a README »).
2. Créer un **Personal Access Token** pour pousser en HTTP : avatar > **Edit profile** >
   **Access tokens** > **Add new token**, scopes `write_repository` + `api`. Le token sert de mot de
   passe pour `git push` (le login est `root`).
3. Pousser le projet du TP11 :

```bash
cd ../tp11_gitlab_ci_pytest/projet_ci
git init -b main && git add -A && git commit -m "Projet initial"
git remote add origin http://localhost:8080/formation/calculs.git
git push -u origin main       # login root, mot de passe = le token
```

4. **Build > Pipelines** : la pipeline définie par `.gitlab-ci.yml` démarre.

Astuce : GitLab crée le projet tout seul si on pousse vers un chemin inexistant d'un groupe où l'on a
les droits (`git push http://root:<token>@localhost:8080/formation/calculs.git main` suffit). Le premier job prend
   une minute de plus (téléchargement des dépendances pip dans le conteneur de job).

## Déroulé de la présentation

### Les trois briques

**Ce que montre le code.** `docker-compose.yml` déclare deux services :

- `gitlab` : l'application (Rails, PostgreSQL, Redis, nginx, Gitaly… tout est dans l'image
  « omnibus »). Sa configuration passe par la variable `GITLAB_OMNIBUS_CONFIG` (du Ruby) : `external_url`,
  port SSH, mot de passe root initial, et quelques allègements (`puma['worker_processes'] = 0`,
  `prometheus_monitoring['enable'] = false`) pour tenir dans 4 Go.
- `runner` : un agent qui interroge GitLab toutes les 3 secondes (« un job pour moi ? ») et l'exécute
  via un **exécuteur**. Ici l'exécuteur `docker` : chaque job tourne dans un conteneur neuf, créé à
  partir de l'`image:` du job. Le runner a accès au démon Docker de l'hôte grâce au montage de
  `/var/run/docker.sock` : les conteneurs de job sont donc des **frères** du runner, pas des enfants.

**À dire aux stagiaires.** En entreprise, le GitLab est central et les runners sont partagés ou
dédiés à un groupe. Ce qui change en local : rien dans le `.gitlab-ci.yml`. C'est le point important :
tout ce qu'on écrit au TP11/TP12 est transposable tel quel.

**À montrer en direct.**

```bash
docker exec gitlab-runner cat /etc/gitlab-runner/config.toml
docker stats --no-stream            # GitLab consomme 3 à 4 Go au repos
docker ps                           # pendant une pipeline : un conteneur runner-xxx-project-1-concurrent-0 apparaît
```

### Trois URL pour un seul GitLab

| Qui parle | URL | Pourquoi |
|---|---|---|
| Le navigateur, `git push` depuis le poste | `http://localhost:8080` | port publié par Compose |
| Le runner (enregistrement, polling) | `http://gitlab:8080` | nom de service sur le réseau `gitlab_net` |
| Les conteneurs de job (`git clone`) | `http://gitlab:8080` via `clone_url` | sinon GitLab leur donnerait `external_url`, c'est-à-dire `localhost`, qui ne mène nulle part depuis un conteneur |

**Pièges et erreurs fréquentes.**

- Job bloqué sur `fatal: unable to access 'http://localhost:8080/...'` : `clone_url` ou
  `network_mode` manquant dans `config.toml`. Relancer `register-runner.sh` ou éditer le fichier
  puis `docker compose restart runner`.
- Job `pending` indéfiniment : aucun runner ne prend le job. Soit le runner n'est pas enregistré, soit
  le job a un `tags:` que le runner n'a pas, soit « Run untagged jobs » n'est pas coché.
- `pip install` échoue dans le job (`Temporary failure in name resolution`) : le réseau `gitlab_net`
  n'a pas accès à Internet (VPN d'entreprise, proxy). Solution rapide : pré-construire une image avec
  les dépendances ou configurer `HTTP_PROXY` dans les variables CI.
- Page 502 qui ne s'arrête jamais alors que `gitlab-ctl status` (dans le conteneur) montre `puma` qui
  redémarre toutes les 30 s : Puma n'arrive pas à démarrer. Lire
  `docker exec gitlab tail -50 /var/log/gitlab/puma/current`. Cas rencontré en préparant ce TP :
  `Address already in use ... port 8080` parce que nginx (port de `external_url`) et Puma (port
  interne par défaut : 8080 aussi) se marchaient dessus, d'où `puma['port'] = 8081` dans le compose.
- GitLab qui disparaît d'un coup (`docker ps -a` : `Exited (137)`) : la VM Docker a manqué de mémoire
  et a tué le conteneur. Vu en préparation avec 8 Go alloués, pendant qu'une pipeline tournait **et**
  que trois `docker run` de validation tournaient en parallèle. `docker compose up -d` relance tout
  (les données sont dans les volumes) ; éviter les gros conteneurs en parallèle des pipelines, ou
  monter Docker à 10 Go.
- Page 502 après plus de 8 minutes : Docker n'a pas assez de mémoire. Vérifier `docker stats` et
  augmenter l'allocation.
- Mot de passe root refusé : `initial_root_password` n'est lu qu'au **premier** démarrage. Si les
  volumes existent déjà, réinitialiser avec
  `docker exec -it gitlab gitlab-rake "gitlab:password:reset[root]"`.

### Instance partagée pour toute la salle

Un seul GitLab sur le poste du formateur suffit pour 12 stagiaires. Dans `.env`, remplacer
`GITLAB_HOST=localhost` par l'adresse IP du poste (`ipconfig getifaddr en0` sur Mac) **avant** le
premier `docker compose up`, sinon les liens et URL de clone pointeront vers `localhost`. Chaque
stagiaire se crée un compte (`Register now` sur la page de connexion ; l'admin doit ensuite
l'approuver dans **Admin area > Users > Pending approval**, ou désactiver l'approbation dans
**Admin area > Settings > General > Sign-up restrictions**).

Pour changer d'hôte après coup : modifier `.env`, puis `docker compose up -d` (Compose recrée le
conteneur avec la nouvelle `external_url` ; les données sont dans les volumes et sont conservées).

## Questions fréquentes des stagiaires

- **Pourquoi pas `gitlab-runner exec` pour tester une pipeline sans GitLab ?** La commande a été
  retirée dans GitLab Runner 17.0. On teste les scripts de job localement dans un conteneur
  (`docker run --rm -v "$PWD:/app" -w /app python:3.12-slim sh -c "..."`) : c'est ce que fait le TP11.
- **Et l'exécuteur `shell` ?** Plus simple, mais les jobs partagent l'environnement du runner : pas
  d'isolation, pas de choix d'image. Docker est le standard.
- **Où sont les données ?** `docker volume ls | grep gitlab`. `docker compose down` les garde ;
  `docker compose down -v` efface tout (utile pour rejouer le TP à blanc).
- **Piège vu sur la toute première pipeline** : `ModuleNotFoundError` dans le job alors que les tests
  passent sur le poste. Sur le poste, le paquet est installé en éditable ou le shell a un `PYTHONPATH` ;
  dans le conteneur, non. D'où `pythonpath` dans `pyproject.toml` ou `pip install -e .` dans le job (TP11).
- **Version installée ?** `docker exec gitlab cat /opt/gitlab/version-manifest.txt | head -1` ou
  **Help** dans l'interface.

## Ce qu'il faut retenir

- GitLab = application + runners ; le runner exécute, GitLab orchestre.
- Un runner Docker crée un conteneur par job à partir de `image:` ; l'état ne survit pas d'un job à l'autre (d'où `cache` et `artifacts`, TP11).
- `external_url` est l'URL que GitLab **donne** aux clients ; en local elle diffère de l'URL que les conteneurs peuvent **joindre** : `clone_url` fait le pont.
- Un job `pending` = pas de runner compatible ; un job qui échoue au clone = problème d'URL ; un job qui échoue à `pip install` = problème de réseau.
- Tout `.gitlab-ci.yml` écrit ici tourne tel quel sur un GitLab d'entreprise.

## Exercices

1. **Repartir de zéro** : `docker compose down -v`, `docker compose up -d`, et refaire l'enregistrement
   du runner en moins de 10 minutes chrono. Résultat attendu : runner en ligne, pipeline verte.
2. **Casser le clone** : dans `config.toml`, supprimer la ligne `clone_url`, redémarrer le runner,
   relancer une pipeline. Lire l'erreur, la corriger.
3. **Un job qui attend** : ajouter `tags: [gpu]` à un job. Observer `pending`, puis lire dans
   l'interface la raison (« This job is stuck because… »). Retirer le tag.
4. **Deuxième runner** : enregistrer un second runner avec le tag `lent` et `--docker-image python:3.13-slim`.
   Vérifier avec deux jobs (un taggé, un non) lequel prend quoi.

## Transition vers le TP suivant

L'infrastructure est en place et invisible : le TP11 ne parle plus que du fichier `.gitlab-ci.yml`.
