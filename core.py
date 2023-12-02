# base libraries
import math
import os
import random
from pprint import pprint
import pandas as pd
import numpy as np
import scipy
import openpyxl
import gdown

# basic plotting libraries
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import seaborn as sns

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def save_to_excell(df, tab, path):

    # if spreadsheet not exists, create a new one
    if not os.path.isfile(path):
        writer = pd.ExcelWriter(path)
        df.to_excel(writer, sheet_name=tab)
        writer.close()
        
    book = openpyxl.load_workbook(path)
    
    # remove old tab if it exists
    if tab in book.sheetnames:
        book.remove(book[tab])
    
    # add new tab content
    writer = pd.ExcelWriter(path)
    writer.book = book     
    df.to_excel(writer, sheet_name=tab)
    writer.close()

# Default datasets colors
group_to_color_map = {
    #'BR_NEUTRAL_pt': '#F6D900', 
    #'BR_NEUTRAL_pt_translated': '#f4efcb', 
    #'BR_NEUTRAL_en': '#CE2A1D',
    #'BIASED_pt': '#3B5998', 
    #'BR_BIASED_en': '#8B9DC3', 
    #'FB_OTHER_en': '#DFE3EE', 
    #'FB_PERSON_en': '#F7F7F7', 
    #'G1_SITE_pt': '#C4170C',     
    #'NYT_SITE_en': '#111111', 
    #'NEUTRAL_pt': '#3A923A', 
    #'NEUTRAL_en': '#B3D495',
    #'TOXIC_pt': '#C03D3E', 
    #'TOXIC_en': '#EFA6A5', 
}

def create_palette(groups):
    
    # Okabe-lto scale for color blind people https://wilkelab.org/SDS375/slides/color-spaces.html#29
    divergent_colors = [
        '#E69F00', '#56b4e9', '#009e73', '#f0e442', '#0072b2', '#d55e00', '#cc79a7', '#666'
    ]
    
    # create color palette
    palette = {}
    for group in groups:
        if group in group_to_color_map:
            palette[group] = group_to_color_map[group]
        else:
            # get the first color from divergent_colors and append to the end of this list
            color = divergent_colors.pop(0)
            divergent_colors.append(color)
            
            palette[group] = color
            
    return palette


def prepare_comments_dataframe(df, attributes, group_by):
    
    # project only needed attributes to reduce dataframe dimensions
    if attributes is not None:
        df = df[[group_by] + attributes]
    
    # melt the dataframe
    df_melted = pd.melt(df, id_vars=[group_by], value_vars=attributes, var_name='attribute')
    
    # cast 'attribute' to category type to allow sorting 
    df_melted['attribute'] = df_melted['attribute'].astype('category')
    df_melted['attribute'].cat.set_categories(attributes, inplace=True)
    
    return df_melted


def summarize_prepared_dataframe(df, group_by, stats=['mean', 'median', 'std'], sort_by='mean'):
    pd.set_option('display.max_rows', 200)
    return df.groupby(['attribute', group_by]).agg(stats).sort_values(['attribute', ('value', sort_by)], ascending=[True, False])


def analyze_comments_dataframe(df, attributes, group_by, hue_order=None, legend_ncols=4, width=None, height=None, legend_top=True, xlabel=None, ylabel=None, sort_by_median=False, save_as=None):
    
    # sort by medians
    if sort_by_median:        
        df['median'] = df.groupby(group_by)['TOXICITY'].transform('median')
        df = df.loc[df['median'].sort_values(ascending=False).index]
    
    # prepare and summarize the dataframe before plotting
    df = prepare_comments_dataframe(df, attributes, group_by)
    df_summarized = summarize_prepared_dataframe(df, group_by)
    
    groups = df[group_by].unique()

    N_groups = len(groups)
    N_attributes = len(attributes)
    
    # legend parameters
    ncols = legend_ncols or 4
    nrows = math.ceil(N_groups / ncols)
    
    # calculate figure width and height according the # of attributes and groups
    if width is None:
        width = 15 if N_groups*N_attributes*0.3 >= 15 else N_groups*N_attributes*0.3
    if height is None:
        height = 3 + 0.1*nrows
    
    # automatically create color palette
    palette = create_palette(groups)        
    
    # plot the figure
    fig, ax = plt.subplots(figsize=(width, height))
    ax = sns.boxplot(y='value', x='attribute', data=df, hue=group_by, width=0.9, showfliers = False, hue_order=hue_order, palette=palette, saturation=1)
    ax.tick_params(labelsize=8)
    
    # add xlabel
    ax.set(xlabel=xlabel, ylabel=ylabel)
    
    # replace original legend
    ax.get_legend().remove()
    if legend_top:
        lgd = fig.legend(loc='upper center', ncol=ncols, bbox_to_anchor=(.5, 1 + .04*nrows))
    else:
        # move legend to right of the plot
        lgd = fig.legend(loc='center left', bbox_to_anchor=(0.95, 0.6), ncol=ncols) 
    
    if save_as:
        fig.tight_layout()
        fig.savefig('figures/' + save_as, format='png', dpi=300, bbox_extra_artists=(lgd,), bbox_inches='tight')
        
    return df, df_summarized



