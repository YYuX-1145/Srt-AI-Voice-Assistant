help = r"""
# Guide de l'utilisateur

## 0. Configuration et utilisation du service
#### Ce projet peut appeler deux projets locaux : Bert-VITS2, GPT-SoVITS
#### Et un service en ligne : Microsoft TTS
* **Pour les projets TTS locaux** :

    * Remplissez et enregistrez le chemin racine du projet et le chemin de l'interpréteur Python correspondant sur la page des paramètres.
    * **Méthode plus simple** : Placez le programme dans le répertoire racine du paquet intégré, puis cliquez sur le bouton correspondant sur la première page pour démarrer le service API !

* **Pour Microsoft TTS** :

    * Suivez le tutoriel pour vous inscrire à un compte et saisissez la clé API sur la page des paramètres.
    * Prenez note de la quota mensuelle gratuite !

## 1. Démarrage
### Ce projet peut doubler pour les sous-titres et les textes bruts.
* **Pour les sous-titres** :

    * Lorsqu'un sous-titre est trop long, les sous-titres suivants seront retardés en conséquence. Et vous pouvez définir l'intervalle de parole minimum dans les paramètres.

* **Pour le texte brut** :

    * Le texte sera divisé en entrées de sous-titres en fonction des ponctuations de fin et des retours à la ligne.

* Après la génération, vous pouvez exporter les sous-titres avec les horodatages audio réels sur la page d'édition.

### A. Scénario avec un seul locuteur
* **I.** Téléchargez les fichiers de sous-titres ou de texte dans le panneau de droite de la page `Doublage de sous-titres`.
* Mode de balisage : Le contenu du fichier doit être le suivant : `Locuteur : Contenu`, e.g. `Vincent:Bonjour.` Le tableau de correspondance peut convertir le locuteur d'origine dans le fichier de texte en locuteur cible correspondant.  

* **II.** Sélectionnez votre projet et ajustez les paramètres dans le panneau central.

* **III.** Cliquez sur le bouton `Produire l'audio` en bas et attendez.

* **IV.** Téléchargez votre audio.

### B. Scénario avec plusieurs locuteurs
* **I.** Téléchargez les fichiers de sous-titres/texte dans le panneau de droite de `Doublage de sous-titres`.

* **II.** Cliquez sur `Créer un projet de doublage avec plusieurs locuteurs` en dessous de l'affichage du fichier.

* **III.** Créez des locuteurs :
    * **a.** Détendez la section Doublure avec plusieurs locuteurs en bas de la page d'édition.
    * **b.** Sélectionnez le projet cible.
    * **c.** Dans la boîte de sélection/creation de locuteur, saisissez un nom de locuteur.
    * **d.** Ajustez les paramètres (y compris les numéros de port) et cliquez sur 💾 pour enregistrer. Les noms dupliqués écraseront les locuteurs existants.

* **IV.** Sélectionnez un locuteur dans la liste déroulante, cochez les sous-titres correspondants, puis cliquez sur ✅ pour appliquer. Les informations du locuteur apparaîtront dans la colonne 4.

* **V.** Le dernier locuteur attribué devient le locuteur par défaut (s'applique aux sous-titres non attribués dans les projets avec plusieurs locuteurs).

* **VI.** Cliquez sur `Lancer la synthèse à plusieurs locuteurs` pour commencer la génération.

### Regénérer des lignes spécifiques
* **I.** Localisez le sous-titre cible à l'aide du curseur sur la page d'édition.

* **II.** Modifiez le texte si nécessaire. Les modifications sont enregistrées automatiquement après la régénération.

* **III.** Cliquez sur 🔄 pour régénérer une seule ligne :

    * Utilise les paramètres du projet s'il n'est pas attribué.
    * Utilise les paramètres spécifiques du locuteur s'il est attribué.
    * Les projets avec plusieurs locuteurs doivent avoir des locuteurs attribués.

* **IV.** Après avoir apporté des modifications aux sous-titres, vous pouvez également cliquer sur `Continuer la Génération` pour régénérer la voix des sous-titres modifiés ou dont la synthèse n'a pas été réussie.

* **V.** Cliquez sur `Reconstituer l'audio` pour recomposer l'audio complet.

### C. Rééditer des projets historiques
* Sélectionnez un projet de l'historique de synthèse dans le panneau supérieur. Ensuite, cliquez sur le bouton `Charger`.
* Le reste est évident.

### D. Édition des sous-titres
#### 1. Copier
* Copier les sous-titres sélectionnés.

#### 2. Supprimer
* Supprimer les sous-titres sélectionnés.

#### 3. Fusionner
* Sélectionnez au moins 2 sous-titres comme points de départ/fin.
* Les sous-titres du point de départ au point de fin seront fusionnés.

⚠️ Les modifications ne sont pas enregistrées automatiquement sur le disque immédiatement, vous pouvez donc recharger le projet pour annuler.

#### 4. Modifier les horodatages
* Éditez les heures de début/fin au format SRT.
* Cliquez sur `Appliquer les horodatages` pour enregistrer les modifications.

⚠️ Les modifications non appliquées seront perdues lors de la navigation.

## 2. Dépannage
* Lorsque vous trouvez un problème :  
Décrivez le problème en détail et répertoriez les étapes effectuées pour reproduire l'erreur.
* Visitez [GitHub-issues](https://github.com/YYuX-1145/Srt-AI-Voice-Assistant/issues) pour rapporter un problème ou demander de l'aide (les modèles de Issue vous guideront pour signaler correctement). 
"""
