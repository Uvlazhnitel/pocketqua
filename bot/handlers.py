from __future__ import annotations

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from bot.client import BackendClient
from bot.formatters import (
    format_action_explain,
    format_actions,
    format_portfolio,
    format_staking,
)


def get_client(context: ContextTypes.DEFAULT_TYPE) -> BackendClient:
    client = context.application.bot_data.get("backend_client")
    if client is None:
        raise RuntimeError("backend client is not configured")
    return client


async def register_chat_if_needed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    timezone = context.application.bot_data.get("bot_timezone", "UTC")
    client = get_client(context)
    try:
        await client.register_chat(chat_id=chat.id, timezone=str(timezone))
    except httpx.HTTPError:
        # Non-fatal for command response
        return


async def cmd_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await register_chat_if_needed(update, context)
    client = get_client(context)
    try:
        summary = await client.portfolio_summary()
        risk = await client.risk_summary()
        text = format_portfolio(summary, risk)
    except httpx.HTTPError as exc:
        text = f"Backend error: {exc}"
    await update.effective_message.reply_text(text)


async def cmd_actions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await register_chat_if_needed(update, context)
    client = get_client(context)
    try:
        actions = await client.actions(status="new", limit=5)
        text = format_actions(actions)
    except httpx.HTTPError as exc:
        text = f"Backend error: {exc}"
    await update.effective_message.reply_text(text)


async def cmd_staking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await register_chat_if_needed(update, context)
    client = get_client(context)
    try:
        rows = await client.staking_positions(limit=5)
        text = format_staking(rows)
    except httpx.HTTPError as exc:
        text = f"Backend error: {exc}"
    await update.effective_message.reply_text(text)


async def cmd_explain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await register_chat_if_needed(update, context)
    client = get_client(context)

    if not context.args:
        await update.effective_message.reply_text("Usage: /explain <id>")
        return

    try:
        action_id = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("Action id must be an integer")
        return

    try:
        action = await client.action_by_id(action_id)
        text = format_action_explain(action)
    except httpx.HTTPStatusError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            text = "Action not found"
        else:
            text = f"Backend error: {exc}"
    except httpx.HTTPError as exc:
        text = f"Backend error: {exc}"

    await update.effective_message.reply_text(text)
