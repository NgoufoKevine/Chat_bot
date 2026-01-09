#!/usr/bin/env python3
"""
Migration des données de Qdrant local vers Qdrant Server
"""
from qdrant_client import QdrantClient
import os

# Ancien client (local file)
old_client = QdrantClient(path="./ease_qdrant.db")

# Nouveau client (server)
new_client = QdrantClient(host="localhost", port=6333)

COLLECTIONS = [
    "ease_tourisme",
    "ease_hotel",
    "ease_activites",
    "ease_appartements",
    "ease_voiture",
    "ease_visa",
    "ease_general"
]

def migrate_collection(collection_name):
    """Migre une collection"""
    print(f"\n📦 Migration: {collection_name}")
    
    try:
        # Récupérer info collection
        old_info = old_client.get_collection(collection_name)
        print(f"   Points dans ancienne DB: {old_info.points_count}")
        
        if old_info.points_count == 0:
            print(f"   ⚠️  Collection vide, création seulement")
            new_client.create_collection(
                collection_name=collection_name,
                vectors_config=old_info.config.params.vectors
            )
            return
        
        # Récupérer tous les points
        points, _ = old_client.scroll(
            collection_name=collection_name,
            limit=10000,
            with_payload=True,
            with_vectors=True
        )
        
        print(f"   📥 Récupéré {len(points)} points")
        
        # Créer collection dans nouveau serveur
        try:
            new_client.create_collection(
                collection_name=collection_name,
                vectors_config=old_info.config.params.vectors
            )
            print(f"   ✅ Collection créée")
        except Exception as e:
            if "already exists" in str(e):
                print(f"   ℹ️  Collection existe déjà")
            else:
                raise
        
        # Migrer les points
        if points:
            new_client.upsert(
                collection_name=collection_name,
                points=points
            )
            print(f"   ✅ {len(points)} points migrés")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    print("="*60)
    print("🔄 MIGRATION QDRANT LOCAL → SERVER")
    print("="*60)
    
    # Vérifier que le serveur est accessible
    try:
        new_client.get_collections()
        print("✅ Serveur Qdrant accessible\n")
    except Exception as e:
        print(f"❌ Serveur Qdrant non accessible: {e}")
        print("💡 Démarrer avec: docker-compose up -d")
        exit(1)
    
    # Migrer chaque collection
    for collection in COLLECTIONS:
        try:
            migrate_collection(collection)
        except Exception as e:
            print(f"❌ Erreur pour {collection}: {e}")
    
    print("\n" + "="*60)
    print("✅ Migration terminée!")
    print("="*60)
    print("\n💡 Prochaines étapes:")
    print("1. Vérifier: curl http://localhost:6333/collections")
    print("2. Mettre à jour qdrant_kb.py pour utiliser le serveur")
    print("3. Redémarrer vos applications")