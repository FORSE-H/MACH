// Build-time data loader — fetches the full catalogue from the live MACH API so
// pages can be statically generated. Runtime search hits the API directly (see
// the Search island), so this is only for the baked pages.

const API = import.meta.env.PUBLIC_MACH_API || "https://mach-render-deploy.onrender.com";

export const apiBase = API;

// Fetch JSON with retries — the free-tier API may be cold-starting at build time
// (first request can take ~50s), so a single failed fetch shouldn't fail the build.
async function getJson(path, { retries = 4 } = {}) {
  let lastErr;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(`${API}${path}`, { signal: AbortSignal.timeout(90000) });
      if (!res.ok) throw new Error(`${path} -> HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      lastErr = err;
      if (attempt < retries) await new Promise((r) => setTimeout(r, 3000 * (attempt + 1)));
    }
  }
  throw new Error(`Failed to fetch ${path} after ${retries + 1} attempts: ${lastErr}`);
}

// Reshape an entry's flat facts into a convenient object + a facts list that
// keeps the source (lineage) for display.
function shapeEntry(raw) {
  const byName = {};
  for (const f of raw.facts) byName[f.field_name] = f;
  const val = (k) => byName[k]?.value ?? null;

  return {
    identifier: raw.identifier,
    name: raw.name,
    url: raw.url,
    codeRepository: raw.code_repository,
    category: raw.category,
    description: val("description"),
    license: val("license"),
    stars: numOrNull(val("repo_stars")),
    forks: numOrNull(val("repo_forks")),
    lastCommit: val("repo_last_commit"),
    archived: val("repo_archived") === "True",
    pypiDownloads: numOrNull(val("pypi_downloads")),
    hfDownloads: numOrNull(val("hf_downloads")),
    judgement: val("judgement"),
    judgementReason: val("judgement_reason"),
    // every fact with its source, for the lineage table
    facts: raw.facts
      .filter((f) => f.value !== null && !["judgement", "judgement_reason"].includes(f.field_name))
      .map((f) => ({ field: f.field_name, value: f.value, source: f.source_id })),
  };
}

function numOrNull(v) {
  if (v === null || v === undefined) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

let _cache = null;

// All entries, fully shaped, fetched once at build time. On failure (API asleep)
// the build fails loudly rather than shipping an empty site — which is correct;
// retry the build when the API is awake.
export async function loadCatalog() {
  if (_cache) return _cache;
  const list = await getJson("/catalog");
  // Fetch in small batches, not 200+ at once — gentler on the free-tier API.
  const entries = [];
  const BATCH = 8;
  for (let i = 0; i < list.length; i += BATCH) {
    const slice = list.slice(i, i + BATCH);
    const got = await Promise.all(
      slice.map((item) => getJson(`/dataset/${item.identifier}`).then(shapeEntry)),
    );
    entries.push(...got);
  }
  // stable order: judgement (Adopt first), then stars desc, then name
  const ringRank = { Adopt: 0, Assess: 1, Caution: 2 };
  entries.sort((a, b) => {
    const r = (ringRank[a.judgement] ?? 3) - (ringRank[b.judgement] ?? 3);
    if (r) return r;
    const s = (b.stars ?? -1) - (a.stars ?? -1);
    if (s) return s;
    return a.name.localeCompare(b.name);
  });
  _cache = entries;
  return entries;
}

export function catalogStats(entries) {
  const rings = { Adopt: 0, Assess: 0, Caution: 0, unscored: 0 };
  const categories = {};
  for (const e of entries) {
    rings[e.judgement || "unscored"] = (rings[e.judgement || "unscored"] || 0) + 1;
    categories[e.category] = (categories[e.category] || 0) + 1;
  }
  return { total: entries.length, rings, categories };
}
