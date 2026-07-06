"""
Perfume History & Formulation Reference Data
=============================================
Curated reference knowledge covering:
1. Historical periods and landmark fragrances
2. Classical formulation structures (accord types)
3. Key perfumers and their signatures
4. Raw material categories and usage
5. IFRA safety and regulatory knowledge
6. Cultural fragrance traditions

This module provides structured data for the expert agent's knowledge base.
"""

from typing import Dict, List
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# 1. Historical Periods & Landmark Fragrances
# ---------------------------------------------------------------------------

PERFUME_HISTORY = [
    {
        "period": "Ancient (3000 BCE - 500 CE)",
        "description": (
            "Fragrance in Mesopotamia, Egypt, Greece, and Rome. Incense trade routes. "
            "Kyphi (Egyptian temple incense blend). Use of myrrh, frankincense, benzoin, "
            "labdanum, rose, jasmine in religious and funerary rites. Distillation developed "
            "by Arabs (Avicenna, ~1000 CE) for rose water."
        ),
        "landmark_fragrances": [
            "Kyphi (Egyptian temple incense)",
            "Megaleion (Greek perfume with myrrh and cinnamon)",
            "Susa perfumes (Persian royal court)",
        ],
        "key_materials": ["myrrh", "frankincense", "labdanum", "cinnamon", "rose", "cassia"],
        "cultural_traditions": ["Egyptian", "Greek", "Roman", "Mesopotamian"],
    },
    {
        "period": "Medieval & Islamic Golden Age (500 - 1400)",
        "description": (
            "Islamic perfumery advances: improved distillation (steam distillation), "
            "alcohol-based perfumes. Al-Kindi writes Kitab Kimiya' al-'Itr (Book of Perfume Chemistry). "
            "Ibn Sina (Avicenna) refines steam distillation of essential oils. "
            "Pomanders and nosegays in Europe. Spices from the Silk Road."
        ),
        "landmark_fragrances": [
            "Rose water (distilled, widespread across Islamic world)",
            "Hungary Water (first alcohol-based perfume, 14th century, attributed to Queen Elizabeth of Hungary)",
        ],
        "key_materials": ["rose", "sandalwood", "oud", "musk", "ambergris", "saffron"],
        "cultural_traditions": ["Islamic", "Byzantine", "Medieval European"],
    },
    {
        "period": "Renaissance & Early Modern (1400 - 1700)",
        "description": (
            "Italian perfumery flourishes in Florence (Catherine de' Medici brings perfumer "
            "Rene to France). Grasse emerges as perfume capital. Glove-makers-perfumers guild "
            "in France. First modern eau de toilette. Animalic notes (musk, civet, ambergris) "
            "used heavily to mask body odor and tanned leather."
        ),
        "landmark_fragrances": [
            "Acqua della Regina (Santa Maria Novella, 1221, oldest still-operating pharmacy)",
            "Eau de Cologne origin precursors",
        ],
        "key_materials": ["civet", "musk", "ambergris", "bergamot", "lavender", "rosemary"],
        "cultural_traditions": ["Italian Renaissance", "French Court", "Grassois"],
    },
    {
        "period": "Age of Eau de Cologne (1700 - 1850)",
        "description": (
            "Jean-Antoine Farina creates original Eau de Cologne (1709) in Cologne, Germany. "
            "Light, citrus-based, refreshing compositions. 4711 Eau de Cologne (1792). "
            "Napoleon reportedly used 60 bottles of Eau de Cologne per month. "
            "Rise of synthetic chemistry: nitrobenzene (first synthetic aroma, 1834), "
            "coumarin synthesized (1868)."
        ),
        "landmark_fragrances": [
            "Farina Eau de Cologne (1709)",
            "4711 Eau de Cologne (1792)",
            "Florida Water (1808)",
        ],
        "key_materials": ["bergamot", "lemon", "neroli", "rosemary", "petitgrain"],
        "cultural_traditions": ["German", "French", "American"],
    },
    {
        "period": "Belle Epoque & Birth of Modern Perfumery (1850 - 1920)",
        "description": (
            "Synthetic chemistry revolutionizes perfumery. Vanillin synthesis (1874), "
            "coumarin (1868), ionones (violet notes, 1893), hydroxycitronellal (lily/muguet, 1905). "
            "Fougere Royale (1882, Houbigant) establishes the fougere family. "
            "Jicky (1889, Guerlain, Aime Guerlain) considered first modern perfume: "
            "combines naturals with synthetics (coumarin, linalool, ethyl vanillin)."
        ),
        "landmark_fragrances": [
            "Fougere Royale (Houbigant, 1882)",
            "Jicky (Guerlain, 1889)",
            "L'Heure Bleue (Guerlain, 1912)",
            "Apres l'Ondee (Guerlain, 1906)",
            "Chanel No. 5 (1921) — bridges to next era",
        ],
        "key_materials": ["coumarin", "vanillin", "ionone", "hydroxycitronellal", "linalool"],
        "cultural_traditions": ["French", "Belle Epoque Paris"],
    },
    {
        "period": "Golden Age of Perfumery (1920 - 1970)",
        "description": (
            "Chanel No. 5 (1921, Ernest Beaux) — first aldehydic floral, revolutionary use of "
            "synthetic aldehydes. Shalimar (1925, Jacques Guerlain) — oriental masterpiece. "
            "Rise of great perfume houses: Guerlain, Caron, Lanvin, Worth, Schiaparelli. "
            "Emergence of chypre family (Mitsouko 1919, Chypre de Coty 1917). "
            "American perfumery emerges post-WWII. Youth-oriented fragrances in the 1960s."
        ),
        "landmark_fragrances": [
            "Chanel No. 5 (Chanel, 1921)",
            "Shalimar (Guerlain, 1925)",
            "Mitsouko (Guerlain, 1919)",
            "Chypre (Coty, 1917)",
            "L'Air du Temps (Nina Ricci, 1948)",
            "Femme (Rochas, 1944)",
            "Cabochard (Grès, 1959)",
            "Calandre (Paco Rabanne, 1969)",
        ],
        "key_materials": ["aldehydes C-12", "bergamot", "patchouli", "oakmoss", "sandalwood", "vetiver"],
        "cultural_traditions": ["French Haute Parfumerie", "American mid-century"],
    },
    {
        "period": "Designer Era & Power Fragrances (1970 - 2000)",
        "description": (
            "Rise of designer fragrances: YSL Opium (1977), Dior Poison (1985). "
            "Power fragrances of the 1980s: Giorgio Beverly Hills, Poison, Obsession. "
            "Fresh/aquatic revolution: Davidoff Cool Water (1988, Pierre Bourdon) introduces "
            "dihydromyrcenol and the aquatic family. CK One (1994) unisex revolution. "
            "Angel (1992, Thierry Mugler, Olivier Cresp) creates the gourmand family. "
            "Fruity-floral trend emerges in late 1990s."
        ),
        "landmark_fragrances": [
            "Opium (YSL, 1977)",
            "Obsession (Calvin Klein, 1985)",
            "Poison (Dior, 1985)",
            "Cool Water (Davidoff, 1988)",
            "Angel (Thierry Mugler, 1992)",
            "CK One (Calvin Klein, 1994)",
            "Le Male (Jean Paul Gaultier, 1995)",
            "Acqua di Gio (Giorgio Armani, 1996)",
        ],
        "key_materials": ["dihydromyrcenol", "ethyl maltol", "calone", "hedione", "Iso E Super"],
        "cultural_traditions": ["American power dressing", "Unisex 90s", "Gourmand"],
    },
    {
        "period": "Niche & Molecular Age (2000 - Present)",
        "description": (
            "Niche perfumery explodes: Le Labo, Byredo, Diptyque, Frederic Malle, Creed. "
            "Molecular/minimalist fragrances: Escentric Molecules (Geza Schoen, 2006) "
            "single-molecule concept (Iso E Super, ambroxan). Oud trend (2009-2016). "
            "Clean/skin scents: Glossier You, Juliette Has A Gun Not A Perfume. "
            "Sustainability and natural perfumery revival. Indie/artisan perfumers. "
            "AI-assisted formulation begins (Symrise, Givaudan). IFRA restrictions reshape classic structures."
        ),
        "landmark_fragrances": [
            "Escentric 01 / Molecule 01 (Escentric Molecules, 2006)",
            "Santal 33 (Le Labo, 2011)",
            "Baccarat Rouge 540 (Maison Francis Kurkdjian, 2015)",
            "Oud Wood (Tom Ford, 2007)",
            "Glossier You (Glossier, 2017)",
            "Not A Perfume (Juliette Has A Gun, 2010)",
            "Aventus (Creed, 2010)",
        ],
        "key_materials": ["Iso E Super", "ambroxan", "ambroxide", "saffron", "oud", "sandalwood"],
        "cultural_traditions": ["Niche/artisanal", "Molecular minimalism", "Sustainable/indie"],
    },
]


