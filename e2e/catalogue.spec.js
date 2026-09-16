import { expect, test } from './fixtures.js';

// Dépendances explicites de la slice C :
// - Slice A/Core : cartes, sélecteurs data-*, capacité et paging.
// - Slice B/Core : recherche multi-termes, suggestions, durée et favoris.
// La qualification de la surface wheel reste assurée par tests/test_packaging.py
// du Core ; ces tests vérifient ici le même contrat observable côté navigateur.

const visibleCards = (page) => page.locator('.recipe-card:visible');

test.describe('Catalogue — intégration desktop', () => {
  test('sélectionner une carte ne navigue pas, puis son lien ouvre la recette', async ({ page }) => {
    await page.goto('/');

    const cards = page.locator('.recipe-card');
    const cardCount = await cards.count();
    expect(cardCount).toBeGreaterThan(0);
    await expect(cards.locator('[data-recipe-select]')).toHaveCount(cardCount);

    const card = cards.first();
    const select = card.locator('[data-recipe-select]');
    const slug = await select.getAttribute('data-recipe-select');
    await expect(card.locator('a.recipe-card-link')).toHaveAttribute('href', new RegExp(`recipes/${slug}/`));

    const catalogueUrl = page.url();
    await select.click();
    await expect(page).toHaveURL(catalogueUrl);
    await expect(select).toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('[data-selection-count]')).toContainText('1');

    await card.locator('a.recipe-card-link').click();
    await expect(page).toHaveURL(new RegExp(`/recipes/${slug}/`));
  });

  test('recherche clavier : suggestion, terme actif, échappement et remise à zéro', async ({ page }) => {
    await page.goto('/');

    const input = page.locator('#recipe-search');
    await input.fill('poulet');
    await expect(input).toHaveAttribute('role', 'combobox');
    await expect(input).toHaveAttribute('aria-expanded', 'true');
    await expect(page.locator('#recipe-suggestions')).toBeVisible();

    await input.press('ArrowDown');
    await expect(input).toHaveAttribute('aria-activedescendant', /search-suggestion-/);
    await input.press('Enter');
    await expect(page.locator('[data-search-terms] .search-term')).toHaveCount(1);
    await expect(input).toHaveValue('');
    await expect(page.locator('#recipe-suggestions')).toBeHidden();

    await input.fill('curry');
    await expect(page.locator('#recipe-suggestions')).toBeVisible();
    await input.press('Escape');
    await expect(page.locator('#recipe-suggestions')).toBeHidden();

    await input.fill('introuvable_xyz_999');
    await expect(page.locator('.empty-search')).toBeVisible();
    await page.locator('.reset-search-btn').click();
    await expect(page.locator('[data-search-terms] .search-term')).toHaveCount(0);
    await expect(input).toHaveValue('');
    await expect(visibleCards(page)).not.toHaveCount(0);
  });

  test('compose texte, tag, durée et favoris sans perdre les contraintes', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('cookigram:recipe-favorites', JSON.stringify(['salade-cesar']));
    });
    await page.goto('/');

    const input = page.locator('#recipe-search');
    await input.fill('poulet');
    await input.press('Enter');
    await expect(page.locator('[data-search-terms] .search-term')).toHaveCount(1);

    await input.fill('volaille');
    const tagSuggestion = page.locator('.search-suggestion').filter({ hasText: /volaille/ }).first();
    await expect(tagSuggestion).toBeVisible();
    await tagSuggestion.click();
    await expect(page.locator('[data-search-terms] .search-term')).toHaveCount(2);

    const slider = page.locator('[data-time-slider]');
    await slider.press('Home');
    await expect(slider).toHaveAttribute('aria-valuetext', /Jusqu'à/);

    const favoriteFilter = page.locator('[data-favorite-filter]');
    await expect(favoriteFilter).toBeVisible();
    await favoriteFilter.click();
    await expect(favoriteFilter).toHaveAttribute('aria-pressed', 'true');
    await expect(visibleCards(page)).toHaveCount(1);
    await expect(visibleCards(page).first()).toHaveAttribute('data-title-slug', 'salade-cesar');

    await input.fill('introuvable_xyz_999');
    await expect(page.locator('.empty-search')).toBeVisible();
    await page.locator('.reset-search-btn').click();
    await expect(favoriteFilter).toHaveAttribute('aria-pressed', 'false');
    await expect(slider).toHaveAttribute('aria-valuetext', 'Aucune limite');
    await expect(page.locator('[data-search-terms] .search-term')).toHaveCount(0);
    await expect(visibleCards(page)).not.toHaveCount(0);
  });

  test('le filtre durée conserve l’outlier long et reste réversible', async ({ page }) => {
    await page.goto('/');

    const input = page.locator('#recipe-search');
    await input.fill('rôti');
    await expect(visibleCards(page)).toHaveCount(1);
    await expect(visibleCards(page).first()).toHaveAttribute('data-total-time', '1 h 15 min');

    const slider = page.locator('[data-time-slider]');
    await expect(slider).toHaveAttribute('aria-valuetext', 'Aucune limite');
    const maximum = await slider.inputValue();
    await slider.press('Home');
    await expect(visibleCards(page)).toHaveCount(0);
    await expect(page.locator('.empty-search')).toBeVisible();
    await slider.press('End');
    await expect(slider).toHaveValue(maximum);
    await expect(visibleCards(page)).toHaveCount(1);
    await expect(page.locator('.empty-search')).toBeHidden();
  });

  test('feuillette les feuilles de capacité et revient à la première', async ({ page }) => {
    await page.goto('/');

    const next = page.locator('[data-page-next]');
    const previous = page.locator('[data-page-prev]');
    await expect(next).toBeVisible();
    const firstSlug = await visibleCards(page).first().getAttribute('data-title-slug');
    await next.click();
    await expect(visibleCards(page).first()).not.toHaveAttribute('data-title-slug', firstSlug);
    await expect(previous).toBeVisible();
    await previous.click();
    await expect(visibleCards(page).first()).toHaveAttribute('data-title-slug', firstSlug);
    await expect(page.locator('[data-page-number]')).toHaveCount(0);
  });
});

