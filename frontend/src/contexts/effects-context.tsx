'use client'

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'

export type EffectType =
  | 'boot'
  | 'hacker'
  | 'drunk'
  | 'redacted'
  | 'crt'
  | 'dvd'
  | 'binary'
  | 'glitch'
  | 'beatSync'
  | 'beatSyncLite'
  | 'phosphor'
  | 'flicker'
  | 'noise'
  | 'interlace'

export type AnalyzerStatus = 'idle' | 'requesting' | 'listening' | 'synced' | 'error'

export interface BeatState {
  bpm: number
  status: AnalyzerStatus
  confidence: number
  errorMessage?: string
}

interface EffectsContextType {
  // Hydration state (true once localStorage is loaded)
  hydrated: boolean

  // Individual effects
  enabledEffects: Set<EffectType>
  toggleEffect: (effect: EffectType) => void
  isEffectEnabled: (effect: EffectType) => boolean
  disableAllEffects: () => void

  // Effect intensity (0-100)
  effectIntensities: Record<EffectType, number>
  getEffectIntensity: (effect: EffectType) => number
  setEffectIntensity: (effect: EffectType, intensity: number) => void

  // Boot sequence
  bootComplete: boolean
  setBootComplete: (complete: boolean) => void

  // Settings panel
  settingsPanelOpen: boolean
  setSettingsPanelOpen: (open: boolean) => void

  // Marquee toggles
  stockMarqueeEnabled: boolean
  setStockMarqueeEnabled: (enabled: boolean) => void
  headlinesMarqueeEnabled: boolean
  setHeadlinesMarqueeEnabled: (enabled: boolean) => void

  // Marquee position
  stockMarqueePosition: 'top' | 'bottom'
  setStockMarqueePosition: (position: 'top' | 'bottom') => void
  headlinesMarqueePosition: 'top' | 'bottom'
  setHeadlinesMarqueePosition: (position: 'top' | 'bottom') => void

  // Marquee scroll speed (multiplier: 1 = normal, 2 = 2x faster, 0.5 = 2x slower)
  marqueeScrollSpeed: number
  setMarqueeScrollSpeed: (speed: number) => void

  // Kiosk mode (larger text/elements for overhead displays)
  kioskMode: boolean
  setKioskMode: (enabled: boolean) => void

  // Beat sync state
  beatState: BeatState
  setBeatState: (state: BeatState) => void

  // Reset on error
  resetEffects: () => void
}

const EffectsContext = createContext<EffectsContextType | null>(null)

const STORAGE_KEY = 'smg-effects-settings'

const DEFAULT_INTENSITY = 50

const DEFAULT_INTENSITIES: Record<EffectType, number> = {
  boot: DEFAULT_INTENSITY,
  hacker: DEFAULT_INTENSITY,
  drunk: DEFAULT_INTENSITY,
  redacted: DEFAULT_INTENSITY,
  crt: DEFAULT_INTENSITY,
  dvd: DEFAULT_INTENSITY,
  binary: DEFAULT_INTENSITY,
  glitch: DEFAULT_INTENSITY,
  beatSync: DEFAULT_INTENSITY,
  beatSyncLite: DEFAULT_INTENSITY,
  phosphor: DEFAULT_INTENSITY,
  flicker: DEFAULT_INTENSITY,
  noise: DEFAULT_INTENSITY,
  interlace: DEFAULT_INTENSITY,
}

interface StoredSettings {
  enabledEffects: EffectType[]
  effectIntensities?: Partial<Record<EffectType, number>>
  stockMarqueeEnabled?: boolean
  headlinesMarqueeEnabled?: boolean
  stockMarqueePosition?: 'top' | 'bottom'
  headlinesMarqueePosition?: 'top' | 'bottom'
  marqueeScrollSpeed?: number
  kioskMode?: boolean
}

