import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import gradio as gr

from app.agents.orchestrator import Orchestrator
from app.core.llm_service import AzureOpenAIProvider, OpenAILLMProvider
from config.settings import get_settings


def _build_orchestrator() -> Orchestrator:
    settings = get_settings()
    if settings.azure_openai.endpoint and settings.azure_openai.api_key:
        provider = AzureOpenAIProvider(
            endpoint=settings.azure_openai.endpoint,
            api_key=settings.azure_openai.api_key,
            deployment_name=settings.azure_openai.deployment_name,
            api_version=settings.azure_openai.api_version,
            temperature=settings.azure_openai.temperature,
            max_tokens=settings.azure_openai.max_tokens,
        )
    elif settings.openai_api_key:
        provider = OpenAILLMProvider(
            api_key=settings.openai_api_key,
            model_name=settings.azure_openai.deployment_name or "gpt-4o-mini",
            max_tokens=settings.azure_openai.max_tokens,
            temperature=settings.azure_openai.temperature,
        )
    else:
        raise RuntimeError("No LLM API key configured. Set AZURE_OPENAI_API_KEY or OPENAI_API_KEY.")
    return Orchestrator(provider, settings)


async def _respond(user_msg: str, history: list, orchestrator):
    if not user_msg.strip():
        return history, "", orchestrator
    if orchestrator is None:
        orchestrator = _build_orchestrator()
    response = await orchestrator.process(user_msg)
    history = history + [(user_msg, response)]
    return history, "", orchestrator


def _reset(orchestrator):
    if orchestrator is not None:
        orchestrator.reset()
    return [], orchestrator


with gr.Blocks(title="SurfSense", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# 🏄 SurfSense\n"
        "AI surf trip planning assistant. Ask about conditions, spots, and trip itineraries worldwide.\n\n"
        "*Tip: mention your skill level (beginner / intermediate / advanced) and a surf spot to get started.*"
    )

    state = gr.State(None)

    chatbot = gr.Chatbot(height=520, label="SurfSense", show_copy_button=True)

    with gr.Row():
        msg_box = gr.Textbox(
            placeholder="e.g. I'm an intermediate surfer — how are conditions at Pipeline this week?",
            show_label=False,
            scale=9,
            lines=1,
        )
        send_btn = gr.Button("Send", scale=1, variant="primary")

    reset_btn = gr.Button("Reset conversation", variant="secondary", size="sm")

    for trigger in (send_btn.click, msg_box.submit):
        trigger(
            fn=_respond,
            inputs=[msg_box, chatbot, state],
            outputs=[chatbot, msg_box, state],
        )

    reset_btn.click(fn=_reset, inputs=[state], outputs=[chatbot, state])


if __name__ == "__main__":
    demo.launch()
