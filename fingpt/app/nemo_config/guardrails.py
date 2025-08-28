import functools
import json
import os
from typing import Tuple

from langfuse import Langfuse  # type: ignore
from nemoguardrails import RailsConfig  # type: ignore
from nemoguardrails.integrations.langchain.runnable_rails import (
    LLMRails,  # type: ignore
)

from app.entity.error import GuardrailInputError
from app.nemo_config.input_config.actions import self_check_user_query
from app.nemo_config.output_config.actions import self_check_bot_response
from app.utils.modified_langfuse_decorator import observe  # type: ignore

# Initialize Langfuse
langfuse = Langfuse()


def load_config(config_path: str) -> str:
    """
    Load and process the configuration file, replacing placeholders with environment variables.
    """
    with open(f"{config_path}/config.yml", "r") as file:
        config = file.read()

    # Define environment variables to replace in the config
    env_vars = {
        "AZURE_OPENAI_ENDPOINT": "",
        "OPENAI_API_VERSION": "",
        "AZURE_OPENAI_DEPLOYMENT": "",
        "AZURE_OPENAI_API_KEY": "",
    }

    # Replace placeholders with actual environment variables
    for key, default in env_vars.items():
        config = config.replace(key, os.getenv(key, default))

    return config


def load_prompt(config_path: str, action_name: str) -> str:
    with open(f"{config_path}/prompts.yml", "r") as file:
        prompt = file.read()

    # Fetch the prompt from Langfuse
    prompt_template = langfuse.get_prompt(
        name=os.getenv(f"{action_name.upper()}_PROMPT"),
        type="chat",
        label=os.getenv(f"{action_name.upper()}_LABEL"),
    )

    prompt_template_content = prompt_template.prompt[0]["content"].strip()
    # Fix the indentation level for YAML
    indentation_level = " " * 6  # 6 spaces
    formatted_template_lines = [
        indentation_level + line if line.strip() != "" else line
        for line in prompt_template_content.strip().splitlines()
    ]

    # Join the formatted lines into a single string
    formatted_prompt_template_content = "\n".join(formatted_template_lines)

    final_prompt_template_content = prompt.replace(
        f"{action_name.upper()}", formatted_prompt_template_content
    )

    return final_prompt_template_content


def load_colang(config_path: str) -> str:
    """
    Load the Colang content from the rails.co file.
    """
    with open(f"{config_path}/rails/rails.co", "r") as file:
        return file.read()


def create_guardrails(config_path: str, action: callable) -> LLMRails:  # type: ignore
    """
    Create and configure the LLMRails object with the loaded configurations.
    """
    config = load_config(config_path)
    prompt = load_prompt(config_path, action.__name__)  # type: ignore
    colang = load_colang(config_path)

    yaml_content = f"{config}\n\n{prompt}"
    rails_config = RailsConfig.from_content(
        yaml_content=yaml_content, colang_content=colang
    )

    guardrails = LLMRails(rails_config)
    guardrails.register_action(action, action.__name__)  # type: ignore
    return guardrails


@observe()
async def process_guardrails(guardrails: LLMRails, content: str) -> Tuple[bool, dict]:
    """
    Process the input through the guardrails and return the result.
    """
    response = await guardrails.generate_async(
        messages=[{"role": "user", "content": content}]
    )
    json_response = json.loads(response["content"])

    if json_response["message"].lower() == "yes":
        return False, {
            "message": "Sorry, I don't support this.",
            "reason": json_response["reason"],
            "summary": f"Sorry, I don't support this. The reason is {json_response['reason']}",
        }
    return True, {}


@observe()
async def guardrails_input_func(user_query: str) -> Tuple[bool, dict]:
    """
    Apply input guardrails to the user query.
    """
    input_guardrails = create_guardrails(
        "app/nemo_config/input_config", self_check_user_query
    )
    return await process_guardrails(input_guardrails, user_query)


@observe()
async def guardrails_output_func(llm_response: str) -> Tuple[bool, dict]:
    """
    Apply output guardrails to the LLM response.
    """
    output_guardrails = create_guardrails(
        "app/nemo_config/output_config", self_check_bot_response
    )
    return await process_guardrails(output_guardrails, llm_response)


def guardrails_input(arg_name: str):
    """Guardrail Input decorator

    Args:
        arg_name (str): user query argument name
    """

    def wrap(f):
        @functools.wraps(f)
        async def wrapped_f(*args):
            arg_name_segments = arg_name.split(".")
            arg_pos = f.__code__.co_varnames.index(arg_name_segments[0])
            if len(arg_name_segments) > 1:
                obj = args[arg_pos]
                arg_name_segments = arg_name_segments[::-1]
                arg_name_segments.pop()
                while len(arg_name_segments) > 1:
                    obj = getattr(obj, arg_name_segments.pop())
                user_query = getattr(obj, arg_name_segments[0])
            else:
                user_query = args[arg_pos]
            is_pass, messages = await guardrails_input_func(user_query)
            if not is_pass:
                ctx_arg_pos = f.__code__.co_varnames.index("ctx")
                request_id = (
                    args[ctx_arg_pos].request_id() if ctx_arg_pos >= 0 else None
                )
                raise GuardrailInputError(
                    messages["summary"],
                    trace={"func_name": f.__name__, "request_id": request_id},
                )
            else:
                return await f(*args)

        return wrapped_f

    return wrap
