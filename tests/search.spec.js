// End-to-end tests for MACH search + filters.
//
// These guard the exact bug class that broke search repeatedly: single-word
// "keyword" queries (a language) must route to the complete LOCAL filter (not
// the semantic API, which under-returns for generic words), and the local
// filters must keep working after a search. They need no network — the semantic
// API path is covered separately (and stubbed) so these stay fast + deterministic.

const { test, expect } = require('@playwright/test');

const SEARCH = '#entry-search';
const RUN = '#semantic-btn';
const STATUS = '#semantic-status';
const CARD = '.entry-card';

// Cards shown on the CURRENT page (the local filter paginates at 16/page).
async function visibleCount(page) {
  return await page.$$eval(CARD, (cards) =>
    cards.filter((c) => getComputedStyle(c).display !== 'none').length
  );
}

// The number of entries the active filters MATCH (across all pages). This is the
// real result of a filter — visibleCount() only shows the current page of it.
async function matchedCount(page) {
  return await page.evaluate(() =>
    (window.MACHFilters && window.MACHFilters.getVisible)
      ? window.MACHFilters.getVisible().length
      : -1
  );
}

test.beforeEach(async ({ page }) => {
  await page.goto('/index.html');
  await page.waitForSelector(CARD);               // cards rendered
  await page.waitForFunction(() => !!window.MACHFilters); // filter API ready
});

test('the search box is visible and usable', async ({ page }) => {
  const box = page.locator(SEARCH);
  await expect(box).toBeVisible();
  await expect(box).toBeEditable();
});

test('typing a language ("python") shows many entries, not a handful', async ({ page }) => {
  // How many Python entries exist in the catalogue (ground truth from the DOM)?
  const pythonTotal = await page.$$eval(CARD, (cards) =>
    cards.filter((c) => c.getAttribute('data-lang') === 'Python').length
  );
  expect(pythonTotal).toBeGreaterThan(40); // sanity: the catalogue really has many

  await page.fill(SEARCH, 'python');
  await page.click(RUN);

  // The language route should MATCH essentially all Python entries — this is the
  // regression guard (the bug matched 1, then 7, instead of ~all). The list
  // paginates, so we check the matched set, not just the visible page.
  await expect.poll(() => matchedCount(page)).toBeGreaterThan(pythonTotal - 5);
  await expect.poll(() => visibleCount(page)).toBeGreaterThan(0); // a page is shown

  // And the status should say it filtered by language.
  await expect(page.locator(STATUS)).toContainText(/Python/i);
});

test('clicking a category filter after a search resets the view (not stuck/blank)', async ({ page }) => {
  // Run a search first (puts the page into result mode).
  await page.fill(SEARCH, 'python');
  await page.click(RUN);
  await expect.poll(() => visibleCount(page)).toBeGreaterThan(10);

  // Now click a category filter chip (AI/ML models, say). This must escape
  // search mode and show the filtered list — the "filters do nothing after a
  // search / no reset" bug.
  const chip = page.locator('#filter-cat .filter-btn[data-value]').first();
  await chip.click();

  // Cards for that category should be visible, and the semantic status gone.
  await expect.poll(() => visibleCount(page)).toBeGreaterThan(0);
  await expect(page.locator(STATUS)).toBeHidden();

  // Every visible card matches the chosen category (the filter actually applied).
  const chosen = await chip.getAttribute('data-value');
  const offCategory = await page.$$eval(
    CARD,
    (cards, cat) =>
      cards.filter(
        (c) => getComputedStyle(c).display !== 'none' && c.getAttribute('data-cat') !== cat
      ).length,
    chosen
  );
  expect(offCategory).toBe(0);
});

test('clearing the search returns to the full catalogue', async ({ page }) => {
  const allMatched = await matchedCount(page);   // every entry, unfiltered
  await page.fill(SEARCH, 'python');
  await page.click(RUN);
  await expect.poll(() => matchedCount(page)).toBeLessThan(allMatched); // narrowed

  // Clear the box → back to the normal (unfiltered) listing.
  await page.fill(SEARCH, '');
  await expect.poll(() => matchedCount(page)).toBe(allMatched);
});
