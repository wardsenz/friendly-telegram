-----
- [Source code on Gitlab](https://gitlab.com/friendly-telegram)
- [Author](https://gitlab.com/hackintosh5)
-----

## Установка:

* ### Termux


	```sh
	(. <($(which curl>/dev/null&&echo curl -Ls||echo wget -qO-) https://kutt.it/ftgimod) --no-web)
	```


	Введите APP_ID, API_HASH, номер телефона и код. Дождитесь запуска, когда напишет "Started for <id>".
	Последующие запуски -
	
	```sh
	cd $HOME/friendly-telegram && python3 -m friendly-telegram
	```

* ### На Heroku через Termux

	```sh
	(. <($(which curl>/dev/null&&echo curl -Ls||echo wget -qO-) https://kutt.it/ftgimod) --heroku --no-web)
	```

	Первый запуск идентичный с примером выше, только в этом случае Вам потребуется ещё и API Key (ключ) с сайта Heroku.


	- Telegram App_ID и Api_hash - [Тут](https://my.telegram.org/apps)
	- Heroku Api Key - [Тут](https://dashboard.heroku.com)


* ### Alpine Linux (iPhone iSh)
	1. Обновляем список пакетов и сами пакеты.
                Upd. 25.10: Если появляется ошибка о том что команда apk не найдена, то установите его [здесь](https://github.com/ish-app/ish/wiki/Installing-apk-on-the-App-Store-Version)
		- $`apk update && apk upgrade`
		![Обновление](src/apk_update.jpg)
	2. Скачиваем необходимые пакеты bash.
		- $`apk add bash bash-completion sudo nano`
		![Установка bash](src/apk_bash.jpg)
	3. Используя nano (или любой другой редактор) открываем конфигурационный файл passwd в папке /etc.
		- $`nano /etc/passwd`
		![Файл passwd](src/nano_passwd.jpg)
		- Видим первую строку с нашем именем пользователя и путь к shell по умолчанию. В моем случае это `root`, потому что в системе нет других пользователей - 
		- `root:x:0:0:root:/root:/bin/ash`.
		![Файл passwd](src/nano_passwd1.jpg)
		- Заменяем `ash` (иногда может быть просто`sh`) => `bash`. Получится как-то так:
		- `root:x:0:0:root:/root:/bin/bash`
		![Файл passwd](src/nano_passwd2.jpg)
		- Сохраняем и идём дальше.
		- (! Не нужно обращаться к автору/чат поддержки с вопросами по типу _"Как редактировать?"_, _"Как сделать *что-то*_" и особенно с _"Что дальше?"_. В интернете сотни гайдов на эти темы. Пишите только в случае ошибки в самом скрипте или гайде.)
	4. Редактируем теперь /etc/profile и добавим переменную SHELL ниже остальных переменных.
		- $`nano /etc/profile` - добавим в список экспортов следующее: `export SHELL=/bin/bash`
		![Файл profile](src/nano_profile.jpg)
	5. Закрываем консоль командой **exit** и открываем, чтобы изменения уж точно сработали.
		Проверим shell, в котором мы находимся:
		- `echo "$OSTYPE"`.
		![Успех](src/echo_ostype.jpg)
		- Получили **linux-musl**? Успех. Идём дальше.
		А если пустота - значит где-то и что-то сделали не так. Повторите шаги 3-4.

	6. Запуск
		
		```sh
		 git clone https://github.com/wardsenz/friendly-telegram
		 cd friendly-telegram
		 bash install.sh --heroku --no-web
		```
		Локальный сервер работать не будет, ставим только на Heroku.
		Выполняем команду и ждём, ждём, и снова ждём. 
	7. И у нас хорошие новости :)
		![Успешная установка и запуск интерфейса настроек](src/successfully.jpg)
		![Конец](src/successfully1.jpg)

	Вводим API_HASH, API_ID и Heroku API_KEY - логинимся.
	И поздравляю, мы победили Купертино.
	Проверяем `.ping` и вступаем в чат поддержки.


### Возможные ошибки

* #### **No module named requests**
     Попробуйте вручную установить зависимости, т.к. инсталлер мог попросту пропустить их:
    ```sh
      cd && cd friendly-telegram
      pip3 install -r requirements.txt
    ```
* #### **The SSL module is not available**
    Отсутствует или не обновлен пакет openssl
    ```sh
      apt update
      apt install --only-upgrade openssl
    ```
* #### **No module named friendly-telegram.__main__**
    Запускать надо модуль, а не папку с ботом
    ```sh
      cd && cd friendly-telegram
      python3 -m friendly-telegram <аргументы>
    ```
* #### **/dev/fd/63: No such file or directory**
    Чаще появляется на Alpine iSh iOS. Причины:
    - Не установлен/добавлен в систему bash - шаги 3-4 в гайде выше.
    - Попытка установки через авто-установщик - про установку с iSh написано в 6 пункте.
    
Список будет дополняться.
    


### Важно
- Поддержка мода & ЧаВо - https://t.me/friendly_telegram
- Если раньше не встречались/пользовались этим ботом, то пожалуйста, прочитайте оригинальную документацию [здесь](https://friendly-telegram.gitlab.io).
