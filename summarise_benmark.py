import pandas as pd
import os



def get_one_line_for_one_FA(model_name, FA_name, task_name):
    print(' ====> ', FA_name)
    eva_output_dir=f"evaluation_results/benchmark/{model_name}_{FA_name}/{task_name}/"
    directory = os.fsencode(eva_output_dir)
    suff_mean = 0
    comp_mean = 0
    random_suff_mean = 0
    random_comp_mean = 0

    if FA_name == 'norm': lis =['Grad norms']
    elif FA_name == 'input_x_gradient': lis =['GradxEmb']
    elif FA_name == 'integrated_gradients': lis =['Integrated Grad']
    else: lis = [FA_name.replace('_', ' ').title()]
    
    len = 0
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        
        if filename.endswith("mean.csv"): 
            len +=1
            faithful_results = pd.read_csv(eva_output_dir+filename) # one data
            suff_mean += faithful_results['norm_suff_mean'][0]
            random_suff_mean += faithful_results['random_suff_mean'][0]
            comp_mean += faithful_results['norm_comp_mean'][0]
            random_comp_mean += faithful_results['random_comp_mean'][0]
            continue
        else:continue

    print(suff_mean-random_suff_mean, comp_mean-random_comp_mean)
    lis.append((suff_mean-random_suff_mean)/len)
    lis.append((comp_mean-random_comp_mean)/len)
    return lis



all_results = []
for model_name in ["gpt6b", "OPT350M", "gpt2", "gpt2_xl", "OPT1B", "OPT6B"]: # "gpt2","gpt2_xl", "OPT1B", "OPT6B"
# "gpt6b", "OPT350M", 
    for dataset in ['wikitext']: # 'tellmewhy', 
        print()
        print()
        print(f' ============== {model_name},  {dataset}  ============== ')
        try: norm = get_one_line_for_one_FA(model_name, "norm", dataset)
        except: norm = None
        signed = get_one_line_for_one_FA(model_name, "input_x_gradient", dataset)
        integrated = get_one_line_for_one_FA(model_name, "integrated_gradients", dataset)
        gradient_shap = get_one_line_for_one_FA(model_name, "gradient_shap", dataset)

        rollout_attention = get_one_line_for_one_FA(model_name, "attention_rollout", dataset)
        last_attention = get_one_line_for_one_FA(model_name, "attention_last", dataset)
        attention = get_one_line_for_one_FA(model_name, "attention", dataset)
        ours = get_one_line_for_one_FA(model_name, "ours", dataset)

        try: df = pd.DataFrame([norm, signed, integrated, gradient_shap,\
                            rollout_attention, last_attention, attention, ours], columns=['FAs', 'Soft Suff', 'Soft Comp'])
        except: df = pd.DataFrame([signed, integrated, gradient_shap,\
                            rollout_attention, last_attention, attention, ours], columns=['FAs', 'Soft Suff', 'Soft Comp'])
        print(df)
        
        os.makedirs(f'evaluation_results/summary/benchmark/{dataset}/', exist_ok=True)
        df.to_csv(f'evaluation_results/summary/benchmark/{dataset}/{model_name}_{dataset}.csv')
        df['Model'] = model_name
        df['Data'] = dataset
        all_results.append(df)


df = pd.concat(all_results)
df.to_csv(f'evaluation_results/summary/benchmark/ALL.csv')