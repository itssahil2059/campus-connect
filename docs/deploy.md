# Deploying Git Together to AWS (EC2 + RDS)

What we end up with:

```
Browser ──http / websocket──▶ EC2 (Ubuntu)
                   ├─ Nginx: serves the React build, forwards /api, /admin and /ws
                   ├─ Daphne: runs Django + chat WebSockets ──▶ RDS PostgreSQL (private)
                   └─ Redis (localhost only): passes live chat messages between connections
```

Cost on the 6-month Free Plan: covered by credits (roughly $20–25/month of
usage). **Do step 0 first.** Use the same **region** for everything (top-right
of the AWS console, e.g. *US East (Ohio)*).

Console menus change over time — if a label doesn't match exactly, look for
the closest option and ask before picking anything that mentions extra cost.

---

## 0. Protect the account (once)

1. **MFA:** account menu (top right) → *Security credentials* → *Assign MFA device*.
2. **Budget alert:** search *Budgets* → *Create budget* → *Monthly cost budget*
   → amount **$5** → your email. You'll get an email before costs surprise you.

## 1. Launch the EC2 server

Search **EC2** → *Launch instance*:

| Setting | Value |
| --- | --- |
| Name | `gittogether-web` |
| Image (AMI) | **Ubuntu Server 24.04 LTS** (64-bit x86) |
| Instance type | **t3.micro** (must say *Free tier eligible*) |
| Key pair | *Create new key pair* → name `gittogether-key`, type ED25519, `.pem` → it downloads. **Keep this file safe; it's the only way to log in.** |
| Network → Firewall | *Create security group*; allow **SSH from My IP**, allow **HTTP from the internet** |
| Storage | **20 GiB gp3** |

*Launch instance.* Then give it a permanent address:
**EC2 → Elastic IPs → Allocate → Associate** with `gittogether-web`.
(Otherwise the IP changes every time the server stops. A public IPv4 address
costs ~$3.60/month either way; just **release** it if you ever delete the server.)

Write down the **Elastic IP** — it's the site's address.

## 2. Create the database (RDS)

Search **RDS** → *Create database*:

