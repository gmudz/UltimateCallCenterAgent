"""
RAG Engine - Retrieval Augmented Generation
In-memory knowledge base with TF-IDF vectorization and semantic caching.
"""
import json, os, re, hashlib
from typing import Dict, List, Optional
from collections import defaultdict

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class RAGEngine:
    def __init__(self, knowledge_path: str = None):
        self.documents: List[Dict] = []
        self.doc_texts: List[str] = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.semantic_cache: Dict[str, Dict] = {}
        if knowledge_path:
            self.load_knowledge_base(knowledge_path)

    def load_knowledge_base(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            kb = json.load(f)
        company = kb.get("company_info", {})
        if company:
            self.add_document(
                f"شركة {company.get('name','')} ({company.get('name_en','')}). {company.get('tagline','')}. المميزات: " +
                "، ".join(company.get("competitive_advantages", [])),
                {"type": "company_info", "section": "overview"}
            )
            for lic in company.get("licenses", []):
                self.add_document(f"ترخيص {lic['authority']} — {lic['region']}: {lic['details']}", {"type": "license"})
            self.add_document("ميزات الأمان: " + "، ".join(company.get("security_features", [])), {"type": "security"})
        for term in kb.get("trading_terms", []):
            self.add_document(f"{term['term']} ({term['term_en']}): {term['definition']}", {"type": "term"})
        for comp in kb.get("competitor_comparisons", []):
            self.add_document(f"مقارنة مع {comp['competitor']}: {comp['our_advantage']}", {"type": "competitor"})
        for faq in kb.get("faq", []):
            self.add_document(f"سؤال: {faq['q']} — الإجابة: {faq['a']}", {"type": "faq"})
        self._build_index()

    def add_document(self, text: str, metadata: Dict = None):
        self.documents.append({"text": text, "metadata": metadata or {}, "id": len(self.documents)})
        self.doc_texts.append(text)

    def _build_index(self):
        if not self.doc_texts or not HAS_SKLEARN:
            return
        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), max_features=10000)
        self.tfidf_matrix = self.vectorizer.fit_transform(self.doc_texts)

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        cached = self._check_cache(query)
        if cached:
            return cached
        results = []
        if HAS_SKLEARN and self.vectorizer and self.tfidf_matrix is not None:
            from sklearn.metrics.pairwise import cosine_similarity
            query_vec = self.vectorizer.transform([query])
            sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            for idx in sims.argsort()[-top_k:][::-1]:
                if sims[idx] > 0.05:
                    results.append({"document": self.documents[idx], "score": round(float(sims[idx]), 3), "method": "tfidf"})
        kw = self._keyword_search(query, top_k)
        seen = {r["document"]["id"] for r in results}
        for kr in kw:
            if kr["document"]["id"] not in seen:
                results.append(kr)
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:top_k]
        self._cache_result(query, results)
        return results

    def _keyword_search(self, query: str, top_k: int) -> List[Dict]:
        qw = set(re.findall(r'\w+', query.lower()))
        scores = []
        for i, doc in enumerate(self.documents):
            dw = set(re.findall(r'\w+', doc["text"].lower()))
            overlap = len(qw & dw)
            if overlap > 0:
                scores.append((i, overlap / max(len(qw), 1)))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [{"document": self.documents[i], "score": round(s, 3), "method": "keyword"} for i, s in scores[:top_k] if s > 0.1]

    def _check_cache(self, query: str) -> Optional[List[Dict]]:
        h = hashlib.md5(query.encode()).hexdigest()
        if h in self.semantic_cache:
            return self.semantic_cache[h]["results"]
        return None

    def _cache_result(self, query: str, results: List[Dict]):
        h = hashlib.md5(query.encode()).hexdigest()
        self.semantic_cache[h] = {"results": results, "query_words": query.lower().split()}

    def get_context_for_query(self, query: str) -> str:
        results = self.search(query, top_k=5)
        if not results:
            return "لم يتم العثور على معلومات ذات صلة."
        return "\n".join(f"• {r['document']['text']}" for r in results)

    def remove_documents_by_source(self, source_file_id: str):
        """Remove all documents from a specific source file."""
        self.documents = [d for d in self.documents if d.get("metadata", {}).get("source_file") != source_file_id]
        self.doc_texts = [d["text"] for d in self.documents]
        # Re-assign IDs
        for i, d in enumerate(self.documents):
            d["id"] = i
        self.semantic_cache.clear()
        self._build_index()

    def get_document_sources(self) -> list:
        """Get unique document sources."""
        sources = {}
        for d in self.documents:
            src = d.get("metadata", {}).get("source_file", "built-in")
            name = d.get("metadata", {}).get("source_name", "قاعدة المعرفة الأساسية")
            if src not in sources:
                sources[src] = {"id": src, "name": name, "count": 0}
            sources[src]["count"] += 1
        return list(sources.values())

    def get_stats(self) -> Dict:
        return {"total_documents": len(self.documents), "cache_size": len(self.semantic_cache), "has_tfidf": HAS_SKLEARN}
