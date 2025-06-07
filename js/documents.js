/**
 * NetworkView IS - Модуль управления документами
 * Обработка нормативной документации по ИБ
 */

class DocumentManager {
    constructor(app) {
        this.app = app;
        this.filteredDocuments = [];
        this.selectedDocuments = [];
        this.currentSearch = '';
        this.currentFilters = {
            category: '',
            type: ''
        };
        
        this.init();
    }

    /**
     * Инициализация модуля документов
     */
    init() {
        this.initEventListeners();
        this.loadSampleDocuments();
    }

    /**
     * Инициализация обработчиков событий
     */
    initEventListeners() {
        // Поиск документов
        const searchInput = document.getElementById('docSearch');
        searchInput.addEventListener('input', (e) => {
            this.currentSearch = e.target.value;
            this.filterDocuments();
        });

        // Фильтры
        const categoryFilter = document.getElementById('categoryFilter');
        const typeFilter = document.getElementById('typeFilter');
        
        categoryFilter.addEventListener('change', (e) => {
            this.currentFilters.category = e.target.value;
            this.filterDocuments();
        });

        typeFilter.addEventListener('change', (e) => {
            this.currentFilters.type = e.target.value;
            this.filterDocuments();
        });

        // Кнопки управления
        document.getElementById('uploadDocBtn').addEventListener('click', () => {
            this.showUploadDialog();
        });

        document.getElementById('refreshDocsBtn').addEventListener('click', () => {
            this.refreshDocuments();
        });
    }

    /**
     * Загрузка примеров документов
     */
    loadSampleDocuments() {
        const sampleDocuments = [
            {
                id: 1,
                name: 'ФЗ-152 О персональных данных',
                description: 'Федеральный закон о персональных данных',
                category: 'ФЗ',
                type: 'PDF',
                size: '2.3 MB',
                uploadDate: '2024-01-15',
                tags: ['персональные данные', 'защита информации', 'федеральный закон'],
                url: '#',
                status: 'active'
            },
            {
                id: 2,
                name: 'ISO/IEC 27001:2013',
                description: 'Системы менеджмента информационной безопасности',
                category: 'ISO',
                type: 'PDF',
                size: '1.8 MB',
                uploadDate: '2024-01-20',
                tags: ['ISO', 'ISMS', 'информационная безопасность'],
                url: '#',
                status: 'active'
            },
            {
                id: 3,
                name: 'ГОСТ Р 57580-2017',
                description: 'Безопасность информационных технологий',
                category: 'ГОСТ',
                type: 'PDF',
                size: '3.1 MB',
                uploadDate: '2024-01-25',
                tags: ['ГОСТ', 'ИТ безопасность', 'российский стандарт'],
                url: '#',
                status: 'active'
            },
            {
                id: 4,
                name: 'Приказ ФСТЭК №21',
                description: 'Состав и содержание организационных и технических мер',
                category: 'Приказы',
                type: 'DOCX',
                size: '890 KB',
                uploadDate: '2024-02-01',
                tags: ['ФСТЭК', 'организационные меры', 'технические меры'],
                url: '#',
                status: 'active'
            },
            {
                id: 5,
                name: 'ISO/IEC 27002:2022',
                description: 'Свод правил по управлению информационной безопасностью',
                category: 'ISO',
                type: 'PDF',
                size: '2.7 MB',
                uploadDate: '2024-02-05',
                tags: ['ISO', 'свод правил', 'управление ИБ'],
                url: '#',
                status: 'active'
            }
        ];

        this.app.documents = sampleDocuments;
        this.filterDocuments();
    }

    /**
     * Фильтрация документов
     */
    filterDocuments() {
        let filtered = [...this.app.documents];

        // Поиск по тексту
        if (this.currentSearch) {
            const searchLower = this.currentSearch.toLowerCase();
            filtered = filtered.filter(doc => 
                doc.name.toLowerCase().includes(searchLower) ||
                doc.description.toLowerCase().includes(searchLower) ||
                doc.tags.some(tag => tag.toLowerCase().includes(searchLower))
            );
        }

        // Фильтр по категории
        if (this.currentFilters.category) {
            filtered = filtered.filter(doc => doc.category === this.currentFilters.category);
        }

        // Фильтр по типу
        if (this.currentFilters.type) {
            filtered = filtered.filter(doc => doc.type === this.currentFilters.type);
        }

        this.filteredDocuments = filtered;
        this.renderDocuments();
    }

