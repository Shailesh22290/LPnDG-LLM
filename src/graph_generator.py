# src/graph_generator.py

import google.generativeai as genai
import os
import re
import networkx as nx
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def build_dependency_prompt(skill_list):
    """Builds a prompt to ask Gemini for skill dependencies."""

    formatted_skills = "\n".join([f"{i+1}. {skill}" for i, skill in enumerate(skill_list)])

    prompt = f"""
    You are a task planner for a multi-robot system. Your job is to identify precedence dependencies between a given list of skills. A dependency exists if one skill must be completed before another can begin.

    **Skill List:**
    {formatted_skills}

    **Your Task:**
    1.  **Reasoning:** First, explain your reasoning step-by-step. For each skill, consider if it depends on any other skill in the list. For example, a stacking task `pick_and_place(A, B)` depends on the placement of B.
    2.  **Dependencies:** After your reasoning, provide the dependencies in a clear list format. Use the format "N -> M" to indicate that skill N must be completed before skill M. If there are no dependencies, state "None".

    **Example Output:**

    **Reasoning:**
    - The skill 'pick_and_place(blue block, middle of the table)' has no dependencies.
    - The skill 'pick_and_place(red block, blue block)' requires the 'blue block' to be in its final position. Therefore, skill 2 depends on skill 1.

    **Dependencies:**
    1 -> 2
    """
    return prompt

def parse_dependencies(response_text, skill_list):
    """Parses the LLM's text response to extract dependency edges."""
    edges = []
    # Regex to find lines like "1 -> 2" or "1->2"
    dependency_pattern = re.compile(r'(\d+)\s*->\s*(\d+)')
    
    # We only look for dependencies in the "Dependencies" section
    if "Dependencies:" in response_text:
        dependency_section = response_text.split("Dependencies:")[1]
        matches = dependency_pattern.findall(dependency_section)
        for pred_idx, succ_idx in matches:
            # Convert from 1-based index to 0-based index
            u = skill_list[int(pred_idx) - 1]
            v = skill_list[int(succ_idx) - 1]
            edges.append((u, v))
    return edges

def generate_dependency_graph(skill_list):
    """
    Generates a dependency graph from a skill list using an LLM.
    [cite_start]Includes a cycle check and regeneration loop as described in the paper. [cite: 160]
    """
    if not skill_list:
        return nx.DiGraph()

    prompt = build_dependency_prompt(skill_list)
    
    for attempt in range(3): # Try up to 3 times to get an acyclic graph
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            response = model.generate_content(prompt)
            
            graph = nx.DiGraph()
            graph.add_nodes_from(skill_list)
            
            edges = parse_dependencies(response.text, skill_list)
            graph.add_edges_from(edges)
            
            if nx.is_directed_acyclic_graph(graph):
                print("Successfully generated a Directed Acyclic Graph (DAG).")
                return graph
            else:
                print(f"Warning: Cycle detected in graph on attempt {attempt + 1}. Retrying...")

        except Exception as e:
            print(f"Error generating graph: {e}")
            # On error, return an empty graph or handle as needed
            return nx.DiGraph()
            
    print("Error: Could not generate an acyclic graph after multiple attempts.")
    return nx.DiGraph() # Return an empty or simple sequential graph as a fallback

# --- Example Usage ---
# if __name__ == '__main__':
#     # This list would come from our skill_generator module
#     example_skill_list = [
#         'pick_and_place(blue block, middle of the table)',
#         'pick_and_place(red block, blue block)',
#         'pick_and_place(green block, corner of the table)'
#     ]
#     dependency_graph = generate_dependency_graph(example_skill_list)
    
#     if dependency_graph:
#         print("\n--- Graph Details ---")
#         print("Nodes:", dependency_graph.nodes())
#         print("Edges:", dependency_graph.edges())