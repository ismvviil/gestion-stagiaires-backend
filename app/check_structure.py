import os

def check_project_structure():
    print("=== VÉRIFICATION DE LA STRUCTURE DU PROJET ===")
    
    # Répertoire actuel
    current_dir = os.getcwd()
    print(f"Répertoire actuel: {current_dir}")
    
    # Vérifier si le dossier uploads existe
    uploads_dir = "uploads"
    uploads_path = os.path.join(current_dir, uploads_dir)
    
    print(f"\nVérification du dossier uploads: {uploads_path}")
    if os.path.exists(uploads_path):
        print("✅ Le dossier uploads existe")
        
        # Lister les fichiers dans uploads
        files = os.listdir(uploads_path)
        print(f"Fichiers dans uploads: {files}")
        
        # Vérifier le fichier spécifique
        target_file = "1736375619848.jpg"
        target_path = os.path.join(uploads_path, target_file)
        if os.path.exists(target_path):
            print(f"✅ Le fichier {target_file} existe")
            file_size = os.path.getsize(target_path)
            print(f"Taille du fichier: {file_size} bytes")
        else:
            print(f"❌ Le fichier {target_file} n'existe pas")
    else:
        print("❌ Le dossier uploads n'existe pas")
        
        # Chercher des fichiers image dans le projet
        print("\nRecherche de fichiers image dans le projet...")
        for root, dirs, files in os.walk(current_dir):
            for file in files:
                if file.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    print(f"Image trouvée: {os.path.join(root, file)}")
    
    # Vérifier les autres dossiers possibles
    possible_dirs = ["static", "media", "images", "files", "storage"]
    print(f"\nVérification d'autres dossiers possibles...")
    for dir_name in possible_dirs:
        dir_path = os.path.join(current_dir, dir_name)
        if os.path.exists(dir_path):
            print(f"✅ Dossier trouvé: {dir_name}")
            files = os.listdir(dir_path)
            if files:
                print(f"   Fichiers: {files[:5]}...")  # Afficher les 5 premiers

if __name__ == "__main__":
    check_project_structure()