import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface NewsItem {
  id: string;
  title: string;
  content?: string;
  source: string;
  publishTime: string;
  relatedStocks?: string[];
}

interface NewsState {
  newsList: NewsItem[];
  favorites: string[];
  
  setNewsList: (news: NewsItem[]) => void;
  addToFavorites: (id: string) => void;
  removeFromFavorites: (id: string) => void;
  clearNews: () => void;
}

export const useNewsStore = create<NewsState>()(
  persist(
    (set) => ({
      newsList: [],
      favorites: [],
      
      setNewsList: (news) => set({ newsList: news }),
      
      addToFavorites: (id) => set((state) => ({
        favorites: state.favorites.includes(id) 
          ? state.favorites 
          : [...state.favorites, id]
      })),
      
      removeFromFavorites: (id) => set((state) => ({
        favorites: state.favorites.filter((fid) => fid !== id)
      })),
      
      clearNews: () => set({ newsList: [] }),
    }),
    {
      name: 'news-storage',
    }
  )
);
