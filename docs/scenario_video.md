# Vidéo de présentation de Yokkuté : script de tournage

**Durée visée** : 5 à 6 minutes. **Format** : enregistrement d'écran (OBS Studio) + voix off.

## L'histoire

**Ibrahima Sarr**, 42 ans, maraîcher à **Sangalkam** (zone des Niayes), cultive l'oignon et la tomate depuis 6 ans sur un demi-hectare. Il arrose encore au seau et avec une vieille pompe qui tombe souvent en panne : il perd une partie de ses récoltes en saison sèche.
Il a une idée : **une motopompe solaire et un kit de goutte-à-goutte** pour cultiver un hectare entier et produire toute l'année. Mais il ne sait pas comment financer ce projet, ni si une institution lui fera confiance.
Un voisin lui parle d'une institution de microfinance qui étudie les dossiers rapidement et explique ses décisions.

## Données à saisir (vérifiées avec le modèle en service)

| Champ | Valeur |
|---|---|
| Nom / Prénom | Sarr / Ibrahima |
| Date de naissance | 12/03/1984 |
| Sexe | Masculin |
| Téléphone | 77 000 00 01 *(numéro fictif)* |
| Adresse | Sangalkam, Rufisque |
| Agence | Agence Dakar Plateau |
| Type de revenu | Indépendant |
| Profession | Agriculteur, éleveur, pêcheur |
| Situation familiale | Marié(e) |
| Logement | Propriétaire |
| Ancienneté de l'activité | 72 mois |
| Enfants / Taille du ménage | 4 / 8 |
| Revenu mensuel moyen estimé | 200 000 FCFA |
| Bien immobilier / Véhicule | Oui / Non |
| **Demande** | **Crédit agricole, 1 200 000 FCFA sur 12 mois** |
| Objet | Motopompe solaire et kit goutte-à-goutte (1 ha) |

**Résultat attendu** (vérifié, stable quel que soit le jour du tournage) :
- probabilité de défaut du montant demandé : **12,2 %**, au-dessus du seuil de 12 % ;
- mensualité demandée : 111 161 FCFA, soit **56 % du revenu** (maximum 40 %) ;
- recommandation : **accord réduit à 860 000 FCFA** (risque 11,6 %, mensualité 79 666 FCFA, 39,8 % du revenu) ;
- explication : la taille du ménage, la mensualité par rapport au revenu et la profession augmentent le risque ; **les 6 ans d'ancienneté** et le type de revenu le diminuent.

> ⚠️ Ne pas modifier ces valeurs : un autre revenu ou une autre durée peut faire basculer la recommandation (accord complet ou refus).

## Avant de tourner

1. Démarrer la base, l'API et le site (`docker start scoring-db metabase`, puis `uvicorn` et `npm run dev`).
2. Vérifier que le seuil est à 12 % (page Paramètres, en directeur).
3. Préparer trois onglets ou fenêtres de navigation privée : **agent** (Awa Ndiaye), **directeur** (Moussa Diop), **client** (créé pendant la vidéo).
4. Zoom du navigateur à 110 % ou 125 % pour la lisibilité, fermer les notifications.
5. Choisir l'adresse de connexion du client : elle doit finir par `@gmail.com` (règle de l'application). C'est seulement un identifiant, aucun e-mail n'est envoyé, mais préférez une adresse que vous contrôlez ou manifestement fictive.

---

## Scène 1 : Le problème (≈ 30 s)

**À l'écran** : page d'accueil, défilement lent jusqu'à « Comment ça marche ».

**Voix off**
> Voici Ibrahima Sarr, maraîcher à Sangalkam depuis six ans. Chaque saison sèche, il perd une partie de sa récolte faute d'eau. Il a une idée : une motopompe solaire et un système de goutte-à-goutte, pour cultiver un hectare toute l'année. Mais comment financer ce projet ? Et surtout, une institution lui fera-t-elle confiance ?

## Scène 2 : Les produits (≈ 20 s)

**À l'écran** : menu « Nos produits », s'arrêter sur la carte **Crédit agricole** (100 000 à 25 000 000 FCFA, 6 mois à 5 ans).

**Voix off**
> Un voisin lui parle d'une institution de microfinance qui utilise Yokkuté. Sur le site, il découvre un crédit pensé pour les agriculteurs. Il décide de se rendre en agence.

## Scène 3 : L'accueil et la fiche client (≈ 45 s)

**À l'écran** : connexion de l'**agent** → Clients → **+ Nouveau client** → saisie des données du tableau → **Créer le client**.
*Astuce : taper volontairement un mauvais numéro (72 123 45 67), sortir du champ pour montrer le message, puis le corriger.*

**Voix off**
> En agence, Awa, sa gestionnaire, l'accueille. Elle enregistre sa fiche : son activité, sa famille, son revenu moyen estimé. L'application vérifie les informations au fur et à mesure, par exemple le format du numéro de téléphone sénégalais.

