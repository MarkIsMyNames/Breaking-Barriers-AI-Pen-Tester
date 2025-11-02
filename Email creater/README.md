# Qwen 3:8b Jailbroken - AI Interface

AI-powered interface using the Qwen 3:8b Jailbroken model for penetration testing and security awareness training.

## Features

- **Local AI Processing**: Runs Qwen 3:8b model completely on your machine
- **Dark Mode Interface**: Clean, modern Gradio UI with optimized contrast
- **Customizable Parameters**: Adjust temperature, tokens, and sampling
- **No Cloud Dependencies**: All processing happens locally
- **Example Prompts**: Pre-configured examples to get started
- **Copy Functionality**: Easy copy button for generated responses
- **Proper Error Handling**: User-friendly error messages and logging

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Verify Model File

Ensure the model file is in the project directory:

```bash
ls -lh Qwen3-8b-Jailbroken
```

### 3. Launch

```bash
python qwen3_8b_jailbroken_gui.py
```

Access the interface at `http://localhost:7860`

## Usage

1. Open `http://localhost:7860` in your browser
2. Enter your prompt in the text area
3. Optionally adjust "Advanced Settings" (temperature, max tokens, top-p)
4. Click "Generate Response"
5. Copy the generated output using the copy button

### Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| Max Tokens | 50-2048 | 512 | Maximum output length |
| Temperature | 0.1-2.0 | 0.7 | Creativity level (higher = more random) |
| Top P | 0.1-1.0 | 0.9 | Nucleus sampling threshold |

## Configuration

Edit `qwen3_8b_jailbroken_gui.py` to modify settings:

```python
class ModelConfig:
    NAME = "Qwen 3:8b Jailbroken"
    PATH = "Qwen3-8b-Jailbroken"
    CONTEXT_SIZE = 2048
    CPU_THREADS = 4      # Adjust based on your CPU
    GPU_LAYERS = 0       # Set to >0 for GPU support
```

## Project Structure

```
Email creater/
├── qwen3_8b_jailbroken_gui.py    # Main application
├── Prompt.txt                     # System prompt template
├── requirements.txt               # Dependencies
├── Qwen3-8b-Jailbroken           # AI model (4.7GB)
├── .gitignore                     # Git ignore rules
└── README.md
```

## Troubleshooting

**Model Not Found**
- Verify the model file exists in the project directory
- Check filename matches `ModelConfig.PATH` in the code

**Out of Memory**
- Close other applications to free up RAM
- Reduce `CONTEXT_SIZE` in `ModelConfig`

**Slow Generation**
- Increase `CPU_THREADS` to match your CPU cores
- Reduce `max_tokens` parameter in the UI
- Enable GPU acceleration (see below)

**Port Already in Use**
- Change `SERVER_PORT` in `UIConfig` class

**Text Not Readable (Contrast Issues)**
- The dark theme is pre-configured for optimal readability
- If issues persist, check your browser's zoom level

## GPU Acceleration (Optional)

For faster inference with NVIDIA GPU:

```bash
pip uninstall llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python
```

Then set `GPU_LAYERS = 35` in `ModelConfig`.

## Requirements

- Python 3.8+
- llama-cpp-python
- gradio
- 8GB+ RAM recommended
- 5GB disk space for model
