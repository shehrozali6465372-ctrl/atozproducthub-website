import { Container } from "./container";
import { Logo } from "./logo";

export interface FooterGroup {
  title: string;
  links: { label: string; href: string }[];
}

const DEFAULT_DISCLOSURE =
  "AtozProductHub participates in affiliate programs and may earn a commission from qualifying purchases. This does not affect editorial independence.";

export function SiteFooter({
  groups,
  disclosure = DEFAULT_DISCLOSURE,
}: {
  groups: FooterGroup[];
  disclosure?: string;
}) {
  return (
    <footer className="border-t border-border/60 bg-text-900 text-surface-0">
      <Container className="py-14 sm:py-16 lg:py-20">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-3">
            <Logo inverse />
            <p className="max-w-xs text-sm leading-relaxed text-surface-0/75">
              A premium editorial commerce platform across 10 carefully separated worlds.
            </p>
          </div>
          {groups.map((group) => (
            <nav key={group.title} aria-label={group.title}>
              <h2 className="text-sm font-semibold text-surface-0">{group.title}</h2>
              <ul className="mt-3 space-y-2">
                {group.links.map((link) => (
                  <li key={link.href}>
                    <a
                      href={link.href}
                      className="text-sm text-surface-0/70 hover:text-primary-500 hover:underline"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>
        <div className="mt-10 border-t border-white/10 pt-6">
          <p className="max-w-3xl text-xs leading-relaxed text-surface-0/60">
            {disclosure}
          </p>
          <p className="mt-3 text-xs tracking-wide text-surface-0/60">
            © {new Date().getFullYear()} AtozProductHub. All rights reserved.
          </p>
        </div>
      </Container>
    </footer>
  );
}
