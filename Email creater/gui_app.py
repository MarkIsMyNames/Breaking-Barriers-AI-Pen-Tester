#!/usr/bin/env python3
"""
Qwen3-8B GGUF Model GUI Interface

A web-based interface for interacting with the Qwen3-8B language model
using Gradio and llama-cpp-python.
"""

from typing import Optional, Tuple
import logging
from pathlib import Path

import gradio as gr
from llama_cpp import Llama

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration Constants
# ============================================================================

class ModelConfig:
    """Model configuration constants."""
    PATH = "Qwen3-8B-Jailbroken.i1-Q4_K_M.gguf"
    CONTEXT_SIZE = 2048
    CPU_THREADS = 4
    GPU_LAYERS = 0  # Set to -1 to use GPU if available
    STOP_SEQUENCES = ["</s>", "User:", "Human:"]


class UIConfig:
    """UI configuration constants."""
    SERVER_NAME = "0.0.0.0"
    SERVER_PORT = 7860
    SHARE_LINK = False

    # Default generation parameters
    DEFAULT_MAX_TOKENS = 512
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_TOP_P = 0.9

    # Slider ranges
    MAX_TOKENS_RANGE = (50, 2048, 50)  # (min, max, step)
    TEMPERATURE_RANGE = (0.1, 2.0, 0.1)
    TOP_P_RANGE = (0.1, 1.0, 0.05)

    # Example prompts
    EXAMPLES = [
        "Write a short poem about artificial intelligence.",
        "Explain quantum computing in simple terms.",
        "What are the main benefits of using Python for data science?",
    ]


# ============================================================================
# Theme Configuration
# ============================================================================

def create_dark_theme() -> gr.themes.Soft:
    """
    Create a custom dark theme for the Gradio interface.

    Returns:
        Configured Gradio theme with dark color scheme
    """
    return gr.themes.Soft(primary_hue="blue").set(
        # Background colors
        body_background_fill="*neutral_950",
        body_background_fill_dark="*neutral_950",
        block_background_fill="*neutral_900",
        block_background_fill_dark="*neutral_900",
        input_background_fill="*neutral_800",
        input_background_fill_dark="*neutral_800",

        # Text colors
        body_text_color="*neutral_100",
        body_text_color_dark="*neutral_100",
        block_label_text_color="*neutral_100",
        block_label_text_color_dark="*neutral_100",
        block_title_text_color="*neutral_50",
        block_title_text_color_dark="*neutral_50",

        # Button colors
        button_primary_background_fill="*primary_600",
        button_primary_background_fill_dark="*primary_600",
        button_primary_text_color="white",
        button_primary_text_color_dark="white",
        button_secondary_background_fill="*neutral_700",
        button_secondary_background_fill_dark="*neutral_700",
        button_secondary_text_color="*neutral_100",
        button_secondary_text_color_dark="*neutral_100",

        # Input placeholder
        input_placeholder_color="*neutral_400",
        input_placeholder_color_dark="*neutral_400",
    )


CUSTOM_CSS = """
    .gradio-container { color: #e5e5e5 !important; }
    label, .label { color: #f5f5f5 !important; }
    .gr-button { color: #ffffff !important; }
    button { background-color: #404040 !important; color: #ffffff !important; }
    button.primary { background-color: #2563eb !important; }
    input::placeholder { color: #a3a3a3 !important; }
    textarea::placeholder { color: #a3a3a3 !important; }
    input, textarea { color: #f5f5f5 !important; }
"""


# ============================================================================
# Model Management
# ============================================================================

class ModelManager:
    """Manages the LLM model loading and inference."""

    def __init__(self, config: ModelConfig):
        """
        Initialize the model manager.

        Args:
            config: Model configuration object
        """
        self.config = config
        self.model: Optional[Llama] = None
        self._load_model()

    def _load_model(self) -> None:
        """Load the GGUF model into memory."""
        model_path = Path(self.config.PATH)

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {model_path.absolute()}"
            )

        logger.info(f"Loading model from {model_path}...")
        logger.info("This may take a moment depending on model size.")

        try:
            self.model = Llama(
                model_path=str(model_path),
                n_ctx=self.config.CONTEXT_SIZE,
                n_threads=self.config.CPU_THREADS,
                n_gpu_layers=self.config.GPU_LAYERS,
                verbose=False,
            )
            logger.info("Model loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float
    ) -> str:
        """
        Generate a response from the model.

        Args:
            prompt: Input text prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_p: Nucleus sampling parameter

        Returns:
            Generated text response
        """
        if not prompt.strip():
            return "⚠️ Please enter a prompt."

        if self.model is None:
            return "❌ Model not loaded. Please restart the application."

        try:
            logger.info(f"Generating response for prompt: {prompt[:50]}...")

            output = self.model(
                prompt,
                max_tokens=int(max_tokens),
                temperature=float(temperature),
                top_p=float(top_p),
                echo=False,
                stop=self.config.STOP_SEQUENCES,
            )

            response = output['choices'][0]['text'].strip()
            logger.info("Response generated successfully")
            return response

        except Exception as e:
            error_msg = f"❌ Error generating response: {str(e)}"
            logger.error(error_msg)
            return error_msg


