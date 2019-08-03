# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 17:17:08 2019

@author: tais
"""

# Import libs
import os
import pandas as pd
import numpy as np

def GetCatchmentCumulPopByISO(in_file, in_sep=';', out_file='', out_sep='', col_prefix="ISO", df_return=False):
    """Get one line per health facility with cumulative population per isochrone"""
    # Parameters for outputfile (path and sep)
    if out_file == '':
        path, ext = os.path.splitext(in_file)
        out_file = "%s_clean%s"%(path,ext)
    if out_sep == '':
        out_sep = in_sep
    # Import input csv
    df = pd.read_csv(in_file, sep=in_sep)
    # Create two new columns with the ID of health facility and isochrone value
    df['HF_cat'] = df.apply (lambda row: int(row['label'].split(';')[0].split(" ")[-1]), axis=1)
    df['ISO_cat'] = df.apply (lambda row: int(row['label'].split(';')[1].split(" ")[-1]), axis=1)
    # Keep only required columns and sort by HF id and Isochrone value
    df = df[['HF_cat','ISO_cat','sum']]
    df.sort_values(['HF_cat','ISO_cat'],inplace=True)
    # Compute cumulated population by increasing isochrone for each HF
    cumul_by_HF = pd.Series([])
    list_of_HF = list(set(df['HF_cat'].values))
    for HF in list_of_HF:
        df_HF = df.loc[df['HF_cat'] == HF]
        a = df_HF['sum'].cumsum(axis=0)
        cumul_by_HF = cumul_by_HF.add(a, fill_value=0)
    df['cumul_sum'] = cumul_by_HF
    # Pivot the table
    df_pivot = pd.pivot_table(df, values='cumul_sum', index='HF_cat', columns='ISO_cat', aggfunc=np.min, fill_value=0)
    df_pivot.rename(columns=lambda x: '%s_%s'%(col_prefix,x), inplace=True)
    # Add column with total population
    ISO_column_name = [ x for x in list(df_pivot)]
    df_pivot['%s_TOT'%col_prefix] = df_pivot.iloc[:,-1]
    ISO_column_name.append('%s_TOT'%col_prefix)
    # Add percentage of population
    for name in ISO_column_name:
        iso_value = name[len(col_prefix)+1:]
        df_pivot['%s_prct%s'%(col_prefix,iso_value)] = (df_pivot['%s'%name]/df_pivot['%s_TOT'%col_prefix])*100
    # Export table as csv
    df_pivot.to_csv(out_file, sep=out_sep)
    # Return
    if df_return:
        return df_pivot

def GetCatchmentPopByISO(in_file, in_sep=';', out_file='', out_sep='', col_prefix="ISO", df_return=False):
    """Get one line per health facility with population per isochrone"""
    # Parameters for outputfile (path and sep)
    if out_file == '':
        path, ext = os.path.splitext(in_file)
        out_file = "%s_clean%s"%(path,ext)
    if out_sep == '':
        out_sep = in_sep
    # Import input csv
    df = pd.read_csv(in_file, sep=in_sep)
    # Create two new columns with the ID of health facility and isochrone value
    df['HF_cat'] = df.apply (lambda row: int(row['label'].split(';')[0].split(" ")[-1]), axis=1)
    df['ISO_cat'] = df.apply (lambda row: int(row['label'].split(';')[1].split(" ")[-1]), axis=1)
    # Keep only required columns and sort by HF id and Isochrone value
    df = df[['HF_cat','ISO_cat','sum']]
    df.sort_values(['HF_cat','ISO_cat'],inplace=True)
    # Pivot the table
    df_pivot = pd.pivot_table(df, values='sum', index='HF_cat', columns='ISO_cat', aggfunc=np.min, fill_value=0)
    df_pivot.rename(columns=lambda x: '%s_%s'%(col_prefix,x), inplace=True)
    # Add column with total population
    ISO_column_name = [ x for x in list(df_pivot)]
    df_pivot['%s_TOT'%col_prefix] = sum([df_pivot['%s'%name] for name in ISO_column_name])
    ISO_column_name.append('%s_TOT'%col_prefix)
    # Add percentage of population
    for name in ISO_column_name:
        iso_value = name[len(col_prefix)+1:]
        df_pivot['%s_prct%s'%(col_prefix,iso_value)] = (df_pivot['%s'%name]/df_pivot['%s_TOT'%col_prefix])*100
    # Export table as csv
    df_pivot.to_csv(out_file, sep=out_sep)
    # Return
    if df_return:
        return df_pivot
