from dataset.dataset import get_loader_cost
from networks.mpnet import MPNet
from networks.costnet import CostNet
import torch

import numpy as np
import click

from training_utils.trainer import train_network
 
@click.command()
@click.option('--ae_output_size', default=1024, help='ae_output_size')
@click.option('--state_size', default=4, help='')
@click.option('--lr', default=1e-3, help='learning_rate')
@click.option('--epochs', default=5000, help='epochs')
@click.option('--batch', default=128, help='batch')
@click.option('--system_env', default='sst_envs')
@click.option('--system', default='acrobot_obs')
@click.option('--setup', default='default_norm')
@click.option('--loss_type', default='l1_loss')
@click.option('--load_from', default='mpnet')
@click.option('--network_type', default='cost_to_go')
def main(ae_output_size, state_size, lr, epochs, batch, 
    system_env, system, setup, loss_type, load_from, network_type):
    mpnet = MPNet(ae_input_size=32, ae_output_size=1024, in_channels=1, state_size=4)
    mpnet.load_state_dict(torch.load('output/acrobot_obs/{}/{}/ep10000.pth'.format(setup,load_from)))
    
    costnet = CostNet(ae_input_size=32, ae_output_size=1024, in_channels=1, state_size=4, encoder=mpnet.encoder)
    for param in costnet.encoder.parameters():
        param.requires_grad = False

    data_loaders = get_loader_cost(system_env, system, batch_size=batch, setup=setup, network_type=network_type)

    train_network(network=costnet, data_loaders=data_loaders, 
            network_name=network_type,
        lr=lr, epochs=epochs, batch=batch, 
        system_env=system_env, system=system, setup=setup,
        using_step_lr=True, step_size=50, gamma=0.9,
        loss_type=loss_type, weight_save_epochs=50)


if __name__ == "__main__":
    main()
