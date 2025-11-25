import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

_vectorizer: TfidfVectorizer | None = None

def _ensure_vectorizer(text: str) -> TfidfVectorizer:
    global _vectorizer
    if _vectorizer is None:
        _vectorizer = TfidfVectorizer()
        _vectorizer.fit([text])
    return _vectorizer

def generate_embedding(text: str) -> np.ndarray:
    vec = _ensure_vectorizer(text).transform([text])
    return np.asarray(vec.todense(), dtype=np.float32).ravel()

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    if vec1.shape != vec2.shape:
        raise ValueError("Embedding vectors must have the same shape")
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

def batch_embeddings(texts: list[str]) -> np.ndarray:
    global _vectorizer
    if _vectorizer is None:
        _vectorizer = TfidfVectorizer()
        _vectorizer.fit(texts)
    else:
        _vectorizer.fit(texts)
    mat = _vectorizer.transform(texts)
    return np.asarray(mat.todense(), dtype=np.float32)
