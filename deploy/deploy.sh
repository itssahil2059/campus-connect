#!/usr/bin/env bash
# Update the live site to the latest code. Run ON THE EC2 SERVER:
#
#   ~/campus-connect/deploy/deploy.sh          # deploys the main branch
#   ~/campus-connect/deploy/deploy.sh dev      # or another branch
#
# Safe to run any time; it only applies what changed.
set -euo pipefail

# Everything is inside main() so bash reads the whole file before running it:
# `git pull` below may rewrite this very script mid-run.
main() {
  BRANCH="${1:-main}"
  cd "$(dirname "$0")/.."

  echo "==> Pulling $BRANCH"
  git fetch origin
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"

  echo "==> Backend: dependencies, database migrations, static files"
  cd backend
  .venv/bin/pip install --quiet -r requirements.txt
  .venv/bin/python manage.py migrate --noinput
  .venv/bin/python manage.py collectstatic --noinput --verbosity 0

  echo "==> Frontend: build"
  cd ../frontend
  npm ci --no-audit --no-fund --loglevel=error
  npm run build

  echo "==> Server config: copy the systemd service / Nginx site if they changed"
  cd ..
  if ! cmp -s deploy/gittogether.service /etc/systemd/system/gittogether.service; then
    sudo cp deploy/gittogether.service /etc/systemd/system/gittogether.service
    sudo systemctl daemon-reload
    echo "    updated gittogether.service"
  fi
  if ! cmp -s deploy/nginx.conf /etc/nginx/sites-available/gittogether; then
    sudo cp deploy/nginx.conf /etc/nginx/sites-available/gittogether
    sudo nginx -t && sudo systemctl reload nginx
    echo "    updated Nginx site"
  fi

  echo "==> Restarting the API"
  sudo systemctl restart gittogether

  echo "Deployed $(git rev-parse --short HEAD) from $BRANCH"
}

main "$@"
