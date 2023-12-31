import requests
import json
from collections import namedtuple
from typing import Callable, Tuple
import os


class Bot:
    BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
    PARSE_MODES = namedtuple(
        "Parse_Modes", ("HTML", "MD"))(
        "HTML", "MarkdownV2")

    def __init__(self, token: str = BOT_TOKEN) -> None:
        """
        arguments: token - string (required if enviornment variable 'TG_BOT_TOKEN' is not set)
        returns: None
        """
        self.__bot_token = token
        self.__base_url = f"https://api.telegram.org/bot{token}"

    # this function will handle the webhook url setting.
    def set_webhook(self, webhook_url: str) -> dict:
        request_url = self.__base_url + "/setWebhook"
        data = {"url": webhook_url}
        return requests.post(request_url, json=data).json()

    def validate_update(self, update: dict) -> "UpdateChat":
        return UpdateChat(update, self.__bot_token)

    def send_message(
        self,
        chat_id: int,
        text: str,
        message_thread_id: int = None,
        parse_mode: str = "HTML",
        entities: dict = {},
        disable_web_page_preview: bool = False,
        disable_notification: bool = False,
        protect_content: bool = False,
        reply_to_message_id: int = None,
        allow_sending_without_reply: bool = False,
        reply_markup: dict = {},
    ) -> dict:
        """
        Please refer to this link for more information on arguments:\n
        https://core.telegram.org/bots/api#sendmessage\n
        Returns a new object with methods to update message text or delete the sent message.
        """
        url = f"{self.__base_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "parse_mode": parse_mode if parse_mode is not None else self.PARSE_MODES.HTML,
            "text": text,
            "allow_sending_without_reply": True,
            "disable_web_page_preview": disable_web_page_preview,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": json.dumps(reply_markup),
            "disable_notification": disable_notification,
            "protect_content": protect_content,
            "message_thread_id": message_thread_id,
            "entities": json.dumps(entities),
        }
        return SentChat(self.__bot_token, requests.post(url, json=data).json())

    def edit_message_text(self, chat_id: int, message_id: int, text: str):
        url = self.__base_url + "/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
        }
        return requests.post(url, json=payload).json()

    def delete_message(self, chat_id: int, message_id: int):
        url = self.__base_url + "/deleteMessage"
        payload = {"chat_id": chat_id, "message_id": message_id}
        return requests.post(url, json=payload).json()

    @staticmethod
    def callback_button(text: str, callback_data: str = None) -> dict:
        return {"text": text, "callback_data": callback_data}

    @staticmethod
    def url_button(text: str, url: str = None) -> dict:
        return {"text": text, "url": url}


class UpdateChat(Bot):
    def __init__(self, update: dict, token: str) -> None:
        """
        Arguments:
            update - dict,
            token - str
        Returns:
            None
        """
        super().__init__(token)
        update_tuple = tuple(update.items())
        self.update_type = update_tuple[1][0]
        self.from_id = update_tuple[1][1].get("from", {}).get("id")
        self.text = update_tuple[1][1].get("text")
        self.__message_type = (
            update_tuple[1][1].get("entities", [{}])[0].get("type", "text")
        )
        self.__entities = update_tuple[1][1].get("entities", [{}])
        if self.update_type == "callback_query":
            self.chat_id: int = update_tuple[1][1]["message"].get(
                "chat", {}).get("id")
            self.message_id: int = update_tuple[1][1]["message"].get(
                "message_id")
        else:
            self.chat_id = update_tuple[1][1].get("chat", {}).get("id")
            self.message_id = update_tuple[1][1].get("message_id")

    def send_message(self, text: str) -> dict:
        return super().send_message(self.chat_id, text)

    def send_inline_keyboard(self, text: str, reply_markup={}) -> dict:
        return super().send_message(self.chat_id, text, reply_markup=reply_markup)

    def reply_message(self, text: str) -> dict:
        return super().send_message(
            self.from_id, text, reply_to_message_id=self.message_id
        )

    def command_handler(self, command: str, handler: Callable):
        """
        I'll work on this later, It will add a command handler to the class.
        """
        pass

    def get_command(
        self, argument: bool = False, only_start: bool = True
    ) -> None | str | Tuple[str | str]:
        """
        I'll work on this later, It'll return either `None` or `str` or `tuple`.\n
        Returns:
            `None` - If the message does not contain a command.\n
            `str` - If the message contains a command and the argument parameter is set to `False`.\n
            `tuple` - If the message contains a command and the argument parameter is set to `True`.\n
        Sample returns:
            `None`: 'Just a simple text message'\n
            `'bot_command'`: '/bot_command'\n
            `('bot_command', 'argument')`: '/bot_command argument'
        """
        if self.message_type != "bot_command":
            return None
        start = self.__entities[0]["offset"] + 1
        end = start + self.__entities[0]["length"] - 1
        if only_start:
            if start == 1:
                if not argument:
                    return self.text[start:end]
                else:
                    return (self.text[start:end], self.text[end:].strip())
            else:
                return None

        return self.text[start:end]

    @property
    def message_type(self) -> str:
        """
        Returns the message type from command or callback (text otherwise)
        """
        return self.__message_type


class SentChat(Bot):
    def __init__(self, token: str, sent_msg: dict) -> None:
        super().__init__(token)
        update_tuple = tuple(sent_msg.items())
        self.update_type = update_tuple[1][0]
        self.from_id = update_tuple[1][1].get("from", {}).get("id")
        self.chat_id = update_tuple[1][1].get("chat", {}).get("id")
        self.message_id = update_tuple[1][1].get("message_id")
        self.sent_text = update_tuple[1][1].get("message_id")

    def edit_message_text(self, text: str):
        """
        Edit the sent message.
        Usage:
            message = bot.send_message(chat_id, text)
            message.edit_message_text(new_text)
        """
        return super().edit_message_text(self.chat_id, self.message_id, text)

    def delete_message(self):
        """
        Delete the sent message.
        Usage:
            message = bot.send_message(chat_id, text)
            message.delete_message()
        """
        return super().delete_message(self.chat_id, self.message_id)
