/**
 * NetworkView IS - Модуль управления диаграммами
 * Работа с интерактивными схемами .drawio
 */

class DiagramManager {
    constructor(app) {
        this.app = app;
        this.currentDiagram = null;
        this.graph = null;
        this.nodes = new Map();
        this.edges = new Map();
        this.selectedElement = null;
        this.zoomLevel = 1;
        
        this.init();
    }

    /**
     * Инициализация модуля диаграмм
     */
    init() {
        this.initEventListeners();
        this.loadSampleDiagrams();
        this.initMxGraph();
    }

    /**
     * Инициализация обработчиков событий
     */
    initEventListeners() {
        // Загрузка диаграммы
        document.getElementById('uploadDiagramBtn').addEventListener('click', () => {
            this.showUploadDialog();
        });

        // Экспорт диаграммы
        document.getElementById('exportDiagramBtn').addEventListener('click', () => {
            this.exportDiagram();
        });

        // Управление масштабом
        document.getElementById('zoomInBtn').addEventListener('click', () => {
            this.zoomIn();
        });

        document.getElementById('zoomOutBtn').addEventListener('click', () => {
            this.zoomOut();
        });

        document.getElementById('fitToScreenBtn').addEventListener('click', () => {
            this.fitToScreen();
        });

        // Выбор диаграммы
        document.getElementById('diagramList').addEventListener('change', (e) => {
            if (e.target.value) {
                this.loadDiagram(parseInt(e.target.value));
            }
        });
    }

    /**
     * Инициализация mxGraph
     */
    initMxGraph() {
        // Проверяем доступность mxGraph
        if (typeof mxGraph === 'undefined') {
            console.warn('mxGraph не загружен, используем базовую SVG визуализацию');
            this.initBasicVisualization();
            return;
        }

        try {
            const container = document.getElementById('diagramCanvas');
            this.graph = new mxGraph(container);
            
            // Настройка графа
            this.graph.setEnabled(false); // Только просмотр
            this.graph.setPanning(true);
            this.graph.setConnectable(false);
            
            // Обработчики событий графа
            this.graph.addListener(mxEvent.CLICK, (sender, evt) => {
                this.handleGraphClick(evt);
            });

        } catch (error) {
            console.error('Ошибка инициализации mxGraph:', error);
            this.initBasicVisualization();
        }
    }

    /**
     * Базовая SVG визуализация (fallback)
     */
    initBasicVisualization() {
        const container = document.getElementById('diagramCanvas');
        container.innerHTML = `
            <svg id="diagramSvg" width="100%" height="100%" viewBox="0 0 800 600">
                <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                            refX="0" refY="3.5" orient="auto">
                        <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
                    </marker>
                </defs>
                <g id="diagramGroup"></g>
            </svg>
        `;
        
        this.useSvgFallback = true;
    }

