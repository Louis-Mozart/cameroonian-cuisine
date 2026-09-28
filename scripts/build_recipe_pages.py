#!/usr/bin/env python3
"""
Extracts each <article class="recipe-block"> from index.html and generates
a standalone, SEO-optimized page per recipe under /recettes/<id>.html,
complete with Recipe (schema.org) JSON-LD structured data, bilingual FR/EN
toggle, shared styling, and links back to the main site + the cookbook upsell.
"""
import re
import os
import html
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
OUT_DIR = os.path.join(ROOT, "recettes")
os.makedirs(OUT_DIR, exist_ok=True)

with open(INDEX, "r", encoding="utf-8") as f:
    src = f.read()

# ---- Extract shared <style> block ----
style_match = re.search(r"<style>(.*?)</style>", src, re.S)
STYLE = style_match.group(1)

# ---- Extract each recipe article block ----
article_re = re.compile(r'<article class="recipe-block" id="([a-z]+)">(.*?)</article>', re.S)
articles = article_re.findall(src)

# Metadata: id -> (french title, english title, french desc snippet, image, minutes iso, servings)
META = {
    "ndole":    dict(fr="Ndolé", en="Ndolé — Cameroon's National Stew", img="images/image14.jpg", time="PT1H30M", serv=4, num="01"),
    "eru":      dict(fr="Eru & Water Fufu", en="Eru & Water Fufu — South-West Classic", img="images/image7.jpg", time="PT1H45M", serv=5, num="02"),
    "beignets": dict(fr="Beignets Haricots", en="Bean Fritters & Beans", img="images/image3.jpg", time="PT1H15M", serv=4, num="03"),
    "mbongo":   dict(fr="Mbongo Tchobi", en="Mbongo Tchobi — Black Spice Fish Stew", img="images/image13.jpg", time="PT1H20M", serv=4, num="04"),
    "koki":     dict(fr="Koki", en="Koki — Steamed Bean Cake", img="images/image4.jpg", time="PT2H", serv=5, num="05"),
    "pouletdg": dict(fr="Poulet DG", en="Poulet DG — \"Director General\" Chicken", img="images/image10.jpg", time="PT1H15M", serv=4, num="06"),
    "pistache": dict(fr="Sauce Pistache & Couscous de Manioc", en="Pumpkin Seed Sauce & Cassava Couscous", img="images/image1.jpg", time="PT1H30M", serv=5, num="07"),
    "okok":     dict(fr="Okok", en="Okok — Bëti Leaf & Peanut Stew", img="images/image12.jpg", time="PT1H30M", serv=5, num="08"),
    "couscous": dict(fr="Couscous de Maïs & Légumes", en="Corn Couscous & Vegetables", img="images/image16.jpg", time="PT1H", serv=4, num="09"),
    "plantain": dict(fr="Frites de Plantain Mûr & Haricots Rouges", en="Fried Ripe Plantain & Red Beans", img="images/image9.jpg", time="PT1H15M", serv=4, num="10"),
    "poisson":  dict(fr="Poisson Braisé à la Camerounaise", en="Cameroonian-Style Grilled Fish", img="images/image5.jpg", time="PT1H20M", serv=4, num="11"),
    "jollof":   dict(fr="Jollof Rice au Poulet", en="Jollof Rice with Chicken", img="images/image2.jpg", time="PT1H15M", serv=5, num="12"),
    "taro":     dict(fr="Taro & Sauce Jaune", en="Taro & Yellow Sauce", img="images/image11.jpg", time="PT2H", serv=6, num="13"),
    "pile":     dict(fr="Pilé de Pommes de Terre & Haricots", en="Pounded Potato & Black Beans", img="images/image6.jpg", time="PT1H", serv=4, num="14"),
    "spaghetti":dict(fr="Spaghettis Sautés à la Camerounaise", en="Cameroonian Stir-Fried Spaghetti", img="images/image8.jpg", time="PT45M", serv=4, num="15"),
    "kondre":   dict(fr="Kondré", en="Kondré — Unripe Plantain & Meat Stew", img="images/image15.jpg", time="PT2H", serv=6, num="16"),
}

# French descriptions used for SEO meta description + schema description (short excerpt)
DESC_RE = re.compile(r'<div class="desc-box fr">(.*?)</div>', re.S)
STEPS_FR_RE = re.compile(r'<ol class="steps-list fr">(.*?)</ol>', re.S)
STEP_ITEM_RE = re.compile(r'<span class="step-num">\d+</span><span>(.*?)</span>', re.S)
ING_RE = re.compile(r'<div class="ingredient-item"><span class="fr">(.*?)</span>', re.S)

def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

NAV_LINKS = "\n".join(
    f'  <a href="{rid}.html">{META[rid]["fr"].split(" & ")[0].split(" (")[0]}</a>'
    for rid in META
)

