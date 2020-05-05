import numpy as np
from mpnet.sst_envs.utils import load_data, visualize_point, get_obs
import pickle
import time
import click

import sys
sys.path.append('/media/arclabdl1/HD1/Linjun/mpc-mpnet-py/deps/sparse_rrt-1')

from sparse_rrt import _sst_module

def experiment(env_id, traj_id, verbose=False, model='acrobot_obs'):
    obs_list = get_obs(model, env_id)[env_id].reshape(-1, 2)
    data = load_data(model, env_id, traj_id)
    ref_path = data['path']
    start_goal = data['start_goal']
    env_vox = np.load('mpnet/sst_envs/acrobot_obs_env_vox.npy')
    obc = env_vox[env_id, 0]
    width = 6
    number_of_iterations = 5000

    planner = _sst_module.DSSTMPCWrapper(
            start_state=np.array(ref_path[0]),
            goal_state=np.array(ref_path[-1]),
            goal_radius=10,
            random_seed=0,
            sst_delta_near=1,
            sst_delta_drain=0.5,
            obs_list=obs_list,
            width=width,
            verbose=False
        )
    ## start experiment
    tic = time.perf_counter()
    for iteration in range(number_of_iterations):
        # planner.step(min_time_steps, max_time_steps, integration_step)
        planner.neural_step(obc.reshape(-1))
    #         planner.neural_step(obc.reshape(-1))
        solution = planner.get_solution()
        if iteration % 100 == 0:
            if solution is not None:
                break    
    toc = time.perf_counter()
#     print(mpc_mpnet.costs)
    costs = solution[2].sum() if solution is not None else np.inf
    result = {
        'env_id': env_id,
        'traj_id': traj_id,
        'planning_time': toc-tic,
        'successful': solution is not None,
        'costs': costs
    }
    
    print("env {}, traj {}, {}, time: {} seconds, {}(ref:{}) costs".format(
            env_id, 
            traj_id,
            result['successful'],
            result['planning_time'],
            result['costs'],
            data['cost'].sum()))
    return result
    

def full_benchmark(num_env, num_traj, save=True, config='default'):
    sr = np.zeros((num_env, num_traj))
    time = np.zeros((num_env, num_traj))
    costs = np.zeros((num_env, num_traj))

    for env_id in range(num_env):
        for traj_id in range(num_traj):
            result = experiment(env_id, traj_id)
            sr[env_id, traj_id] = result['successful']
            if result['successful']:
                time[env_id, traj_id] = result['planning_time']
                costs[env_id, traj_id] = result['costs']
            if save:
                np.save('results/cpp_full/{}/sr_{}_{}_{}.npy'.format(config, config, num_env, num_traj), sr)
                np.save('results/cpp_full/{}/time_{}_{}_{}.npy'.format(config, config, num_env, num_traj), time)
                np.save('results/cpp_full/{}/costs_{}_{}_{}.npy'.format(config, config, num_env, num_traj), costs)


@click.command()
@click.option('--full', default=True)
@click.option('--env_id', default=0)
@click.option('--traj_id', default=0)
@click.option('--num_env', default=10)
@click.option('--num_traj', default=1000)
@click.option('--save', default=True)
@click.option('--config', default='ls')
def main(full, env_id, traj_id, num_env, num_traj, save, config):
    if not full:
        result = experiment(env_id, traj_id)
    else:
        result = full_benchmark(num_env, num_traj, save, config)
   
    
    
if __name__ == '__main__':
    main()