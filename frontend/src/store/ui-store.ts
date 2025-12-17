import { create } from 'zustand';
import { UIState } from '@/types';

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  currentSession: null,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setCurrentSession: (sessionId) => set({ currentSession: sessionId }),
}));