    /**
     * Загрузка примеров диаграмм
     */
    loadSampleDiagrams() {
        const sampleDiagrams = [
            {
                id: 1,
                name: 'Сетевая архитектура офиса',
                description: 'Схема сетевой инфраструктуры главного офиса',
                uploadDate: '2024-01-10',
                nodes: [
                    {
                        id: 'router1',
                        type: 'router',
                        name: 'Главный маршрутизатор',
                        ip: '192.168.1.1',
                        status: 'online',
                        x: 100,
                        y: 100,
                        metadata: {
                            model: 'Cisco ISR 4321',
                            uptime: '45 дней',
                            load: '23%'
                        }
                    },
                    {
                        id: 'switch1',
                        type: 'switch',
                        name: 'Коммутатор уровня доступа',
                        ip: '192.168.1.10',
                        status: 'online',
                        x: 300,
                        y: 100,
                        metadata: {
                            model: 'Cisco Catalyst 2960',
                            ports: '24',
                            vlan: 'VLAN 10, 20, 30'
                        }
                    },
                    {
                        id: 'server1',
                        type: 'server',
                        name: 'Файловый сервер',
                        ip: '192.168.1.100',
                        status: 'online',
                        x: 500,
                        y: 100,
                        metadata: {
                            os: 'Windows Server 2019',
                            cpu: '32%',
                            memory: '68%',
                            disk: '45%'
                        }
                    },
                    {
                        id: 'workstation1',
                        type: 'workstation',
                        name: 'Рабочая станция #1',
                        ip: '192.168.1.201',
                        status: 'online',
                        x: 200,
                        y: 250,
                        metadata: {
                            os: 'Windows 10',
                            user: 'Иванов И.И.',
                            department: 'ИТ'
                        }
                    },
                    {
                        id: 'workstation2',
                        type: 'workstation',
                        name: 'Рабочая станция #2',
                        ip: '192.168.1.202',
                        status: 'offline',
                        x: 400,
                        y: 250,
                        metadata: {
                            os: 'Windows 10',
                            user: 'Петров П.П.',
                            department: 'Бухгалтерия'
                        }
                    }
                ],
                edges: [
                    {
                        id: 'edge1',
                        from: 'router1',
                        to: 'switch1',
                        port: '80',
                        subnet: '192.168.1.0/24',
                        bandwidth: '1 Gbps',
                        protocol: 'Ethernet'
                    },
                    {
                        id: 'edge2',
                        from: 'switch1',
                        to: 'server1',
                        port: '443',
                        subnet: '192.168.1.0/24',
                        bandwidth: '1 Gbps',
                        protocol: 'Ethernet'
                    },
                    {
                        id: 'edge3',
                        from: 'switch1',
                        to: 'workstation1',
                        port: '22',
                        subnet: '192.168.1.0/24',
                        bandwidth: '100 Mbps',
                        protocol: 'Ethernet'
                    },
                    {
                        id: 'edge4',
                        from: 'switch1',
                        to: 'workstation2',
                        port: '22',
                        subnet: '192.168.1.0/24',
                        bandwidth: '100 Mbps',
                        protocol: 'Ethernet'
                    }
                ]
            },
            {
                id: 2,
                name: 'Серверная инфраструктура',
                description: 'Схема серверного окружения и виртуализации',
                uploadDate: '2024-01-15',
                nodes: [
                    {
                        id: 'esxi1',
                        type: 'hypervisor',
                        name: 'VMware ESXi Host 1',
                        ip: '10.0.1.10',
                        status: 'online',
                        x: 150,
                        y: 100,
                        metadata: {
                            version: 'ESXi 7.0',
                            vms: '12',
                            cpu: '45%',
                            memory: '78%'
                        }
                    },
                    {
                        id: 'vm1',
                        type: 'vm',
                        name: 'Web Server VM',
                        ip: '10.0.1.101',
                        status: 'online',
                        x: 50,
                        y: 250,
                        metadata: {
                            os: 'Ubuntu 20.04',
                            vcpu: '2',
                            memory: '4 GB',
                            service: 'Apache'
                        }
                    },
                    {
                        id: 'vm2',
                        type: 'vm',
                        name: 'Database VM',
                        ip: '10.0.1.102',
                        status: 'online',
                        x: 250,
                        y: 250,
                        metadata: {
                            os: 'CentOS 8',
                            vcpu: '4',
                            memory: '8 GB',
                            service: 'PostgreSQL'
                        }
                    }
                ],
                edges: [
                    {
                        id: 'vm_edge1',
                        from: 'esxi1',
                        to: 'vm1',
                        port: 'vNIC',
                        subnet: '10.0.1.0/24',
                        bandwidth: 'Virtual',
                        protocol: 'Virtual Switch'
                    },
                    {
                        id: 'vm_edge2',
                        from: 'esxi1',
                        to: 'vm2',
                        port: 'vNIC',
                        subnet: '10.0.1.0/24',
                        bandwidth: 'Virtual',
                        protocol: 'Virtual Switch'
                    }
                ]
            }
        ];

        this.app.diagrams = sampleDiagrams;
        this.populateDiagramList();
    }

    /**
     * Заполнение списка диаграмм
     */
    populateDiagramList() {
        const select = document.getElementById('diagramList');
        select.innerHTML = '<option value="">Выберите схему...</option>';
        
        this.app.diagrams.forEach(diagram => {
            const option = document.createElement('option');
            option.value = diagram.id;
            option.textContent = diagram.name;
            select.appendChild(option);
        });
    }

    /**
     * Загрузка диаграммы
     */
    loadDiagram(diagramId) {
        const diagram = this.app.diagrams.find(d => d.id === diagramId);
        if (!diagram) return;

        this.currentDiagram = diagram;
        this.nodes.clear();
        this.edges.clear();

        // Сохранение узлов и ребер
        diagram.nodes.forEach(node => {
            this.nodes.set(node.id, node);
        });

        diagram.edges.forEach(edge => {
            this.edges.set(edge.id, edge);
        });

        // Очистка placeholder
        document.getElementById('diagramPlaceholder').style.display = 'none';

        // Рендеринг диаграммы
        if (this.useSvgFallback) {
            this.renderSvgDiagram();
        } else {
            this.renderMxGraphDiagram();
        }

        this.app.showNotification('success', 'Диаграмма загружена', `Схема "${diagram.name}" успешно отображена`);
    }

