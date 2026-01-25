"""README - Frontend Application"""

# Stock Analysis System - Frontend

## Overview
React + TypeScript + Vite based web interface for the Stock Analysis System.

## Project Structure

```
frontend/
├── src/
│   ├── pages/                  # Page components
│   ├── components/             # Reusable components
│   ├── services/               # API service calls
│   ├── hooks/                  # Custom React hooks
│   ├── store/                  # Zustand state management
│   ├── types/                  # TypeScript type definitions
│   ├── styles/                 # Global styles
│   ├── App.tsx                 # Root component
│   └── main.tsx                # Entry point
├── public/                     # Static assets
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── README.md                   # This file
```

## Setup

### 1. Install Node.js
- Download from https://nodejs.org/ (LTS version recommended)
- Verify: `node --version` and `npm --version`

### 2. Install Dependencies

```bash
npm install
# or
yarn install
```

### 3. Development Server

```bash
npm run dev
# or
yarn dev
```

Application will be available at `http://localhost:5173`

## Building for Production

```bash
npm run build
npm run preview
```

## Code Quality

### Linting
```bash
npm run lint
```

### Formatting
```bash
npm run format
```

### Type Checking
```bash
npm run type-check
```

### Testing
```bash
npm test
npm run test:ui
```

## Technologies Used

- **React 18**: UI library
- **TypeScript**: Type safety
- **Vite**: Build tool and dev server
- **React Router**: Client-side routing
- **Zustand**: State management
- **Axios**: HTTP client
- **React Query**: Data fetching and caching
- **ECharts**: Data visualization
- **Ant Design**: UI component library
- **Tailwind CSS**: Utility-first CSS
- **Vitest**: Unit testing framework

## Project Organization

### Pages
- Stock Analysis
- Market Analysis
- News Center
- Limit Up Pool

### Components
- StockSearch: Stock input and search
- KLineChart: K-line chart visualization
- IndicatorDisplay: Technical indicators display
- NewsCard: News article card
- Common: Shared components

### Services
- API calls to backend
- Data transformation
- Error handling

### Hooks
- useAnalysis: Stock analysis hook
- useFetch: Data fetching hook
- useLocalStorage: Local storage hook

### Store
- analysisStore: Global analysis state using Zustand

## Environment Configuration

Create a `.env.local` file:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_API_TIMEOUT=30000
```

## API Integration

All API calls are centralized in `src/services/api.ts`:

```typescript
import { api } from '@/services/api';

// Example usage
const data = await api.getStockKline('000001', 'day');
```

## Styling

### Tailwind CSS
Used for utility-first styling. Configuration in `tailwind.config.js`

### Component Libraries
- **Ant Design**: Enterprise-grade UI components
- **ECharts**: Professional data visualization

## Performance Optimization

- Code splitting with dynamic imports
- Image optimization
- Tree-shaking with Vite
- Lazy loading of routes
- Query caching with React Query

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Troubleshooting

### Port Already in Use
```bash
# Use different port
npm run dev -- --port 3000
```

### Module Not Found
```bash
# Clear node_modules and reinstall
rm -rf node_modules
npm install
```

### API Connection Issues
- Check backend is running
- Verify VITE_API_BASE_URL in .env.local
- Check CORS configuration on backend

## Next Steps

1. Create page components
2. Implement API service calls
3. Set up global state management
4. Add chart visualizations
5. Implement error handling and loading states

## License

(Add your license here)
