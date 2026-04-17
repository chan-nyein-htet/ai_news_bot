import requests
from deep_translator import GoogleTranslator

def translate_and_refine(en_text, lang='my'):
    en_text = str(en_text) if en_text else ""
    if not en_text: return ""

    # ၁။ Google Draft (အမြဲတမ်း Ready ဖြစ်အောင်)
    try:
        draft = str(GoogleTranslator(source='auto', target=lang).translate(en_text))
    except:
        draft = en_text

    # ၂။ Ollama Refinement (Timeout 10s ပဲပေးမယ် - Busy ဖြစ်ရင် မစောင့်ဘူး)
    try:
        url = "http://localhost:11434/api/generate"
        prompt = (
            f"Instruction: Refine this Myanmar translation. KEEP all technical terms in English "
            f"(AI, GPU, LLM, Computing Infrastructure, Valuation, Startup). "
            f"Draft: {draft}\n\nRefined Myanmar:"
        )

        res = requests.post(url, json={"model": "phi3", "prompt": prompt, "stream": False, "options": {"temperature": 0.1}}, timeout=10)
        
        if res.status_code == 200:
            refined = res.json().get("response", "").strip()
            if refined and len(refined) > 5:
                return refined
        return draft
    except:
        # Ollama Busy ဖြစ်ရင် စောင့်မနေဘဲ Draft ကိုပဲ ပြန်ပေးမယ် Dude
        return draft

