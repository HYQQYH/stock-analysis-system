import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ModalState {
  visible: boolean;
  type: string | null;
  data: unknown;
  openModal: (type: string, data?: unknown) => void;
  closeModal: () => void;
}

export const useModalStore = create<ModalState>()(
  persist(
    (set) => ({
      visible: false,
      type: null,
      data: null,
      
      openModal: (type, data = null) => set({ visible: true, type, data }),
      closeModal: () => set({ visible: false, type: null, data: null }),
    }),
    {
      name: 'modal-storage',
      partialize: () => ({}),
    }
  )
);

interface ToastState {
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  visible: boolean;
  showToast: (message: string, type: ToastState['type']) => void;
  hideToast: () => void;
}

export const useToastStore = create<ToastState>()(
  persist(
    (set) => ({
      message: '',
      type: 'info',
      visible: false,
      
      showToast: (message, type = 'info') => {
        set({ message, type, visible: true });
        setTimeout(() => set({ visible: false }), 3000);
      },
      
      hideToast: () => set({ visible: false }),
    }),
    {
      name: 'toast-storage',
      partialize: () => ({}),
    }
  )
);

interface LoadingState {
  globalLoading: boolean;
  analysisLoading: boolean;
  dataLoading: boolean;
  marketLoading: boolean;
  newsLoading: boolean;
  
  setGlobalLoading: (loading: boolean) => void;
  setAnalysisLoading: (loading: boolean) => void;
  setDataLoading: (loading: boolean) => void;
  setMarketLoading: (loading: boolean) => void;
  setNewsLoading: (loading: boolean) => void;
  resetLoading: () => void;
}

export const useLoadingStore = create<LoadingState>()(
  persist(
    (set) => ({
      globalLoading: false,
      analysisLoading: false,
      dataLoading: false,
      marketLoading: false,
      newsLoading: false,
      
      setGlobalLoading: (loading) => set({ globalLoading: loading }),
      setAnalysisLoading: (loading) => set({ analysisLoading: loading }),
      setDataLoading: (loading) => set({ dataLoading: loading }),
      setMarketLoading: (loading) => set({ marketLoading: loading }),
      setNewsLoading: (loading) => set({ newsLoading: loading }),
      
      resetLoading: () => set({
        globalLoading: false,
        analysisLoading: false,
        dataLoading: false,
        marketLoading: false,
        newsLoading: false,
      }),
    }),
    {
      name: 'loading-storage',
      partialize: () => ({}),
    }
  )
);

interface ThemeState {
  theme: 'light' | 'dark';
  primaryColor: string;
  
  setTheme: (theme: 'light' | 'dark') => void;
  setPrimaryColor: (color: string) => void;
  toggleTheme: () => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'light',
      primaryColor: '#1890ff',
      
      setTheme: (theme) => set({ theme }),
      setPrimaryColor: (color) => set({ primaryColor: color }),
      toggleTheme: () => set((state) => ({
        theme: state.theme === 'light' ? 'dark' : 'light',
      })),
    }),
    {
      name: 'theme-storage',
    }
  )
);
