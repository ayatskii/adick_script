import React, { createContext, useContext } from 'react'
import type { ScreenProps } from './types'

export const AppContext = createContext<ScreenProps | null>(null)

export function useApp(): ScreenProps {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used inside AppContext.Provider')
  return ctx
}
