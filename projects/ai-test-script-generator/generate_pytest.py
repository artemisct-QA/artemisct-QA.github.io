#!/usr/bin/env python3
"""
AI Test Script Generator - pytest Version
Generates pytest test cases from API specifications using Claude API
"""

import os
import sys
import argparse
import json
from datetime import datetime
import anthropic


def load_system_prompt():
    """Load the pytest generation system prompt"""
    return """You are an expert SDET (Software Development Engineer in Test) who writes high-quality pytest test scripts.

Your task: Given an API specification or test requirement, generate complete, production-ready pytest test code.

Guidelines:
1. Always use pytest fixtures and mocking (unittest.mock)
2. Include multiple test scenarios: happy path, error cases, edge cases
3. Use descriptive test names that clearly state what is being tested
4. Include proper assertions with meaningful error messages
5. Add docstrings explaining each test
6. Use parametrize for multiple similar test cases
7. Include setup/teardown if needed
8. Handle authentication (Bearer tokens, API keys, etc.)
9. Generate realistic test data
10. Never use real external API calls - always mock

Output format:
- Only provide Python/pytest code
- Include imports at the top
- Use markdown code blocks with ```python at the start
- Add comments explaining complex logic
- Ensure code is runnable without additional setup

Remember: The goal is to help an SDET write tests faster by generating the boilerplate and structure."""


def generate_pytest_script(api_spec: str, model: str = "claude-opus-4-6") -> str:
    """
    Generate a pytest script from an API specification
    
    Args:
        api_spec: Description of the API or test requirement
        model: Claude model to use
        
    Returns:
        Generated pytest script as a string
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    system_prompt = load_system_prompt()
    
    user_message = f"""Generate a complete pytest test script for the following API specification:

{api_spec}

Provide a production-ready pytest test class with multiple test methods covering all scenarios mentioned."""
    
    print(f"🤖 Generating pytest script for:\n{api_spec}\n")
    print("⏳ Calling Claude API...\n")
    
    message = client.messages.create(
        model=model,
        max_tokens=2000,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    response_text = message.content[0].text
    return response_text


def save_generated_test(script: str, output_dir: str = "generated_tests") -> str:
    """
    Save generated test script to a file
    
    Args:
        script: The generated test script
        output_dir: Directory to save to
        
    Returns:
        Path to saved file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/test_api_{timestamp}.py"
    
    with open(filename, "w") as f:
        f.write(script)
    
    print(f"✅ Test script saved to: {filename}")
    return filename


def main():
    parser = argparse.ArgumentParser(
        description="AI Test Script Generator - pytest version"
    )
    parser.add_argument(
        "--spec",
        type=str,
        required=True,
        help="API specification or test requirement description"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-opus-4-6",
        help="Claude model to use (default: claude-opus-4-6)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="generated_tests",
        help="Output directory for generated tests"
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print to stdout instead of saving to file"
    )
    
    args = parser.parse_args()
    
    # Validate API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
    
    try:
        # Generate the pytest script
        generated_script = generate_pytest_script(args.spec, args.model)
        
        # Output the result
        if args.print_only:
            print("=" * 80)
            print("GENERATED PYTEST SCRIPT:")
            print("=" * 80)
            print(generated_script)
        else:
            save_generated_test(generated_script, args.output)
            print("\n" + "=" * 80)
            print("PREVIEW OF GENERATED SCRIPT:")
            print("=" * 80)
            # Print first 50 lines as preview
            lines = generated_script.split("\n")
            print("\n".join(lines[:50]))
            if len(lines) > 50:
                print(f"\n... (showing first 50 lines of {len(lines)} total)")
        
        print("\n✨ Generation complete!")
        
    except anthropic.APIError as e:
        print(f"❌ API Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
