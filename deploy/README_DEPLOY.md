Deployment quick-start for adv-an.tsaone.cloud

Overview
- This repository is a small Flask app. Recommended production stack:
  - systemd + Gunicorn to run the Python app
  - Nginx as reverse proxy and static file server
  - Certbot (Let's Encrypt) for SSL

Assumptions
- You will upload project files (the repo contents) to the server using SFTP (FileZilla) into `/opt/adscore`.
- You have a domain DNS A record for `adv-an.tsaone.cloud` pointing to your server IP.
- You have sudo/root access on the VPS (commands below use `sudo`).

Step-by-step commands to run on the VPS (copy/paste)

1) Create application directory and user, then move uploaded files

```bash
# Run as root or a user with sudo
sudo mkdir -p /opt/adscore
sudo chown $USER:$USER /opt/adscore
# Upload files via FileZilla into /opt/adscore (put repo root files here)
```

2) Create Python venv and install deps

```bash
cd /opt/adscore
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3) Create `.env` with `GROQ_API_KEY` and any other env vars

```bash
cat > /opt/adscore/.env <<EOF
GROQ_API_KEY=your_groq_api_key_here
FLASK_ENV=production
EOF
```

4) Create systemd service (see `gunicorn.service` in this repo) and start it

```bash
sudo cp deploy/gunicorn.service /etc/systemd/system/gunicorn-adscore.service
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn-adscore.service
sudo journalctl -u gunicorn-adscore.service -f
```

5) Create Nginx server block (see `nginx_adv_an.conf`), enable and reload

```bash
sudo cp deploy/nginx_adv_an.conf /etc/nginx/sites-available/adv-an.tsaone.cloud
sudo ln -s /etc/nginx/sites-available/adv-an.tsaone.cloud /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

6) Obtain SSL cert with Certbot

```bash
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d adv-an.tsaone.cloud
```

7) Verify

```bash
curl -I https://adv-an.tsaone.cloud
```

If anything fails, check logs:
- `sudo journalctl -u gunicorn-adscore.service -e`
- `sudo journalctl -u nginx -e`
- `/var/log/nginx/error.log`

Security note
- Do NOT store secrets in source control. Keep `.env` on the server and restrict permissions (`chmod 600 /opt/adscore/.env`).
