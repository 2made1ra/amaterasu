import os
from langchain_community.llms import HuggingFacePipeline
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAI, OpenAIEmbeddings
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from app.core.config import settings

# Global caches to avoid instantiating the models on every request
_llm_instance = None
_embeddings_instance = None

def get_llm():
    global _llm_instance
    if _llm_instance is None:
        if settings.LLM_PROVIDER == "lmstudio":
            _llm_instance = OpenAI(
                base_url=settings.LMSTUDIO_API_BASE,
                api_key=settings.LMSTUDIO_API_KEY,
                model_name=settings.LLM_MODEL
            )
        else: # Default to HuggingFace
            model_id = settings.LLM_MODEL
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForCausalLM.from_pretrained(model_id)
            pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=256)
            _llm_instance = HuggingFacePipeline(pipeline=pipe)
    return _llm_instance

def get_embeddings():
    global _embeddings_instance
    if _embeddings_instance is None:
        if settings.EMBEDDINGS_PROVIDER == "lmstudio":
            _embeddings_instance = OpenAIEmbeddings(
                base_url=settings.LMSTUDIO_API_BASE,
                api_key=settings.LMSTUDIO_API_KEY,
                model=settings.EMBEDDINGS_MODEL
            )
        else: # Default to HuggingFace
            _embeddings_instance = HuggingFaceEmbeddings(model_name=settings.EMBEDDINGS_MODEL)
    return _embeddings_instance
