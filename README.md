# NLI BNF Manual Inspection Tool

A manual inspection tool for Natural Language Interface (NLI) that tests the conversion of natural language queries into structured JSON filter objects using Backus-Naur Form (BNF) grammar definitions.

## Overview

This tool tests a mobile app's ability to translate natural language location queries into structured JSON filter objects. The system is designed for a location-based app called "NearMe" where users can ask questions like "find pizza places nearby" and get structured filters for database queries.

The tool uses Google's Gemini AI to translate queries and displays the raw output for manual inspection and evaluation.

## What This Tool Does

### `nli_bnf.py` - Manual Inspection Tool
- Processes natural language queries through Google Gemini API
- Displays raw LLM output for manual evaluation
- Shows what the API actually generates without any post-processing
- Perfect for debugging, prompt engineering, and understanding model behavior
- No automatic validation - pure inspection mode for qualitative analysis
- Follows complete BNF specification with `current` and `saved` structure

## Filter Structure

The system converts natural language to JSON objects following this BNF grammar structure:

### Complete BNF Filter Object
```json
{
  "current": {
    "version": 1,
    "include": {
      "or": { /* filterValues object */ },
      "and": { /* filterValues object */ }
    },
    "exclude": {
      "or": { /* filterValues object */ },
      "and": { /* filterValues object */ }
    }
  },
  "saved": []
}
```

### Filter Types (BNF Specification)

- **lt** (Location Types): `'lt:' '[' <id> { ',' <id> } ']'`
  - Complete mapping of 45+ location types with exact IDs
  - Examples: restaurant(693), cafe(695), museum(715), hospital(718), etc.

- **st** (Subtypes/Properties): `'st:' '[' <id> { ',' <id> } ']'`
  - Food types: Pizza(101), Sushi(102), Italian(103), Vegetarian(104)
  - Properties: Trendy(202), Cheap(207), Free parking(205), Child-friendly(210)

- **pr** (Price Range): `'pr:' '[' <fromPrice> ',' <toPrice> ']'`
  - Requires two numeric values: [from, to]

- **pk** (Parking): `'pk:' '[' <parking> { ',' <parking> } ']'`
  - Values: "parkingSpaces", "parkingSpacesWithCharging"

- **ml** (My Locations): `'ml:' '[' 0 ']'`
  - For saved/favorite places, always contains [0]

### Test Cases Format

The `test.json` file should contain test cases in this format:
```json
[
  {
    "input": "where can I find a pizza restaurant",
    "description": "Simple restaurant search"
  },
  {
    "input": "trendy cafes nearby that are not expensive",
    "description": "Cafe search with inclusion and exclusion criteria"
  },
  {
    "input": "restaurant or cafe with free parking",
    "description": "OR query with parking requirement"
  }
]
```

**Required fields:**
- `input`: The natural language query to test
- `description`: Brief description of what the test case covers (optional)

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
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_google_ai_api_key_here
   ```

4. **Prepare test cases:**
   Create `test.json` with your test cases in the correct format.

## Usage

### Running the Manual Inspection Tool
```bash
python nli_bnf.py
```

This will:
- Load all test cases from `test.json`
- Run each query through the Gemini API
- Display raw LLM output for each test case
- Allow manual evaluation of model performance
- Help with debugging and prompt engineering

### Understanding the Output
The tool displays:
- **Input**: The original natural language query
- **Description**: What the test case is testing
- **Actual LLM**: The raw JSON response from Google Gemini

### Example Output

```
--- Test 1/3 ---
Input:      'where can I find a pizza restaurant'
Description: Simple restaurant search
Actual LLM: {"current": {"version": 1, "include": {"or": {}, "and": {"lt": [693], "st": [101]}}, "exclude": {"or": {}, "and": {}}}, "saved": []}
------------------------------

