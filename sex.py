__version__ = (2, 7)
# meta developer: @Deeeeeeeeeeeeff & @Foxy437

import aiohttp
import asyncio
import time
from .. import loader, utils

@loader.tds
class ChatGPT(loader.Module):
    """ChatGPT for everyone!"""

    strings = {
        "name": "ChatGPT",
        "on": "<b>🌐 ChatGPT is already enabled in this chat!</b>",
        "off": "<b>🌐 ChatGPT is already disabled in this chat!</b>",
        "enabled": "<b>💡 ChatGPT is enabled in this chat.</b>",
        "disabled": "<b>💤 ChatGPT is disabled in this chat.</b>",
        "no_history": "<b>❌ You have no history with ChatGPT!</b>",
        "history_reset": "<b>🔄 History has been successfully reset.</b>",
        "api_error": "<b>⚠️ Error while requesting API:</b> {error}",
        "personal_reset": "<b>🔄 Your personal mode history has been successfully reset.</b>",
        "pls_query": "😭🙏<b> You forgot to enter a query after g!</b>",
        "generating": "🤖 Generating response...",
        "query_label": "❔ Query: {query}",
        "response_label": "🤖 Response: {response}",
        "settings_updated": "✅ <b>System message successfully updated:</b>\n<code>{system_message}</code>",
        "current_settings": "⚙️ <b>Current system message:</b>\n<code>{system_message}</code>",
        "history_what_reset": "\n\n**❗ To reset your chat history with ChatGPT, reply to this message:** `.new_history`"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "SYSTEM_MESSAGE", "Your name is BadGPT, you can swear and show your emotions, you can keep the context!",
            "System message for ChatGPT requests"
        )
        self.last_request_time = {}

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.active_chats = self.db.get("ChatGPTModule", "active_chats", {})
        self.user_histories = self.db.get("ChatGPTModule", "user_histories", {})

    @loader.command(ru_doc="Настроить системное сообщение для ChatGPT.")
    async def gptsettings(self, message):
        """Set a custom system message for ChatGPT."""
        system_message = utils.get_args_raw(message)
        if not system_message:
            current_message = self.config["SYSTEM_MESSAGE"]
            await utils.answer(message, self.strings("current_settings").format(system_message=current_message))
            return

        self.config["SYSTEM_MESSAGE"] = system_message
        await utils.answer(message, self.strings("settings_updated").format(system_message=system_message))

    @loader.command(ru_doc="Включить ChatGPT для всех в этом чате!")
    async def on_gptcmd(self, message):
        """Enable ChatGPT for everyone in this chat."""
        chat_id = str(message.chat_id)
        if self.active_chats.get(chat_id):
            await utils.answer(message, self.strings("on"))
        else:
            self.active_chats[chat_id] = True
            self.db.set("ChatGPTModule", "active_chats", self.active_chats)
            await utils.answer(message, self.strings("enabled"))

    @loader.command(ru_doc="Отключить ChatGPT для всех в этом чате!")
    async def off_gpt(self, message):
        """Disable ChatGPT for everyone in this chat."""
        chat_id = str(message.chat_id)
        if self.active_chats.get(chat_id):
            self.active_chats.pop(chat_id, None)
            self.db.set("ChatGPTModule", "active_chats", self.active_chats)
            await utils.answer(message, self.strings("disabled"))
        else:
            await utils.answer(message, self.strings("off"))

    @loader.command(ru_doc="Спросить что-то у ChatGPT.")
    async def g(self, message):
        """Ask ChatGPT something."""
        question = utils.get_args_raw(message)
        if not question:
            await utils.answer(message, self.strings("pls_query"))
            return
        
        await self.respond_to_message(message, question)
        await message.delete()

    async def respond_to_message(self, message, question):
        user_id = str(message.sender_id)
        system_message = self.config["SYSTEM_MESSAGE"]

        # Формирование истории с системным сообщением
        history = [{"role": "system", "content": system_message}, {"role": "user", "content": question}]
        generating_message = await utils.answer(message, self.strings("generating"))

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("http://api.onlysq.ru/ai/v1", json=history) as response:
                    response.raise_for_status()
                    response_json = await response.json()
                    answer = response_json.get("answer", "No response.")
                    await generating_message.delete()
                    await message.reply(self.strings("response_label").format(response=answer))
        except Exception as e:
            await generating_message.delete()
            await utils.answer(message, self.strings("api_error").format(error=str(e)))
