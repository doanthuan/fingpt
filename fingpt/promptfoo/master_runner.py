import asyncio
import json
import os

from pydantic import BaseModel

eval_paths = [
    "promptfoo/financial_report/staging_prompt_eval.yaml",
    "promptfoo/primary_assistant/staging_prompt_eval.yaml",
    "promptfoo/term_deposit/staging_agent_prompt_eval.yaml",
    "promptfoo/transaction/staging_agent_prompt_eval.yaml",
    "promptfoo/transfer/staging_agent_prompt_eval.yaml",
    "promptfoo/term_deposit/staging_router_prompt_eval.yaml",
    "promptfoo/transaction/staging_router_prompt_eval.yaml",
    "promptfoo/transfer/staging_router_prompt_eval.yaml",
]


class EvalOutput(BaseModel):
    eval_id: str
    prompt_name: str
    test_pass_count: int
    test_fail_count: int


def parse_eval_output(output_path: str) -> EvalOutput:
    with open(output_path, "r") as f:
        data = json.load(f)

    return EvalOutput(
        eval_id=data["evalId"],
        prompt_name=data["results"]["prompts"][0]["raw"],
        test_pass_count=data["results"]["prompts"][0]["metrics"]["testPassCount"],
        test_fail_count=data["results"]["prompts"][0]["metrics"]["testFailCount"],
    )


async def run_eval(path: str) -> EvalOutput:
    output_file_path = path.replace(".yaml", ".json")
    process = await asyncio.create_subprocess_exec(
        "promptfoo",
        "eval",
        "-c",
        path,
        "-o",
        output_file_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    print(stdout.decode())
    print(stderr.decode())
    eval_result = parse_eval_output(output_file_path)
    # clear the output file
    os.remove(output_file_path)
    return eval_result


async def main(eval_paths: list[str]):
    tasks = []
    for path in eval_paths:
        tasks.append(run_eval(path))
    return await asyncio.gather(*tasks)


if __name__ == "__main__":
    results: tuple[EvalOutput] = asyncio.run(main(eval_paths))
    all_passed = True
    messages = ""
    for result in results:
        if result.test_fail_count > 0:
            all_passed = False
            messages += f" :warning: {result.prompt_name} FAILED. Test failed count: {result.test_fail_count}\n"
        else:
            messages += f" :white_check_mark: {result.prompt_name} PASSED\n"
    if all_passed:
        messages += " :party_blob: All tests passed! :party_blob:"
    else:
        messages += " :fire: Some tests failed! :fire:"
    print(f"Result: {messages}")
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"messages<<EOF\n{messages}\nEOF\n")
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
        f.write(f"### PromptFoo Eval Summary\n{messages}")

    if not all_passed:
        exit(1)
    else:
        exit(0)