## Scène 4 : La demande et le score expliqué (≈ 60 s) ★ moment clé

**À l'écran** : sur la fiche, **+ Nouvelle demande de crédit** → Crédit agricole, 1 200 000 FCFA, 12 mois, objet → **Créer la demande** → **Marquer le dossier complet** → **Calculer le score**. Défiler lentement sur le score, la jauge, « Ce qui explique ce score » et « Au regard de la politique de crédit ».

**Voix off**
> Ibrahima demande un million deux cent mille francs sur douze mois. En quelques secondes, le modèle évalue le risque : douze virgule deux pour cent de probabilité de défaut, juste au-dessus du seuil de l'institution. Surtout, la mensualité représenterait cinquante-six pour cent de son revenu : trop lourd.
> Le score n'est pas une boîte noire. Awa voit ce qui pèse : la taille du ménage et la mensualité augmentent le risque ; ses six ans d'expérience le diminuent. Le modèle recommande un accord réduit à huit cent soixante mille francs, une mensualité supportable.

## Scène 5 : L'avis de l'agent (≈ 20 s)

**À l'écran** : avis d'instruction → texte ci-dessous → **Enregistrer l'avis** → **Soumettre à la décision du directeur**.

*Avis* : « Visite de l'exploitation effectuée : 0,5 ha cultivé, débouchés réguliers au marché de Thiaroye. Projet cohérent. »

**Voix off**
> Awa ajoute son avis après la visite de l'exploitation, puis transmet le dossier au directeur.

## Scène 6 : La décision du directeur (≈ 60 s) ★ l'humain décide

**À l'écran** : connexion du **directeur** → Dossiers (filtre « Soumis à décision ») → ouvrir le dossier.
Décision : **Accorder avec modification**.
1. Saisir **1 000 000 FCFA sur 15 mois** : l'encadré indique **« Hors politique : motif obligatoire »** (risque 13,0 %).
2. Corriger en **860 000 FCFA sur 12 mois** : l'encadré passe à **« Conforme à la politique »**.
3. Commentaire : « Montant suggéré retenu : la motopompe est financée, le kit sera complété avec la prochaine récolte. » → **Enregistrer la décision**.

**Voix off**
> C'est le directeur qui décide, pas la machine. Il peut tester d'autres montants : un million sur quinze mois sortirait de la politique de crédit, et il devrait le justifier. Il retient finalement huit cent soixante mille francs : de quoi acheter la motopompe tout de suite. Sa décision, sa justification et la recommandation du modèle sont enregistrées dans un journal qu'on ne peut pas modifier.

## Scène 7 : Le décaissement (≈ 30 s)

**À l'écran** : retour sur le compte **agent** → ouvrir le dossier → **Décaisser le crédit** → mode **Mobile money**, référence « OM-20261112-0451 » → **Confirmer le décaissement** → afficher le calendrier des 12 échéances.

**Voix off**
> Le crédit est décaissé par mobile money. Le calendrier de remboursement est généré automatiquement : douze mensualités de soixante-dix-neuf mille six cent soixante-six francs.

## Scène 8 : L'espace client et l'assistant (≈ 60 s)

**À l'écran** :
1. Agent, fiche du client → **Accès à l'espace client** → adresse Gmail → **Créer l'accès** : le mot de passe temporaire s'affiche une seule fois.
2. Ouvrir une fenêtre privée → connexion du **client** → l'application demande de **changer le mot de passe**.
3. **Mon espace** : prochaine échéance, rappels, crédits.
4. **Assistant** : cliquer « Quelle est ma prochaine échéance ? », puis « Combien me reste-t-il à payer ? », puis « Puis-je refaire un crédit ? ».

**Voix off**
> Ibrahima n'est pas laissé seul après le décaissement. Depuis son téléphone, il consulte ses échéances, reçoit des rappels et pose ses questions à un assistant, qui ne répond que sur son propre compte.

## Scène 9 : La vue d'ensemble (≈ 25 s, facultatif)

**À l'écran** : compte **directeur** → **Tableau de bord** → onglet Risque (PAR 30 et ligne de la norme BCEAO), puis onglet Inclusion.

**Voix off**
> Pour la direction, un tableau de bord suit l'activité, la qualité du portefeuille face aux normes de la BCEAO et l'équité des décisions.

## Conclusion (≈ 15 s)

**À l'écran** : retour sur la page d'accueil.

**Voix off**
> Avec Yokkuté, Ibrahima a obtenu un crédit adapté à sa capacité de remboursement, une décision expliquée, et un suivi transparent. Décider en quelques minutes, pas à l'intuition.

---

## Après le tournage

Le dossier, la décision, le crédit et le compte client d'Ibrahima restent dans la base de développement : les décisions et le journal sont en ajout seul, ils ne peuvent pas être supprimés. Ce sont des données de démonstration, elles apparaîtront dans le tableau de bord après le prochain lancement de l'ETL.
