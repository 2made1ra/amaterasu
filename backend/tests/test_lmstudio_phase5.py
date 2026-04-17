from types import SimpleNamespace

from app.services import document_indexing, fact_extraction, llm


def test_split_text_for_llm_respects_budget(monkeypatch):
    monkeypatch.setattr("app.services.llm.settings.LLM_CONTEXT_WINDOW", 1000)
    monkeypatch.setattr("app.services.llm.settings.LLM_RESERVED_OUTPUT_TOKENS", 100)
    monkeypatch.setattr("app.services.llm.settings.LLM_PROMPT_OVERHEAD_TOKENS", 100)
    monkeypatch.setattr("app.services.llm.settings.LLM_APPROX_CHARS_PER_TOKEN", 1.0)
    monkeypatch.setattr("app.services.llm.settings.LLM_CHUNK_OVERLAP_CHARS", 10)

    text = "A" * 2200

    chunks = llm.split_text_for_llm(text)

    assert len(chunks) >= 2
    assert all(chunk for chunk in chunks)
    assert max(len(chunk) for chunk in chunks) <= 1500


def test_lmstudio_embeddings_send_raw_strings_to_openai_compatible_api():
    captured = {}

    class FakeEmbeddingsClient:
        def create(self, *, model, input, encoding_format):
            captured["model"] = model
            captured["input"] = input
            captured["encoding_format"] = encoding_format
            return SimpleNamespace(
                data=[
                    SimpleNamespace(embedding=[0.1, 0.2, 0.3]),
                    SimpleNamespace(embedding=[0.4, 0.5, 0.6]),
                ]
            )

    client = SimpleNamespace(embeddings=FakeEmbeddingsClient())
    embeddings = llm.LMStudioEmbeddings(
        base_url="http://localhost:1234/v1",
        api_key="not-needed",
        model="text-embedding-nomic-embed-text-v1.5",
        client=client,
    )

    vectors = embeddings.embed_documents(["hello", "world"])

    assert vectors == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    assert captured == {
        "model": "text-embedding-nomic-embed-text-v1.5",
        "input": ["hello", "world"],
        "encoding_format": "float",
    }


def test_generate_document_summary_merges_partial_summaries(monkeypatch):
    prompts = []

    class FakeLlm:
        def invoke(self, prompt):
            prompts.append(prompt)
            if "Merge the partial summaries" in prompt:
                return "final merged summary"
            if "chunk 1/2" in prompt:
                return "summary from first chunk"
            return "summary from second chunk"

    monkeypatch.setattr(document_indexing, "get_llm", lambda purpose="default": FakeLlm())
    monkeypatch.setattr(document_indexing, "split_text_for_llm", lambda markdown: ["chunk-1", "chunk-2"])

    summary = document_indexing.generate_document_summary("long markdown", {"company_name": "Acme"})

    assert summary == "final merged summary"
    assert len(prompts) == 3


def test_request_facts_payload_merges_chunk_results(monkeypatch):
    responses = iter(
        [
            '{"company_name":"Acme","document_kind":"contract","parties":["Acme"],"source_hints":{"company_name":{"page_number":1,"snippet":"Acme"}}}',
            '{"service_price":"1000 RUB","summary":"Longer summary","parties":["Globex"]}',
        ]
    )

    class FakeLlm:
        def invoke(self, prompt):
            return next(responses)

    monkeypatch.setattr(fact_extraction, "get_llm", lambda purpose="default": FakeLlm())
    monkeypatch.setattr(fact_extraction, "split_text_for_llm", lambda markdown: ["chunk-1", "chunk-2"])

    payload = fact_extraction._request_facts_payload("long markdown")

    assert payload["company_name"] == "Acme"
    assert payload["service_price"] == "1000 RUB"
    assert payload["document_kind"] == "contract"
    assert payload["summary"] == "Longer summary"
    assert payload["parties"] == ["Acme", "Globex"]
    assert payload["source_hints"]["company_name"]["page_number"] == 1


def test_contract_vector_index_auto_detects_vector_size(monkeypatch):
    class FakeEmbeddings:
        def embed_documents(self, texts):
            return [[0.1, 0.2, 0.3]]

    class FakeCollections:
        collections = []

    class FakeClient:
        def get_collections(self):
            return FakeCollections()

    fake_models = SimpleNamespace(
        Distance=SimpleNamespace(COSINE="cosine"),
        VectorParams=lambda size, distance: SimpleNamespace(size=size, distance=distance),
    )
    fake_qdrant_module = SimpleNamespace(QdrantClient=lambda host, port: FakeClient())

    monkeypatch.setattr("app.services.qdrant_index.settings.QDRANT_AUTO_DETECT_VECTOR_SIZE", True)
    monkeypatch.setattr("app.services.qdrant_index.get_embeddings", lambda: FakeEmbeddings())

    import builtins

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "qdrant_client":
            return fake_qdrant_module
        if name == "qdrant_client.http":
            return SimpleNamespace(models=fake_models)
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    from app.services.qdrant_index import ContractVectorIndex

    index = ContractVectorIndex()

    assert index.collection_configs
    assert all(config.size == 3 for config in index.collection_configs.values())
