# AI Debate Engine

A Python project where two AI models (an advocate and a critic) debate your prompt, and a third AI model evaluates their arguments to provide the final answer.

## Features

- **Collaborative AI Reasoning:** Two models take opposing roles (advocate and critic) on any prompt you provide.
- **Debate and Evaluation:** Each model presents its arguments, after which a third AI model observes the debate and synthesizes a final answer.
- **Modular Design:** Easily extend or swap AI models for experimentation.

## How It Works

1. **Prompt Submission:** The user submits a question or prompt.
2. **Advocate & Critic:** Two AI models generate arguments for and against, or offer complementary perspectives.
3. **Evaluation:** A third AI model reviews the debate and produces a balanced, final answer.

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/ai-debate-engine.git
   cd ai-debate-engine
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   python main.py
   ```

## Example Usage

```python
from debate_engine import DebateEngine

engine = DebateEngine()
final_answer = engine.debate("Is AI beneficial to society?")
print(final_answer)
```

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](LICENSE)
