FROM node:18-alpine

# Установка системных зависимостей
RUN apk add --no-cache git

# Создание рабочей директории
WORKDIR /app

# Копирование package.json и package-lock.json
COPY package*.json ./

# Установка зависимостей
RUN npm ci

# Копирование исходного кода
COPY . .

# Экспорт порта
EXPOSE 3000

# Запуск dev сервера
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Использование nginx для сервинга
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=0 /app/dist /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открытие порта
EXPOSE 80

# Команда запуска
CMD ["nginx", "-g", "daemon off;"] 