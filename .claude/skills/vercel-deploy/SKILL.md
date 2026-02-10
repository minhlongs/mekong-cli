---
name: vercel
description: Deploy applications and manage projects with Vercel CLI
---

# Vercel Skill

## Deployment

```bash
vercel                          # deploy current directory
vercel --prod                   # deploy to production
vercel /path/to/project         # deploy specific path
vercel -e NODE_ENV=production   # with env var
vercel build && vercel --prebuilt  # prebuilt deploy
```

## Project Management

```bash
vercel link                      # link to project
vercel projects list             # list all projects
vercel projects add <name>       # create new project
vercel pull                      # pull settings + env vars
```

## Environment Variables

```bash
vercel env list [environment]    # list env vars
vercel env add <name> production # add env var
vercel env pull .env.local       # pull to .env.local
```

## Domains & Aliases

```bash
vercel domains list              # list domains
vercel domains add <domain> <project>
vercel alias set <deployment> <alias>
```

## Deployments

```bash
vercel ls                        # list deployments
vercel inspect <url|id>          # deployment info
vercel logs <url|id>             # runtime logs
vercel promote <url|id>          # promote to production
vercel rollback                  # rollback
vercel redeploy <url|id>         # rebuild + deploy
```

## Auth

```bash
vercel login [email]
vercel whoami
vercel switch [scope]
```
