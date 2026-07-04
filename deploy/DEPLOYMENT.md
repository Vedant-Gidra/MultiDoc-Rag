# Deployment Guide — AWS EC2 + Vercel (End to End)

Deploy **MultiDocRAG** with:
- **Frontend** → Vercel (free)
- **Backend + Ollama + Chroma + SQLite** → AWS EC2 Ubuntu VM

```
Browser → Vercel (React)
              ↓  HTTPS
         AWS EC2 (nginx → FastAPI → Ollama embeddings)
              ↓
         Groq API (LLM answers)
```

**Estimated cost:** $0 on AWS Free Tier (t3.micro, 12 months) + Vercel free + Groq free tier.

---

## Table of contents

1. [Prerequisites](#part-0--prerequisites)
2. [Local prep on Windows](#part-1--local-prep-windows-powershell)
3. [Create EC2 instance (AWS Console)](#part-2--create-ec2-instance-aws-console)
4. [Connect to EC2 from Windows](#part-3--connect-to-ec2-from-windows)
5. [Set up the EC2 server](#part-4--set-up-the-ec2-server-ssh-session)
6. [Deploy backend (systemd + nginx)](#part-5--deploy-backend-systemd--nginx)
7. [Deploy frontend on Vercel](#part-6--deploy-frontend-on-vercel)
8. [Final wiring (CORS + test)](#part-7--final-wiring-and-end-to-end-test)
9. [Optional: HTTPS with a domain](#part-8--optional-https-with-a-domain)
10. [Resume checklist](#part-9--resume-checklist)
11. [Troubleshooting](#part-10--troubleshooting)
12. [Updating after code changes](#part-11--updating-after-code-changes)

---

## Part 0 — Prerequisites

Before you start, have these ready:

| Item | Where |
|------|--------|
| AWS account | [aws.amazon.com](https://aws.amazon.com) (you already have this) |
| GitHub repo | This project pushed to GitHub |
| Groq API key | [console.groq.com](https://console.groq.com) → API Keys |
| Vercel account | [vercel.com](https://vercel.com) → sign in with GitHub |
| Domain (optional) | For HTTPS; you can use raw EC2 IP first |

**Recommended EC2 instance:** `t3.micro` (Free Tier). Ollama works but is slow — we add **2 GB swap** in Part 4.

---

## Part 1 — Local prep (Windows PowerShell)

### 1.1 Open project folder

```powershell
cd C:\Users\vedan\Downloads\projects\MultiDocRag
```

### 1.2 Push latest code to GitHub

```powershell
git add .
git status
git commit -m "Prepare for AWS EC2 deployment"
git push origin main
```

> Never commit `Backend/.env` — it contains secrets and is gitignored.

### 1.3 Confirm local backend env (for reference)

Your local `Backend\.env` should have:

```env
GROQ_API_KEY=your-key
SECRET_KEY=your-secret
DATABASE_URL=sqlite:///./app.db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

You will copy the same keys (plus Vercel URL later) onto the EC2 server.

Generate a new secret if needed:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 1.4 (Optional) Test locally before deploying

Reinstall Ollama from [ollama.com/download](https://ollama.com/download) if removed:

```powershell
ollama pull nomic-embed-text
```

```powershell
cd Backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Another PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected: `status : ok`

---

## Part 2 — Create EC2 instance (AWS Console)

Do all of this in the browser at **[AWS Console → EC2](https://console.aws.amazon.com/ec2/)**.

Pick a region close to you (top-right, e.g. **Asia Pacific (Mumbai) ap-south-1**).

### Step 2.1 — Launch instance

1. Click **EC2** in the search bar (or go to Services → Compute → EC2).
2. Left sidebar → **Instances** → **Launch instances**.

### Step 2.2 — Name and OS

| Field | Value |
|-------|--------|
| **Name** | `multidocrag-api` |
| **Application and OS Images (AMI)** | **Ubuntu Server 24.04 LTS (HVM), SSD Volume Type** |
| **Architecture** | 64-bit (x86) |
| **Free tier eligible** | Should show "Free tier eligible" badge |

### Step 2.3 — Instance type

| Field | Value |
|-------|--------|
| **Instance type** | **t3.micro** (2 vCPU, 1 GiB RAM) — Free Tier |

> `t3.micro` is enough for a resume demo. First PDF upload may take 1–2 minutes while Ollama embeds chunks.

### Step 2.4 — Key pair (login)

1. **Key pair name** → **Create new key pair**
2. Name: `multidocrag-key`
3. Type: **RSA**
4. Format: **.pem** (for OpenSSH on Windows)
5. Click **Create key pair** — a `.pem` file downloads automatically.
6. Move it somewhere safe, e.g.:

```powershell
Move-Item -Path "$env:USERPROFILE\Downloads\multidocrag-key.pem" -Destination "$env:USERPROFILE\.ssh\multidocrag-key.pem"
```

Fix permissions (required by SSH on Windows):

```powershell
icacls "$env:USERPROFILE\.ssh\multidocrag-key.pem" /inheritance:r
icacls "$env:USERPROFILE\.ssh\multidocrag-key.pem" /grant:r "$($env:USERNAME):(R)"
```

### Step 2.5 — Network settings (Security Group)

Click **Edit** on Network settings and configure:

| Setting | Value |
|---------|--------|
| **VPC** | Default |
| **Subnet** | No preference (default) |
| **Auto-assign public IP** | **Enable** |
| **Firewall (security group)** | **Create security group** |
| **Security group name** | `multidocrag-sg` |

**Inbound rules** — add these three rules:

| Type | Port | Source | Purpose |
|------|------|--------|---------|
| SSH | 22 | **My IP** (dropdown) | You connecting from Windows |
| HTTP | 80 | **Anywhere** (`0.0.0.0/0`) | nginx API |
| HTTPS | 443 | **Anywhere** (`0.0.0.0/0`) | HTTPS later |

> Do **not** open port 8000 publicly. FastAPI stays on `127.0.0.1` behind nginx.

### Step 2.6 — Storage

| Field | Value |
|-------|--------|
| **Size** | **20–30 GiB** (Free Tier includes 30 GiB) |
| **Volume type** | gp3 or gp2 |

### Step 2.7 — Launch

1. Review summary on the right.
2. Click **Launch instance**.
3. Wait until **Instance state** = **Running** (Instances page, ~1–2 min).

### Step 2.8 — Note your Public IP

1. Click your instance ID → **Details** tab.
2. Copy **Public IPv4 address** (e.g. `3.110.45.67`).

This is your API host until you add a domain.

### Step 2.9 — (Recommended) Elastic IP

EC2 public IP changes if you stop/start the instance. For a stable URL:

1. Left sidebar → **Network & Security** → **Elastic IPs**.
2. **Allocate Elastic IP address** → **Allocate**.
3. Select the new IP → **Actions** → **Associate Elastic IP address**.
4. Choose your `multidocrag-api` instance → **Associate**.

Use this Elastic IP everywhere instead of the temporary public IP.

---

## Part 3 — Connect to EC2 from Windows

Replace `YOUR_EC2_IP` with your Public or Elastic IP.

```powershell
ssh -i "$env:USERPROFILE\.ssh\multidocrag-key.pem" ubuntu@YOUR_EC2_IP
```

First connect asks `Are you sure you want to continue connecting?` → type **yes**.

> Default username for Ubuntu AMI on AWS is always **`ubuntu`**.

If SSH times out:
- Check instance is **Running**
- Security group allows SSH from **your current IP** (IP changes on home Wi‑Fi — update rule in EC2 → Security Groups → Edit inbound rules)
- You used the correct `.pem` path

---

## Part 4 — Set up the EC2 server (SSH session)

All commands below run **on the EC2 server** after SSH login, unless marked Windows.

### 4.1 Update system and install packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx git certbot python3-certbot-nginx curl
```

### 4.2 Add swap (required on t3.micro for Ollama)

t3.micro has only 1 GB RAM. Run the project swap script:

```bash
# After cloning in 4.4, or run manually now:
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

You should see ~2G swap.

Or use the included script after cloning:

```bash
bash ~/MultiDocRag/deploy/setup-ec2-swap.sh
```

### 4.3 Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable ollama
sudo systemctl start ollama
sudo systemctl status ollama
```

Pull the embedding model (used by this project):

```bash
ollama pull nomic-embed-text
ollama list
```

Quick test:

```bash
curl http://127.0.0.1:11434/api/tags
```

### 4.4 Clone your GitHub repo

```bash
cd ~
git clone https://github.com/YOUR_GITHUB_USERNAME/MultiDocRag.git
cd MultiDocRag
```

Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username.

If the repo is private, use a Personal Access Token:

```bash
git clone https://YOUR_TOKEN@github.com/YOUR_GITHUB_USERNAME/MultiDocRag.git
```

### 4.5 Python virtual environment

```bash
cd ~/MultiDocRag/Backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

This takes several minutes (torch, chromadb, etc.).

### 4.6 Create production `.env` on EC2

```bash
nano ~/MultiDocRag/Backend/.env
```

Paste (replace with your real values):

```env
GROQ_API_KEY=gsk_your_groq_key_here
SECRET_KEY=your_long_random_secret_here
DATABASE_URL=sqlite:///./app.db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Save: **Ctrl+O** → Enter → **Ctrl+X**.

Generate secret on server:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

> You will add your Vercel URL to `CORS_ORIGINS` in Part 7 after frontend deploy.

### 4.7 Test API manually

```bash
cd ~/MultiDocRag/Backend
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On the server (new SSH tab or same session after opening another terminal):

```bash
curl http://127.0.0.1:8000/health
```

Expected: `{"status":"ok"}`

Stop test server: **Ctrl+C**

---

## Part 5 — Deploy backend (systemd + nginx)

### 5.1 Install systemd service

The service file is preconfigured for AWS Ubuntu (`user=ubuntu`):

```bash
sudo cp ~/MultiDocRag/deploy/multidocrag-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable multidocrag-api
sudo systemctl start multidocrag-api
sudo systemctl status multidocrag-api
```

Should show **active (running)**.

View logs:

```bash
journalctl -u multidocrag-api -f
```

Exit logs: **Ctrl+C**

### 5.2 Configure nginx

Copy config and set your EC2 IP:

```bash
sudo cp ~/MultiDocRag/deploy/nginx-multidocrag.conf /etc/nginx/sites-available/multidocrag
sudo nano /etc/nginx/sites-available/multidocrag
```

Change the `server_name` line to your EC2 public IP (or domain later):

```nginx
server_name YOUR_EC2_PUBLIC_IP;
```

Example:

```nginx
server_name 3.110.45.67;
```

Enable site:

```bash
sudo ln -sf /etc/nginx/sites-available/multidocrag /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 5.3 Test API from Windows (PowerShell)

Replace IP:

```powershell
Invoke-RestMethod http://YOUR_EC2_IP/health
```

Expected:

```
status
------
ok
```

If this works, your **backend is live**. API base URL for Vercel:

```
http://YOUR_EC2_IP
```

(no trailing slash)

---

## Part 6 — Deploy frontend on Vercel

### 6.1 Import project (browser)

1. Go to [vercel.com/new](https://vercel.com/new).
2. **Import** your GitHub `MultiDocRag` repository.
3. Configure:

| Setting | Value |
|---------|--------|
| **Framework Preset** | Vite |
| **Root Directory** | `Frontend` (click Edit → set to Frontend) |
| **Build Command** | `npm run build` (default) |
| **Output Directory** | `dist` (default) |

4. **Environment Variables** — add before first deploy:

| Name | Value |
|------|--------|
| `VITE_API_URL` | `http://YOUR_EC2_IP` |

Example: `http://3.110.45.67`

> Vite bakes this into the build. If you change it later, you must **redeploy**.

5. Click **Deploy**.
6. Wait ~1–2 minutes. Copy your live URL, e.g. `https://multidocrag.vercel.app`.

### 6.2 (Alternative) Vercel CLI from Windows

```powershell
npm install -g vercel
cd C:\Users\vedan\Downloads\projects\MultiDocRag\Frontend
vercel login
vercel --prod
```

Set `VITE_API_URL` in Vercel dashboard → Project → Settings → Environment Variables, then redeploy.

---

## Part 7 — Final wiring and end-to-end test

### 7.1 Add Vercel URL to backend CORS

Back on EC2 (SSH):

```bash
nano ~/MultiDocRag/Backend/.env
```

Update `CORS_ORIGINS` to include your exact Vercel URL (no trailing slash):

```env
CORS_ORIGINS=https://multidocrag.vercel.app,http://localhost:5173,http://127.0.0.1:5173
```

Restart API:

```bash
sudo systemctl restart multidocrag-api
```

### 7.2 Full app test

1. Open your Vercel URL in the browser.
2. **Sign up** with a test email/password.
3. **Upload** a small PDF (1–5 pages). Wait 30–90 seconds on t3.micro.
4. Click the PDF in the sidebar.
5. Ask a question, e.g. *"What is this document about?"*
6. Confirm you get an **answer** and **sources**.

### 7.3 Smoke-test from PowerShell

```powershell
# Backend health
Invoke-RestMethod http://YOUR_EC2_IP/health

# Frontend loads (should return 200)
Invoke-WebRequest https://YOUR_VERCEL_URL.vercel.app -UseBasicParsing | Select-Object StatusCode
```

---

## Part 8 — Optional: HTTPS with a domain

Browsers and some networks prefer HTTPS. Steps:

### 8.1 Buy/use a domain

Any registrar (Namecheap, GoDaddy, etc.). Create DNS records:

| Type | Name | Value |
|------|------|--------|
| A | `api` | YOUR_EC2_IP |
| CNAME | `www` | your-app.vercel.app (Vercel handles this in their dashboard) |

### 8.2 Update nginx on EC2

```bash
sudo nano /etc/nginx/sites-available/multidocrag
```

Set:

```nginx
server_name api.yourdomain.com;
```

```bash
sudo nginx -t && sudo systemctl restart nginx
```

### 8.3 Get free SSL certificate

```bash
sudo certbot --nginx -d api.yourdomain.com
```

Follow prompts (email, agree, redirect HTTP→HTTPS yes).

### 8.4 Update Vercel and CORS

1. Vercel → Environment Variables → `VITE_API_URL` = `https://api.yourdomain.com` → **Redeploy**.
2. EC2 `.env` → add `https://your-app.vercel.app` to `CORS_ORIGINS` → restart API.

---

## Part 9 — Resume checklist

Add to README and resume:

```markdown
**MultiDocRAG** — Multi-user RAG over PDFs
- Stack: React, FastAPI, ChromaDB, Ollama, Groq, AWS EC2, Vercel
- Live demo: https://your-app.vercel.app
- GitHub: https://github.com/yourusername/MultiDocRag
```

Create a demo account once (via signup) and mention credentials in README for recruiters.

Optional: record a 2-minute Loom/screen capture as backup.

---

## Part 10 — Troubleshooting

### SSH / connection

| Problem | Fix |
|---------|-----|
| `Permission denied (publickey)` | Wrong `.pem` path or user — use `ubuntu@IP` |
| `Connection timed out` | Security group: SSH port 22 from **My IP**; instance must be Running |
| IP changed after stop/start | Use **Elastic IP** (Part 2.9) |

### AWS Console

| Problem | Fix |
|---------|-----|
| Can't find instance | Check correct **region** (top-right) |
| HTTP blocked | Security group: inbound **80** and **443** from `0.0.0.0/0` |
| Free tier warning | t3.micro + 30GB disk stays in free tier for 12 months |

### App errors

| Problem | Fix |
|---------|-----|
| CORS error in browser DevTools | Add exact Vercel URL to `CORS_ORIGINS`, restart API |
| `502 Bad Gateway` from nginx | `sudo systemctl status multidocrag-api` — fix errors in `journalctl -u multidocrag-api -f` |
| Upload hangs / very slow | Normal on t2.micro; check Ollama: `systemctl status ollama`, `ollama list` |
| Upload fails | `journalctl -u multidocrag-api -f` while uploading; ensure swap is on: `free -h` |
| Query fails | Check `GROQ_API_KEY` in EC2 `.env`; test Groq key at console.groq.com |
| Ollama OOM / killed | Re-run swap setup (Part 4.2); consider stopping other services |
| Frontend hits wrong API | Redeploy Vercel after changing `VITE_API_URL` |
| Mixed content error | Vercel is HTTPS but API is HTTP — use domain + certbot (Part 8) or test with HTTP Vercel preview |

### Useful diagnostic commands (EC2)

```bash
# All services
sudo systemctl status nginx ollama multidocrag-api

# API logs
journalctl -u multidocrag-api -n 50 --no-pager

# Ollama
curl http://127.0.0.1:11434/api/tags

# Disk / memory
df -h
free -h

# nginx config test
sudo nginx -t
```

---

## Part 11 — Updating after code changes

### Windows — push code

```powershell
cd C:\Users\vedan\Downloads\projects\MultiDocRag
git add .
git commit -m "Describe your change"
git push origin main
```

### EC2 — pull and restart

```bash
cd ~/MultiDocRag
git pull origin main
source Backend/venv/bin/activate
pip install -r Backend/requirements.txt
sudo systemctl restart multidocrag-api
```

Vercel auto-redeploys on push if connected to GitHub.

---

## Quick reference

| What | Where / Value |
|------|----------------|
| EC2 SSH | `ssh -i ~/.ssh/multidocrag-key.pem ubuntu@YOUR_EC2_IP` |
| API health | `http://YOUR_EC2_IP/health` |
| Frontend | `https://your-app.vercel.app` |
| Env on EC2 | `~/MultiDocRag/Backend/.env` |
| API logs | `journalctl -u multidocrag-api -f` |
| Restart API | `sudo systemctl restart multidocrag-api` |
| Restart nginx | `sudo systemctl restart nginx` |

---

## Cost summary

| Service | Cost |
|---------|------|
| AWS EC2 t3.micro | Free Tier 12 months, then ~$8–10/mo if kept running |
| Elastic IP | Free while attached to running instance |
| Vercel | Free |
| Groq API | Free tier |
| Domain (optional) | ~$10/year |

**Tip:** **Stop** (not terminate) the EC2 instance when not demoing to save money after free tier ends. Data on the root volume is kept when stopped.
