from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from io import StringIO, BytesIO
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spesa.db'
db = SQLAlchemy(app)

# Models
class Ingrediente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    in_frigo = db.Column(db.Boolean, default=False)
    quantita_in_frigo = db.Column(db.Float, default=0)
    unita_misura = db.Column(db.String(20))
    piatti = db.relationship('PiattoIngrediente', backref='ingrediente')
    spuntini = db.relationship('Spuntini', backref='ingrediente')

class Piatto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20))  # colazione, pranzo, cena, spuntino
    ingredienti = db.relationship('PiattoIngrediente', backref='piatto')

class PiattoIngrediente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    piatto_id = db.Column(db.Integer, db.ForeignKey('piatto.id'), nullable=False)
    ingrediente_id = db.Column(db.Integer, db.ForeignKey('ingrediente.id'), nullable=False)
    quantita = db.Column(db.Float, nullable=False)
    unita_misura = db.Column(db.String(20))

class MenuSettimanale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    giorno = db.Column(db.String(20), nullable=False)
    colazione_id = db.Column(db.Integer, db.ForeignKey('piatto.id'))
    pranzo_id = db.Column(db.Integer, db.ForeignKey('piatto.id'))
    cena_id = db.Column(db.Integer, db.ForeignKey('piatto.id'))
    colazione = db.relationship('Piatto', foreign_keys=[colazione_id])
    pranzo = db.relationship('Piatto', foreign_keys=[pranzo_id])
    cena = db.relationship('Piatto', foreign_keys=[cena_id])

