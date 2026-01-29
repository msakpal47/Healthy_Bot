# Healthy Bot

Doctor-style consultation web app with CSV-driven prescriptions and optional PDF Q&A.

## Local
- Python 3.12+
- pip install -r requirements.txt
- set DATA_PATH to your Data folder if needed
- run: `python e:\Healthy\simple\app.py` or `python src\web\app.py`

## AWS (Bundle: healthy_aws)
- Upload `healthy_aws` to `/home/ec2-user/healthy_aws`
- `python3 -m venv venv && source venv/bin/activate`
- `pip install -r requirements.txt`
- `export DATA_PATH=$(pwd)/Data`
- `gunicorn -b 0.0.0.0:8000 'src.web.app:app'`

## Packaging
- Use `scripts/pack.ps1` to create `healthy_local` and `healthy_aws`
