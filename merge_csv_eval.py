from collections import defaultdict
import os
import re
import pandas as pd
from scipy import stats
from analyze_test_suites import get_analyze_dfs
import matplotlib.pyplot as plt
import seaborn as sns

name_mapping = {
    # "segment_based_AGEMOEA2": "SegTCP1",
    "segment_based_AGEMOEA": "SegTCP",
    # "segment_based_NSGA2": "SegTCP3",
    "ga": "GA",
    "gt": "GT",
    "ga_s": "GA-S",
    "terminator": "Terminator",
    # "fast": "FAST",
    "artf": "ART-F",
    "random": "Random",
}

def get_csv(folder):
    # get all csv files in folder recursively
    csv_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file == "all_solutions-dup.csv":
                csv_files.append(os.path.join(root, file))
    return csv_files


def dfs2excel(dfs, sheet_names, file_name):
    writer = pd.ExcelWriter(file_name)
    # try: 
    #     get_analyze_dfs(writer)
    # except:
    #     pass

    for df, sheet_name in zip(dfs, sheet_names):
        if 'APFD' in df.columns:
            df.sort_values(by=['APFD'], inplace=True, ascending=False)
        df.to_excel(writer, sheet_name=sheet_name)
    # workbook = writer.book
    # sheets = workbook.worksheets()
    # sheets.sort(key=lambda x: x.name)
    writer._save()


def average_df(dfs):
    avg_sols = {}
    sols = set()
    for df in dfs:
        # remove rows that match regex of a number
        regex = r"^\d+$"
        print(df)
        df = df[df['solution'].apply(lambda x: not re.match(regex, str(x)))]
        sols = sols.union(set(df['solution'].values))
        print(df)

    # merge all dfs
    df = pd.concat(dfs)
    # group by solution
    df = df.groupby(['solution'])
    # calculate std
    df_std = df.std()
    # calculate average
    df = df.mean()
    # add std to df
    df['std'] = df_std['APFD']

    # add to dict
    for sol in sols:
        avg_sols[sol] = df.loc[sol]
    # convert to df
    df = pd.DataFrame.from_dict(avg_sols)
    # transpose
    df = df.transpose()
    # add column for solution
    df['solution'] = df.index
    # set index to solution
    df.set_index('solution', inplace=True)
    # sort by solution
    df.sort_index(inplace=True)
    return df

def kruskal_wallis_df(dfs, average_df, metric='APFD'):
    # get all methods names from average_df
    methods = average_df.index.values
    my_methods = [method for method in methods if method.startswith('segment')]
    other_methods = [method for method in methods if method not in my_methods and method not in ['best', 'worst']]

    #get all solutions of each method from dfs
    my_solutions = {}
    other_solutions = {}

    for df in dfs:
        for method in my_methods:
            if method not in my_solutions:
                my_solutions[method] = []
            # print(df[df['solution'] == method])
            my_solutions[method].extend(df[df['solution'] == method][metric].values)
        for method in other_methods:
            if method not in other_solutions:
                other_solutions[method] = []
            other_solutions[method].extend(df[df['solution'] == method][metric].values)

    # compare each of my methods with each of other methods
    comparison = {}
    for my_method in my_methods:
        for other_method in other_methods:
            if metric == 'sibling_dup':
                comparison[(my_method, other_method)] = p_value([-x for x in my_solutions[my_method]], [-x for x in other_solutions[other_method]])
            else:
                comparison[(my_method, other_method)] = p_value(my_solutions[my_method], other_solutions[other_method])

    # create a df from comparison
    df = pd.DataFrame.from_dict(comparison, orient='index')
    df.columns = [f'p-value-{metric}']
    # add column for checking if p-value is significant
    df[f'significant-{metric}'] = df[f'p-value-{metric}'].apply(lambda x: x < 0.05)
    df.sort_index(inplace=True)
    print(df)
    return df

def p_value(your_method_results, other_method_results):
    statistic, p_value = stats.wilcoxon(your_method_results, other_method_results, alternative='greater')
    # statistic, p_value = stats.mannwhitneyu(your_method_results, other_method_results)
    print(your_method_results, other_method_results)
    print("statistic", statistic)
    print("p_value", p_value)
    return float(p_value)

def plot_boxplot_apfd(apfd_dict, file_name):

    # draw multiple boxplots in one figure, each representing a solution
    fig, ax = plt.subplots(figsize=(12, 8))
    df = pd.DataFrame.from_dict(apfd_dict)
    df = df.melt(var_name='solution', value_name='APFD')
    sns.boxplot(x='solution', y='APFD', data=df, ax=ax)
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(file_name)
    plt.show()

