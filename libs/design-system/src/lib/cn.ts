/**
 * Lightweight class-name joiner (dependency-free; keeps bundles small).
 * Design-system helper only — no business logic.
 */
export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}
