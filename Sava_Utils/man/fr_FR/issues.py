issues = r"""
# Problèmes typiques
## 1. Erreur GPT-SoVITS : 404 NOT FOUND
```
/tts 404 NOT FOUND
```
* Cause typique de cette erreur : Utilisation de code non officiel standard.
* Veuillez vous assurer que vous utilisez le package intégré officiel ou le code le plus récent du dépôt officiel.

### Solution :
* Téléchargez manuellement le code du dépôt officiel.
* Téléchargez le package intégré fourni dans le README. (stable mais les mises à jour peuvent être lentes)

## 2. Impossible d'établir de connexion car l'ordinateur cible a expressément refusé celle-ci.
```
Impossible d'établir de connexion car l'ordinateur cible a expressément refusé celle-ci.
```
Vous devez vérifier :
* Le service API est-il déjà démarré et en cours d'exécution ?
* Veuillez attendre que l'API soit entièrement démarrée avant d'effectuer des opérations.
* Ne fermez pas la console de l'API !
* Le port est-il correctement renseigné ?

## 3. 400 Bad Request
```
400 Bad Request
```
Vérifiez les journaux d'erreur en rouge dans la console de ce programme ; généralement, l'API renverra la cause de l'erreur.
Si aucun message d'erreur n'est reçu, veuillez signaler ce problème.
* Cause d'erreur typique : Audio de référence en dehors de la plage de 3 à 10 secondes ; le chemin du modèle n'existe pas.

## 4. Les sous-titres suivants sont retardés en raison de la longueur excessive de l'audio précédent.
```
Les sous-titres suivants sont retardés en raison de la longueur excessive de l'audio précédent.
```
* Vos intervalles de temps des sous-titres ne sont pas appropriés.
* Considérez d'augmenter la valeur de la configuration ` rapport maximal d'accélération audio`(en la fixant à
une valeur supérieure à 1 pour activer la fonction) et activez `Supprimer l'inhalation et le silence`.
* Il existe une option d'intervalle vocal minimum dans les paramètres (par défaut 0,3 seconde) pour éviter que les voix ne se chevauchent dans de tels cas. Si cela n'est pas nécessaire, il peut être égal 0.

## 5. Le fichier audio de sortie de GPT-SoVITS a une durée mais est silencieux.
```
Le fichier audio de sortie de GPT-SoVITS a une durée mais est silencieux.
```
* Votre carte graphique ne supporte pas le fp-16.
* Modifiez manuellement la valeur de `is_half` en `false` dans `GPT_SoVITS\configs\tts_infer.yaml`.
"""
