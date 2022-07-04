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

import os

from .. import loader, main, utils
import telethon


@loader.tds
class CoreMod(loader.Module):
    """Управление основными настройками бота"""
    strings = {"name": "Настройки",
               "too_many_args": "<b>Слишком много аргументов</b>",
               "blacklisted": "<b>Чат {} занесен в черный список бота.</b>",
               "unblacklisted": "<b>Чат {} больше не в черном списке.</b>",
               "user_blacklisted": "<b>Пользователь {} занесен в черный список бота.</b>",
               "user_unblacklisted": "<b>Пользователь {} убран из черного списка.</b>",
               "what_prefix": "<b>Какой префикс должен быть установлен?</b>",
               "prefix_set": ("<b>Обновлен префикс комманд. Введите</b> <code>{newprefix}setprefix {oldprefix}"
                              "</code> <b>чтобы вернуть его обратно.</b>"),
               "alias_created": "<b>Алиас создан. Быстрый доступ: </b> <code>{}</code>",
               "no_command": "<b>Команда</b> <code>{}</code> <b>не найдена.</b>",
               "alias_args": "<b>Вы должны предоставить команду и алиас к ней.</b>",
               "delalias_args": "<b>Вы должны предоставить нужный алиас.</b>",
               "alias_removed": "<b>Алиас</b> <code>{}</code> <b>удален.",
               "no_alias": "<b>Алиас</b> <code>{}</code> <b>не найден.</b>",
               "no_pack": "<b>Какой пакет перевода хотите добавить?</b>",
               "bad_pack": "<b>Указан неверный пакет перевода</b>",
               "trnsl_saved": "<b>Пакет перевода добавлен</b>",
               "packs_cleared": "<b>Установленные пакеты удалены.</b>",
               "lang_set": "<b>Язык сменен</b>",
               "db_cleared": "<b>База данных очищена</b>"}

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

    async def blacklistcommon(self, message):
        args = utils.get_args(message)
        if len(args) > 2:
            await utils.answer(message, self.strings("too_many_args", message))
            return
        chatid = None
        module = None
        if args:
            try:
                chatid = int(args[0])
            except ValueError:
                module = args[0]
        if len(args) == 2:
            module = args[1]
        if chatid is None:
            chatid = utils.get_chat_id(message)
        module = self.allmodules.get_classname(module)
        return str(chatid) + "." + module if module else chatid

    async def blacklistcmd(self, message):
        """.blacklist [id]
           Черный список бота, где он не может работать"""
        chatid = await self.blacklistcommon(message)
        self._db.set(main.__name__, "blacklist_chats", self._db.get(main.__name__, "blacklist_chats", []) + [chatid])
        await utils.answer(message, self.strings("blacklisted", message).format(chatid))

    async def unblacklistcmd(self, message):
        """.unblacklist [id]
           Удаление из черного списка"""
        chatid = await self.blacklistcommon(message)
        self._db.set(main.__name__, "blacklist_chats",
                     list(set(self._db.get(main.__name__, "blacklist_chats", [])) - set([chatid])))
        await utils.answer(message, self.strings("unblacklisted", message).format(chatid))

    async def getuser(self, message):
        try:
            return int(utils.get_args(message)[0])
        except (ValueError, IndexError):
            reply = await message.get_reply_message()
            if not reply:
                if message.is_private:
                    return message.to_id.user_id
                else:
                    await utils.answer(message, self.strings("who_to_unblacklist", message))
                    return
            else:
                return (await message.get_reply_message()).sender_id

    async def blacklistusercmd(self, message):
        """.blacklistuser [id]
           Запрет пользователю запускать любые команды"""
        user = await self.getuser(message)
        self._db.set(main.__name__, "blacklist_users", self._db.get(main.__name__, "blacklist_users", []) + [user])
        await utils.answer(message, self.strings("user_blacklisted", message).format(user))

    async def unblacklistusercmd(self, message):
        """.unblacklistuser [id]
           Разрешить этому пользователю запускать разрешенные команды"""
        user = await self.getuser(message)
        self._db.set(main.__name__, "blacklist_users",
                     list(set(self._db.get(main.__name__, "blacklist_users", [])) - set([user])))
        await utils.answer(message, self.strings("user_unblacklisted", message).format(user))

    @loader.owner
    async def setprefixcmd(self, message):
        """Устанавливает префикс команды"""
        args = utils.get_args(message)
        if len(args) == 0:
            await utils.answer(message, self.strings("what_prefix", message))
            return
        oldprefix = self._db.get(main.__name__, "command_prefix", ["."])[0]
        self._db.set(main.__name__, "command_prefix", args)
        await utils.answer(message, self.strings("prefix_set", message).format(newprefix=utils.escape_html(args[0]),
                                                                               oldprefix=utils.escape_html(oldprefix)))

    @loader.owner
    async def addaliascmd(self, message):
        """Установка алиаса для команды"""
        args = utils.get_args(message)
        if len(args) != 2:
            await utils.answer(message, self.strings("alias_args", message))
            return
        alias, cmd = args
        ret = self.allmodules.add_alias(alias, cmd)
        if ret:
            self._db.set(__name__, "aliases", {**self._db.get(__name__, "aliases"), alias: cmd})
            await utils.answer(message, self.strings("alias_created", message).format(utils.escape_html(alias)))
        else:
            await utils.answer(message, self.strings("no_command", message).format(utils.escape_html(cmd)))

    @loader.owner
    async def delaliascmd(self, message):
        """Удалить алиас для команды"""
        args = utils.get_args(message)
        if len(args) != 1:
            await utils.answer(message, self.strings("delalias_args", message))
            return
        alias = args[0]
        ret = self.allmodules.remove_alias(alias)
        if ret:
            current = self._db.get(__name__, "aliases")
            del current[alias]
            self._db.set(__name__, "aliases", current)
            await utils.answer(message, self.strings("alias_removed", message).format(utils.escape_html(alias)))
        else:
            await utils.answer(message, self.strings("no_alias", message).format(utils.escape_html(alias)))

    async def addtrnslcmd(self, message):
        """Добавить пакет перевода
           .addtrnsl <pack>
           После использования нужно перезагрузить"""
        args = utils.get_args(message)
        if len(args) != 1:
            await utils.answer(message, self.strings("no_pack", message))
            return
        pack = args[0]
        if await message.client.is_bot():
            if not pack.isalnum():
                await utils.answer(message, self.strings("bad_pack", message))
                return
            if not os.path.isfile(os.path.join("translations", pack + ".json")):
                await utils.answer(message, self.strings("bad_pack", message))
                return
            self._db.setdefault(main.__name__, {}).setdefault("langpacks", []).append(pack)
            self._db.save()
            await utils.answer(message, self.strings("trnsl_saved", message))
        else:
            try:
                pack = int(pack)
            except ValueError:
                pass
            try:
                pack = await self._client.get_entity(pack)
            except ValueError:
                await utils.answer(message, self.strings("bad_pack", message))
                return
            if isinstance(pack, telethon.tl.types.Channel) and not pack.megagroup:
                self._db.setdefault(main.__name__, {}).setdefault("langpacks", []).append(pack.id)
                self._db.save()
                await utils.answer(message, self.strings("trnsl_saved", message))
            else:
                await utils.answer(message, self.strings("bad_pack", message))

    async def cleartrnslcmd(self, message):
        """Удалить все пакеты переводов"""
        self._db.set(main.__name__, "langpacks", [])
        await utils.answer(message, self.strings("packs_cleared", message))

    async def setlangcmd(self, message):
        """Изменить предпочитаемый язык для переводов
           Укажите язык как разделенный пробелами список кодов языка ISO 639-1 в порядке предпочтения (например, fr en)
           Без параметров отключает все переводы
           После использования нужно перезагрузить"""
        langs = utils.get_args(message)
        self._db.set(main.__name__, "language", langs)
        await utils.answer(message, self.strings("lang_set", message))

    @loader.owner
    async def cleardbcmd(self, message):
        """Очищает всю базу данных, эффективно выполняя сброс настроек"""
        self._db.clear()
        await self._db.save()
        await utils.answer(message, self.strings("db_cleared", message))

    async def _client_ready2(self, client, db):
        ret = {}
        for alias, cmd in db.get(__name__, "aliases", {}).items():
            if self.allmodules.add_alias(alias, cmd):
                ret[alias] = cmd
        db.set(__name__, "aliases", ret)
