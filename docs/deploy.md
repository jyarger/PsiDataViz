# Deploying MolViz on a public VPS

MolViz ships as a small Docker stack: the app (served by gunicorn) behind
[Caddy](https://caddyserver.com/), which terminates TLS and obtains a free Let's Encrypt
certificate automatically.

## Prerequisites

- A VPS (any provider) running Docker + the Compose plugin.
- A domain name with a DNS **A record** pointing at the VPS's public IP.
- Ports **80** and **443** open in the firewall.

## Steps

```bash
git clone <your-fork-of-molviz> && cd molviz

# Tell Caddy which hostname to get a certificate for:
export MOLVIZ_DOMAIN=molviz.example.org
# Optional: raise the GitHub API rate limit (60/hr -> 5000/hr):
export GITHUB_TOKEN=ghp_xxx          # a read-only, public-repo token is enough

docker compose up -d --build
```

Visit `https://molviz.example.org`. Caddy provisions and renews the certificate with no further
configuration.

## Operations

```bash
docker compose logs -f app      # application logs
docker compose pull && docker compose up -d --build   # update
docker compose down             # stop
```

- **Cache:** fetched files and repo listings are cached in the `molviz-cache` volume. Remove it
  (`docker volume rm molviz_molviz-cache`) to force a cold re-fetch.
- **Scaling:** increase gunicorn workers in the `Dockerfile` `CMD` (`--workers`) for more
  concurrency; the app is stateless, so you can also run multiple replicas behind Caddy.

## Local smoke test (no domain needed)

```bash
docker compose up --build      # MOLVIZ_DOMAIN defaults to localhost
# open http://localhost  (Caddy serves a local self-signed cert on https)
```

Or run just the app container directly:

```bash
docker build -t molviz .
docker run --rm -p 8050:8050 molviz
# open http://localhost:8050
```
