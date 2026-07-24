import os
import secrets
import json

# Generate API key and print instructions
api_key = secrets.token_hex(32)

print("=" * 60)
print("  DISCORD BOT - DÉPLOIEMENT CLOUD")
print("=" * 60)
print()
print("  ÉTAPE 1: Créer un compte gratuit sur render.com")
print("          https://render.com/register")
print()
print("  ÉTAPE 2: Créer un 'New Web Service'")
print          "          - Connecte ton compte GitHub")
print("          - Sélectionne ce repo")
print("          - Build: pip install -r requirements-full.txt")
print("          - Start: gunicorn backend:app")
print()
print(f"  ÉTAPE 3: Ajouter cette variable d'environnement:")
print(f"          API_KEY = {api_key}")
print()
print("  ÉTAPE 4: Attendre le déploiement (~2 min)")
print()
print("  ÉTAPE 5: Ouvrir le dashboard sur GitHub Pages")
print("           et entrer l'URL Render + cette clé API")
print()
print("=" * 60)
print(f"  TA CLÉ API: {api_key}")
print("=" * 60)
print()
print("  Sauvegarde cette clé! Tu en auras besoin.")
print()

# Save the key to a file for reference
with open('API_KEY.txt', 'w') as f:
    f.write(api_key)
print("  Clé sauvegardée dans API_KEY.txt")
