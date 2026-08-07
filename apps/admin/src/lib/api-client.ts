import {
  AUTOMATION_RULES,
  DASHBOARD_KPIS,
  NOTIFICATIONS,
  PAGE_TITLES,
  PIN_ACCOUNTS,
  PIN_QUEUE,
  REVENUE_SERIES,
  TOP_PAGES,
  TRAFFIC_SERIES,
  TRAFFIC_SOURCES,
} from "./mock-data";

/**
 * Typed admin API client — M2 foundation stub.
 *
 * Mirrors the Admin API shape from 12-api-contracts.md. Replaced in Phases
 * 5/11 by a contract-generated client over `libs/contracts/admin/` and the
 * API gateway. No real network calls exist in M2.
 */

export interface Kpi {
  label: string;
  value: string;
  delta: string;
  trend: "up" | "down" | "flat";
  hint: string;
}

export interface AdminApiClient {
  dashboard: {
    getKpis(): Promise<Kpi[]>;
    getRevenueSeries(): Promise<typeof REVENUE_SERIES>;
    getTrafficSeries(): Promise<typeof TRAFFIC_SERIES>;
    getTopPages(): Promise<typeof TOP_PAGES>;
    getNotifications(): Promise<typeof NOTIFICATIONS>;
  };
  analytics: {
    getTrafficSources(): Promise<typeof TRAFFIC_SOURCES>;
  };
  pinterest: {
    getAccounts(): Promise<typeof PIN_ACCOUNTS>;
    getPinQueue(): Promise<typeof PIN_QUEUE>;
  };
  automation: {
    getRules(): Promise<typeof AUTOMATION_RULES>;
  };
}

const delay = <T>(value: T): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(value), 0));

const mockAdminApiClient: AdminApiClient = {
  dashboard: {
    getKpis: () => delay(DASHBOARD_KPIS),
    getRevenueSeries: () => delay(REVENUE_SERIES),
    getTrafficSeries: () => delay(TRAFFIC_SERIES),
    getTopPages: () => delay(TOP_PAGES),
    getNotifications: () => delay(NOTIFICATIONS),
  },
  analytics: {
    getTrafficSources: () => delay(TRAFFIC_SOURCES),
  },
  pinterest: {
    getAccounts: () => delay(PIN_ACCOUNTS),
    getPinQueue: () => delay(PIN_QUEUE),
  },
  automation: {
    getRules: () => delay(AUTOMATION_RULES),
  },
};

export function createAdminApiClient(): AdminApiClient {
  return mockAdminApiClient;
}

export { PAGE_TITLES };