# ---------------------------------------------------------------------------
# 2. Classical Formulation Structures (Accord Types)
# ---------------------------------------------------------------------------

CLASSICAL_ACCORDS = {
    "rose_jasmine_violet": {
        "name": "Floral Triad",
        "description": "The foundational floral accord of Western perfumery. Rose provides structure, jasmine adds indolic warmth, violet (ionones) adds powdery sweetness.",
        "typical_proportions": {
            "rose": "30-40%",
            "jasmine": "20-30%",
            "violet/ionone": "10-15%",
            "supporting": "lily of the valley, carnation, ylang-ylang",
        },
        "famous_examples": ["Chanel No. 5", "Joy (Jean Patou)", "Paris (YSL)"],
    },
    "chypre": {
        "name": "Chypre Accord",
        "description": "Built on the contrast between citrus top (bergamot) and mossy-woody base (oakmoss, patchouli, labdanum). The backbone of the chypre family.",
        "typical_proportions": {
            "bergamot": "15-25% (top)",
            "oakmoss": "10-20% (base)",
            "patchouli": "5-15% (base)",
            "labdanum": "5-10% (base)",
            "jasmine/rose": "10-20% (heart)",
        },
        "famous_examples": ["Chypre (Coty)", "Mitsouko (Guerlain)", "Cabochard (Grès)"],
    },
    "fougere": {
        "name": "Fougere Accord",
        "description": "Lavender + oakmoss + coumarin. The masculine fragrance backbone. Fresh-herbal top, sweet-woody base.",
        "typical_proportions": {
            "lavender": "20-30% (top)",
            "oakmoss": "15-25% (base)",
            "coumarin/tonka": "10-20% (base)",
            "geranium": "5-10% (heart)",
            "bergamot": "5-10% (top)",
        },
        "famous_examples": ["Fougere Royale (Houbigant)", "Brut (Fabergé)", "Drakkar Noir (Guy Laroche)"],
    },
    "oriental_ambery": {
        "name": "Oriental/Ambery Accord",
        "description": "Warm, sweet, resinous. Vanilla + balsams + animalics. The foundation of the oriental family.",
        "typical_proportions": {
            "vanilla/vanillin": "15-25%",
            "benzoin/balsams": "10-20%",
            "labdanum/ambrarome": "5-15%",
            "sandalwood": "5-10%",
            "musk/animalic": "5-10%",
        },
        "famous_examples": ["Shalimar (Guerlain)", "Opium (YSL)", "Obsession (CK)"],
    },
    "citrus_cologne": {
        "name": "Eau de Cologne Accord",
        "description": "Light, refreshing citrus blend. The oldest Western fragrance structure. Short-lived by nature.",
        "typical_proportions": {
            "bergamot": "20-30%",
            "lemon": "15-25%",
            "neroli/orange blossom": "10-15%",
            "petitgrain": "5-10%",
            "rosemary/lavender": "5-10%",
        },
        "famous_examples": ["4711", "Farina Eau de Cologne", "Acqua di Parma Colonia"],
    },
    "aquatic_marine": {
        "name": "Aquatic/Marine Accord",
        "description": "Built on calone/dihydromyrcenol + citrus + woody base. Revolutionized masculine perfumery in 1988.",
        "typical_proportions": {
            "calone/maritime aldehyde": "5-15%",
            "dihydromyrcenol": "10-20%",
            "bergamot/citrus": "10-15%",
            "hedione": "5-10%",
            "sandalwood/cedar": "10-15%",
        },
        "famous_examples": ["Cool Water (Davidoff)", "Acqua di Gio (Armani)", "L'Eau d'Issey (Issey Miyake)"],
    },
    "gourmand": {
        "name": "Gourmand Accord",
        "description": "Edible-smelling fragrance built on ethyl maltol, vanillin, caramel notes, chocolate. Invented by Angel (1992).",
        "typical_proportions": {
            "ethyl maltol": "5-15%",
            "vanillin/vanilla": "10-20%",
            "caramel/furfural derivatives": "5-10%",
            "patchouli": "10-20%",
            "chocolate/cocoa": "5-10%",
        },
        "famous_examples": ["Angel (Mugler)", "La Vie Est Belle (Lancôme)", "Black Opium (YSL)"],
    },
    "leather_smoky": {
        "name": "Leather Accord",
        "description": "Smoky, animalic, birch tar or isobutyl quinoline based. One of the oldest fragrance families, originating from perfumed gloves.",
        "typical_proportions": {
            "isobutyl quinoline": "5-10%",
            "birch tar": "5-10%",
            "saffron": "5-10%",
            "musk/civet": "5-10%",
            "suede/aldehyde C-14": "5-10%",
        },
        "famous_examples": ["Knize Ten", "Cuir de Russie (Chanel)", "Bandit (Piguet)"],
    },
    "oud_oriental": {
        "name": "Oud Accord",
        "description": "Built around agarwood (oud) + rose + saffron + amber. Middle Eastern tradition meets Western perfumery post-2007.",
        "typical_proportions": {
            "oud/agarwood": "15-30%",
            "rose": "10-20%",
            "saffron": "5-10%",
            "sandalwood": "5-10%",
            "amber/musk": "10-15%",
        },
        "famous_examples": ["Oud Wood (Tom Ford)", "Oud 27 (Le Labo)", "Royal Oud (Creed)"],
    },
}


