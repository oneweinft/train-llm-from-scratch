"""
Fragrance Agent Configuration
=============================
Central configuration for all scrapers, data processors, knowledge graph,
and expert agent components.
"""

import os

# --- Project Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "knowledge")

# Raw output files
TGSC_MOLECULES_FILE = os.path.join(RAW_DIR, "tgsc_molecules.jsonl")
TGSC_ODOR_TYPES_FILE = os.path.join(RAW_DIR, "tgsc_odor_types.json")
FRAGNANTICA_PERFUMES_FILE = os.path.join(RAW_DIR, "fragrantica_perfumes.jsonl")
FRAGNANTICA_NOTES_FILE = os.path.join(RAW_DIR, "fragrantica_notes.json")
BASENOTES_PERFUMES_FILE = os.path.join(RAW_DIR, "basenotes_perfumes.jsonl")

# Processed output files
CANONICAL_MOLECULES_FILE = os.path.join(PROCESSED_DIR, "canonical_molecules.json")
CANONICAL_NOTES_FILE = os.path.join(PROCESSED_DIR, "canonical_notes.json")
CANONICAL_PERFUMES_FILE = os.path.join(PROCESSED_DIR, "canonical_perfumes.json")
COOCCURRENCE_GRAPH_FILE = os.path.join(PROCESSED_DIR, "cooccurrence_graph.json")
MOLECULE_ODOR_GRAPH_FILE = os.path.join(PROCESSED_DIR, "molecule_odor_graph.json")
KNOWLEDGE_BASE_FILE = os.path.join(KNOWLEDGE_DIR, "fragrance_knowledge_base.json")

# --- TGSC Scraper Config ---
TGSC_BASE_URL = "https://www.thegoodscentscompany.com"
TGSC_ODOR_LIST_URL = f"{TGSC_BASE_URL}/allodor.html"
TGSC_DATA_PATH = "/data/rw{cas_id}.html"
TGSC_RATE_LIMIT_SECONDS = 1.0  # Delay between requests (be polite)
TGSC_MAX_RETRIES = 3

# --- Fragrantica Scraper Config ---
FRAGNANTICA_BASE_URL = "https://www.fragrantica.com"
FRAGNANTICA_SEARCH_URL = f"{FRAGNANTICA_BASE_URL}/search/"
FRAGNANTICA_RATE_LIMIT_SECONDS = 2.0  # Fragrantica is aggressive with blocking
FRAGNANTICA_MAX_RETRIES = 3

# --- Basenotes Scraper Config ---
BASENOTES_BASE_URL = "https://www.basenotes.net"
BASENOTES_RATE_LIMIT_SECONDS = 2.0

