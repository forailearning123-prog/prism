# Deploying Prism on KVM using Coolify

This guide explains how to deploy the Prism application on a KVM virtual machine using Coolify. Coolify is an open-source, self-hostable alternative to Vercel/Netlify/Heroku that makes managing Docker-based deployments extremely easy.

## Prerequisites
1. **A KVM Virtual Machine:** (e.g., from a cloud provider or self-hosted) with at least 2GB RAM and Ubuntu/Debian installed.
2. **Coolify Installed:** If you haven't installed Coolify on your KVM instance yet, run this command via SSH:
   ```bash
   curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
   ```
3. **A GitHub Repository:** Ensure your local code is pushed to a GitHub (or GitLab/Bitbucket) repository.

## Deployment Steps

### 1. Connect your Repository to Coolify
1. Open your Coolify Dashboard.
2. Navigate to **Projects** and create a new Project (or select an existing one).
3. Create a new **Environment** (e.g., `production`).
4. Click **+ Add Resource** and select **Docker Compose**.
5. Connect your Git repository (e.g., using a GitHub App or Public/Private Repo URL) and select the branch you want to deploy (usually `main`).

### 2. Configure the Deployment
1. Once the resource is created, Coolify will parse the `docker-compose.yml` file from the repository.
2. In the Coolify Dashboard for this resource, ensure the **Docker Compose Location** is set to `/docker-compose.yml`.
3. **Domains/Routing:** Coolify will automatically detect the services `frontend` and `backend`.
   - Set the domain for the **frontend** service (e.g., `https://prism.yourdomain.com`).
   - Set the domain for the **backend** service (e.g., `https://api.prism.yourdomain.com`).
4. Coolify will map these domains to the internal container ports (`80` for frontend and `8000` for backend) without exposing them directly on the KVM host, thanks to Coolify's built-in reverse proxy (Traefik).

### 3. Environment Variables
Navigate to the **Environment Variables** section in the Coolify resource dashboard and set the following variables based on `.env.example`:

- `SECRET_KEY`: Generate a random string (e.g., using `openssl rand -hex 32`).
- `DEBUG`: Set to `false`.
- `FRONTEND_URL`: Set to your frontend domain (e.g., `https://prism.yourdomain.com`).
- `VITE_API_URL`: Set to your backend domain (e.g., `https://api.prism.yourdomain.com`).

### 4. Deploy
1. Click the **Deploy** button.
2. Coolify will build the Docker images for both `backend` and `frontend` and start the containers.
3. You can monitor the build process and container logs directly from the Coolify dashboard.
4. Once deployed, the frontend will wait for the backend healthcheck to pass, ensuring a smooth startup.

## Updating the Code
To update your application, simply push your changes to your Git repository branch.
You can configure Coolify to trigger automatic deployments upon new commits via webhooks in the **Webhooks** section of your Coolify resource.