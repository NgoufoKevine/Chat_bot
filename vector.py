from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import Qdrant, QdrantVectorStore
from langchain_core.documents import Document
import json
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client import QdrantClient



# Modèle d'embedding Ollama
embeddings = OllamaEmbeddings(model="bge-m3:latest", temperature=0.2)

# Charger les données JSON
with open("doc_8_date_for_rag.json", "r", encoding="utf-8") as f:
    conv = json.load(f)

# Dossier local Qdrant
db_location = "./qdrant_local"
client = QdrantClient(path=db_location)


# Nom de la collection
collection_name = "history_chat"
client.delete_collection(collection_name="history_chat")

client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
            )


# Vérifier si la collection existe
collections_list = [c.name for c in client.get_collections().collections]
add_documents = collection_name not in collections_list

# print(f'add_documents : {add_documents}')
# print(f'collections_list : {collections_list}')


if add_documents:
    print(f"📦 Collection '{collection_name}' inexistante — création et ajout des documents...")
    documents = []
    ids=[]
    for dial in conv:
        print(f'dial : {dial}')
        msg_id = dial["id"]
        msg_text = dial["text"]
        date_str = msg_text.split(",", 1)[0]  # Extraire la date avant la virgule

        document = Document(
            page_content=msg_text,
            metadata={"date": date_str, "id": msg_id}
        )
        ids.append(str(msg_id))
        documents.append(document)



vector_store = QdrantVectorStore(
    collection_name="history_chat",
    # persist_directory=db_location,
    client = client,
    embedding = embeddings
)

if add_documents:
    vector_store.add_documents(documents=documents, ids=ids)
    
retriever = vector_store.as_retriever(search_type="similarity",
    search_kwargs={"k": 5}
)
# print(embeddings)