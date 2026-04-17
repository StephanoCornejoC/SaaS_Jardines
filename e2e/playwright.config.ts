import { defineConfig, devices } from '@playwright/test';
import * as dotenv from 'dotenv';

// Cargar variables de entorno desde .env si existe
dotenv.config({ path: '.env' });

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  // En CI falla si hay test.only accidentales
  forbidOnly: !!process.env.CI,
  // Reintentos en CI para flakiness de red
  retries: process.env.CI ? 2 : 0,
  // Workers reducidos en CI para evitar sobrecarga
  workers: process.env.CI ? 1 : undefined,

  reporter: [
    ['html', { open: 'never', outputFolder: 'playwright-report' }],
    ['list'],
    ['junit', { outputFile: 'test-results/e2e-results.xml' }],
  ],

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    // Captura de trazas solo en primer reintento (ahorra espacio en CI)
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
    // Timeouts conservadores: Ant Design puede tardar en montar modales
    actionTimeout: 15000,
    navigationTimeout: 30000,
    // Locale espanol para fechas en DatePicker de Ant Design
    locale: 'es-PE',
    timezoneId: 'America/Lima',
  },

  projects: [
    // -------------------------------------------------------
    // Proyecto de autenticacion: corre primero, genera storage state
    // -------------------------------------------------------
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },

    // -------------------------------------------------------
    // Browsers desktop con sesion reutilizada
    // -------------------------------------------------------
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },

    // -------------------------------------------------------
    // Mobile viewport (solo Chromium para no duplicar tiempo)
    // -------------------------------------------------------
    {
      name: 'mobile-chrome',
      use: {
        ...devices['Pixel 5'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],

  // Arrancar el servidor de desarrollo si no esta corriendo
  webServer: {
    command: 'npm run dev',
    cwd: '../frontend',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
    stdout: 'ignore',
    stderr: 'pipe',
  },

  outputDir: 'test-results',
});
