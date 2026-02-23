#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/deploy_ec2.sh /home/ubuntu/letsrace /home/ubuntu/venv
# Defaults:
#   APP_DIR=/home/ubuntu/letsrace
#   VENV_DIR=/home/ubuntu/venv

APP_DIR="${1:-/home/ubuntu/letsrace}"
VENV_DIR="${2:-/home/ubuntu/venv}"

cd "$APP_DIR"
source "$VENV_DIR/bin/activate"

export DJANGO_SETTINGS_MODULE="letsrace.settings_prod"

python -m pip install --upgrade pip
pip install -r requirements.txt

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py check --deploy

sudo systemctl restart gunicorn
sudo systemctl reload nginx

echo "[deploy] done"
