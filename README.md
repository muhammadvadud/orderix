<div align="center">

# OrderiX · Backend

**Restoran ish jarayonlari uchun yagona API**

Buyurtmalar · Menyu · Stollar · Xodimlar · Hisobotlar

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white) ![Django](https://img.shields.io/badge/Django-6.0-092E20?style=flat-square&logo=django) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white) ![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)

[Frontend](https://github.com/muhammadvadud/orderix-front) · [O‘rnatish](#ornatish) · [API](#api-va-websocket) · [Tuzilma](#papka-tuzilmasi)

</div>

## Loyiha haqida

OrderiX — restoranlarda buyurtmalar, menyu, zal va stollar, xodimlar hamda savdo ko‘rsatkichlarini boshqarish tizimi. Ushbu repository Django REST Framework asosidagi backend’ni saqlaydi. Next.js frontend REST API orqali ishlaydi, buyurtma va joylashuvlardagi o‘zgarishlar esa Django Channels orqali real vaqtda yetkaziladi.

## Imkoniyatlar

- **Autentifikatsiya:** telefon va parol yoki OTP orqali kirish, JWT tokenlarini yangilash.
- **Xodimlar:** admin, menejer, ofitsiant va oshpaz rollari, restoran bilan bog‘langan profillar.
- **Restoran:** zallar va stollar, menyu kategoriyalari, taomlar, valyuta va xizmat haqi sozlamalari.
- **Buyurtmalar:** buyurtma yaratish, tarkibini yangilash, buyurtma va alohida taom holatlarini boshqarish.
- **Statistika:** dashboard, tushum va buyurtmalar dinamikasi, mashhur taomlar va ofitsiantlar ko‘rsatkichlari.
- **Real vaqt:** JWT bilan himoyalangan WebSocket, Redis orqali resurs o‘zgarishlarini tarqatish.
- **Ishlab chiqish:** OpenAPI, Swagger, ReDoc, Django admin va demo ma’lumotlar yaratish buyrug‘i.

## Talablar

- Docker Engine va Docker Compose v2 — tavsiya etilgan ishga tushirish usuli.
- Docker’siz ishlash uchun: Python 3.13, PostgreSQL 16 va Redis 7.
- Frontend: [orderix-front](https://github.com/muhammadvadud/orderix-front).

## O‘rnatish

```bash
git clone https://github.com/muhammadvadud/orderix.git
cd orderix
cp .env.example .env
```

`.env` ichidagi `SECRET_KEY` qiymatini o‘zingiz yaratgan kalit bilan almashtiring. Namunadagi ma’lumotlar lokal development uchun; `DB_*` qiymatlari `docker-compose.yml` dagi PostgreSQL sozlamalariga mos bo‘lishi kerak.

```bash
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
```

Entrypoint PostgreSQL tayyor bo‘lishini kutadi, migratsiyalarni qo‘llaydi va static fayllarni yig‘adi. Standart `.env.example` bilan server `http://localhost:8080` manzilida ishlaydi.

Demo restoran, xodimlar, menyu va buyurtmalarni yaratish uchun lokal muhitda:

```bash
docker compose exec web python manage.py seed_demo
```

Demo hisoblar haqidagi ma’lumotlar [seed_demo.py](restaurant/management/commands/seed_demo.py) ichida keltirilgan.

## Muhit sozlamalari

| O‘zgaruvchi | Vazifasi |
| --- | --- |
| `DEBUG`, `PROJECT_ENV` | Development rejimi; API hujjatlari uchun `PROJECT_ENV=debug` |
| `SECRET_KEY` | Django maxfiy kaliti |
| `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL ulanishi |
| `WEB_PORT` | Backend porti; namunada `8080` |
| `REDIS_URL` | WebSocket channel layer va cache; Compose ichida avtomatik beriladi |
| `CORS_ALLOWED_ORIGINS` | Frontend origin’lari; lokal muhitda `http://localhost:3000` |
| `ALLOWED_HOSTS` | Ruxsat etilgan host’lar, vergul bilan ajratiladi |

Redis manzili berilmasa, channel layer va cache lokal xotirada ishlaydi.

## API va WebSocket

| Manzil | Vazifasi |
| --- | --- |
| `/admin/` | Django admin |
| `/api/v1/auth/` | Login, OTP, JWT va joriy profil |
| `/api/v1/users` | Xodimlar |
| `/api/v1/restaurants`, `/api/v1/locations` | Restoranlar, zallar va stollar |
| `/api/v1/menu/categories`, `/api/v1/menu/items` | Menyu |
| `/api/v1/orders` | Buyurtmalar |
| `/api/v1/stats/` | Statistika endpoint’lari |
| `/api/v1/settings` | Restoran sozlamalari |
| `/ws/realtime/` | Real vaqt yangilanishlari |
| `/schema/`, `/swagger/`, `/redoc/` | `PROJECT_ENV=debug` bo‘lgandagi API hujjatlari |

REST router endpoint’lari oxirida `/` ishlatilmaydi. Himoyalangan REST so‘rovlariga `Authorization: Bearer <access_token>` yuboriladi. WebSocket ulanishi `/ws/realtime/?token=<access_token>` orqali ochiladi va `resource_changed` hodisalarini yetkazadi.

## Papka tuzilmasi

```text
accounts/      # Hisoblar, rollar, JWT va OTP
restaurant/    # Restoran, menyu, zallar, stollar va sozlamalar
order/         # Buyurtmalar va buyurtma tarkibi
stats/         # Statistika va hisobotlar
realtime/      # WebSocket, JWT middleware va hodisalar
storage/       # Fayl saqlash moduli
helpers/       # Umumiy yordamchi kod
config/        # Django sozlamalari, URL va ASGI
```

## Tekshirish va boshqarish

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py test
docker compose logs -f web
docker compose down
```

Joriy Compose konfiguratsiyasi `runserver` orqali development serverini ishga tushiradi. Production uchun ASGI server va reverse proxy sozlang, `DEBUG=False`, haqiqiy `ALLOWED_HOSTS`, HTTPS hamda alohida maxfiy kalitlardan foydalaning.

## Bog‘liq loyiha

[OrderiX Frontend](https://github.com/muhammadvadud/orderix-front) — menejer va ofitsiant uchun Next.js interfeysi.
