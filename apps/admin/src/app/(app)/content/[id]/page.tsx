"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  SectionHeading,
} from "@atoz/design-system";
import { ArrowLeft } from "lucide-react";
import { ContentForm } from "@/components/content-form";
import {
  createAdminApiClient,
  type AdminArticle,
  type AdminArticleDetail,
  type AdminCategory,
  type AdminTag,
  type LifecycleAction,
} from "@/lib/api-client";

const STATUS_VARIANT: Record<string, "neutral" | "warning" | "success" | "danger" | "info"> = {
  draft: "neutral",
  review: "warning",
  published: "success",
  unpublished: "info",
  archived: "danger",
};

const TRANSITIONS: Partial<Record<LifecycleAction, string[]>> = {
  submit: ["draft"],
  approve: ["review"],
  reject: ["review"],
  publish: ["draft", "unpublished", "published"],
  unpublish: ["published"],
  archive: ["published", "unpublished"],
  restore: ["archived"],
};

const ACTION_LABEL: Record<LifecycleAction, string> = {
  submit: "Submit for review",
  approve: "Approve",
  reject: "Reject",
  publish: "Publish",
  unpublish: "Unpublish",
  archive: "Archive",
  restore: "Restore to draft",
};

export default function EditArticlePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [detail, setDetail] = useState<AdminArticleDetail | null>(null);
  const [categories, setCategories] = useState<AdminCategory[]>([]);
  const [tags, setTags] = useState<AdminTag[]>([]);
  const [ready, setReady] = useState(false);
  const [notice, setNotice] = useState<string | undefined>();
  const [error, setError] = useState<string | undefined>();

  const load = useCallback(async () => {
    const api = createAdminApiClient();
    const [loaded, categoryItems, tagItems] = await Promise.all([
      api.content.getArticle(id),
      api.content.listCategories(),
      api.content.listTags(),
    ]);
    setDetail(loaded);
    setCategories(categoryItems);
    setTags(tagItems);
    setReady(true);
  }, [id]);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      const api = createAdminApiClient();
      const [loaded, categoryItems, tagItems] = await Promise.all([
        api.content.getArticle(id),
        api.content.listCategories(),
        api.content.listTags(),
      ]);
      if (cancelled) return;
      setDetail(loaded);
      setCategories(categoryItems);
      setTags(tagItems);
      setReady(true);
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (!ready) {
    return <EmptyState title="Loading article…" />;
  }

  if (!detail) {
    return (
      <div className="space-y-6">
        <SectionHeading eyebrow="CMS" title="Article not found" />
        <Button variant="outline" size="sm" onClick={() => router.push("/content")}>
          <ArrowLeft aria-hidden="true" className="size-4" />
          Back to content
        </Button>
      </div>
    );
  }

  const availableActions = Object.entries(TRANSITIONS)
    .filter(([, from]) => from.includes(detail.status))
    .map(([action]) => action as LifecycleAction);

  const runAction = async (action: LifecycleAction) => {
    setNotice(undefined);
    setError(undefined);
    try {
      const updated: AdminArticle = await createAdminApiClient().content.transition(id, action);
      setDetail((current) => (current ? { ...current, status: updated.status } : current));
      setNotice(`Article moved to "${updated.status}".`);
      void load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lifecycle action failed.");
    }
  };

  const handleDelete = async () => {
    setNotice(undefined);
    setError(undefined);
    try {
      await createAdminApiClient().content.deleteArticle(id);
      router.push("/content");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed.");
    }
  };

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="CMS"
        title={detail.title}
        description={`Slug /${detail.slug} · Updated ${new Date(detail.updatedAt).toLocaleString()}`}
        action={
          <Button variant="outline" size="sm" onClick={() => router.push("/content")}>
            <ArrowLeft aria-hidden="true" className="size-4" />
            Back to content
          </Button>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={STATUS_VARIANT[detail.status] ?? "neutral"}>{detail.status}</Badge>
        <span className="text-xs text-text-600">
          {detail.publishedAt
            ? `Published ${new Date(detail.publishedAt).toLocaleDateString()}`
            : "Not published yet"}
        </span>
      </div>

      {availableActions.length > 0 ? (
        <Card title="Lifecycle" description="Server-validated status transitions (draft → review → published → archived).">
          <div className="flex flex-wrap gap-2">
            {availableActions.map((action) => (
              <Button
                key={action}
                size="sm"
                variant={action === "archive" || action === "reject" ? "danger" : "secondary"}
                onClick={() => void runAction(action)}
              >
                {ACTION_LABEL[action]}
              </Button>
            ))}
            <Button size="sm" variant="danger" onClick={() => void handleDelete()}>
              Delete (soft)
            </Button>
          </div>
          {notice ? (
            <p role="status" className="mt-3 text-sm font-medium text-success-600">{notice}</p>
          ) : null}
          {error ? (
            <p role="alert" className="mt-3 text-sm font-medium text-danger-500">{error}</p>
          ) : null}
        </Card>
      ) : null}

      <Card title="Edit article">
        <ContentForm
          categories={categories}
          tags={tags}
          initial={{
            title: detail.title,
            excerpt: detail.excerpt,
            body: detail.body,
            slug: detail.slug,
            primaryCategoryId: detail.primaryCategoryId,
            categoryIds: detail.categories.map((category) => category.id),
            tagIds: detail.tags.map((tag) => tag.id),
          }}
          submitLabel="Save changes"
          onSubmit={async (payload) => {
            await createAdminApiClient().content.updateArticle(id, payload);
            setNotice("Changes saved. Published content keeps its snapshot until re-published.");
            void load();
          }}
        />
      </Card>

      <Card title="Version history" description="Immutable snapshots — each save creates a new version.">
        {detail.versions.length === 0 ? (
          <EmptyState title="No versions yet" description="The first save creates version 1." />
        ) : (
          <ul className="space-y-3">
            {detail.versions.map((version) => (
              <li key={version.id} className="rounded-lg border border-border p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-text-900">
                    Version {version.versionNo} · {version.title}
                  </p>
                  <p className="text-xs text-text-600">
                    {version.createdBy ?? "system"} · {new Date(version.createdAt).toLocaleString()}
                  </p>
                </div>
                {version.changeSummary ? (
                  <p className="mt-1 text-sm text-text-600">{version.changeSummary}</p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