def plot_toxicity_boxplots_to_paper(df, group_by, width, height, callback, sort_by_median=False, save_as=None):
    
    sns.set_theme()
    sns.set(style='ticks', rc={'figure.figsize':(width, height), 'axes.facecolor': 'white'})
    
    # sort by medians
    if sort_by_median:        
        df['median'] = df.groupby(group_by)['TOXICITY'].transform('median')
        df = df.loc[df['median'].sort_values(ascending=False).index]
    
    # prepare and summarize the dataframe before plotting
    df = df[[group_by, 'TOXICITY']]
    
    groups = df[group_by].unique()
    N_groups = len(groups)
    
    # automatically create color palette
    palette = create_palette(groups)
    
    # plot the figure
    #fig, ax = plt.subplots(figsize=(width, height))
    ax = sns.boxplot(y='TOXICITY', x=group_by, data=df, showfliers = False, palette=palette, saturation=1)
    
    # add group labels on x-axis
    ax.tick_params(axis='x', labelrotation=90, labelsize=12)
    
    # set x and y labels
    ax.set(xlabel=None, ylabel='Toxicity')
    
    # calculate median for each group and add it to plot
    medians = df.groupby([group_by])['TOXICITY'].median().to_dict()
    x_ticks = range(len(medians))
    for tick, label in enumerate(ax.get_xticklabels()):
        label = label.get_text()
        
        ax.text(x_ticks[tick], # x position 
                medians[label] + 0.04,  # y position
                "{:.2f}".format(medians[label]),
                bbox=dict(facecolor='#000000', boxstyle='round,pad=0.3', alpha=0.3),
                horizontalalignment='center',
                size='9',
                color='#fff',
                #rotation=90,
                weight='bold')
    
    ax.grid(axis='y')
    
    if callback:
        callback(ax)
    
    if save_as:
        plt.tight_layout()
        plt.savefig('figures/' + save_as, format='png', dpi=300, bbox_inches='tight')
        
    return ax





# QQ Plot
from statsmodels.graphics.gofplots import qqplot
from matplotlib import pyplot

def plot_qq(df, group_by, groups=None):
    
    if groups is None:
        groups = df[group_by].unique()

    # create subplots for QQ
    fig_qq, ax_qq = plt.subplots(figsize=(len(groups)*2.5, 2.5), ncols=len(groups), sharex=True, sharey=True)
    fig_qq.suptitle('TOXICITY', fontsize=14, y=1.1)

    # create subplots for Histograms
    fig_hist, ax_hist = plt.subplots(figsize=(len(groups)*2.5, 2.5), ncols=len(groups), sharex=True, sharey=True)    

    for i, group in enumerate(groups):
        data = df[df[group_by] == group]['TOXICITY']

        # QQ Plot
        qqplot(data, line='s', ax=ax_qq[i])
        ax_qq[i].set_title(group)

        # histogram
        data.plot.hist(ax=ax_hist[i])
        ax_hist[i].set_title(group)



from scipy.stats import mannwhitneyu
    
def run_mannwhitneyu_test(df, group_by, export_to_latex=False, report_h0_acceptance=False, alpha=.05):
    
    groups = df[group_by].unique()        
    N_groups = len(groups)

    # initiate a matrix for pairwise results
    results = [["" for j in range(N_groups)] for i in range(N_groups)]

    # Calculate Wilcoxon Test pairwise
    for i in range(len(groups)):
        for j in range(i+1, len(groups)):
            
            # group i toxicity values
            group_i = groups[i]
            sample_i = df[df[group_by] == group_i]['TOXICITY'].tolist()
            
            # group j toxicity values
            group_j = groups[j]
            sample_j = df[df[group_by] == group_j]['TOXICITY'].tolist()
        
            statistic, pvalue = mannwhitneyu(sample_i, sample_j, use_continuity=True, alternative='two-sided')
            
            if report_h0_acceptance and pvalue >= alpha:
                print(groups[i], '(N = ' + str(len(sample_i)) + ') ', ' VS ', groups[j], '(N = ' + str(len(sample_j)) +')', '\tKS =', str(statistic) + '\tp-value =', pvalue, '\n')
            
            results[i][j] = str(round(statistic, 3)) + pvalue_as_star(pvalue)
            
    df_results = pd.DataFrame(results, columns=groups, index=groups)
    
    # invert column order to make it easier to read (placing values in the diagonal)
    #df_results = df_results[reversed(df_results.columns)]
    
    # report on paper
    if export_to_latex:
        print(df_results.to_latex(index=True, float_format="%.4f"))
            
    return df_results


