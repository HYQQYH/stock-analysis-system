# Docker Hub Connectivity Fix Guide

## Problem
Docker cannot connect to Docker Hub (auth.docker.io) due to network restrictions in China.

## Solution 1: Configure Docker Registry Mirrors (Recommended)

### Step 1: Configure Docker Daemon

#### For Windows Docker Desktop:
1. Right-click Docker Desktop icon → Settings
2. Go to "Docker Engine"
3. Replace the configuration with the content from `docker-daemon-config.json`
4. Click "Apply & Restart"

#### For Linux (with systemctl):
```bash
# Copy the configuration file
sudo cp docker-daemon-config.json /etc/docker/daemon.json

# Restart Docker
sudo systemctl daemon-reload
sudo systemctl restart docker
```

#### For Linux (with snap):
```bash
sudo snap restart docker
```

### Step 2: Verify Configuration
```bash
docker info | grep -A 10 "Registry Mirrors"
```

### Step 3: Run Docker Compose
```bash
docker compose -f ./docker-compose-dev.yml pull
docker compose -f ./docker-compose-dev.yml up -d
```

## Solution 2: Manual Pull from Mirror

If Solution 1 doesn't work, pull images manually from mirrors:

```bash
# Pull PostgreSQL
docker pull docker.m.daocloud.io/postgres:15-alpine
docker tag docker.m.daocloud.io/postgres:15-alpine postgres:15-alpine

# Pull Redis
docker pull docker.m.daocloud.io/redis:7-alpine
docker tag docker.m.daocloud.io/redis:7-alpine redis:7-alpine

# Then run docker-compose
docker compose -f ./docker-compose-dev.yml up -d
```

## Solution 3: Use Proxy

If you have access to a VPN/Proxy:

#### For Docker Desktop (Windows):
1. Right-click Docker Desktop → Settings → Resources → Proxies
2. Enable "Manual proxy configuration"
3. Set your proxy server and port
4. Apply & Restart

#### For Linux:
Edit `/etc/systemd/system/docker.service.d/http-proxy.conf`:
```ini
[Service]
Environment="HTTP_PROXY=http://proxy.example.com:8080"
Environment="HTTPS_PROXY=http://proxy.example.com:8080"
Environment="NO_PROXY=localhost,127.0.0.1"
```

Then restart Docker:
```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

## Solution 4: Switch to Image-Specific Repositories

Modify `docker-compose-dev.yml` to use alternative image sources:

```yaml
services:
  postgres:
    image: registry.cn-hangzhou.aliyuncs.com/library/postgres:15-alpine
    # ... rest of config
  
  redis:
    image: registry.cn-hangzhou.aliyuncs.com/library/redis:7-alpine
    # ... rest of config
```

## Verify Fix

After applying any solution, test with:
```bash
docker pull postgres:15-alpine
docker pull redis:7-alpine
```

If images pull successfully, run:
```bash
docker compose -f ./docker-compose-dev.yml up -d
```

## Troubleshooting

### Check Docker Status
```bash
docker ps
docker info
```

### View Docker Logs
```bash
docker compose -f ./docker-compose-dev.yml logs
```

### Test Network Connectivity
```bash
ping auth.docker.io
curl -I https://auth.docker.io
```

### Clear Docker Cache (if needed)
```bash
docker system prune -a
```

## Available Mirror Registries

If one mirror fails, try another:
- https://docker.m.daocloud.io
- https://docker.1panel.live
- https://hub.rat.dev
- https://docker.chenby.cn
- https://docker.awsl9527.cn
- https://registry.cn-hangzhou.aliyuncs.com (Alibaba Cloud)
- https://dockerproxy.com

## Additional Fix: Backend Build Issues

If you encounter Debian repository errors during backend build:

The Dockerfile has been updated to use Chinese mirrors:
- Debian packages: mirrors.tuna.tsinghua.edu.cn
- Python packages: https://pypi.tuna.tsinghua.edu.cn/simple

### Rebuild After Fixing Docker Hub Issue

After configuring registry mirrors, rebuild with:

```bash
# Clean previous build cache
docker compose -f ./docker-compose-dev.yml down
docker system prune -f

# Rebuild with no cache
docker compose -f ./docker-compose-dev.yml build --no-cache

# Start services
docker compose -f ./docker-compose-dev.yml up -d
```

## Notes

- The mirrors listed in `docker-daemon-config.json` are currently active in China
- Mirror availability may change over time
- If all mirrors fail, consider using a VPN/Proxy or find updated mirror lists
- The backend Dockerfile now uses Tsinghua University mirrors for both Debian and PyPI packages
