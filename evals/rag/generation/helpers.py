import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.agents.services.llm import get_llm
from app.rag.generation.generation import GenerationRequest, LLMGenerationService
from app.rag.retrieval.retrieval import RetrievedChunk

DATASET_PATH = (
    Path(__file__).resolve().parent / "generation_golden_v2.json"
)


def load_generation_cases() -> list[dict[str, Any]]:
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def generate_answer(
    query: str,
    symbol: str,
    horizon: str,
    retrieved_chunks: list[dict[str, Any]],
) -> str:
    serialized_chunks = json.dumps(retrieved_chunks, sort_keys=True)
    return _generate_answer_cached(query, symbol, horizon, serialized_chunks)


@lru_cache(maxsize=128)
def _generate_answer_cached(
    query: str,
    symbol: str,
    horizon: str,
    serialized_chunks: str,
) -> str:
    retrieved_chunks = json.loads(serialized_chunks)
    chunk_models = [
        RetrievedChunk(
            text=chunk["text"],
            source_id=chunk.get("source_id"),
            source_type=chunk.get("source_type"),
            doc_hash=chunk.get("doc_hash"),
            metadata=chunk.get("metadata", {}),
        )
        for chunk in retrieved_chunks
    ]
    generation_service = LLMGenerationService(llm=get_llm())
    response = generation_service.generate(
        request=GenerationRequest(
            query=query,
            symbol=symbol,
            horizon=horizon,
            retrieved_chunks=chunk_models,
            max_context_chunks=5,
        )
    )
    return response.answer