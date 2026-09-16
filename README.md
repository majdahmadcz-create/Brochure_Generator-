# Brochure Generator

Scrapes a company's website, follows the most relevant links (About, Careers, Products, etc.),
and asks a local LLM to write a company brochure — streamed live in a Gradio UI.

Every model runs **free and locally via [Ollama](https://ollama.com)** — no API key, no cloud calls, no cost.

## How it works

1. You give it a company name and landing page URL.
2. It scrapes the page and asks the model which of the found links are worth following
   (About, Careers, Products, Team, Press, etc.).
3. It scrapes those pages too, then asks the model to write a structured markdown brochure,
   streaming the output live.

## Setup

1. Install [Ollama](https://ollama.com) and start it: `ollama serve`
2. Pull the models you want to use:
   ```
   ollama pull gemma3:270m
   ollama pull llama3.2:1b
   ollama pull llama3.2:3b
   ollama pull qwen2.5:1.5b
   ollama pull deepseek-r1:1.5b
   ollama pull mistral
   ollama pull glm4
   ```
3. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run it:
   ```
   python3 Brochure_Generator.py
   ```

The Gradio app opens in your browser (defaults to `http://127.0.0.1:7860`, or the next free port).

## Available models

| Dropdown label     | Ollama tag         | Size   |
|---------------------|---------------------|--------|
| Gemma 3 270M        | `gemma3:270m`       | ~0.3GB |
| Llama 3.2 1B        | `llama3.2:1b`       | ~1.3GB |
| Llama 3.2 3B        | `llama3.2:3b`       | ~2.0GB |
| Qwen 2.5 1.5B       | `qwen2.5:1.5b`      | ~1.0GB |
| DeepSeek R1 1.5B    | `deepseek-r1:1.5b`  | ~1.1GB |
| Mistral 7B          | `mistral`           | ~4.4GB |
| GLM-4 9B            | `glm4`              | ~5.5GB |

Smaller models are faster but less reliable at following instructions; larger models
(Llama 3.2 3B, Mistral 7B, GLM-4 9B) generally produce noticeably better brochures.

You only need to pull the models you actually plan to use — the app just won't offer
a working result for any model that isn't pulled (it'll tell you to run `ollama pull <model>`).