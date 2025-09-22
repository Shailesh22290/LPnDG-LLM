# src/skill_generator.py

import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from .env file
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- Skill and Prompt Definitions ---
# This part remains the same
OBJECTS = ["red block", "blue block", "green block", "yellow block", "blue bowl"]
LOCATIONS = ["middle of the table", "corner of the table", "red block", "blue block", "green block", "yellow block", "blue bowl"]

def get_skill_set():
    """Generates the predefined list of possible robot skills."""
    skill_set = []
    for obj in OBJECTS:
        for loc in LOCATIONS:
            if obj != loc:
                skill_set.append(f"pick_and_place({obj}, {loc})")
    skill_set.append("transport(table)")
    skill_set.append("done")
    return skill_set

# In src/skill_generator.py

def build_gemini_prompt(instruction, generated_skills, candidate_skills):
    """Builds the prompt for Gemini to choose the best next skill."""
    
    prompt_template = """
    You are a task planner for a multi-robot system. Your job is to decompose a natural language instruction into the most efficient sequence of executable skills.

    **Instruction:**
    "{instruction}"

    **Completed Skills:**
    {skill_history}

    **Analysis:**
    Based on the instruction, determine the final goal for each object. From the list of candidates below, choose the single most direct and logical next skill. Avoid any redundant or unnecessary intermediate steps. For example, to stack A on B, you only need to place B, then place A on B. Do not place A somewhere else first.

    **Candidate Skills:**
    {candidate_list}

    **Your Choice:**
    Return only the full text of the single best skill from the candidate list.
    """
    
    skill_history = "\n".join([f"- {s}" for s in generated_skills]) if generated_skills else "No skills completed yet."
    candidate_list = "\n".join([f"- {s}" for s in candidate_skills])
    
    return prompt_template.format(
        instruction=instruction,
        skill_history=skill_history,
        candidate_list=candidate_list
    )

def choose_best_skill(instruction, generated_skills, skill_set):
    """
    Uses the Gemini model to choose the most likely next skill from the skill set.
    """
    prompt = build_gemini_prompt(instruction, generated_skills, skill_set)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(prompt)
        
        # Clean up the response to get only the skill text
        chosen_skill = response.text.strip()
        
        # Validate that the model returned a valid skill
        if chosen_skill in skill_set:
            return chosen_skill
        else:
            print(f"Warning: Model returned an invalid skill: '{chosen_skill}'")
            # Fallback: We could add more complex error handling here if needed
            return None
            
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def generate_skill_list(instruction, skill_set):
    """
    Generates a list of skills by iteratively asking Gemini to choose the best next skill.
    """
    generated_skills = []
    
    # Create a dynamic list of skills that can still be chosen
    remaining_skills = skill_set.copy()
    
    while True:
        best_skill = choose_best_skill(instruction, generated_skills, remaining_skills)
        
        if best_skill is None or best_skill == "done":
            break
        
        generated_skills.append(best_skill)
        
        # A skill can't be performed twice (in most simple cases)
        if best_skill in remaining_skills:
            remaining_skills.remove(best_skill)
    
    return generated_skills

# --- Example Usage ---
# if __name__ == '__main__':
#     all_skills = get_skill_set()
#     user_instruction = "Put the red block and the blue block in the blue bowl."
#     final_skill_list = generate_skill_list(user_instruction, all_skills)
#     print("--- Generated Skill List ---")
#     for i, skill in enumerate(final_skill_list, 1):
#         print(f"{i}. {skill}")