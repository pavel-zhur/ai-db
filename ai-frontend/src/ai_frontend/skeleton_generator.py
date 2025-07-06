"""React project skeleton generator."""

import logging
from pathlib import Path

from ai_frontend.utils import write_file

logger = logging.getLogger(__name__)


class SkeletonGenerator:
    """Generate React project skeleton with Material-UI and Vite."""

    async def generate(
        self,
        project_dir: Path,
        project_name: str = "ai-frontend",
        api_base_url: str = "http://localhost:8000",
    ) -> None:
        """Generate complete React project skeleton.

        Args:
            project_dir: Directory to generate project in
            project_name: Name of the project
            api_base_url: Base URL for API calls
        """
        logger.info(f"Generating React skeleton in {project_dir}")

        # Create directory structure
        directories = [
            "src",
            "src/components",
            "src/components/common",
            "src/api",
            "src/types",
            "src/hooks",
            "src/utils",
            "src/pages",
            "src/theme",
            "public",
        ]

        for dir_path in directories:
            (project_dir / dir_path).mkdir(parents=True, exist_ok=True)

        # Generate files
        files = {
            "package.json": self._generate_package_json(project_name),
            "tsconfig.json": self._generate_tsconfig(),
            "tsconfig.node.json": self._generate_tsconfig_node(),
            "vite.config.ts": self._generate_vite_config(),
            ".gitignore": self._generate_gitignore(),
            "index.html": self._generate_index_html(project_name),
            "src/main.tsx": self._generate_main_tsx(),
            "src/App.tsx": self._generate_app_tsx(),
            "src/theme/theme.ts": self._generate_theme(),
            "src/api/client.ts": self._generate_api_client(api_base_url),
            "src/hooks/useApi.ts": self._generate_use_api_hook(),
            "src/utils/index.ts": self._generate_utils(),
            "src/components/common/Loading.tsx": self._generate_loading_component(),
            "src/components/common/ErrorDisplay.tsx": self._generate_error_component(),
            "src/vite-env.d.ts": self._generate_vite_env(),
            ".env.example": self._generate_env_example(api_base_url),
            ".eslintrc.json": self._generate_eslint_config(),
        }

        for file_path, content in files.items():
            await write_file(project_dir / file_path, content)

        logger.info("React skeleton generated successfully")

    def _generate_package_json(self, project_name: str) -> str:
        """Generate package.json file."""
        return f"""{
  "name": "{project_name}",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "@mui/material": "^5.15.0",
    "@mui/icons-material": "^5.15.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0",
    "@vitejs/plugin-react": "^4.2.0",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }
}"""

    def _generate_tsconfig(self) -> str:
        """Generate tsconfig.json file."""
        return """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "allowSyntheticDefaultImports": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}"""

    def _generate_tsconfig_node(self) -> str:
        """Generate tsconfig.node.json file."""
        return """{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}"""

    def _generate_vite_config(self) -> str:
        """Generate vite.config.ts file."""
        return """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})"""

    def _generate_gitignore(self) -> str:
        """Generate .gitignore file."""
        # Load from template
        template_path = Path(__file__).parent / "templates" / "gitignore"
        if template_path.exists():
            with open(template_path, "r") as f:
                return f.read()

        # Fallback if template not found
        return """# Dependencies
node_modules/
.pnp
.pnp.js

# Production
dist/
build/

# Misc
.DS_Store
.env.local
.env.development.local
.env.test.local
.env.production.local
*.log

# Editor
.vscode/
.idea/
*.swp
*.swo

# TypeScript
*.tsbuildinfo"""

    def _generate_index_html(self, project_name: str) -> str:
        """Generate index.html file."""
        return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
    <link
      rel="stylesheet"
      href="https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap"
    />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>"""

    def _generate_main_tsx(self) -> str:
        """Generate main.tsx file."""
        return """import React from 'react'
import ReactDOM from 'react-dom/client'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import App from './App'
import { theme } from './theme/theme'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>,
)"""

    def _generate_app_tsx(self) -> str:
        """Generate App.tsx file."""
        return """import { Container, Typography, Box } from '@mui/material'

function App() {
  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h2" component="h1" gutterBottom>
          AI-Generated Frontend
        </Typography>
        <Typography variant="body1">
          This frontend is ready to be customized by Claude Code.
        </Typography>
      </Box>
    </Container>
  )
}

export default App"""

    def _generate_theme(self) -> str:
        """Generate theme.ts file."""
        return """import { createTheme } from '@mui/material/styles'

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
})"""

    def _generate_api_client(self, api_base_url: str) -> str:
        """Generate API client."""
        return f"""import axios, {{ AxiosInstance, AxiosError }} from 'axios'
import {{ ApiResponse, QueryResult, MutationResult }} from '@/types/api'

class ApiClient {{
  private client: AxiosInstance
  private retryAttempts = 3
  private retryDelay = 1000

