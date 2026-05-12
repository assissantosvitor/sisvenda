from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "sisvenda.db"
app = Flask(__name__)
app.secret_key = "troque_esta_chave"

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, nome TEXT, preco REAL, estoque INTEGER);
    CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY, nome TEXT, email TEXT);
    CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY, produto_id INTEGER, cliente_id INTEGER, quantidade INTEGER, total REAL, created_at TEXT);
    """)
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/produtos")
def produtos():
    db = get_db()
    produtos = db.execute("SELECT * FROM produtos").fetchall()
    return render_template("produtos.html", produtos=produtos)

@app.route("/clientes")
def clientes():
    db = get_db()
    clientes = db.execute("SELECT * FROM clientes").fetchall()
    return render_template("clientes.html", clientes=clientes)

@app.route("/vendas", methods=["GET","POST"])
def vendas():
    db = get_db()
    if request.method == "POST":
        produto_id = int(request.form["produto_id"])
        cliente_id = int(request.form["cliente_id"])
        quantidade = int(request.form["quantidade"])
        produto = db.execute("SELECT * FROM produtos WHERE id=?", (produto_id,)).fetchone()
        total = produto["preco"] * quantidade
        db.execute("INSERT INTO vendas (produto_id, cliente_id, quantidade, total, created_at) VALUES (?,?,?,?,datetime('now'))",
                   (produto_id, cliente_id, quantidade, total))
        db.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade, produto_id))
        db.commit()
        return redirect(url_for("vendas"))
    produtos = db.execute("SELECT * FROM produtos").fetchall()
    clientes = db.execute("SELECT * FROM clientes").fetchall()
    vendas = db.execute("SELECT v.*, p.nome as produto, c.nome as cliente FROM vendas v JOIN produtos p ON v.produto_id=p.id JOIN clientes c ON v.cliente_id=c.id ORDER BY v.id DESC").fetchall()
    return render_template("vendas.html", produtos=produtos, clientes=clientes, vendas=vendas)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        # exemplo simples: aceitar qualquer usuário (substituir por autenticação real)
        return redirect(url_for("index"))
    return render_template("login.html")

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
