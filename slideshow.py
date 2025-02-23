from gurobipy import Model, GRB, quicksum
import itertools

#  Lecture du fichier d'entrée
def lire_fichier(nom_fichier):
    with open(nom_fichier, 'r') as f:
        lignes = f.readlines()

    N = int(lignes[0].strip())  # Nombre total de photos
    photos = []

    for i in range(1, N + 1):
        elements = lignes[i].strip().split()
        orientation = elements[0]
        tags = set(elements[2:])  # Ensemble de tags
        photos.append((i - 1, orientation, tags))  # (ID, Orientation, Tags)

    return N, photos

#  Étape 1 : Construction des diapositives
def construire_slides(photos):
    slides = []
    used = set()  # Photos déjà utilisées

    # Ajouter les photos horizontales directement
    for photo in photos:
        if photo[1] == "H" and photo[0] not in used:
            slides.append(([photo[0]], photo[2]))  # ([ID], tags)
            used.add(photo[0])

    # Regrouper les photos verticales par paires
    verticales = [p for p in photos if p[1] == "V" and p[0] not in used]
    
    while len(verticales) > 1:
        best_pair = None
        best_score = -1

        # Trouver la meilleure paire en maximisant la diversité des tags
        for p1, p2 in itertools.combinations(verticales, 2):
            score = len(p1[2].union(p2[2]))  # Maximisation de la diversité des tags
            if score > best_score:
                best_pair = (p1, p2)
                best_score = score

        if best_pair:
            slides.append(([best_pair[0][0], best_pair[1][0]], best_pair[0][2].union(best_pair[1][2])))
            used.add(best_pair[0][0])
            used.add(best_pair[1][0])
            verticales.remove(best_pair[0])
            verticales.remove(best_pair[1])

    print(f"\n✅ {len(slides)} diapositives construites.")

    # 🔍 Affichage des diapositives AVANT optimisation
    print("\n🔍 **Diaporama avant optimisation**")
    for idx, slide in enumerate(slides):
        print(f"Slide {idx}: {slide[0]}")

    return slides

#  Étape 2 : Calcul du score total d’un diaporama
def calculer_score(slides):
    if len(slides) < 2:
        return 0  # Pas de transitions possibles

    score_total = sum(
        min(
            len(slides[i][1].intersection(slides[i + 1][1])),  # Tags communs
            len(slides[i][1] - slides[i + 1][1]),  # Uniques à S_i
            len(slides[i + 1][1] - slides[i][1])  # Uniques à S_j
        )
        for i in range(len(slides) - 1)
    )
    
    return score_total

#  Étape 3 : Optimisation de l’ordre des diapositives avec Gurobi
def optimiser_ordre_slides(slides):
    model = Model("Optimisation_Slideshow")

    S = len(slides)
    if S == 0:
        return []  # Pas de slides à optimiser

    # Variables : ordre des diapositives
    o = model.addVars(S, S, vtype=GRB.BINARY, name="o")  # o[s, t] = 1 si la slide s précède la slide t

    # **Ajout d'une contrainte d'ordre pour forcer un chemin continu**
    model.addConstrs((quicksum(o[i, j] for j in range(S) if j != i) == 1 for i in range(S)), name="one_outgoing")
    model.addConstrs((quicksum(o[j, i] for j in range(S) if j != i) == 1 for i in range(S)), name="one_incoming")

    # Fonction Objectif : Maximiser le score total des transitions
    score = quicksum(
        o[s, t] * min(
            len(slides[s][1].intersection(slides[t][1])),  # Tags communs
            len(slides[s][1] - slides[t][1]),  # Uniques à s
            len(slides[t][1] - slides[s][1])  # Uniques à t
        )
        for s in range(S) for t in range(S) if s != t
    )

    model.setObjective(score, GRB.MAXIMIZE)

    #  Résolution du modèle
    model.optimize()

    # Récupération de l'ordre optimal
    ordered_slides = []
    used = []
    for s in range(S):
        for t in range(S):
            if o[s, t].X > 0.5 and slides[s] not in used:
                ordered_slides.append(slides[s])
                used.append(slides[s])
            

    if not ordered_slides:
        ordered_slides = slides  # Garder l'ordre initial si Gurobi ne modifie rien

    #  Affichage des diapositives APRÈS optimisation
    print("\n **Diaporama après optimisation avec Gurobi**")
    for idx, slide in enumerate(ordered_slides):
        print(f"Slide {idx}: {slide[0]}")

    return ordered_slides
    


#  Étape 4 : Génération du fichier de sortie
def ecrire_fichier_sortie(nom_fichier_sortie, slides):
    if not slides:
        print("\n⚠️ Aucune diapositive valide trouvée. Fichier non généré.")
        return

    with open(nom_fichier_sortie, 'w') as f:
        f.write(f"{len(slides)}\n")
        for slide in slides:
            f.write(" ".join(map(str, slide[0])) + "\n")

    print(f"\n✅ **Diaporama sauvegardé dans {nom_fichier_sortie}**")

#  Exécution du programme
nom_fichier = "data/PetPics-20.txt"
N, photos = lire_fichier(nom_fichier)
slides = construire_slides(photos)

score_avant = calculer_score(slides)
print(f"\n **Score total AVANT optimisation : {score_avant}**")

diaporama = optimiser_ordre_slides(slides)

score_apres = calculer_score(diaporama)


ecrire_fichier_sortie("data/slideshow.sol", diaporama)

print("\n **Diaporama Final**")
for idx, slide in enumerate(diaporama):
    print(f"Slide {idx}: {slide[0]}")
