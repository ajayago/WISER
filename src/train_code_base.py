import os
from itertools import chain

from src.dsn_ae import DSNAE
from src.evaluation_utils import *
from src.mlp import MLP


def eval_dsnae_epoch(model, data_loader, device, history):
    """

    :param model:
    :param data_loader:
    :param device:
    :param history:
    :return:
    """
    model.eval()
    avg_loss_dict = defaultdict(float)
    for x_batch in data_loader:
        x_batch = x_batch[0].to(device)
        with torch.no_grad():
            loss_dict = model.loss_function(*(model(x_batch)))
            for k, v in loss_dict.items():
                avg_loss_dict[k] += v.cpu().detach().item() / len(data_loader)

    for k, v in avg_loss_dict.items():
        history[k].append(v)
    return history


def eval_basis_dsnae_epoch(model, data_loader, device, history):
    """

    :param model:
    :param data_loader:
    :param device:
    :param history:
    :return:
    """
    model.eval()
    avg_loss_dict = defaultdict(float)

    for x_batch in data_loader:
        # print(f'x_batch : {x_batch[1].shape}')
        X_batch = x_batch[0].to(device)
        T_batch = x_batch[1].to(device)
        with torch.no_grad():
            loss_dict = model.loss_function(X_batch, T_batch)
            for k, v in loss_dict.items():
                avg_loss_dict[k] += v.cpu().detach().item() / len(data_loader)

    for k, v in avg_loss_dict.items():
        history[k].append(v)
    return history



def dsn_ae_train_step(s_dsnae, t_dsnae, s_batch, t_batch, device, optimizer, history, scheduler=None):
    s_dsnae.zero_grad()
    t_dsnae.zero_grad()
    s_dsnae.train()
    t_dsnae.train()

    s_x = s_batch[0].to(device)
    t_x = t_batch[0].to(device)

    s_loss_dict = s_dsnae.loss_function(*s_dsnae(s_x))
    t_loss_dict = t_dsnae.loss_function(*t_dsnae(t_x))

    optimizer.zero_grad()
    loss = s_loss_dict['loss'] + t_loss_dict['loss']
    loss.backward()

    optimizer.step()
    if scheduler is not None:
        scheduler.step()
    loss_dict = {k: v.cpu().detach().item() + t_loss_dict[k].cpu().detach().item() for k, v in s_loss_dict.items()}

    for k, v in loss_dict.items():
        history[k].append(v)

    return history


def basis_dsn_ae_train_step(s_dsnae, t_dsnae, s_batch, t_batch, device, optimizer, history, scheduler=None):
    s_dsnae.zero_grad()
    t_dsnae.zero_grad()
    s_dsnae.train()
    t_dsnae.train()

    # s_x = s_batch[0].to(device)
    # t_x = t_batch[0].to(device)

    # s_target = s_batch[1].to(device)
    # t_target = t_batch[1].to(device)
    print(s_batch)
    print("src==")
    print(s_x, t_x)
    print("target==")
    print(s_target, t_target)
    # source_prediction = s_dsnae(s_x)
    # target_prediction = t_dsnae(t_x)
    
    s_loss_dict = s_dsnae.loss_function(s_x, s_target)
    t_loss_dict = t_dsnae.loss_function(t_x, t_target)

    optimizer.zero_grad()

    loss = s_loss_dict['loss'] + t_loss_dict['loss'] ## NOTE : hyperparameter not included
    loss.backward()

    optimizer.step()
    if scheduler is not None:
        scheduler.step()
    loss_dict = {k: v.cpu().detach().item() + t_loss_dict[k].cpu().detach().item() for k, v in s_loss_dict.items()}

    for k, v in loss_dict.items():
        history[k].append(v)

    return history





