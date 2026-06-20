# -*- coding: utf-8 -*-
"""
Name Resolver v3 — Team-level 名称解析引擎
============================================
整合 CGMBet26 + DJYY + Sofascore → Bet Angel 市场匹配

核心设计：
- 以 BA (Bet Angel) 市场名称为唯一准
- 别名库 team-level: external_name → ba_team_name
- 双向同时匹配: home + away 必须匹配同一市场
- 性别/联赛消歧: 男足≠女足，二队过滤
- 自动学习: 高置信度结果写入别名库

数据流:
  CGMBet26 / DJYY / Sofascore → NameResolver → BA Match Odds / O0.5 / OU 市场 → 下单

API 格式 (from MEMORY.md):
  - getMarketPrices: selections = [{id, back1.prc, lay1.prc, ...}]
  - placeBets: selectionId = INT(不是字符串), type = "BACK"|"LAY"
  - 端点: /api/betting/v1.0/placeBets (不是 /api/markets/v1.0/placeBets)

用法:
  nr = NameResolver()
  nr.register_ba_markets(ba_markets)      # ba_markets = {name: id}
  result = nr.find_match("Flamengo", "Vasco da Gama")
  if result:
      nr.place_bet(result['ba_id'], selection_id, "BACK", price, 1.0)
"""

import sys, json, os, re, unicodedata, time
from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

# ─── 路径 ────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
DATA_DIR   = SCRIPT_DIR.parent / "data"
ALIASES_FILE = DATA_DIR / "team_aliases.json"

# ─── CGMBet26 → BA 缩写映射 ─────────────────────────────
# CGMBet26 数据库球队名 → 标准化缩写（不展开为全称）
CGM_SHORTEN = {
    # 联赛统一缩写
    "athletico go":       "Atletico GO",
    "athletico paranaense":"Athletico PR",
    "atletico go":        "Atletico GO",
    "america fc":         "America FC",
    "botafogo":           "Botafogo",
    "coritiba":           "Coritiba",
    "criciuma":           "Criciuma",
    "cruzeiro":           "Cruzeiro",
    "fluminense":         "Fluminense",
    "gremio":             "Gremio",
    "juventude":          "Juventude",
    "sao paulo":          "Sao Paulo",
    "sport recife":       "Sport",
    "vasco da gama":      "Vasco",
    # 北欧
    "bodo glimt":         "Bodo Glimt",
    "bodø glimt":         "Bodo Glimt",
    "fk bodø/glimt":      "Bodo Glimt",
    "mjällby":            "Mjallby",
    "mjällby aif":        "Mjallby",
    "if brommapojkarna":  "Brommapojkarna",
    "kalmar ff":          "Kalmar FF",
    "ifk göteborg":       "IFK Goteborg",
    "ifk goteborg":       "IFK Goteborg",
    "häcken":             "Hacken",
    "hacken":             "Hacken",
    " Sirius":            "Sirius",
    " Sirius":             "Sirius",
    # 德语圈
    "msv duisburg":       "Duisburg",
    "energie cottbus":    "Cottbus",
    "wehen wiesbaden":    "Wiesbaden",
    "sv wehen":           "Wiesbaden",
    "vfl osnabrück":      "Osnabruck",
    "vfl osnabruck":      "Osnabruck",
    "sc paderborn":       "Paderborn",
    "sc freiburg":        "Freiburg",
    "1.fc köln":          "FC Koln",
    "1.fc koln":          "FC Koln",
    "fc köln":            "FC Koln",
    "tsg 1899 hoffenheim": "Hoffenheim",
    "borussia mönchengladbach": "Mgladbach",
    "eintracht frankfurt": "Eintracht Frankfurt",
    "vfb stuttgart":      "Stuttgart",
    "fc augsburg":        "Augsburg",
    "sv darmstadt 98":    "Darmstadt",
    "darmstadt 98":       "Darmstadt",
    # 荷语/荷甲
    "az alkmaar":         "Az Alkmaar",
    "az":                 "Az Alkmaar",
    "ajax":               "Ajax",
    "psv":                "PSV",
    "feyenoord":          "Feyenoord",
    "fc twente":          "Twente",
    "sc heerenveen":      "Heerenveen",
    "fc groningen":       "Groningen",
    "fortuna sittard":     "Sittard",
    "pec zwolle":         "Zwolle",
    "zwolle":             "Zwolle",
    "nac breda":          "NAC",
    # 葡超
    "sporting cp":        "Sporting Lisbon",
    "sporting braga":     "Braga",
    "fc porto":           "Porto",
    "sl benfica":         "Benfica",
    "boavista":           "Boavista",
    "gil vicente":        "Gil Vicente",
    "estrela红了amadora":  "Estrela Amadora",
    " Casa Pia":          "Casa Pia",
    "vizela":             "Vizela",
    "arouca":             "Arouca",
    # 苏超
    "celtic":             "Celtic",
    "rangers":            "Rangers",
    "hearts":             "Hearts",
    "hibernian":          "Hibernian",
    "aberdeen":           "Aberdeen",
    "st johnstone":       "St Johnstone",
    "dundee utd":         "Dundee Utd",
    " Livingston":         "Livingston",
    # 五大联赛
    "tottenham hotspur":  "Tottenham",
    "tottenham":          "Tottenham",
    "manchester utd":     "Man Utd",
    "manchester city":    "Man City",
    "newcastle utd":      "Newcastle",
    "leicester city":     "Leicester",
    "wolves":             "Wolves",
    "west ham utd":       "West Ham",
    "aston villa":        "Aston Villa",
    "crystal palace":     "Crystal Palace",
    "brighton":           "Brighton",
    "bournemouth":        "Bournemouth",
    "arsenal":            "Arsenal",
    "liverpool":          "Liverpool",
    "chelsea":            "Chelsea",
    "manchester united":  "Man Utd",
    "nottingham forest":  "Nottm Forest",
    "nottm forest":       "Nottm Forest",
    "ipswich":            "Ipswich",
    "luton":              "Luton",
    # 意甲
    "inter":              "Inter",
    "ac milan":           "AC Milan",
    "as roma":            "Roma",
    "lazio":              "Lazio",
    "atalanta":           "Atalanta",
    "fiorentina":         "Fiorentina",
    "torino":             "Torino",
    "bologna":            "Bologna",
    # 西甲
    "real madrid":        "Real Madrid",
    "barcelona":          "Barcelona",
    "atletico madrid":    "Atletico Madrid",
    "sevilla":            "Sevilla",
    "betis":              "Betis",
    "athletic bilbao":    "Athletic Bilbao",
    "real sociedad":      "Real Sociedad",
    "villarreal":         "Villarreal",
    "valencia":           "Valencia",
    "osasuna":            "Osasuna",
    "celta vigo":         "Celta Vigo",
    "granada":            "Granada",
    "alaves":             "Alaves",
    "girona":             "Girona",
    "las palmas":         "Las Palmas",
    "mallorca":           "Mallorca",
    "rayo vallecano":     "Rayo Vallecano",
    # 法甲
    "paris saint-germain":"Paris St-G",
    "paris sg":           "Paris St-G",
    "marseille":          "Marseille",
    "lyon":               "Lyon",
    "monaco":             "Monaco",
    "lille":              "Lille",
    "nice":               "Nice",
    "rennes":             "Rennes",
    "lens":               "Lens",
    "toulouse":           "Toulouse",
    "brest":              "Brest",
    "auxerre":            "Auxerre",
    "lehavre":            "Le Havre",
    "angers":             "Angers",
    "saint-etienne":      "Saint-Etienne",
    "montpellier":        "Montpellier",
    "strasbourg":         "Strasbourg",
    # 土超
    "fenerbahçe":         "Fenerbahce",
    "fenerbahce":         "Fenerbahce",
    "galatasaray":        "Galatasaray",
    "beşiktaş":           "Besiktas",
    "besiktas":           "Besiktas",
    "trabzonspor":        "Trabzonspor",
    "antalyaspor":        "Antalyaspor",
    "kayserispor":        "Kayserispor",
    "kasımpaşa":          "Kasimpasa",
    "sivasspor":          "Sivasspor",
    "alanya":             "Alanyaspor",
    "konyaspor":          "Konyaspor",
    "gazişehir":          "Gazisehir",
    "istanbul başakşehir": "Basaksehir",
    "basaksehir":         "Basaksehir",
    # 罗甲
    "cfr cluj":           "CFR Cluj",
    "steaua bucharest":   "Steaua",
    " FCSB":              "FCSB",
    "dinamo bucuresti":   "Dinamo Bucharest",
    "universitatea craiova":"U Craiova",
    # 挪超/丹超
    "molde":              "Molde",
    " Rosenborg":          "Rosenborg",
    "viking":             "Viking",
    "brann":              "Brann",
    "lillestrøm":         "Lillestrom",
    "odd":                "Odd",
    "sarpsborg 08":       "Sarpsborg",
    "sandefjord":         "Sandefjord",
    "tromso":             "Tromso",
    "bodø/glimt":         "Bodo Glimt",
    "aalesund":           "Aalesund",
    "kfum oslo":           "Kfum Oslo",
    "strømsgodset":       "Stromsgodset",
    "vålerenga":           "Valerenga",
    "fc københavn":       "FC Copenhagen",
    "fck":                "FC Copenhagen",
    "brøndby":            "Brondby",
    "brondby":            "Brondby",
    "aab":                "AaB",
    "randers fc":         "Randers",
    "sønderjysk e":       "SonderjyskE",
    "sonderjyske":        "SonderjyskE",
    "midtjylland":        "Midtjylland",
    "viborg ff":          "Viborg",
    "silkeborg":          "Silkeborg",
    "odense":             "Odense",
    "ob":                 "Odense",
    # 奥地利/瑞士
    "red bull salzburg":  "Red Bull Salzburg",
    "salzburg":           "Red Bull Salzburg",
    "austria wien":       "Austria Wien",
    "sturm graz":         "Sturm Graz",
    "rapid wien":         "Rapid Wien",
    "wacker innsbruck":   "Wacker Innsbruck",
    "lugano":             "Lugano",
    "young boys":         "Young Boys",
    "servette":           "Servette",
    "básel":              "Basel",
    # 波兰/捷克/斯洛伐克
    "legia warszawa":     "Legia Warsaw",
    "pogoń szczecin":     "Pogon Szczecin",
    "lech poznań":        "Lech Poznan",
    "lech":               "Lech Poznan",
    "wisła kraków":       "Wisla Krakow",
    "piast gliwice":      "Piast",
    "cracovia":           "Cracovia",
    "zagłębie lubin":     "Zaglebie",
    "zaglebie":           "Zaglebie",
    " Sparta Praha":       "Sparta Prague",
    "slavia praha":       "Slavia Prague",
    "baník ostrava":      "Banik Ostrava",
    "slovácko":           "Slovacko",
    # 其他
    " Shamrock Rovers":   "Shamrock",
    "shamrock rovers":    "Shamrock",
    "drogheda united":    "Drogheda",
    "shamrock":           "Shamrock",
    "drogheda":           "Drogheda",
    "bohemians":          "Bohemians",
    "st patricks":        "St Patricks",
    "waterford":          "Waterford",
    " Derry City":         "Derry City",
    "sligo rovers":       "Sligo Rovers",
    "fin":                "Finn Harps",
    " Shelbourne":        "Shelbourne",
}

