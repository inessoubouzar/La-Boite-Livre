from flask import Flask,session, render_template, request, redirect, url_for,flash
from werkzeug.security import generate_password_hash, check_password_hash
from base_donnee import recuperer_toutes_les_boites, recuperer_details_boite, ajouter_signalement,creer_utilisateur,get_connection

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete'  

@app.route('/')
def acceuil(): 
    boites = recuperer_toutes_les_boites()
    return render_template('acceuil.html', boites=boites)

@app.route('/boite/<id>')
def fiche(id):
    boite, historique = recuperer_details_boite(id)
    return render_template('fiche.html', boite=boite, historique=historique)

@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        nom_utilisateur = request.form['nom_utilisateur'] #récupère le nom d'utilisateur du formulaire
        mot_de_passe = request.form['mot_de_passe'] #récupère le mot de passe du formulaire
        
        conn = get_connection()#ouvre une connexion à la base de données
        user = conn.execute('SELECT * FROM utilisateurs WHERE nom_utilisateur = ?', (nom_utilisateur,)).fetchone()#exécute une requête pour trouver l'utilisateur avec le nom d'utilisateur donné
        conn.close()#ferme la connexion à la base de données

        #check_password_hash compare le mot de passe saisi avec le mot de passe haché stocké dans la base de données
        if user and check_password_hash(user['mot_de_passe'], mot_de_passe):
            session.clear() 
            session['id'] = user['id']
            session['nom_utilisateur'] = user['nom_utilisateur']
            
            # C'est ici qu'on prépare le message de bienvenue
            flash(f"Bienvenue, {user['nom_utilisateur']} ! Contant de vous revoir.", "success")
            
            return redirect(url_for('acceuil')) # Redirection vers la liste des boites
        else:
            # Si on arrive ici, c'est que l'identifiant ou le MDP est faux
            flash("Nom d'utilisateur ou mot de passe incorrect", "danger") #danger correspond à une etiquette pour connaitre la categorie de flash
        
    # Si c'est un GET ou si la connexion a échoué, on affiche le formulaire de connexion        
    return render_template('connexion.html')



@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    # Si c'est un POST, on traite le formulaire d'inscription
    if request.method == 'POST':
        nom_utilisateur = request.form['nom_utilisateur'] #recupere les données saisies
        mot_de_passe = request.form['mot_de_passe_k']
        
        creer_utilisateur(nom_utilisateur, mot_de_passe)
        
        return redirect('/connexion')
    
    # Si c'est un GET, on affiche le formulaire d'inscription
    return render_template('cree_compte.html')


@app.route('/boite/<id>/signalement', methods=['GET', 'POST']) 
def signalement(id):
    # 1. Vérification de la session
    if not session.get('id'):
        flash("Désolé, vous devez être connecté pour signaler l'état d'une boîte.", "warning")
        return redirect(url_for('connexion'))
    
    if request.method == 'POST':
        # 2. Récupération des données du formulaire (noms correspondants aux balises <select>)
        remplissage = request.form.get('remplissage')
        etat_livres = request.form.get('etat_livres')
        id_utilisateur = session.get('id')

        # 3. Appel de la fonction de base de données
        ajouter_signalement(id, id_utilisateur, remplissage, etat_livres)
        
        flash("Merci ! Votre signalement a bien été pris en compte.", "success")
        
        # 4. Redirection vers la fiche de la boîte qu'on vient de signaler
        return redirect(url_for('fiche', id=id))
    
    # 5. Si c'est un GET, on affiche le formulaire
    # On récupère les détails pour pouvoir afficher le nom de la boîte dans le template
    boite, historique  = recuperer_details_boite(id) 
    return render_template('signalement.html', boite=boite)

@app.route('/deconnexion')
def deconnexion():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True) # Le debug=True affichera l'erreur précise sur ton navigateur.