from scipy.stats import normaltest

def pvalue_as_star(p):
    p_star = ''
    if p < .001:
        p_star = '***'
    elif p < .01:
        p_star = '**'
    elif p < .05:
        p_star = '*'
    return p_star
    
def run_normal_test(df, group_by, export_to_latex=False):
    
    results = []
    for group in df[group_by].unique():

        # D’Agostino Test
        x = df[df[group_by] == group]['TOXICITY'].tolist()
        k2, pvalue = normaltest(x)

        results.append({
            group_by: group,
            'k²': k2,
            'k² (with p)': str(round(k2, 4)) + pvalue_as_star(pvalue),
            'N': len(x), 
            'p-value': pvalue
        })
            
    df_results = pd.DataFrame(results)
    
    # report on paper
    if export_to_latex:
        print(df_results[[group_by, 'k² (with p)']].to_latex(index=False, float_format="%.4f"))

    return df_results







from scipy.stats import ks_2samp
    
def run_ks_test(df, group_by, export_to_latex=False, report_h0_acceptance=False, alpha=.05):
    
    groups = df[group_by].unique()        
    N_groups = len(groups)

    # initiate a matrix for pairwise results
    results = [["" for j in range(N_groups)] for i in range(N_groups)]

    # Calculate Wilcoxon Test pairwise
    for i in range(len(groups)):
        for j in range(i+1, len(groups)):
            
            # group i toxicity values
            group_i = groups[i]
            sample_i = df[df[group_by] == group_i]['TOXICITY'].tolist()
            
            # group j toxicity values
            group_j = groups[j]
            sample_j = df[df[group_by] == group_j]['TOXICITY'].tolist()
        
            statistic, pvalue = ks_2samp(sample_i, sample_j)
            
            if report_h0_acceptance and pvalue >= alpha:
                print(groups[i], '(N = ' + str(len(sample_i)) + ') ', ' VS ', groups[j], '(N = ' + str(len(sample_j)) +')', '\tKS =', str(statistic) + '\tp-value =', pvalue, '\n')
            
            results[i][j] = str(round(statistic, 3)) + pvalue_as_star(pvalue)
            
    df_results = pd.DataFrame(results, columns=groups, index=groups)
    
    # invert column order to make it easier to read (placing values in the diagonal)
    #df_results = df_results[reversed(df_results.columns)]
            
    # report on paper
    if export_to_latex:
        print(df_results.to_latex(index=True, float_format="%.4f"))
            
    return df_results



from scipy.stats import median_test
    
def run_median_test(df, group_by, export_to_latex=False, report_h0_acceptance=False, alpha=.05):
    
    groups = df[group_by].unique()        
    N_groups = len(groups)

    # initiate a matrix for pairwise results
    results = [["" for j in range(N_groups)] for i in range(N_groups)]

    # Calculate Wilcoxon Test pairwise
    for i in range(len(groups)):
        for j in range(i+1, len(groups)):
            
            # group i toxicity values
            group_i = groups[i]
            sample_i = df[df[group_by] == group_i]['TOXICITY'].tolist()
            
            # group j toxicity values
            group_j = groups[j]
            sample_j = df[df[group_by] == group_j]['TOXICITY'].tolist()
        
            statistic, pvalue, median, table = median_test(sample_i, sample_j)
            
            if report_h0_acceptance and pvalue >= alpha:
                print(groups[i], '(N = ' + str(len(sample_i)) + ') ', ' VS ', groups[j], '(N = ' + str(len(sample_j)) +')', '\tKS =', str(statistic) + '\tp-value =', pvalue, '\n')
            
            results[i][j] = str(round(statistic, 3)) + pvalue_as_star(pvalue)
            
    df_results = pd.DataFrame(results, columns=groups, index=groups)
    
    # invert column order to make it easier to read (placing values in the diagonal)
    #df_results = df_results[reversed(df_results.columns)]
            
    # report on paper
    if export_to_latex:
        print(df_results.to_latex(index=True, float_format="%.4f"))
            
    return df_results



from scipy.stats import kruskal
    
def run_kruskall_wallis_test(df, group_by, export_to_latex=False):
    
    groups = df[group_by].unique()

    results = []

    # Kruskall-Wallis Test
    samples = []
    for group in groups:
        sample = df[df[group_by] == group]['TOXICITY'].tolist()
        samples.append(sample)
    H, pvalue = kruskal(*samples)

    results.append({
        'H': H,
        'H (with p)': str(round(H, 4)) + pvalue_as_star(pvalue),
        'p-value': pvalue
    })
        
    results_df = pd.DataFrame(results)
    
    # report on paper
    if export_to_latex:
        print(results_df[['H (with p)']].to_latex(index=False, float_format="%.4f"))

    return results_df