# ---------------------------------------------------------------------------
# 3. Key Perfumers & Their Signatures
# ---------------------------------------------------------------------------

MASTER_PERFUMERS = [
    {
        "name": "Ernest Beaux",
        "era": "1910s-1960s",
        "house": "Chanel / Rallet",
        "signature": "Aldehydic florals, Russian-inspired contrasts",
        "masterpieces": ["Chanel No. 5", "Chanel No. 22", "Bois des Iles", "Cuir de Russie"],
        "innovation": "Pioneered use of synthetic aldehydes in high concentration (Chanel No. 5, 1921)",
    },
    {
        "name": "Jacques Guerlain",
        "era": "1894-1955",
        "house": "Guerlain",
        "signature": "Oriental-woody richness, vanillic-ambery depth, emotional compositions",
        "masterpieces": ["Shalimar", "Mitsouko", "L'Heure Bleue", "Vol de Nuit", "Apres l'Ondee"],
        "innovation": "Elevated the oriental family; pioneered the Guerlinade (vanilla, bergamot, rose, tonka accord)",
    },
    {
        "name": "Edmond Roudnitska",
        "era": "1940s-1990s",
        "house": "Independent / Dior / Rochas",
        "signature": "Clarity, restraint, natural-smelling compositions",
        "masterpieces": ["Diorissimo", "Eau Sauvage", "Femme (Rochas)", "Le Parfum de Therese"],
        "innovation": "Pioneered hedione (methyl dihydrojasmonate) in Eau Sauvage (1966); championed natural-smelling simplicity",
    },
    {
        "name": "Jean-Claude Ellena",
        "era": "1970s-2010s",
        "house": "Hermès (in-house), Frederic Malle",
        "signature": "Minimalism, 'writing' fragrance like poetry, economy of means",
        "masterpieces": ["Terre d'Hermès", "Un Jardin sur le Nil", "L'Eau d'Hiver", "Cartier Declaration"],
        "innovation": "Developed 'osmotheque' approach; proof that fewer materials can create more complex perception",
    },
    {
        "name": "Dominique Ropion",
        "era": "1980s-present",
        "house": "IFF / Frederic Malle",
        "signature": "Technical mastery, powerful sillage, classical structure",
        "masterpieces": ["Carnal Flower", "Portrait of a Lady", "La Vie Est Belle", "Amouage Jubilation XXV"],
        "innovation": "Master of the floral-overdose technique; tuberose absolute at unprecedented levels in Carnal Flower",
    },
    {
        "name": "Thierry Wasser",
        "era": "2000s-present",
        "house": "Guerlain (in-house)",
        "signature": "Respect for Guerlain heritage while modernizing",
        "masterpieces": ["L'Instant de Guerlain", "Idylle", "Mon Guerlain"],
        "innovation": "Continues the Guerlinade tradition with contemporary raw materials",
    },
    {
        "name": "Pierre Bourdon",
        "era": "1980s-present",
        "house": "Firmenich / Frederic Malle",
        "signature": "Technical innovation, fresh-mineral compositions",
        "masterpieces": ["Cool Water", "Green Irish Tweed", "Iris Poudre", "French Lover"],
        "innovation": "Created the aquatic family with Cool Water (1988); pioneered dihydromyrcenol use",
    },
    {
        "name": "Geza Schoen",
        "era": "2000s-present",
        "house": "Escentric Molecules / independent",
        "signature": "Single-molecule focus, molecular minimalism",
        "masterpieces": ["Molecule 01 (Iso E Super)", "Molecule 02 (Ambroxan)", "Escentric 01-05"],
        "innovation": "Proved single aroma chemicals can be compelling fragrances; launched molecular perfumery movement",
    },
    {
        "name": "Francis Kurkdjian",
        "era": "1990s-present",
        "house": "MFK (own house) / previously freelance",
        "signature": "Precise, luminous compositions with amber-woody warmth",
        "masterpieces": ["Baccarat Rouge 540", "Le Male (co-creator)", "Aqua Universalis", "Amyris Femme"],
        "innovation": "Baccarat Rouge 540's spun-cotton saffron-amber-woody accord became the most imitated fragrance of the 2020s",
    },
    {
        "name": "Olivier Cresp",
        "era": "1980s-present",
        "house": "Firmenich",
        "signature": "Gourmand innovation, trend-setting compositions",
        "masterpieces": ["Angel (Thierry Mugler)", "Nina (Nina Ricci)", "Omnia (Bulgari)"],
        "innovation": "Created the gourmand family with Angel (1992); pioneered ethyl maltol + patchouli combination",
    },
]


