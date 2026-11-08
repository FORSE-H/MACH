// @ts-check
import { defineConfig } from "astro/config";

// Served at the root custom domain machcatalog.org, so base is "/".
// The catalogue is fetched from the live MACH API at build time.
export default defineConfig({
  site: process.env.SITE_URL || "https://machcatalog.org",
  base: process.env.BASE_PATH ?? "/",
  build: { format: "directory" },
});