# ============================================================================
# UI Components
# ============================================================================

def create_input_column(ui_config: UIConfig) -> Tuple:
    """
    Create the input column with prompt and settings.

    Args:
        ui_config: UI configuration object

    Returns:
        Tuple of UI components (prompt_input, max_tokens, temperature,
                               top_p, submit_btn, clear_btn)
    """
    with gr.Column():
        prompt_input = gr.Textbox(
            label="Enter your prompt",
            placeholder="Type your message here...",
            lines=5
        )

        with gr.Accordion("Advanced Settings", open=False):
            max_tokens = gr.Slider(
                minimum=ui_config.MAX_TOKENS_RANGE[0],
                maximum=ui_config.MAX_TOKENS_RANGE[1],
                value=ui_config.DEFAULT_MAX_TOKENS,
                step=ui_config.MAX_TOKENS_RANGE[2],
                label="Max Tokens",
                info="Maximum number of tokens to generate"
            )
            temperature = gr.Slider(
                minimum=ui_config.TEMPERATURE_RANGE[0],
                maximum=ui_config.TEMPERATURE_RANGE[1],
                value=ui_config.DEFAULT_TEMPERATURE,
                step=ui_config.TEMPERATURE_RANGE[2],
                label="Temperature",
                info="Higher values make output more random"
            )
            top_p = gr.Slider(
                minimum=ui_config.TOP_P_RANGE[0],
                maximum=ui_config.TOP_P_RANGE[1],
                value=ui_config.DEFAULT_TOP_P,
                step=ui_config.TOP_P_RANGE[2],
                label="Top P",
                info="Nucleus sampling threshold"
            )

        submit_btn = gr.Button("Generate Response", variant="primary")
        clear_btn = gr.Button("Clear")

    return prompt_input, max_tokens, temperature, top_p, submit_btn, clear_btn


def create_output_column() -> gr.Textbox:
    """
    Create the output column for model responses.

    Returns:
        Output textbox component
    """
    with gr.Column():
        output_text = gr.Textbox(
            label="Model Response",
            placeholder="Response will appear here...",
            lines=15,
            interactive=False,
            show_copy_button=True
        )
    return output_text


def clear_inputs() -> Tuple[str, str]:
    """
    Clear both input and output fields.

    Returns:
        Tuple of empty strings for prompt and output
    """
    return "", ""


# ============================================================================
# Main Application
# ============================================================================

def create_interface(model_manager: ModelManager, ui_config: UIConfig) -> gr.Blocks:
    """
    Create the main Gradio interface.

    Args:
        model_manager: Initialized model manager
        ui_config: UI configuration object

    Returns:
        Configured Gradio Blocks interface
    """
    with gr.Blocks(
        title="Qwen3-8B Chat Interface",
        theme=create_dark_theme(),
        css=CUSTOM_CSS
    ) as demo:
        # Header
        gr.Markdown("# 🤖 Qwen3-8B AI Model Interface")
        gr.Markdown(
            "Enter your prompt below and adjust the generation parameters as needed. "
            "Click the examples below to get started!"
        )

        # Main UI layout
        with gr.Row():
            components = create_input_column(ui_config)
            prompt_input, max_tokens, temperature, top_p, submit_btn, clear_btn = components
            output_text = create_output_column()

        # Event handlers
        submit_btn.click(
            fn=model_manager.generate,
            inputs=[prompt_input, max_tokens, temperature, top_p],
            outputs=output_text
        )

        clear_btn.click(
            fn=clear_inputs,
            outputs=[prompt_input, output_text]
        )

        # Example prompts
        gr.Examples(
            examples=[[example] for example in ui_config.EXAMPLES],
            inputs=prompt_input,
            label="Example Prompts"
        )

    return demo


def main():
    """Main application entry point."""
    try:
        # Initialize configuration
        model_config = ModelConfig()
        ui_config = UIConfig()

        # Load model
        model_manager = ModelManager(model_config)

        # Create and launch interface
        demo = create_interface(model_manager, ui_config)

        logger.info(f"Launching server on {ui_config.SERVER_NAME}:{ui_config.SERVER_PORT}")
        demo.launch(
            server_name=ui_config.SERVER_NAME,
            server_port=ui_config.SERVER_PORT,
            share=ui_config.SHARE_LINK
        )

    except Exception as e:
        logger.critical(f"Application failed to start: {e}")
        raise


if __name__ == "__main__":
    main()