# ---------------------------------------------------------------------------
# 4. Raw Material Categories
# ---------------------------------------------------------------------------

RAW_MATERIAL_CATEGORIES = {
    "citrus_oils": {
        "name": "Citrus Essential Oils",
        "volatility": "top",
        "longevity": "poor (1-3 hours)",
        "materials": [
            {"name": "Bergamot", "origin": "Italy (Calabria), Ivory Coast", "key_compounds": "linalyl acetate, limonene, linalool", "notes": "Fresh, fruity, slightly floral; backbone of Eau de Cologne. FCF (furanocoumarin-free) version required by IFRA for leave-on products."},
            {"name": "Lemon", "origin": "Italy, Spain, Argentina", "key_compounds": "limonene, citral, gamma-terpinene", "notes": "Sharp, fresh, clean. Phototoxic unless distilled."},
            {"name": "Sweet Orange", "origin": "Brazil, USA, Spain", "key_compounds": "limonene (90%+), myrcene", "notes": "Sweet, juicy, cheerful. Very short-lived. Common in top notes."},
            {"name": "Grapefruit", "origin": "USA, Israel, South Africa", "key_compounds": "nootkatone, limonene", "notes": "Bitter, fresh, slightly sulfurous. Nootkatone provides signature bite."},
            {"name": "Yuzu", "origin": "Japan", "key_compounds": "limonene, gamma-terpinene, linalool", "notes": "Mandarin-grapefruit hybrid. Complex citrus with floral undertones."},
        ],
    },
    "floral_absolutes": {
        "name": "Floral Absolutes & Concretes",
        "volatility": "heart",
        "longevity": "moderate (4-8 hours)",
        "materials": [
            {"name": "Rose de Mai Absolute", "origin": "Grasse, Morocco, Bulgaria", "key_compounds": "citronellol, geraniol, nerol, phenethyl alcohol, rose oxide", "notes": "The queen of florals. ~10,000 roses for 5ml absolute. Complex honeyed-rosy-spicy-winey."},
            {"name": "Jasmine Sambac Absolute", "origin": "India, Egypt", "key_compounds": "benzyl acetate, linalool, indole, cis-jasmone", "notes": "Indolic, animalic, sweet. Indole gives the 'ripe' quality."},
            {"name": "Tuberose Absolute", "origin": "India, Mexico", "key_compounds": "methyl salicylate, methyl anthranilate, eugenol, benzyl alcohol", "notes": "Crepuscular, creamy, narcotic. One of the most expensive naturals."},
            {"name": "Iris/Orris Butter", "origin": "Italy (Florence), Morocco", "key_compounds": "alpha-irone, gamma-irone", "notes": "Buttery, powdery, violet-woody. Rhizomes must age 3-5 years. Extremely expensive."},
            {"name": "Narcissus Absolute", "origin": "Grasse, Spain", "key_compounds": "benzyl acetate, methyl benzoate, indole", "notes": "Green, floral, animalic. Rare and costly."},
        ],
    },
    "woods_resins": {
        "name": "Woods & Resins",
        "volatility": "base",
        "longevity": "excellent (12+ hours)",
        "materials": [
            {"name": "Sandalwood (Mysore)", "origin": "India (Mysore), Australia", "key_compounds": "alpha-santalol, beta-santalol", "notes": "Creamy, smooth, meditative. Indian sandalwood (S. album) is endangered; Australian (S. spicatum) is sustainable alternative."},
            {"name": "Oud/Agarwood", "origin": "Southeast Asia, India, Middle East", "key_compounds": "agarospirol, jinkoh-eremol, vetiverol", "notes": "Complex woody-smoky-animalic-sweet. Most expensive raw material in perfumery. Wild harvesting unsustainable; plantation oud emerging."},
            {"name": "Vetiver", "origin": "Haiti, Java, Réunion (Bourbon)", "key_compounds": "vetiverol, vetivone, kousimene", "notes": "Earthy, rooty, smoky, grapefruit-like. Haitian is smoother; Java is smokier; Bourbon is finest."},
            {"name": "Patchouli", "origin": "Indonesia, India, China", "key_compounds": "patchoulol, alpha-bulnesene, alpha-guaiene", "notes": "Earthy, woody, camphoraceous, sweet. Essential to chypre and oriental families. Heart (distilled) version is smoother."},
            {"name": "Cedarwood (Atlas/Virginia)", "origin": "Morocco (Atlas), USA (Virginia)", "key_compounds": "alpha-cedrene, thujopsene, cedrol", "notes": "Dry, woody, pencil-shavings. Atlas is warmer; Virginia is drier."},
            {"name": "Frankincense/Olibanum", "origin": "Oman, Somalia, Yemen", "key_compounds": "alpha-pinene, limonene, alpha-thujene, incensole", "notes": "Resinous, lemony, smoky, meditative. Used in religious ceremony for millennia."},
        ],
    },
    "animalics": {
        "name": "Animalic Materials (Historical & Synthetic)",
        "volatility": "base",
        "longevity": "exceptional (days)",
        "materials": [
            {"name": "Ambergris (natural)", "origin": "Sperm whale (beach-found)", "key_compounds": "ambrein, ambroxide", "notes": "Marine, sweet, tobacco, animalic. ETHICAL: only beach-found ambergris is legal. Now almost entirely replaced by Ambroxan/Ambroxide."},
            {"name": "Ambroxan (synthetic)", "origin": "Synthesized from sclareol or labdanum", "key_compounds": "ambroxide", "notes": "Warm, woody, ambergris-like, mineral. Key material in Baccarat Rouge 540, Not A Perfume, Sauvage."},
            {"name": "Musk (synthetic)", "origin": "Synthetic (galaxolide, habanolide, etc.)", "key_compounds": "galaxolide, habanolide, ethylene brassylate", "notes": "Clean, skin-like, warm. Natural musk deer musk is banned. Multiple synthetic musk families: polycyclic, macrocyclic, alicyclic."},
            {"name": "Civet (historical)", "origin": "Civet cat (now banned in most countries)", "key_compounds": "civetone, skatole", "notes": "Fecal, warm, animalic. Now replaced by synthetic civettone and indolic blends."},
            {"name": "Castoreum (historical)", "origin": "Beaver castor sacs (now mostly synthetic)", "key_compounds": "castorin, benzoic acid", "notes": "Leathery, smoky, animalic. Used in leather accords. Now largely synthetic."},
        ],
    },
    "synthetics": {
        "name": "Key Synthetic Aroma Chemicals",
        "volatility": "varies",
        "longevity": "varies",
        "materials": [
            {"name": "Iso E Super (Tetramethyl octahydro naphthalenfuran)", "key_odor": "velvety, woody, cedar-like, musky", "notes": "Transparent woody-amber. Star of Molecule 01. Enhances other materials. Used in huge quantities in modern perfumery."},
            {"name": "Hedione (Methyl dihydrojasmonate)", "key_odor": "jasmine, fresh, radiant, diffusive", "notes": "Breakthrough material (1960s, Demole). Used in Eau Sauvage. Adds 'radiance' and diffusivity at low concentrations."},
            {"name": "Galaxolide (HHCB)", "key_odor": "clean, musky, sweet, floral", "notes": "Most-used musk in perfumery. Provides the 'clean laundry' and 'skin' note. Environmental concerns due to bioaccumulation."},
            {"name": "Ambroxan (Ambroxide)", "key_odor": "ambergris, warm, woody, mineral", "notes": "Synthetic ambergris surrogate. Star of Sauvage, Baccarat Rouge 540. Very long-lasting."},
            {"name": "Ethyl Maltol", "key_odor": "cotton candy, caramel, strawberry, sweet", "notes": "3-5x sweeter than maltol. The key to the gourmand family. Angel (1992) pioneered its use in fine fragrance."},
            {"name": "Dihydromyrcenol", "key_odor": "fresh, citrus-lavender, metallic, soapy", "notes": "The 'Cool Water molecule'. Revolutionized masculine perfumery. Aggressive top note that fades to clean-woody."},
            {"name": "Calone (Methylbenzodioxepinone)", "key_odor": "marine, melon, watery, ozone", "notes": "The 'sea breeze' molecule. Invented 1966, popularized 1990s. Key to aquatic/marine fragrances."},
            {"name": "Aldehydes C-12 MNA / C-12 MOF", "key_odor": "soapy, waxy, metallic, fatty, champagne-like", "notes": "Revolutionary in Chanel No. 5 (1921). Provide 'lift', 'sparkle', and 'champagne fizz' effect at trace amounts."},
            {"name": "Norlimbanol (Firmyrene / Timberol)", "key_odor": "dry, woody, amber, dusty", "notes": "The 'dry wood' molecule. Provides amber-woody dry-down. Key in Dior Sauvage and many modern masculine fragrances."},
        ],
    },
}


