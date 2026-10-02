"""
RAG index: chunking -> TF-IDF embeddings -> FAISS (with an automatic
numpy-cosine-similarity fallback if FAISS isn't available on a given
host) -> retrieval.

Why TF-IDF instead of a neural embedding model: it needs no external API
key, no model download at runtime (neural embedding models would need to
fetch weights from a host not every deployment target can reach), and no
GPU/heavy runtime dependency — all of which matter for a lean, low-cost
deployment. It's a legitimate, classic embedding representation and is
swappable for a neural embedder later (e.g. OpenAI/Groq embeddings, or
sentence-transformers) without changing the retrieval interface below.

The index is built once per process (properties + static knowledge docs)
and cached in memory. Call reset() if the underlying property data
changes and the index needs to be rebuilt.
"""
import logging
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.orm import Session

from app.models import Property
from app.rag.knowledge_base import STATIC_DOCS
from app.rag.chunking import chunk_text

logger = logging.getLogger("property_pulse")

try:
    import faiss
    _HAS_FAISS = True
except ImportError:
    _HAS_FAISS = False
    logger.warning("faiss not available, falling back to numpy cosine similarity for RAG")


@dataclass
class Doc:
    id: str
    title: str
    text: str
    source_type: str  # "knowledge" | "property"
    property_id: int | None = None


class RAGIndex:
    def __init__(self):
        self.docs: list[Doc] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.matrix = None  # normalized float32 dense array
        self.faiss_index = None

    def build(self, db: Session):
        docs: list[Doc] = []

        for d in STATIC_DOCS:
            for i, chunk in enumerate(chunk_text(d["text"])):
                docs.append(Doc(
                    id=f"{d['id']}-{i}",
                    title=d["title"],
                    text=chunk,
                    source_type="knowledge",
                ))

        for p in db.query(Property).all():
            text = (
                f"{p.name} in {p.location}, built by {p.builder}. "
                f"{p.property_type}, {p.bedrooms} BHK, {p.area_sqft} sq.ft. "
                f"Amenities: {p.amenities or 'not specified'}. "
                f"{p.description or ''}"
            ).strip()
            for i, chunk in enumerate(chunk_text(text)):
                docs.append(Doc(
                    id=f"property-{p.id}-{i}",
                    title=p.name,
                    text=chunk,
                    source_type="property",
                    property_id=p.id,
                ))

        if not docs:
            logger.warning("RAG index build found no documents")
            self.docs = []
            return

        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=4096)
        # Weight titles more heavily than body text so a query like
        # "tell me about Whitefield" ranks the Whitefield overview above
        # a property that merely happens to be located there.
        indexed_texts = [f"{d.title} {d.title} {d.title}. {d.text}" for d in docs]
        sparse_matrix = self.vectorizer.fit_transform(indexed_texts)
        dense = sparse_matrix.toarray().astype("float32")
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        dense = dense / norms

        self.docs = docs
        self.matrix = dense

        if _HAS_FAISS:
            dim = dense.shape[1]
            index = faiss.IndexFlatIP(dim)
            index.add(dense)
            self.faiss_index = index
        else:
            self.faiss_index = None

        logger.info("RAG index built: %d chunks (%d properties)", len(docs), db.query(Property).count())

    def search(self, query: str, k: int = 4) -> list[dict]:
        if not self.docs or self.vectorizer is None:
            return []

        q_vec = self.vectorizer.transform([query]).toarray().astype("float32")
        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec = q_vec / norm

        if self.faiss_index is not None:
            scores, indices = self.faiss_index.search(q_vec, min(k, len(self.docs)))
            scores, indices = scores[0], indices[0]
        else:
            sims = (self.matrix @ q_vec[0])
            indices = np.argsort(-sims)[:k]
            scores = sims[indices]

        results = []
        for score, idx in zip(scores, indices):
            if idx < 0 or idx >= len(self.docs):
                continue
            doc = self.docs[idx]
            results.append({
                "title": doc.title,
                "text": doc.text,
                "source_type": doc.source_type,
                "property_id": doc.property_id,
                "score": float(score),
            })
        return results


_index: RAGIndex | None = None


def get_index(db: Session) -> RAGIndex:
    global _index
    if _index is None:
        _index = RAGIndex()
        _index.build(db)
    return _index


def reset_index():
    global _index
    _index = None