# --- Odor Category Taxonomy ---
# 15 primary odor families (analogous to Epicure's 15 compound types)
# Mapped from TGSC's ~500+ specific odor types into top-level categories
ODOR_FAMILIES = {
    "floral": [
        "floral", "rose", "jasmin", "lily", "lily of the valley", "muguet",
        "carnation", "violet", "iris", "orris", "narcissus", "hyacinth",
        "tuberose", "gardenia", "magnolia", "peony", "freesia", "lilac",
        "heliotrope", "cyclamen", "orchid", "osmanthus", "neroli", "orangeflower",
        "acacia", "mimosa", "jonquil", "honeysuckle", "sweet pea", "privetblossom",
        "chrysanthemum", "marigold", "daffodil", "genet", "broom",
    ],
    "woody": [
        "woody", "cedar", "cedarwood", "sandalwood", "vetiver", "patchouli",
        "guaiacwood", "oakmoss", "mahogany", "sawdust", "woody burnt wood",
        "woody oak wood", "woody old wood", "sandy", "rooty",
    ],
    "citrus": [
        "citrus", "lemon", "lemon peel", "lime", "orange", "orange peel",
        "grapefruit", "grapefruit peel", "bergamot", "mandarin", "tangerine",
        "kumquat", "yuzu", "clementine", "citronella", "citrus peel",
        "citrus rind", "peely", "rindy", "zesty", "petitgrain", "bois de rose",
    ],
    "spicy": [
        "spicy", "cinnamon", "clove", "cassia", "nutmeg", "cardamom",
        "pepper black pepper", "peppery", "ginger", "cumin", "coriander",
        "caraway", "allspice", "pimenta", "mace", "sassafrass", "horseradish",
        "mustard", "wasabi", "curry", "turmeric", "saffron", "ajwain",
    ],
    "amber": [
        "amber", "ambergris", "labdanum", "opoponax", "benzoin", "tolu balsam",
        "peru balsam", "storax", "cistus", "balsamic", "resinous", "copaiba",
        "myrrh", "frankincense", "elemi", "mastic",
    ],
    "musky": [
        "musk", "ambrette", "civet", "castoreum", "animal", "fecal",
        "urine", "sweaty", "skunk", "ammoniacal", "goaty",
    ],
    "green": [
        "green", "grassy", "leafy", "foliage", "hay", "hay new mown hay",
        "cucumber", "cucumber skin", "pea green pea", "bean green bean",
        "cut grass", "galbanum", "stemmy", "sappy", "fig leaf",
        "tomato leaf", "violet leaf", "dewy", "fresh outdoors",
    ],
    "fruity": [
        "fruity", "apple", "peach", "apricot", "pear", "plum", "cherry",
        "berry", "strawberry", "raspberry", "blackberry", "blueberry",
        "currant black currant", "currant red currant", "pineapple", "mango",
        "papaya", "passion fruit", "guava", "lychee", "banana", "coconut",
        "melon", "cantaloupe", "watermelon", "grape", "fig", "date",
        "pomegranate", "cranberry", "tropical", "fruit tropical fruit",
        "fruit ripe fruit", "fruit dried fruit", "juicy", "pulpy",
        "cotton candy", "bubble gum", "tutti frutti",
    ],
    "gourmand": [
        "chocolate", "cocoa", "vanilla", "caramellic", "honey", "toffee",
        "fudge", "butterscotch", "praline", "almond", "marzipan", "cookie",
        "cake", "marshmallow", "popcorn", "graham cracker", "maple",
        "molasses", "sugar", "sugar brown sugar", "sugar burnt sugar",
        "buttermilk", "creamy", "milky", "buttery", "chocolate dark chocolate",
        "chocolate milk chocolate", "chocolate white chocolate",
    ],
    "aquatic": [
        "marine", "ocean", "seashore", "seaweed", "ozone", "watery",
        "rain", "fresh", "clean", "cooling",
    ],
    "aromatic_herbal": [
        "herbal", "lavender", "rosemary", "thyme", "basil", "sage",
        "sage clary sage", "marjoram", "origanum", "fennel", "dill",
        "tarragon", "chervil", "minty", "peppermint", "spearmint",
        "cornmint", "pennyroyal", "eucalyptus", "camphoreous", "mentholic",
        "wintergreen", "horehound", "hyssop", "lovage", "angelica",
        "chamomile", "wormwood", "absinthe", "artemisia", "calamus",
        "lemongrass", "palmarosa", "citronella",
    ],
    "powdery": [
        "powdery", "orris", "violet", "heliotrope", "coumarinic",
        "tonka", "soft", "musk", "clean",
    ],
    "leathery": [
        "leathery", "smoky", "burnt", "charred", "tobacco", "tar",
        "phenolic", "smoked", "smoky", "guaiacol", "pyrogenic",
    ],
    "aldehydic": [
        "aldehydic", "soapy", "waxy", "fatty", "oily", "greasy",
        "metallic", "ethereal", "chemical", "acrylate", "solvent",
        "painty", "naphthyl", "styrene", "terpenic", "ketonic",
        "lactonic",
    ],
    "earthy": [
        "earthy", "mossy", "moldy", "musty", "humus", "mushroom",
        "fungal", "rooty", "dusty", "dirt", "potato raw potato",
        "damp", "vegetable", "root vegetable",
    ],
}

# Reverse mapping: specific odor type -> family
ODOR_TYPE_TO_FAMILY = {}
for family, types in ODOR_FAMILIES.items():
    for t in types:
        ODOR_TYPE_TO_FAMILY[t.lower()] = family

# --- Fragrance Family Taxonomy (Olfactive Classification) ---
FRAGRANCE_FAMILIES = [
    "Floral",
    "Oriental",
    "Woody",
    "Fresh",
    "Aromatic Fougere",
    "Chypre",
    "Citrus",
    "Leather",
]

# --- Note Pyramid Layers ---
NOTE_LAYERS = ["top", "heart", "base"]

# --- IFRA Safety Categories ---
IFRA_CATEGORIES = {
    1: "Lip products",
    2: "Deodorant/antiperspirant",
    3: "Hydroalcoholics shaved skin",
    4: "Hydroalcoholics unshaved skin",
    5: "Hand cream",
    6: "Mouthwash",
    7: "Intimate wipes",
    8: "Hair styling aids",
    9: "Rinse-off hair care",
    10: "Body lotion",
    11: "Eye products",
    12: "Body powder",
}

# --- Agent Config ---
AGENT_NAME = "Epicure-Fragrance"
AGENT_MODEL = "gpt-4"  # or local model
AGENT_MAX_CONTEXT_TOKENS = 8000
AGENT_TEMPERATURE = 0.3

print(f"Fragrance Agent config loaded. Data dir: {DATA_DIR}")
