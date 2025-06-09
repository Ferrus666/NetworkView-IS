import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react'
import { toast } from 'react-toastify'
import { apiClient } from '../services/api'

// Типы для пользователя
interface User {
  id: string
  username: string
  email: string
  role: string
  is_active: boolean
  created_at: string
}

// Состояние аутентификации
interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
}

// Действия для reducer
type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; token: string } }
  | { type: 'LOGIN_FAILURE' }
  | { type: 'LOGOUT' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'UPDATE_USER'; payload: User }

// Интерфейс контекста
interface AuthContextType {
  state: AuthState
  login: (email: string, password: string) => Promise<boolean>
  logout: () => void
  register: (userData: RegisterData) => Promise<boolean>
  updateProfile: (userData: Partial<User>) => Promise<boolean>
  changePassword: (currentPassword: string, newPassword: string) => Promise<boolean>
}

// Данные для регистрации
interface RegisterData {
  username: string
  email: string
  password: string
  role?: string
}

// Начальное состояние
const initialState: AuthState = {
  user: null,
  token: null,
  isLoading: true,
  isAuthenticated: false
}

// Reducer для управления состоянием
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'LOGIN_START':
      return {
        ...state,
        isLoading: true
      }
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isLoading: false,
        isAuthenticated: true
      }
    case 'LOGIN_FAILURE':
      return {
        ...state,
        user: null,
        token: null,
        isLoading: false,
        isAuthenticated: false
      }
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false
      }
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload
      }
    case 'UPDATE_USER':
      return {
        ...state,
        user: action.payload
      }
    default:
      return state
  }
}

// Создание контекста
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Провайдер контекста
interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState)

  // Функция входа
  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      dispatch({ type: 'LOGIN_START' })

      const formData = new FormData()
      formData.append('username', email)
      formData.append('password', password)

      const response = await apiClient.post('/auth/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })

      const { access_token } = response.data

      // Сохранение токена
      localStorage.setItem('bmk_token', access_token)
      
      // Установка токена в axios
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

      // Получение информации о пользователе
      const userResponse = await apiClient.get('/auth/me')
      const user = userResponse.data

      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: { user, token: access_token }
      })

      toast.success('Вход выполнен успешно!')
      return true

    } catch (error: any) {
      dispatch({ type: 'LOGIN_FAILURE' })
      
      const errorMessage = error.response?.data?.detail || 'Ошибка входа'
      toast.error(errorMessage)
      
      return false
    }
  }

  // Функция выхода
  const logout = async (): Promise<void> => {
    try {
      // Отправка запроса на выход (если токен еще действителен)
      if (state.token) {
        await apiClient.post('/auth/logout')
      }
    } catch (error) {
      // Игнорируем ошибки при выходе
    } finally {
      // Очистка локального состояния
      localStorage.removeItem('bmk_token')
      delete apiClient.defaults.headers.common['Authorization']
      dispatch({ type: 'LOGOUT' })
      toast.info('Выход выполнен')
    }
  }

  // Функция регистрации
  const register = async (userData: RegisterData): Promise<boolean> => {
    try {
      await apiClient.post('/auth/register', userData)
      toast.success('Регистрация выполнена успешно! Теперь вы можете войти.')
      return true
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Ошибка регистрации'
      toast.error(errorMessage)
      return false
    }
  }

  // Функция обновления профиля
  const updateProfile = async (userData: Partial<User>): Promise<boolean> => {
    try {
      const response = await apiClient.put('/api/user/profile', userData)
      const updatedUser = response.data
      
      dispatch({ type: 'UPDATE_USER', payload: updatedUser })
      toast.success('Профиль обновлен успешно!')
      return true
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Ошибка обновления профиля'
      toast.error(errorMessage)
      return false
    }
  }

  // Функция смены пароля
  const changePassword = async (currentPassword: string, newPassword: string): Promise<boolean> => {
    try {
      await apiClient.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword
      })
      toast.success('Пароль изменен успешно!')
      return true
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Ошибка смены пароля'
      toast.error(errorMessage)
      return false
    }
  }

  // Проверка токена при загрузке
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('bmk_token')
      
      if (token) {
        try {
          // Установка токена в axios
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
          
          // Проверка валидности токена
          const response = await apiClient.get('/auth/me')
          const user = response.data

          dispatch({
            type: 'LOGIN_SUCCESS',
            payload: { user, token }
          })
        } catch (error) {
          // Токен невалиден, очищаем
          localStorage.removeItem('bmk_token')
          delete apiClient.defaults.headers.common['Authorization']
          dispatch({ type: 'LOGIN_FAILURE' })
        }
      } else {
        dispatch({ type: 'SET_LOADING', payload: false })
      }
    }

    checkAuth()
  }, [])

  const value: AuthContextType = {
    state,
    login,
    logout,
    register,
    updateProfile,
    changePassword
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// Хук для использования аутентификации
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export type { User, AuthState, RegisterData }
export default AuthContext 