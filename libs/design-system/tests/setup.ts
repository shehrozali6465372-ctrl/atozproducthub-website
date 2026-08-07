import "@testing-library/jest-dom/vitest";
import { mockMatchMedia } from "./helpers";

mockMatchMedia();

/** In-memory localStorage polyfill (Node 26 does not expose window.localStorage). */
const storage = new Map<string, string>();
Object.defineProperty(window, "localStorage", {
  writable: true,
  value: {
    getItem: (key: string) => storage.get(key) ?? null,
    setItem: (key: string, value: string) => {
      storage.set(key, String(value));
    },
    removeItem: (key: string) => {
      storage.delete(key);
    },
    clear: () => storage.clear(),
  },
});

/** Silence jsdom canvas warnings; charts render SVG and do not need real canvas. */
Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
  writable: true,
  value: () => null,
});
