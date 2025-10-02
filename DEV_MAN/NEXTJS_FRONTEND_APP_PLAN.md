# APP Plan: Next.js Frontend for PeteRental VAPI

## 🎯 Overview

Create a beautiful, modern Next.js 15 frontend using shadcn/ui and TypeScript to visualize the PeteRental VAPI system architecture, documentation, and real-time data. The frontend will communicate with the existing Python FastAPI backend via REST API.

**Model**: Based on successful patterns from `/Users/markcarpenter/Desktop/pete/pete-intercom-app`

## 📐 Architecture Philosophy

### Separation of Concerns
```
┌─────────────────────────────────────┐
│   Next.js 15 Frontend (Port 3000)   │
│   - shadcn/ui components            │
│   - TypeScript strict mode          │
│   - Server Actions                  │
│   - App Router                      │
└──────────────┬──────────────────────┘
               │ REST API
               │
┌──────────────▼──────────────────────┐
│   Python FastAPI Backend (Port 8000) │
│   - Rental database                 │
│   - VAPI webhooks                   │
│   - LangChain scraping              │
│   - Calendar integration            │
└─────────────────────────────────────┘
```

### Key Design Principles (from pete-intercom-app)
1. **TypeScript Strict Mode** - No `any` types, full type safety
2. **Server Actions First** - Use React Server Components and Server Actions
3. **shadcn/ui Components** - Beautiful, accessible UI components
4. **Pete Branding** - Purple-to-pink gradients, clean design
5. **DRY Principles** - Centralized types in `/types` directory
6. **pnpm Package Manager** - Fast, efficient dependency management

## 📦 Dependencies

### Core Framework
```json
{
  "dependencies": {
    "next": "15.1.6",
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "typescript": "^5.7.2"
  }
}
```

### UI & Styling
```json
{
  "dependencies": {
    "@radix-ui/react-alert-dialog": "^1.1.4",
    "@radix-ui/react-badge": "^1.1.1",
    "@radix-ui/react-card": "^1.1.1",
    "@radix-ui/react-tabs": "^1.1.2",
    "@radix-ui/react-progress": "^1.1.1",
    "tailwindcss": "^3.4.17",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.6.0",
    "lucide-react": "^0.469.0"
  }
}
```

### Data Fetching & State
```json
{
  "dependencies": {
    "swr": "^2.2.5",
    "zod": "^3.24.1"
  }
}
```

### Markdown & Visualization
```json
{
  "dependencies": {
    "react-markdown": "^9.0.2",
    "rehype-highlight": "^7.0.1",
    "rehype-raw": "^7.0.0",
    "mermaid": "^11.4.1"
  }
}
```

## 🗂️ Project Structure

```
peterental-nextjs/
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── (dashboard)/              # Dashboard route group
│   │   │   ├── page.tsx              # Main dashboard
│   │   │   ├── architecture/page.tsx  # Architecture view
│   │   │   ├── documentation/page.tsx # Documentation browser
│   │   │   ├── rentals/page.tsx      # Rentals data view
│   │   │   ├── deployments/page.tsx  # Deployment status
│   │   │   └── layout.tsx            # Dashboard layout with nav
│   │   ├── api/                      # API routes (proxy to Python)
│   │   │   └── [...slug]/route.ts   # Catch-all proxy
│   │   ├── layout.tsx                # Root layout
│   │   └── page.tsx                  # Landing page
│   ├── actions/                      # Server Actions
│   │   ├── documentation.ts          # Fetch DEV_MAN docs
│   │   ├── rentals.ts                # Fetch rental data
│   │   └── system.ts                 # System status
│   ├── components/
│   │   ├── ui/                       # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── table.tsx
│   │   │   ├── progress.tsx
│   │   │   └── alert.tsx
│   │   ├── dashboard/
│   │   │   ├── status-cards.tsx      # System status cards
│   │   │   ├── rental-table.tsx      # Rental data table
│   │   │   ├── doc-browser.tsx       # Document browser
│   │   │   ├── architecture-diagram.tsx  # Mermaid diagrams
│   │   │   └── deployment-status.tsx # CI/CD status
│   │   └── layout/
│   │       ├── nav.tsx               # Navigation
│   │       ├── header.tsx            # Header
│   │       └── footer.tsx            # Footer
│   ├── lib/
│   │   ├── api-client.ts             # Python backend client
│   │   ├── utils.ts                  # Utility functions
│   │   └── constants.ts              # App constants
│   ├── types/
│   │   ├── rental.ts                 # Rental data types
│   │   ├── documentation.ts          # Documentation types
│   │   ├── system.ts                 # System status types
│   │   └── api.ts                    # API response types
│   └── styles/
│       └── globals.css               # Global styles
├── public/
│   ├── pete-logo.svg                 # Pete branding
│   └── favicon.ico
├── package.json
├── tsconfig.json                     # Strict TypeScript config
├── tailwind.config.ts
├── next.config.ts
└── .env.local                        # Environment variables
```

