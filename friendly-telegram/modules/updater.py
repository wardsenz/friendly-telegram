#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import os
import sys
import atexit
import functools
import random
import subprocess
import asyncio
from base64 import b64decode
import io
import uuid

import git
from git import Repo

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class UpdaterMod(loader.Module):
    """Обновляет самого себя"""
    strings = {"name": "Обновления",
               "source": "<b>Исходный код доступен</b> <a href='{}'>здесь</a>",
               "restarting_caption": "<b>Перезапуск ...</b>",
               "downloading": "<b>Загрузка обновлений ...</b>",
               "downloaded": ("<b>Загружен успешно.\nПожалуйста введите</b> "
                              "<code>.restart</code> <b>чтобы перезапустить бота.</b>"),
               "already_updated": "<b>Уже обновлён!</b>",
               "installing": "<b>Установка обновлений ...</b>",
               "success": "<b>Перезагрузка прошла успешно! </b>",
               "success_meme": "<b>Перезагрузка успешно провалилась‽</b>",
               "heroku_warning": ("Ключ API Heroku не был установлен. Обновление прошло успешно, но обновления будут "
                                  "сбрасываться каждый раз, когда бот перезапускается."),
               "origin_cfg_doc": "URL источника Git, для которого нужно обновить",
               "audio_cfg_doc": "Должны ли звуки Windows 7 воспроизводиться при перезагрузке"}

    def __init__(self):
        self.config = loader.ModuleConfig("GIT_ORIGIN_URL",
                                          "https://github.com/wardsenz/friendly-telegram",
                                          lambda m: self.strings("origin_cfg_doc", m),
                                          "AUDIO", True, lambda m: self.strings("audio_cfg_doc", m))

    @loader.owner
    async def restartcmd(self, message):
        """Перезапускает юзербот"""
        if self.config["AUDIO"]:
            msg = (await utils.answer(message, SHUTDOWN, voice_note=True,
                                      caption=self.strings("restarting_caption", message)))[0]
        else:
            msg = (await utils.answer(message, self.strings("restarting_caption", message)))[0]
        await self.restart_common(msg)

    async def prerestart_common(self, message):
        logger.debug("Self-update. " + sys.executable + " -m " + utils.get_base_dir())
        check = str(uuid.uuid4())
        await self._db.set(__name__, "selfupdatecheck", check)
        await asyncio.sleep(3)
        if self._db.get(__name__, "selfupdatecheck", "") != check:
            raise ValueError("An update is already in progress!")
        self._db.set(__name__, "selfupdatechat", utils.get_chat_id(message))
        await self._db.set(__name__, "selfupdatemsg", message.id)

    async def restart_common(self, message):
        await self.prerestart_common(message)
        atexit.register(functools.partial(restart, *sys.argv[1:]))
        [handler] = logging.getLogger().handlers
        handler.setLevel(logging.CRITICAL)
        for client in self.allclients:
            # Terminate main loop of all running clients
            # Won't work if not all clients are ready
            if client is not message.client:
                await client.disconnect()
        await message.client.disconnect()

    @loader.owner
    async def downloadcmd(self, message):
        """Загружает обновления юзербота"""
        message = await utils.answer(message, self.strings("downloading", message))
        await self.download_common()
        await utils.answer(message, self.strings("downloaded", message))

    async def download_common(self):
        try:
            repo = Repo(os.path.dirname(utils.get_base_dir()))
            origin = repo.remote("origin")
            r = origin.pull()
            new_commit = repo.head.commit
            for info in r:
                if info.old_commit:
                    for d in new_commit.diff(info.old_commit):
                        if d.b_path == "requirements.txt":
                            return True
            return False
        except git.exc.InvalidGitRepositoryError:
            repo = Repo.init(os.path.dirname(utils.get_base_dir()))
            origin = repo.create_remote("origin", self.config["GIT_ORIGIN_URL"])
            origin.fetch()
            repo.create_head("master", origin.refs.master)
            repo.heads.master.set_tracking_branch(origin.refs.master)
            repo.heads.master.checkout(True)
            return False  # Heroku never needs to install dependencies because we redeploy

    def req_common(self):
        # Now we have downloaded new code, install requirements
        logger.debug("Установка новых зависимостей...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r",
                            os.path.join(os.path.dirname(utils.get_base_dir()), "requirements.txt"), "--user"])
        except subprocess.CalledProcessError:
            logger.exception("Req install failed")

    @loader.owner
    async def updatecmd(self, message):
        """Обновляет юзербот"""
        # We don't really care about asyncio at this point, as we are shutting down
        msgs = await utils.answer(message, self.strings("downloading", message))
        req_update = await self.download_common()
        if self.config["AUDIO"]:
            message = await message.client.send_file(message.chat_id, SHUTDOWN,
                                                     caption=self.strings("installing", message), voice_note=True)
            await asyncio.gather(*[msg.delete() for msg in msgs])
        else:
            message = (await utils.answer(message, self.strings("installing", message)))[0]
        heroku_key = os.environ.get("heroku_api_token")
        if heroku_key:
            from .. import heroku
            await self.prerestart_common(message)
            heroku.publish(self.allclients, heroku_key)
            # If we pushed, this won't return. If the push failed, we will get thrown at.
            # So this only happens when remote is already up to date (remote is heroku, where we are running)
            self._db.set(__name__, "selfupdatechat", None)
            self._db.set(__name__, "selfupdatemsg", None)
            if self.config["AUDIO"]:
                await message.client.send_file(message.chat_id, STARTUP, voice_note=True,
                                               caption=self.strings("already_updated", message))
                await message.delete()
            else:
                await utils.answer(message, self.strings("already_updated", message))
        else:
            if req_update:
                self.req_common()
            await self.restart_common(message)

    @loader.unrestricted
    async def sourcecmd(self, message):
        """Ссылки на исходный код этого проекта"""
        await utils.answer(message, self.strings("source", message).format(self.config["GIT_ORIGIN_URL"]))

    async def client_ready(self, client, db):
        self._db = db
        self._me = await client.get_me()
        if db.get(__name__, "selfupdatechat") is not None and db.get(__name__, "selfupdatemsg") is not None:
            await self.update_complete(client)
        self._db.set(__name__, "selfupdatechat", None)
        self._db.set(__name__, "selfupdatemsg", None)

    async def update_complete(self, client):
        logger.debug("Self update successful! Edit message")
        heroku_key = os.environ.get("heroku_api_token")
        herokufail = ("DYNO" in os.environ) and (heroku_key is None)
        if herokufail:
            logger.warning("heroku token not set")
            msg = self.strings("heroku_warning")
        else:
            logger.debug("Self update successful! Edit message")
            msg = self.strings("success") if random.randint(0, 10) != 0 else self.strings["success_meme"]
        if self.config["AUDIO"]:
            await client.send_file(self._db.get(__name__, "selfupdatechat"), STARTUP, caption=msg, voice_note=True)
            await client.delete_messages(self._db.get(__name__, "selfupdatechat"),
                                         [self._db.get(__name__, "selfupdatemsg")])
        else:
            await client.edit_message(self._db.get(__name__, "selfupdatechat"),
                                      self._db.get(__name__, "selfupdatemsg"), msg)


def restart(*argv):
    os.execl(sys.executable, sys.executable, "-m", os.path.relpath(utils.get_base_dir()), *argv)


###################################################################################
# Blobs (mp3 files from the Internet Archive, Windows XP shutdown/startup sounds) #
###################################################################################
from requests import get
on = get("https://raw.githubusercontent.com/wardsenz/friendly-telegram/master/src/start.mp3").content
off = get("https://raw.githubusercontent.com/wardsenz/friendly-telegram/master/src/turnoff.mp3").content
SHUTDOWN = io.BytesIO(off)
SHUTDOWN.name = "voice.mp3"
STARTUP = io.BytesIO(on)
STARTUP.name = "voice.mp3"