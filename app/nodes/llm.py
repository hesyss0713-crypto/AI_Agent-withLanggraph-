from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


def load_llm(model_id: str = "meta-llama/Llama-3.2-3B-Instruct"):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=torch.bfloat16,
        device_map="auto",
    )
    return tokenizer, model


def make_llm_runner(tokenizer: AutoTokenizer, model: AutoModelForCausalLM):
    def run_llm(system_prompt: str, user_prompt: str, max_tokens=512) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        chat_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = tokenizer(chat_text, return_tensors="pt").to(model.device)

        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
        )

        return tokenizer.decode(output_ids[0], skip_special_tokens=True)

    return run_llm