for rid, block in articles:
    meta = META.get(rid)
    if not meta:
        continue
    desc_match = DESC_RE.search(block)
    desc_text = strip_tags(desc_match.group(1)) if desc_match else ""
    meta_description = (desc_text[:155] + "…") if len(desc_text) > 155 else desc_text

    steps_match = STEPS_FR_RE.search(block)
    steps = STEP_ITEM_RE.findall(steps_match.group(1)) if steps_match else []
    steps_clean = [strip_tags(s) for s in steps]

    ingredients = [strip_tags(x) for x in ING_RE.findall(block)]

    title_fr = meta["fr"]
    title_en = meta["en"]
    canonical = f"https://louis-mozart.github.io/cameroonian-cuisine/recettes/{rid}.html"

    recipe_schema = {
        "@context": "https://schema.org/",
        "@type": "Recipe",
        "name": title_fr,
        "image": [f"https://louis-mozart.github.io/cameroonian-cuisine/{meta['img']}"],
        "author": {"@type": "Person", "name": "Téclaire Writes"},
        "description": meta_description,
        "recipeCuisine": "Cameroonian",
        "recipeCategory": "Main Course",
        "prepTime": "PT20M",
        "cookTime": meta["time"],
        "recipeYield": f"{meta['serv']} servings",
        "recipeIngredient": ingredients,
        "recipeInstructions": [
            {"@type": "HowToStep", "text": s} for s in steps_clean
        ],
        "inLanguage": "fr",
    }
    schema_json = json.dumps(recipe_schema, ensure_ascii=False, indent=2)

    page = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title_fr} — Recette Camerounaise | {title_en} Recipe</title>
<meta name="description" content="{html.escape(meta_description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title_fr)} — {html.escape(title_en)}">
<meta property="og:description" content="{html.escape(meta_description)}">
<meta property="og:image" content="https://louis-mozart.github.io/cameroonian-cuisine/{meta['img']}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;0,900;1,400;1,700&family=Lato:wght@300;400;700&family=Lobster&display=swap" rel="stylesheet">
<script type="application/ld+json">
{schema_json}
</script>
<style>
{STYLE}
.breadcrumb {{ max-width:960px;margin:0 auto;padding:18px 24px 0; font-size:.82rem; }}
.breadcrumb a {{ color:var(--green); text-decoration:none; font-weight:700; }}
.breadcrumb span {{ color:var(--text-light); margin:0 6px; }}
.recipe-page-header {{ max-width:960px;margin:0 auto;padding:20px 24px 0; }}
.back-cta {{ display:block; text-align:center; margin:40px auto; }}
.upsell-strip {{ max-width:960px;margin:60px auto 0;padding:24px;background:linear-gradient(135deg,var(--green-dark),var(--green));border-radius:16px;color:#fff;text-align:center; }}
.upsell-strip h3 {{ font-family:'Playfair Display',serif; margin-bottom:10px; color:var(--gold); }}
.upsell-strip a.cta {{ display:inline-block;margin-top:12px;background:var(--gold);color:var(--green-dark);padding:10px 22px;border-radius:24px;text-decoration:none;font-weight:800; }}
</style>
</head>
<body data-lang="fr">
<div id="lang-bar">
  <button class="lang-btn active" onclick="setLang('fr')">&#127467;&#127479; FR</button>
  <button class="lang-btn" onclick="setLang('en')">&#127468;&#127463; EN</button>
</div>

<nav class="site-nav">
  <a href="../index.html">{'← Toutes les recettes'}</a>
{NAV_LINKS}
</nav>

<div class="breadcrumb">
  <a href="../index.html">Accueil</a><span>/</span><a href="../index.html#{rid}">Recettes</a><span>/</span>{title_fr}
</div>

<div class="recipes-wrapper">
<article class="recipe-block" id="{rid}">{block}</article>
</div>

<div class="upsell-strip">
  <h3><span class="fr">Envie des 16 recettes en un seul livre&nbsp;?</span><span class="en">Want all 16 recipes in one book?</span></h3>
  <p><span class="fr">Le livre num&eacute;rique inclut plus de recettes, un guide du d&eacute;butant et des listes de courses.</span><span class="en">The digital cookbook includes more recipes, a beginner's guide and shopping lists.</span></p>
  <a class="cta" href="../index.html#cookbook"><span class="fr">Voir le livre num&eacute;rique →</span><span class="en">See the digital cookbook →</span></a>
</div>

<a class="back-cta" href="../index.html"><span class="fr">&larr; Retour &agrave; toutes les recettes</span><span class="en">&larr; Back to all recipes</span></a>

<footer>
  <div class="footer-logo">T&eacute;claire Writes</div>
  <p class="fr">Merci de voyager avec moi &agrave; travers les saveurs du Cameroun. <span class="heart">&#9829;</span></p>
  <p class="en">Thank you for journeying with me through the flavours of Cameroon. <span class="heart">&#9829;</span></p>
  <p style="margin-top:16px;font-size:.8rem;opacity:.5;">&copy; 2026 T&eacute;claire Writes &middot; Un Voyage dans les Repas Camerounais</p>
</footer>

<script>
  function setLang(lang) {{
    document.body.dataset.lang = lang;
    document.querySelectorAll('.lang-btn').forEach(function(btn) {{
      btn.classList.toggle('active', btn.textContent.toLowerCase().indexOf(lang) !== -1);
    }});
  }}
</script>
</body>
</html>
"""
    out_path = os.path.join(OUT_DIR, f"{rid}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote", out_path)

print(f"\nDone. Generated {len(articles)} recipe pages in {OUT_DIR}")
