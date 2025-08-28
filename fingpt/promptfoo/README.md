# Promptfoo for Prompt Stability

## Directory Structures

Each prompt will have its own directory. Inside, there are different configuration files per agent's prompts. This structure ensures clear separation of prompts and easier test maintenance.

```bash
promptfoo
├── README.md
├── financial_report
│   ├── agent_runner.py
│   └── delegation.yaml
├── primary_assistant
│   ├── agent_runner.py
│   ├── chit-chat.yaml
│   ├── delegation.yaml
│   └── not-supported.yaml
└── term_deposit
    ├── agent_runner.py
    └── delegation.yaml
```

## Workflow

1. Install Promptfoo. Noted that Promptfoo is an NPM package so it is easiest to install it globally as a global command. Follow the instructions here:

   - https://www.promptfoo.dev/docs/installation/

1. Start your local UI environment with `promptfoo view`

   - this will give you the UI to navigate your run results

1. Run the actual tests
   - **To run ONE set of test cases**:
     - `promptfoo eval -c promptfoo/primary_assistant/chit-chat.yaml`
     - this will run the chit-chat test cases for the agent's prompt: Primary Asisstant
   - **To run all the tests for a prompt, follow this example command:**
     - `promptfoo eval -c promptfoo/term_deposit/*.yaml`

## How It Works?

To offer the most flexibility our integration use Python scripts to trigger the LLMs to **EXACTLY** produce the same output as the agent's normal execution. The code is usually in the file `agent_runner.py`

**Example code**:

```python
agent = await Assistant.build_agent(
    RequestContext(""),
    module.prompt_srv(),
    llm,
)
result = await agent.ainvoke(
    {
        "messages": messages,
    },
    temperature=0.0,
)

return {
    "output": {
        "content": result.content,
        "tool_calls": result.tool_calls,
    }
}
```

In this code snippet, we directly use the `build_agent` method from the `Assistant` class. This guarantee that the output utilize the same prompts and tools as in code execution.

**TODO**

- [ ] Extract the testing requirements into an PromptFoo interface and require all agents to implement the interface so that our test runners can directly use with minimal setup.

## When to Evaluate

Whenever there are prompt updates, re-run promptfoo against all the effected prompts and only employ the new prompts if they are perform better than the previous prompts.

Some examples where Promptfoo will act as our guards are

- **There are bugs that require us to update our prompts**
  - _use Promptfoo to validate the changes._
- **We want to test our new optimized prompts either coming from OpenAI prompt generators or from a new fancy technique**
  - _use Promptfoo to validate the changes._
- **We apply new LLM optimization such as Semantic Caching to speed up our serving**
  - _use Promptfoo to validate correctness of cache's output._

### Shared Promptfoo Environment

In the near future, we can self-host Promptfoo inside our infrastructure to better track past experiments and share results. This task is currently in backlog.
