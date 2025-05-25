import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import traceback
import sys

# --- Konfiguration ---
load_dotenv()
API_KEY = os.getenv('GEMINI_API_KEY')
MODEL_NAME = 'gemini-1.5-flash-latest' # Sørg for dette navn er korrekt
TEST_CASES_FILE = 'test2.json' # Fil med testcases i JSON format

# --- API Opsætning ---
model = None # Initialiser model til None
try:
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
    # Valider modellen (kan udkommenteres for hurtigere start, men anbefales)
    # try:
    #     # Prøv et dummy kald for at validere nøgle og model
    #     model.generate_content("ping", request_options={'timeout': 10})
    #     print(f"Successfully configured and validated Gemini model: {MODEL_NAME}")
    # except Exception as e:
    #      raise ConnectionError(f"Failed to validate model {MODEL_NAME}. Check API key, model name, or connectivity. Error: {e}")

    print(f"Successfully configured Gemini model: {MODEL_NAME}")

except (ValueError, ConnectionError) as e:
    print(f"Error during API setup: {e}")
    # model forbliver None, scriptet vil tjekke for dette senere
    # sys.exit(1) # Afslut ikke nødvendigvis her, hvis man vil se load fejl
except Exception as e:
    print(f"An unexpected error occurred during API setup: {e}")
    traceback.print_exc()
    model = None
    # sys.exit(1)