  constructor() {{
    this.client = axios.create({{
      baseURL: import.meta.env.VITE_API_URL || '{api_base_url}',
      timeout: 30000,
      headers: {{
        'Content-Type': 'application/json',
      }},
    }})

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      response => response,
      async error => {{
        if (this.shouldRetry(error)) {{
          return this.retryRequest(error)
        }}
        return Promise.reject(this.formatError(error))
      }}
    )
  }}

  private shouldRetry(error: AxiosError): boolean {{
    if (!error.config || error.config.method?.toUpperCase() !== 'GET') {{
      return false
    }}

    const status = error.response?.status
    return status === 502 || status === 503 || status === 504 || !status
  }}

  private async retryRequest(error: AxiosError): Promise<any> {{
    const config = error.config!
    const retryCount = (config as any).__retryCount || 0

    if (retryCount >= this.retryAttempts) {{
      return Promise.reject(error)
    }}

    (config as any).__retryCount = retryCount + 1

    await new Promise(resolve => setTimeout(resolve, this.retryDelay * (retryCount + 1)))

    return this.client.request(config)
  }}

  private formatError(error: AxiosError): Error {{
    if (error.response?.data) {{
      const data = error.response.data as any
      return new Error(data.message || data.error || 'API Error')
    }}
    return error
  }}

  async query<T>(query: string): Promise<QueryResult<T>> {{
    const response = await this.client.post<ApiResponse<QueryResult<T>>>('/db/query', {{
      query,
      permission: 'select',
    }})

    if (!response.data.success) {{
      throw new Error(response.data.error || 'Query failed')
    }}

    return response.data.data!
  }}

  async queryView<T>(viewName: string, params?: Record<string, any>): Promise<QueryResult<T>> {{
    const response = await this.client.post<ApiResponse<QueryResult<T>>>('/db/query/view', {{
      view: viewName,
      params,
      permission: 'select',
    }})

    if (!response.data.success) {{
      throw new Error(response.data.error || 'View query failed')
    }}

    return response.data.data!
  }}

  async execute(query: string): Promise<MutationResult> {{
    const response = await this.client.post<ApiResponse<MutationResult>>('/db/data', {{
      query,
      permission: 'data_modify',
    }})

    if (!response.data.success) {{
      throw new Error(response.data.error || 'Execution failed')
    }}

    return response.data.data!
  }}
}}

export const apiClient = new ApiClient()"""

    def _generate_use_api_hook(self) -> str:
        """Generate useApi hook."""
        return """import { useState, useEffect, useCallback } from 'react'
import { apiClient } from '@/api/client'

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: Error | null
}

export function useApi<T>(
  query: string | null,
  deps: any[] = []
): UseApiState<T> & { refetch: () => void } {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  })

  const fetchData = useCallback(async () => {
    if (!query) return

    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const result = await apiClient.query<T>(query)
      setState({ data: result.rows as any, loading: false, error: null })
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error })
    }
  }, [query])

  useEffect(() => {
    fetchData()
  }, [fetchData, ...deps])

  return { ...state, refetch: fetchData }
}"""

    def _generate_utils(self) -> str:
        """Generate utils/index.ts file."""
        return """export function formatDate(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleDateString()
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount)
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout

  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}"""

    def _generate_loading_component(self) -> str:
        """Generate Loading component."""
        return """import { CircularProgress, Box, Typography } from '@mui/material'

interface LoadingProps {
  message?: string
}

export function Loading({ message = 'Loading...' }: LoadingProps) {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="200px"
    >
      <CircularProgress />
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        {message}
      </Typography>
    </Box>
  )
}"""

    def _generate_error_component(self) -> str:
        """Generate ErrorDisplay component."""
        return """import { Alert, AlertTitle, Button, Box } from '@mui/material'

interface ErrorDisplayProps {
  error: Error | string
  onRetry?: () => void
}

export function ErrorDisplay({ error, onRetry }: ErrorDisplayProps) {
  const message = typeof error === 'string' ? error : error.message

  return (
    <Box sx={{ my: 2 }}>
      <Alert severity="error">
        <AlertTitle>Error</AlertTitle>
        {message}
      </Alert>
      {onRetry && (
        <Button onClick={onRetry} variant="contained" sx={{ mt: 2 }}>
          Retry
        </Button>
      )}
    </Box>
  )
}"""

    def _generate_vite_env(self) -> str:
        """Generate vite-env.d.ts file."""
        return """/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}"""

    def _generate_env_example(self, api_base_url: str) -> str:
        """Generate .env.example file."""
        return f"VITE_API_URL={api_base_url}"

    def _generate_eslint_config(self) -> str:
        """Generate .eslintrc.json file."""
        return """{
  "env": {
    "browser": true,
    "es2020": true
  },
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaVersion": "latest",
    "sourceType": "module"
  },
  "plugins": ["react-refresh"],
  "rules": {
    "react-refresh/only-export-components": [
      "warn",
      { "allowConstantExport": true }
    ]
  }
}"""
