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
import asyncio

import telethon

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class NoCollisionsMod(loader.Module):
    """Убеждается, что одновременно работает только 1 юзербот"""
    strings = {"name": "Анти-столкновения ботов",
               "killed": "<b>Убивает все другие юзерботы</b>"}

    @loader.owner
    async def cleanbotscmd(self, message):
        """Убивает всех юзоботов, кроме 1, выбранного в соответствии с самым быстрым (приблизительно)"""
        try:
            await message.edit("<code>DEADBEEF</code>")
            await asyncio.sleep(5)
            await utils.answer(message, self.strings("killed", message))
        except telethon.errors.rpcerrorlist.MessageNotModifiedError:
            [handler] = logging.getLogger().handlers
            handler.setLevel(logging.CRITICAL)
            for client in self.allclients:
                # Terminate main loop of all running clients
                # Won't work if not all clients are ready
                if client is not message.client:
                    await client.disconnect()
            await message.client.disconnect()
