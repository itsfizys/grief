import asyncio
import base64
import re
from typing import Any, Optional

import aiohttp
from loguru import logger

from base.config import EMOJIS


EMOJI_PATTERN = re.compile(r"^<(a?):(\w+):(\d+)>$")
DISCORD_API = "https://discord.com/api/v10"
DISCORD_CDN = "https://cdn.discordapp.com"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)


def _markup(name: str, emoji_id: str, animated: bool) -> str:
    prefix = "a" if animated else ""
    return f"<{prefix}:{name}:{emoji_id}>"


async def _get_json(
    session: aiohttp.ClientSession, url: str, headers: dict[str, str]
) -> Any:
    async with session.get(url, headers=headers) as response:
        response.raise_for_status()
        payload = await response.json()
    return payload


async def sync_emojis(token: Optional[str]) -> None:
    """Ensure configured custom emojis exist on the bot application."""
    if not token:
        logger.warning("Emoji sync skipped: the bot has no login token.")
        return

    entries = [
        (key, value)
        for key, value in vars(EMOJIS).items()
        if not key.startswith("_") and isinstance(value, str)
    ]
    headers = {"Authorization": f"Bot {token}"}

    async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
        try:
            application = await _get_json(
                session, f"{DISCORD_API}/applications/@me", headers
            )
            application_id = application.get("id") if application else None
            if not application_id:
                logger.warning("Emoji sync skipped: Discord returned no application ID.")
                return

            emoji_response = await _get_json(
                session,
                f"{DISCORD_API}/applications/{application_id}/emojis",
                headers,
            )
            if isinstance(emoji_response, list):
                application_emojis = emoji_response
            elif isinstance(emoji_response, dict):
                application_emojis = emoji_response.get("items", [])
            else:
                logger.warning("Emoji sync skipped: Discord returned an invalid emoji list.")
                return
            if not isinstance(application_emojis, list):
                logger.warning("Emoji sync skipped: Discord returned an invalid emoji list.")
                return
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as error:
            logger.warning("Emoji sync could not load application emojis: {}", error)
            return

        uploaded = 0
        reconciled = 0
        failed = 0
        logger.info(
            "Starting emoji sync for {} configured emojis ({} on the application).",
            len(entries),
            len(application_emojis),
        )

        for key, emoji_string in entries:
            match = EMOJI_PATTERN.fullmatch(emoji_string)
            if not match:
                logger.debug("Skipping {}: it is not a custom emoji string.", key)
                continue

            animated = match.group(1) == "a"
            name = match.group(2)
            emoji_id = match.group(3)
            existing = next(
                (
                    emoji
                    for emoji in application_emojis
                    if str(emoji.get("id")) == emoji_id
                ),
                None,
            )
            if existing is None:
                existing = next(
                    (
                        emoji
                        for emoji in application_emojis
                        if emoji.get("name") == name
                    ),
                    None,
                )

            if existing is not None:
                current_markup = _markup(
                    existing.get("name", name),
                    str(existing.get("id", emoji_id)),
                    bool(existing.get("animated", animated)),
                )
                if current_markup != emoji_string:
                    setattr(EMOJIS, key, current_markup)
                    reconciled += 1
                continue

            extension = "gif" if animated else "webp"
            mime_type = "image/gif" if animated else "image/webp"
            image_url = f"{DISCORD_CDN}/emojis/{emoji_id}.{extension}"
            try:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        failed += 1
                        logger.warning(
                            "Could not download configured emoji {} (HTTP {}).",
                            name,
                            response.status,
                        )
                        continue
                    image_bytes = await response.read()

                image_data = (
                    f"data:{mime_type};base64,"
                    f"{base64.b64encode(image_bytes).decode('ascii')}"
                )
                async with session.post(
                    f"{DISCORD_API}/applications/{application_id}/emojis",
                    json={"name": name, "image": image_data},
                    headers=headers,
                ) as response:
                    response.raise_for_status()
                    created = await response.json()

                if not isinstance(created, dict) or not created.get("id"):
                    failed += 1
                    logger.warning("Discord did not return an ID for emoji {}.", name)
                    continue

                created_name = created.get("name", name)
                created_animated = bool(created.get("animated", animated))
                setattr(
                    EMOJIS,
                    key,
                    _markup(created_name, str(created["id"]), created_animated),
                )
                application_emojis.append(created)
                uploaded += 1
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as error:
                failed += 1
                logger.warning("Could not sync emoji {}: {}", name, error)

        logger.info(
            "Emoji sync complete: {} uploaded, {} configuration values reconciled, "
            "{} failed or unavailable.",
            uploaded,
            reconciled,
            failed,
        )
