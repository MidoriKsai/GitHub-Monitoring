1. Клонирование проекта

Клонируйте репозиторий с GitHub:

git clone [<URL_репозитория>](https://github.com/MidoriKsai/GitHub-Monitoring.git)
cd <название_папки_проекта>

2. Настройка виртуального окружения и установка зависимостей

Создайте виртуальное окружение и активируйте его:

python -m venv venv
 Windows
venv\Scripts\activate
 Linux/macOS
source venv/bin/activate


Установите необходимые зависимости:

pip install --upgrade pip
pip install -r requirements.txt


После установки Playwright необходимо скачать браузеры:

playwright install

3. Настройка переменных окружения

Создайте файл .env в корне проекта и укажите необходимые параметры:

GITHUB_TOKEN=<ваш персональный токен GitHub>
NATS_URL=nats://127.0.0.1:4222

GITHUB_TOKEN — персональный токен GitHub с правами на чтение и управление репозиториями.

NATS_URL — адрес сервера NATS (по умолчанию локальный).

4. Запуск проекта
  
Локальный запуск с uvicorn
uvicorn app.main:app --reload




