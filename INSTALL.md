# 🚀 Инструкция по установке NetworkView IS

## 📋 Предварительные требования

Для работы системы NetworkView IS необходимо установить Node.js и npm.

## 🔧 Установка Node.js

### Способ 1: Официальный сайт (Рекомендуется)

1. **Скачайте Node.js:**
   - Перейдите на [nodejs.org](https://nodejs.org/)
   - Выберите версию LTS (Long Term Support)
   - Скачайте установщик для Windows (.msi)

2. **Установите Node.js:**
   - Запустите скачанный файл
   - Следуйте инструкциям мастера установки
   - Убедитесь, что отмечена опция "Add to PATH"
   - Дождитесь завершения установки

3. **Проверьте установку:**
   Откройте новую командную строку (PowerShell) и выполните:
   ```powershell
   node --version
   npm --version
   ```

### Способ 2: Использование Chocolatey

1. **Установите Chocolatey** (если не установлен):
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. **Установите Node.js через Chocolatey:**
   ```powershell
   choco install nodejs
   ```

### Способ 3: Использование Winget (Windows Package Manager)

```powershell
winget install OpenJS.NodeJS
```

## 🚀 Запуск NetworkView IS

После установки Node.js выполните следующие шаги:

### 1. Установка зависимостей

Откройте PowerShell в папке проекта и выполните:

```powershell
cd "C:\Users\Kumsk\Desktop\NetworkView-IS"
npm install
```

### 2. Запуск системы

#### Режим разработки (рекомендуется):
```powershell
npm run dev
```

#### Только сервер:
```powershell
npm run dev:server
```

#### Продакшн режим:
```powershell
npm start
```

### 3. Открытие в браузере

После запуска откройте браузер и перейдите по адресу:
- **Клиентская часть:** http://localhost:3001
- **API сервер:** http://localhost:3000

## 🔧 Альтернативные способы запуска

### Без установки зависимостей (Упрощенная версия)

Если у вас проблемы с установкой Node.js, можно использовать упрощенную версию:

1. **Создайте простой HTTP сервер на Python** (если установлен):
   ```powershell
   cd "C:\Users\Kumsk\Desktop\NetworkView-IS"
   python -m http.server 8000
   ```

2. **Откройте в браузере:**
   http://localhost:8000

   ⚠️ **Внимание:** В этом режиме будет работать только клиентская часть без серверной функциональности.

### Использование VS Code Live Server

1. **Установите Visual Studio Code**
2. **Установите расширение "Live Server"**
3. **Откройте папку проекта в VS Code**
4. **Щелкните правой кнопкой на index.html → "Open with Live Server"**

## 🐛 Решение проблем

### Проблема: "npm не распознано"

**Решение:**
1. Убедитесь, что Node.js установлен правильно
2. Перезапустите PowerShell
3. Проверьте переменную PATH:
   ```powershell
   echo $env:PATH
   ```
4. Если Node.js не в PATH, добавьте вручную:
   - Откройте "Системные свойства" → "Переменные среды"
   - Добавьте путь к Node.js (обычно C:\Program Files\nodejs)

### Проблема: Ошибки при установке пакетов

**Решение:**
1. Очистите кэш npm:
   ```powershell
   npm cache clean --force
   ```
2. Удалите node_modules и переустановите:
   ```powershell
   Remove-Item -Recurse -Force node_modules
   Remove-Item package-lock.json
   npm install
   ```

### Проблема: Порт уже используется

**Решение:**
1. Измените порт в package.json
2. Или завершите процесс, использующий порт:
   ```powershell
   netstat -ano | findstr :3000
   taskkill /PID <PID номер> /F
   ```

### Проблема: Файрвол блокирует соединение

**Решение:**
1. Разрешите Node.js в файрволе Windows
2. Или временно отключите файрвол для тестирования

## 📝 Проверка работы системы

После успешного запуска вы должны увидеть:

1. **В консоли:**
   ```
   🚀 NetworkView IS Server запущен на порту 3000
   📁 Статические файлы: http://localhost:3000
   🔗 API: http://localhost:3000/api
   ⚡ WebSocket: ws://localhost:3000
   📊 Статистика: http://localhost:3000/api/stats
   
   ✅ Сервер готов к работе!
   ```

2. **В браузере:**
   - Заголовок "NetworkView IS"
   - 4 виджета в сетке
   - Индикатор "Онлайн" в правом верхнем углу
   - Примеры документов и устройств

## 🎯 Первые шаги

1. **Изучите интерфейс:**
   - Попробуйте поиск в модуле документов
   - Загрузите тестовую схему в модуле диаграмм
   - Проверьте мониторинг устройств

2. **Загрузите тестовые файлы:**
   - PDF документ в модуль документации
   - .drawio файл в модуль диаграмм

3. **Протестируйте функции:**
   - Предварительный просмотр документов
   - Пинг устройств
   - Экспорт данных

## 📞 Поддержка

Если у вас возникли проблемы:

1. **Проверьте логи в консоли**
2. **Откройте Developer Tools в браузере** (F12)
3. **Убедитесь, что все порты доступны**
4. **Проверьте права доступа к файлам**

## 🎉 Готово!

После выполнения всех шагов система NetworkView IS будет полностью готова к работе!

---

**Удачного использования NetworkView IS! 🚀** 