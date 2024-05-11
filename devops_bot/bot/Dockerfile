# Скачиваем образ питона
FROM python:3.12-slim

# Устанавливаем рабочий каталог
WORKDIR /app

# Копируем директорию
COPY . /app

# Устанавливем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем бота
CMD ["python", "main.py"]
