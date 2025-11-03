# OpsCraft Frontend

Modern React + TypeScript frontend for OpsCraft microservices platform.

## 🚀 Tech Stack

- **Framework**: React 18
- **Build Tool**: Vite
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Forms**: React Hook Form + Zod
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Code Editor**: Monaco Editor
- **Notifications**: React Hot Toast
- **Charts**: Recharts

## 📦 Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

## 🛠️ Development

```bash
# Start dev server (http://localhost:3000)
npm run dev

# Type check
npm run type-check

# Lint
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🏗️ Project Structure

```
src/
├── components/          # Reusable UI components
│   └── layout/         # Layout components (Header, Sidebar)
├── pages/              # Page components
│   ├── auth/           # Authentication pages
│   ├── scripts/        # Script management pages
│   ├── executions/     # Execution pages
│   ├── secrets/        # Secret management pages
│   └── admin/          # Admin pages
├── stores/             # Zustand stores
├── hooks/              # Custom React hooks
├── lib/                # Utilities and API client
├── types/              # TypeScript types
├── App.tsx             # Main app component
├── main.tsx            # Entry point
└── index.css           # Global styles
```

## 🔑 Key Features

### Authentication
- JWT-based authentication
- Automatic token refresh
- Protected routes
- Role-based access control

### Scripts Management
- Create, read, update, delete scripts
- Support for Bash, Python, Ansible, Terraform
- Monaco code editor with syntax highlighting
- Version control
- Tag management

### Execution Monitoring
- Real-time execution status
- WebSocket for live logs
- Execution history
- Cancel running executions

### Secret Management
- Encrypted secret storage
- Reveal/hide secret values
- Audit log tracking
- Category-based organization

### Admin Dashboard
- System statistics
- User management
- Service health monitoring
- Role management

## 🌐 API Integration

The frontend communicates with backend services through:

```typescript
// API Base URL
VITE_API_URL=http://localhost:8000

// WebSocket URL
VITE_WS_URL=ws://localhost:8000
```

### API Client (`src/lib/api.ts`)

Centralized API client with:
- Automatic token injection
- Token refresh on 401
- Type-safe endpoints
- Error handling

```typescript
import { scriptsApi } from '@/lib/api'

// List scripts
const scripts = await scriptsApi.list()

// Create script
const newScript = await scriptsApi.create({
  name: 'My Script',
  script_type: 'bash',
  content: '#!/bin/bash\necho "Hello"',
})
```

## 🎨 Styling

### TailwindCSS

Utility-first CSS framework with custom configuration:

```javascript
// Custom colors
primary: {
  50: '#f0f9ff',
  // ... more shades
  900: '#0c4a6e',
}

// Custom components
.btn-primary
.btn-secondary
.btn-danger
.input
.card
```

### Custom Utilities

```typescript
// src/lib/utils.ts
cn()                    // Merge Tailwind classes
formatDate()           // Format dates
formatRelativeTime()   // "2h ago"
getStatusColor()       // Status badge colors
getScriptIcon()        // Script type icons
```

## 🔌 WebSocket Integration

Real-time updates via WebSocket:

```typescript
import { useWebSocket } from '@/hooks/useWebSocket'

function ExecutionLogs({ executionId }) {
  const { messages, isConnected } = useWebSocket(`executions/${executionId}`)
  
  return (
    <div>
      {messages.map(msg => <div>{msg.output}</div>)}
    </div>
  )
}
```

## 📊 State Management

### Zustand Stores

```typescript
// Auth store
import { useAuthStore } from '@/stores/authStore'

const { user, login, logout } = useAuthStore()
```

### React Query

```typescript
import { useQuery } from '@tanstack/react-query'

const { data, isLoading, error } = useQuery({
  queryKey: ['scripts'],
  queryFn: () => scriptsApi.list(),
})
```

## 🔒 Environment Variables

```bash
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# App Configuration
VITE_APP_TITLE=OpsCraft
VITE_APP_VERSION=1.0.0
```

## 🐳 Docker

```bash
# Build image
docker build -t opscraft-frontend .

# Run container
docker run -p 3000:80 opscraft-frontend
```

## 🚢 Production Build

```bash
# Build
npm run build

# Output directory
dist/
```

The production build:
- Minified and optimized
- Tree-shaken dependencies
- Code splitting
- Source maps included

## 📱 Responsive Design

The UI is fully responsive with breakpoints:
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

## ♿ Accessibility

- Semantic HTML
- ARIA labels
- Keyboard navigation
- Focus management
- Screen reader support

## 🧪 Testing

```bash
# Unit tests (to be added)
npm test

# E2E tests (to be added)
npm run test:e2e
```

## 📈 Performance

- Code splitting by route
- Lazy loading components
- Image optimization
- Caching strategies
- Bundle size optimization

## 🤝 Contributing

1. Follow the existing code structure
2. Use TypeScript for type safety
3. Follow component naming conventions
4. Write meaningful commit messages
5. Test your changes

## 📄 License

MIT License