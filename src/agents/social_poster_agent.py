"""Mekong CLI - SocialPosterAgent

Platform adapters for auto-posting and comment polling on:
  - Discord  → social_discord_adapter.py
  - dev.to   → REST API via httpx
  - GitHub Discussions → gh CLI + GraphQL
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from typing import Any

import httpx

from .social_discord_adapter import DiscordAdapter

logger = logging.getLogger(__name__)

DEVTO_API_BASE = "https://dev.to/api"


class SocialPosterAgent:
    """Adapters for posting content and fetching/replying to comments."""

    def __init__(self) -> None:
        self._discord = DiscordAdapter()
        self.devto_api_key = os.getenv("DEVTO_API_KEY", "")

    # ------------------------------------------------------------------
    # Discord (delegated to DiscordAdapter)
    # ------------------------------------------------------------------

    def post_to_discord(
        self,
        content: str,
        webhook_url: str | None = None,
        embed: dict[str, Any] | None = None,
    ) -> bool:
        """POST content (+ optional embed) to a Discord webhook."""
        return self._discord.post(content, webhook_url=webhook_url, embed=embed)

    # ------------------------------------------------------------------
    # dev.to
    # ------------------------------------------------------------------

    def post_to_devto(
        self,
        title: str,
        body_markdown: str,
        tags: list[str],
        published: bool = True,
    ) -> dict[str, Any]:
        """Create a new article on dev.to.

        Returns:
            Dict with 'id', 'url', 'title'; empty dict on failure.
        """
        if not self.devto_api_key:
            logger.error("[dev.to] DEVTO_API_KEY not set")
            return {}

        headers = {"api-key": self.devto_api_key, "Content-Type": "application/json"}
        payload = {"article": {"title": title, "body_markdown": body_markdown,
                               "tags": tags, "published": published}}
        try:
            resp = httpx.post(f"{DEVTO_API_BASE}/articles", json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            logger.info("[dev.to] Article created: %s", data.get("url"))
            return {"id": data.get("id"), "url": data.get("url"), "title": data.get("title")}
        except httpx.HTTPError as exc:
            logger.exception("[dev.to] Failed to post article: %s", exc)
            return {}

    def get_devto_comments(self, article_id: int) -> list[dict[str, Any]]:
        """Fetch all comments for a dev.to article."""
        try:
            resp = httpx.get(f"{DEVTO_API_BASE}/comments",
                             params={"a_id": article_id}, timeout=10)
            resp.raise_for_status()
            return resp.json()  # type: ignore[return-value]
        except httpx.HTTPError as exc:
            logger.exception("[dev.to] Failed to fetch comments %d: %s", article_id, exc)
            return []

    def reply_devto_comment(
        self, article_id: int, parent_id: int, body: str
    ) -> dict[str, Any]:
        """Post a reply to a dev.to comment."""
        if not self.devto_api_key:
            logger.error("[dev.to] DEVTO_API_KEY not set")
            return {}

        headers = {"api-key": self.devto_api_key, "Content-Type": "application/json"}
        payload = {"comment": {"body_markdown": body, "commentable_id": article_id,
                               "commentable_type": "Article", "parent_id": parent_id}}
        try:
            resp = httpx.post(f"{DEVTO_API_BASE}/comments", json=payload,
                              headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()  # type: ignore[return-value]
        except httpx.HTTPError as exc:
            logger.exception("[dev.to] Reply to comment %d failed: %s", parent_id, exc)
            return {}

    # ------------------------------------------------------------------
    # GitHub Discussions (via gh CLI)
    # ------------------------------------------------------------------

    def _gh_graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GitHub GraphQL query via `gh api graphql`."""
        cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
        if variables:
            cmd += ["-F", f"variables={json.dumps(variables)}"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.error("[GH] GraphQL error: %s", result.stderr)
                return {}
            return json.loads(result.stdout)  # type: ignore[return-value]
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as exc:
            logger.exception("[GH] gh CLI error: %s", exc)
            return {}

    def create_gh_discussion(
        self, repo: str, category_id: str, title: str, body: str
    ) -> dict[str, Any]:
        """Create a GitHub Discussion. Returns dict with 'id', 'number', 'url'."""
        owner, name = repo.split("/", 1)
        repo_data = self._gh_graphql(
            'query($o:String!,$n:String!){repository(owner:$o,name:$n){id}}',
            {"o": owner, "n": name},
        )
        repo_id = repo_data.get("data", {}).get("repository", {}).get("id", "")
        if not repo_id:
            logger.error("[GH] Could not resolve repo ID for %s", repo)
            return {}

        mutation = (
            "mutation($rId:ID!,$cId:ID!,$t:String!,$b:String!){"
            "createDiscussion(input:{repositoryId:$rId,categoryId:$cId,title:$t,body:$b})"
            "{discussion{id number url}}}"
        )
        data = self._gh_graphql(mutation, {"rId": repo_id, "cId": category_id, "t": title, "b": body})
        disc = data.get("data", {}).get("createDiscussion", {}).get("discussion", {})
        if disc:
            logger.info("[GH] Discussion created: %s", disc.get("url"))
        return disc

    def get_gh_discussion_comments(self, repo: str, discussion_number: int) -> list[dict[str, Any]]:
        """Fetch comments for a GitHub Discussion."""
        owner, name = repo.split("/", 1)
        query = (
            "query($o:String!,$n:String!,$num:Int!){"
            "repository(owner:$o,name:$n){discussion(number:$num){"
            "comments(first:100){nodes{id body createdAt author{login}}}}}}"
        )
        data = self._gh_graphql(query, {"o": owner, "n": name, "num": discussion_number})
        return (
            data.get("data", {}).get("repository", {})
            .get("discussion", {}).get("comments", {}).get("nodes", [])
        )

    def reply_gh_discussion(self, repo: str, discussion_id: str, body: str) -> dict[str, Any]:
        """Add a comment to a GitHub Discussion."""
        mutation = (
            "mutation($dId:ID!,$b:String!){addDiscussionComment(input:{discussionId:$dId,body:$b})"
            "{comment{id url}}}"
        )
        data = self._gh_graphql(mutation, {"dId": discussion_id, "b": body})
        comment = data.get("data", {}).get("addDiscussionComment", {}).get("comment", {})
        if comment:
            logger.info("[GH] Reply posted in %s: %s", repo, comment.get("url"))
        return comment


__all__ = ["SocialPosterAgent"]
