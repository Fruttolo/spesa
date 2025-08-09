# Gestore Spesa

Un'applicazione web Flask per gestire la lista della spesa e il menu settimanale.

## Caratteristiche

- Gestione degli ingredienti con quantità in frigorifero
- Gestione dei piatti con relativi ingredienti
- Pianificazione del menu settimanale
- Gestione degli spuntini settimanali
- Generazione automatica della lista della spesa

## Requisiti

- Python 3.x
- Flask
- Flask-SQLAlchemy

## Installazione

1. Clona il repository o scarica i file
2. Crea un ambiente virtuale:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # o
   .venv\Scripts\activate  # Windows
   ```
3. Installa le dipendenze:
   ```bash
   pip install flask flask-sqlalchemy
   ```

## Avvio

1. Assicurati di essere nell'ambiente virtuale
2. Esegui l'applicazione:
   ```bash
   python app.py
   ```
3. Apri un browser e vai a `http://localhost:5000`

## Utilizzo

1. **Gestione Ingredienti**
   - Aggiungi nuovi ingredienti
   - Indica se sono presenti in frigorifero e la quantità

2. **Gestione Piatti**
   - Crea nuovi piatti
   - Assegna ingredienti e quantità
   - Categorizza i piatti (colazione, pranzo, cena, spuntino)

3. **Menu Settimanale**
   - Imposta i pasti per ogni giorno della settimana
   - Gestisci gli spuntini settimanali

4. **Lista della Spesa**
   - Visualizza automaticamente gli ingredienti necessari
   - Le quantità tengono conto di ciò che è già presente in frigorifero