# ─── DJYY → BA 别名库 (高优先级直接映射) ────────────────
DJYY_ALIASES = {
    "paris":              "Paris St-G",
    "lyon":               "Lyon",
    "lille":              "Lille",
    "nice":               "OGC Nice",
    "rennes":             "Rennes",
    "marseille":          "Marseille",
    "monaco":             "Monaco",
    "brest":              "Brest",
    "lens":               "Lens",
    "auxerre":            "AJ Auxerre",
    "koln":               "FC Koln",
    "bayern":             "Bayern Munich",
    "bayern munich":      "Bayern Munich",
    "mainz":              "Mainz 05",
    "nurnberg":           "Nurnberg",
    "magdeburg":          "1. FC Magdeburg",
    "hannover":           "Hannover 96",
    "karlsruhe":          "Karlsruher SC",
    "paderborn":          "SC Paderborn",
    "schalke":            "Schalke 04",
    "salzburg":           "Red Bull Salzburg",
    "inter":              "Inter Milan",
    "flamengo":           "Flamengo",
    "vasco":              "Vasco",
    "botafogo":           "Botafogo",
    "palmeiras":          "Palmeiras",
    "corinthians":        "Corinthians",
    "sao paulo":          "Sao Paulo",
    "gremio":             "Gremio",
    "internacional":      "Internacional",
    "athletico pr":       "Athletico PR",
    "atletico go":        "Atletico GO",
    "atletico mg":        "Atletico MG",
    "cruzeiro":           "Cruzeiro",
    "fluminense":         "Fluminense",
    "santos":             "Santos",
    "bahia":              "Bahia",
    "fortaleza":          "Fortaleza",
    "sport":              "Sport",
    "ceara":              "Ceara",
    "chapecoense":        "Chapecoense",
    "vila nova":          "Vila Nova",
    "criciuma":           "Criciuma",
    "guarani":            "Guarani",
    "cuiaba":             "Cuiaba",
    "america mg":         "America MG",
    "america rn":         "America RN",
    "botafogo sp":        "Botafogo SP",
    "ponte preta":        "Ponte Preta",
    "operario":           "Operario",
    "ituano":             "Ituano",
    "novorizontino":      "Novorizontino",
    "brusque":            "Brusque",
    "avo":                "Avai",
    "novacaixa":          "Nova Iguacu",
    "flamengo rj":        "Flamengo",
    "vasco da gama":      "Vasco",
    "girona":             "Girona",
    "almeria":            "Almeria",
    "alaves":             "Alaves",
    "osasuna":            "Osasuna",
    "valencia":           "Valencia",
    "real sociedad":      "Real Sociedad",
    "real betis":         "Betis",
    "athletic":           "Athletic Bilbao",
    "villareal":          "Villarreal",
    "celta":              "Celta Vigo",
    "granada":            "Granada",
    "mallorca":           "Mallorca",
    "las palmas":         "Las Palmas",
    "rayo":               "Rayo Vallecano",
    "sevilla":            "Sevilla",
    "ferencvaros":        "Ferencvaros",
    "ferencváros":        "Ferencvaros",
    "eto":                "Gyori",
    "pyunik":             "Pyunik",
    "ararat-armenia":     "Ararat-Armenia",
    "nov":                "Novara",
    "bodo":               "Bodo Glimt",
    "bodø":               "Bodo Glimt",
    "glimt":              "Bodo Glimt",
    "molde":              "Molde",
    "rosenborg":          "Rosenborg",
    "brann":              "Brann",
    "bodo/glimt":         "Bodo Glimt",
    "estrela":            "Estrela Amadora",
    "sporting":           "Sporting Lisbon",
    "rio ave":            "Rio Ave",
    "gil vicente":         "Gil Vicente",
    "farense":            "Farense",
    "vizela":             "Vizela",
    "arouca":             "Arouca",
    "casap ram":           "Casa Pia",
    "estoril":            "Estoril",
    "nacional":           "Nacional",
    "porto":              "Porto",
    "benfica":            "Benfica",
    "braga":              "Braga",
    "boavista":           "Boavista",
    "moreirense":         "Moreirense",
    "setubal":            "Setubal",
    "tondela":            "Tondela",
    "arreda":             "Arouca",
    "gallas":             "Arouca",
    "ibernacional":       "Internacional",
    "galatasaray":        "Galatasaray",
    "fenerbahce":         "Fenerbahce",
    "besiktas":           "Besiktas",
    "trabzonspor":        "Trabzonspor",
    "sivasspor":          "Sivasspor",
    "kayserispor":        "Kayserispor",
    "antalyaspor":        "Antalyaspor",
    "konyaspor":          "Konyaspor",
    "goztepe":            "Goztepe",
    "kasimpasa":          "Kasimpasa",
    "alanya":             "Alanyaspor",
    "basaksehir":         "Basaksehir",
    "istanbul basaksehir": "Basaksehir",
    "hearts":             "Heart of Midlothian",
    "hibernian":          "Hibernian",
    "celtic":             "Celtic",
    "rangers":            "Rangers",
    "dundee":             "Dundee Utd",
    "aberdeen":           "Aberdeen",
    "st johnstone":       "St Johnstone",
    "st mirren":          "St Mirren",
    "ross county":        "Ross County",
    "dundee utd":         "Dundee Utd",
    "livingston":         "Livingston",
    "kilmarnock":         "Kilmarnock",
    "motherwell":         "Motherwell",
    "ayr":                "Ayr",
    "partick":            "Partick",
    "greenock":           "Greenock Morton",
    "morton":             "Greenock Morton",
    "dumbarton":          "Dumbarton",
    "queens park":        "Queens Park",
    "Raith":              "Raith Rovers",
    "falkirk":            "Falkirk",
    "inverness":          "Inverness CT",
    "caledonian thistle": "Inverness CT",
    "dynamo kyiv":        "Dynamo Kyiv",
    "shakhtar":           "Shakhtar Donetsk",
    "dnipro":             "Dnipro",
    "metalist":           "Metalist",
    "vorskla":            "Vorskla",
    "zyndrama":           "Zorya",
    "zorja":              "Zorya",
    "austria wien":       "Austria Wien",
    "rapid wien":         "Rapid Wien",
    "sturm graz":         "Sturm Graz",
    "wattens":            "WSG Tirol",
    "hartberg":           "Hartberg",
    "altach":             "Altach",
    "st polten":          "St Polten",
    "ried":               "Ried",
    "a klagenfurt":       "Austria Klagenfurt",
    "austrian":           "Austria Klagenfurt",
    "wiener":             "Wiener SC",
    "horn":               "Horn",
    "lafnitz":            "Lafnitz",
    " SKU":                "SKU Ems",
    "liefering":          "Liefering",
    "grazer":             "Grazer AK",
    "voes":               "First Vienna",
    "st patrick":         "St Patricks",
    "longford":           "Longford",
    "wexford":            "Wexford",
    "cabinteely":         "Cabinteely",
    " Athlone":            "Athlone Town",
    "bray":               "Bray",
    "galway":             "Galway Utd",
    "galway utd":         "Galway Utd",
    "cork":               "Cork City",
    "shamrock":           "Shamrock",
    "drogheda":           "Drogheda",
    "bohemians":          "Bohemians",
    "shamrock rovers":    "Shamrock",
    "drogheda united":    "Drogheda",
    "hafnarfjordur":      "Hafnarfjordur",
    "fh":                 "Hafnarfjordur",
    "fram":               "Fram",
    "vikings":            "Viking",
    "keflavik":           "Keflavik",
    "kr":                 "KR Reykjavik",
    "breidablik":         "Breidablik",
    "ia":                 "IA",
    "ft":                 "Fjolnir",
    "selfoss":            "Selfoss",
    "kv":                 "KV Reykjavik",
    "throttol":           "Throttol",
    "augnablik":          "Augnablik",
    "vestmannaeyjar":     "IBV",
    "ibv":                "IBV",
    "austmann":           "Austmann",
    "klaksvik":           "Klaksvik",
    "b36":                "B36",
    "tvoroyari":          "Tvoroyri",
    "runavik":            "Runavik",
    "nsi":                "NSI",
    "ab":                 "AB",
    "fc sudamericana":    "Sud America",
    "cerro largo":        "Cerro Largo",
    "defensor":           "Defensor Sporting",
    "danubio":            "Danubio",
    "liverpool mtd":     "Liverpool Montevideo",
    "nacional":           "Nacional",
    "penarol":            "Penarol",
    "wanderers":          "Wanderers",
    "racing":             "Racing",
    "boca":               "Boca Juniors",
    "river":              "River Plate",
    "independiente":     "Independiente",
    "velez":              "Velez",
    "huracan":            "Huracan",
    "banfield":           "Banfield",
    "lanus":              "Lanus",
    "argentinos":         "Argentinos Juniors",
    "arsenal sarandi":    "Arsenal S.",
    "atletico tucuman":   "Atletico Tucuman",
    "belgrano":           "Belgrano",
    "talleres":          "Talleres Cordoba",
    "union":             "Union Santa Fe",
    "gimnasia":           "Gimnasia LP",
    "rosario":           "Rosario Central",
    "san lorenzo":       "San Lorenzo",
    "tigre":              "Tigre",
    "barracas":           "Barracas Central",
    "central":            "Central Cordoba",
    "platense":           "Platense",
    "instituto":          "Instituto",
    "alvarado":           " Alvarado",
    "chaco":              "Chaco For Ever",
    "guemes":             "Guemes",
    "san martin tj":     "San Martin T",
    " All Boys":          "All Boys",
    " All Boys":          "All Boys",
    "alumni":             "Alumni",
    "chacarita":         "Chacarita",
    "defensores":         "Defensores Belgrano",
    "deportivo moron":    "Deportivo Moron",
    "ferro":              "Ferro",
    "flandria":          "Flandria",
    "tristan":            " Tristan Suarez",
    "sacachispas":       "Sacachispas",
    "san telmo":         "San Telmo",
    "temperley":          "Temperley",
    "villa dalmine":     "Villa Dalmine",
    "aguirreg":           "Aguirregabiria",
    "v心眼":              "Vasco",
}