test.describe('Catalogue — mobile 390px et surface wheel', () => {
  test('reste utilisable au clavier et sans débordement à 390px', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');

    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
    await expect(page.locator('#recipe-search')).toBeVisible();
    await expect(page.locator('[data-time-slider]')).toBeVisible();

    const controls = page.locator('#recipe-search, .search-clear, [data-time-slider], [data-favorite-filter], [data-recipe-select], [data-favorite-toggle], [data-page-prev], [data-page-next]');
    const controlCount = await controls.count();
    for (let index = 0; index < controlCount; index += 1) {
      const control = controls.nth(index);
      if (await control.isVisible()) {
        const box = await control.boundingBox();
        expect(box, `contrôle mobile ${index} sans boîte`).not.toBeNull();
        if (!box) throw new Error(`contrôle mobile ${index} sans boîte`);
        expect(Math.min(box.width, box.height)).toBeGreaterThanOrEqual(40);
      }
    }

    await page.locator('#recipe-search').fill('salade');
    await page.locator('#recipe-search').press('Enter');
    await expect(page.locator('[data-search-terms] .search-term')).toHaveCount(1);
    await page.locator('#recipe-search').fill('introuvable_xyz_999');
    await expect(page.locator('.empty-search')).toBeVisible();
    await page.locator('.reset-search-btn').click();
    await expect(visibleCards(page)).not.toHaveCount(0);
  });

  test('la page servie par le builder reste la surface navigateur attendue', async ({ page }) => {
    await page.goto('/');

    // Le serveur Playwright peut être alimenté par le Core installé en wheel
    // (voir tests/test_packaging.py). Aucun fallback ne doit masquer une erreur.
    await expect(page.locator('.catalogue .cards')).toHaveAttribute('data-catalogue-paging', 'true');
    await expect(page.locator('[data-time-slider]')).toHaveAttribute('aria-valuetext', 'Aucune limite');
    await expect(page.locator('.recipe-card').first().locator('[data-favorite-toggle]')).toBeVisible();
  });
});