    /**
     * Рендеринг диаграммы через SVG (fallback)
     */
    renderSvgDiagram() {
        const group = document.getElementById('diagramGroup');
        group.innerHTML = '';

        // Рендеринг ребер (связей)
        this.edges.forEach(edge => {
            const fromNode = this.nodes.get(edge.from);
            const toNode = this.nodes.get(edge.to);
            
            if (fromNode && toNode) {
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('x1', fromNode.x + 25);
                line.setAttribute('y1', fromNode.y + 25);
                line.setAttribute('x2', toNode.x + 25);
                line.setAttribute('y2', toNode.y + 25);
                line.setAttribute('stroke', '#666');
                line.setAttribute('stroke-width', '2');
                line.setAttribute('marker-end', 'url(#arrowhead)');
                line.classList.add('diagram-edge');
                line.addEventListener('click', () => this.showEdgeInfo(edge));
                group.appendChild(line);
            }
        });

        // Рендеринг узлов
        this.nodes.forEach(node => {
            const nodeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            nodeGroup.classList.add('diagram-node');
            nodeGroup.addEventListener('click', () => this.showNodeInfo(node));

            // Фон узла
            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('x', node.x);
            rect.setAttribute('y', node.y);
            rect.setAttribute('width', '50');
            rect.setAttribute('height', '50');
            rect.setAttribute('fill', this.getNodeColor(node.type, node.status));
            rect.setAttribute('stroke', '#333');
            rect.setAttribute('stroke-width', '2');
            rect.setAttribute('rx', '5');

            // Иконка узла
            const icon = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            icon.setAttribute('x', node.x + 25);
            icon.setAttribute('y', node.y + 30);
            icon.setAttribute('text-anchor', 'middle');
            icon.setAttribute('font-family', 'FontAwesome');
            icon.setAttribute('font-size', '16');
            icon.setAttribute('fill', '#fff');
            icon.textContent = this.getNodeIcon(node.type);

            // Подпись узла
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', node.x + 25);
            label.setAttribute('y', node.y + 65);
            label.setAttribute('text-anchor', 'middle');
            label.setAttribute('font-size', '10');
            label.setAttribute('fill', '#333');
            label.textContent = node.name;

            nodeGroup.appendChild(rect);
            nodeGroup.appendChild(icon);
            nodeGroup.appendChild(label);
            group.appendChild(nodeGroup);
        });
    }

    /**
     * Рендеринг диаграммы через mxGraph
     */
    renderMxGraphDiagram() {
        if (!this.graph) return;

        const parent = this.graph.getDefaultParent();
        this.graph.getModel().beginUpdate();

        try {
            this.graph.removeCells(this.graph.getChildVertices(parent));

            const vertices = {};

            // Создание вершин
            this.nodes.forEach(node => {
                const vertex = this.graph.insertVertex(
                    parent, 
                    node.id, 
                    node.name, 
                    node.x, 
                    node.y, 
                    80, 
                    40,
                    this.getMxGraphStyle(node.type, node.status)
                );
                vertices[node.id] = vertex;
            });

            // Создание ребер
            this.edges.forEach(edge => {
                const source = vertices[edge.from];
                const target = vertices[edge.to];
                
                if (source && target) {
                    this.graph.insertEdge(parent, edge.id, '', source, target);
                }
            });

        } finally {
            this.graph.getModel().endUpdate();
        }
    }

    /**
     * Получение цвета узла
     */
    getNodeColor(type, status) {
        const colors = {
            router: status === 'online' ? '#4CAF50' : '#F44336',
            switch: status === 'online' ? '#2196F3' : '#FF9800',
            server: status === 'online' ? '#9C27B0' : '#795548',
            workstation: status === 'online' ? '#FF9800' : '#607D8B',
            hypervisor: status === 'online' ? '#3F51B5' : '#9E9E9E',
            vm: status === 'online' ? '#00BCD4' : '#757575'
        };
        return colors[type] || '#666';
    }

