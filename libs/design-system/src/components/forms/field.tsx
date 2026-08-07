import { cloneElement, type ReactElement } from "react";

export interface FieldControlProps {
  id?: string;
  "aria-describedby"?: string;
  "aria-invalid"?: boolean;
}

export interface FieldProps {
  label: string;
  htmlFor: string;
  hint?: string;
  error?: string;
  required?: boolean;
  children: ReactElement<FieldControlProps>;
}

/**
 * Label + control + hint/error wiring. Injects id / aria-describedby /
 * aria-invalid into the child control (13 §13: visible labels, inline errors).
 */
export function Field({ label, htmlFor, hint, error, required, children }: FieldProps) {
  const describedBy = [hint ? `${htmlFor}-hint` : null, error ? `${htmlFor}-error` : null]
    .filter(Boolean)
    .join(" ") || undefined;

  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="block text-sm font-medium text-text-900">
        {label}
        {required ? (
          <>
            <span aria-hidden="true" className="text-danger-500">
              {" "}
              *
            </span>
            <span className="sr-only"> (required)</span>
          </>
        ) : null}
      </label>
      {cloneElement(children as ReactElement<FieldControlProps>, {
        id: htmlFor,
        "aria-describedby": describedBy,
        "aria-invalid": error ? true : undefined,
      })}
      {hint && !error ? (
        <p id={`${htmlFor}-hint`} className="text-xs text-text-600">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={`${htmlFor}-error`} className="text-xs font-medium text-danger-500">
          {error}
        </p>
      ) : null}
    </div>
  );
}
