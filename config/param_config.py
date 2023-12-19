import torch

results_data = {"TCGA" : -1, "CCLE" : -2}
graphLoader = False
cosine_flag = True
ccle_only = False 
a_thres = 0.0
pseudo_loss_flag = False
############ Subset Selection #########
subset_selection_flag = True

seed = 2020
folder_name = "logs/exp_tmp"
assert(not graphLoader)
device = 'cuda:1' if torch.cuda.is_available() else 'cpu'
# eff_drug_list = ['fu', 'tem', 'gem', 'cis', 'sor']
eff_drug_list = [ 'sor', 'gem', 'fu', 'cis','tem' ]
# eff_drug_list = ['gem']
test_data_index = results_data["TCGA"]
basis_drug_list = ['fu', 'tem', 'gem', 'cis', 'sor','sun', 'dox', 'tam', 'pac', 'car', 'Cetuximab', 'Methotrexate', 'Topotecan', 'Erlotinib', 'Irinotecan', 'Bicalutamide', 'Temsirolimus', 'Oxaliplatin', 'Docetaxel', 'Etoposide']