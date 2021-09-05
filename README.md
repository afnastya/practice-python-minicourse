# BookHelper Telegram bot

<h2>Запуск:</h2> TelegramBot.py - запуск бота (перед этим нужно вставить свои telegram, yandex и google токены (строки 9, 239, 285), изменить yandex_folder на свою (строка 240))

web-scrapping.py - не надо запускать, только если хочется обновить данные с брифли в csv файлах, работать будет долго (5-10 минут)

<h2>Описание:</h2> бот может рандомно подобрать книгу, а также прочитать краткое содержание какой-нибудь книги (отправляет в голосовых сообщениях текст краткого содержания с брифли).
<h3>Для кого было бы полезно:</h3> Тем, кто часто сталкивается с проблемой выбора, что бы почитать следующим, будет полезна первая функция бота (подбор книги).
Вторая функция была бы полезна тем любителям контента брифли (например, школьники, не любящие читать то, что задают на литературе, или те, кто хочет освежить в памяти детали книги, которою читали) , кто легче воспринимает аудио информацию или кто любит слушать что-то в дороге и тд.

<h2>Что было сделано и что использовано:</h2>

 * web-scrapping сервиса 'briefly.ru' с помощью BeautifulSoup. Оттуда были взяты авторы, названия, года выпуска, краткие содержания, тэги, ссылки на краткие содержания и ссылки на полные тексты у всех книг, у которых были краткие содержания. Код скрапинга есть в файле 'web-scrapping.py' и в 'web-scrapping.ipynb' (возможно, в ноутбуке будет легче смотреть, так как делалось всё там, и таблички легче там смотреть, а не в csv). Все соскрапленные данные хранятся в 'books_table.csv' и 'tags_table.csv.csv'.
 * В Телеграм боте есть 2 функции: выбор книги и чтение краткого содержания:
    * выбор книги предлагает выбрать одну из 3 категорий:
        * "нет": выбирается просто рандомная книга с таблицы
        * "по автору": можно вбить что-нибудь из ФИО автора в свободной форме и выберется его рандомная книга
        * "по тэгу": даётся на выбор очень много тэгов с брифли (из файла 'tags_table.csv'). В основном там по культурам (например, 'Аргентинская литература'), есть некоторые с указанием века (например, "Американская литература 19-го века"), ещё есть тэг "Нонфикшн".
    * чтение краткого содержания: отправляются голосовые сообщения, созданные с помощью озвучки краткого содержания с брифли Yandex SpeechKit'ом. Предлагается выбрать одну из 2 категорий запроса:
        * рандомная
        * конкретная: нужно вбить полное точное название книги без учета регистра
* Если как-то неправильно заполнены фио автора при выборе рандомной книги или название книги в озвучке конкретной книги, то предлагается ещё раз попробовать их ввести
* Когда выводится какая-нибудь книга, появляется её обложка, найденная запросом в Google (Google API custom search), также выводятся имеющиеся о ней данные с брифли, кроме краткого содержания.
* Голосовых сообщений иногда несколько, так как Yandex SpeechKit не даёт возможность отправлять запрос с более чем 5000 символами текста, поэтому приходится резать текст на куски и синтезировать озвучку по отдельности. Текст обязательно режется на границе абзацев, чтобы не ломалась интонация и чтобы не было слышно склейки. Голосовые сообщения играются друг за другом, поэтому наличие нескольких сообщений вместо одного пользователю не доставляет никакого дискомфорта.
