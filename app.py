from flask import Flask, render_template
from markupsafe import Markup
import os

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
        "sprawca": 0.2,
        "zdarzenie": 0.3,
        "obiekt": 0.1,
        "narzedzie": 0.1,
        "miejsce": 0.15,
        "cel": 0.15
    },
    "synergy": {
        ("sprawca", "zdarzenie"): 0.1,
        ("zdarzenie", "miejsce"): 0.05
    }
}

# 2. FUNKCJA ANALIZUJĄCA TEKST
def analyze_text(content):
    score = 0.0
    found_roles = {}
    highlighted = content

    for role, keywords in CONFIG["roles"].items():
        found_in_role = [word for word in keywords if word.lower() in content.lower()]
        if found_in_role:
            found_roles[role] = found_in_role
            score += CONFIG["weights"][role]
            # Podświetlanie w tekście
            for word in found_in_role:
                highlighted = highlighted.replace(word, f'<mark class="hl-{role}">{word}</mark>')

    # Dodanie synergii
    active_roles = found_roles.keys()
    for (r1, r2), bonus in CONFIG["synergy"].items():
        if r1 in active_roles and r2 in active_roles:
            score += bonus

    return {
        "highlighted_text": highlighted,
        "score": round(min(score, 1.0), 2),
        "found_roles": found_roles
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
    # Upewnij się, że te ścieżki odpowiadają Twoim folderom na dysku
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
                                "folder": folder_name, # potrzebne do linku
                                "score": analysis["score"]
                            })
                    except Exception as e:
                        print(f"Błąd odczytu pliku {filename}: {e}")

    return render_template('text_list.html', results=results)

@app.route('/tekst/<folder>/<filename>')
def analyze_specific_text(folder, filename):
    # folder to 'imola_1994' lub 'others' przekazane z URL
    filepath = os.path.join('data', folder, filename)
    
    if not os.path.exists(filepath):
        return "Plik nie istnieje", 404
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    analysis = analyze_text(content)
    
    return render_template('analiza.html', 
                           filename=filename,
                           highlighted_content=Markup(analysis["highlighted_text"]),
                           found_roles=analysis["found_roles"],
                           all_roles=CONFIG["roles"].keys(),
                           score=analysis["score"])

if __name__ == '__main__':
    app.run(debug=True)