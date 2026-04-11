# 💈 BarberBot — Telegram Booking System (SaaS-ready)

## 🚀 Overview

**BarberBot** is a production-oriented fullstack system for automating client bookings in barbershops and service-based businesses.

It replaces manual scheduling with a seamless Telegram WebApp interface, real-time availability checks, automated notifications, and integrated payments.

Designed with scalability in mind, the system supports a SaaS-like architecture for easy adaptation to multiple businesses.

---

## 🔗 Live Demo

- 🤖 Bot: https://t.me/YOUR_BOT  
- 🌐 WebApp: https://barberbot-zp.duckdns.org/webapp/  

---

## ✨ Features

### 👤 Client Experience
- Interactive booking via Telegram WebApp
- Real-time availability validation (no double booking)
- Service and master selection
- 📅 Smart time-slot filtering
- 💳 Built-in payments (Telegram Payments API)
- 🎁 Digital gift certificates with unique promo codes

---

### 🛠 Admin Panel (Django)
- Manage masters, services, schedules
- View and control bookings
- ⚙️ Dynamic configuration via database (Singleton pattern)
- Business logic controlled without code changes

---

### ⚙️ Backend & Integrations
- REST API with Django REST Framework
- Asynchronous bot (Aiogram 3)
- Redis + Celery for background tasks
- 📊 Google Sheets integration (auto export of bookings)
- Notifications for client, admin, and master

---

## 🧱 Architecture Highlights

- Fullstack system (Bot + WebApp + API + Admin)
- SaaS-ready configuration layer
- Unique constraints to prevent double booking
- Separation of concerns (bot / backend / frontend)
- Production-ready deployment with Docker

---

## 🛠 Tech Stack

- **Backend:** Python, Django, Django REST Framework
- **Bot:** Aiogram 3
- **Database:** PostgreSQL
- **Async & Queue:** Celery, Redis
- **Frontend:** Telegram WebApp (Vanilla JS)
- **Infra:** Docker, Docker Compose, Nginx, Gunicorn
- **Integrations:** Google Sheets API, Telegram Payments

---

## 📦 Installation

### 1. Clone repository
```bash
git clone https://github.com/ForShure/BarberBot.git
cd BarberBot 
```

### 2. Setup environment
```
TOKEN=your_bot_token
ADMIN_ID=your_telegram_id
PAYMENT_TOKEN=your_payment_provider_token

POSTGRES_DB=barber_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret
POSTGRES_HOST=db
POSTGRES_PORT=5432
 ```
### 3. Run project
```bash
docker-compose up -d --build
```
### 4. Apply migrations
```bash
docker-compose exec web python web/manage.py migrate
```
### 5. Create superuser
```bash
docker-compose exec web python web/manage.py createsuperuser
```  
### 6. Optional: Google Sheets Integration
```markdown
  Place your google_credentials.json file into:
  web/
```
🧑‍💻 Author
Vladislav (For Shure)
Backend & Telegram Bot Developer