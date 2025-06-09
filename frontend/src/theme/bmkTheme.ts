import { createTheme } from '@mui/material/styles'

// Цветовая палитра банка БМК
const BMK_COLORS = {
  primary: {
    main: '#D32F2F',
    light: '#FF6659',
    dark: '#B71C1C',
    contrastText: '#FFFFFF'
  },
  secondary: {
    main: '#B71C1C',
    light: '#E57373',
    dark: '#7F0000',
    contrastText: '#FFFFFF'
  },
  background: {
    default: '#FFFFFF',
    paper: '#F5F5F5'
  },
  text: {
    primary: '#424242',
    secondary: '#757575'
  },
  success: {
    main: '#4CAF50',
    light: '#81C784',
    dark: '#388E3C'
  },
  warning: {
    main: '#FF9800',
    light: '#FFB74D',
    dark: '#F57C00'
  },
  error: {
    main: '#F44336',
    light: '#E57373',
    dark: '#D32F2F'
  },
  info: {
    main: '#2196F3',
    light: '#64B5F6',
    dark: '#1976D2'
  }
}

export const bmkTheme = createTheme({
  palette: {
    mode: 'light',
    primary: BMK_COLORS.primary,
    secondary: BMK_COLORS.secondary,
    background: BMK_COLORS.background,
    text: BMK_COLORS.text,
    success: BMK_COLORS.success,
    warning: BMK_COLORS.warning,
    error: BMK_COLORS.error,
    info: BMK_COLORS.info,
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      color: BMK_COLORS.primary.main,
      lineHeight: 1.2
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      color: BMK_COLORS.primary.main,
      lineHeight: 1.3
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      color: BMK_COLORS.text.primary,
      lineHeight: 1.4
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 500,
      color: BMK_COLORS.text.primary,
      lineHeight: 1.4
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
      color: BMK_COLORS.text.primary,
      lineHeight: 1.5
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
      color: BMK_COLORS.text.primary,
      lineHeight: 1.5
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
      color: BMK_COLORS.text.primary
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
      color: BMK_COLORS.text.secondary
    },
    button: {
      fontWeight: 600,
      textTransform: 'none' as const,
      fontSize: '0.875rem'
    }
  },
  shape: {
    borderRadius: 8
  },
  spacing: 8,
  components: {
    // Кнопки
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 24px',
          fontWeight: 600,
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-1px)',
            boxShadow: '0 4px 8px rgba(211, 47, 47, 0.2)'
          }
        },
        contained: {
          backgroundColor: BMK_COLORS.primary.main,
          color: '#FFFFFF',
          boxShadow: '0 2px 4px rgba(211, 47, 47, 0.2)',
          '&:hover': {
            backgroundColor: BMK_COLORS.primary.dark,
            boxShadow: '0 4px 8px rgba(211, 47, 47, 0.3)'
          }
        },
        outlined: {
          borderColor: BMK_COLORS.primary.main,
          color: BMK_COLORS.primary.main,
          borderWidth: 2,
          '&:hover': {
            borderColor: BMK_COLORS.primary.dark,
            backgroundColor: 'rgba(211, 47, 47, 0.04)'
          }
        }
      }
    },
    // AppBar
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: BMK_COLORS.primary.main,
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }
      }
    },
    // Карточки
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          border: '1px solid #E0E0E0',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
            transform: 'translateY(-2px)'
          }
        }
      }
    },
    // Заголовки карточек
    MuiCardHeader: {
      styleOverrides: {
        root: {
          backgroundColor: BMK_COLORS.background.paper,
          borderBottom: `1px solid #E0E0E0`
        },
        title: {
          color: BMK_COLORS.primary.main,
          fontWeight: 600
        }
      }
    },
    // Поля ввода
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: BMK_COLORS.primary.main
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: BMK_COLORS.primary.main,
              borderWidth: 2
            }
          },
          '& .MuiInputLabel-root.Mui-focused': {
            color: BMK_COLORS.primary.main
          }
        }
      }
    },
    // Чипы
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          fontWeight: 500
        },
        filled: {
          backgroundColor: BMK_COLORS.primary.main,
          color: '#FFFFFF',
          '&:hover': {
            backgroundColor: BMK_COLORS.primary.dark
          }
        },
        outlined: {
          borderColor: BMK_COLORS.primary.main,
          color: BMK_COLORS.primary.main,
          '&:hover': {
            backgroundColor: 'rgba(211, 47, 47, 0.04)'
          }
        }
      }
    },
    // Прогресс-бары
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          backgroundColor: '#E0E0E0'
        },
        bar: {
          backgroundColor: BMK_COLORS.primary.main
        }
      }
    },
    // Табы
    MuiTabs: {
      styleOverrides: {
        root: {
          '& .MuiTab-root': {
            textTransform: 'none',
            fontWeight: 500,
            fontSize: '1rem',
            '&.Mui-selected': {
              color: BMK_COLORS.primary.main,
              fontWeight: 600
            }
          },
          '& .MuiTabs-indicator': {
            backgroundColor: BMK_COLORS.primary.main,
            height: 3
          }
        }
      }
    },
    // Drawers/боковые панели
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#FAFAFA',
          borderRight: `1px solid #E0E0E0`
        }
      }
    },
    // Списки
    MuiListItem: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          margin: '2px 8px',
          '&:hover': {
            backgroundColor: 'rgba(211, 47, 47, 0.04)'
          },
          '&.Mui-selected': {
            backgroundColor: 'rgba(211, 47, 47, 0.08)',
            '&:hover': {
              backgroundColor: 'rgba(211, 47, 47, 0.12)'
            },
            '& .MuiListItemIcon-root': {
              color: BMK_COLORS.primary.main
            },
            '& .MuiListItemText-primary': {
              color: BMK_COLORS.primary.main,
              fontWeight: 600
            }
          }
        }
      }
    },
    // Иконки списков
    MuiListItemIcon: {
      styleOverrides: {
        root: {
          color: BMK_COLORS.text.secondary,
          minWidth: 40
        }
      }
    },
    // Таблицы
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: BMK_COLORS.background.paper,
          '& .MuiTableCell-head': {
            color: BMK_COLORS.primary.main,
            fontWeight: 600,
            borderBottom: `2px solid ${BMK_COLORS.primary.main}`
          }
        }
      }
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: 'rgba(211, 47, 47, 0.02)'
          }
        }
      }
    },
    // Снэкбары/уведомления
    MuiSnackbar: {
      styleOverrides: {
        root: {
          '& .MuiSnackbarContent-root': {
            backgroundColor: BMK_COLORS.primary.main,
            color: '#FFFFFF'
          }
        }
      }
    },
    // Диалоги
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 12,
          padding: '8px'
        }
      }
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          color: BMK_COLORS.primary.main,
          fontWeight: 600,
          borderBottom: `1px solid #E0E0E0`,
          paddingBottom: 16
        }
      }
    }
  }
})

export default bmkTheme 