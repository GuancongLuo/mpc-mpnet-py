import numpy as np

def get_params():
    # params from cpp_dst_gr2_n1_d0_1_s32_e4_step3.py
    params = {
        'n_sample': 32,
        'n_elite': 4,
        'n_t': 3,
        'max_it': 10,
        'converge_r': 1e-1,

        'dt': 2e-2,
        'mu_u': 0,
        'sigma_u': 4,
        'mu_t': 1e-1,
        'sigma_t': 5e-1,
        't_max': 0.5,
        'verbose': False,
        'step_size': 0.75,

        "goal_radius": 2,
        "sst_delta_near": 1,
        "sst_delta_drain": 1e-1,
        "width": 6,
        "hybrid": False,
        "hybrid_p": 0.2,
        "cost_samples": 10,
        "mpnet_weight_path":"mpnet/exported/output/mpnet_10k.pt",
        "cost_predictor_weight_path": "mpnet/exported/output/cost_10k.pt",
        "refine": False,
        "refine_lr": 5e-2
    }

    return params
    