--- Test 2/3 ---
Input:      'trendy cafes nearby that are not expensive'
Description: Cafe with exclusion criteria
Actual LLM: {"current": {"version": 1, "include": {"or": {}, "and": {"lt": [695], "st": [202]}}, "exclude": {"or": {}, "and": {"st": [208]}}}, "saved": []}
------------------------------
```

## Use Cases

This manual inspection tool is perfect for:

### 🔍 **Prompt Engineering**
- See exactly how the LLM interprets your prompts
- Identify patterns in successful vs unsuccessful responses
- Iterate on prompt design based on actual output
- Test edge cases and complex queries

### 🐛 **Debugging**
- Understand why certain queries might not work as expected
- See raw API responses before any processing
- Identify unexpected model behaviors
- Validate that the BNF structure is followed correctly

### 📊 **Model Evaluation**
- Manually assess the quality of responses
- Compare performance across different query types
- Evaluate consistency of output format
- Test multilingual capabilities (Danish/English queries)

### 🎯 **Development & Testing**
- Validate new test cases before using them elsewhere
- Understand what constitutes good vs poor responses
- Develop intuition for model capabilities and limitations
- Create comprehensive test suites for different scenarios

## Query Examples

| Query Type | Example | Expected Behavior |
|------------|---------|-------------------|
| Simple location | "find restaurants nearby" | Include restaurant location type |
| With properties | "trendy cafes with free wifi" | Include cafe + trendy + free wifi |
| Exclusion | "pizza places that are not fast food" | Include pizza, exclude fast food |
| OR condition | "restaurant or cafe" | Use OR structure for location types |
| Complex | "cheap italian restaurants with parking" | Multiple criteria in AND structure |

## Configuration

### Model Settings
- **Model**: `gemini-1.5-flash-latest`
- **Temperature**: 0.0 (deterministic output)
- **Timeout**: 120 seconds per request

### File Locations
- Test cases: `test.json`
- Environment: `.env`

## BNF Grammar Reference

The complete BNF specification for the filter syntax:

```
<filter>             ::= '{' 'current:' <filterDefinition> ',' 'saved:' <savedUserFilters> '}'
<filterDefinition>   ::= <empty> | '{' <version> ',' 'include:' <filterAndOr> ',' 'exclude:' <filterAndOr> '}'
<empty>              ::= '{}'
<version>            ::= 'version:' <number>
<filterAndOr>        ::= '{' 'or:' <filterValues> ',' 'and:' <filterValues> '}'
<filterValues>       ::= '{' <filterValue> { ',' <filterValue> } '}'
<filterValue>        ::= <locationTypeFilter> | <subTypeFilter> | <priceFilter> | <parkingFilter> | <myLocationsFilter>
<locationTypeFilter> ::= 'lt:' '[' <id> { ',' <id> } ']'
<subTypeFilter>      ::= 'st:' '[' <id> { ',' <id> } ']'
<priceFilter>        ::= 'pr:' '[' <fromPrice> ',' <toPrice> ']'
<parkingFilter>      ::= 'pk:' '[' <parking> { ',' <parking> } ']'
<myLocationsFilter>  ::= 'ml:' '[' 0 ']'
<id>                 ::= <number>
<fromPrice>          ::= <number>
<toPrice>            ::= <number>
<parking>            ::= 'parkingSpaces' | 'parkingSpacesWithCharging'
<savedUserFilters>   ::= '[' { 'name:' <filterName> ',' 'filter:' <filterDefinition> } ']'
```

## Error Handling

The system handles various error conditions:
- **API timeouts**: 120-second timeout with graceful failure
- **Missing API key**: Clear error messages for setup issues
- **Invalid test files**: JSON validation and file existence checks
- **Blocked responses**: Safety filter detection and reporting
- **API errors**: Comprehensive exception handling with stack traces

## Troubleshooting

### Common Issues

**API Key Issues:**
- Verify `.env` file exists with correct `GEMINI_API_KEY`
- Check API key permissions and quotas in Google AI Studio
- Ensure the API key has access to the specified model

**Model Access:**
- Confirm access to `gemini-1.5-flash-latest`
- Try alternative model names if needed
- Check Google AI service availability

**Test File Issues:**
- Validate `test.json` syntax using an online JSON validator
- Ensure all test cases have required `input` field
- Check file encoding is UTF-8 for special characters
- Verify file exists in the same directory as the script

**Unexpected Output:**
- Use this tool to see exactly what the model produces
- Check if queries are too ambiguous or complex
- Consider if the prompt needs adjustment for specific use cases

## Contributing

1. Add test cases to `test.json`
2. Ensure proper JSON formatting
3. Test with various query types and complexity levels
4. Document any patterns or issues you discover

## License

[Add your license information here]

## Contact

[Add your contact information here]