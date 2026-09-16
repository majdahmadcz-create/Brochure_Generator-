import json
import gradio as gr
from openai import OpenAI
from scraper import fetch_website_links, fetch_website_contents

print("All models run free and locally via Ollama - make sure `ollama serve` is running and the models below are pulled.")

OLLAMA_BASE_URL = "http://localhost:11434/v1"
MAX_CONTENT_CHARS = 8_000

# The openai SDK is just an HTTP client here - Ollama exposes an OpenAI-compatible API, no key or cloud calls involved.
ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

MODEL_CONFIGS = {
    "Gemma 3 270M": "gemma3:270m",
    "Llama 3.2 1B": "llama3.2:1b",
    "Llama 3.2 3B": "llama3.2:3b",
    "Qwen 2.5 1.5B": "qwen2.5:1.5b",
    "DeepSeek R1 1.5B": "deepseek-r1:1.5b",
    "Mistral 7B": "mistral",
    "GLM-4 9B": "glm4",
}

link_system_prompt = """
You are provided with a list of links found on a webpage.
You are able to decide which of the links would be most relevant to include in a brochure about the company,
such as an About page, a Company page, Careers/Jobs pages, Products/Pricing pages, a Team page, or a Press/News page.
You should respond in JSON as in this example:

{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
"""


def get_links_user_prompt(url):
    user_prompt = f"""
Here is the list of links on the website {url} -
Please decide which of these are relevant web links for a brochure about the company,
respond with the full https URL in JSON format.
Do not include Terms of Service, Privacy, or email links.

Links (some might be relative links):

"""
    links = fetch_website_links(url)
    user_prompt += "\n".join(links)
    return user_prompt


def select_relevant_links(url, model):
    print(f"Selecting relevant links for {url} using {model}")
    user_prompt = get_links_user_prompt(url)
    response = ollama.chat.completions.create(
        model=MODEL_CONFIGS[model],
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    result = response.choices[0].message.content

    result = result.strip().strip("`")
    if result.lower().startswith("json"):
        result = result[4:].strip()
    links = json.loads(result)
    print(f"Found {len(links.get('links', []))} relevant links")
    return links


def fetch_page_and_all_relevant_links(url, model):
    contents = fetch_website_contents(url)
    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
    try:
        relevant_links = select_relevant_links(url, model)
    except Exception as error:
        print(f"Could not select relevant links for {url}: {error}")
        return result
    for link in relevant_links.get("links", []):
        try:
            result += f"\n\n### Link: {link['type']}\n"
            result += fetch_website_contents(link["url"])
        except Exception as error:
            print(f"Skipping link {link.get('url')}: {error}")
    return result


brochure_system_prompt = """
You are an assistant that analyzes the contents of several relevant pages from a company website
and creates a compelling, well-structured brochure about the company for prospective customers,
investors and recruits.

Organize the brochure in markdown (without code blocks) using clear headings, for example:
- A short, punchy overview of what the company does
- Products / Services
- Company Culture and Values
- Customers (who they serve, notable clients or case studies if mentioned)
- Careers / Jobs (only if the source material has this information)
- How to learn more / contact

Only include a section if you actually have relevant information for it - do not invent facts.
Keep the tone engaging and professional, and make the company sound genuinely appealing.
"""


def get_brochure_user_prompt(company_name, url, model):
    user_prompt = f"""
You are looking at a company called: {company_name}
Here are the contents of its landing page and other relevant pages;
use this information to build a compelling brochure of the company in markdown without code blocks.

"""
    user_prompt += fetch_page_and_all_relevant_links(url, model)
    user_prompt = user_prompt[:MAX_CONTENT_CHARS]
    return user_prompt


def stream_completion(model, system_prompt, user_prompt):
    stream = ollama.chat.completions.create(
        model=MODEL_CONFIGS[model],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
    )
    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ""
        yield response


def stream_brochure(company_name, url, model):
    if model not in MODEL_CONFIGS:
        yield f"**Unknown model:** {model}"
        return

    yield "Scraping the website and picking out the relevant pages..."
    try:
        user_prompt = get_brochure_user_prompt(company_name, url, model)
    except Exception as error:
        yield f"**Something went wrong while scraping {url}:**\n\n{error}"
        return

    yield "Writing the brochure..."
    try:
        yield from stream_completion(model, brochure_system_prompt, user_prompt)
    except Exception as error:
        ollama_model = MODEL_CONFIGS[model]
        hint = f"\n\nMake sure Ollama is running locally (`ollama serve`) and the model is pulled (`ollama pull {ollama_model}`)."
        yield f"**Something went wrong while generating the brochure with {model}:**\n\n{error}{hint}"


view = gr.Interface(
    fn=stream_brochure,
    title="Brochure Generator",
    description="Scrapes a company's website, follows the most relevant links, and asks a free local LLM (via Ollama) to write a brochure. No API key required.",
    inputs=[
        gr.Textbox(label="Company name:", lines=2),
        gr.Textbox(label="Landing page URL including http:// or https://", lines=2),
        gr.Dropdown(list(MODEL_CONFIGS.keys()), label="Select model", value="Llama 3.2 3B"),
    ],
    outputs=[gr.Markdown(label="Brochure:")],
    examples=[
        ["Hugging Face", "https://huggingface.co", "Gemma 3 270M"],
        ["Hugging Face", "https://huggingface.co", "Llama 3.2 1B"],
        ["Anthropic", "https://www.anthropic.com", "Llama 3.2 3B"],
        ["OpenAI", "https://openai.com", "Qwen 2.5 1.5B"],
        ["Stripe", "https://stripe.com", "DeepSeek R1 1.5B"],
        ["Tesla", "https://www.tesla.com", "Mistral 7B"],
        ["Nvidia", "https://www.nvidia.com", "GLM-4 9B"]
    ],
    allow_flagging="never",
)

if __name__ == "__main__":
    view.launch(inbrowser=True, share=False)
