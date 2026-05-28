# Vendor Assessment Tool - Frontend

Advanced Bayesian Hierarchical Model for Vendor Performance Analysis

## 🚀 Tech Stack

- **Framework**: Next.js 14 (App Router)
- **UI Library**: React 18 + React Bootstrap
- **Styling**: Bootstrap 5 with custom CSS (professional tech vibes)
- **State Management**: Zustand
- **API Client**: Axios with interceptors
- **Data Fetching**: TanStack React Query
- **Visualization**: Recharts
- **Language**: TypeScript

## 📋 Features

- 🔐 User authentication (JWT-based)
- 📤 Excel file upload (PO, OC, SHIP)
- 📊 Real-time analytics dashboard
- 🏆 Vendor rankings with Bayesian scoring
- 📈 Interactive charts and visualizations
- 🔒 Model locking for year-over-year comparisons
- ⚡ Professional dark theme with cyan accents

## 🛠️ Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
```

### Development

```bash
npm run dev
```

Visit http://localhost:3000

### Production Build

```bash
npm run build
npm start
```

## 📁 Project Structure

```
frontend/
├── app/                      # Next.js App Router
│   ├── layout.tsx           # Root layout with providers
│   ├── page.tsx             # Home page
│   ├── login/page.tsx       # Login page
│   ├── register/page.tsx    # Registration page
│   ├── dashboard/           # Dashboard with file upload
│   ├── rankings/            # Vendor rankings
│   │   └── [vendor]/        # Vendor detail view
│   └── admin/               # Admin panel
├── components/              # Reusable components
│   ├── Navbar.tsx          # Navigation bar
│   ├── Upload/             # Upload components
│   ├── Dashboard/          # Dashboard components
│   └── ...
├── lib/                    # Utilities
│   ├── api.ts             # Axios client
│   ├── auth.ts            # Authentication utilities
│   ├── constants.ts       # API endpoints
│   └── providers.tsx      # React providers
├── hooks/                 # Custom hooks
│   ├── useDashboard.ts   # Dashboard queries
│   └── useBHM.ts         # BHM queries
├── store/                # Zustand stores
│   └── authStore.ts      # Auth state
├── types/                # TypeScript types
│   └── api.ts           # API response types
└── globals.css          # Global styles
```

## 🎨 Color Scheme

- **Primary**: #0d47a1 (Dark Blue)
- **Accent**: #00d9ff (Cyan)
- **Success**: #10b981 (Green)
- **Background**: #0f1419 (Very Dark)

## 🔌 API Integration

All API calls are made through the Axios client in `lib/api.ts` with:

- Automatic JWT token injection
- 401 error handling with redirect to login
- Request/response logging for debugging

### Example Usage

```typescript
import { api } from "@/lib/api";
import { API_ENDPOINTS } from "@/lib/constants";

const response = await api.post(API_ENDPOINTS.AUTH.LOGIN, {
    email: "user@example.com",
    password: "password",
});
```

## 📊 Pages

### Login (`/login`)

- JWT-based authentication
- Registration link

### Dashboard (`/dashboard`)

- Upload PO, OC, SHIP files
- Real-time metrics display
- Interactive charts

### Rankings (`/rankings`)

- Bayesian hierarchical model results
- Vendor rankings with confidence intervals
- Sort by rank, price, or timeliness

### Vendor Detail (`/rankings/[vendor]`)

- Individual vendor performance
- Convergence diagnostics
- Confidence intervals

### Admin (`/admin`)

- Model locking
- Configuration status

## 🐛 Debugging

Environment logging is enabled by default. API requests and responses are logged to console:

```
🔵 API Request: POST /upload
✅ API Success: 200 /upload
❌ API Error: 401 /bhm/rankings
```

## 📦 Dependencies

Key packages:

- `react-bootstrap@2.10.0` - Bootstrap components
- `axios@1.6.0` - HTTP client
- `zustand@4.4.0` - State management
- `@tanstack/react-query@5.0.0` - Server state management
- `recharts@2.10.0` - Charts library

## 🚀 Deployment

For production deployment:

1. Build the application: `npm run build`
2. Update `.env.local` with production API URL
3. Deploy to Vercel, Netlify, or your preferred platform

## 📝 License

This project is part of a thesis on vendor assessment using Bayesian methods.
