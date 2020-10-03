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
import time
from datetime import datetime
import asyncio
from io import BytesIO

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.test(args=None)
async def dumptest(conv):
    m = await conv.send_message("test")
    await conv.send_message(".dump", reply_to=m)
    r = await conv.get_response()
    assert r.message.startswith("Message(") and "test" in r.message, r


@loader.test(args=("0", "FORCE_INSECURE"))
async def logstest(conv):
    r = await conv.get_response()
    assert r.message == "Загрузка медиа...", r
    r2 = await conv.get_response()
    assert r2.document, r2


@loader.tds
class TestMod(loader.Module):
    """Тестирование бота"""
    strings = {"name": "Тестер",
               "pong": "<code>Понг: {}ms</code>",
               "bad_loglevel": ("<b>Неверный лог-уровень. Пожалуйста, обратитесь к </b>"
                                "<a href='https://docs.python.org/3/library/logging.html#logging-levels'>"
                                "документации</a><b>.</b>"),
               "set_loglevel": "<b>Пожалуйста, укажите уровень в виде целого числа или строки</b>",
               "uploading_logs": "<b>Загрузка логов...</b>",
               "no_logs": "<b>У вас нет логов на уровне {}.</b>",
               "logs_filename": "ftg-logs.txt",
               "logs_caption": "Friendly-telegram логи с уровнем {}",
               "logs_unsafe": ("<b>ПРЕДУПРЕЖДЕНИЕ: Выполнение этой команды может раскрыть личную или опасную информацию! "
                               "Вы можете написать</b> <code>{}</code> <b>в конце, если понимаете, что делаете!</b>"),
               "logs_force": "FORCE_INSECURE",
               "suspend_invalid_time": "<b>Неверное время заморозки</b>"}

    @loader.test(resp="Pong")
    @loader.unrestricted
    async def pingcmd(self, message):
        """Измеряет время неообходимое для отправки сообщения"""
        start = datetime.now()
        msg = await utils.answer(message, "Измеряю...")
        end = datetime.now()
        ms = (end - start).microseconds / 1000
        await asyncio.sleep(0.2)
        await msg[0].edit(self.strings("pong", message).format(ms))

    @loader.test(func=dumptest)
    async def dumpcmd(self, message):
        """Используйте в ответ, чтобы получить дамп сообщения"""
        if not message.is_reply:
            return
        await utils.answer(message, "<code>"
                           + utils.escape_html((await message.get_reply_message()).stringify()) + "</code>")

    @loader.test(func=logstest)
    async def logscmd(self, message):
        """.logs <уровень>
           Дампит логи. Уровни логов ниже WARNING могут содержать личную информацию."""
        args = utils.get_args(message)
        if not len(args) == 1 and not len(args) == 2:
            await utils.answer(message, self.strings("set_loglevel", message))
            return
        try:
            lvl = int(args[0])
        except ValueError:
            # It's not an int. Maybe it's a loglevel
            lvl = getattr(logging, args[0].upper(), None)
        if not isinstance(lvl, int):
            await utils.answer(message, self.strings("bad_loglevel", message))
            return
        if not (lvl >= logging.WARNING or (len(args) == 2 and args[1] == self.strings("logs_force", message))):
            await utils.answer(message,
                               self.strings("logs_unsafe", message).format(utils.escape_html(self.strings("logs_force",
                                                                                                          message))))
            return
        [handler] = logging.getLogger().handlers
        logs = ("\n".join(handler.dumps(lvl))).encode("utf-16")
        if not len(logs) > 0:
            await utils.answer(message, self.strings("no_logs", message).format(lvl))
            return
        logs = BytesIO(logs)
        logs.name = self.strings("logs_filename", message)
        await utils.answer(message, logs, caption=self.strings("logs_caption", message).format(lvl))

    @loader.owner
    async def suspendcmd(self, message):
        """.suspend <время>
           Приостанавливает бота на N секунд"""
        # Blocks asyncio event loop, preventing ANYTHING happening (except multithread ops,
        # but they will be blocked on return).
        try:
            time.sleep(int(utils.get_args_raw(message)))
        except ValueError:
            await utils.answer(message, self.strings("suspend_invalid_time", message))

    async def client_ready(self, client, db):
        self.client = client
