"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type Niche = { id: string; name: string; slug: string; status: string };
type Category = { id: string; name: string; slug: string; status: string };
type Tag = { id: string; name: string; slug: string; status: string };
type Article = { id: string; title: string; slug: string; status: string; excerpt: string };

async function adminFetch<T>(
  path: string,
  options: RequestInit = {},
  nicheId?: string,
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (nicheId) headers.set("X-Niche-Id", nicheId);
  if (options.body) headers.set("Content-Type", "application/json");
  const response = await fetch(`/api/admin/content${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });
  const text = await response.text();
  let data: unknown = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!response.ok) {
    const message =
      typeof data === "object" && data && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : typeof data === "object" && data && "error" in data
          ? String((data as { error: unknown }).error)
          : `Request failed (${response.status}).`;
    throw new Error(message);
  }
  return data as T;
}

export default function BlogAdmin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [authenticated, setAuthenticated] = useState(false);
  const [niches, setNiches] = useState<Niche[]>([]);
  const [nicheId, setNicheId] = useState("");
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [articles, setArticles] = useState<Article[]>([]);
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [excerpt, setExcerpt] = useState("");
  const [body, setBody] = useState("");
  const [categoryIds, setCategoryIds] = useState<string[]>([]);
  const [tagIds, setTagIds] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const selectedNiche = useMemo(
    () => niches.find((niche) => niche.id === nicheId),
    [niches, nicheId],
  );

  useEffect(() => {
    if (!authenticated) return;
    adminFetch<Niche[]>("/niches")
      .then((items) => {
        setNiches(items);
        const active = items.find((item) => item.status === "active") ?? items[0];
        if (active) setNicheId(active.id);
      })
      .catch((error) => setMessage(error.message));
  }, [authenticated]);

  useEffect(() => {
    if (!nicheId) return;
    Promise.all([
      adminFetch<Category[]>("/categories", {}, nicheId),
      adminFetch<Tag[]>("/tags", {}, nicheId),
      adminFetch<{ items: Article[] }>("/articles?page=1&page_size=100", {}, nicheId),
    ])
      .then(([categoryItems, tagItems, articlePage]) => {
        setCategories(categoryItems);
        setTags(tagItems);
        setArticles(articlePage.items);
      })
      .catch((error) => setMessage(error.message));
  }, [nicheId]);

  async function signIn(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const response = await fetch("/api/admin/auth/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) { const data = await response.json().catch(() => null); throw new Error(typeof data?.error === "string" ? data.error : "Authentication failed."); }
      setAuthenticated(true);
      setPassword("");
      setMessage("Session created. Loading CMS data…");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Authentication failed.");
    } finally {
      setBusy(false);
    }
  }

  async function createDraft(event: FormEvent) {
    event.preventDefault();
    if (!nicheId) return setMessage("Select a niche first.");
    setBusy(true);
    setMessage("");
    try {
      const article = await adminFetch<Article>(
        "/articles",
        {
          method: "POST",
          body: JSON.stringify({
            title: title.trim(),
            slug: slug.trim() || undefined,
            excerpt: excerpt.trim(),
            body,
            category_ids: categoryIds,
            primary_category_id: categoryIds[0] || undefined,
            tag_ids: tagIds,
          }),
        },
        nicheId,
      );
      setArticles((current) => [article, ...current]);
      setMessage(`Draft created: ${article.title}`);
      setTitle(""); setSlug(""); setExcerpt(""); setBody("");
      setCategoryIds([]); setTagIds([]);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not create draft.");
    } finally {
      setBusy(false);
    }
  }

  async function publish(articleId: string) {
    setBusy(true);
    setMessage("");
    try {
      const article = await adminFetch<Article>(
        `/articles/${articleId}/lifecycle`,
        { method: "POST", body: JSON.stringify({ action: "publish" }) },
        nicheId,
      );
      setArticles((current) =>
        current.map((item) => item.id === article.id ? article : item),
      );
      setMessage(`Published: ${article.title}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not publish.");
    } finally {
      setBusy(false);
    }
  }

  async function signOut() {
    await fetch("/api/admin/session", { method: "DELETE" });
    setAuthenticated(false);
    setNiches([]); setCategories([]); setTags([]); setArticles([]);
    setMessage("Signed out.");
  }

  if (!authenticated) {
    return (
      <main className="mx-auto min-h-screen max-w-xl px-5 py-12">
        <h1 className="text-3xl font-bold">AtoZ Blog Admin</h1>
        <p className="mt-2 text-sm opacity-70">
          Secure CMS console. Credentials are exchanged server-side; the access token is stored only in an HttpOnly session cookie.
        </p>
        <form onSubmit={signIn} className="mt-8 space-y-4 rounded-2xl border p-5">
          <label className="block text-sm font-medium">
            Username
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              type="text"
              autoComplete="username"
              required
              className="mt-2 w-full rounded-xl border px-3 py-3"
            />
          </label>
          <label className="block text-sm font-medium">
            Password
            <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" autoComplete="current-password" required className="mt-2 w-full rounded-xl border px-3 py-3" />
          </label>
          <button disabled={busy} className="w-full rounded-xl border px-4 py-3 font-semibold disabled:opacity-50">
            {busy ? "Signing in…" : "Open CMS"}
          </button>
        </form>
        {message && <p className="mt-4 text-sm">{message}</p>}
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen max-w-4xl px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold">Blog CMS</h1>
          <p className="text-sm opacity-70">Create drafts and publish through the existing Content Service.</p>
        </div>
        <button onClick={signOut} className="rounded-xl border px-3 py-2 text-sm">Sign out</button>
      </div>

      <div className="mt-6 rounded-2xl border p-4">
        <label className="text-sm font-medium">
          Niche
          <select value={nicheId} onChange={(event) => setNicheId(event.target.value)} className="mt-2 w-full rounded-xl border px-3 py-3">
            {niches.map((niche) => <option key={niche.id} value={niche.id}>{niche.name} ({niche.slug})</option>)}
          </select>
        </label>
        {selectedNiche && <p className="mt-2 text-xs opacity-60">Tenant: {selectedNiche.id}</p>}
      </div>

      <form onSubmit={createDraft} className="mt-6 space-y-4 rounded-2xl border p-5">
        <h2 className="text-xl font-semibold">New blog post</h2>
        <input required maxLength={300} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" className="w-full rounded-xl border px-3 py-3" />
        <input maxLength={200} value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="Slug (optional — generated automatically)" className="w-full rounded-xl border px-3 py-3" />
        <textarea maxLength={2000} value={excerpt} onChange={(e) => setExcerpt(e.target.value)} placeholder="Short excerpt" rows={3} className="w-full rounded-xl border px-3 py-3" />
        <textarea required value={body} onChange={(e) => setBody(e.target.value)} placeholder="Article body. Separate paragraphs with blank lines." rows={14} className="w-full rounded-xl border px-3 py-3" />

        <fieldset>
          <legend className="text-sm font-medium">Categories</legend>
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            {categories.map((category) => (
              <label key={category.id} className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={categoryIds.includes(category.id)}
                  onChange={(e) => setCategoryIds((current) => e.target.checked ? [...current, category.id] : current.filter((id) => id !== category.id))} />
                {category.name}
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend className="text-sm font-medium">Tags</legend>
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            {tags.map((tag) => (
              <label key={tag.id} className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={tagIds.includes(tag.id)}
                  onChange={(e) => setTagIds((current) => e.target.checked ? [...current, tag.id] : current.filter((id) => id !== tag.id))} />
                {tag.name}
              </label>
            ))}
          </div>
        </fieldset>

        <button disabled={busy} className="w-full rounded-xl border px-4 py-3 font-semibold disabled:opacity-50">
          {busy ? "Saving…" : "Save draft"}
        </button>
      </form>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Articles</h2>
        <div className="mt-3 space-y-3">
          {articles.map((article) => (
            <article key={article.id} className="rounded-2xl border p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold">{article.title}</h3>
                  <p className="text-xs opacity-60">{article.slug} · {article.status}</p>
                </div>
                {article.status === "draft" && (
                  <button disabled={busy} onClick={() => publish(article.id)} className="rounded-xl border px-3 py-2 text-sm font-semibold disabled:opacity-50">
                    Publish
                  </button>
                )}
              </div>
            </article>
          ))}
          {!articles.length && <p className="text-sm opacity-60">No articles yet.</p>}
        </div>
      </section>

      {message && <p className="mt-6 rounded-xl border p-3 text-sm">{message}</p>}
    </main>
  );
}
