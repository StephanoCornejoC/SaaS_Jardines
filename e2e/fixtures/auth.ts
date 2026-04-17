/**
 * CUSTOM FIXTURES
 *
 * Extienden el objeto `test` base de Playwright con:
 * - Todas las Page Objects pre-instanciadas
 * - Helper de API para setup/teardown de datos
 * - Utilidades de Ant Design
 *
 * Uso en tests:
 *   import { test, expect } from '../fixtures/auth';
 *   test('mi test', async ({ loginPage, studentsPage }) => { ... });
 */
import { test as base, type APIRequestContext } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { StudentsPage } from '../pages/StudentsPage';
import { StudentDetailPage } from '../pages/StudentDetailPage';
import { PaymentsPage } from '../pages/PaymentsPage';
import { AttendancePage } from '../pages/AttendancePage';
import { CashflowPage } from '../pages/CashflowPage';

// -------------------------------------------------------------------
// Helper de API para crear/limpiar datos de prueba sin pasar por la UI
// -------------------------------------------------------------------
export class ApiHelper {
  constructor(
    private readonly request: APIRequestContext,
    private readonly baseUrl: string = process.env.API_URL || 'http://localhost:8000'
  ) {}

  private get headers() {
    // Los tests que usan ApiHelper ya tienen sesion activa via storageState.
    // Para llamadas directas a la API necesitamos el token del env.
    return {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${process.env.TEST_ACCESS_TOKEN || ''}`,
    };
  }

  async getAuthToken(): Promise<string> {
    const res = await this.request.post(`${this.baseUrl}/api/auth/token/`, {
      data: {
        email: process.env.TEST_EMAIL || 'admin@garabato.test',
        password: process.env.TEST_PASSWORD || 'admin123',
      },
    });
    const { access } = await res.json();
    return access;
  }

  async createStudent(token: string, data?: Partial<StudentData>): Promise<StudentData> {
    const dni = data?.dni || `9${Date.now().toString().slice(-7)}`;
    const payload: StudentData = {
      dni,
      nombres: data?.nombres || 'TestNombre',
      apellidos: data?.apellidos || 'TestApellido',
      fecha_nacimiento: data?.fecha_nacimiento || '2020-01-15',
      genero: data?.genero || 'M',
      estado: data?.estado || 'ACTIVO',
    };

    const res = await this.request.post(`${this.baseUrl}/api/students/`, {
      data: payload,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    });

    if (!res.ok()) {
      throw new Error(`Error al crear alumno: ${await res.text()}`);
    }
    return res.json();
  }

  async deleteStudent(token: string, id: number): Promise<void> {
    await this.request.delete(`${this.baseUrl}/api/students/${id}/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  }

  async getClassrooms(token: string): Promise<ClassroomData[]> {
    const res = await this.request.get(`${this.baseUrl}/api/classrooms/?estado=ACTIVO`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    return data.results || data;
  }

  async getPendingPayments(token: string): Promise<PaymentData[]> {
    const res = await this.request.get(`${this.baseUrl}/api/payments/?estado=PENDIENTE`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    return data.results || data;
  }
}

// -------------------------------------------------------------------
// Tipos de datos del dominio
// -------------------------------------------------------------------
export interface StudentData {
  id?: number;
  dni: string;
  nombres: string;
  apellidos: string;
  fecha_nacimiento: string;
  genero: 'M' | 'F';
  estado?: 'ACTIVO' | 'RETIRADO' | 'EGRESADO';
}

export interface ClassroomData {
  id: number;
  nombre: string;
  nivel: string;
}

export interface PaymentData {
  id: number;
  alumno_nombre: string;
  mes: number;
  anio: number;
  monto: string;
  estado: 'PENDIENTE' | 'PAGADO' | 'VENCIDO';
}

// -------------------------------------------------------------------
// Tipo de los fixtures extendidos
// -------------------------------------------------------------------
type MyFixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  studentsPage: StudentsPage;
  studentDetailPage: StudentDetailPage;
  paymentsPage: PaymentsPage;
  attendancePage: AttendancePage;
  cashflowPage: CashflowPage;
  apiHelper: ApiHelper;
};

// -------------------------------------------------------------------
// Extension del test base con todos los fixtures
// -------------------------------------------------------------------
export const test = base.extend<MyFixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },

  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },

  studentsPage: async ({ page }, use) => {
    await use(new StudentsPage(page));
  },

  studentDetailPage: async ({ page }, use) => {
    await use(new StudentDetailPage(page));
  },

  paymentsPage: async ({ page }, use) => {
    await use(new PaymentsPage(page));
  },

  attendancePage: async ({ page }, use) => {
    await use(new AttendancePage(page));
  },

  cashflowPage: async ({ page }, use) => {
    await use(new CashflowPage(page));
  },

  apiHelper: async ({ request }, use) => {
    await use(new ApiHelper(request));
  },
});

export { expect } from '@playwright/test';
