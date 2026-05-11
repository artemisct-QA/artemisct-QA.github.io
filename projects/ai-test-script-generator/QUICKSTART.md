# Quick Start Guide - AI Test Script Generator

**Time to first working test: ~5 minutes**

## Step 1: Clone & Setup (1 min)

```bash
# Navigate to project
cd test-script-generator

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies (for Jest version)
npm install
```

## Step 2: Set Your API Key (1 min)

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Anthropic API key
# Open .env and replace: ANTHROPIC_API_KEY=your-api-key-here
nano .env

# OR set it directly in your shell
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxx"
```

## Step 3: Generate Your First Test (2 min)

### Python (pytest) Version:
```bash
python scripts/generate_pytest.py \
  --spec "Test GET /api/vehicle/status endpoint that returns battery percentage and charging state. Should handle 200 OK and 401 Unauthorized responses."
```

### JavaScript (Jest) Version:
```bash
npm run generate:jest -- \
  --spec "Test POST /api/auth/login endpoint with username and password. Returns JWT token on 200 OK, returns error on 401 Unauthorized and 400 Bad Request."
```

## Step 4: Check Your Generated Test

✅ **pytest version** will be saved to: `generated_tests/test_api_YYYYMMDD_HHMMSS.py`

✅ **Jest version** will be saved to: `generated_tests/test.api.YYYYMMDD_HHMMSS.test.js`

Open and review! The generated test should be:
- ✅ Fully functional
- ✅ Well-structured with fixtures/mocks
- ✅ Include multiple test scenarios
- ✅ Have proper assertions

## Example Test Specs to Try

### API Testing Examples:

**Simple GET endpoint:**
```
Test GET /api/users/profile endpoint. Returns user object with id, name, email. 
Handle 200 OK success and 401 Unauthorized when token is missing.
```

**POST with request body:**
```
Test POST /api/orders/create endpoint that accepts {userId, items, totalPrice}. 
Should validate required fields. Return 201 Created with order ID on success, 
400 Bad Request if fields missing, 401 if unauthorized.
```

**Complex endpoint with multiple scenarios:**
```
Test GET /api/charging/status endpoint. Query params: stationId (required), 
format (optional: 'detailed' or 'basic'). Returns charging info. 
Handle: 200 OK, 400 (missing stationId), 401 (unauthorized), 
404 (station not found), 500 (service error).
```

## Tips for Best Results

1. **Be descriptive** — The more detail in your spec, the better the generated tests
   - ✅ Good: "Test GET /api/vehicle/status with battery level, charging state, and location fields"
   - ❌ Poor: "Test vehicle endpoint"

2. **Include error cases** — Mention the error responses your API returns
   - 400 Bad Request, 401 Unauthorized, 404 Not Found, 500 Server Error, etc.

3. **Specify request/response formats** — Include JSON field names
   - Example: "Returns {batteryPercent: number, chargingState: string}"

4. **Mention authentication** — If your endpoint uses API keys, Bearer tokens, etc.
   - Example: "Endpoint requires Bearer token in Authorization header"

## Next Steps (Day 2+)

Once you've got the basic generators working:

1. **Expand the system prompts** in `prompts/` directory for more specific output
2. **Add Appium support** for mobile test generation
3. **Build a simple web UI** (React) to make it easier to use
4. **Create example specs** in `demo/example_specs.json`
5. **Write documentation** for your portfolio

## Troubleshooting

**"ANTHROPIC_API_KEY not found"**
```bash
# Make sure your API key is set
export ANTHROPIC_API_KEY="your-key-here"
# Verify it's set:
echo $ANTHROPIC_API_KEY
```

**"Module not found" errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
npm install
```

**Generated tests look incomplete**
- Your spec might be too vague. Add more details about request/response format
- Try a shorter, more focused spec first

## Support

Check the main README.md for architecture details and long-term project structure.

---

**🎯 Goal:** Get your first generated test working, then expand from there!

**⏱️ Time estimate:** 5 minutes to first working test, 5 hours to MVP, 5 days to full hackathon submission.

Happy hacking! 🚀