# ─── 全局缩写展开 ────────────────────────────────────────
EXPANSIONS = {
    "utd":     "united",        "sheff":  "sheffield",    "manc":    "manchester",
    "boro":    "borough",       "wolves": "wolverhampton", "spurs":   "tottenham",
    "villa":   "aston villa",   "barca":  "barcelona",
    "bayern":  "bayern munich", "dort":   "dortmund",
    "gladbach":"borussia monchengladbach", "glad": "borussia monchengladbach",
    "koln":    "koln",          "nurnberg":"nurnberg",    "nurn":   "nurnberg",
    "hoffenheim":"hoffenheim",  "augsburg":"augsburg",
    "bremen":  "werder bremen", "freiburg":"freiburg",
    "stuttgart":"stuttgart",    "wolfsburg":"wolfsburg",
    "hamburg": "hamburger sv",  "leverkusen":"bayer leverkusen",
    "arsenal": "arsenal fc",
    # DJYY 特殊
    "paris":   "paris saint germain",
    "sporting":"sporting lisbon",
    "braga":   "sporting braga",
    "porto":   "fc porto",
    "lille":   "losc lille",
    "inter":   "inter milan",
    "salzburg":"red bull salzburg",
    "hearts":  "heart of midlothian",
    "hibs":    "hibernian",
    "celtic":  "celtic",
    "rangers": "rangers",
    "ajax":    "ajax",
    "psv":     "psv eindhoven",
    "feyenoord":"feyenoord",
    "az":      "az alkmaar",
    "utrecht": "fc utrecht",
    "twente":  "fc twente",
    "zwolle":  "pec zwolle",
    "heerenveen":"sc heerenveen",
    "groningen":"fc groningen",
    "nac":     "nac breda",
    "viva":    "viva",
    "bodo":    "bodo glimt",
    "bodoglimt":"bodo glimt",
    "molde":   "molde fk",
    "kfum":    "kfum oslo",
    "sonderjyske":"sonderjyske", "sonder":"sonderjyske",
    "midtjylland":"fc midtjylland",
    "brondby": "brondby if",
    "viborg":  "viborg ff",
    "ferencvaros":"ferencvaros tc",
    "gyori":   "eto fc gyor",
    # 波兰
    "legia":   "legia warszawa",
    "lech":    "lech poznan",
    "pogon":   "pogon szczecin",
    "wisla":   "wisla krakow",
    "piast":   "piast gliwice",
    "cracovia":"ks cracovia",
    "zaglebie":"zaglebie lubin",
    # 捷克
    "sparta":  "sparta praha",
    "slavia":  "slavia praha",
    "banik":   "banik ostrava",
    "teplice": "teplice",
    # 罗甲
    "cfr":     "cfr cluj",
    "steaua":  "steaua bucharest",
    "fcsb":    "fcsb",
    "dinamo":  "dinamo bucuresti",
    "craiova": "universitatea craiova",
    # 瑞士/奥
    "lugano":  "fc lugano",
    "yb":      "young boys bern",
    "basel":   "fc basel",
    "zurich":  "fc zurich",
    "stgallen":"fc st gallen",
    "austria": "austria wien",
    "rapid":   "rapid wien",
    "sturm":   "sturm graz",
    "redbull": "red bull salzburg",
    # 土超
    "galatasaray":"galatasaray",
    "fenerbahce":"fenerbahce",
    "besiktas":"besiktas",
    "trabzon":"trabzonspor",
    # 瑞典
    "malmo":   "malmo ff",
    "hacken":  "ifk haken",
    "hacken":  "ifk hacken",
    " Sirius": "ik sirius",
    " Sirius": " Sirius",
    "djurgarden":"djurgardens if",
    "orebro":  "orebro sk",
    "kalmar":  "kalmar ff",
    "ifkg":    "ifk goteborg",
    "malmö":   "malmo ff",
    " Häcken": " Hacken",
    # 芬超
    "hjk":     "hjk helsinki",
    "inter t":"inter turku",
    "kups":    "kuopio psv",
    "honka":   "ac honka",
    "ifk":     "ifk mariehamn",
    "vatten":  "vaasa",
    "kpv":     "kpv",
    # 爱超
    "shamrock":"shamrock rovers",
    "drogheda":"drogheda united",
    "bohs":    "bohemians",
    "st pat":  "st patricks athletic",
    "derry":   "derry city",
    "sligo":   "sligo rovers",
    "finn":    "finn harps",
    "waterford":"waterford fc",
    "cabin":   "cabinteely",
    "cork":    "cork city",
    "galway":  "galway utd",
    "wexford": "wexford fc",
    "longford":"longford town",
    "athlon":  "athlon town",
    # 冰岛
    "fh":      "fh hafnarfjordur",
    "kr":      "kr reykjavik",
    "vik":     "vikingur reykjavik",
    "breid":   "breidablik",
    "kef":     "keflavik if",
    "ibv":     "ibv vestmannaeyjar",
    "ft":      "fjolnir",
    "self":    "selfoss",
    "throt":   "throttol",
    # 匈甲
    "ferencvaros":"ferencvaros tc",
    "ujpe":    "ujpe",
    "dvtk":    "dvtk",
    "haladas": "szombathelyi haladas",
    "honved":  "budapest honved",
    "vasas":   "vasas fc",
    "debrecen":"debreceni vsc",
    "mid":     "mezokovesd",
    "paksi":   "paksi se",
    "zalaegerszeg":"zalaegerszegi te",
    "ujhb":    "ujhb",
    # 塞甲
    "partizan":"partizan belgrade",
    "vojvodina":"fk vojvodina",
    "cg":      "cg",
    "voj":     "vojvodina",
    # 希超
    "paok":    "paok",
    "aek":     "aek athens",
    "olympiacos":"olympiacos",
    "aris":    "aris thessaloniki",
    "of":      "of",
    # 保超
    "cska":    "cska sofia",
    "levski":  "levski sofia",
    "botev":   "botev plovdiv",
    "loko":    "lokomotiv sofia",
    # 挪甲
    "rb":      "bracknell",
    "os":      "odd",
    "viking":  "viking fk",
    "brann":   "sk brann",
    "tromso":  "tromso il",
    "bodog":   "bodo glimt",
    "stroem":  "stroemsgodset",
    "valerenga":"valerenga if",
    "aal":     "aalesund",
    "kfum":    "kfum oslo",
    "sander":  "sandefjord",
    "sarpsborg":"sarpsborg 08",
    "lillestrom":"lillestrom sk",
    "stab":    "stabekk",
    "mf":      "molde fk",
}

