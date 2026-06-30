# Prism — Deployment Guide (KVM + Coolify)

> **Who is this guide for?**
> This guide is written for people who are **not technical**. Every step is explained in plain language. You do not need to be a developer to follow it.

---

## 📖 What You Will End Up With

After following this guide you will have **Prism running live on the internet** on your own server, secured with HTTPS, accessible via a domain name (e.g. `https://prism.yourcompany.com`).

---

## 🗺️ Big Picture (Plain English)

| Term | What it means in simple words |
|------|-------------------------------|
| **KVM server** | A virtual machine (computer in the cloud) that actually runs your software |
| **Coolify** | A friendly control panel you install on that server — it lets you deploy apps by clicking buttons instead of typing code |
| **Docker** | The technology that packages Prism so it runs the same way everywhere (Coolify handles this for you) |
| **Domain** | Your web address, e.g. `prism.yourcompany.com` |
| **HTTPS / SSL** | The padlock in the browser — Coolify sets this up automatically for free |

---

## ✅ What You Need Before You Start

Before beginning, make sure you have:

1. **A KVM virtual machine** (VPS) with:
   - At least **2 CPU cores** and **4 GB RAM** (8 GB recommended)
   - **Ubuntu 22.04** operating system (most providers let you pick this)
   - A **public IP address** (your hosting provider gives you this)
   - **SSH access** — a way to log in to the server (explained below)

2. **A domain name** (e.g. bought from GoDaddy, Namecheap, Google Domains, etc.)

3. **A computer** (Windows, Mac, or Linux) to do the setup from

> **Where to get a KVM server?**
> Popular providers: Hetzner Cloud, DigitalOcean, Vultr, Linode, or any provider that offers "KVM VPS". Pick the cheapest plan that meets the specs above. Most cost $6–$20/month.

---

## 🔑 Step 1 — Get SSH Access to Your Server

SSH is simply a secure way to send commands to your server. Think of it like a remote control.

### 1.1 — Install an SSH client

