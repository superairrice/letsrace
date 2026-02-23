# Dev/Prod Settings and Deployment

## Settings modules
- Local dev: `letsrace.settings_dev`
- Production: `letsrace.settings_prod`

Defaults set in entrypoints:
- `manage.py` -> dev
- `wsgi.py`/`asgi.py` -> prod

You can always override with environment variable:

```bash
export DJANGO_SETTINGS_MODULE=letsrace.settings_prod
```

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=letsrace.settings_dev
python manage.py migrate
python manage.py runserver
```

Optional sqlite in dev:

```bash
export USE_SQLITE_FOR_DEV=true
```

## AWS EC2 deployment

1. Copy `.env.prod.example` to `.env.prod` and set real values.
2. Ensure systemd unit and nginx config are installed from `deploy/` examples.
3. Run:

```bash
./scripts/deploy_ec2.sh /home/ubuntu/letsrace /home/ubuntu/venv
```

## Recommended server commands

```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl restart gunicorn
sudo systemctl reload nginx
```
