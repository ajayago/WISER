from evaluation_utils import evaluate_target_classification_epoch, model_save_check, predict_target_classification
from collections import defaultdict
from itertools import chain
from mlp import MLP, geo_MLP
from encoder_decoder_final import  EncoderDecoder_basis
import os
import torch
import torch.nn as nn


def classification_train_step(model, batch, loss_fn, device, optimizer, history, scheduler=None, clip=None):
    model.zero_grad()
    model.train()

    x = batch[0].to(device)
    y = batch[1].to(device)
    loss = loss_fn(model(x), y.double().unsqueeze(1))

    optimizer.zero_grad()
    loss.backward()
    if clip is not None:
        torch.nn.utils.clip_grad_norm_(model.parameters(), clip)

    optimizer.step()
    if scheduler is not None:
        scheduler.step()

    history['bce'].append(loss.cpu().detach().item())

    return history

def fine_tune_encoder_basis(encoder, basis_vec,  train_dataloader, val_dataloader, seed, task_save_folder, inv_temp, test_dataloader=None,
                      metric_name='auroc',
                      normalize_flag=False,
                      break_flag=False,
                      test_df=None,
                      **kwargs):
    
    target_decoder = MLP(input_dim=kwargs['latent_dim'],
                         output_dim=1,
                         hidden_dims=kwargs['classifier_hidden_dims']).to(kwargs['device'])
    target_classifier = EncoderDecoder_basis(encoder=encoder, decoder=target_decoder, basis_vec = basis_vec,  normalize_flag=normalize_flag, testing_drug_len = kwargs['testing_drug_len'], inv_temp = inv_temp).to(
        kwargs['device'])
    
    classification_loss = nn.BCEWithLogitsLoss()

    target_classification_train_history = defaultdict(list)
    target_classification_eval_train_history = defaultdict(list)
    target_classification_eval_val_history = defaultdict(list)
    target_classification_eval_test_history = defaultdict(list)

    encoder_module_indices = [i for i in range(len(list(encoder.modules())))
                              if str(list(encoder.modules())[i]).startswith('Linear')]

    reset_count = 1
    lr = kwargs['lr']

    target_classification_params = [target_classifier.decoder.parameters()]
    target_classification_optimizer = torch.optim.AdamW(chain(*target_classification_params),
                                                        lr=lr)

    for epoch in range(kwargs['train_num_epochs']):
        if epoch % 50 == 0:
            print(f'Fine tuning epoch {epoch}')
        for step, batch in enumerate(train_dataloader):
            target_classification_train_history = classification_train_step(model=target_classifier,
                                                                            batch=batch,
                                                                            loss_fn=classification_loss,
                                                                            device=kwargs['device'],
                                                                            optimizer=target_classification_optimizer,
                                                                            history=target_classification_train_history)
        target_classification_eval_train_history = evaluate_target_classification_epoch(classifier=target_classifier,
                                                                                        dataloader=train_dataloader,
                                                                                        device=kwargs['device'],
                                                                                        history=target_classification_eval_train_history)
        target_classification_eval_val_history = evaluate_target_classification_epoch(classifier=target_classifier,
                                                                                      dataloader=val_dataloader,
                                                                                      device=kwargs['device'],
                                                                                      history=target_classification_eval_val_history)

        if test_dataloader is not None:
            target_classification_eval_test_history = evaluate_target_classification_epoch(classifier=target_classifier,
                                                                                           dataloader=test_dataloader,
                                                                                           device=kwargs['device'],
                                                                                           history=target_classification_eval_test_history)
        save_flag, stop_flag = model_save_check(history=target_classification_eval_val_history,
                                                metric_name=metric_name,
                                                tolerance_count=10,
                                                reset_count=reset_count)
        if save_flag:
            torch.save(target_classifier.state_dict(),
                       os.path.join(task_save_folder, f'target_classifier_{seed}.pt'))
        if stop_flag:
            try:
                ind = encoder_module_indices.pop()
                print(f'Unfreezing {epoch}')
                target_classifier.load_state_dict(
                    torch.load(os.path.join(task_save_folder, f'target_classifier_{seed}.pt')))

                target_classification_params.append(list(target_classifier.encoder.modules())[ind].parameters())
                lr = lr * kwargs['decay_coefficient']
                target_classification_optimizer = torch.optim.AdamW(chain(*target_classification_params), lr=lr)
                reset_count += 1
            except IndexError:
                break
        # if stop_flag and not break_flag:
        #     print(f'Unfreezing {epoch}')
        #     target_classifier.load_state_dict(
        #         torch.load(os.path.join(task_save_folder, f'target_classifier_{seed}.pt')))
        #
        #     target_classification_params.append(target_classifier.encoder.shared_encoder.parameters())
        #     target_classification_params.append(target_classifier.encoder.private_encoder.parameters())
        #
        #     lr = lr * kwargs['decay_coefficient']
        #     target_classification_optimizer = torch.optim.AdamW(chain(*target_classification_params), lr=lr)
        #     break_flag = True
        #     stop_flag = False
        # if stop_flag and break_flag:
        #     break

    target_classifier.load_state_dict(
        torch.load(os.path.join(task_save_folder, f'target_classifier_{seed}.pt')))

    prediction_df = None
    if test_df is not None:
        prediction_df = predict_target_classification(classifier=target_classifier, test_df=test_df,
                                                      device=kwargs['device'])

    return target_classifier, (target_classification_train_history, target_classification_eval_train_history,
                               target_classification_eval_val_history, target_classification_eval_test_history)

