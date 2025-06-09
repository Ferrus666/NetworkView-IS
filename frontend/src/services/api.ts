import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios'
import { toast } from 'react-toastify'

// Базовый URL API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Создание экземпляра axios
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Интерсептор для обработки ответов
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error: AxiosError) => {
    // Обработка ошибок аутентификации
    if (error.response?.status === 401) {
      // Удаляем токен и перенаправляем на страницу входа
      localStorage.removeItem('bmk_token')
      delete apiClient.defaults.headers.common['Authorization']
      
      // Перенаправление на страницу входа (можно использовать router)
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    
    // Обработка ошибок сервера
    if (error.response?.status === 500) {
      toast.error('Ошибка сервера. Попробуйте позже.')
    }
    
    // Обработка ошибок сети
    if (!error.response) {
      toast.error('Ошибка сети. Проверьте подключение к интернету.')
    }
    
    return Promise.reject(error)
  }
)

// Интерсептор для добавления токена к запросам
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('bmk_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Интерфейсы для API ответов
export interface ApiResponse<T = any> {
  data: T
  message?: string
  status: string
}

export interface PaginatedResponse<T = any> {
  data: T[]
  total: number
  page: number
  limit: number
  has_next: boolean
  has_prev: boolean
}

// Сервис для работы с документами
export const documentsApi = {
  // Получение списка документов
  getDocuments: (params?: {
    limit?: number
    offset?: number
    category?: string
    status?: string
    search?: string
  }) => apiClient.get('/api/documents/', { params }),

  // Получение документа по ID
  getDocument: (id: string) => apiClient.get(`/api/documents/${id}`),

  // Загрузка документа
  uploadDocument: (formData: FormData) => 
    apiClient.post('/api/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  // Обновление документа
  updateDocument: (id: string, data: any) => 
    apiClient.put(`/api/documents/${id}`, data),

  // Удаление документа
  deleteDocument: (id: string) => apiClient.delete(`/api/documents/${id}`),

  // Скачивание документа
  downloadDocument: (id: string) => 
    apiClient.get(`/api/documents/${id}/download`, { responseType: 'blob' }),

  // Поиск документов
  searchDocuments: (searchData: any) => 
    apiClient.post('/api/documents/search', searchData),

  // Получение категорий
  getCategories: () => apiClient.get('/api/documents/categories/list'),

  // Получение статистики
  getStats: () => apiClient.get('/api/documents/stats/summary')
}

// Сервис для работы с SAST
export const sastApi = {
  // Запуск анализа загруженного файла
  scanUploadedFile: (formData: FormData) =>
    apiClient.post('/api/sast/scan/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  // Запуск анализа репозитория
  scanRepository: (data: any) => apiClient.post('/api/sast/scan/repository', data),

  // Получение результата анализа
  getScanResult: (scanId: string) => apiClient.get(`/api/sast/results/${scanId}`),

  // Получение списка результатов
  getScanResults: (params?: { limit?: number; offset?: number; status?: string }) =>
    apiClient.get('/api/sast/results', { params }),

  // Удаление результата
  deleteScanResult: (scanId: string) => apiClient.delete(`/api/sast/results/${scanId}`),

  // Получение поддерживаемых языков
  getSupportedLanguages: () => apiClient.get('/api/sast/languages')
}

// Сервис для работы с мониторингом
export const monitoringApi = {
  // Получение статуса устройств
  getDeviceStatuses: () => apiClient.get('/api/monitoring/devices'),

  // Получение статуса конкретного устройства
  getDeviceStatus: (deviceId: string) => 
    apiClient.get(`/api/monitoring/devices/${deviceId}`),

  // Получение общих метрик сети
  getNetworkMetrics: () => apiClient.get('/api/monitoring/metrics/overview'),

  // Получение логов мониторинга
  getMonitoringLogs: (params?: {
    limit?: number
    offset?: number
    device_id?: string
    alert_level?: string
  }) => apiClient.get('/api/monitoring/logs', { params }),

  // Создание записи в логах
  createMonitoringLog: (data: any) => apiClient.post('/api/monitoring/logs', data),

  // Получение исторических метрик устройства
  getDeviceMetricsHistory: (deviceId: string, period: string = '1h') =>
    apiClient.get(`/api/monitoring/devices/${deviceId}/metrics/history`, {
      params: { period }
    }),

  // Получение предупреждений
  getAlerts: (params?: {
    limit?: number
    offset?: number
    status?: string
    severity?: string
  }) => apiClient.get('/api/monitoring/alerts', { params }),

  // Подтверждение предупреждения
  acknowledgeAlert: (alertId: string) =>
    apiClient.put(`/api/monitoring/alerts/${alertId}/acknowledge`)
}

// Сервис для работы с сетью
export const networkApi = {
  // Получение топологии сети
  getNetworkTopology: () => apiClient.get('/api/network/topology'),

  // Создание аннотации
  createAnnotation: (data: any) => apiClient.post('/api/network/annotations', data),

  // Получение аннотаций
  getAnnotations: () => apiClient.get('/api/network/annotations'),

  // Импорт схемы draw.io
  importDrawio: (formData: FormData) =>
    apiClient.post('/api/network/import/drawio', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
}

// Сервис для работы с интеграциями
export const integrationsApi = {
  // Получение списка интеграций
  getIntegrations: () => apiClient.get('/api/integrations/'),

  // Тестирование интеграции
  testIntegration: (config: any) => apiClient.post('/api/integrations/test', config),

  // Синхронизация интеграции
  syncIntegration: (integrationId: string) =>
    apiClient.post(`/api/integrations/sync/${integrationId}`)
}

// Сервис для работы с пользователями
export const userApi = {
  // Получение профиля пользователя
  getProfile: () => apiClient.get('/api/user/profile'),

  // Обновление профиля
  updateProfile: (data: any) => apiClient.put('/api/user/profile', data)
}

// WebSocket для real-time мониторинга
export class MonitoringWebSocket {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(private onMessage: (data: any) => void) {}

  connect() {
    const wsUrl = (API_BASE_URL.replace('http', 'ws')) + '/ws/monitoring'
    
    try {
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.onMessage(data)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.attemptReconnect()
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
        this.connect()
      }, this.reconnectDelay * this.reconnectAttempts)
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
}

export default apiClient 