# ─── 停用词 ─────────────────────────────────────────────
STOP_WORDS = {
    'fc', 'cf', 'sc', 'afc', 'if', 'ff', 'kf', 'bk', 'fk', 'sk',
    'ac', 'as', 'rc', 'cs', 'cd', 'ca', 'ud', 'sd', 'sl', 'sa', 'sv',
    'vk', 'nk', 'hnk', 'ofk', 'ss', 'rs', 'ns', 'ks', 'ps', 'gs',
    'wd', 'gf', 'tf', 'hf', 'rf', 'ef',
    'the', 'club', 'de', 'do', 'da', 'dos', 'das', 'du', 'del', 'di',
    'la', 'le', 'les', 'united', 'city', 'town', 'sporting', 'sport',
    'sp', 'es', 'ec', 'se', 'ce', 'st', 'saint', 'v', 'vs', 'bp',
    'ii', 'b', 'res', 'reserves', 'reserve',
    'u23', 'u21', 'u19', 'u20', 'u18',
    '04', '05', '06', '07', '08', '09', '10', '11', '12', '13',
    '1893', '1899', '1903', '1904', '1905', '1906', '1907', '1908',
    '1910', '1911', '1912', '1913', '1920', '1945', '1946', '1947',
    # 联赛/组织名
    'as', 'ak', 'sk', 'nk', 'fk', 'uk', 'hk',
    'athletic', 'athletico', 'atlético',
    'de', 'do', 'da', 'del', 'di', 'y', 'e',
    'club', 'sc', 'cf', 'rc', 'ac',
    'afc', 'rfc', 'sfc', 'gfc', 'bfc', 'dfc', 'cfc', 'lfc', 'cfc',
    'real', 'club',
    # 特殊
    'u', 'v', 'ii', 'iii', 'iv',
}


