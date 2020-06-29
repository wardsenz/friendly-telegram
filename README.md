-----
- [Source code on Gitlab](https://gitlab.com/friendly-telegram)
- [Author](https://gitlab.com/hackintosh5)
-----


## Инфо
1. Это всё делалось для себя.
2. Мод предназначен для тех, кто уже пользовался юзерботом.
3. Установщик PowerShell сломан. С винды не поставите никак. Ссылка на оригинал выше.
### Изменено/Дополнено:
- Кастомный звук Выключения/Включения (Windows 7).
- 29.06 - фикс ошибки SSL, которая начала появляться у некоторых пользователей с Termux.
- Русифицирован процесс получения кода по Web.
- Сразу ставит регион EU (Европа, пинг 30-50мс) в Heroku прямо во время установки.
- Ставит пакет neofetch по умолчанию. В Heroku нет доступа к пакетному менеджеру apt.
- Обновляется/устанавливается из этого репозитория.
- Возможно ещё будут и другие изменения.

### Установка:
- Только Termux: `(. <($(which curl>/dev/null&&echo curl -Ls||echo wget -qO-) https://kutt.it/ftgi) --no-web)`
Вводите APP_ID, API_HASH, номер телефона и код. Дождитесь запуска, когда напишет "Started for <id>".
Последующие запуски - `cd $HOME/friendly-telegram && python3 -m friendly-telegram`

- На Heroku через Termux: `(. <($(which curl>/dev/null&&echo curl -Ls||echo wget -qO-) https://kutt.it/ftgi) --heroku --no-web)`.
Начальный запуск идентичный с примером выше, только в этом случае Вам потребуется ещё и API Key (ключ) с сайта Heroku.


- Telegram App_ID и Api_hash - [Тут](https://my.telegram.org/apps)
- Heroku Api Key - [Тут](https://dashboard.heroku.com)

Поддержка мода & ЧаВо - https://t.me/wardsenz
### Важно
Если раньше не встречали/пользовались этим ботом, то пожалуйста, прочитайте оригинальную документацию [здесь](https://friendly-telegram.gitlab.io).
