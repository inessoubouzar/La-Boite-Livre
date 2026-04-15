import sqlite3
import json
from werkzeug.security import generate_password_hash

JSONFILENAME = 'la_boite_a_livre.json'
DBFILENAME = 'la_boite_a_livre.sqlite'

def get_connection():#permet de ne respecter les cle etrangere. 
    """Utilitaire pour ouvrir une connexion avec support des clés étrangères."""
    conn = sqlite3.connect(DBFILENAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row # Permet d'accéder aux colonnes par nom
    return conn

def load(fname=JSONFILENAME, db_name=DBFILENAME):
    conn = get_connection()
    cursor = conn.cursor()

    # --- 1. NETTOYAGE ET CRÉATION DES TABLES ---
    
    cursor.execute('DROP TABLE IF EXISTS signalements')
    cursor.execute('DROP TABLE IF EXISTS utilisateurs')
    cursor.execute('DROP TABLE IF EXISTS boites')
    
    cursor.execute('''
        CREATE TABLE utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nom_utilisateur TEXT UNIQUE, 
            mot_de_passe TEXT
        )''')
    
    cursor.execute('''
        CREATE TABLE boites (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nom_lieu TEXT, 
            description TEXT
        )''')
    
    cursor.execute('''
        CREATE TABLE signalements (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            id_boite INTEGER,
            id_utilisateur INTEGER, 
            date_signalement TEXT, 
            remplissage TEXT,
            etat_livres TEXT, 
            FOREIGN KEY(id_boite) REFERENCES boites(id), 
            FOREIGN KEY(id_utilisateur) REFERENCES utilisateurs(id)
        )''')

    # --- 2. CHARGEMENT DES DONNÉES FIXES (BOITES) ---
    
    insert_boite = 'INSERT INTO boites (nom_lieu, description) VALUES (:nom_lieu, :description)'
    
    try:
        with open(fname, 'r', encoding='utf-8') as fh:
            boites_fixes = json.load(fh)
            for boite in boites_fixes:
                cursor.execute(insert_boite, boite)
        print("listes des boîtes importées avec succès.")
    except FileNotFoundError:
        print(f"Erreur : Le fichier {fname} est introuvable. Aucune boîte ajoutée.")

    # --- 3. CRÉATION DU PREMIER UTILISATEUR (ADMIN) ---
    # On le crée ici car il n'est pas dans le JSON
    insert_utilisateur = 'INSERT INTO utilisateurs (nom_utilisateur, mot_de_passe) VALUES (:nom_utilisateur, :mot_de_passe)'
    user_admin = {
        'nom_utilisateur': 'admin',
        'mot_de_passe': generate_password_hash('admin123')  # Mot de passe sécurisé
    }
    cursor.execute(insert_utilisateur, user_admin)

    conn.commit()
    conn.close()
    print(f"Base de données '{db_name}' prête !")
    
    
#fonction d'accès
    
def recuperer_toutes_les_boites():
    
    # on ouvre une connexion
    conn = get_connection()
    
    # on crée un curseur pour exécuter des requêtes
    cursor = conn.cursor()
    
    # Jointure pour avoir le dernier état connu de chaque boîte
    requete = '''
        SELECT b.*, s.remplissage, s.etat_livres 
        FROM boites b LEFT JOIN signalements s ON s.id = (
                                            SELECT id 
                                            FROM signalements 
                                            WHERE id_boite = b.id 
                                            ORDER BY date_signalement DESC LIMIT 1
        )
    '''
    
    # on exécute la requête et récupère les résultats
    cursor.execute(requete)
    
    #on retourne le resultat sous forme de liste 
    liste_boites = cursor.fetchall()
    
    #on ferme toujours la connexion après utilisation
    conn.close()
    
    return liste_boites

def recuperer_details_boite(id_boite):
    # On ouvre une connexion
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Infos de la boîte (Reste inchangé)
    cursor.execute("SELECT * FROM boites WHERE id = ?", (id_boite,))
    boite = cursor.fetchone()
    
    # 2. Historique avec JOINTURE
    # On sélectionne toutes les colonnes de signalements 
    # ET la colonne nom_utilisateur de la table utilisateurs
    
    cursor.execute('''
        SELECT s.*, u.nom_utilisateur 
        FROM signalements s JOIN utilisateurs u ON s.id_utilisateur = u.id 
        WHERE s.id_boite = ? 
        ORDER BY s.date_signalement DESC''', (id_boite,))
    
    historique = cursor.fetchall() # Récupère tous les signalements de la boîte avec le nom de l'utilisateur qui a fait le signalement
    
    conn.close()
    return boite, historique

def ajouter_signalement(id_boite, id_user, remplissage, etat):
     # on ouvre une connexion
    conn = get_connection()
    
    # on crée un curseur pour exécuter des requêtes
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO signalements (id_boite, id_utilisateur, remplissage, etat_livres, date_signalement)
        VALUES (?, ?, ?, ?, datetime('now'))''', (id_boite, id_user, remplissage, etat))
    conn.commit()
    conn.close()

def creer_utilisateur(nom, mdp):
     # on ouvre une connexion
    conn = get_connection()
    
    # on crée un curseur pour exécuter des requêtes
    cursor = conn.cursor()
    
    code_secret = generate_password_hash(mdp)
    try:
        cursor.execute("INSERT INTO utilisateurs (nom_utilisateur, mot_de_passe) VALUES (?, ?)", (nom, code_secret))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Nom d'utilisateur déjà pris
    finally:
        conn.close()
        
        
if __name__ == "__main__":
    load()