class Spuntini(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ingrediente_id = db.Column(db.Integer, db.ForeignKey('ingrediente.id'), nullable=False)
    quantita = db.Column(db.Float, nullable=False)
    unita_misura = db.Column(db.String(20))

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/ingredienti', methods=['GET', 'POST'])
def ingredienti():
    if request.method == 'POST':
        nome = request.form.get('nome')
        in_frigo = bool(request.form.get('in_frigo'))
        quantita = float(request.form.get('quantita', 0))
        unita_misura = request.form.get('unita_misura')
        
        ingrediente = Ingrediente(nome=nome, in_frigo=in_frigo, 
                                quantita_in_frigo=quantita, 
                                unita_misura=unita_misura)
        db.session.add(ingrediente)
        db.session.commit()
        return redirect(url_for('ingredienti'))
    
    # Gestione filtri
    filtro_frigo = request.args.get('in_frigo')
    filtro_nome = request.args.get('nome', '').lower()
    
    query = Ingrediente.query.order_by(Ingrediente.nome)
    
    if filtro_frigo in ['true', 'false']:
        query = query.filter(Ingrediente.in_frigo == (filtro_frigo == 'true'))
    if filtro_nome:
        query = query.filter(Ingrediente.nome.ilike(f'%{filtro_nome}%'))
    
    ingredienti = query.all()
    # Per ogni ingrediente, verifica se è utilizzato
    ingredienti_info = []
    for ing in ingredienti:
        is_used = len(ing.piatti) > 0 or len(ing.spuntini) > 0
        ingredienti_info.append({
            'ingrediente': ing,
            'is_used': is_used
        })
    return render_template('ingredienti.html', 
                         ingredienti=ingredienti_info,
                         filtro_frigo=filtro_frigo,
                         filtro_nome=filtro_nome)

@app.route('/ingrediente/modifica/<int:id>', methods=['POST'])
def modifica_ingrediente(id):
    ingrediente = Ingrediente.query.get_or_404(id)
    ingrediente.nome = request.form.get('nome')
    ingrediente.in_frigo = bool(request.form.get('in_frigo'))
    ingrediente.quantita_in_frigo = float(request.form.get('quantita', 0))
    ingrediente.unita_misura = request.form.get('unita_misura')
    db.session.commit()
    return redirect(url_for('ingredienti'))

@app.route('/ingrediente/elimina/<int:id>', methods=['POST'])
def elimina_ingrediente(id):
    ingrediente = Ingrediente.query.get_or_404(id)
    if len(ingrediente.piatti) > 0 or len(ingrediente.spuntini) > 0:
        return "Non puoi eliminare questo ingrediente perché è utilizzato in piatti o spuntini", 400
    db.session.delete(ingrediente)
    db.session.commit()
    return redirect(url_for('ingredienti'))

@app.route('/piatti', methods=['GET', 'POST'])
def piatti():
    if request.method == 'POST':
        nome = request.form.get('nome')
        tipo = request.form.get('tipo')
        
        piatto = Piatto(nome=nome, tipo=tipo)
        db.session.add(piatto)
        db.session.commit()
        return redirect(url_for('piatti'))
    
    # Gestione filtri
    filtro_tipo = request.args.get('tipo')
    filtro_nome = request.args.get('nome', '').lower()
    
    query = Piatto.query.order_by(Piatto.nome)
    
    if filtro_tipo:
        query = query.filter(Piatto.tipo == filtro_tipo)
    if filtro_nome:
        query = query.filter(Piatto.nome.ilike(f'%{filtro_nome}%'))
    
    piatti = query.all()
    # Verifica quali piatti sono utilizzati nel menu
    piatti_info = []
    for piatto in piatti:
        is_used = MenuSettimanale.query.filter(
            (MenuSettimanale.colazione_id == piatto.id) |
            (MenuSettimanale.pranzo_id == piatto.id) |
            (MenuSettimanale.cena_id == piatto.id)
        ).first() is not None
        piatti_info.append({
            'piatto': piatto,
            'is_used': is_used
        })
    
    tipi_piatto = ['colazione', 'pranzo', 'cena', 'spuntino']
    return render_template('piatti.html', 
                         piatti=piatti_info,
                         tipi_piatto=tipi_piatto,
                         filtro_tipo=filtro_tipo,
                         filtro_nome=filtro_nome)

@app.route('/piatto/modifica/<int:id>', methods=['POST'])
def modifica_piatto(id):
    piatto = Piatto.query.get_or_404(id)
    piatto.nome = request.form.get('nome')
    piatto.tipo = request.form.get('tipo')
    db.session.commit()
    return redirect(url_for('piatti'))

@app.route('/piatto/elimina/<int:id>', methods=['POST'])
def elimina_piatto(id):
    piatto = Piatto.query.get_or_404(id)
    # Verifica se il piatto è usato nel menu
    is_used = MenuSettimanale.query.filter(
        (MenuSettimanale.colazione_id == piatto.id) |
        (MenuSettimanale.pranzo_id == piatto.id) |
        (MenuSettimanale.cena_id == piatto.id)
    ).first() is not None
    
    if is_used:
        return "Non puoi eliminare questo piatto perché è utilizzato nel menu", 400
    
    # Elimina prima tutti gli ingredienti associati al piatto
    PiattoIngrediente.query.filter_by(piatto_id=id).delete()
    db.session.delete(piatto)
    db.session.commit()
    return redirect(url_for('piatti'))

@app.route('/piatto/<int:id>/ingredienti', methods=['GET', 'POST'])
def piatto_ingredienti(id):
    piatto = Piatto.query.get_or_404(id)
    if request.method == 'POST':
        ingrediente_id = request.form.get('ingrediente_id')
        quantita = float(request.form.get('quantita'))
        unita_misura = request.form.get('unita_misura')
        
        piatto_ing = PiattoIngrediente(piatto_id=id, 
                                     ingrediente_id=ingrediente_id,
                                     quantita=quantita,
                                     unita_misura=unita_misura)
        db.session.add(piatto_ing)
        db.session.commit()
        return redirect(url_for('piatto_ingredienti', id=id))
    
    ingredienti_piatto = PiattoIngrediente.query.filter_by(piatto_id=id).join(Ingrediente).order_by(Ingrediente.nome).all()
    ingredienti_disponibili = Ingrediente.query.order_by(Ingrediente.nome).all()
    return render_template('piatto_ingredienti.html', 
                         piatto=piatto,
                         ingredienti_piatto=ingredienti_piatto,
                         ingredienti_disponibili=ingredienti_disponibili)

@app.route('/piatto/<int:piatto_id>/ingrediente/<int:ingrediente_id>/elimina', methods=['POST'])
def elimina_ingrediente_da_piatto(piatto_id, ingrediente_id):
    PiattoIngrediente.query.filter_by(piatto_id=piatto_id, ingrediente_id=ingrediente_id).delete()
    db.session.commit()
    return redirect(url_for('piatto_ingredienti', id=piatto_id))

@app.route('/menu/download')
def download_menu():
    giorni = ['Lunedi', 'Martedi', 'Mercoledi', 'Giovedi', 'Venerdi', 'Sabato', 'Domenica']
    menu_settimanale = {giorno: MenuSettimanale.query.filter_by(giorno=giorno).first() 
                       for giorno in giorni}
    
    output = StringIO()
    output.write("MENU SETTIMANALE\n")
    output.write("===============\n\n")
    
    for giorno in giorni:
        menu_giorno = menu_settimanale[giorno]
        output.write(f"{giorno.upper()}\n")
        output.write("-" * len(giorno) + "\n")
        if menu_giorno:
            if menu_giorno.colazione:
                output.write(f"Colazione: {menu_giorno.colazione.nome}\n")
            if menu_giorno.pranzo:
                output.write(f"Pranzo: {menu_giorno.pranzo.nome}\n")
            if menu_giorno.cena:
                output.write(f"Cena: {menu_giorno.cena.nome}\n")
        output.write("\n")
    
    output.write("SPUNTINI SETTIMANALI\n")
    output.write("===================\n\n")
    
    spuntini = Spuntini.query.join(Ingrediente).order_by(Ingrediente.nome).all()
    for spuntino in spuntini:
        output.write(f"- {spuntino.ingrediente.nome}: {spuntino.quantita} {spuntino.unita_misura}\n")
    
    # Convert the text to bytes and use BytesIO
    output_bytes = BytesIO()
    output_bytes.write(output.getvalue().encode('utf-8'))
    output_bytes.seek(0)
    return send_file(
        output_bytes,
        mimetype='text/plain',
        as_attachment=True,
        download_name='menu_settimanale.txt'
    )

@app.route('/menu', methods=['GET', 'POST'])
def menu():
    if request.method == 'POST':
        giorno = request.form.get('giorno')
        colazione_id = request.form.get('colazione_id')
        pranzo_id = request.form.get('pranzo_id')
        cena_id = request.form.get('cena_id')
        
        menu = MenuSettimanale.query.filter_by(giorno=giorno).first()
        if menu:
            menu.colazione_id = colazione_id
            menu.pranzo_id = pranzo_id
            menu.cena_id = cena_id
        else:
            menu = MenuSettimanale(giorno=giorno,
                                 colazione_id=colazione_id,
                                 pranzo_id=pranzo_id,
                                 cena_id=cena_id)
            db.session.add(menu)
        db.session.commit()
        return redirect(url_for('menu'))
    
    giorni = ['Lunedi', 'Martedi', 'Mercoledi', 'Giovedi', 'Venerdi', 'Sabato', 'Domenica']
    menu_settimanale = {giorno: MenuSettimanale.query.filter_by(giorno=giorno).first() 
                       for giorno in giorni}
    piatti = Piatto.query.all()
    return render_template('menu.html', 
                         giorni=giorni,
                         menu_settimanale=menu_settimanale,
                         piatti=piatti)

@app.route('/menu/svuota', methods=['POST'])
def svuota_menu():
    # Elimina tutti i record del menu settimanale
    MenuSettimanale.query.delete()
    # Elimina tutti gli spuntini
    Spuntini.query.delete()
    db.session.commit()
    return redirect(url_for('menu'))

@app.route('/spuntini', methods=['GET', 'POST'])
def spuntini():
    if request.method == 'POST':
        ingrediente_id = request.form.get('ingrediente_id')
        quantita = float(request.form.get('quantita'))
        unita_misura = request.form.get('unita_misura')
        
        spuntino = Spuntini(ingrediente_id=ingrediente_id,
                           quantita=quantita,
                           unita_misura=unita_misura)
        db.session.add(spuntino)
        db.session.commit()
        return redirect(url_for('spuntini'))
    
    spuntini = Spuntini.query.join(Ingrediente).order_by(Ingrediente.nome).all()
    ingredienti = Ingrediente.query.order_by(Ingrediente.nome).all()
    return render_template('spuntini.html', 
                         spuntini=spuntini,
                         ingredienti=ingredienti)

@app.route('/spuntini/<int:id>/elimina', methods=['POST'])
def elimina_spuntino(id):
    spuntino = Spuntini.query.get_or_404(id)
    db.session.delete(spuntino)
    db.session.commit()
    return redirect(url_for('spuntini'))

@app.route('/lista_spesa')
def lista_spesa():
    lista_spesa_items = genera_lista_spesa()
    return render_template('lista_spesa.html', lista_spesa=lista_spesa_items)

@app.route('/lista_spesa/download')
def download_lista_spesa():
    lista_spesa_items = genera_lista_spesa()
    
    output = StringIO()
    output.write("LISTA DELLA SPESA\n")
    output.write("================\n\n")
    
    for item in lista_spesa_items:
        output.write(f"- {item['nome']}: {item['quantita']} {item['unita_misura']}\n")
    
    # Convert the text to bytes and use BytesIO
    output_bytes = BytesIO()
    output_bytes.write(output.getvalue().encode('utf-8'))
    output_bytes.seek(0)
    return send_file(
        output_bytes,
        mimetype='text/plain',
        as_attachment=True,
        download_name='lista_spesa.txt'
    )

def genera_lista_spesa():
    # Raccoglie tutti gli ingredienti necessari dal menu settimanale
    ingredienti_necessari = {}
    menu_items = MenuSettimanale.query.all()
    
    for menu_item in menu_items:
        for pasto_id in [menu_item.colazione_id, menu_item.pranzo_id, menu_item.cena_id]:
            if pasto_id:
                ingredienti_piatto = PiattoIngrediente.query.filter_by(piatto_id=pasto_id).all()
                for ing in ingredienti_piatto:
                    if ing.ingrediente_id not in ingredienti_necessari:
                        ingredienti_necessari[ing.ingrediente_id] = {
                            'quantita': ing.quantita,
                            'unita_misura': ing.unita_misura
                        }
                    else:
                        ingredienti_necessari[ing.ingrediente_id]['quantita'] += ing.quantita
    
    # Aggiunge gli ingredienti degli spuntini
    spuntini = Spuntini.query.all()
    for spuntino in spuntini:
        if spuntino.ingrediente_id not in ingredienti_necessari:
            ingredienti_necessari[spuntino.ingrediente_id] = {
                'quantita': spuntino.quantita,
                'unita_misura': spuntino.unita_misura
            }
        else:
            ingredienti_necessari[spuntino.ingrediente_id]['quantita'] += spuntino.quantita
    
    # Sottrae gli ingredienti già presenti in frigo
    lista_spesa = []
    for ing_id, necessario in ingredienti_necessari.items():
        ingrediente = Ingrediente.query.get(ing_id)
        quantita_da_comprare = necessario['quantita']
        if ingrediente.in_frigo:
            quantita_da_comprare -= ingrediente.quantita_in_frigo
        
        if quantita_da_comprare > 0:
            lista_spesa.append({
                'nome': ingrediente.nome,
                'quantita': quantita_da_comprare,
                'unita_misura': necessario['unita_misura']
            })
    
    return lista_spesa

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=28000)
