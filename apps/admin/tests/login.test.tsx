import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { LoginForm } from "@/components/login-form";
import { expectNoAxeViolations } from "./helpers";

describe("Admin login wireframe", () => {
  it("validates required email and passes axe", async () => {
    const user = userEvent.setup();
    const { container } = render(<LoginForm />);

    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(screen.getByText("Email is required.")).toBeInTheDocument();

    await user.type(screen.getByLabelText(/email/i), "admin@example.com");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(screen.queryByText("Email is required.")).not.toBeInTheDocument();

    await expectNoAxeViolations(container);
  });
});
