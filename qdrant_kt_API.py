import os
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain.embeddings import OpenAIEmbeddings

import uuid


class QdrantKnowledgeBase:
    def __init__(
        self, 
        host: str = "localhost", 
        port: int = 6333,
        collection_name: str = None,
        embedding_model: str = None
    ):
        # Qdrant client
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name

        # Embeddings client (Gemini via OpenAI-compatible API)
        embedding_model = embedding_model or os.environ.get("OPENAI_EMBEDDING_MODEL")
        api_key = os.environ.get("OPENAI_API_KEY")
        

        if not api_key:
            raise ValueError("GEMINI_API_KEY must be provided or set as environment variable")

        self.embedder = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=api_key
        )

    def _embed_text(self, text: str) -> List[float]:
        """Return a semantic embedding vector using the embedder"""
        return self.embedder.embed_query(text)

    def create_collection(self, collection_name: str, vector_size: int = 1536):
        """Create a Qdrant collection if it does not exist"""
        collections = [c.name for c in self.client.get_collections().collections]

        if collection_name not in collections:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )
        self.collection_name = collection_name

    @staticmethod
    def _chunk_text(text: str, max_tokens: int = 350):
        """Simple chunking to avoid embedding very large text blocks"""
        sentences = text.split(". ")
        chunk, total = [], []

        for s in sentences:
            if len(" ".join(chunk + [s]).split()) <= max_tokens:
                chunk.append(s)
            else:
                total.append(". ".join(chunk))
                chunk = [s]

        if chunk:
            total.append(". ".join(chunk))

        return total

    def add_document(
        self,
        content: str,
        metadata: Dict,
        collection_name: str,
        doc_type: str = None
    ):
        if doc_type:
            metadata["doc_type"] = doc_type

        self.create_collection(collection_name)

        chunks = self._chunk_text(content)

        points = []
        for chunk in chunks:
            embedding = self._embed_text(chunk)
            point_id = uuid.uuid4().hex

            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": chunk,
                        **metadata
                    }
                )
            )

        self.client.upsert(collection_name=collection_name, points=points)

    def search(self, query: str, collection_name: str, limit: int = 4):
        """Semantic search"""
        embedding = self._embed_text(query)

        results = self.client.search(
            collection_name=collection_name,
            query_vector=embedding,
            limit=limit
        )

        return [
            {
                "score": hit.score,
                "text": hit.payload.get("text", ""),
                "metadata": hit.payload
            }
            for hit in results
        ]
