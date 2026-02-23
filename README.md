

## Installation 

Install Vllm : 

```

uv pip install -U vllm --torch-backend=auto --extra-index-url https://wheels.vllm.ai/nightly

uv pip install git+https://github.com/huggingface/transformers.git
```

Launch Vllm server :

```

docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HF_TOKEN=$HF_TOKEN" \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:nightly \
    --model zai-org/GLM-OCR \
    --allowed-local-media-path \ \
    --speculative-config '{"method": "mtp", "num_speculative_tokens": 1}' \
    --served-model-name glm-ocr


vllm serve zai-org/GLM-OCR --allowed-local-media-path / --port 8090 --served-model-name glm-ocr
```

[source](https://github.com/zai-org/GLM-OCR)