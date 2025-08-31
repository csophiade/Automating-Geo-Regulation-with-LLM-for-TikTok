from transformers import AutoTokenizer, AutoModelForCausalLM
import torch, os

MODEL_ID = os.environ.get("LLM_MODEL_ID", "Qwen/Qwen2.5-0.5B-Instruct")

_tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)
# Force CPU to avoid disk offload; keep memory low
_model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    device_map={"": "cpu"},
    low_cpu_mem_usage=True,
)

def generate_json(system_prompt: str, user_prompt: str, temperature: float = 0.0, max_new_tokens: int = 600) -> str:
    # Build a simple chat format most instruct models accept
    prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}\n<|assistant|>\n"
    inputs = _tokenizer(prompt, return_tensors="pt")
    # Deterministic, short outputs for speed on CPU
    out = _model.generate(
        **{k: v for k, v in inputs.items()},
        max_new_tokens=max_new_tokens,
        do_sample=False,              # deterministic, ignores temperature
        num_beams=1,
        eos_token_id=_tokenizer.eos_token_id,
        pad_token_id=_tokenizer.eos_token_id,
    )
    return _tokenizer.decode(out[0], skip_special_tokens=True).split("<|assistant|>")[-1].strip()