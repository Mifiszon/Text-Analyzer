from flask import Flask, render_template
from markupsafe import Markup
import os
import re
from clp3 import clp

app = Flask(__name__)

# 1. KONFIGURACJA
CONFIG = {
    "roles": {
        "sprawca": ["senna", "ayrton", "brazylijczyk", "ratzenberger", "roland"],
        "zdarzenie": ["wypadek", "wyścig", "śmierć", "grand prix", "okrążenie"],
        "obiekt": ["samochód", "bolid", "williams", "zespół", "tor"],
        "narzedzie": ["formuła", "prędkość", "km/h", "zakręt"],
        "miejsce": ["imola", "san marino", "tamburello"],
        "cel": ["bezpieczeństwo", "życie", "zwycięstwo", "czas"]
    },
    "weights": {
        "sprawca": 0.25, "zdarzenie": 0.12, "miejsce": 0.15,
        "obiekt": 0.08, "narzedzie": 0.05, "cel": 0.05
    },
    "synergy": {
        ("sprawca", "zdarzenie"): 0.20, ("zdarzenie", "miejsce"): 0.05,
        ("sprawca", "miejsce"): 0.30, ("obiekt", "narzedzie"): 0.02,
        ("zdarzenie", "obiekt"): 0.02, ("zdarzenie", "narzedzie"): 0.02,
        ("sprawca", "cel"): 0.05, ("zdarzenie", "cel"): 0.02,
        ("sprawca", "obiekt"): 0.05, ("sprawca", "narzedzie"): 0.05,
        ("obiekt", "miejsce"): 0.03, ("narzedzie", "miejsce"): 0.03,
        ("miejsce", "cel"): 0.03, ("obiekt", "cel"): 0.02, ("narzedzie", "cel"): 0.02
    },
    "group_bonus": 0.00
}

# 2. FUNKCJE
def get_all_files():
    base_path = 'data'
    folders = {'imola_1994': 'Tematyczny', 'others': 'Inny'}
    all_files = []
    for folder_name, label in folders.items():
        folder_path = os.path.join(base_path, folder_name)
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith(".txt"):
                    all_files.append((folder_name, filename, label))
    return all_files

def analyze_text(content):
    score = 0.0
    found_roles = {}
    highlights = []

    for match in re.finditer(r'\b\w+\b', content):
        word = match.group(0)
        start, end = match.span()
        w_lower = word.lower()

        ids = clp(w_lower)
        if ids:
            base = clp.bform(ids[0]).lower()
        else:
            base = w_lower

        if "imol" in w_lower:
            base = "imola"
        elif "ayrt" in w_lower:
            base = "ayrton"
        elif "ratzenb" in w_lower:
            base = "ratzenberger"
        elif w_lower in ["senna", "senny"]:
            base = "senna"
        elif "brazylij" in w_lower:
            base = "brazylijczyk"
        elif "williams" in w_lower:
            base = "williams"

        for role, keywords in CONFIG["roles"].items():
            if base in [k.lower() for k in keywords]:
                highlights.append((start, end, role))
                found_roles.setdefault(role, set()).add(base)
                break

    for role in found_roles:
        score += CONFIG["weights"][role]

    active_roles = list(found_roles.keys())
    for i in range(len(active_roles)):
        for j in range(i + 1, len(active_roles)):
            r1, r2 = active_roles[i], active_roles[j]
            for (p1, p2), bonus in CONFIG["synergy"].items():
                if (r1 == p1 and r2 == p2) or (r1 == p2 and r2 == p1):
                    score += bonus

    highlighted = content
    for start, end, role in sorted(highlights, key=lambda x: x[0], reverse=True):
        highlighted = (
            highlighted[:start]
            + f'<mark class="hl-{role}">'
            + highlighted[start:end]
            + '</mark>'
            + highlighted[end:]
        )

    return {
        "score": min(round(score, 2), 1.0),
        "found_roles": {k: list(v) for k, v in found_roles.items()},
        "highlighted_text": highlighted
    }

# 3. TRASY
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/formularz')
def dictionary():
    return render_template('keyword_form.html', roles=CONFIG["roles"])

@app.route('/wagi')
def weights():
    return render_template('weight_table.html', weights=CONFIG["weights"], synergy=CONFIG["synergy"])

@app.route('/teksty')
def list_texts():
    files = get_all_files()
    results = []

    for folder, filename, label in files:
        filepath = os.path.join('data', folder, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                analysis = analyze_text(content)

                results.append({
                    "filename": filename,
                    "label": label,
                    "folder": folder,
                    "score": analysis["score"],
                    "highlighted": Markup(analysis["highlighted_text"]),
                    "found_roles": analysis["found_roles"]
                })
        except Exception as e:
            print("Błąd:", e)
            
    results.sort(key=lambda x: x["score"], reverse=True)

    return render_template('text_list.html', results=results)


@app.route('/frekwencja')
def frequency_list():
    all_files = get_all_files()
    
    stats = {'tematyczne': {}, 'pozostale': {}}
    stop_words = ["się", "ten", "taki", "który", "siebie", "on", "ona", "oraz", "jeśli", "tylko", "jaki", "swój", "mnie", "jego", "które", 'także', 'przez', 'przed']

    for folder, filename, label in all_files:
        filepath = os.path.join('data', folder, filename)
        
        target = 'tematyczne' if folder == 'imola_1994' else 'pozostale'
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
            words = re.findall(r'\b\w+\b', content.lower())
            for w in words:
                ids = clp(w)
                if ids:
                    base = clp.bform(ids[0]).lower()

                    if w.lower() == "senna":
                        base = "senna"
                    
                    if len(base) > 3 and base not in stop_words:
                        stats[target][base] = stats[target].get(base, 0) + 1

    top_t = sorted(stats['tematyczne'].items(), key=lambda x: x[1], reverse=True)[:30]
    top_p = sorted(stats['pozostale'].items(), key=lambda x: x[1], reverse=True)[:30]
    
    return render_template('freq.html', tematyczne=top_t, pozostale=top_p)

if __name__ == '__main__':
    app.run(port='12226', host='0.0.0.0', debug=True)