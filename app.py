from flask import Flask, render_template
from markupsafe import Markup
import os
import re

app = Flask(__name__)

# 1. KONFIGURACJA RÓL I WAG
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
        "sprawca": 0.20,
        "zdarzenie": 0.30,
        "obiekt": 0.10,
        "narzedzie": 0.10,
        "miejsce": 0.15,
        "cel": 0.15
    },
    "synergy": {
        ("sprawca", "zdarzenie"): 0.15,
        ("zdarzenie", "miejsce"): 0.10,
        ("sprawca", "miejsce"): 0.05,
        ("obiekt", "narzedzie"): 0.05,
    },
    "group_bonus": 0.10
}

# 2. FUNKCJA ANALIZUJĄCA TEKST
def analyze_text(content):
    score = 0.0
    found_roles = {}
    highlighted = content 

    for role, keywords in CONFIG["roles"].items():
        # Sortujemy od najdłuższych słów
        sorted_keywords = sorted(keywords, key=len, reverse=True)
        found_in_this_role = []
        
        for word in sorted_keywords:
            # \b oznacza granicę słowa (spacje, znaki interpunkcyjne, początek linii)
            # re.IGNORECASE sprawia, że nie musimy robić .lower() na całym tekście
            pattern = r'\b' + re.escape(word) + r'\b'
            
            if re.search(pattern, content, re.IGNORECASE):
                # Jeśli słowo jeszcze nie zostało podświetlone (żeby nie podmieniać marków)
                if word.lower() not in [f.lower() for f in found_in_this_role]:
                    found_in_this_role.append(word)
                    
                    # Podmiana z zachowaniem granic słów
                    highlighted = re.sub(pattern, f'<mark class="hl-{role}">\\g<0></mark>', highlighted, flags=re.IGNORECASE)
        
        if found_in_this_role:
            found_roles[role] = found_in_this_role
            score += CONFIG["weights"][role]

    # Reszta logiki synergii pozostaje bez zmian
    active = list(found_roles.keys())
    from itertools import combinations
    for r1, r2 in combinations(active, 2):
        for (p1, p2), bonus in CONFIG["synergy"].items():
            if (r1 == p1 and r2 == p2) or (r1 == p2 and r2 == p1):
                score += bonus

    if len(active) >= 3:
        score += (len(active) - 2) * CONFIG.get("group_bonus", 0)

    return {
        "score": min(round(score, 2), 1.0),
        "found_roles": found_roles,
        "highlighted_text": highlighted
    }

# 3. TRASY (ROUTES)
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
    base_path = 'data'
    folders = {
        'imola_1994': 'Tematyczny',
        'others': 'Inny'
    }
    
    results = []

    for folder_name, label in folders.items():
        folder_path = os.path.join(base_path, folder_name)
        
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith(".txt"):
                    file_path = os.path.join(folder_path, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            analysis = analyze_text(content)
                            results.append({
                                "filename": filename,
                                "label": label,
                                "folder": folder_name,
                                "score": analysis["score"]
                            })
                    except Exception as e:
                        print(f"Błąd odczytu pliku {filename}: {e}")

    return render_template('text_list.html', results=results)

@app.route('/tekst/<folder>/<filename>')
def analyze_specific_text(folder, filename):
    filepath = os.path.join('data', folder, filename)
    
    if not os.path.exists(filepath):
        return "Plik nie istnieje", 404
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    analysis = analyze_text(content)
    
    return render_template('analyze.html', 
                           filename=filename,
                           highlighted_content=Markup(analysis["highlighted_text"]),
                           found_roles=analysis["found_roles"],
                           all_roles=CONFIG["roles"].keys(),
                           score=analysis["score"])

@app.route('/load_texts/<int:offset>')
def load_texts(offset):
    limit = 10
    base_path = 'data'
    folders = {'imola_1994': 'Tematyczny', 'others': 'Inny'}
    
    all_files = []
    for folder_name, label in folders.items():
        folder_path = os.path.join(base_path, folder_name)
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith(".txt"):
                    all_files.append((folder_name, filename, label))
    
    chunk = all_files[offset : offset + limit]
    
    results = []
    for folder, filename, label in chunk:
        filepath = os.path.join(base_path, folder, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        analysis = analyze_text(content)
        results.append({
            "filename": filename,
            "label": label,
            "score": analysis["score"],
            "highlighted": Markup(analysis["highlighted_text"]),
            "found_roles": analysis["found_roles"]
        })
    
    return render_template('single_text.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)