import os
import re
from huggingface_hub import snapshot_download
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, set_seed
import modal
import requests
from modal import App, Image, Secret

# ------------------------------------------------------------------------------
# Modal App Definition
# ------------------------------------------------------------------------------
app    = App("pricer-service")
image  = Image.debian_slim().pip_install("huggingface-hub", "torch", "transformers", "accelerate", "requests")
secrets = [Secret.from_name("hf_secret")]

# ------------------------------------------------------------------------------
# Model & Prompt Configuration
# ------------------------------------------------------------------------------
BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  
QUESTION   = "Please reply with only the numeric price in USD, no extra text."

# ------------------------------------------------------------------------------
# Pricer Class (CPU-only, tiny model)
# ------------------------------------------------------------------------------
@app.cls(image=image, secrets=secrets)
class Pricer:
    def __init__(self):
        # 1) Retrieve HF token injected by Modal
        token = os.getenv("HF_TOKEN")
        if not token:
            raise RuntimeError("HF_TOKEN not found in environment")

        # 2) Ensure the model is downloaded to the local HF cache
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub/")
        os.makedirs(cache_dir, exist_ok=True)
        snapshot_download(BASE_MODEL, local_dir=cache_dir, token=token)

        # 3) Load tokenizer & model on CPU
        self.tokenizer = AutoTokenizer.from_pretrained(
            BASE_MODEL, token=token
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token    = self.tokenizer.eos_token
            self.tokenizer.padding_side = "right"

        self.model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            torch_dtype=torch.float32,
            token=token
        )

    @modal.method()
    def price(self, description: str) -> float:
        # Deterministic output
        set_seed(42)

        # Build prompt
        prompt = f"{QUESTION}\n\n{description}"
        try:
            # Encode + generate
            inputs = self.tokenizer(prompt, return_tensors="pt", padding=True)
            attention_mask = torch.ones_like(inputs["input_ids"])
            outputs = self.model.generate(
                inputs["input_ids"],
                attention_mask=attention_mask,
                max_new_tokens=8,
                num_return_sequences=1,
                do_sample=False
            )
            text = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

            # Extract first number
            match = re.search(r"[-+]?\d*\.\d+|\d+", text)
            return float(match.group()) if match else 0.0
        except Exception as e:
            # Fallback to local Ollama
            try:
                print(f"⚠️ Falling back to Ollama: {e}")
                ollama_url = "http://127.0.0.1:11436/api/chat"
                ollama_model = "llama3"  # Or whatever local model you prefer
                ollama_prompt = {
                    "model": ollama_model,
                    "messages": [
                        {"role": "system", "content": "You estimate prices. Reply with only the numeric price."},
                        {"role": "user", "content": prompt}
                    ]
                }
                resp = requests.post(ollama_url, json=ollama_prompt)
                resp.raise_for_status()
                ollama_out = resp.json()
                # Adjust for whatever format Ollama returns. If in chat format:
                content = ollama_out.get("message", {}).get("content", "")
                match = re.search(r"[-+]?\d*\.\d+|\d+", content)
                return float(match.group()) if match else 0.0
            except Exception as ollama_e:
                print(f"❌ Ollama fallback also failed: {ollama_e}")
                return 0.0  # Or some sentinel/error value

    @modal.method()
    def wake_up(self) -> str:
        return "ok"
