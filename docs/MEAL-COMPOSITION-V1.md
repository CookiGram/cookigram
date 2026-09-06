# Meal Composition v1 — contenu public

Les recettes peuvent déclarer une qualification `meal` dans leur frontmatter.
Cette qualification est déclarative : elle ne déduit aucune relation depuis le
titre, les tags, les ingrédients, la nutrition ou le texte libre.

```yaml
meal:
  completeness: complete | partial | component
  role: main | starch | vegetable | sauce
  needs: [starch | vegetable | sauce]
  benefits_from: [starch | vegetable | sauce]
```

La tranche canonique de l’issue #200 est :

```text
Porc au caramel: partial/main, needs [starch], benefits_from [vegetable]
Riz blanc long à la casserole: component/starch
```

L’absence du bloc `meal` signifie `unknown`. Une recette `complete` ne
déclare aucune relation. Une recette `component` déclare exactement un rôle et
aucune relation. Les listes ne contiennent ni doublon, ni rôle `main`, ni
intersection entre `needs` et `benefits_from`.

La validation sémantique et l’interprétation déterministe sont consommées par
CookiGram Core (#64). Le validateur public versionné `cookigram-contract`
v1.0.0 valide le frontmatter générique et autorise les champs additionnels ;
il ne porte pas encore ces invariants Meal Composition.