| Setting | Value |
| --- | --- |
| Creation method | Standard create |
| Engine | **PostgreSQL** (version 16) |
| Template | **Free tier** |
| DB instance identifier | `gittogether-db` |
| Master username | e.g. `gtadmin` |
| Credentials | *Self managed*, set a strong password (save it) |
| Instance class | **db.t4g.micro** (or db.t3.micro) |
| Storage | 20 GiB, **turn off storage autoscaling** |
| Connectivity | **Connect to an EC2 compute resource** → pick `gittogether-web` (AWS sets up the firewall rules so only the server can reach the DB) |
| Public access | **No** |
| Monitoring | turn **off** Performance Insights / Enhanced monitoring if offered |
| Additional configuration → **Initial database name** | **`campus_connect`** (easy to miss — without it the database doesn't exist) |

*Create database* and wait ~5–10 minutes until status is **Available**. Copy the
**Endpoint** (looks like `gittogether-db.xxxx.us-east-2.rds.amazonaws.com`).

## 3. Log in to the server

On your Mac:

```bash
mv ~/Downloads/gittogether-key.pem ~/.ssh/
chmod 400 ~/.ssh/gittogether-key.pem
ssh -i ~/.ssh/gittogether-key.pem ubuntu@<ELASTIC_IP>
```

Everything below runs **on the server** (the prompt shows `ubuntu@ip-...`).

## 4. Give the server read access to the (private) repo

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
```

Copy that line → GitHub repo → *Settings → Deploy keys → Add deploy key* →
title `ec2-gittogether`, paste, **leave "Allow write access" unchecked** → Add.

```bash
git clone git@github.com:itssahil2059/campus-connect.git ~/campus-connect
# type "yes" when asked about GitHub's fingerprint
```

## 5. Configure and install

```bash
cd ~/campus-connect
cp deploy/env.production.example backend/.env
python3 -c "import secrets; print(secrets.token_urlsafe(50))"   # copy the output
nano backend/.env
```

Fill in every `<...>`: `SECRET_KEY` (the value you just generated), the
Elastic IP in `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` / `FRONTEND_URL`, and the
RDS endpoint, username and password. Save: `Ctrl+O`, `Enter`, `Ctrl+X`.

Check the database connection (should print a `campus_connect=>` prompt; type `\q`):

```bash
psql -h <RDS_ENDPOINT> -U <RDS_USERNAME> -d campus_connect
```

> `psql` isn't installed yet on a fresh server — if it's missing, run
> `sudo apt-get install -y postgresql-client` first.

Then the one-time setup (5–10 minutes):

```bash
deploy/setup-server.sh
```

Create an admin login and (optionally) the demo students:

```bash
cd ~/campus-connect/backend
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py seed_demo
```

Open **http://\<ELASTIC_IP\>/** — the app should load. Admin:
`http://<ELASTIC_IP>/admin/`.

**Verification links:** emails aren't really sent yet. Watch the server log and
copy the link from it:

```bash
journalctl -u gittogether -f      # Ctrl+C to stop watching
```

---

## Updating the live site

Code goes live from the **`main`** branch: merge your work into `dev` (PR), then
open a PR **`dev` → `main`** when it's ready to go live. Then on the server:

```bash
ssh -i ~/.ssh/gittogether-key.pem ubuntu@<ELASTIC_IP>
~/campus-connect/deploy/deploy.sh
```

## One-time upgrade: real-time chat (server set up before chat existed)

Servers created with an older `setup-server.sh` run gunicorn and have no
Redis. Chat needs both changed **once**. Do these steps in order, on the server,
**after the chat PRs are merged into the branch you deploy**:

```bash
ssh -i ~/.ssh/gittogether-key.pem ubuntu@<ELASTIC_IP>
cd ~/campus-connect

# 1. Redis: listens on localhost only by default, so no security-group change.
sudo apt-get update -y && sudo apt-get install -y redis-server
sudo systemctl enable --now redis-server
redis-cli ping                       # should print PONG

# 2. Tell Django where Redis is.
nano backend/.env                    # replace REDIS_HOST/REDIS_PORT with:
                                     #   REDIS_URL=redis://127.0.0.1:6379/0

# 3. Pull first (the old deploy.sh can trip over being rewritten mid-run),
#    then deploy. deploy.sh now also copies the new systemd service (Daphne
#    instead of gunicorn) and the Nginx config with the /ws/ location.
git fetch origin && git checkout dev && git pull --ff-only origin dev
deploy/deploy.sh dev
```

Check it worked:

```bash
systemctl status gittogether         # "Daphne" in the description, active (running)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/api/auth/me/   # 401 = API OK
# WebSocket handshake through Nginx: first line should be "101 Switching Protocols"
curl -s -i -N --max-time 2 -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  -H "Origin: http://<ELASTIC_IP>" http://localhost/ws/chat/1/ | head -1
```

**Roll back** (if chat breaks the site): `git checkout <previous commit>` in
`~/campus-connect`, then `sudo cp deploy/gittogether.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl restart gittogether`
and the same for `deploy/nginx.conf` → `/etc/nginx/sites-available/gittogether` + `sudo systemctl reload nginx`.
Redis can stay installed; it's harmless.

Costs: nothing new. Redis runs on the same EC2 instance (no ElastiCache),
and WebSockets go through the existing Nginx (no load balancer).

## Domain + HTTPS (datewithincampus.com)

Puts the site on **https://datewithincampus.com** with a free Let's Encrypt
certificate. Nginx does the encryption; Django and Daphne are unchanged.
`deploy.sh` switches Nginx to `deploy/nginx-https.conf` by itself once the
certificate exists, so a deploy can never undo HTTPS. Do the steps in order.

**1. Check the IP won't change (AWS console).** EC2 → **Elastic IPs**: the
site's IP (`18.119.39.20`) should be listed and associated with
`gittogether-web`. If it isn't, allocate one and associate it first. A plain
public IP changes when the instance stops, which would break the domain.

**2. Open port 443 (AWS console).** EC2 → Security Groups → the server's group
→ Edit inbound rules → **Add rule: HTTPS, port 443, source Anywhere-IPv4
(0.0.0.0/0)**. Keep the HTTP (80) rule: Let's Encrypt and the redirect use it.

**3. Point the domain at the server (GoDaddy).** My Products →
datewithincampus.com → **DNS**:

| Type | Name | Value | TTL |
| --- | --- | --- | --- |
| A | `@` | `18.119.39.20` | 600 seconds |
| CNAME | `www` | `datewithincampus.com` | 1 hour |

Delete any other `A` record for `@` (GoDaddy adds a "Parked" one) and turn
off domain forwarding if it's on. Check from your laptop, it can take a few
minutes up to an hour:

```bash
dig +short datewithincampus.com        # should print 18.119.39.20
dig +short www.datewithincampus.com    # datewithincampus.com. + 18.119.39.20
```

**4. Deploy this code, then get the certificate (on the server).**

```bash
ssh -i ~/.ssh/gittogether-key.pem ubuntu@18.119.39.20
~/campus-connect/deploy/deploy.sh dev        # adds the /.well-known/ path to Nginx
sudo apt-get install -y certbot
sudo certbot certonly --webroot -w /var/www/certbot \
  -d datewithincampus.com -d www.datewithincampus.com \
  --email <your email> --agree-tos --no-eff-email \
  --deploy-hook "systemctl reload nginx"
```

Certbot should end with "Successfully received certificate". It renews by
itself (a systemd timer runs twice a day; certificates last 90 days) and the
hook reloads Nginx after each renewal. Test renewal with
`sudo certbot renew --dry-run`.

**5. Tell Django about the domain (on the server).** `nano ~/campus-connect/backend/.env`
and set:

```
ALLOWED_HOSTS=datewithincampus.com,www.datewithincampus.com,18.119.39.20
CSRF_TRUSTED_ORIGINS=https://datewithincampus.com,https://www.datewithincampus.com
FRONTEND_URL=https://datewithincampus.com
USE_HTTPS=True
```

`FRONTEND_URL` is where verification emails link to. `USE_HTTPS` makes
Django mark cookies secure and treat the request as HTTPS.

**6. Switch Nginx to HTTPS.** Run the deploy again; it now finds the
certificate and installs `nginx-https.conf`:

```bash
~/campus-connect/deploy/deploy.sh dev        # prints "updated Nginx site (deploy/nginx-https.conf)"
```

**Check it worked** (from your laptop):

```bash
curl -sI http://datewithincampus.com | head -3     # 301 -> https://datewithincampus.com/
curl -s -o /dev/null -w "%{http_code}\n" https://datewithincampus.com/api/auth/me/   # 401 = API OK
```

Then open https://datewithincampus.com, log in, and open a chat: the padlock
should show, and messages should still arrive live (the app switches to
secure WebSockets, `wss://`, on its own). Old `http://18.119.39.20` links now
redirect to the domain.

**Roll back** (if HTTPS breaks the site): on the server,
`sudo cp ~/campus-connect/deploy/nginx.conf /etc/nginx/sites-available/gittogether && sudo systemctl reload nginx`,
set `USE_HTTPS=False` and `FRONTEND_URL=http://18.119.39.20` in `backend/.env`,
then `sudo systemctl restart gittogether`. (The next deploy switches back to
HTTPS while the certificate exists; move it aside with
`sudo mv /etc/letsencrypt/live/datewithincampus.com ~/cert-backup` to stop that.)

Costs: none from AWS (same server and IP; certificates are free). The domain
is billed by GoDaddy.

## Handy commands (on the server)

| What | Command |
| --- | --- |
| Is Django running? | `sudo systemctl status gittogether` |
| Django logs (incl. verification emails) | `journalctl -u gittogether -f` |
| Restart Django | `sudo systemctl restart gittogether` |
| Is Redis running? | `redis-cli ping` (→ `PONG`) |
| Nginx errors | `sudo tail -f /var/log/nginx/error.log` |
| Django shell | `cd ~/campus-connect/backend && .venv/bin/python manage.py shell` |

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| Browser can't connect at all | Security group missing *HTTP from anywhere*, or wrong IP |
| `502 Bad Gateway` | Django isn't running → `journalctl -u gittogether -n 50` |
| `400 Bad Request` on every page | The IP isn't in `ALLOWED_HOSTS` in `backend/.env` |
| Admin login says CSRF failed | `CSRF_TRUSTED_ORIGINS` missing `http://<ELASTIC_IP>` |
| Django log: `could not connect to server` | RDS endpoint/password wrong, or RDS not connected to this EC2 |
| Chat doesn't update live, but messages appear after a refresh | WebSocket not connecting. Check `redis-cli ping`, that `/ws/` is in the Nginx site (`sudo nginx -T \| grep ws`), and `journalctl -u gittogether -n 50` |
| WebSocket closes right away with 403 | The page's address isn't in `ALLOWED_HOSTS` (the origin check uses it) |
| `ssh: Permission denied` | Wrong key file, or `chmod 400` not done, or your IP changed (update the SSH rule to *My IP*) |

## Stopping costs (end of semester)

Delete in this order: **RDS database** (choose whether to keep a final
snapshot — snapshots cost storage), **EC2 instance**, then **release the
Elastic IP** and delete leftover **EBS volumes/snapshots**. Check *Billing →
Bills* the next day to confirm nothing is still running.