    /**
     * Рендеринг списка документов
     */
    renderDocuments() {
        const documentsList = document.getElementById('documentsList');
        documentsList.innerHTML = '';

        if (this.filteredDocuments.length === 0) {
            documentsList.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-search text-3xl mb-3"></i>
                    <p>Документы не найдены</p>
                    <p class="text-sm">Попробуйте изменить критерии поиска</p>
                </div>
            `;
            return;
        }

        this.filteredDocuments.forEach(doc => {
            const docElement = this.createDocumentElement(doc);
            documentsList.appendChild(docElement);
        });

        // Обновление счетчика документов
        document.getElementById('documentCount').textContent = this.filteredDocuments.length;
    }

    /**
     * Создание элемента документа
     */
    createDocumentElement(doc) {
        const docElement = document.createElement('div');
        docElement.className = 'document-item scrollbar-custom';
        docElement.innerHTML = `
            <div class="flex items-start justify-between">
                <div class="flex-1">
                    <div class="flex items-center mb-2">
                        <div class="file-icon ${doc.type.toLowerCase()} mr-3">
                            <i class="fas ${this.getFileIcon(doc.type)}"></i>
                        </div>
                        <div>
                            <h3 class="font-medium text-gray-900">${doc.name}</h3>
                            <p class="text-sm text-gray-600">${doc.description}</p>
                        </div>
                    </div>
                    <div class="flex flex-wrap gap-1 mb-2">
                        <span class="tag category-${doc.category.toLowerCase()}">${doc.category}</span>
                        ${doc.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                    <div class="flex items-center text-xs text-gray-500 space-x-4">
                        <span><i class="fas fa-calendar mr-1"></i>${new Date(doc.uploadDate).toLocaleDateString('ru-RU')}</span>
                        <span><i class="fas fa-hdd mr-1"></i>${doc.size}</span>
                        <span><i class="fas fa-file mr-1"></i>${doc.type}</span>
                    </div>
                </div>
                <div class="flex flex-col space-y-2 ml-4">
                    <button class="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors text-sm" 
                            onclick="documentManager.previewDocument(${doc.id})">
                        <i class="fas fa-eye mr-1"></i>Просмотр
                    </button>
                    <button class="px-3 py-1 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors text-sm"
                            onclick="documentManager.downloadDocument(${doc.id})">
                        <i class="fas fa-download mr-1"></i>Скачать
                    </button>
                    <button class="px-3 py-1 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors text-sm"
                            onclick="documentManager.shareDocument(${doc.id})">
                        <i class="fas fa-share mr-1"></i>Поделиться
                    </button>
                </div>
            </div>
        `;

        // Обработчик клика для выделения
        docElement.addEventListener('click', (e) => {
            if (!e.target.closest('button')) {
                this.toggleDocumentSelection(doc.id, docElement);
            }
        });

        return docElement;
    }

    /**
     * Получение иконки файла
     */
    getFileIcon(type) {
        const icons = {
            'PDF': 'fa-file-pdf',
            'DOCX': 'fa-file-word',
            'TXT': 'fa-file-alt'
        };
        return icons[type] || 'fa-file';
    }

    /**
     * Переключение выделения документа
     */
    toggleDocumentSelection(docId, element) {
        const index = this.selectedDocuments.indexOf(docId);
        if (index > -1) {
            this.selectedDocuments.splice(index, 1);
            element.classList.remove('selected');
        } else {
            this.selectedDocuments.push(docId);
            element.classList.add('selected');
        }
    }

    /**
     * Предварительный просмотр документа
     */
    async previewDocument(docId) {
        const doc = this.app.documents.find(d => d.id === docId);
        if (!doc) return;

        const modal = document.getElementById('documentModal');
        const modalTitle = document.getElementById('modalTitle');
        const modalContent = document.getElementById('modalContent');

        modalTitle.textContent = doc.name;
        modalContent.innerHTML = this.generatePreviewContent(doc);

        modal.classList.remove('hidden');
    }

    /**
     * Генерация содержимого предварительного просмотра
     */
    generatePreviewContent(doc) {
        // Симуляция содержимого документа с Markdown
        const content = `
# ${doc.name}

## Описание
${doc.description}

## Основные положения

### 1. Общие требования
Документ устанавливает основные требования к системам информационной безопасности в соответствии с российскими и международными стандартами.

### 2. Области применения
- Государственные информационные системы
- Коммерческие организации
- Критическая информационная инфраструктура

### 3. Ключевые принципы
1. **Конфиденциальность** - защита от несанкционированного доступа
2. **Целостность** - предотвращение несанкционированного изменения
3. **Доступность** - обеспечение доступа авторизованных пользователей

## Требования к реализации

### Организационные меры
- Разработка политики информационной безопасности
- Назначение ответственных лиц
- Проведение аудитов и проверок

### Технические меры
- Внедрение систем контроля доступа
- Использование средств криптографической защиты
- Мониторинг событий безопасности

## Заключение
Соблюдение данных требований обеспечивает необходимый уровень защиты информационных активов организации.

---
**Теги:** ${doc.tags.join(', ')}  
**Категория:** ${doc.category}  
**Дата загрузки:** ${new Date(doc.uploadDate).toLocaleDateString('ru-RU')}
`;

        return marked.parse(content);
    }

    /**
     * Скачивание документа
     */
    async downloadDocument(docId) {
        const doc = this.app.documents.find(d => d.id === docId);
        if (!doc) return;

        // Симуляция скачивания
        this.app.showNotification('info', 'Загрузка документа', `Начинается загрузка ${doc.name}`);
        
        // В реальном приложении здесь был бы запрос к серверу
        setTimeout(() => {
            this.app.showNotification('success', 'Документ загружен', `${doc.name} успешно загружен`);
        }, 2000);
    }

    /**
     * Поделиться документом
     */
    async shareDocument(docId) {
        const doc = this.app.documents.find(d => d.id === docId);
        if (!doc) return;

        if (navigator.share) {
            try {
                await navigator.share({
                    title: doc.name,
                    text: doc.description,
                    url: window.location.href + '#doc=' + docId
                });
            } catch (error) {
                console.log('Ошибка при попытке поделиться:', error);
            }
        } else {
            // Копирование ссылки в буфер обмена
            const url = window.location.href + '#doc=' + docId;
            try {
                await navigator.clipboard.writeText(url);
                this.app.showNotification('success', 'Ссылка скопирована', 'Ссылка на документ скопирована в буфер обмена');
            } catch (error) {
                this.app.showNotification('error', 'Ошибка', 'Не удалось скопировать ссылку');
            }
        }
    }

    /**
     * Показать диалог загрузки
     */
    showUploadDialog() {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.accept = '.pdf,.docx,.txt';
        
        input.onchange = (e) => {
            const files = Array.from(e.target.files);
            files.forEach(file => {
                this.app.uploadDocument(file);
            });
        };
        
        input.click();
    }

    /**
     * Обновление списка документов
     */
    async refreshDocuments() {
        try {
            this.app.showNotification('info', 'Обновление', 'Загрузка актуального списка документов...');
            
            // В реальном приложении здесь был бы запрос к серверу
            setTimeout(() => {
                this.loadSampleDocuments();
                this.app.showNotification('success', 'Обновлено', 'Список документов успешно обновлен');
            }, 1000);
            
        } catch (error) {
            console.error('Ошибка обновления документов:', error);
            this.app.showNotification('error', 'Ошибка обновления', 'Не удалось обновить список документов');
        }
    }

    /**
     * Экспорт выбранных документов
     */
    async exportSelectedDocuments() {
        if (this.selectedDocuments.length === 0) {
            this.app.showNotification('warning', 'Нет выделенных документов', 'Выберите документы для экспорта');
            return;
        }

        const selectedDocs = this.app.documents.filter(doc => 
            this.selectedDocuments.includes(doc.id)
        );

        const exportData = {
            exportDate: new Date().toISOString(),
            totalDocuments: selectedDocs.length,
            documents: selectedDocs
        };

        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `documents_export_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        
        URL.revokeObjectURL(url);
        this.app.showNotification('success', 'Экспорт завершен', `Экспортировано ${selectedDocs.length} документов`);
    }

    /**
     * Полнотекстовый поиск по содержимому документов
     */
    async fullTextSearch(query) {
        // В реальном приложении здесь был бы запрос к серверу для полнотекстового поиска
        this.app.showNotification('info', 'Поиск по содержимому', 'Функция полнотекстового поиска будет добавлена в следующих версиях');
    }
}

// Инициализация менеджера документов после загрузки приложения
document.addEventListener('DOMContentLoaded', () => {
    // Ждем инициализации основного приложения
    setTimeout(() => {
        if (window.app) {
            window.documentManager = new DocumentManager(window.app);
            
            // Переопределяем метод рендеринга документов в основном приложении
            window.app.renderDocuments = () => {
                window.documentManager.renderDocuments();
            };
        }
    }, 100);
}); 