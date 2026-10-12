#!/usr/bin/env bash
# ONE-TIME setup for a fresh Ubuntu 24.04 EC2 instance. Run ON THE SERVER
# after cloning the repo to ~/campus-connect and creating backend/.env
# (copy deploy/env.production.example and fill it in):
#
#   ~/campus-connect/deploy/setup-server.sh
#
# Afterwards, use deploy.sh for every update.
set -euo pipefail

REPO="$HOME/campus-connect"
cd "$REPO"

if [ ! -f backend/.env ]; then
  echo "Missing backend/.env — copy deploy/env.production.example to backend/.env and fill it in first."
  exit 1
fi

echo "==> 2 GB swap file (small instances can run out of memory building the frontend)"
if [ ! -f /swapfile ]; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

echo "==> System packages (Python, Nginx, Postgres client)"
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-dev build-essential nginx postgresql-client git curl

echo "==> Node.js 22 (Ubuntu's own Node is too old for Vite)"
if ! command -v node >/dev/null || [ "$(node -p 'process.versions.node.split(".")[0]')" -lt 22 ]; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi

echo "==> Python virtualenv"
python3 -m venv backend/.venv

echo "==> Let Nginx read the built frontend and static files in this home folder"
chmod o+x "$HOME"

echo "==> Install the gunicorn service and the Nginx site"
sudo cp deploy/gittogether.service /etc/systemd/system/gittogether.service
sudo cp deploy/nginx.conf /etc/nginx/sites-available/gittogether
sudo ln -sf /etc/nginx/sites-available/gittogether /etc/nginx/sites-enabled/gittogether
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable gittogether nginx

echo "==> First deploy"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
deploy/deploy.sh "$BRANCH"
sudo systemctl reload nginx

echo
echo "Done. Open http://<this server's public IP>/ in a browser."
