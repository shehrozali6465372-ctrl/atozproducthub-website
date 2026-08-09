"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Badge,
  Button,
  Card,
  DataTable,
  EmptyState,
  Pagination,
  SectionHeading,
  Select,
} from "@atoz/design-system";
import { Plus } from "lucide-react";
import { createAdminApiClient, type AdminArticle } from "@/lib/api-client";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "draft", label: "Draft" },
  { value: "review", label: "In review" },
  { value: "published", label: "Published" },
  { value: "unpublished", label: "Unpublished" },
  { value: "archived", label: "Archived" },
];

const STATUS_VARIANT: Record<string, "neutral" | "warning" | "success" | "danger" | "info"> = {
  draft: "neutral",
  review: "warning",
  published: "success",
  unpublished: "info",
  archived: "danger",
};

export default function ContentPage() {
  const [status, setStatus] = useState("");
  const [articles, setArticles] = useState<AdminArticle[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      try {
        const items = await createAdminApiClient().content.listArticles(status || undefined);
        if (!cancelled) setArticles(items);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [status]);

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="CMS"
        title="Content"
        description="Articles, categories, and tags for the active niche. Lifecycle: draft → review → published → archived."
        action={
          <Button asChild variant="outline" size="sm">
            <Link href="/content/new">
              <Plus aria-hidden="true" className="size-4" />
              New article
            </Link>
          </Button>
        }
      />
      <Card
        title="Articles"
        description="Every record is scoped to the active niche (X-Niche-Id)."
      >
        <div className="mb-4 flex justify-end">
          <label className="flex items-center gap-2 text-sm">
            <span className="text-text-600">Status</span>
            <Select
              className="w-44"
              aria-label="Filter articles by status"
              value={status}
              onChange={(event) => setStatus(event.target.value)}
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </label>
        </div>
        {loading ? (
          <EmptyState title="Loading articles…" description="Fetching the CMS list." />
        ) : (
          <DataTable
            caption="Articles in the active niche"
            columns={[
              {
                key: "title",
                header: "Title",
                render: (row) => (
                  <Link
                    href={`/content/${row.id}`}
                    className="font-medium text-primary-500 hover:underline"
                  >
                    {row.title}
                  </Link>
                ),
              },
              {
                key: "status",
                header: "Status",
                render: (row) => (
                  <Badge variant={STATUS_VARIANT[row.status] ?? "neutral"}>{row.status}</Badge>
                ),
              },
              { key: "slug", header: "Slug", render: (row) => <span className="text-text-600">/{row.slug}</span> },
              { key: "updatedAt", header: "Updated", render: (row) => new Date(row.updatedAt).toLocaleDateString("en-US") },
            ]}
            rows={articles}
            emptyLabel="No articles in this status yet"
          />
        )}
        <Pagination className="mt-6" page={1} totalPages={1} onPageChange={() => undefined} />
      </Card>
    </div>
  );
}
