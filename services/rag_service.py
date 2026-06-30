import numpy as np

from config import RAG_TOP_K
from database.crud import (
    get_ready_attachment_chunks,
    get_ready_chunks_by_chat_id,
    get_ready_global_chunks,
    get_ready_social_chunks,
    get_ready_website_chunks
)
from services.embedding_service import generate_embedding


DEFAULT_MINIMUM_RELEVANCE = 0.20
ATTACHMENT_MINIMUM_RELEVANCE = 0.08


def cosine_similarity(first_vector, second_vector):
    first = np.asarray(first_vector, dtype=np.float32)
    second = np.asarray(second_vector, dtype=np.float32)

    if first.shape != second.shape:
        return 0.0

    first_norm = np.linalg.norm(first)
    second_norm = np.linalg.norm(second)

    if first_norm == 0 or second_norm == 0:
        return 0.0

    return float(np.dot(first, second) / (first_norm * second_norm))


def retrieve_relevant_context(
    chat_id,
    query,
    top_k=None,
    document_ids=None,
    global_document_ids=None,
    website_source_ids=None,
    social_source_ids=None,
    include_global_documents=True,
    include_website_sources=True,
    include_social_sources=True,
    minimum_relevance=DEFAULT_MINIMUM_RELEVANCE
):
    chat_chunks = get_ready_chunks_by_chat_id(
        chat_id=chat_id,
        document_ids=document_ids
    )

    global_chunks = (
        get_ready_global_chunks(global_document_ids=global_document_ids)
        if include_global_documents
        else []
    )

    website_chunks = (
        get_ready_website_chunks(website_source_ids=website_source_ids)
        if include_website_sources
        else []
    )

    social_chunks = (
        get_ready_social_chunks(social_source_ids=social_source_ids)
        if include_social_sources
        else []
    )

    if not any((chat_chunks, global_chunks, website_chunks, social_chunks)):
        return []

    query_embedding = generate_embedding(query)
    scored_chunks = []

    for chunk in chat_chunks:
        add_scored_item(
            scored_chunks,
            query_embedding,
            chunk.embedding,
            minimum_relevance,
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "source_scope": "chat",
                "filename": chunk.document.original_filename,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content
            }
        )

    for chunk in global_chunks:
        add_scored_item(
            scored_chunks,
            query_embedding,
            chunk.embedding,
            minimum_relevance,
            {
                "chunk_id": chunk.id,
                "document_id": chunk.global_document_id,
                "source_scope": "global",
                "filename": chunk.global_document.original_filename,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content
            }
        )

    for chunk in website_chunks:
        add_scored_item(
            scored_chunks,
            query_embedding,
            chunk.embedding,
            minimum_relevance,
            {
                "chunk_id": chunk.id,
                "document_id": chunk.website_source_id,
                "source_scope": "website",
                "filename": chunk.website_source.title or chunk.website_source.domain,
                "source_url": chunk.website_source.canonical_url or chunk.website_source.url,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content
            }
        )

    for chunk in social_chunks:
        add_scored_item(
            scored_chunks,
            query_embedding,
            chunk.embedding,
            minimum_relevance,
            {
                "chunk_id": chunk.id,
                "document_id": chunk.social_source_id,
                "source_scope": "social",
                "filename": chunk.social_source.title,
                "source_url": chunk.social_source.canonical_url or chunk.social_source.url,
                "platform": chunk.social_source.platform,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content
            }
        )

    scored_chunks.sort(key=lambda item: item["score"], reverse=True)
    return scored_chunks[: top_k if top_k is not None else RAG_TOP_K]


def retrieve_attachment_context(
    chat_id,
    query,
    attachment_ids,
    top_k=6,
    minimum_relevance=ATTACHMENT_MINIMUM_RELEVANCE
):
    chunks = get_ready_attachment_chunks(
        chat_id=chat_id,
        attachment_ids=attachment_ids
    )

    if not chunks:
        return []

    query_embedding = generate_embedding(query)
    scored_chunks = []

    for chunk in chunks:
        add_scored_item(
            scored_chunks,
            query_embedding,
            chunk.embedding,
            minimum_relevance,
            {
                "chunk_id": chunk.id,
                "document_id": chunk.attachment_id,
                "source_scope": "attachment",
                "filename": chunk.attachment.original_filename,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content
            }
        )

    scored_chunks.sort(key=lambda item: item["score"], reverse=True)
    return scored_chunks[:top_k]


def add_scored_item(
    destination,
    query_embedding,
    item_embedding,
    minimum_relevance,
    item
):
    if not item_embedding:
        return

    score = cosine_similarity(query_embedding, item_embedding)
    if score < minimum_relevance:
        return

    destination.append({**item, "score": score})


def build_rag_prompt(user_prompt, context_items, strict_mode=True):
    if not context_items:
        return user_prompt

    context_sections = []

    for index, item in enumerate(context_items, start=1):
        source_scope = item.get("source_scope")

        if source_scope == "website":
            source_detail = (
                f"{item['filename']} | Website | {item.get('source_url', '')}"
            )
        elif source_scope == "social":
            platform = item.get("platform") or "Social media"
            source_detail = (
                f"{item['filename']} | {platform} social source | "
                f"{item.get('source_url', '')}"
            )
        elif source_scope == "global":
            source_detail = f"{item['filename']} | Global library"
        elif source_scope == "attachment":
            source_detail = f"{item['filename']} | Message attachment"
        elif source_scope == "vision":
            source_detail = f"{item['filename']} | Vision analysis"
        else:
            source_detail = f"{item['filename']} | Chat document"

        context_sections.append(
            f"[Source {index}: {source_detail}]\n{item['content']}"
        )

    context_text = "\n\n".join(context_sections)

    if strict_mode:
        answer_policy = """
- Answer only from the supplied source context and directly attached images.
- Do not use outside knowledge to fill gaps.
- Do not invent names, dates, qualifications, experience, or other facts.
- If the context is insufficient, say exactly what information is missing.
""".strip()
    else:
        answer_policy = """
- Use the supplied source context and attached images as the primary source.
- You may add general knowledge only when you clearly label it as general information.
- Never present unsupported details as if they came from the supplied sources.
""".strip()

    return f"""
You are answering a question with retrieval-augmented generation.

Instructions:
{answer_policy}
- Cite supporting passages using [Source 1], [Source 2], and so on.
- Keep each citation attached to the claim it supports.
- Do not mention hidden retrieval scores or internal chunk IDs.
- A source marked Global library is reusable across conversations.
- A source marked Website is an indexed webpage from the global library.
- A source marked social source is indexed social-media content.
- A source marked Message attachment belongs to this user message.
- A source marked Chat document belongs only to the current conversation.

SOURCE CONTEXT:

{context_text}

USER QUESTION:

{user_prompt}
""".strip()
