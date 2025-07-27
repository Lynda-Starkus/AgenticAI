## Instructions d'installation pour Windows

Utilisez une plateforme appelée **Anaconda** pour configurer votre environnement. Anaconda garantit que vous utilisez la bonne version de Python et que tous vos packages sont compatibles avec le cours, même si nos systèmes sont complètement différents. Cela prend plus de temps à configurer et utilise plus d'espace disque (5+ Go), mais c'est très fiable une fois installé.

Cela dit : si vous avez des problèmes avec Anaconda, j'ai prévu une approche alternative. Elle est plus rapide et plus simple, mais offre moins de garanties en termes de compatibilité.

### Partie 1 : Installer l'environnement Anaconda

Si cette Partie 1 vous pose des problèmes, vous pouvez utiliser l'alternative en Partie 1B ci-dessous.

1. **Installer Anaconda :**

* Téléchargez Anaconda depuis [https://docs.anaconda.com/anaconda/install/windows/](https://docs.anaconda.com/anaconda/install/windows/)
* Lancez l'installateur et suivez les instructions. Notez que cela prend plusieurs Go et un certain temps, mais c'est une plateforme puissante à utiliser par la suite.

2. **Configurer l'environnement :**

* Ouvrez **Anaconda Prompt** (recherchez-le dans le menu Démarrer)
* Naviguez vers le "répertoire racine du projet" en entrant par exemple : `cd C:\Users\VotreNom\Documents\Projects\pstb_agenticai` en remplaçant par le chemin réel de votre projet pstb_agenticai. Faites un `dir` et vérifiez que vous voyez les sous-dossiers pour chaque semaine du cours.
* Créez l'environnement : `conda env create -f environment.yml`
* Attendez quelques minutes pour que tous les packages soient installés - cela peut prendre 20-30 minutes si c'est votre première utilisation d'Anaconda, voire plus selon votre connexion internet. Si cela dure plus d'1h15 ou rencontre des problèmes, passez à la Partie 1B.
* Vous avez maintenant un environnement dédié et isolé pour l'ingénierie des LLMs, l'utilisation de vector stores, et bien plus ! Activez-le avec cette commande : `conda activate pstb_agenticai`

Vous devriez voir `(pstb_agenticai)` dans votre invite de commande, signe que votre environnement est activé.
(Après quand on aura besoin de pytorch, on l'installera à part.)
3. **Lancer Jupyter Lab :**

* Dans l'Anaconda Prompt, depuis le dossier `pstb_agenticai`, tapez : `jupyter lab`

...et Jupyter Lab devrait s'ouvrir dans un navigateur. Si vous ne connaissez pas encore Jupyter Lab, je vous l'expliquerai bientôt ! Fermez l'onglet du navigateur et l'Anaconda Prompt, puis passez à la Partie 3.

### Partie 1B - Alternative si Anaconda pose problème

1. **Ouvrir l'invite de commande**

Appuyez sur Win + R, tapez `cmd`, et appuyez sur Entrée

Exécutez `python --version` pour vérifier votre version de Python. Idéalement, utilisez une version 3.11 pour rester synchronisé.
Sinon, ce n'est pas grave, mais on pourrait y revenir plus tard si des problèmes de compatibilité apparaissent.
Téléchargez Python ici :
[https://www.python.org/downloads/](https://www.python.org/downloads/)

2. Naviguez vers le "répertoire racine du projet" :
   `cd C:\Users\VotreNom\Documents\Projects\pstb_agenticai`
   Faites un `dir` pour vérifier que les sous-dossiers du cours apparaissent.

Puis, créez un nouvel environnement virtuel avec :
`python -m venv pstb_agenticai`

3. Activez l'environnement virtuel avec :
   `pstb_agenticai\Scripts\activate`
   Vous devriez voir (llms) dans l'invite de commande, signe que tout fonctionne.

4. Exécutez : `pip install -r requirements.txt`
   L'installation peut prendre quelques minutes.

5. **Lancer Jupyter Lab :**

Depuis le dossier `pstb_agenticai`, tapez : `jupyter lab`
...et Jupyter Lab devrait s'ouvrir. Ouvrez le dossier `workshop` et double-cliquez sur `agent1.ipynb`. Succès ! Fermez Jupyter Lab et passez à la Partie 3.

Si vous avez un souci, contactez-moi !

### Partie 2 – Clé API Gemini (OPTIONNEL mais recommandé)

Vous allez écrire du code pour appeler les modèles Gemini de Google via le SDK Google Gen AI.

1. **Créer un compte Google AI Studio**
   Connectez-vous avec votre compte Google sur : [https://studio.ai.google.com/](https://studio.ai.google.com/)

2. **Accédez à la page des clés API**
   Dans AI Studio, cliquez sur **Get API key** (ou allez dans l'onglet "Gemini API" et sélectionnez "Get API key") pour générer une clé pour votre projet.

3. **Acceptez les conditions**
   Approuvez les conditions d'utilisation des API Google et les conditions supplémentaires Gemini, puis cliquez sur **Create API key**.

4. **Copiez et sauvegardez votre clé**
   Copiez la clé générée et sauvegardez-la en lieu sûr : vous ne pourrez plus la revoir ensuite.

5. **Définir votre variable d'environnement**
   Pour la sécurité de votre clé, exportez-la en variable d'environnement :

```bash
export GEMINI_API_KEY="<VOTRE_CLE_API_ICI>"
```

### PARTIE 3 - Fichier .env

Quand vous avez vos clés, créez un fichier appelé `.env` dans le dossier racine de votre projet. Le nom doit être exactement `.env` (et non `mes-cles.env` ou `.env.txt`). Voici comment faire :

1. Ouvrez le Bloc-notes (Windows + R, tapez `notepad`)

2. Tapez ce qui suit, en remplaçant xxxx par vos clés API :

```
GEMINI_API_KEY=xxxx
HF_TOKEN=xxxx
```

Assurez-vous qu'il n'y a pas d'espace autour des `=` et pas d'espaces en fin de ligne.

3. Fichier > Enregistrer sous. Choisissez "Tous les fichiers" comme type. Entrez **.env** comme nom, et sauvegardez-le dans la racine du dossier.

4. Vérifiez dans l'explorateur que le fichier est bien nommé `.env` (et pas `.env.txt`) - renommez-le si nécessaire. Activez l'option "Afficher les extensions de fichiers" pour voir les vrais noms. Contactez-moi si ce n'est pas clair !

Ce fichier n'apparaîtra pas dans Jupyter Lab car les fichiers commençant par un point sont cachés. Il est listé dans le fichier `.gitignore`, donc il ne sera pas versionné et vos clés resteront sûres.

### Partie 4 - C'est parti !!

* Ouvrez **Anaconda Prompt** si vous avez utilisé Anaconda, sinon ouvrez PowerShell si vous avez suivi la Partie 1B

* Naviguez jusqu'au dossier `pstb_agenticai` avec une commande comme : `cd C:\Users\VotreNom\Documents\Projects\pstb_agenticai`

* Activez votre environnement avec `conda activate pstb_agenticai` (ou `pstb_agenticai\Scripts\activate` pour la Partie 1B)

* Vous devriez voir `(pstb_agenticai)` dans votre invite de commande, signe que tout va bien. Tapez ensuite : `jupyter lab` et Jupyter Lab s'ouvrira. Ouvrez le dossier `workshop` et double-cliquez sur `agent1.ipynb`.

Et c'est parti !

Notez que chaque fois que vous voudrez relancer Jupyter Lab, vous devrez suivre ces instructions de la Partie 4 en partant du dossier `pstb_agenticai` avec l'environnement `pstb_agenticai` activé.