def plot_boxplot_2(apfd_dict, apfdc_dict, file_name):
    # draw multiple boxplots in one figure, each solution has 2 boxplots, one for apfd and one for apfdc
    plt.rcParams.update({'font.size': 20})
    fig, ax = plt.subplots(figsize=(12, 8))
    df = pd.DataFrame.from_dict(apfd_dict)
    df = df.melt(var_name='solution', value_name='APFD')
    df2 = pd.DataFrame.from_dict(apfdc_dict)
    df2 = df2.melt(var_name='solution', value_name='APFDC')
    df = df.merge(df2, on='solution')
    # remove solution 'best' and 'worst'
    df = df[df['solution'].apply(lambda x: x not in ['best', 'worst'] and x in name_mapping)]
    # rename solution names
    df['solution'] = df['solution'].apply(lambda x: name_mapping[x])
    # sort solution name by order of name_mapping
    df['solution'] = pd.Categorical(df['solution'], name_mapping.values())
    # *100 for apfdc and apfd and round to 2 decimal places
    df['APFDC'] = df['APFDC'].apply(lambda x: round(x*100, 2))
    df['APFD'] = df['APFD'].apply(lambda x: round(x*100, 2))
    df = df.melt(id_vars=['solution'], var_name='metric', value_name='value')
    #set font size: 14
    sns.set(font_scale=1.4)
    sns.boxplot(x='solution', y='value', hue='metric', data=df, ax=ax, palette="Set3", linewidth=2.5)
    plt.xticks(rotation=45, fontsize=20)
    plt.xlabel('Method', fontsize=20)
    plt.ylabel('Value', fontsize=20)
    plt.tight_layout()
    plt.savefig(file_name)
    # plt.show()/



    


def main(folder="data/solutions-main/solutions-all-01-12-2023 14:50:15"):
    csv_files = get_csv(folder)
    dfs = []
    processed_files = []
    # my_data = ["moodle", "juice_shop", "mattermost"]
    for file in csv_files:
        # if not any(data in file for data in my_data):
        #     continue    
        print("Processing", file)
        df = pd.read_csv(file)
        # remove rows that match regex of a number
        regex = r"^\d+$"
        df = df[df['solution'].apply(lambda x: not re.match(regex, str(x)))]
        dfs.append(df)
        processed_files.append(file)
    avg_df = average_df(dfs)

    solutions = avg_df.index.values
    apfd_dict = defaultdict(list)
    apfdc_dict = defaultdict(list)
    # for each solution, get all apfd values from all dfs
    for solution in solutions:
        print(solution)
        for df in dfs:
            apfd_dict[solution].append(df[df['solution'] == solution]['APFD'].values[0])
            apfdc_dict[solution].append(df[df['solution'] == solution]['APFDC'].values[0])
    plot_boxplot_2(apfd_dict, apfdc_dict, f"{folder}/apfd_apfdc_boxplot.pdf")

    try:
        stats_df_apfd = kruskal_wallis_df(dfs, avg_df, metric='APFD')
        stats_df_apfdc = kruskal_wallis_df(dfs, avg_df, metric='APFDC')
        stats_df_apsd = kruskal_wallis_df(dfs, avg_df, metric='APSD')
        stats_df_apod = kruskal_wallis_df(dfs, avg_df, metric='APOD')
        stats_df_apotd = kruskal_wallis_df(dfs, avg_df, metric='APOTD')
        stats_df_apsbd = kruskal_wallis_df(dfs, avg_df, metric='APSBD')
        stats_df_sbdr = kruskal_wallis_df(dfs, avg_df, metric='sibling_dup')

        # merge all stats dfs by index
        stats_df = pd.concat([stats_df_apfd, stats_df_apfdc, stats_df_apsd, stats_df_apod, stats_df_apotd, stats_df_apsbd, stats_df_sbdr], axis=1)
    except:
        stats_df = pd.DataFrame()

    # dfs.append(stats_df_apfd)
    # dfs.append(stats_df_apfdc)
    # dfs.append(stats_df_apsd)
    # dfs.append(stats_df_apod)
    # dfs.append(stats_df_apotd)
    # dfs.append(stats_df_apsbd)
    dfs.append(stats_df)
    dfs.append(avg_df)

    sheet_names = [os.path.basename(file.split("/all_solutions-dup.csv")[0])[:31] for file in processed_files] + ['stats', 'average']
    dfs2excel(dfs, sheet_names, f"{folder}/merged_greater_all-dup.xlsx")




if __name__ == '__main__':
    main()
