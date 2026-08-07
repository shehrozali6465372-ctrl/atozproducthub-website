# Contributing to AtozProductHub Website

Thank you for your interest in contributing. This repository holds the **business layer** for the AtozProductHub website. It currently contains documentation only; website implementation will begin in a future phase, and only after approved scope and design docs.

## Code of Conduct

Be respectful, constructive, and inclusive. Harassment, personal attacks, and unprofessional behavior will not be tolerated.

## Scope and Boundaries

Read [README.md](README.md) before contributing, especially these sections:

- **Project Scope** — what belongs in this repository.
- **Relationship with Universal AI Content Operating System** — how the two systems interact.
- **"No Duplicate Features" Policy** — the AI OS already exists; nothing from it may be copied or reimplemented here.

### What this repository is for

- Website, articles, affiliate products, Pinterest, SEO, traffic, revenue, analytics, automation, and admin dashboard (business layer).

### What this repository is NOT for

- The Universal AI Content Operating System (AI OS) — its code, features, or documentation belong in the AI OS repository.
- Any contribution that duplicates AI OS functionality will be rejected during review.

## How to Contribute

### Reporting Bugs

- Open an issue and include: expected behavior, actual behavior, steps to reproduce, and environment details.
- Search existing issues first to avoid duplicates.

### Feature Requests

- Describe the business value, user impact, and which system should own the feature (this website or the AI OS).
- If the AI OS already covers the capability, the request will be closed under the "No Duplicate Features" policy.

### Documentation Improvements

- Typos, clarifications, and missing context are welcome as small pull requests.
- Keep documentation consistent with the repository rules in [README.md](README.md).

## Development Workflow

1. **Docs first:** no implementation is merged without an approved scope/design document.
2. Branch from `main` using a descriptive name:
   - `docs/...` for documentation
   - `feat/...` for new features
   - `fix/...` for bug fixes
   - `chore/...` for maintenance
3. Use [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat:`, `fix:`, `docs:`, `chore:`).
4. Keep pull requests small and focused on a single concern.
5. Update `CHANGELOG.md` under `Unreleased` for user-facing changes.
6. Open a pull request to `main` describing the change and referencing related issues.

## Pull Request Checklist

- [ ] Scope and boundaries respected (no AI OS duplication).
- [ ] Changes are minimal and focused.
- [ ] Documentation updated where relevant.
- [ ] `CHANGELOG.md` updated for user-facing changes.
- [ ] Linting, formatting, and tests pass (once implementation begins).
- [ ] No secrets, keys, or local environment files committed.
- [ ] License-compatible dependencies only (MIT-compatible).

## Security

Do not open public issues for security vulnerabilities. Report them privately to the repository maintainers so they can be addressed before disclosure.

## Questions

Open a discussion or issue for questions about scope, architecture, or the contribution process.
