# NLI BNF Manual Inspection Tool

A manual inspection tool for Natural Language Interface (NLI) that tests the conversion of natural language queries into structured JSON filter objects using Backus-Naur Form (BNF) grammar definitions.

## Overview

This tool tests a mobile app's ability to translate Danish natural language location queries into structured JSON filter objects. The system is designed for a location-based app called "NearMe" where users can ask questions like "find pizza places nearby" and get structured filters for database queries.

## What This Tool Does

### `nli_bnf.py` - Manual Inspection Tool
- Displays raw LLM output for manual evaluation
- Shows what the Google Gemini API actually generates without parsing
- Useful for debugging and prompt engineering
- Helps identify patterns in model behavior
- No automatic validation - pure inspection mode
- Perfect for understanding how the LLM interprets different queries

### 3. `test2.json` - Test Cases
Contains test cases in the following format:
```json
[
  {
    "input": "hvor finder jeg en pizza det skal ikke være fastfood",
    "expected_output": "{ \"version\": 1, \"include\": { \"or\": {}, \"and\": { \"lt\": [1], \"st\": [101] } }, \"exclude\": { \"or\": {}, \"and\": { \"st\": [105] } } }",
    "description": "Pizza restaurant excluding fastfood"
  }
]
```

## Filter Structure

The system converts natural language to JSON objects with this structure:

```json
{
  "version": 1,
  "include": {
    "or": { /* filterValues object */ },
    "and": { /* filterValues object */ }
  },
  "exclude": {
    "or": { /* filterValues object */ },
    "and": { /* filterValues object */ }
  }
}
```

### Filter Types

- **lt** (Location Types): Restaurant(1), Cafe(2), Gallery(3), Park(4), etc.
- **st** (Subtypes/Properties): Pizza(101), Sushi(102), Trendy(202), Cheap(207), etc.
- **pk** (Parking): "parkingSpaces", "parkingSpacesWithCharging"
- **ml** (My Locations): Saved places [0]
- **pr** (Price Range): [from, to] numeric values

## Installation

### Prerequisites
- Python 3.7+
- Google AI API Key (Gemini)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd nli-bnf-testing
   ```

2. **Install dependencies:**
   ```bash
   python3 -m venv venv
   . venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_gemini_ai_api_key_here
   ```

4. **Prepare test cases:**
   Ensure `test.json` exists with your test cases in the correct format.

### Optional Dependencies

This tool doesn't require additional dependencies beyond what's in `requirements.txt`, but you may want to install JSON formatting tools for better readability:
```bash
pip install jq  # For command-line JSON formatting
```

## Usage

### Running the Manual Inspection Tool
```bash
python nli_bnf.py
```

This will:
- Load all test cases from `test.json`
- Run each query through the Gemini API
- Display raw LLM output for each test case
- Show expected vs actual results side by side
- Allow manual evaluation of model performance
- Help with debugging and prompt engineering

### Understanding the Output
The tool displays:
- **Input**: The original Danish query
- **Description**: What the test case is testing
- **Expected**: The expected JSON output (for reference)
- **Actual LLM**: The raw text response from Google Gemini

## Configuration

### Model Settings
- **Model**: `gemini-1.5-flash-latest`
- **Temperature**: 0.0 (deterministic output)
- **Timeout**: 120 seconds per request

## Use Cases

This manual inspection tool is perfect for:

### 🔍 **Prompt Engineering**
- See exactly how the LLM interprets your prompts
- Identify patterns in successful vs unsuccessful responses
- Iterate on prompt design based on actual output

### 🐛 **Debugging**
- Understand why certain queries fail
- See raw API responses before any processing
- Identify edge cases and unexpected behaviors

### 📊 **Model Evaluation**
- Manually assess the quality of responses
- Compare different model versions or configurations
- Evaluate performance on specific types of queries

### 🎯 **Test Case Development**
- Validate new test cases before adding them
- Understand what the "expected output" should be
- Refine test cases based on actual model behavior

## Example Queries

| Danish Query | English Translation | Expected Filter Type |
|-------------|-------------------|----------------|
| "hvor finder jeg en pizza det skal ikke være fastfood" | "where do I find pizza that should not be fastfood" | Include: Restaurant + Pizza, Exclude: Fastfood |
| "Restaurant eller cafe?" | "Restaurant or cafe?" | Include: Restaurant OR Cafe |
| "Er der nogle nye in steder (cafeer) i nærheden" | "Are there any trendy places (cafes) nearby" | Include: Cafe + Trendy |

## Example Output

When you run the tool, you'll see output like this:

```
--- Test 1/10 ---
Input:      'hvor finder jeg en pizza det skal ikke være fastfood'
Description: Pizza restaurant excluding fastfood
Expected:   { "version": 1, "include": { "or": {}, "and": { "lt": [1], "st": [101] } }, "exclude": { "or": {}, "and": { "st": [105] } } }
Actual LLM: { "version": 1, "include": { "or": {}, "and": { "lt": [1], "st": [101] } }, "exclude": { "or": {}, "and": { "st": [105] } } }
------------------------------
```

## Error Handling

The system handles various error conditions:
- **API timeouts**: 120-second timeout with graceful failure
- **Invalid JSON**: Error reporting with original text
- **Blocked responses**: Safety filter detection
- **Missing test cases**: File validation before execution
- **Invalid API keys**: Clear error messages

## Contributing

1. Add test cases to `test.json`
2. Ensure proper JSON formatting
3. Test with both automated and manual tools
4. Update documentation as needed

## Troubleshooting

### Common Issues

**API Key Issues:**
- Verify `.env` file exists with correct `GEMINI_API_KEY`
- Check API key permissions and quotas

**Model Access:**
- Ensure you have access to `gemini-1.5-flash-latest`
- Try alternative model names if needed

**JSON Parsing Errors:**
- Use manual inspection tool to see raw output
- Check for formatting issues in responses

**Missing Test File Issues:**
- Validate `test.json` syntax using an online JSON validator
- Ensure all required fields (`input`, `expected_output`, `description`) are present
- Check file encoding is UTF-8 for Danish characters

**Unexpected Output:**
- Use this tool to see exactly what the model produces
- Compare with expected output to identify discrepancies
- Consider if the prompt needs adjustment

## License

[Add your license information here]

## Contact

[Add your contact information here]