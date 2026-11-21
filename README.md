# SAFI DOWNLOADER BOT

Telegram-боти касбӣ барои гирифтани **медиаи оммавӣ ва дастраси Instagram** (Reels, видео, акс, carousel) ва фиристодани он ҳамчун файл дар Telegram.

Бот медиаи хусусиро намегирад ва аз муҳофизати аккаунтҳо намегузарад.

## Имкониятҳо

- Боргирии Instagram Reels, видео, акс ва carousel
- Забонҳо: тоҷикӣ ва русӣ
- Профил, омор, кӯмак
- Admin Panel: dashboard, users, analytics, broadcast, block, logs, settings
- База: SQLite дар компютер, PostgreSQL (Neon) вақте ки `DATABASE_URL` гузошта шавад
- Rate-limit ва тозакунии файлҳои муваққатӣ

## Талабот

- Windows / Linux / macOS
- Python **3.11+**
- [FFmpeg](https://ffmpeg.org/) (барои видео тавсия мешавад)
- Токени бот аз [@BotFather](https://t.me/BotFather)
- Telegram ID-и шумо (масалан аз [@userinfobot](https://t.me/userinfobot))

## Насб дар Windows (VS Code)

### 1. Python

1. Аз [python.org](https://www.python.org/downloads/) Python 3.11 ё навтар насб кунед.
2. Ҳангоми насб **Add python.exe to PATH**-ро фаъол кунед.
3. VS Code-ро кушоед: **File → Open Folder** → папкаи `SAFI DOWNLOADER`.

### 2. FFmpeg

Дар PowerShell:

```powershell
winget install Gyan.FFmpeg
```

Баъд терминалро пӯшида аз нав кушоед ва санҷед:

```powershell
ffmpeg -version
```

### 3. Муҳити виртуалӣ ва китобхонаҳо

Дар терминали VS Code (`Ctrl + `` `):

```powershell
cd "C:\Users\safi\Desktop\SAFI DOWNLOADER"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Агар активизатсия манъ бошад:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 4. Гирифтани BOT_TOKEN аз BotFather

1. Дар Telegram [@BotFather](https://t.me/BotFather)-ро кушоед.
2. `/newbot` фиристед.
3. Ном: `SAFI DOWNLOADER`
4. Username: масалан `SafiDownloaderBot` (бояд бо `bot` тамом шавад).
5. Токени дарозе мисли `123456789:AAH...`-ро нусха бардоред.
6. Ихтиёрӣ: `/setuserpic`, `/setdescription`, `/setabouttext`.

### 5. Гирифтани ADMIN_ID

1. [@userinfobot](https://t.me/userinfobot)-ро кушоед.
2. `/start` пахш кунед.
3. Рақами **Id**-ро нусха бардоред. Ҳамин рақам `ADMIN_ID` аст.

### 6. Танзими `.env`

Файли `.env`-ро дар решаи лоиҳа кушоед ва пур кунед:

```env
BOT_TOKEN=123456789:AAH_your_token_here
ADMIN_ID=123456789
INSTAGRAM_COOKIES=
RATE_LIMIT_PER_MINUTE=5
MAX_FILE_SIZE_MB=49
CONCURRENT_DOWNLOADS=3
```

- `BOT_TOKEN` ва `ADMIN_ID`-ро ҳеҷ гоҳ ба касе надиҳед.
- Якчанд админ: `ADMIN_ID=111,222`

### 7. Санҷиши автоматӣ

```powershell
python -m pytest -q
```

### 8. Оғози бот

```powershell
python main.py
```

Агар ҳама чиз дуруст бошад, дар терминал мебинед:

```text
SAFI DOWNLOADER v1.0.0 started
```

Сипас дар Telegram боти худро кушоед ва `/start` пахш кунед.

Барои ист: дар терминал `Ctrl + C`.

## Admin Panel

Дар чат бо бот:

- `/admin` ё тугмаи **🛠 Admin** (танҳо барои `ADMIN_ID`)

Он ҷо dashboard, корбарон, омор, рассылка, блок, логҳо ва танзимот ҳастанд. Ҳама рақамҳо аз SQLite меоянд, на аз рақамҳои сохтагӣ.

## Instagram ва yt-dlp

Бот барои медиаи **оммавӣ** `yt-dlp` истифода мебарад. Instagram гоҳо дархости анонимиро мебандад.

Агар боргирии постҳои оммавӣ кор накунад, метавонед `cookies.txt`-и **аккаунти худатон**-ро гузоред (барои дастрасии оммавӣ, на барои аккаунтҳои хусусӣ):

1. Дар браузер ба Instagram ворид шавед.
2. Бо васеъшавии Netscape cookies файли `cookies.txt` созед.
3. Роҳро дар `.env` гузоред:

```env
INSTAGRAM_COOKIES=C:\Users\safi\Desktop\SAFI DOWNLOADER\cookies.txt
```

Агар пост хусусӣ бошад, бот кӯшиши гузаштан намекунад ва хатои фаҳмо нишон медиҳад.

## Маҳдудиятҳои Telegram

Бо Bot API файли калонтар аз ~50 MB фиристода намешавад. Агар файл калон бошад, бот сабабро мегӯяд.

Барои файлҳои калонтар лозим аст Telegram Local Bot API. Дар ҳамин компютери Windows он то 1 ГБ-ро мефиристад. Дар Railway бинарнии маҳаллӣ нест, бинобар ин ҳадди Telegram тақрибан 50 МБ мемонад.

## Ҷойгиркунӣ

Frontend ба Vercel, backend ба Railway ва база ба Neon. Қадамҳо дар [DEPLOY.md](DEPLOY.md).

## Сохтори лоиҳа

```text
SAFI DOWNLOADER/
├── main.py
├── config.py
├── database.py
├── downloader.py
├── keyboards.py
├── handlers/
├── utils/
├── locales/
├── downloads/
├── tests/
├── .env
├── .env.example
└── requirements.txt
```

## Амният

- Токен танҳо дар `.env` аст, на дар код.
- Ссылкаҳо санҷида мешаванд (танҳо доменҳои расмии Instagram).
- Файлҳои муваққатӣ баъди фиристодан нест карда мешаванд.
- Rate-limit барои ҳар корбар фаъол аст.
- Admin Panel ҳар дафъа бо `ADMIN_ID` санҷида мешавад, на бо username.
- Рассылка пешнамоиш ва тасдиқ дорад.

## Хатоҳои маъмул

| Хато | Ҳал |
| --- | --- |
| `BOT_TOKEN ёфт нашуд` | `.env`-ро пур кунед |
| `Unauthorized` | Токен нодуруст аст |
| `Conflict: terminated by other getUpdates` | Боти дигар (ё инстансияи дуюм) аллакай кор мекунад |
| Instagram медиа дастрас нест | Пост хусусӣ/нест аст, ё cookies лозим аст |
| FFmpeg: NO | FFmpeg насб кунед ва терминалро аз нав кушоед |
