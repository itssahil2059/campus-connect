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

  echo "==> Media folder for uploaded profile photos"
  # Wherever MEDIA_ROOT points (default backend/media). Owned by ubuntu, the
  # user the API runs as (gittogether.service), so Django can write photos;
  # 755 so Nginx (www-data) can read them.
  MEDIA_DIR="$(.venv/bin/python manage.py shell --verbosity 0 -c 'from django.conf import settings; print(settings.MEDIA_ROOT)')"
  if [ ! -d "$MEDIA_DIR" ]; then
    sudo install -d -m 755 -o ubuntu -g ubuntu "$MEDIA_DIR"
    echo "    created $MEDIA_DIR"
  fi

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
  # HTTPS config once the Let's Encrypt certificate exists, plain HTTP before.
  SITE=deploy/nginx.conf
  if sudo test -f /etc/letsencrypt/live/datewithincampus.com/fullchain.pem; then
    SITE=deploy/nginx-https.conf
  fi
  sudo mkdir -p /var/www/certbot
  if ! cmp -s "$SITE" /etc/nginx/sites-available/gittogether; then
    sudo cp "$SITE" /etc/nginx/sites-available/gittogether
    echo "    updated Nginx site ($SITE)"
  fi
  # Always reload: nginx-app.conf is included from the repo, so a change
  # there doesn't show up as a change to the site file.
  sudo nginx -t && sudo systemctl reload nginx

  echo "==> Restarting the API"
  sudo systemctl restart gittogether

  echo "Deployed $(git rev-parse --short HEAD) from $BRANCH"
}

main "$@"
