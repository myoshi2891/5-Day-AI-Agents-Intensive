"""Debug helpers for printing tool traces."""

from __future__ import annotations

from typing import Any


def show_python_code_and_result(response: Any) -> None:
    for i in range(len(response)):
        parts = response[i].content.parts
        if (
            parts
            and parts[0]
            and parts[0].function_response
            and parts[0].function_response.response
        ):
            response_code = parts[0].function_response.response
            if "result" in response_code and response_code["result"] != "```":
                if "tool_code" in response_code["result"]:
                    print(
                        "Generated Python Code >> ",
                        response_code["result"].replace("tool_code", ""),
                    )
                else:
                    print("Generated Python Response >> ", response_code["result"])


__all__ = ["show_python_code_and_result"]
