import numpy as np
from mpnet.sst_envs.utils import load_data, get_obs
import pickle
import time
import click
from tqdm import tqdm
from pathlib import Path
import importlib

import sys
sys.path.append('/media/arclabdl1/HD1/Linjun/mpc-mpnet-py/deps/sparse_rrt-1')

from sparse_rrt import _deep_smp_module
# from params.cpp_dst_s32_e4 import get_params

def experiment(env_id, traj_id, verbose=False, system='cartpole_obs', params_module=None):
    print("env {}, traj {}".format(env_id, traj_id))
    obs_list = get_obs(system, env_id)[env_id].reshape(-1, 2)
    data = load_data(system, env_id, traj_id)
    ref_path = data['path']
    start_goal = data['start_goal']
    # print(start_goal)
    env_vox = np.load('mpnet/sst_envs/{}_env_vox.npy'.format(system))
    obc = env_vox[env_id, 0]
    # print(obs_list)
    params = params_module.get_params()
    number_of_iterations = params['number_of_iterations'] #3000000# 
    min_time_steps = params['min_time_steps'] if 'min_time_steps' in params else 80
    max_time_steps = params['max_time_steps'] if 'min_time_steps' in params else 400
    integration_step = params['dt']

    planner = _deep_smp_module.DSSTMPCWrapper(
            system,
            start_state=np.array(ref_path[0]),
            goal_state=np.array(ref_path[-1]),
            # goal_state=np.array(data['start_goal'][-1]),
            goal_radius=params['goal_radius'],
            random_seed=0,
            sst_delta_near=params['sst_delta_near'],
            sst_delta_drain=params['sst_delta_drain'],
            goal_bias=params['goal_bias'],
            obs_list=obs_list,
            width=params['width'],
            verbose=params['verbose'],
            mpnet_weight_path=params['mpnet_weight_path'], 
            cost_predictor_weight_path=params['cost_predictor_weight_path'],
            cost_to_go_predictor_weight_path=params['cost_to_go_predictor_weight_path'],
            num_sample=params['cost_samples'],
            ns=params['n_sample'], nt=params['n_t'], ne=params['n_elite'], max_it=params['max_it'],
            converge_r=params['converge_r'], mu_u=params['mu_u'], std_u=params['sigma_u'], mu_t=params['mu_t'], 
            std_t=params['sigma_t'], t_max=params['t_max'], step_size=params['step_size'], integration_step=params['dt'], 
            device_id=params['device_id'], refine_lr=params['refine_lr'],
        )
    solution = planner.get_solution()

    data_cost = np.sum(data['cost'])
    th = 1.2 * data_cost
    ## start experiment
    tic = time.perf_counter()
    for iteration in tqdm(range(number_of_iterations)):
        # planner.step(min_time_steps, max_time_steps, params['dt'])
        if params['hybrid']:
            if np.random.rand() < params['hybrid_p']:
                planner.step(min_time_steps, max_time_steps, integration_step)
            else:
                planner.neural_step(obc.reshape(-1), params['refine'], 
                    refine_threshold=params['refine_threshold'],
                    using_one_step_cost=params['using_one_step_cost'],
                    cost_reselection=params['cost_reselection'])
        else:
            # planner.step(min_time_steps, max_time_steps, integration_step)
            planner.neural_step(obc.reshape(-1), params['refine'], 
                    refine_threshold=params['refine_threshold'],
                    using_one_step_cost=params['using_one_step_cost'],
                    cost_reselection=params['cost_reselection'])
        # planner.mpc_step(integration_step)
        solution = planner.get_solution()
        if solution is not None: #and np.sum(solution[2]) < th:
            break    
    toc = time.perf_counter()
    if solution is not None:
        print(solution[0], solution[2])
#     print(mpc_mpnet.costs)
    costs = solution[2].sum() if solution is not None else np.inf
    result = {
        'env_id': env_id,
        'traj_id': traj_id,
        'planning_time': toc-tic,
        'successful': solution is not None,
        'costs': costs
    }
    
    print("\t{}, time: {} seconds, {}(ref:{}) costs".format(
            result['successful'],
            result['planning_time'],
            result['costs'],
            np.sum(data['cost'])))
    return result
    

def full_benchmark(num_env, num_traj, save=True, config='default', report=True, params_module=None, system='acrobot_obs'):
    sr = np.zeros((num_env, num_traj))
    time = np.zeros((num_env, num_traj))
    costs = np.zeros((num_env, num_traj))

    for env_id in range(num_env):
        for traj_id in range(num_traj):
            result = experiment(env_id, traj_id, params_module=params_module, system=system)
            sr[env_id, traj_id] = result['successful']
            if result['successful']:
                time[env_id, traj_id] = result['planning_time']
                costs[env_id, traj_id] = result['costs']
            if save:
                Path("results/cpp_full/{}/{}/".format(config, system)).mkdir(parents=True, exist_ok=True)
                np.save('results/cpp_full/{}/{}/sr_{}_{}.npy'.format(config, system, num_env, num_traj), sr)
                np.save('results/cpp_full/{}/{}/time_{}_{}.npy'.format(config, system, num_env, num_traj), time)
                np.save('results/cpp_full/{}/{}/costs_{}_{}.npy'.format(config, system,  num_env, num_traj), costs)
            if report:
                print("sr:{}\ttime:{}\tcosts:{}".format(
                    sr.reshape(-1)[:(num_traj*env_id+traj_id+1)].mean(),
                    time.reshape(-1)[:(num_traj*env_id+traj_id+1)].mean(),
                    costs.reshape(-1)[:(num_traj*env_id+traj_id+1)].mean(),
                    ))

@click.command()
@click.option('--full', default=True)
@click.option('--env_id', default=0)
@click.option('--traj_id', default=0)
@click.option('--num_env', default=10)
@click.option('--num_traj', default=100)
@click.option('--save', default=True)
@click.option('--config', default='default')
@click.option('--report', default=True)
@click.option('--system', default="cartpole_obs")
def main(full, env_id, traj_id, num_env, num_traj, save, config, report, system):
    p = importlib.import_module('.cpp_dst_{}'.format(config), package=".params.{}".format(system))
    if not full:
        result = experiment(env_id, traj_id, system=system)
    else:
        result = full_benchmark(num_env, num_traj, save, config, report, p, system=system)
   
    
    
if __name__ == '__main__':
    main()
