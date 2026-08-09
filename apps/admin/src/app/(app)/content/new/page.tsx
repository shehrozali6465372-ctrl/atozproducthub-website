"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, SectionHeading, EmptyState } from "@atoz/design-system";
import { ContentForm } from "@/components/content-form";
import { createAdminApiClient, type AdminCategory, type AdminTag } from "@/lib/api-client";

export default function NewArticlePage() {
  const router = useRouter();
  const [categories, setCategories] = useState<AdminCategory[]>([]);
  const [tags, setTags] = useState<AdminTag[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const api = createAdminApiClient();
    void Promise.all([api.content.listCategories(), api.content.listTags()]).then(
      ([categoryItems, tagItems]) => {
        setCategories(categoryItems);
        setTags(tagItems);
        setReady(true);
      },
    );
  }, []);

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="CMS"
        title="New article"
        description="Create a draft. It is visible to the public only after it is published."
      />
      <Card title="Article details">
        {!ready ? (
          <EmptyState title="Loading categories and tags…" />
        ) : (
          <ContentForm
            categories={categories}
            tags={tags}
            submitLabel="Save draft"
            onSubmit={async (payload) => {
              await createAdminApiClient().content.createArticle(payload);
              router.push("/content");
            }}
          />
        )}
      </Card>
    </div>
  );
}
