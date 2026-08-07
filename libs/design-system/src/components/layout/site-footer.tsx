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
    <footer className="border-t border-border bg-surface-1">
      <Container className="py-12">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-3">
            <Logo />
            <p className="max-w-xs text-sm text-text-600">
              Products worth knowing. Independent articles, tested recommendations,
              and honest disclosure.
            </p>
          </div>
          {groups.map((group) => (
            <nav key={group.title} aria-label={group.title}>
              <h2 className="text-sm font-semibold text-text-900">{group.title}</h2>
              <ul className="mt-3 space-y-2">
                {group.links.map((link) => (
                  <li key={link.href}>
                    <a
                      href={link.href}
                      className="text-sm text-text-600 hover:text-primary-500 hover:underline"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>
        <div className="mt-10 border-t border-border pt-6">
          <p className="max-w-3xl text-xs leading-relaxed text-text-400">
            {disclosure}
          </p>
          <p className="mt-3 text-xs text-text-400">
            © {new Date().getFullYear()} AtozProductHub. All rights reserved.
          </p>
        </div>
      </Container>
    </footer>
  );
}
