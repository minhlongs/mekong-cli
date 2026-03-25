# Docker Skill — Best Practices

## Standards
- Multi-stage builds to minimize image size
- Non-root user in production containers
- `.dockerignore` to exclude unnecessary files
- Pin base image versions (no `latest` tag)

## Patterns
- Builder pattern: compile in stage 1, copy binary to stage 2
- Use `COPY --from=builder` for minimal final images
- Health checks via `HEALTHCHECK` instruction
- Docker Compose for local dev, K8s for production

## Gotchas
- Layer caching: put rarely-changing layers first
- `COPY requirements.txt` before `COPY .` for pip cache
- Don't store secrets in image layers — use runtime env
- `docker-compose up --build` to rebuild after changes
- Alpine images may have musl compatibility issues

## Security
- Scan images with `docker scout` or `trivy`
- No secrets in Dockerfile or build args
- Read-only filesystem where possible
- Drop all capabilities, add only what's needed