# ---------------------------------------------------------------------------
# 5. IFRA Safety & Regulatory Knowledge
# ---------------------------------------------------------------------------

IFRA_KEY_RESTRICTIONS = {
    "oakmoss": {
        "substance": "Oakmoss (Evernia prunastri) extract and treemoss",
        "restriction": "Maximum 0.1% in leave-on products (Category 4); 0.6% in rinse-off",
        "reason": "Sensitization (atranyl aldehydes). Devastated the chypre family.",
        "impact": "Chypre fragrances must reformulate; synthetic oakmoss substitutes (evernyl) are used",
        "ifra_amendment": "49th Amendment (2020)",
    },
    "citrus_phototoxicity": {
        "substance": "Citrus essential oils containing furanocoumarins (bergamot, lemon, lime, grapefruit)",
        "restriction": "Varies by oil; bergamot FCF (furanocoumarin-free) required for leave-on products",
        "reason": "Phototoxicity (bergapten/psoralen causes UV-induced skin damage)",
        "impact": "All fine fragrances use bergamot FCF or synthetic bergamot reconstructions",
        "ifra_amendment": "48th Amendment",
    },
    "lilial": {
        "substance": "Lilial (Butylphenyl methylpropional / BMHCA)",
        "restriction": "BANNED in EU/UK from March 2022 (CLP Regulation)",
        "reason": "Reproductive toxicity (Cat 1B). Classified as CMR substance.",
        "impact": "Major reformulation required for hundreds of fragrances using lily/muguet accords",
        "ifra_amendment": "EU REACH/CLP, not IFRA-specific",
    },
    "eugenol": {
        "substance": "Eugenol (found in clove, cinnamon leaf, ylang-ylang)",
        "restriction": "Maximum 0.5% in leave-on products",
        "reason": "Sensitization potential",
        "impact": "Restricts use of clove, cinnamon, and some ylang-ylang oils in fine fragrance",
        "ifra_amendment": "49th Amendment",
    },
    "coumarin": {
        "substance": "Coumarin (found in tonka bean, lavender, sweetgrass)",
        "restriction": "Restricted in some categories; specific limits vary",
        "reason": "Hepatotoxicity in high doses (though fine fragrance concentrations are safe)",
        "impact": "Fougere and oriental formulations must account for limits",
        "ifra_amendment": "49th Amendment",
    },
}