    /**
     * Получение иконки узла
     */
    getNodeIcon(type) {
        const icons = {
            router: '🔗',
            switch: '🔀',
            server: '🖥️',
            workstation: '💻',
            hypervisor: '☁️',
            vm: '📦'
        };
        return icons[type] || '❓';
    }

    /**
     * Получение стиля для mxGraph
     */
    getMxGraphStyle(type, status) {
        const color = this.getNodeColor(type, status);
        return `fillColor=${color};strokeColor=#333333;fontColor=#FFFFFF;rounded=1;`;
    }

    /**
     * Показ информации об узле
     */
    showNodeInfo(node) {
        const modal = document.getElementById('elementModal');
        const modalTitle = document.getElementById('elementModalTitle');
        const modalContent = document.getElementById('elementModalContent');

        modalTitle.textContent = `Узел: ${node.name}`;
        modalContent.innerHTML = `
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">IP-адрес</label>
                        <div class="mt-1 text-sm text-gray-900">${node.ip}</div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Тип</label>
                        <div class="mt-1 text-sm text-gray-900">${node.type}</div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Статус</label>
                        <div class="mt-1">
                            <span class="device-status ${node.status}"></span>
                            <span class="text-sm text-gray-900 ml-2">${node.status === 'online' ? 'Активен' : 'Неактивен'}</span>
                        </div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Позиция</label>
                        <div class="mt-1 text-sm text-gray-900">X: ${node.x}, Y: ${node.y}</div>
                    </div>
                </div>
                
                ${node.metadata ? `
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Дополнительная информация</label>
                        <div class="bg-gray-50 p-3 rounded-md">
                            ${Object.entries(node.metadata).map(([key, value]) => 
                                `<div class="flex justify-between py-1">
                                    <span class="text-sm text-gray-600">${key}:</span>
                                    <span class="text-sm text-gray-900">${value}</span>
                                </div>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <div class="flex space-x-2 pt-4">
                    <button class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors text-sm"
                            onclick="diagramManager.pingNode('${node.id}')">
                        <i class="fas fa-satellite-dish mr-1"></i>Пинг
                    </button>
                    <button class="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors text-sm"
                            onclick="diagramManager.openNodeConsole('${node.id}')">
                        <i class="fas fa-terminal mr-1"></i>Консоль
                    </button>
                    <button class="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors text-sm"
                            onclick="diagramManager.exportNodeInfo('${node.id}')">
                        <i class="fas fa-download mr-1"></i>Экспорт
                    </button>
                </div>
            </div>
        `;

        modal.classList.remove('hidden');
    }

    /**
     * Показ информации о ребре
     */
    showEdgeInfo(edge) {
        const modal = document.getElementById('elementModal');
        const modalTitle = document.getElementById('elementModalTitle');
        const modalContent = document.getElementById('elementModalContent');

        const fromNode = this.nodes.get(edge.from);
        const toNode = this.nodes.get(edge.to);

        modalTitle.textContent = `Соединение: ${fromNode.name} → ${toNode.name}`;
        modalContent.innerHTML = `
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Порт</label>
                        <div class="mt-1 text-sm text-gray-900">${edge.port}</div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Подсеть</label>
                        <div class="mt-1 text-sm text-gray-900">${edge.subnet}</div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Пропускная способность</label>
                        <div class="mt-1 text-sm text-gray-900">${edge.bandwidth}</div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Протокол</label>
                        <div class="mt-1 text-sm text-gray-900">${edge.protocol}</div>
                    </div>
                </div>
                
                <div class="flex space-x-2 pt-4">
                    <button class="px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors text-sm"
                            onclick="diagramManager.testConnection('${edge.id}')">
                        <i class="fas fa-plug mr-1"></i>Тест соединения
                    </button>
                    <button class="px-4 py-2 bg-purple-500 text-white rounded-md hover:bg-purple-600 transition-colors text-sm"
                            onclick="diagramManager.showTraffic('${edge.id}')">
                        <i class="fas fa-chart-line mr-1"></i>Трафик
                    </button>
                </div>
            </div>
        `;

        modal.classList.remove('hidden');
    }

    /**
     * Пинг узла
     */
    async pingNode(nodeId) {
        const node = this.nodes.get(nodeId);
        if (!node) return;

        this.app.showNotification('info', 'Пинг узла', `Отправка пинга на ${node.ip}...`);
        
        // Симуляция пинга
        setTimeout(() => {
            const success = Math.random() > 0.2; // 80% успешных пингов
            if (success) {
                this.app.showNotification('success', 'Пинг успешен', `Узел ${node.name} (${node.ip}) отвечает`);
            } else {
                this.app.showNotification('error', 'Пинг неудачен', `Узел ${node.name} (${node.ip}) не отвечает`);
            }
        }, 2000);
    }

    /**
     * Управление масштабом
     */
    zoomIn() {
        this.zoomLevel = Math.min(this.zoomLevel * 1.2, 3);
        this.applyZoom();
    }

    zoomOut() {
        this.zoomLevel = Math.max(this.zoomLevel / 1.2, 0.3);
        this.applyZoom();
    }

    fitToScreen() {
        this.zoomLevel = 1;
        this.applyZoom();
    }

    applyZoom() {
        const canvas = document.getElementById('diagramCanvas');
        if (this.useSvgFallback) {
            const svg = document.getElementById('diagramSvg');
            svg.style.transform = `scale(${this.zoomLevel})`;
        } else if (this.graph) {
            this.graph.getView().setScale(this.zoomLevel);
        }
    }

    /**
     * Показ диалога загрузки
     */
    showUploadDialog() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.drawio,.xml';
        
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                this.processDiagramFile(file);
            }
        };
        
