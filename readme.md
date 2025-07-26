## Pré-configuration : exécuter Ollama en local avec des outils open-source

Avant la configuration complète, essayez d'abord d'installer Ollama pour voir des résultats immédiatement !

1. Téléchargez et installez Ollama depuis https://ollama.com. Notez que sur un PC, vous pourriez avoir besoin de droits administrateur pour que l'installation fonctionne correctement.
2. Sur un PC, ouvrez l'invite de commande ou PowerShell (Appuyez sur Win + R, tapez `cmd`, puis Entrée).
3. Exécutez `ollama run llama3.2` ou, pour des machines moins puissantes, essayez `ollama run llama3.2:1b`.  
   **Attention** : évitez le modèle le plus récent de Meta, `llama3.3`, car avec 70 milliards de paramètres, il est beaucoup trop lourd pour la plupart des ordinateurs domestiques !
4. Si cela ne fonctionne pas, vous devrez peut-être lancer `ollama serve` dans un autre PowerShell (Windows) et réessayer l'étape 3.
5. Si cela ne fonctionne toujours pas, j'ai prévu une version dans le cloud via Google Colab. Il vous faudra un compte Google, mais c'est gratuit :  
   https://colab.research.google.com/drive/1-_f5XZPsChvfU1sJ0QqCePtIuc55LSdu?usp=sharing

## Instructions de configuration

J'espère que j'ai fait un bon travail pour rendre ces guides infaillibles - mais contactez-moi immédiatement si vous rencontrez des blocages :

- Utilisateurs PC : suivez les instructions dans [SETUP-PC.md](SETUP-PC.md)
- Utilisateurs Mac : fichier non encore disponible
- Utilisateurs Linux : les instructions Mac devraient être suffisamment proches !

### Un point important sur les coûts d'API (optionnels ! inutile de dépenser si vous ne le souhaitez pas)

Dans ce projet d'exemple, je vous suggérerai d'essayer les modèles les plus avancés du moment, appelés modèles "Frontier". Ces services peuvent avoir des coûts, mais je veillerai à ce qu'ils soient minimes - quelques centimes à la fois. Et je fournirai des alternatives si vous préférez ne rien dépenser.

Surveillez votre utilisation d'API pour être à l'aise avec les dépenses. Il n'est pas nécessaire de dépenser plus de quelques euros pour tout le cours. Certains fournisseurs comme OpenAI demandent un crédit minimum (par ex. 5 $), mais nous n'en utiliserons qu'une petite fraction. Cela dit, ce n'est absolument pas indispensable : l'important est de se concentrer sur l'apprentissage.

### Alternative gratuite aux API payantes

Voici une alternative si vous préférez ne rien dépenser pour des API :  
Chaque fois que nous avons du code comme :  
`openai = OpenAI()`  
Vous pouvez le remplacer directement par :  
`openai = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')`

Voici un exemple complet :

```python
# Vous devez faire cela une seule fois sur votre ordinateur
!ollama pull llama3.2

from openai import OpenAI
MODEL = "llama3.2"
openai = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

response = openai.chat.completions.create(
 model=MODEL,
 messages=[{"role": "user", "content": "Combien font 2 + 2 ?"}]
)

print(response.choices[0].message.content)