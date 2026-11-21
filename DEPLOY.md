# Ҷойгиркунӣ: Vercel + Railway + Neon

Frontend дар Vercel, backend дар Railway ва база дар Neon (PostgreSQL). Файли `.env` ва `bot.db`-ро ба git нагузоред.

Дар Railway Telegram файлро то тақрибан **50 МБ** якбора мефиристад. То 1 ГБ танҳо дар ҳамин компютер мемонад, чунки Local Bot API барои Windows аст.

## 1. Neon

1. Дар [neon.tech](https://neon.tech) лоиҳа созед.
2. Connection string-и **direct** (порти 5432)-ро нусха гиред. Намуд: `postgresql://...@...neon.tech/neondb?sslmode=require`
3. Ин қимат баъдтар `DATABASE_URL` мешавад. Ҳангоми оғоз ҷадвалҳо худашон сохта мешаванд.

## 2. Railway

1. Репозиторийро ба Railway пайваст кунед. Builder: Dockerfile (файли `railway.toml` аллакай инро мегӯяд).
2. Домен созед, масалан `https://safi-downloader.up.railway.app`.
3. Ин тағйирёбандаҳоро гузоред:

| Ном | Қимат |
| --- | --- |
| `BOT_TOKEN` | токен аз @BotFather |
| `ADMIN_ID` | ID-и Telegram-и шумо |
| `DATABASE_URL` | сатри Neon |
| `WEBAPP_URL` | суроғаи Vercel, баъд аз қадами 3 |
| `CORS_ORIGINS` | ҳамон суроғаи Vercel |
| `MAX_FILE_SIZE_MB` | `50` |

`PORT`-ро Railway худаш медиҳад. Тунели cloudflared дар сервер кор намекунад.

## 3. Vercel

1. Лоиҳаро ворид кунед ва **Root Directory**-ро `webapp` гузоред.
2. Environment Variables:

| Ном | Қимат |
| --- | --- |
| `VITE_USE_MOCK` | `false` |
| `VITE_API_URL` | суроғаи Railway, бе `/` дар охир |

3. Deploy кунед. Суроғаи Vercel-ро ба `WEBAPP_URL` ва `CORS_ORIGINS` дар Railway гузоред ва сервисро аз нав оғоз кунед. Бот тугмаи Menu-ро ба ҳамин суроға мегузорад.

## Санҷиш

- `https://<railway>/health` бояд `{"ok": true}` диҳад.
- Дар Telegram тугмаи Menu Mini App-ро кушояд.
- Ссылкаро дар чати бот фиристед: боргирӣ дар базаи Neon сабт мешавад.

Дар компютер, агар `DATABASE_URL` холӣ бошад, бот мисли пештара `bot.db`-ро истифода мебарад.