- **Windows:** Download and install [PuTTY](https://www.putty.org/) or use the built-in **Windows Terminal** (search for it in the Start menu).
- **Mac / Linux:** SSH is already installed. Open the **Terminal** app.

### 1.2 — Get your server's IP address

Your hosting provider shows the IP address in their dashboard after you create the server. It looks something like `159.89.12.34`.

### 1.3 — Connect to your server

Open Terminal (or PuTTY) and type:

```
ssh root@YOUR_SERVER_IP
```

Replace `YOUR_SERVER_IP` with your actual IP address, for example:

```
ssh root@159.89.12.34
```

When asked "Are you sure you want to continue connecting?" type `yes` and press **Enter**.

Enter the password your hosting provider gave you (or use your SSH key if you set one up).

> ✅ If you see a command prompt like `root@ubuntu-server:~#` you are successfully logged in.

---

## 🛠️ Step 2 — Install Coolify on Your Server

Coolify is a free, open-source tool that makes deploying apps as easy as using a website.

### 2.1 — Run the Coolify installer

While still logged in to your server via SSH, paste this single command and press **Enter**:

```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

This will:
- Install Docker automatically
- Install Coolify
- Start Coolify on port 8000

The process takes about 2–5 minutes. Wait until you see the message saying installation is complete.

### 2.2 — Open Coolify in your browser

On your own computer, open a web browser and go to:

```
http://YOUR_SERVER_IP:8000
```

For example: `http://159.89.12.34:8000`

> ⚠️ If the page does not load, your server firewall may be blocking port 8000. In your hosting provider's dashboard, look for "Firewall" or "Security Groups" and allow inbound traffic on port **8000** temporarily (you can remove it after setup).

### 2.3 — Create your Coolify admin account

You will see a registration form. Fill in:
- **Email address** (yours)
- **Password** (choose something strong)

Click **Register**. This is your Coolify admin account — save these credentials safely.

---

## 🖥️ Step 3 — Add Your Server to Coolify

Coolify needs to know about your server so it can deploy apps on it.

1. After logging in, click **Servers** in the left sidebar.
2. Click **Add Server**.
3. Choose **Remote Server** (not localhost, unless Coolify is installed on the same machine you will deploy to — if you followed this guide, choose **localhost** since Coolify is already on your KVM server).

> **Simple rule:** Because you installed Coolify directly on your KVM server, you will use the **localhost** option. Coolify is already on the same machine where apps will run.

4. Click **Validate & Save**.
5. Coolify will check the server and show a green ✅ when it's ready.

---

## 🌐 Step 4 — Point Your Domain to Your Server

Before Coolify can give you an HTTPS address, your domain needs to point to your server's IP.

1. Log in to wherever you bought your domain (e.g. GoDaddy, Namecheap).
2. Find **DNS Settings** or **DNS Management**.
3. Add an **A Record**:
   - **Name / Host:** `prism` (or `@` for the root domain)
   - **Value / Points to:** your server's IP address (e.g. `159.89.12.34`)
   - **TTL:** leave as default (usually 3600)
4. Save the record.

> ⏱️ DNS changes can take up to **24 hours** to work worldwide, but usually propagate within 15–30 minutes.

> **Example:** If your domain is `yourcompany.com` and you added a record for `prism`, your Prism app will be accessible at `https://prism.yourcompany.com`.

---

## 🚀 Step 5 — Deploy Prism with Coolify

### 5.1 — Create a new Project

1. In Coolify, click **Projects** in the left sidebar.
2. Click **New Project**.
3. Give it a name, e.g. `Prism`, and click **Create**.

### 5.2 — Add a new Resource (the app)

1. Inside your new project, click **New Resource**.
2. Choose **Docker Compose**.
3. Choose **Public Repository**.
4. In the **Repository URL** field, enter:
   ```
   https://github.com/forailearning123-prog/prism
   ```
5. Leave the **Branch** as `main`.
6. Click **Next / Continue**.

Coolify will fetch the repository and detect the `docker-compose.yml` file automatically.

### 5.3 — Set Environment Variables

This is the important configuration step. Click the **Environment Variables** tab and add the following:

| Variable Name | What to put |
|---------------|-------------|
| `SECRET_KEY` | A long random password — see how to generate one below |
| `FRONTEND_URL` | Your full domain with https, e.g. `https://prism.yourcompany.com` |
| `DEBUG` | `false` |
| `VITE_API_URL` | Leave **empty** (blank) |

**How to generate a SECRET_KEY:**

Go back to your SSH terminal and type:

```bash
openssl rand -hex 32
```

Copy the long string of letters and numbers it outputs (e.g. `a3f9d2c1...`). Paste that as the value for `SECRET_KEY`.

> ⚠️ Keep your `SECRET_KEY` private. It protects your users' login sessions. Never share it publicly.

### 5.4 — Configure the Domain

1. Click the **Domains** or **Network** tab in your resource settings.
2. In the domain field for the **frontend** service, enter your domain:
   ```
   https://prism.yourcompany.com
   ```
3. Make sure **HTTPS** is enabled (there is usually a toggle — turn it on).
4. Coolify will automatically get a free SSL certificate from **Let's Encrypt** (this is what creates the padlock in the browser).

### 5.5 — Deploy!

1. Click the **Deploy** button (it may be labelled **Deploy** or **Start**).
2. Coolify will build and start both services (backend + frontend). This takes **3–8 minutes** the first time.
3. Watch the **Logs** tab — you will see lines scrolling by. When you see messages like `Application startup complete` and `nginx: worker process`, the deployment is done.

> ✅ If the deployment is successful, you will see both services show as **Running** with green indicators.

---

## 🔍 Step 6 — Verify Everything is Working

1. Open a new browser tab and go to your domain, e.g.:
   ```
   https://prism.yourcompany.com
   ```
2. You should see the **Prism login page**.
3. Log in with the demo credentials:
   - **Email:** `demo@prism.ai`
   - **Password:** `demo1234`

> 🎉 If you see the Prism dashboard — congratulations, your deployment is complete!

---

## 🔒 Step 7 — Change the Demo Password (Important!)

The demo account password is public. Change it immediately after first login:

1. Log in with `demo@prism.ai` / `demo1234`.
2. Go to **Settings** (gear icon) in the sidebar.
3. Change the password to something strong that only you know.

---

## 🔁 Step 8 — Updating Prism in the Future

When a new version of Prism is released:

1. Open Coolify and go to your Prism resource.
2. Click **Redeploy** or **Pull & Deploy**.
3. Coolify will pull the latest code and restart the app automatically. Your data is preserved.

---

## 🆘 Troubleshooting

### "Page not found" or can't reach the domain
- Wait a bit longer — DNS can take up to 24 hours.
- Check in Coolify that both services show as **Running**.
- Make sure your domain A record points to the correct IP.

### Deployment failed / error in logs
- Click the **Logs** tab in Coolify and scroll to find the red error message.
- The most common cause is a missing or wrong environment variable. Double-check `SECRET_KEY` and `FRONTEND_URL`.

### Forgot Coolify password
- On your server via SSH, run: `coolify reset-password` and follow the prompts.

### 502 Bad Gateway
- The backend service may still be starting. Wait 1–2 minutes and refresh.
- Check the backend logs in Coolify for error messages.

### Need to restart the app
- In Coolify, find your Prism resource and click **Restart**.

---

## 📞 Getting Help

- **Coolify Documentation:** https://coolify.io/docs
- **Coolify Community (Discord):** https://coolify.io/discord
- **Prism GitHub Issues:** https://github.com/forailearning123-prog/prism/issues

---

## 📋 Quick Reference Checklist

Use this as a checklist to track your progress:

- [ ] KVM server created (Ubuntu 22.04, 2 CPU, 4 GB RAM minimum)
- [ ] SSH access confirmed
- [ ] Coolify installed via the install script
- [ ] Coolify admin account created
- [ ] Server validated in Coolify
- [ ] Domain A record pointing to server IP
- [ ] Prism resource created in Coolify (Docker Compose from GitHub)
- [ ] Environment variables set (`SECRET_KEY`, `FRONTEND_URL`, `DEBUG=false`)
- [ ] Domain configured with HTTPS in Coolify
- [ ] Deployment successful (both services Running)
- [ ] Prism login page accessible at your domain
- [ ] Demo password changed
