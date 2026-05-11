#!/usr/bin/env node
import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";
import path from "path";
function loadSystemPrompt() {
  return `You are an expert SDET (Software Development Engineer in Test) who writes high-quality Jest test scripts.

Your task: Given an API specification or test requirement, generate complete, production-ready Jest test code.

Guidelines:
1. Always use Jest mocking (jest.mock or jest.spyOn)
2. Include multiple test scenarios: happy path, error cases, edge cases
3. Use descriptive test names that clearly state what is being tested
4. Include proper assertions with meaningful error messages
5. Add comments explaining complex logic
6. Use describe blocks to organize related tests
7. Use beforeEach/afterEach for setup/teardown
8. Handle authentication (Bearer tokens, API keys, etc.)
9. Generate realistic test data
10. Never use real external API calls - always mock

Output format:
- Only provide JavaScript/Jest code
- Include all necessary imports at the top
- Use markdown code blocks with \`\`\`javascript at the start
- Add comments explaining setup and complex logic
- Ensure code is runnable with 'jest' command

Remember: The goal is to help an SDET write tests faster by generating the boilerplate and structure.`;
}

async function generateJestScript(apiSpec, model = "claude-opus-4-6") {
  const client = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY,
  });

  const systemPrompt = loadSystemPrompt();
  const userMessage = `Generate a complete Jest test script for the following API specification:

${apiSpec}

Provide a production-ready Jest test suite with multiple test cases covering all scenarios mentioned.`;

  console.log(`🤖 Generating Jest script for:\n${apiSpec}\n`);
  console.log("⏳ Calling Claude API...\n");

  const message = await client.messages.create({
    model: model,
    max_tokens: 2000,
    system: systemPrompt,
    messages: [
      {
        role: "user",
        content: userMessage,
      },
    ],
  });

  return message.content[0].text;
}

function saveGeneratedTest(script, outputDir = "generated_tests") {
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const timestamp = new Date()
    .toISOString()
    .replace(/[-:]/g, "")
    .replace("T", "_")
    .slice(0, 15);
  const filename = path.join(outputDir, `test.api.${timestamp}.test.js`);

  fs.writeFileSync(filename, script);

  console.log(`✅ Test script saved to: ${filename}`);
  return filename;
}

async function main() {
  const args = process.argv.slice(2);

  let spec = null;
  let model = "claude-opus-4-6";
  let output = "generated_tests";
  let printOnly = false;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--spec" && i + 1 < args.length) {
      spec = args[i + 1];
      i++;
    } else if (args[i] === "--model" && i + 1 < args.length) {
      model = args[i + 1];
      i++;
    } else if (args[i] === "--output" && i + 1 < args.length) {
      output = args[i + 1];
      i++;
    } else if (args[i] === "--print-only") {
      printOnly = true;
    }
  }

  if (!spec) {
    console.error(
      "❌ Error: --spec argument is required\n" +
        "Usage: node generate_jest.js --spec \"Your API specification here\""
    );
    process.exit(1);
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    console.error(
      "❌ Error: ANTHROPIC_API_KEY environment variable not set"
    );
    process.exit(1);
  }

  try {
    const generatedScript = await generateJestScript(spec, model);

    if (printOnly) {
      console.log("=".repeat(80));
      console.log("GENERATED JEST SCRIPT:");
      console.log("=".repeat(80));
      console.log(generatedScript);
    } else {
      saveGeneratedTest(generatedScript, output);
      console.log("\n" + "=".repeat(80));
      console.log("PREVIEW OF GENERATED SCRIPT:");
      console.log("=".repeat(80));

      const lines = generatedScript.split("\n");
      console.log(lines.slice(0, 50).join("\n"));

      if (lines.length > 50) {
        console.log(`\n... (showing first 50 lines of ${lines.length} total)`);
      }
    }

    console.log("\n✨ Generation complete!");
  } catch (error) {
    if (error.status === 401) {
      console.error("❌ API Error: Invalid or missing API key");
    } else if (error.status === 429) {
      console.error("❌ API Error: Rate limit exceeded");
    } else {
      console.error(`❌ Error: ${error.message}`);
    }
    process.exit(1);
  }
}

main();
