import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import traceback
import sys

# --- Configuration ---
load_dotenv()
API_KEY = os.getenv('GEMINI_API_KEY')
MODEL_NAME = 'gemini-1.5-flash-latest'
TEST_CASES_FILE = 'test.json'

# --- API Setup ---
model = None
try:
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env file.")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
    print(f"Successfully configured Gemini model: {MODEL_NAME}")

except (ValueError, ConnectionError) as e:
    print(f"Error during API setup: {e}")
    model = None
except Exception as e:
    print(f"An unexpected error occurred during API setup: {e}")
    traceback.print_exc()
    model = None


def get_instruction_prompt(user_query):
    """
    Creates the prompt for the LLM to translate user queries to JSON filter objects
    following the BNF specification.
    """
    
    prompt = f"""You are an assistant for a mobile app called "NearMe". Your task is to translate the user's natural language query about nearby places into a structured JSON object that matches the app's internal filter format defined by a BNF notation.

The JSON object must have the following structure (representing the complete BNF structure):
{{
  "current": {{
    "version": 1,
    "include": {{
      "or": {{}},
      "and": {{}}
    }},
    "exclude": {{
      "or": {{}},
      "and": {{}}
    }}
  }},
  "saved": []
}}

Where the "and" and "or" objects can contain filter values with keys like "lt", "st", "pr", "pk", "ml" and corresponding arrays of IDs or strings.

**Mapping of natural language to filter types and IDs:**

**Location Types ("lt"):** Use EXACTLY these IDs for location types:
- takeaway: 1
- packetPickup: 6
- office: 640
- shop: 688
- mall: 689
- market: 690
- supermarket: 691
- restaurant: 693
- fastFood: 694
- cafe: 695
- bar: 696
- pub: 697
- club: 698
- hotel: 699
- motel: 700
- hostel: 701
- transportation: 702
- airport: 704
- port: 705
- chargeStation: 708
- gasStation: 709
- parking: 710
- park: 711
- zoo: 712
- botanicalGarden: 713
- cinema: 714
- museum: 715
- theatre: 716
- concertHall: 717
- hospital: 718
- pharmacy: 719
- doctor: 720
- dentist: 721
- other: 722
- beautySalon: 724
- sport: 726
- swimmingPool: 727
- casino: 732
- canoeRental: 740
- bridge: 743
- conference: 745
- recycling: 747
- grocery: 761
- bowling: 762
- fitness: 763
- tennis: 764
- golf: 765
- diskGolf: 766
- ice: 767
- carRental: 768
- taxi: 769
- bus: 770
- baker: 773
- clothing: 775
- craftsman: 776
- painter: 777
- lumber: 778
- hairdresser: 779

**Properties/Subtypes ("st"):** Use for cuisine types and descriptive properties:
- Pizza: 101
- Sushi: 102
- Italian: 103
- Vegetarian: 104
- Lunch place: 106
- Good: 201
- Trendy: 202
- Open late: 203
- Free entrance: 204
- Free parking: 205
- With playground: 206
- Cheap: 207
- Expensive: 208
- Clean: 209
- Child-friendly: 210
- With view: 211
- Crowded: 212
- Open Sunday: 213
- Free wifi: 214
- Beautiful garden: 215

**Price Range ("pr"):** Requires two numeric values [from, to]. Example: [100, 500]

**Parking ("pk"):** Use specific strings:
- With parking: "parkingSpaces"
- With charging stations: "parkingSpacesWithCharging"

**My Locations ("ml"):** For saved places, always use: [0]

**Translation Rules:**

1. Analyze the user's query to identify Location Types (lt), Properties/Subtypes (st), Parking (pk), My Locations (ml), Price Range (pr).
2. Ignore distance-related words ("nearest", "nearby", "how far") - these are handled by the app.
3. Ignore question words ("where", "is there", "are there") - focus on places and properties.
4. **Inclusion vs. Exclusion:**
   - Criteria to be included go in the "include" section
   - Criteria to be excluded (marked with "not" or negation) go in the "exclude" section
5. **AND vs. OR:**
   - Criteria connected with "and" go in the "and" objects
   - Criteria connected with "or" go in the "or" objects
   - If the user explicitly uses "or" between different places or properties, use the "or" section
   - Otherwise (for implicit "and" or single criteria), use the "and" section
6. **Empty sections:** If there is nothing to include/exclude, omit the filter type entirely. Empty objects are {{}}.
7. **Show all:** If the user asks for "everything" or "just show me", return empty filters.
8. **Unclear/Irrelevant Query:** If the query is irrelevant for finding places, return exactly "UNKNOWN".

**IMPORTANT:** Your output should ONLY be the generated JSON object (as a string) or the text "UNKNOWN". No other text, explanation or formatting. The JSON object must be valid and follow the BNF specification with "current" and "saved" wrapper.

**Examples:**

User: where can I find a pizza restaurant that should not be fast food
Output: {{"current": {{"version": 1, "include": {{"or": {{}}, "and": {{"lt": [693], "st": [101]}}}}, "exclude": {{"or": {{}}, "and": {{"lt": [694]}}}}}}, "saved": []}}

User: Are there any trendy cafes nearby
Output: {{"current": {{"version": 1, "include": {{"or": {{}}, "and": {{"lt": [695], "st": [202]}}}}, "exclude": {{"or": {{}}, "and": {{}}}}}}, "saved": []}}

User: How far is it to the nearest museum
Output: {{"current": {{"version": 1, "include": {{"or": {{}}, "and": {{"lt": [715]}}}}, "exclude": {{"or": {{}}, "and": {{}}}}}}, "saved": []}}

User: Restaurant or cafe?
Output: {{"current": {{"version": 1, "include": {{"or": {{"lt": [693, 695]}}, "and": {{}}}}, "exclude": {{"or": {{}}, "and": {{}}}}}}, "saved": []}}

User: Place with free parking or free entrance?
Output: {{"current": {{"version": 1, "include": {{"or": {{"st": [205, 204]}}, "and": {{}}}}, "exclude": {{"or": {{}}, "and": {{}}}}}}, "saved": []}}

User: Just show me everything nearby
Output: {{"current": {{"version": 1, "include": {{"or": {{}}, "and": {{}}}}, "exclude": {{"or": {{}}, "and": {{}}}}}}, "saved": []}}

User: What time is it?
Output: UNKNOWN

**Translate the following query to a JSON filter object for the NearMe app:**

User: {user_query}
Output:"""
    
    return prompt


