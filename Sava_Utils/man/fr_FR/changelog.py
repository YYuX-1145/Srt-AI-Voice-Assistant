changelog = r"""
## Journal des modifications

### Mise à jour V4-0325 :
#### Afin de rendre les versions plus claires, des numéros de version sont attribués plus des dates de publication.
#### Après cette mise à jour, l'historique de synthèse et les locuteurs enregistrés de la version précédente doivent être recréés ; sinon, des erreurs peuvent se produire !
1. Édition des sous-titres
2. Traduction des sous-titres
3. Amélioration de divers détails et correction de erreurs
4. Supporter CosyVoice2 (réutilisation du panneau GSV)
5. (4.0.1) Mode par lots  
6. (4.1) Mode serveur  
7. (4.2) I18n  
8. (4.3) Accélération automatique de l'audio et suppression du silence; Création de projets de doublage à plusieurs locuteurs à partir de textes étiquetés.  
9. (4.3.1) Ajouter la fonction de Recherche et de Remplacement; ajouter un bouton de régénération en un clic.  
10. (4.4) Permet l'édition des caractères polyphoniques pour GPT-SoVITS ainsi que la détection automatique des modèles; Autorise les invites personnalisées pour Ollama; Permet d'exporter des sous-titres avec les noms des locuteurs selon un modèle personnalisable.  
11.(4.5) Le module de traduction permet de fusionner des sous-titres bilingues; le module de transcription audio-vidéo prend en charge le modèle de séparation vocale UVR et une fonction de fusion vidéo en un clic a été ajoutée.  

### Mise à jour du 140225 :
1. Prise en charge de la lecture de projets historiques
2. Prise en charge du doublage avec plusieurs locuteurs

### Mise à jour du 230125 :
1. Prise en charge de la réexportation de fichiers de sous-titres SRT correspondant aux horodatages de début et de fin réels après synthèse ; prise en charge également de la lecture de fichiers texte TXT pour la synthèse, auquel cas les paragraphes sont divisés par phrases.
2. Afin d'améliorer l'extensibilité à l'avenir et la simplicité, la conception d'un fichier de script unique, qui rendait les téléchargements plus pratiques, a dû être abandonnée. Le code sera refactorisé progressivement à partir de cette version.
3. Ajout de certaines documentations.

### Mise à jour du 110824 :
1. Notification des utilisateurs du message d'erreur
2. Détection automatique des environnements TTS-Project
3. Restauration de la compatibilité avec l'api-v1
4. Une mise à jour majeure de fonctionnalité : La régénération de lignes spécifiques si vous n'êtes pas satisfaites d'elles.
"""
