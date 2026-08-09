"use client";

import { useState, type FormEvent } from "react";
import {
  Button,
  Checkbox,
  Field,
  Input,
  Select,
  Textarea,
} from "@atoz/design-system";
import type {
  AdminCategory,
  AdminTag,
  ArticlePayload,
} from "@/lib/api-client";

interface ContentFormProps {
  categories: AdminCategory[];
  tags: AdminTag[];
  initial?: {
    title: string;
    excerpt: string;
    body: string;
    slug: string;
    primaryCategoryId: string | null;
    categoryIds: string[];
    tagIds: string[];
  };
  submitLabel: string;
  onSubmit: (payload: ArticlePayload) => Promise<void>;
}

/**
 * Article create/edit form shared by /content/new and /content/[id].
 * Pure CMS form — no AI generation, no prompts (Website Contract §4).
 */
export function ContentForm({
  categories,
  tags,
  initial,
  submitLabel,
  onSubmit,
}: ContentFormProps) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [slug, setSlug] = useState(initial?.slug ?? "");
  const [excerpt, setExcerpt] = useState(initial?.excerpt ?? "");
  const [body, setBody] = useState(initial?.body ?? "");
  const [categoryIds, setCategoryIds] = useState<string[]>(initial?.categoryIds ?? []);
  const [primaryCategoryId, setPrimaryCategoryId] = useState<string | null>(
    initial?.primaryCategoryId ?? initial?.categoryIds[0] ?? null,
  );
  const [tagIds, setTagIds] = useState<string[]>(initial?.tagIds ?? []);
  const [changeSummary, setChangeSummary] = useState("");
  const [error, setError] = useState<string | undefined>();
  const [saving, setSaving] = useState(false);

  const toggleCategory = (id: string) => {
    const next = categoryIds.includes(id)
      ? categoryIds.filter((item) => item !== id)
      : [...categoryIds, id];
    setCategoryIds(next);
    if (primaryCategoryId && !next.includes(primaryCategoryId)) {
      setPrimaryCategoryId(next[0] ?? null);
    }
  };

  const toggleTag = (id: string) => {
    setTagIds((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
    );
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(undefined);
    if (!title.trim()) {
      setError("Title is required.");
      return;
    }
    if (primaryCategoryId && !categoryIds.includes(primaryCategoryId)) {
      setError("The primary category must be one of the selected categories.");
      return;
    }
    setSaving(true);
    try {
      await onSubmit({
        title: title.trim(),
        excerpt: excerpt.trim(),
        body,
        slug: slug.trim() || undefined,
        categoryIds,
        primaryCategoryId,
        tagIds,
        changeSummary: changeSummary.trim() || undefined,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save the article.");
      setSaving(false);
    }
  };

  return (
    <form className="space-y-6" onSubmit={handleSubmit} noValidate>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <Field label="Title" htmlFor="article-title" required error={error}>
            <Input
              id="article-title"
              name="title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Article title"
            />
          </Field>
          <Field label="Slug" htmlFor="article-slug" hint="Optional — generated from the title when empty. Locked once published.">
            <Input
              id="article-slug"
              name="slug"
              value={slug}
              onChange={(event) => setSlug(event.target.value)}
              placeholder="article-slug"
            />
          </Field>
          <Field label="Excerpt" htmlFor="article-excerpt">
            <Textarea
              id="article-excerpt"
              name="excerpt"
              rows={3}
              value={excerpt}
              onChange={(event) => setExcerpt(event.target.value)}
              placeholder="Short summary shown in cards and search results."
            />
          </Field>
          <Field label="Body" htmlFor="article-body" hint="Plain text. Blank lines separate paragraphs.">
            <Textarea
              id="article-body"
              name="body"
              rows={16}
              value={body}
              onChange={(event) => setBody(event.target.value)}
              placeholder="Article content — written by the AI Content OS and reviewed here."
            />
          </Field>
        </div>

        <div className="space-y-5">
          <fieldset>
            <legend className="text-sm font-medium text-text-900">Categories</legend>
            <p className="mb-2 mt-1 text-xs text-text-600">
              Select one or more; pick the primary category below.
            </p>
            <div className="space-y-2">
              {categories.map((category) => (
                <label key={category.id} className="flex items-center gap-2 text-sm">
                  <Checkbox
                    checked={categoryIds.includes(category.id)}
                    onChange={() => toggleCategory(category.id)}
                  />
                  {category.name}
                </label>
              ))}
            </div>
          </fieldset>
          <Field label="Primary category" htmlFor="article-primary-category">
            <Select
              id="article-primary-category"
              value={primaryCategoryId ?? ""}
              onChange={(event) => setPrimaryCategoryId(event.target.value || null)}
            >
              <option value="">None</option>
              {categories
                .filter((category) => categoryIds.includes(category.id))
                .map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
            </Select>
          </Field>
          <fieldset>
            <legend className="text-sm font-medium text-text-900">Tags</legend>
            <div className="mt-2 space-y-2">
              {tags.map((tag) => (
                <label key={tag.id} className="flex items-center gap-2 text-sm">
                  <Checkbox checked={tagIds.includes(tag.id)} onChange={() => toggleTag(tag.id)} />
                  {tag.name}
                </label>
              ))}
            </div>
          </fieldset>
          <Field label="Change summary" htmlFor="article-change-summary" hint="Saved with the new version for the audit trail.">
            <Input
              id="article-change-summary"
              name="changeSummary"
              value={changeSummary}
              onChange={(event) => setChangeSummary(event.target.value)}
              placeholder="What changed in this revision?"
            />
          </Field>
        </div>
      </div>

      <div className="flex items-center justify-between gap-4 border-t border-border pt-5">
        <p role="alert" className="text-sm font-medium text-danger-500">
          {error}
        </p>
        <Button type="submit" loading={saving}>
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
