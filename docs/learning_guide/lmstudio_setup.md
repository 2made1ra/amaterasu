# Using LM Studio with Amaterasu

This guide explains how to configure the Amaterasu project to use local models via [LM Studio](https://lmstudio.ai/). This allows you to run powerful models like Gemma or Qwen entirely on your own hardware, ensuring data privacy and reducing dependency on external APIs or heavy local transformers pipelines within the backend process itself.

## Why use LM Studio?

1.  **Offloading Compute**: LM Studio runs in a separate process, often utilizing GPU acceleration more efficiently than a generic Python environment.
2.  **Model Variety**: Easily swap between different models (Gemma, Qwen, Llama 3, etc.) without changing code.
3.  **OpenAI Compatibility**: LM Studio provides an API that mimics OpenAI, making integration straightforward.

## Prerequisites

- [LM Studio](https://lmstudio.ai/) installed and running.
- Amaterasu backend environment set up.

## Step 1: Set up LM Studio

1.  **Download a Model**: Open LM Studio and search for a model you want to use (e.g., `gemma-2b` or `qwen`).
2.  **Start the Local Server**:
    - Click on the **Local Server** icon (the double-headed arrow/hosting icon on the left sidebar).
    - Select your downloaded model from the dropdown at the top.
    - Click **Start Server**.
    - Note the **Server Port** (default is usually `1234`).
    - Note the **Base URL** (usually `http://localhost:1234/v1`).

## Step 2: Configure Amaterasu

The project uses environment variables to determine which LLM provider and model to use. You can set these in your `.env` file or export them in your terminal.

### Configuration for LLM (Text Generation)

To use LM Studio for the main AI Agent:

```env
LLM_PROVIDER=lmstudio
LLM_MODEL=your-model-identifier  # The name shown in LM Studio
LMSTUDIO_API_BASE=http://localhost:1234/v1
```

### Configuration for Embeddings

You can also use LM Studio for generating embeddings if the model you loaded supports it (though dedicated embedding models like `all-MiniLM-L6-v2` via HuggingFace are often faster and more specialized).

```env
EMBEDDINGS_PROVIDER=lmstudio
EMBEDDINGS_MODEL=your-embedding-model-identifier
LMSTUDIO_API_BASE=http://localhost:1234/v1
```

*Note: If you want to keep using local HuggingFace embeddings while using LM Studio for the LLM, simply leave `EMBEDDINGS_PROVIDER=huggingface` (the default).*

## Step 3: Verify the Setup

1.  Restart your Amaterasu backend.
2.  Observe the logs. You should no longer see the HuggingFace model download/loading messages if you switched to `lmstudio`.
3.  Interact with the Chat in the frontend. You should see requests appearing in the LM Studio "Logs" section.

## Troubleshooting

-   **Connection Refused**: Ensure the LM Studio server is actually started and the port matches `LMSTUDIO_API_BASE`.
-   **Model Not Found**: Ensure `LLM_MODEL` matches the identifier expected by LM Studio (though often LM Studio accepts any string if only one model is loaded).
-   **Performance**: If the response is slow, check if LM Studio is utilizing your GPU (Hardware Acceleration settings in LM Studio).