# ─── 工具函数 ───────────────────────────────────────────
def strip_accents(s: str) -> str:
    """去变音符号: Győri → Gyori, Brøndby → Brondby"""
    return ''.join(c for c in unicodedata.normalize('NFKD', s)
                   if not unicodedata.combining(c))


def normalize(s: str) -> str:
    """标准化: 去变音 → 去标点 → 小写 → 合并空格"""
    s = strip_accents(str(s))
    s = s.replace(' - ', ' ').replace('-', ' ')
    s = re.sub(r'[.,/\\()–—:;\'"+*]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s.lower()


def tokenize(s: str) -> list:
    """分词, 过滤停用词和短词"""
    return [t for t in normalize(s).split()
            if t not in STOP_WORDS and len(t) > 1]


def expand(s: str) -> str:
    """递归展开缩写"""
    words = normalize(s).split()
    expanded = []
    for w in words:
        if w in EXPANSIONS:
            exp = EXPANSIONS[w]
            # 递归展开
            for part in exp.split():
                if part in EXPANSIONS and part not in STOP_WORDS:
                    sub = EXPANSIONS[part]
                    expanded.extend(sub.split())
                else:
                    expanded.append(part)
        else:
            expanded.append(w)
    return ' '.join(expanded)


def score_team(ext_name: str, ba_name: str) -> float:
    """
    计算外部队名与 BA 队名的相似度 (0-1)

    策略优先级:
    1. 精确匹配 (1.0)
    2. 去括号后精确 (0.98)
    3. 子串 (0.85-0.9)
    4. 展开→精确 (0.9)
    5. 展开→子串 (0.85)
    6. Token Jaccard + SequenceMatcher (0-0.7)
    """
    ext_n = normalize(ext_name)
    ba_n  = normalize(ba_name)

    if ext_n == ba_n:
        return 1.0

    # 去括号后精确
    ba_nb = re.sub(r'\([^)]*\)', '', ba_n).strip()
    ext_nb = re.sub(r'\([^)]*\)', '', ext_n).strip()
    if ext_nb == ba_nb:
        return 0.98

    # 子串
    if ext_n in ba_n or ba_n in ext_n:
        ratio = min(len(ext_n), len(ba_n)) / max(len(ext_n), len(ba_n))
        return 0.8 + 0.1 * ratio

    # 展开后精确
    ext_e = expand(ext_name)
    ba_e  = expand(ba_name)
    if ext_e == ba_e:
        return 0.9
    if ext_e in ba_e or ba_e in ext_e:
        return 0.85

    # Token Jaccard + SequenceMatcher
    ext_t = set(tokenize(ext_name))
    ba_t  = set(tokenize(ba_name))
    if not ext_t or not ba_t:
        return SequenceMatcher(None, ext_n, ba_n).ratio() * 0.6

    inter = len(ext_t & ba_t)
    union = len(ext_t | ba_t)
    jaccard = inter / union if union else 0
    seq = SequenceMatcher(None, ext_n, ba_n).ratio()
    return 0.6 * jaccard + 0.4 * seq


# ─── NameResolver 主类 ──────────────────────────────────
class NameResolver:
    """
    球队名称解析器 v3
    ─────────────────
    核心方法:
      register_ba_markets(ba_markets)   注册 BA 市场列表
      find_match(home, away, league)    查找比赛
      resolve_batch(ba_markets, events) 批量解析
      place_bet(market_id, sel_id, ...) 下单 (集成 BA API)
    """

    def __init__(self, aliases_file=None):
        self.aliases_file = Path(aliases_file) if aliases_file else ALIASES_FILE
        self.aliases = self._load_aliases()

        # BA 数据
        self._ba_teams  = {}          # {norm_ba_team: original_ba_team}
        self._ba_markets = []          # [{home, away, id, name}]
        self._ba_home_idx = defaultdict(list)
        self._ba_away_idx = defaultdict(list)

        # BA API base
        self._ba_base = "http://localhost:9000/api"
        self._ba_headers = {"Content-Type": "application/json", "Accept": "application/json"}

    # ─── 别名库 ─────────────────────────────────────────
    def _load_aliases(self) -> dict:
        if self.aliases_file.exists():
            try:
                with open(self.aliases_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {k: v for k, v in data.items() if not k.startswith('_')}
            except Exception:
                return {}
        return {}

    def save_aliases(self):
        """保存别名到文件"""
        self.aliases_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.aliases_file, 'w', encoding='utf-8') as f:
            json.dump(self.aliases, f, indent=2, ensure_ascii=False)

    def add_alias(self, external: str, ba_team: str):
        """添加 team-level 别名"""
        if not external or not ba_team:
            return
        key = normalize(external)
        if key:
            self.aliases[key] = ba_team
        # 展开版本
        exp = expand(external)
        exp_key = normalize(exp)
        if exp_key and exp_key != key:
            self.aliases[exp_key] = ba_team

    def learn_from_results(self, results: list, min_score: float = 0.75):
        """从批量结果中学习别名"""
        for r in results:
            if (r.get('score', 0) >= min_score
                    and r.get('ba_home')
                    and r.get('ba_away')):
                self.add_alias(r.get('external_home', ''), r['ba_home'])
                self.add_alias(r.get('external_away', ''), r['ba_away'])
        self.save_aliases()

    # ─── 性别过滤 ───────────────────────────────────────
    _WOMEN_KW  = {'(w)', 'women', 'féminine', 'frauen', 'liga f',
                  'wö', 'damerna', 'damer', 'kvinnor', 'women\'s'}
    _RESERVE_KW = {'ii', 'u23', 'u21', 'u19', 'u20', 'reserves',
                    'reserve', '-b', 'b team', 'r队的', 'r2'}

    @classmethod
    def _is_women(cls, name: str) -> bool:
        n = name.lower()
        return any(k in n for k in cls._WOMEN_KW)

    @classmethod
    def _is_reserve(cls, name: str) -> bool:
        n = normalize(name)
        tokens = n.split()
        return any(t in cls._RESERVE_KW for t in tokens)

    # ─── 注册 BA 市场 ───────────────────────────────────
    def register_ba_markets(self, ba_markets: dict,
                             include_women: bool = False,
                             include_reserves: bool = False):
        """
        注册 BA 市场

        Args:
            ba_markets: {market_name: market_id}
              market_name 格式: "Home Team v Away Team - Match Odds"
              或 "Home Team v Away Team - Over/Under 0.5 Goals"
            include_women:  包含女足
            include_reserves: 包含二队
        """
        self._ba_teams  = {}
        self._ba_markets = []
        self._ba_home_idx = defaultdict(list)
        self._ba_away_idx = defaultdict(list)

        for name, mid in ba_markets.items():
            # 提取纯比赛名
            for suffix in [' - Match Odds', ' - Over/Under 0.5 Goals',
                           ' - Over/Under 0.5 Goal', ' - Over/Under 1.5 Goals',
                           ' - Over/Under 1.5 Goal', ' - Over/Under 2.5 Goals']:
                if name.endswith(suffix):
                    match_name = name[:-len(suffix)].strip()
                    break
            else:
                match_name = name

            if ' v ' not in match_name:
                continue
            if not include_women and self._is_women(match_name):
                continue
            if not include_reserves and self._is_reserve(match_name):
                continue

            parts = match_name.split(' v ')
            if len(parts) != 2:
                continue
            home, away = parts[0].strip(), parts[1].strip()
            idx = len(self._ba_markets)

            self._ba_markets.append({
                'home': home, 'away': away,
                'id': mid, 'name': match_name
            })

            # 索引
            self._ba_home_idx[normalize(home)].append(idx)
            self._ba_away_idx[normalize(away)].append(idx)

            # 注册队名
            self._register_team(home)
            self._register_team(away)

    def _register_team(self, ba_team: str):
        """注册单个 BA 队名"""
        n = normalize(ba_team)
        if n not in self._ba_teams:
            self._ba_teams[n] = ba_team
        # 展开版本
        exp = normalize(expand(ba_team))
        if exp and exp != n and exp not in self._ba_teams:
            self._ba_teams[exp] = ba_team

    # ─── 队名解析 ────────────────────────────────────────
    def _resolve_team(self, ext_name: str) -> list:
        """
        解析外部队名 → BA 队名候选列表
        Returns: [{'ba_team': str, 'score': float, 'method': str}, ...]
        """
        norm = normalize(ext_name)
        candidates = []

        # S1: 精确匹配 BA 队名
        if norm in self._ba_teams:
            candidates.append({'ba_team': self._ba_teams[norm],
                               'score': 1.0, 'method': 'exact'})

        # S1b: CGM 缩写映射
        if norm in CGM_SHORTEN:
            ba = CGM_SHORTEN[norm]
            bn = normalize(ba)
            if bn in self._ba_teams:
                candidates.append({'ba_team': self._ba_teams[bn],
                                  'score': 1.0, 'method': 'cgm_short'})
            else:
                candidates.append({'ba_team': ba,
                                    'score': 0.97, 'method': 'cgm_no_ba'})

        # S1c: DJYY 别名
        if norm in DJYY_ALIASES:
            ba = DJYY_ALIASES[norm]
            bn = normalize(ba)
            if bn in self._ba_teams:
                candidates.append({'ba_team': self._ba_teams[bn],
                                  'score': 1.0, 'method': 'djyy_alias'})
            else:
                candidates.append({'ba_team': ba,
                                    'score': 0.97, 'method': 'djyy_no_ba'})

        # S2: 用户别名库
        if norm in self.aliases:
            ba = self.aliases[norm]
            bn = normalize(ba)
            if bn in self._ba_teams:
                candidates.append({'ba_team': self._ba_teams[bn],
                                  'score': 1.0, 'method': 'alias'})
            else:
                candidates.append({'ba_team': ba,
                                    'score': 0.95, 'method': 'alias_no_ba'})

        # S3: 展开后精确匹配
        exp_n = normalize(expand(ext_name))
        if exp_n != norm and exp_n in self._ba_teams:
            candidates.append({'ba_team': self._ba_teams[exp_n],
                                'score': 0.9, 'method': 'expanded'})

        # S4: 模糊匹配
        if not any(c['score'] >= 0.85 for c in candidates):
            fuzzy = []
            for bn, ba_team in self._ba_teams.items():
                s = score_team(ext_name, ba_team)
                if s >= 0.35:
                    fuzzy.append({'ba_team': ba_team, 'score': s,
                                   'method': 'fuzzy'})
            fuzzy.sort(key=lambda x: x['score'], reverse=True)
            candidates.extend(fuzzy[:3])

        # 去重
        seen, unique = set(), []
        for c in sorted(candidates, key=lambda x: x['score'], reverse=True):
            if c['ba_team'] not in seen:
                seen.add(c['ba_team'])
                unique.append(c)
        return unique[:3]

    def _find_market(self, ba_home: str, ba_away: str) -> int | None:
        """精确查找 BA 市场 (home + away 同时匹配)"""
        for idx, m in enumerate(self._ba_markets):
            if m['home'] == ba_home and m['away'] == ba_away:
                return idx
        return None

    def _fallback_match(self, home: str, away: str,
                         is_women: bool = False) -> dict | None:
        """回退: 对每个 BA 市场做双边模糊匹配"""
        best = None
        best_score = 0
        for m in self._ba_markets:
            if not is_women and self._is_women(m['name']):
                continue
            if is_women and not self._is_women(m['name']):
                continue

            f1 = score_team(home, m['home']) + score_team(away, m['away'])
            f2 = score_team(home, m['away']) + score_team(away, m['home'])
            score = max(f1, f2) / 2
            if score > best_score:
                best_score = score
                swapped = f2 > f1
                best = {
                    'ba_name': m['name'], 'ba_id': m['id'],
                    'score': round(score, 3),
                    'home_score': round(score_team(home, m['away'] if swapped else m['home']), 3),
                    'away_score': round(score_team(away, m['home'] if swapped else m['away']), 3),
                    'ba_home': m['home'], 'ba_away': m['away'],
                    'method': ('high' if score >= 0.75
                               else 'medium' if score >= 0.5
                               else 'low' if score >= 0.35 else 'none'),
                    'swapped': swapped,
                }
        if best and best['score'] >= 0.35:
            return best
        return None

    # ─── 公开 API ────────────────────────────────────────
    def find_match(self, home: str, away: str,
                    league: str = '',
                    is_women: bool | None = None) -> dict | None:
        """
        查找比赛对应的 BA 市场

        Returns: {
          'ba_name': str, 'ba_id': str, 'score': float,
          'home_score': float, 'away_score': float,
          'method': str, 'ba_home': str, 'ba_away': str,
          'swapped': bool
        } or None
        """
        if not self._ba_markets:
            raise RuntimeError("请先调用 register_ba_markets()")

        if is_women is None:
            is_women = (self._is_women(home) or self._is_women(away)
                        or self._is_women(league))

        hc = self._resolve_team(home)
        ac = self._resolve_team(away)
        if not hc or not ac:
            return self._fallback_match(home, away, is_women)

        best = None
        best_score = 0

        for h in hc:
            for a in ac:
                # 正向: h=home, a=away
                idx = self._find_market(h['ba_team'], a['ba_team'])
                if idx is not None:
                    m = self._ba_markets[idx]
                    if (not is_women and self._is_women(m['name'])
                            or is_women and not self._is_women(m['name'])):
                        continue
                    score = (h['score'] + a['score']) / 2
                    if score > best_score:
                        best_score = score
                        best = {
                            'ba_name': m['name'], 'ba_id': m['id'],
                            'score': round(score, 3),
                            'home_score': round(h['score'], 3),
                            'away_score': round(a['score'], 3),
                            'ba_home': m['home'], 'ba_away': m['away'],
                            'method': ('high' if score >= 0.75
                                       else 'medium' if score >= 0.5
                                       else 'low'),
                            'swapped': False,
                        }

                # 反向: h=away, a=home
                idx = self._find_market(a['ba_team'], h['ba_team'])
                if idx is not None:
                    m = self._ba_markets[idx]
                    if (not is_women and self._is_women(m['name'])
                            or is_women and not self._is_women(m['name'])):
                        continue
                    score = (h['score'] + a['score']) / 2
                    if score > best_score:
                        best_score = score
                        best = {
                            'ba_name': m['name'], 'ba_id': m['id'],
                            'score': round(score, 3),
                            'home_score': round(a['score'], 3),
                            'away_score': round(h['score'], 3),
                            'ba_home': m['home'], 'ba_away': m['away'],
                            'method': ('high' if score >= 0.75
                                       else 'medium' if score >= 0.5
                                       else 'low'),
                            'swapped': True,
                        }

        if not best:
            best = self._fallback_match(home, away, is_women)
        return best

    def find_team(self, ext_name: str) -> dict | None:
        """查找单队对应的 BA 队名和市场"""
        candidates = self._resolve_team(ext_name)
        if not candidates:
            return None
        best = candidates[0]
        for m in self._ba_markets:
            if m['home'] == best['ba_team']:
                return {**best, 'market': m['name'],
                         'ba_id': m['id'], 'side': 'home'}
            if m['away'] == best['ba_team']:
                return {**best, 'market': m['name'],
                         'ba_id': m['id'], 'side': 'away'}
        return best

    def resolve_batch(self, ba_markets: dict,
                        external_events: list,
                        source: str = 'unknown') -> list:
        """
        批量解析外部事件 → BA 市场

        Args:
            ba_markets:    {market_name: market_id}
            external_events: [{'home': str, 'away': str, 'league': str, ...}]
            source:         数据源标识

        Returns: list of result dicts
        """
        self.register_ba_markets(ba_markets)
        results = []
        for ev in external_events:
            home = ev.get('home', '')
            away = ev.get('away', '')
            league = ev.get('league', '')
            match = self.find_match(home, away, league)
            results.append({
                'external_home': home,
                'external_away': away,
                'league': league,
                'ba_name': match['ba_name'] if match else None,
                'ba_id': match['ba_id'] if match else None,
                'ba_home': match.get('ba_home') if match else None,
                'ba_away': match.get('ba_away') if match else None,
                'method': match['method'] if match else 'none',
                'score': match['score'] if match else 0,
                'home_score': match['home_score'] if match else 0,
                'away_score': match['away_score'] if match else 0,
                'swapped': match.get('swapped', False) if match else False,
                'source': source,
                **{k: v for k, v in ev.items()
                   if k not in ('home', 'away', 'league')},
            })

        # 自动学习高置信度
        for r in results:
            if (r['score'] >= 0.75 and r.get('ba_home')
                    and r.get('ba_away')):
                self.add_alias(r['external_home'], r['ba_home'])
                self.add_alias(r['external_away'], r['ba_away'])
        return results

    def get_stats(self, results: list) -> dict:
        total = len(results)
        high  = sum(1 for r in results if r.get('score', 0) >= 0.75)
        med   = sum(1 for r in results if 0.5 <= r.get('score', 0) < 0.75)
        low   = sum(1 for r in results if 0.35 <= r.get('score', 0) < 0.5)
        none  = sum(1 for r in results if r.get('score', 0) < 0.35)
        cov   = len({r['ba_id'] for r in results
                      if r.get('ba_id') and r.get('score', 0) >= 0.5})
        return {
            'total': total, 'high': high, 'medium': med,
            'low': low, 'none': none,
            'match_rate': round((high + med) / total * 100, 1) if total else 0,
            'ba_covered': cov, 'ba_total': len(self._ba_markets),
            'ba_coverage': round(cov / len(self._ba_markets) * 100, 1)
                           if self._ba_markets else 0,
        }

    def get_unmatched_ba(self, results: list) -> list:
        matched = {r['ba_id'] for r in results
                   if r.get('ba_id') and r.get('score', 0) >= 0.5}
        return [m for m in self._ba_markets if m['id'] not in matched]

    # ─── BA API 集成 ─────────────────────────────────────
    def get_prices(self, market_id: str) -> list:
        """获取市场实价

        Returns: [{id, name?, back1.prc, lay1.prc, back1.sz, lay1.sz, ...}]
        """
        try:
            r = requests.post(
                f"{self._ba_base}/markets/v1.0/getMarketPrices",
                json={
                    "marketsFilter": {"filter": "SPECIFIED_IDS",
                                       "ids": [market_id]},
                    "dataRequired": ["BEST_THREE_PRICES",
                                      "INPLAY_INFO"]
                },
                headers=self._ba_headers, timeout=10)
            for mkt in r.json().get("result", {}).get("markets", []):
                return mkt.get("selections", [])
        except Exception as e:
            print(f"[NameResolver] get_prices error: {e}")
        return []

    def find_selection(self, market_id: str,
                        selection_hint: str = '') -> dict | None:
        """
        查找最优 selection

        selection_hint: "Over" | "Under" | "Home" | "Draw" | "Away" |
                         "BACK" | "LAY" | '' (auto)
        """
        sels = self.get_prices(market_id)
        if not sels:
            return None

        hint = selection_hint.lower()

        # Auto: 找最高 BACK 价格 (Home) 或最低 (Over)
        if not hint:
            # 选有最高 BACK 价格的 selection
            best = max(sels,
                       key=lambda s: s.get('back1', {}).get('prc', 0))
            return best

        # 按 hint 过滤
        for sel in sels:
            name = sel.get('name', '').lower()
            sid  = str(sel.get('id', '')).lower()
            if hint in name or hint in sid:
                return sel

        # 回退: 返回 BACK 价格最高的
        return max(sels, key=lambda s: s.get('back1', {}).get('prc', 0))

    def place_bet(self, market_id: str,
                   sel_id: int | str,
                   side: str,        # "BACK" | "LAY"
                   price: float,
                   stake: float = 1.0) -> dict:
        """
        下注 (通过 BA API)

        Args:
            market_id:   BA 市场 ID
            sel_id:      selection ID (必须是 INT)
            side:        "BACK" | "LAY"
            price:       赔率
            stake:       本金 (RON)
        """
        payload = {
            "marketId": market_id,
            "async": False,
            "globalSettings": {"persist": True},
            "betsToPlace": [{
                "type": side.upper(),
                "selectionId": int(sel_id),  # INT not string!
                "price": float(price),
                "stake": float(stake),
            }]
        }
        try:
            r = requests.post(
                f"{self._ba_base}/betting/v1.0/placeBets",
                json=payload, headers=self._ba_headers, timeout=15)
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    def get_balance(self) -> float | None:
        """查询 BA 余额"""
        try:
            r = requests.post(
                f"{self._ba_base}/markets/v1.0/getBalance",
                json={}, headers=self._ba_headers, timeout=10)
            return r.json().get("result", {}).get("balance")
        except:
            return None

    # ─── 快捷方法 ───────────────────────────────────────
    def find_and_bet(self, home: str, away: str,
                      side: str = "BACK",
                      max_price: float = 99.0,
                      stake: float = 1.0,
                      selection_hint: str = '') -> dict:
        """
        一句话下单: find_match → get_prices → place_bet

        Returns: {'match': {...}, 'selection': {...}, 'bet': {...}}
        """
        match = self.find_match(home, away)
        if not match:
            return {"error": "No match found"}

        sel = self.find_selection(match['ba_id'], selection_hint)
        if not sel:
            return {"error": "No selection found", "match": match}

        if side.upper() == "BACK":
            price = sel.get('back1', {}).get('prc', 0)
        else:
            price = sel.get('lay1', {}).get('prc', 0)

        if price <= 0 or price > max_price:
            return {"error": f"Price {price} out of range",
                    "match": match, "selection": sel}

        bet = self.place_bet(match['ba_id'], sel['id'],
                              side, price, stake)
        return {"match": match, "selection": sel,
                 "bet": bet, "price": price, "stake": stake}


# ─── CLI 测试 ────────────────────────────────────────────
if __name__ == '__main__':
    import datetime as dt, requests as _req

    BA = "http://localhost:9000"
    tomorrow = (dt.datetime.now() + dt.timedelta(days=1)).strftime("%Y-%m-%d")

    # 1. BA markets
    print("Fetching BA markets...", flush=True)
    r = _req.post(f"{BA}/api/markets/v1.0/getMarkets",
        json={"dataRequired": ["ID","NAME"]},
        headers={"Content-Type":"application/json",
                  "Accept":"application/json"}, timeout=(10,300))
    ba_markets = {m['name']: str(m['id'])
                  for m in r.json().get('result', {}).get('markets', [])
                  if ' - Match Odds' in m.get('name', '')}

    # 2. Sofascore
    print(f"Fetching Sofascore for {tomorrow}...", flush=True)
    try:
        from curl_cffi import requests as cr
        ss = cr.Session(impersonate="chrome")
    except:
        ss = _req.Session()
    try:
        resp = ss.get(
            f"https://api.sofascore.com/api/v1/sport/football/"
            f"scheduled-events/{tomorrow}", timeout=15)
        events = resp.json().get('events', [])
    except Exception as e:
        print(f"Sofascore failed: {e}"); events = []

    SKIP = {'women','féminine','frauen','liga f','u23','u21','u19'}
    ss_events = []
    for ev in events:
        lg  = ev.get('tournament', {}).get('name', '')
        cat = ev.get('tournament', {}).get('category', {}).get('name', '')
        if any(w in lg.lower() for w in SKIP): continue
        h, a = ev.get('homeTeam', {}).get('name', ''), ev.get('awayTeam', {}).get('name', '')
        ts   = ev.get('startTimestamp', 0)
        t    = dt.datetime.fromtimestamp(ts, tz=dt.timezone(dt.timedelta(hours=3))) if ts else None
        ss_events.append({
            'home': h, 'away': a,
            'time': t.strftime("%H:%M") if t else '??',
            'ts': ts, 'league': f"{cat} - {lg}" if cat else lg,
        })

    # 3. Resolve
    nr = NameResolver()
    results = nr.resolve_batch(ba_markets, ss_events, source='sofascore')
    stats = nr.get_stats(results)

    print(f"\n{'='*130}", flush=True)
    print(f"Name Resolver v3 — BA={stats['ba_total']} SS={stats['total']}", flush=True)
    print(f"✅ {stats['high']} ⚠️ {stats['medium']} ❓ {stats['low']} ❌ {stats['none']}"
          f" | SS匹配率={stats['match_rate']}% BA覆盖率={stats['ba_coverage']}%", flush=True)
    print(f"{'='*130}", flush=True)

    good = sorted([r for r in results if r['score'] >= 0.5],
                  key=lambda x: x.get('ts', 0))
    if good:
        print(f"\n{'时间':<6} {'SS主队':<26} {'SS客队':<26} {'BA主队':<22} {'BA客队':<22} {'主%':>5} {'客%':>5} {'总%':>5} {'来源':<8}", flush=True)
        print("-"*130, flush=True)
        for r in good:
            print(f"{r.get('time',''):<6} {r['external_home'][:26]:<26} "
                  f"{r['external_away'][:26]:<26} {(r.get('ba_home','') or '')[:22]:<22} "
                  f"{(r.get('ba_away','') or '')[:22]:<22} {r['home_score']:>5.2f} "
                  f"{r['away_score']:>5.2f} {r['score']:>5.2f} {r.get('source',''):<8}", flush=True)

    unmatched = nr.get_unmatched_ba(results)
    if unmatched:
        print(f"\n🔍 BA有但未匹配Sofascore ({len(unmatched)}场):", flush=True)
        for m in unmatched[:15]:
            print(f"  {m['home']} v {m['away']}", flush=True)

    nr.save_aliases()
    print(f"\n💾 别名库已保存: {nr.aliases_file} ({len(nr.aliases)}条)", flush=True)
