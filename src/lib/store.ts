import { create } from "zustand";

export interface QueryItem {
  id: string;
  text: string;
  timestamp: number;
}

interface QueryStore {
  history: QueryItem[];
  addQuery: (text: string) => void;
  clearHistory: () => void;
}

export const useQueryStore = create<QueryStore>((set) => ({
  history: [],

  addQuery: (text) =>
    set((state) => ({
      history: [
        {
          id: "q-" + crypto.randomUUID(),
          text,
          timestamp: Date.now(),
        },
        ...state.history,
      ],
    })),

  clearHistory: () => set({ history: [] }),
}));
