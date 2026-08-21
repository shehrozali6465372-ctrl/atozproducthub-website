import { defineCloudflareConfig } from "@opennextjs/cloudflare";

export default defineCloudflareConfig({
  // ISR cache uses the default KV incremental cache (no R2 needed for this app size).
});
