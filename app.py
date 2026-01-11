from flask import Flask, render_template
from markupsafe import Markup
import os
import re

# from clp3 import clp 

app = Flask(__name__)

# 1. KONFIGURACJA
CONFIG = {
    "roles": {
        "sprawca": ["senna", "kierowca", "ayrton", "brazylijczyk", "ratzenberger", "roland"],
        "zdarzenie": ["wypadek", "wyścig", "śmierć", "grand prix", "okrążenie"],
        "obiekt": ["samochód", "bolid", "williamsa", "zespół"],
        "narzedzie": ["formuła", "prędkość", "km/h"],
        "miejsce": ["tor", "imola", "san marino", "zakręt", "tamburello", "szpital"],
        "cel": ["bezpieczeństwo", "życie", "zwycięstwo", "czas"]
    },
    "weights": {
        "sprawca": 0.20, "zdarzenie": 0.20, "miejsce": 0.15,
        "obiekt": 0.10, "narzedzie": 0.10, "cel": 0.10
    },
    "synergy": {
        ("sprawca", "zdarzenie"): 0.15, ("zdarzenie", "miejsce"): 0.10,
        ("sprawca", "miejsce"): 0.05, ("obiekt", "narzedzie"): 0.05,
        ("zdarzenie", "obiekt"): 0.05, ("zdarzenie", "narzedzie"): 0.05,
        ("sprawca", "cel"): 0.05, ("zdarzenie", "cel"): 0.05,
        ("sprawca", "obiekt"): 0.03, ("sprawca", "narzedzie"): 0.03,
        ("obiekt", "miejsce"): 0.03, ("narzedzie", "miejsce"): 0.03,
        ("miejsce", "cel"): 0.03, ("obiekt", "cel"): 0.02, ("narzedzie", "cel"): 0.02
    },
    "group_bonus": 0.05
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
    highlighted = content 

    for role, keywords in CONFIG["roles"].items():
        sorted_keywords = sorted(keywords, key=len, reverse=True)
        found_in_this_role = []
        
        for word in sorted_keywords:
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, content, re.IGNORECASE):
                if word.lower() not in [f.lower() for f in found_in_this_role]:
                    found_in_this_role.append(word)
                    highlighted = re.sub(pattern, f'<mark class="hl-{role}">\\g<0></mark>', highlighted, flags=re.IGNORECASE)
        
        if found_in_this_role:
            found_roles[role] = found_in_this_role
            score += CONFIG["weights"][role]

    active_roles = list(found_roles.keys())
    num_roles = len(active_roles)
    for i in range(num_roles):
        for j in range(i + 1, num_roles):
            r1, r2 = active_roles[i], active_roles[j]
            for (p1, p2), bonus in CONFIG["synergy"].items():
                if (r1 == p1 and r2 == p2) or (r1 == p2 and r2 == p1):
                    score += bonus

    if num_roles >= 3:
        score += (num_roles - 2) * CONFIG.get("group_bonus", 0)

    return {
        "score": min(round(score, 2), 1.0),
        "found_roles": found_roles,
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
                analysis = analyze_text(f.read())
                results.append({
                    "filename": filename, "label": label,
                    "folder": folder, "score": analysis["score"]
                })
        except: continue
    return render_template('text_list.html', results=results)

@app.route('/load_texts/<int:offset>')
def load_texts(offset):
    all_files = get_all_files()
    chunk = all_files[offset : offset + 10]
    results = []
    for folder, filename, label in chunk:
        filepath = os.path.join('data', folder, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            analysis = analyze_text(f.read())
            results.append({
                "filename": filename, "label": label, "score": analysis["score"],
                "highlighted": Markup(analysis["highlighted_text"]),
                "found_roles": analysis["found_roles"]
            })
    return render_template('single_text.html', results=results)

@app.route('/frekwencja')
def frequency_list():
    all_files = get_all_files()
    stats = {'tematyczne': {}, 'pozostale': {}}
    stop_words = ["oraz", "jest", "było", "tylko", "przez", "jego", "który", "były", "można", "roku", "dla", "się", "nie", "pod", "nad"]

    for folder, filename, label in all_files:
        filepath = os.path.join('data', folder, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            analysis = analyze_text(content)
            target = 'tematyczne' if analysis['score'] >= 0.5 else 'pozostale'
            
            words = re.findall(r'\b\w{4,}\b', content.lower())
            for w in words:
                if w not in stop_words:
                    stats[target][w] = stats[target].get(w, 0) + 1

    top_t = sorted(stats['tematyczne'].items(), key=lambda x: x[1], reverse=True)[:30]
    top_p = sorted(stats['pozostale'].items(), key=lambda x: x[1], reverse=True)[:30]
    
    return render_template('freq.html', tematyczne=top_t, pozostale=top_p)

if __name__ == '__main__':
    app.run(debug=True)