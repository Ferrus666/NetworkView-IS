import React, { createContext, useContext, ReactNode } from 'react'
import { createClient, SupabaseClient } from '@supabase/supabase-js'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://sfrijfmrmfkcnmwutfvs.supabase.co'
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmcmlqZm1ybWZrY25td3V0ZnZzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk0ODkwMDAsImV4cCI6MjA2NTA2NTAwMH0.mqT8Tvh57_mBC3Zu9TSG_-pQl7S_JmHvSb3gCU0R8i0'

// Создание клиента Supabase
const supabase: SupabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Интерфейс контекста
interface SupabaseContextType {
  supabase: SupabaseClient
}

// Создание контекста
const SupabaseContext = createContext<SupabaseContextType | undefined>(undefined)

// Провайдер контекста
interface SupabaseProviderProps {
  children: ReactNode
}

export const SupabaseProvider: React.FC<SupabaseProviderProps> = ({ children }) => {
  const value = {
    supabase
  }

  return (
    <SupabaseContext.Provider value={value}>
      {children}
    </SupabaseContext.Provider>
  )
}

// Хук для использования Supabase
export const useSupabase = (): SupabaseContextType => {
  const context = useContext(SupabaseContext)
  if (context === undefined) {
    throw new Error('useSupabase must be used within a SupabaseProvider')
  }
  return context
}

export { supabase }
export default SupabaseContext 