#!/usr/bin/env python3
"""
Script de réinitialisation du mot de passe admin
Usage: python reset_password.py
"""
import bcrypt
from database import db

def reset_admin_password():
    """Réinitialiser le mot de passe du premier utilisateur"""

    # Vérifier s'il y a des utilisateurs
    users = db.fetch_all("SELECT id, email, nom, prenom FROM utilisateurs ORDER BY id LIMIT 5")

    if not users:
        print("❌ Aucun utilisateur dans la base de données.")
        print("💡 Lancez l'application pour créer le premier compte.")
        return

    print("👥 Utilisateurs trouvés:")
    print("=" * 60)
    for i, u in enumerate(users, 1):
        print(f"{i}. ID={u[0]}, Email={u[1]}, Nom={u[2]} {u[3]}")
    print("=" * 60)

    # Demander quel utilisateur
    try:
        choix = input("\nNuméro de l'utilisateur à réinitialiser (1-{}): ".format(len(users)))
        index = int(choix) - 1

        if index < 0 or index >= len(users):
            print("❌ Choix invalide")
            return

        user_id = users[index][0]
        email = users[index][1]

    except (ValueError, KeyboardInterrupt):
        print("\n❌ Annulé")
        return

    # Demander nouveau mot de passe
    print(f"\n🔑 Réinitialisation pour : {email}")
    print("   Règles : min. 8 caractères, 1 chiffre")

    while True:
        try:
            new_password = input("Nouveau mot de passe: ").strip()

            if not new_password:
                print("❌ Annulé")
                return

            # Validation
            if len(new_password) < 8:
                print("❌ Trop court (min. 8 caractères)")
                continue

            if not any(c.isdigit() for c in new_password):
                print("❌ Doit contenir au moins 1 chiffre")
                continue

            # Confirmation
            confirm = input("Confirmer le mot de passe: ").strip()
            if new_password != confirm:
                print("❌ Les mots de passe ne correspondent pas")
                continue

            break

        except KeyboardInterrupt:
            print("\n❌ Annulé")
            return

    # Hash et mise à jour
    try:
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        db.execute_query(
            "UPDATE utilisateurs SET mot_de_passe = ? WHERE id = ?",
            (hashed.decode('utf-8'), user_id)
        )

        print(f"\n✅ Mot de passe réinitialisé pour {email}")
        print(f"   Vous pouvez maintenant vous connecter avec :")
        print(f"   Email: {email}")
        print(f"   Mot de passe: {new_password}")
        print("\n⚠️  Notez bien ce mot de passe !")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("RÉINITIALISATION MOT DE PASSE ADMIN")
    print("=" * 60)
    reset_admin_password()
