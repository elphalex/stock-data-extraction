# -*- coding: utf-8 -*-
"""
Created on Sat Oct  9 17:23:51 2021

This script extracts financial data for a given stock ticker from Morningstar, processes it,
and performs various financial calculations such as Discounted Cash Flow, Benjamin Graham Formula,
and Dividend Discount Model.

"""

from pattern.web import URL
import pandas as pd
import os
import sys

def extract_data(stock_ticker):
    url_base = 'http://financials.morningstar.com/ajax/exportKR2CSV.html?&callback=?&t='
    url_end = '&region=usa&culture=en-US&cur=&order=asc'
    stock_exchange_list = ['XNAS:', 'XNYS:', 'PINX:'] 
    for exchange in stock_exchange_list:
        test = URL(url_base + exchange + stock_ticker + url_end)
        if sys.getsizeof(test.download()) > 35:
            break
    temp_data = 'temp.csv'
    f = open(temp_data, mode='w')
    try:
        f.write(test.download())
    except:
        raise IOError('There was an error processing this data')
        sys.exit(1)
    f.close()
    try:
        stock_data_df = pd.read_csv(temp_data, header=2, thousands=',', index_col=0)
    except:
        raise IOError('Problem downloading files')
        os.remove(temp_data)
        sys.exit(1)
    os.remove(temp_data)
    stock_data_df = stock_data_df.transpose()
    return stock_data_df

import numpy as np

def discount_cash_flow(fcf, proj_rate1, proj_rate2, discount, shares, beta):
    fcf = np.array(fcf).astype(float)
    n = len(fcf) - 1
    if fcf[0] < 0:
        fcf[0] = np.mean(fcf)
    cagr = (((fcf[n] / fcf[0]) ** (1.0 / n)) - 1)
    val1numbers = np.zeros(shape=100)
    val2numbers = np.zeros(shape=100)
    d = (2.5 + beta * (9.11 - 2.5)) / 100.0

    for i in range(0, 100):
        proj = fcf[9] * ((1 + proj_rate1) ** (np.arange(1, 11))) + np.random.normal(scale=np.std(fcf, ddof=1), size=10)
        proj2 = proj[9] * ((1 + proj_rate2) ** (np.arange(1, 11))) + np.random.normal(scale=np.std(fcf, ddof=1), size=10)
        projtotal = np.concatenate([proj, proj2])
        dis = projtotal / ((1 + discount) ** np.arange(1, 21))
        dis2 = projtotal / ((1 + d) ** np.arange(1, 21))
        val1 = np.sum(dis) / shares
        val1numbers[i] = val1
        val2 = sum(dis2) / shares
        val2numbers[i] = val2
    return cagr, val1numbers, val2numbers

def ben_graham_formula(eps, proj_growth, risk_free_rate=0.025, safe_eps=False, safe_growth=False, adjust=True):
    eps = np.array(eps)
    adjusted_eps = np.mean(eps) if adjust else None
    const = 7 if safe_eps else 8
    g = 1.5 if safe_growth else 2

    val = (eps[10] * (const + g * (proj_growth * 100) * 4.4)) / (risk_free_rate * 100)
    if adjust:
        val_adj = (adjust * (const + g * (proj_growth * 100) * 4.4)) / (risk_free_rate * 100)
    else:
        val_adj = None
    return val, val_adj

def div_discount_model(current_div, discount, div_growth_rate1, div_growth_rate2, const_growth, div_period1=5, div_period2=5):
    proj1 = current_div * ((1.0 + div_growth_rate1) ** np.arange(1, div_period1 + 1))
    proj2 = proj1[len(proj1) - 1] * ((1.0 + div_growth_rate2) ** np.arange(1, div_period2 + 1))
    const = np.array([(proj2[len(proj2) - 1] * (1 + const_growth)) / (discount - const_growth)])
    dis = np.concatenate([proj1, proj2, const]) / ((1 + discount) ** np.arange(1, len(proj1) + len(proj2) + len(const) + 1))
    val = dis.sum()    
    return val

def gordon_growth_model(current_div, const_growth, discount):
    return (current_div * (1 + const_growth)) / (discount - const_growth)