# ---------------------------------------------------------------------------
# 6. Cultural Fragrance Traditions
# ---------------------------------------------------------------------------

CULTURAL_TRADITIONS = {
    "french_haute_parfumerie": {
        "name": "French Haute Parfumerie",
        "period": "17th century - present",
        "center": "Grasse, Paris",
        "characteristics": (
            "Complex, multi-layered compositions. Emphasis on natural raw materials "
            "(historically) blended with synthetics. Heritage houses (Guerlain, Chanel, Dior) "
            "embody tradition. The 'Guerlinade' is a cultural touchstone."
        ),
        "key_structures": ["floral aldehydic", "chypre", "oriental", "fougere"],
        "representative_materials": ["rose de mai", "jasmine de grasse", "iris butter", "oakmoss", "bergamot"],
    },
    "middle_eastern_attar": {
        "name": "Middle Eastern Attar Tradition",
        "period": "Ancient - present",
        "center": "Arabian Peninsula, Persia, Ottoman Empire",
        "characteristics": (
            "Oil-based perfumery (attar/itr) applied to skin and clothing. "
            "Heavy use of oud, rose, saffron, musk, ambergris. Layering culture. "
            "Bakhoor (incense burning) for clothing and home. "
            "Concentration valued over subtlety."
        ),
        "key_structures": ["oud-rose", "amber-oud", "saffron-oud"],
        "representative_materials": ["oud", "taif rose", "saffron", "deer musk (historical)", "ambergris"],
    },
    "indian_gandha": {
        "name": "Indian Gandha (Perfumery) Tradition",
        "period": "Vedic period (1500 BCE) - present",
        "center": "Kannauj, Tamil Nadu",
        "characteristics": (
            "Attar production by hydrodistillation into sandalwood oil base. "
            "Mitti attar (baked earth after rain, petrichor). Flower garlands (pushpanjali). "
            "Ayurvedic principles: fragrance for dosha balancing. "
            "Integration with spiritual practice (puja, meditation)."
        ),
        "key_structures": ["floral-woody (rose-sandalwood)", "spicy-woody", "earthy (mitti)"],
        "representative_materials": ["sandalwood", "jasmine sambac (motia)", "champa", "vetiver (khus)", "rajkamal"],
    },
    "japanese_kodo": {
        "name": "Japanese Kōdō (Way of Fragrance)",
        "period": "6th century - present",
        "center": "Kyoto",
        "characteristics": (
            "Appreciation of fragrance as art form (listening to incense, not smelling). "
            "Minimalist aesthetic. Mon-kō (incense appreciation ceremony). "
            "Seasonal awareness (kōdō follows utsuroi). Natural materials only."
        ),
        "key_structures": ["resinous-woody", "floral-aquatic (seasonal)"],
        "representative_materials": ["kyara (highest grade oud)", "sandalwood", "aloeswood", "cinnamon bark", "cloves"],
    },
    "chinese_xiang": {
        "name": "Chinese Incense Culture (Xiang)",
        "period": "Han Dynasty (206 BCE) - present",
        "center": "Fujian, Guangdong",
        "characteristics": (
            "Incense as scholarly and meditative practice. Competition with Japanese kōdō. "
            "Chenxiang (agarwood) as the most prized material. "
            "Blending principles from Traditional Chinese Medicine (TCM). "
            "Scholar's studio incense traditions."
        ),
        "key_structures": ["woody-resinous", "floral-spicy", "medicinal-earthy"],
        "representative_materials": ["chenxiang (agarwood)", "ruxiang (frankincense)", "tanxiang (sandalwood)", "dingxiang (clove)"],
    },
}


# ---------------------------------------------------------------------------
# Access Functions
# ---------------------------------------------------------------------------

def get_all_reference_data() -> dict:
    """Return all reference data as a single dictionary for the knowledge base."""
    return {
        "perfume_history": PERFUME_HISTORY,
        "classical_accords": CLASSICAL_ACCORDS,
        "master_perfumers": MASTER_PERFUMERS,
        "raw_material_categories": RAW_MATERIAL_CATEGORIES,
        "ifra_restrictions": IFRA_KEY_RESTRICTIONS,
        "cultural_traditions": CULTURAL_TRADITIONS,
    }


def search_reference(query: str) -> List[dict]:
    """Simple keyword search across all reference data."""
    results = []
    query_lower = query.lower()
    data = get_all_reference_data()

    for category, entries in data.items():
        if isinstance(entries, list):
            for entry in entries:
                text = json.dumps(entry).lower()
                if query_lower in text:
                    results.append({"category": category, "data": entry})
        elif isinstance(entries, dict):
            for key, entry in entries.items():
                text = json.dumps(entry).lower()
                if query_lower in text:
                    results.append({"category": category, "key": key, "data": entry})

    return results


import json
