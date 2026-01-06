from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Witaj w mojej aplikacji Flask!</h1><p>To działa!</p>"

if __name__ == '__main__':
    app.run(debug=True)