import requests
import json

def translate_and_refine(text):
    """
    Ollama (Llama 3) ကို သုံးပြီး သတင်းများကို စိတ်ဝင်စားဖွယ် 
    မြန်မာဘာသာပြန်နှင့် အနှစ်ချုပ် ပြုလုပ်ပေးမည့် Function
    """
    
    url = "http://localhost:11434/api/generate"
    
    # Prompt ကို format ပိုကျအောင် ပြင်လိုက်တယ် Dude
    prompt = (
        f"You are a professional news editor. Translate the following English news into catchy and interesting Myanmar language. "
        f"Instructions: "
        f"1. Headline: Make it bold and exciting. "
        f"2. Summary: Explain clearly with 2-3 detailed bullet points in Myanmar. "
        f"3. Tone: Professional and engaging Burmese. "
        f"4. Keep technical names like OpenAI, Google, Anthropic, NVIDIA as they are. "
        f"Text to process: {text}"
    )
    
    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "Translation Error").strip()
        else:
            return f"Error: AI model is not responding (Status: {response.status_code})"
            
    except Exception as e:
        return f"Translation Service Error: {str(e)}"

if __name__ == "__main__":
    test_text = "NVIDIA reaches new market cap record as AI chips demand surges."
    print("--- Test Translation ---")
    print(translate_and_refine(test_text))