export function EffectsProvider({ children }: { children: React.ReactNode }) {
  const [enabledEffects, setEnabledEffects] = useState<Set<EffectType>>(new Set(['boot']))
  const [effectIntensities, setEffectIntensities] = useState<Record<EffectType, number>>(DEFAULT_INTENSITIES)
  const [bootComplete, setBootComplete] = useState(false)
  const [settingsPanelOpen, setSettingsPanelOpen] = useState(false)
  const [stockMarqueeEnabled, setStockMarqueeEnabled] = useState(false)
  const [headlinesMarqueeEnabled, setHeadlinesMarqueeEnabled] = useState(false)
  const [stockMarqueePosition, setStockMarqueePosition] = useState<'top' | 'bottom'>('top')
  const [headlinesMarqueePosition, setHeadlinesMarqueePosition] = useState<'top' | 'bottom'>('bottom')
  const [marqueeScrollSpeed, setMarqueeScrollSpeed] = useState(1)
  const [kioskMode, setKioskMode] = useState(true)
  const [beatState, setBeatState] = useState<BeatState>({
    bpm: 0,
    status: 'idle',
    confidence: 0,
  })
  const [hydrated, setHydrated] = useState(false)

  // Load settings from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const settings: StoredSettings = JSON.parse(stored)
        setEnabledEffects(new Set(settings.enabledEffects))
        if (settings.effectIntensities) {
          setEffectIntensities({ ...DEFAULT_INTENSITIES, ...settings.effectIntensities })
        }
        if (settings.stockMarqueeEnabled !== undefined) {
          setStockMarqueeEnabled(settings.stockMarqueeEnabled)
        }
        if (settings.headlinesMarqueeEnabled !== undefined) {
          setHeadlinesMarqueeEnabled(settings.headlinesMarqueeEnabled)
        }
        if (settings.stockMarqueePosition !== undefined) {
          setStockMarqueePosition(settings.stockMarqueePosition)
        }
        if (settings.headlinesMarqueePosition !== undefined) {
          setHeadlinesMarqueePosition(settings.headlinesMarqueePosition)
        }
        if (settings.marqueeScrollSpeed !== undefined) {
          setMarqueeScrollSpeed(settings.marqueeScrollSpeed)
        }
        if (settings.kioskMode !== undefined) {
          setKioskMode(settings.kioskMode)
        }
      }
    } catch {
      // Ignore localStorage errors
    }
    setHydrated(true)
  }, [])

  // Save settings to localStorage when they change
  useEffect(() => {
    if (!hydrated) return
    try {
      const settings: StoredSettings = {
        enabledEffects: Array.from(enabledEffects),
        effectIntensities,
        stockMarqueeEnabled,
        headlinesMarqueeEnabled,
        stockMarqueePosition,
        headlinesMarqueePosition,
        marqueeScrollSpeed,
        kioskMode,
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
    } catch {
      // Ignore localStorage errors
    }
  }, [enabledEffects, effectIntensities, stockMarqueeEnabled, headlinesMarqueeEnabled, stockMarqueePosition, headlinesMarqueePosition, marqueeScrollSpeed, kioskMode, hydrated])

  // Keyboard shortcut: Ctrl/Cmd + Shift + E
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'e') {
        e.preventDefault()
        setSettingsPanelOpen((prev) => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const toggleEffect = useCallback((effect: EffectType) => {
    setEnabledEffects((prev) => {
      const next = new Set(prev)
      if (next.has(effect)) {
        next.delete(effect)
      } else {
        next.add(effect)
      }
      return next
    })
  }, [])

  const isEffectEnabled = useCallback(
    (effect: EffectType) => {
      return enabledEffects.has(effect)
    },
    [enabledEffects]
  )

  const disableAllEffects = useCallback(() => {
    setEnabledEffects(new Set())
  }, [])

  const getEffectIntensity = useCallback(
    (effect: EffectType) => {
      return effectIntensities[effect] ?? DEFAULT_INTENSITY
    },
    [effectIntensities]
  )

  const setEffectIntensity = useCallback((effect: EffectType, intensity: number) => {
    setEffectIntensities((prev) => ({
      ...prev,
      [effect]: Math.max(0, Math.min(100, intensity)),
    }))
  }, [])

  const resetEffects = useCallback(() => {
    setEnabledEffects(new Set())
    setEffectIntensities(DEFAULT_INTENSITIES)
  }, [])

  return (
    <EffectsContext.Provider
      value={{
        hydrated,
        enabledEffects,
        toggleEffect,
        isEffectEnabled,
        disableAllEffects,
        effectIntensities,
        getEffectIntensity,
        setEffectIntensity,
        bootComplete,
        setBootComplete,
        settingsPanelOpen,
        setSettingsPanelOpen,
        stockMarqueeEnabled,
        setStockMarqueeEnabled,
        headlinesMarqueeEnabled,
        setHeadlinesMarqueeEnabled,
        stockMarqueePosition,
        setStockMarqueePosition,
        headlinesMarqueePosition,
        setHeadlinesMarqueePosition,
        marqueeScrollSpeed,
        setMarqueeScrollSpeed,
        kioskMode,
        setKioskMode,
        beatState,
        setBeatState,
        resetEffects,
      }}
    >
      {children}
    </EffectsContext.Provider>
  )
}

export function useEffects() {
  const context = useContext(EffectsContext)
  if (!context) {
    throw new Error('useEffects must be used within an EffectsProvider')
  }
  return context
}
