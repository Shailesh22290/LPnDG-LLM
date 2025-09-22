# main.py

from src.skill_generator import generate_skill_list, get_skill_set
from src.graph_generator import generate_dependency_graph
from src.task_allocator import get_executable_skills, solve_task_allocation
import networkx as nx

def main_planner(instruction, robots):
    """
    Runs the full LiP-LLM planning pipeline.
    """
    print(f"## 1. Processing Instruction: '{instruction}'")
    
    # --- Step 1: Skill List Generation ---
    skill_set = get_skill_set()
    skill_list = generate_skill_list(instruction, skill_set)
    if not skill_list:
        print("Could not generate a skill list. Aborting.")
        return
    print("\n--- Generated Skill List ---")
    for i, skill in enumerate(skill_list, 1):
        print(f"{i}. {skill}")

    # --- Step 2: Dependency Graph Generation ---
    print("\n## 2. Generating Dependency Graph")
    graph = generate_dependency_graph(skill_list)
    if not graph.nodes():
        print("Could not generate a dependency graph. Aborting.")
        return
    print("Dependencies (Edges):", graph.edges())
    
    # --- Step 3: Task Allocation and Execution Simulation ---
    print("\n## 3. Simulating Task Allocation and Execution")
    step_counter = 0
    while graph.number_of_nodes() > 0:
        step_counter += 1
        print(f"\n--- Step {step_counter} ---")
        
        # Get skills that can be executed now
        executable_skills = get_executable_skills(graph)
        print("Executable Skills:", executable_skills)
        
        if not executable_skills:
            print("Error: No executable skills found, but graph is not empty. Possible cycle or logic error.")
            break
            
        # Allocate tasks to robots
        assignments = solve_task_allocation(robots, executable_skills)
        print("Assignments:", assignments)
        
        # Simulate execution and update graph
        completed_tasks = list(assignments.values())
        if not completed_tasks:
            print("No tasks assigned in this step. Waiting...")
            continue
            
        graph.remove_nodes_from(completed_tasks)
        print("Completed Tasks:", completed_tasks)
        print("Remaining Tasks:", len(graph.nodes()))
        
    print("\n## 4. Planning Complete!")


if __name__ == '__main__':
    # Define our simulated robots
    ROBOTS = [
        {'name': 'Arm_Robot_1', 'type': 'arm_robot'},
        {'name': 'Arm_Robot_2', 'type': 'arm_robot'},
        {'name': 'Mobile_Robot_1', 'type': 'mobile_robot'}
    ]
    
    # The user's instruction
    user_instruction = "Stack the red block on the blue block, and put the green block in the corner."
    
    # Run the planner
    main_planner(user_instruction, ROBOTS)