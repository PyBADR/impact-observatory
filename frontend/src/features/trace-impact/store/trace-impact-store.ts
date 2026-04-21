"use client";

import { create } from "zustand";

export const TOTAL_STEPS = 6;

interface TraceImpactState {
  stepIndex: number;
  isPlaying: boolean;
  setStep: (index: number) => void;
  next: () => void;
  prev: () => void;
  reset: () => void;
  togglePlay: () => void;
}

export const useTraceImpactStore = create<TraceImpactState>()((set, get) => ({
  stepIndex: 0,
  isPlaying: false,

  setStep: (index) =>
    set({ stepIndex: Math.max(0, Math.min(TOTAL_STEPS - 1, index)) }),

  next: () => {
    const { stepIndex } = get();
    if (stepIndex < TOTAL_STEPS - 1) set({ stepIndex: stepIndex + 1 });
  },

  prev: () => {
    const { stepIndex } = get();
    if (stepIndex > 0) set({ stepIndex: stepIndex - 1 });
  },

  reset: () => set({ stepIndex: 0, isPlaying: false }),

  togglePlay: () => set((s) => ({ isPlaying: !s.isPlaying })),
}));