# --- Prompt Funktion (IDENTISK med den i din app!) ---
def get_instruction_prompt(user_query):
    """
    Opretter prompten til LLM'en, der instruerer den i at oversætte
    brugerens forespørgsel til et JSON-filter objekt.
    """
    # ESCAPE curly braces {{ og }}
    base_prompt_template = """
Du er en assistent til en mobil app kaldet "NearMe". Din opgave er at oversætte brugerens naturlige sprog forespørgsel om steder i nærheden til et struktureret JSON-objekt, der passer til appens interne filter-format defineret af en BNF notation.

JSON-objektet skal have følgende struktur (der repræsenterer <filterDefinition> fra BNF'en med version 1):
{{
  "version": 1,
  "include": {{
    "or": {{ /* <filterValues> object */ }},
    "and": {{ /* <filterValues> object */ }}
  }},
  "exclude": {{
    "or": {{ /* <filterValues> object */ }},
    "and": {{ /* <filterValues> object */ }}
  }}
}}
Hvor <filterValues> er et objekt med nøgler som "lt", "st", "pr", "pk", "ml" og tilhørende arrays af ID'er eller strenge.

**Mapping af naturligt sprog til filtertyper og ID'er:**

*   **Stedstyper ("lt"):** Brug til hovedkategorier af steder. Eksempler:
    *   Restaurant: 1
    *   Cafe: 2
    *   Galleri: 3
    *   Park: 4
    *   Seværdighed: 5
    *   Svømmehal: 6
    *   Museum: 7
    *   Havn: 8
    *   Strand: 9
    *   Butik: 10
    *   Apotek: 11
    *   Bibliotek: 12
    *   Kirke: 13
    *   Hospital: 14
    *   Skole: 15
*   **Egenskaber/Subtyper ("st"):** Brug til køkkentyper og beskrivende egenskaber. Eksempler:
    *   Pizza: 101
    *   Sushi: 102
    *   Italiensk: 103
    *   Vegetarisk: 104
    *   Fastfood: 105
    *   Frokoststed: 106
    *   Tøj (Butik subtype): 107
    *   God: 201
    *   Trendy ("nye in steder", "hippe"): 202
    *   Åbent sent: 203
    *   Gratis adgang: 204
    *   Gratis parkering: 205
    *   Med legeplads: 206
    *   Billig: 207
    *   Dyrt: 208
    *   Ren: 209
    *   Børnevenlig: 210
    *   Med udsigt: 211
    *   Overfyldt: 212
    *   Åben Søndag: 213
    *   Gratis wifi: 214
    *   Flot have: 215
*   **Prisinterval ("pr"):** Bruges sjældent i disse eksempler. Kræver to numeriske værdier [fra, til]. Ignorer for "billig" eller "dyr" - brug "st" ID'er for disse.
*   **Parkering ("pk"):** Bruges med specifikke strenge i et array. Eksempler:
    *   Med parkering: "parkingSpaces"
    *   Med ladestander: "parkingSpacesWithCharging"
*   **Mine Steder ("ml"):** Bruges for gemte steder. Eksempel:
    *   Mine gemte steder: [0]

**Regler for oversættelse:**

1.  Analyser brugerens forespørgsel for at identificere Stedstyper (`lt`), Egenskaber/Subtyper (`st`), Parkering (`pk`), Mine Steder (`ml`).
2.  Ignorer ord relateret til afstand ("nærmeste", "i nærheden", "hvor langt") - disse håndteres af appen, ikke filteret.
3.  Ignorer spørgeord ("hvor", "er der", "findes der") - fokuser på steder og egenskaber.
4.  **Inklusion vs. Eksklusion:**
    *   Kriterier der skal inkluderes placeres i "include" sektionen.
    *   Kriterier der skal ekskluderes (markeret med "ikke" / `NOT`) placeres i "exclude" sektionen.
5.  **AND vs. OR:**
    *   Kriterier forbundet med "og" (`AND`) placeres i "and" objekterne inden for "include" eller "exclude". Hvis der er flere værdier af samme type (f.eks. flere `st` ID'er) i "and" sektionen, placeres de i *samme* array for den filtertype: `"st": [id1, id2]`.
    *   Kriterier forbundet med "eller" (`OR`) placeres i "or" objekterne inden for "include" eller "exclude". Flere værdier af samme type i "or" sektionen placeres i *samme* array: `"lt": [id1, id2]`.
    *   **VIGTIGT:** Hvis brugeren *explicit* bruger "eller" mellem *forskellige* steder eller egenskaber, brug da "or" sektionen for de pågældende filtertyper. Ellers (for implicit "og" eller enkeltkriterier), brug "and" sektionen.
6.  **Tomme sektioner:** Hvis der ikke er noget at inkludere/ekskludere af en bestemt type (or/and) eller en filtertype (lt, st, etc.) er relevant, skal objektet/filtertypen udelades helt fra filterValues objektet. Et tomt <filterValues> objekt er `{{}}`.
7.  **"Vis alt" / Wildcard:** Hvis brugeren spørger efter "alt" eller "bare vis mig", returner en tom filterdefinition: {{ "version": 1, "include": {{ "or": {{}}, "and": {{}} }}, "exclude": {{ "or": {{}}, "and": {{}} }} }}.
8.  **Uklar/Irrelevant Forespørgsel:** Hvis forespørgslen er irrelevant for at finde steder, returner præcis teksten **"UNKNOWN"**.

**VIGTIGT:** Dit output skal KUN være det genererede JSON-objekt (som en streng) eller teksten "UNKNOWN". Ingen anden tekst, forklaring eller formatering. JSON-objektet skal være gyldigt.

---
**Eksempler (Few-shot learning):**

*   Bruger: hvor finder jeg en pizza det skal ikke være fastfood.
    Output: {{ "version": 1, "include": {{ "or": {{}}, "and": {{ "lt": [1], "st": [101] }} }}, "exclude": {{ "or": {{}}, "and": {{ "st": [105] }} }} }}

*   Bruger: Er der nogle nye in steder (cafeer) i nærheden
    Output: {{ "version": 1, "include": {{ "or": {{}}, "and": {{ "lt": [2], "st": [202] }} }}, "exclude": {{ "or": {{}}, "and": {{}} }} }}

*   Bruger: Hvor langt er der til det nærmeste galleri
    Output: {{ "version": 1, "include": {{ "or": {{}}, "and": {{ "lt": [3] }} }}, "exclude": {{ "or": {{}}, "and": {{}} }} }}

*   Bruger: Restaurant eller cafe?
    Output: {{ "version": 1, "include": {{ "or": {{ "lt": [1, 2] }}, "and": {{}} }}, "exclude": {{ "or": {{}}, "and": {{}} }} }}

*   Bruger: Sted med gratis parkering eller gratis adgang?
    Output: {{ "version": 1, "include": {{ "or": {{ "st": [205, 204] }}, "and": {{}} }}, "exclude": {{ "or": {{}}, "and": {{}} }} }}

*   Bruger: Bare vis meg alt i nærheten
    Output: {{ "version": 1, "include": {{ "or": {{}}, "and": {{}} }}, "exclude": {{ "or": {{}}, "and": {{}} }} }}

*   Bruger: Hva er klokken?
    Output: UNKNOWN

---
**Oversæt den følgende forespørgsel til et JSON filter objekt for NearMe appen:**

Bruger: [Sæt brugerens forespørgsel her]
Output:
"""
    # Format the template string with the actual user_query
    return base_prompt_template.replace("[Sæt brugerens forespørgsel her]", user_query)