## 📝 Implementation Details

### 1. TypeScript Configuration (tsconfig.json)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{"name": "next"}],
    "paths": {
      "@/*": ["./src/*"],
      "@/types": ["./src/types"],
      "@/components": ["./src/components"],
      "@/lib": ["./src/lib"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### 2. Tailwind Configuration (tailwind.config.ts)

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ["class"],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        pete: {
          purple: '#8B5CF6',
          pink: '#EC4899',
          dark: '#1F2937',
          light: '#F9FAFB',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
export default config
```

### 3. API Client (src/lib/api-client.ts)

```typescript
import type {
  SystemStatus,
  RentalData,
  DocumentationList,
  DeploymentStatus
} from '@/types/api'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class APIClient {
  private baseURL: string

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
  }

  private async fetch<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store', // Always fetch fresh data
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`)
    }

    return response.json()
  }

  // System endpoints
  async getHealth(): Promise<{ status: string; service: string }> {
    return this.fetch('/health')
  }

  async getSystemStatus(): Promise<SystemStatus> {
    return this.fetch('/database/status')
  }

  // Rental endpoints
  async getRentals(website?: string): Promise<RentalData> {
    const endpoint = website
      ? `/database/rentals/${encodeURIComponent(website)}`
      : '/database/available'
    return this.fetch(endpoint)
  }

  // Documentation endpoints (future)
  async getDocumentation(): Promise<DocumentationList> {
    return this.fetch('/devman/api/docs')
  }

  async getDocument(filename: string): Promise<{ content: string; metadata: Record<string, unknown> }> {
    return this.fetch(`/devman/api/doc/${filename}`)
  }

  // GitHub integration
  async getGitHubStatus(): Promise<DeploymentStatus> {
    return this.fetch('/api/github/status')
  }
}

export const apiClient = new APIClient()
```

### 4. Type Definitions (src/types/api.ts)

```typescript
// src/types/rental.ts
export interface Rental {
  id: string
  website: string
  address: string
  price: string
  bedrooms: number
  bathrooms: number
  square_feet?: string
  available_date?: string
  property_type?: string
  scraped_at: string
}

// src/types/system.ts
export interface SystemStatus {
  status: string
  database_stats: {
    total_rentals: number
    websites_tracked: number
    last_updated: string
    websites: Record<string, {
      rental_count: number
      last_scraped: string
    }>
  }
}

// src/types/documentation.ts
export interface Documentation {
  filename: string
  title: string
  category: string
  description: string
  size: number
  modified: number
  path: string
}

export interface DocumentationList {
  docs: Documentation[]
  categories: string[]
}

// src/types/api.ts
export interface RentalData {
  rentals: Rental[]
  count: number
  website?: string
}

export interface DeploymentStatus {
  workflow_runs: Array<{
    id: number
    name: string
    status: string
    conclusion: string | null
    created_at: string
    updated_at: string
  }>
  latest_deployment: {
    status: string
    url: string
  }
}
```

### 5. Dashboard Home Page (src/app/(dashboard)/page.tsx)

```typescript
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { StatusCards } from '@/components/dashboard/status-cards'
import { RentalTable } from '@/components/dashboard/rental-table'
import { apiClient } from '@/lib/api-client'

export default async function DashboardPage() {
  // Fetch data using Server Components
  const [systemStatus, rentals] = await Promise.all([
    apiClient.getSystemStatus(),
    apiClient.getRentals(),
  ])

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-lg bg-gradient-to-r from-pete-purple to-pete-pink p-8 text-white">
        <div className="relative z-10">
          <h1 className="text-4xl font-bold">PeteRental VAPI Dashboard</h1>
          <p className="mt-2 text-lg opacity-90">
            AI-Powered Rental Property Search & Management
          </p>
        </div>
      </div>

      {/* Status Cards */}
      <StatusCards status={systemStatus} />

      {/* Recent Rentals */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Rentals</CardTitle>
              <CardDescription>
                Latest scraped rental properties from tracked websites
              </CardDescription>
            </div>
            <Badge variant="outline">
              {systemStatus.database_stats.total_rentals} Total
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <RentalTable rentals={rentals.rentals} />
        </CardContent>
      </Card>

      {/* Quick Links */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <CardTitle className="text-lg">📊 Architecture</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              View system architecture diagrams and data flow
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <CardTitle className="text-lg">📚 Documentation</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Browse DEV_MAN documentation and guides
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <CardTitle className="text-lg">🚀 Deployments</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Monitor CI/CD pipeline and deployment status
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
```

### 6. Status Cards Component (src/components/dashboard/status-cards.tsx)

```typescript
'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { SystemStatus } from '@/types/system'

interface StatusCardsProps {
  status: SystemStatus
}

export function StatusCards({ status }: StatusCardsProps) {
  const stats = [
    {
      title: 'Total Rentals',
      value: status.database_stats.total_rentals,
      icon: '🏠',
      trend: '+12%',
    },
    {
      title: 'Websites Tracked',
      value: status.database_stats.websites_tracked,
      icon: '🌐',
      trend: '+1',
    },
    {
      title: 'Last Updated',
      value: new Date(status.database_stats.last_updated).toLocaleDateString(),
      icon: '⏰',
      subtitle: new Date(status.database_stats.last_updated).toLocaleTimeString(),
    },
    {
      title: 'System Status',
      value: 'Healthy',
      icon: '✅',
      badge: 'Online',
    },
  ]

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat, index) => (
        <Card key={index} className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {stat.title}
            </CardTitle>
            <span className="text-2xl">{stat.icon}</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stat.value}</div>
            {stat.subtitle && (
              <p className="text-xs text-muted-foreground mt-1">
                {stat.subtitle}
              </p>
            )}
            {stat.trend && (
              <p className="text-xs text-green-600 mt-1">
                {stat.trend} from last week
              </p>
            )}
            {stat.badge && (
              <Badge variant="outline" className="mt-2">
                {stat.badge}
              </Badge>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
```

### 7. Navigation Component (src/components/layout/nav.tsx)

```typescript
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  Home,
  FileText,
  Database,
  Rocket,
  Network
} from 'lucide-react'

const routes = [
  {
    label: 'Dashboard',
    icon: Home,
    href: '/',
  },
  {
    label: 'Architecture',
    icon: Network,
    href: '/architecture',
  },
  {
    label: 'Documentation',
    icon: FileText,
    href: '/documentation',
  },
  {
    label: 'Rentals',
    icon: Database,
    href: '/rentals',
  },
  {
    label: 'Deployments',
    icon: Rocket,
    href: '/deployments',
  },
]

export function Nav() {
  const pathname = usePathname()

  return (
    <nav className="flex items-center space-x-4 lg:space-x-6">
      {routes.map((route) => (
        <Link
          key={route.href}
          href={route.href}
          className={cn(
            'text-sm font-medium transition-colors hover:text-primary flex items-center gap-2',
            pathname === route.href
              ? 'text-primary'
              : 'text-muted-foreground'
          )}
        >
          <route.icon className="h-4 w-4" />
          {route.label}
        </Link>
      ))}
    </nav>
  )
}
```

## 🧪 Testing Strategy

### Development Testing
```bash
# Install dependencies
pnpm install

# Run development server
pnpm dev

# Check TypeScript
pnpm type-check

# Lint code
pnpm lint
```

### Integration Testing
- Test API client with Python backend
- Verify data fetching and display
- Test responsive design on mobile
- Validate TypeScript types

## 📊 Success Criteria

- [x] Next.js 15 with App Router
- [x] TypeScript strict mode (no `any` types)
- [x] shadcn/ui components integrated
- [x] Pete branding (purple-to-pink gradients)
- [x] Server Components for data fetching
- [x] Responsive mobile-first design
- [x] Fast page loads (<2s)
- [x] Clean, organized code structure
- [x] Full type safety
- [x] Beautiful, modern UI

## 🚀 Deployment Strategy

### Development
```bash
# Start Python backend
cd /path/to/PeteRental_vapi_10_02_25
uv run python -m uvicorn main:app --port 8000

# Start Next.js frontend (separate terminal)
cd peterental-nextjs
pnpm dev
```

### Production
```bash
# Build Next.js app
pnpm build

# Deploy to Vercel/Render
# Python backend: Render (already deployed)
# Next.js frontend: Vercel (recommended)
```

## 🔮 Future Enhancements

### Phase 2
- [ ] Real-time updates with WebSockets
- [ ] Interactive Mermaid diagrams
- [ ] Advanced filtering and search
- [ ] Export documentation as PDF
- [ ] Dark mode toggle

### Phase 3
- [ ] User authentication
- [ ] Admin dashboard
- [ ] Analytics and metrics
- [ ] Custom reports
- [ ] Mobile app (React Native)

---

## 🎯 Implementation Steps

1. **Create Next.js project** (`pnpm create next-app`)
2. **Install shadcn/ui** (`pnpm dlx shadcn@latest init`)
3. **Set up TypeScript** (strict mode)
4. **Create directory structure**
5. **Implement API client**
6. **Build components** (status cards, tables, etc.)
7. **Create pages** (dashboard, docs, etc.)
8. **Style with Tailwind** (Pete branding)
9. **Test locally**
10. **Deploy to Vercel**

**Result**: Beautiful, modern dashboard to visualize PeteRental VAPI system!
