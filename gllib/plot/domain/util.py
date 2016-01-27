#-*- coding: utf-8 -*-
"""
domain utilities
:author: Nicolas 'keksnicoh' Heimann 
"""
import numpy as np 
from scipy.fftpack import fft

def total_mean():
    def _transform(data):
        mean_data = np.zeros_like(data)
        if mean_data.shape[1] == 2:
            for i, point in enumerate(data):
                if i == 0:
                    mean_data[i][0] = 0
                    mean_data[i][1] = 0
                else:
                    time_step = data[i][0] - data[i-1][0]
                    mean_data[i][0] = time_step*i
                    mean_data[i][1] = float(i)/(i+1.0)*mean_data[i-1][1] + 1.0/(i+1.0)*data[i][1];
            return mean_data 
        elif mean_data.shape[1] == 1:
            
            for i, point in enumerate(data):

                if i == 0:
                    mean_data[i][0] = 0
                else:
                    mean_data[i][0] = float(i)/(i+1.0)*mean_data[i-1][0] + 1.0/(i+1.0)*data[i][0];
            return mean_data 
        else:
            raise ValueError('invalid shape ...')
    return _transform

def moving_avarage(nsamples=50):
    def _transform(data):
        mean_data = np.zeros_like(data)
        for i, point in enumerate(data):
            if i == 0:
                mean_data[i][0] = 0
                mean_data[i][1] = 0
            else:
                time_step = data[i][0] - data[i-1][0]
                mean_data[i][0] = time_step*i
                mean_data[i][1] = mean_data[i-1][1] + data[i][1]/nsamples - mean_data[max(0,i-nsamples)][1]/nsamples;
                #mean_data[i][1] = float(i)/(i+1.0)*mean_data[i-1][1] + 1.0/(i+1.0)*data[i][1];
        return mean_data 
    return _transform


def domain_mapper(mapper):
    def _mapper(data):
        new_data = np.zeros_like(data)
        for i, row in enumerate(data):
            new_data[i] = mapper(row)
        return new_data
    return _mapper

def fft1d():
    def _transform(data):
        if len(data) < 2:
            return np.zeros(data.shape, dtype=np.float32)
        time_step = np.abs(data[1][0]-data[0][0])
        nsamples = len(data)

        yf = 2.0/nsamples * np.abs(fft(data[:,1])[0:0.5*nsamples])
        xf = np.linspace(0.0, 1.0/time_step, nsamples/2)

        fft_data = np.empty((nsamples/2,2),dtype=np.float32)
        fft_data[:,0] = xf
        fft_data[:,1] = yf

        return fft_data
    return _transform


def psd():
    def _transform(data):
        if len(data) < 2:
            return np.zeros(data.shape, dtype=np.float32)
        time_step = np.abs(data[1][0]-data[0][0])
        nsamples = len(data)

        yf = fft(data[:,1])        
        yf = 1.0/(nsamples*time_step)*(np.abs(yf)**2)[0:0.5*nsamples]
        xf = np.fft.fftfreq(nsamples, time_step)[0:0.5*nsamples]

        #np.linspace(0.0, 1.0/time_step, nsamples/2)

        fft_data = np.empty((nsamples/2,2),dtype=np.float32)
        fft_data[:,0] = xf
        fft_data[:,1] = yf

        return fft_data
    return _transform