# --- Main Test Logic (Simplified) ---
def run_manual_test():
    if model is None:
        print("\nCannot run tests because the API model could not be configured.")
        print("Please fix the API setup errors and try again.")
        return

    try:
        # Load test cases from JSON file
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

    print(f"\nRunning manual NLI tests using model: {MODEL_NAME}\n")
    print(f"Loading {total_tests} test cases from '{TEST_CASES_FILE}'.\n")
    print("--- Output Format ---")
    print("Input:      'User Query'")
    print("Expected:   Expected JSON (for reference)")
    print("Actual LLM: Raw output received from LLM API")
    print("---------------------\n")


    for i, test_case in enumerate(test_cases):
        input_query = test_case.get("input")
        expected_output_raw = test_case.get("expected_output") # Raw string from JSON file
        description = test_case.get("description", "No description")

        if input_query is None or expected_output_raw is None:
            print(f"--- Skipping test case {i+1}/{total_tests} ---")
            print("Reason: Missing 'input' or 'expected_output' in test case definition.")
            print("-" * 30)
            continue

        print(f"--- Test {i+1}/{total_tests} ---")
        print(f"Input:      '{input_query}'")
        print(f"Description:{description}")
        # Print expected output string for reference
        print(f"Expected:   {expected_output_raw}")

        try:
            full_prompt = get_instruction_prompt(input_query)

            # Call LLM API
            response = model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(temperature=0.0),
                request_options={'timeout': 120} # 2 minute timeout
            )

            # Get the raw text output from the response
            generated_text = "NO CANDIDATES" # Default if no candidates
            if response.candidates:
                 # Try to get text from the first candidate's parts
                 if hasattr(response.candidates[0], 'content') and hasattr(response.candidates[0].content, 'parts'):
                     generated_text = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
                 else:
                      # Fallback to .text if structure is unexpected
                      try:
                          generated_text = response.text
                      except Exception:
                           generated_text = "Could not get text from Gemini response (unexpected structure)."

            elif response.prompt_feedback and response.prompt_feedback.block_reason:
                 generated_text = f"PROMPT BLOCKED: {response.prompt_feedback.block_reason}"
            # else: generated_text remains "NO CANDIDATES"


            print(f"Actual LLM: {generated_text}") # Print the raw text output

        except google.api_core.exceptions.DeadlineExceeded:
            print("Actual LLM: API Timeout")
            print("Error: API call timed out after 120 seconds.")
        except Exception as e:
            print(f"Actual LLM: EXCEPTION: {type(e).__name__}")
            print(f"Error: {e}")
            traceback.print_exc()

        print("-" * 30) # separator

    print("\n--- Manual Test Run Complete ---")


if __name__ == "__main__":
    # Check if the test cases file exists before starting
    if not os.path.exists(TEST_CASES_FILE):
         print(f"\nError: Test cases file '{TEST_CASES_FILE}' not found.")
         print("Please create this file with your JSON test cases.")
         sys.exit(1)

    run_manual_test()