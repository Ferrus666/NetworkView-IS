import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  InputAdornment,
  IconButton,
  Divider,
  CircularProgress
} from '@mui/material'
import {
  Visibility,
  VisibilityOff,
  Email,
  Lock,
  Security
} from '@mui/icons-material'
import { useForm, Controller } from 'react-hook-form'
import { yupResolver } from '@hookform/resolvers/yup'
import * as yup from 'yup'

import { useAuth } from '../../contexts/AuthContext'

// Схема валидации
const loginSchema = yup.object({
  email: yup
    .string()
    .email('Введите корректный email')
    .required('Email обязателен'),
  password: yup
    .string()
    .min(6, 'Пароль должен содержать минимум 6 символов')
    .required('Пароль обязателен')
})

interface LoginFormData {
  email: string
  password: string
}

const LoginPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const { login } = useAuth()
  const navigate = useNavigate()

  const {
    control,
    handleSubmit,
    formState: { errors, isValid }
  } = useForm<LoginFormData>({
    resolver: yupResolver(loginSchema),
    mode: 'onChange'
  })

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true)
    setError(null)

    try {
      const success = await login(data.email, data.password)
      if (success) {
        navigate('/dashboard')
      }
    } catch (err: any) {
      setError(err.message || 'Ошибка входа в систему')
    } finally {
      setIsLoading(false)
    }
  }

  const handleTogglePassword = () => {
    setShowPassword(!showPassword)
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #D32F2F 0%, #B71C1C 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 2
      }}
    >
      <Container maxWidth="sm">
        <Card
          sx={{
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
            overflow: 'hidden'
          }}
        >
          {/* Заголовок */}
          <Box
            sx={{
              background: 'linear-gradient(135deg, #FFFFFF 0%, #F5F5F5 100%)',
              padding: 4,
              textAlign: 'center',
              borderBottom: '1px solid #E0E0E0'
            }}
          >
            <Security 
              sx={{ 
                fontSize: 48, 
                color: '#D32F2F', 
                mb: 2 
              }} 
            />
            <Typography 
              variant="h4" 
              component="h1" 
              sx={{ 
                fontWeight: 700, 
                color: '#D32F2F',
                mb: 1 
              }}
            >
              Банк БМК
            </Typography>
            <Typography 
              variant="h6" 
              sx={{ 
                color: '#424242',
                fontWeight: 500 
              }}
            >
              Личный кабинет инженера ИБ
            </Typography>
          </Box>

          <CardContent sx={{ padding: 4 }}>
            {/* Сообщение об ошибке */}
            {error && (
              <Alert 
                severity="error" 
                sx={{ mb: 3 }}
                onClose={() => setError(null)}
              >
                {error}
              </Alert>
            )}

            {/* Форма входа */}
            <Box 
              component="form" 
              onSubmit={handleSubmit(onSubmit)}
              noValidate
            >
              {/* Email */}
              <Controller
                name="email"
                control={control}
                defaultValue=""
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Email"
                    type="email"
                    autoComplete="email"
                    autoFocus
                    error={!!errors.email}
                    helperText={errors.email?.message}
                    sx={{ mb: 3 }}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Email sx={{ color: '#D32F2F' }} />
                        </InputAdornment>
                      )
                    }}
                  />
                )}
              />

              {/* Пароль */}
              <Controller
                name="password"
                control={control}
                defaultValue=""
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Пароль"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    error={!!errors.password}
                    helperText={errors.password?.message}
                    sx={{ mb: 3 }}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Lock sx={{ color: '#D32F2F' }} />
                        </InputAdornment>
                      ),
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={handleTogglePassword}
                            edge="end"
                            aria-label="toggle password visibility"
                          >
                            {showPassword ? <VisibilityOff /> : <Visibility />}
                          </IconButton>
                        </InputAdornment>
                      )
                    }}
                  />
                )}
              />

              {/* Кнопка входа */}
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={!isValid || isLoading}
                sx={{
                  mb: 3,
                  height: 56,
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  textTransform: 'none'
                }}
              >
                {isLoading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  'Войти в систему'
                )}
              </Button>

              {/* Разделитель */}
              <Divider sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  или
                </Typography>
              </Divider>

              {/* Ссылка на регистрацию */}
              <Box textAlign="center">
                <Typography variant="body2" color="text.secondary">
                  Нет аккаунта?{' '}
                  <Link 
                    to="/register"
                    style={{
                      color: '#D32F2F',
                      textDecoration: 'none',
                      fontWeight: 600
                    }}
                  >
                    Зарегистрироваться
                  </Link>
                </Typography>
              </Box>
            </Box>
          </CardContent>

          {/* Футер */}
          <Box
            sx={{
              background: '#F5F5F5',
              padding: 2,
              textAlign: 'center',
              borderTop: '1px solid #E0E0E0'
            }}
          >
            <Typography variant="caption" color="text.secondary">
              © 2024 Банк БМК. Система информационной безопасности v2.0
            </Typography>
          </Box>
        </Card>
      </Container>
    </Box>
  )
}

export default LoginPage 