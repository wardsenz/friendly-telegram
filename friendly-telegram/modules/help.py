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
import inspect

from telethon.tl.functions.channels import JoinChannelRequest

from .. import loader, utils, main, security

logger = logging.getLogger(__name__)


@loader.tds
class HelpMod(loader.Module):
    """Предоставляет это справочное сообщение"""
    strings = {"name": "Помощь",
               "bad_module": "<b>Указано неверное имя модуля</b>",
               "single_mod_header": ("<b>Помощь для</b> <u>{}</u>:\nОбратите внимание, что моноширинный текст - это команды "
                                     "и они могут быть запущены с <code>{}&lt;command&gt;</code>"),
               "single_cmd": "\n• <code><u>{}</u></code>\n",
               "undoc_cmd": "Для этой команды нет документации",
               "all_header": ("<b>Помощь для</b> <a href='https://t.me/friendlytgbot'>Friendly-Telegram</a> <a href='https://t.me/wardsenz'>Mod/a>\n"
                              "Для получения дополнительной информации о том, как использовать команду, введите <code>{}help &lt;имя модуля&gt;</code>\n\n"
                              "<b>Доступные модули:</b>"),
               "mod_tmpl": "\n• <b>{}</b>",
               "first_cmd_tmpl": ": <code>{}",
               "cmd_tmpl": ", {}",
               "footer": ("\n\nВы можете <b>узнать</b> о большинстве команд "
                          "<a href='https://ftg-ru.ga'>тут</a>"),
               "joined": "<b>Присоединился к</b> <a href='https://t.me/wardsenz'>каналу поддержки</a>",
               "join": "<b>Присоединяйся к</b> <a href='https://t.me/friendlytgbot'>каналу поддержки</a>"}

    @loader.unrestricted
    async def helpcmd(self, message):
        """.help [модуль]"""
        args = utils.get_args_raw(message)
        if args:
            module = None
            for mod in self.allmodules.modules:
                if mod.strings("name", message).lower() == args.lower():
                    module = mod
            if module is None:
                await utils.answer(message, self.strings("bad_module", message))
                return
            # Translate the format specification and the module separately
            try:
                name = module.strings("name", message)
            except KeyError:
                name = getattr(module, "name", "ERROR")
            reply = self.strings("single_mod_header", message).format(utils.escape_html(name),
                                                                      utils.escape_html((self.db.get(main.__name__,
                                                                                                     "command_prefix",
                                                                                                     False) or ".")[0]))
            if module.__doc__:
                reply += "\n" + "\n".join("  " + t for t in utils.escape_html(inspect.getdoc(module)).split("\n"))
            else:
                logger.warning("В модуле %s отсутствует строка документации!", module)
            commands = {name: func for name, func in module.commands.items()
                        if await self.allmodules.check_security(message, func)}
            for name, fun in commands.items():
                reply += self.strings("single_cmd", message).format(name)
                if fun.__doc__:
                    reply += utils.escape_html("\n".join("  " + t for t in inspect.getdoc(fun).split("\n")))
                else:
                    reply += self.strings("undoc_cmd", message)
        else:
            reply = self.strings("all_header", message).format(utils.escape_html((self.db.get(main.__name__,
                                                                                              "command_prefix",
                                                                                              False) or ".")[0]))
            for mod in self.allmodules.modules:
                try:
                    name = mod.strings("name", message)
                except KeyError:
                    name = getattr(mod, "name", "ERROR")
                reply += self.strings("mod_tmpl", message).format(name)
                first = True
                commands = [name for name, func in mod.commands.items()
                            if await self.allmodules.check_security(message, func)]
                for cmd in commands:
                    if first:
                        reply += self.strings("first_cmd_tmpl", message).format(cmd)
                        first = False
                    else:
                        reply += self.strings("cmd_tmpl", message).format(cmd)
                reply += "</code>"
        reply += self.strings("footer", message)
        await utils.answer(message, reply)

    @loader.unrestricted
    async def supportcmd(self, message):
        """Присоединяется в чат поддержки"""
        if not self.is_bot and await self.allmodules.check_security(message, security.OWNER | security.SUDO):
            await self.client(JoinChannelRequest("https://t.me/wardsenz"))
            await utils.answer(message, self.strings("joined", message))
        else:
            await utils.answer(message, self.strings("join", message))

    async def client_ready(self, client, db):
        self.client = client
        self.is_bot = await client.is_bot()
        self.db = db
