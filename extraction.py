"""Extraction du catalogue de books.toscrape.com avec Playwright."""

from playwright.sync_api import Page, sync_playwright

URL_ACCUEIL = "https://books.toscrape.com/"

# Exécuté dans le navigateur : une seule passe sur la page au lieu d'un appel par champ.
JS_CATEGORIES = """liens => liens.map(a => ({
    nom: a.textContent.trim(),
    url: a.href,
}))"""

JS_LIVRES = """articles => articles.map(a => ({
    titre: a.querySelector("h3 a").getAttribute("title"),
    prix: a.querySelector(".price_color").textContent,
    note: a.querySelector("p.star-rating").className.replace("star-rating", "").trim(),
    disponibilite: a.querySelector(".availability").textContent.trim(),
    url: a.querySelector("h3 a").href,
}))"""


class ExtracteurCatalogue:
    """Parcourt chaque catégorie du site, page par page, et collecte les livres."""

    def __init__(self, navigateur: str = "chrome", visible: bool = False,
                 max_categories: int | None = None):
        self.navigateur = navigateur
        self.visible = visible
        self.max_categories = max_categories

    def extraire(self) -> list[dict]:
        # "chrome" et "msedge" réutilisent le navigateur déjà installé sur le poste.
        canal = None if self.navigateur == "chromium" else self.navigateur

        with sync_playwright() as p:
            navigateur = p.chromium.launch(headless=not self.visible, channel=canal)
            page = navigateur.new_page()
            # Les images ne servent pas à l'extraction : les bloquer accélère le parcours.
            page.route("**/*.{png,jpg,jpeg}", lambda route: route.abort())

            page.goto(URL_ACCUEIL)
            categories = self._lister_categories(page)
            if self.max_categories:
                categories = categories[: self.max_categories]

            livres = []
            for numero, categorie in enumerate(categories, start=1):
                trouves = self._extraire_categorie(page, categorie)
                livres.extend(trouves)
                print(f"[{numero}/{len(categories)}] {categorie['nom']} : {len(trouves)} livres")

            navigateur.close()
        return livres

    def _lister_categories(self, page: Page) -> list[dict]:
        liens = page.locator("div.side_categories ul li ul li a")
        return liens.evaluate_all(JS_CATEGORIES)

    def _extraire_categorie(self, page: Page, categorie: dict) -> list[dict]:
        livres = []
        url = categorie["url"]
        while url:
            page.goto(url)
            page.wait_for_selector("article.product_pod")
            lignes = page.locator("article.product_pod").evaluate_all(JS_LIVRES)
            for ligne in lignes:
                ligne["categorie"] = categorie["nom"]
            livres.extend(lignes)

            # Pagination : le bouton "next" n'existe pas sur la dernière page.
            suivant = page.locator("li.next a")
            url = suivant.evaluate("a => a.href") if suivant.count() else None
        return livres
