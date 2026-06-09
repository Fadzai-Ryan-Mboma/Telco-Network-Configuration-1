import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import Dashboard from './pages/Dashboard';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000,
    },
  },
});

export type ThemeMode = 'dark' | 'light';

function App() {
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const savedTheme = localStorage.getItem('netgenix-theme');
    return savedTheme === 'light' ? 'light' : 'dark';
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('netgenix-theme', theme);
  }, [theme]);

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-bg-primary transition-colors duration-300" data-theme={theme}>
        <Dashboard theme={theme} onThemeChange={setTheme} />
      </div>
    </QueryClientProvider>
  );
}

export default App;