def run_manual_test():
    if model is None:
        print("\nCannot run tests because the API model could not be configured.")
        print("Please fix the API setup errors and try again.")
        return

    try:
        with open(TEST_CASES_FILE, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        print(f"\nError: Test cases file not found at {TEST_CASES_FILE}")
        return
    except json.JSONDecodeError:
        print(f"\nError: Could not parse JSON from {TEST_CASES_FILE}. Check for syntax errors.")
        return
    except Exception as e:
        print(f"\nAn error occurred while loading test cases: {e}")
        traceback.print_exc()
        return

    total_tests = len(test_cases)

    print(f"\nRunning manual NLI tests using model: {MODEL_NAME}")
    print(f"Following BNF specification with 'current' and 'saved' structure\n")
    print(f"Loading {total_tests} test cases from '{TEST_CASES_FILE}'.\n")
    print("--- Output Format ---")
    print("Input:      'User Query'")
    print("Actual LLM: Raw output received from LLM API")
    print("---------------------\n")

    for i, test_case in enumerate(test_cases):
        input_query = test_case.get("input")
        description = test_case.get("description", "No description")

        if input_query is None:
            print(f"--- Skipping test case {i+1}/{total_tests} ---")
            print("Reason: Missing 'input' in test case definition.")
            print("-" * 30)
            continue

        print(f"--- Test {i+1}/{total_tests} ---")
        print(f"Input:      '{input_query}'")
        print(f"Description: {description}")

        try:
            full_prompt = get_instruction_prompt(input_query)

            response = model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(temperature=0.0),
                request_options={'timeout': 120}
            )

            generated_text = "NO CANDIDATES"
            if response.candidates:
                if hasattr(response.candidates[0], 'content') and hasattr(response.candidates[0].content, 'parts'):
                    generated_text = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
                else:
                    try:
                        generated_text = response.text
                    except Exception:
                        generated_text = "Could not get text from Gemini response (unexpected structure)."
            elif response.prompt_feedback and response.prompt_feedback.block_reason:
                generated_text = f"PROMPT BLOCKED: {response.prompt_feedback.block_reason}"

            print(f"Actual LLM: {generated_text}")

        except Exception as e:
            print(f"Actual LLM: EXCEPTION: {type(e).__name__}")
            print(f"Error: {e}")
            traceback.print_exc()

        print("-" * 30)

    print("\n--- Manual Test Run Complete ---")


if __name__ == "__main__":
    if not os.path.exists(TEST_CASES_FILE):
        print(f"\nError: Test cases file '{TEST_CASES_FILE}' not found.")
        print("Please create this file with your JSON test cases.")
        sys.exit(1)

    run_manual_test()