        input.click();
    }

    /**
     * Обработка файла диаграммы
     */
    async processDiagramFile(file) {
        try {
            const text = await file.text();
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(text, 'text/xml');
            
            // Парсинг .drawio файла (упрощенная версия)
            const diagram = this.parseDrawioXml(xmlDoc, file.name);
            
            this.app.diagrams.push(diagram);
            this.populateDiagramList();
            
            this.app.showNotification('success', 'Диаграмма загружена', `Файл ${file.name} успешно обработан`);
            
        } catch (error) {
            console.error('Ошибка обработки файла:', error);
            this.app.showNotification('error', 'Ошибка загрузки', 'Не удалось обработать файл диаграммы');
        }
    }

    /**
     * Парсинг XML-файла .drawio (упрощенная версия)
     */
    parseDrawioXml(xmlDoc, filename) {
        // Базовая структура диаграммы
        const diagram = {
            id: Date.now(),
            name: filename.replace(/\.[^/.]+$/, ''),
            description: 'Загруженная диаграмма',
            uploadDate: new Date().toISOString().split('T')[0],
            nodes: [],
            edges: []
        };

        // В реальной реализации здесь был бы полноценный парсинг XML
        // Для демонстрации создаем простую диаграмму
        diagram.nodes.push({
            id: 'imported_node_1',
            type: 'server',
            name: 'Импортированный узел',
            ip: '192.168.1.50',
            status: 'online',
            x: 200,
            y: 150,
            metadata: {
                source: 'Импорт из ' + filename
            }
        });

        return diagram;
    }

    /**
     * Экспорт диаграммы
     */
    async exportDiagram() {
        if (!this.currentDiagram) {
            this.app.showNotification('warning', 'Нет диаграммы', 'Загрузите диаграмму для экспорта');
            return;
        }

        const exportData = {
            ...this.currentDiagram,
            exportDate: new Date().toISOString(),
            version: '1.0'
        };

        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `${this.currentDiagram.name.replace(/\s+/g, '_')}_export.json`;
        link.click();
        
        URL.revokeObjectURL(url);
        this.app.showNotification('success', 'Диаграмма экспортирована', 'Файл успешно сохранен');
    }

    /**
     * Обновление диаграммы (для WebSocket)
     */
    updateDiagram(diagramData) {
        if (!this.currentDiagram || this.currentDiagram.id !== diagramData.id) {
            return;
        }

        // Обновление данных узлов
        if (diagramData.nodes) {
            diagramData.nodes.forEach(updatedNode => {
                const existingNode = this.nodes.get(updatedNode.id);
                if (existingNode) {
                    Object.assign(existingNode, updatedNode);
                }
            });
        }

        // Перерисовка диаграммы
        if (this.useSvgFallback) {
            this.renderSvgDiagram();
        } else {
            this.renderMxGraphDiagram();
        }
    }

    /**
     * Изменение размера canvas
     */
    resize() {
        if (this.graph) {
            this.graph.refresh();
        }
    }
}

// Инициализация менеджера диаграмм
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        if (window.app) {
            window.diagramManager = new DiagramManager(window.app);
        }
    }, 100);
}); 