# src/task_allocator.py

import numpy as np
import networkx as nx
from scipy.optimize import linprog

def get_executable_skills(graph):
    """
    Finds all nodes in the graph with an in-degree of 0 (no dependencies).
    These are the skills that can be executed in the current step.
    """
    return [node for node, in_degree in graph.in_degree() if in_degree == 0]

def calculate_weights(robots, skills):
    """
    Calculates a weight matrix for assigning skills to robots.
    In this simple example, the weight is based on simulated distance.
    A higher weight means a better assignment.
    """
    num_robots = len(robots)
    num_skills = len(skills)
    weights = np.zeros((num_robots, num_skills))

    for r_idx, robot in enumerate(robots):
        for s_idx, skill in enumerate(skills):
            # Simulate a "cost" based on distance. Lower distance = higher weight.
            # This is a placeholder for a real-world calculation.
            simulated_distance = np.random.rand() 
            
            # The paper adjusts weights by distance. We'll use an inverse relationship.
            # Add a small epsilon to avoid division by zero.
            weight = 1.0 / (simulated_distance + 1e-6)
            
            # Simple check for robot capability (can be expanded)
            if robot['type'] == 'arm_robot' and 'pick_and_place' in skill:
                 weights[r_idx, s_idx] = weight
            elif robot['type'] == 'mobile_robot' and 'transport' in skill:
                 weights[r_idx, s_idx] = weight
            else:
                 weights[r_idx, s_idx] = 0 # Robot cannot perform this skill
                 
    return weights

def solve_task_allocation(robots, executable_skills):
    """
    Uses linear programming to find the optimal assignment of skills to robots.
    """
    num_robots = len(robots)
    num_skills = len(executable_skills)

    if num_skills == 0:
        return {} # No tasks to assign

    # Calculate the weight matrix
    weights = calculate_weights(robots, executable_skills)

    # In linear programming, we maximize the sum of weights.
    # The solver `linprog` minimizes, so we use the negative of the weights.
    c = -weights.flatten()

    # Constraint: Each skill can be assigned to at most one robot.
    # For each skill k, sum(x_jk for all j) <= 1
    A_eq_skill = np.zeros((num_skills, num_robots * num_skills))
    for k in range(num_skills):
        for j in range(num_robots):
            A_eq_skill[k, j * num_skills + k] = 1
    b_eq_skill = np.ones(num_skills)

    # Constraint: Each robot can be assigned at most one skill.
    # For each robot j, sum(x_jk for all k) <= 1
    A_eq_robot = np.zeros((num_robots, num_robots * num_skills))
    for j in range(num_robots):
        for k in range(num_skills):
            A_eq_robot[j, j * num_skills + k] = 1
    b_eq_robot = np.ones(num_robots)
    
    # Combine constraints
    A_ub = np.vstack([A_eq_skill, A_eq_robot])
    b_ub = np.hstack([b_eq_skill, b_eq_robot])

    # Bounds for decision variables (x_jk must be between 0 and 1)
    bounds = [(0, 1) for _ in range(num_robots * num_skills)]

    # Solve the linear programming problem
    result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

    if not result.success:
        print("Warning: Optimization failed or was infeasible.")
        return {}

    # Reshape the solution and find the assignments
    assignment_matrix = np.round(result.x).reshape((num_robots, num_skills))
    
    assignments = {}
    for r_idx in range(num_robots):
        skill_indices = np.where(assignment_matrix[r_idx, :] == 1)[0]
        if skill_indices.size > 0:
            skill_index = skill_indices[0]
            assignments[robots[r_idx]['name']] = executable_skills[skill_index]
            
    return assignments