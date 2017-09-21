"""
The eigenvalue method of Silver and Chan (1991)
Low level routines works on numpy arrays and shifts using samples (doesn't know about time)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ..core import core
from ..core.window import Window

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal, stats


    
def eigvalcov(data):
    """
    return sorted eigenvalues of covariance matrix
    lambda1 first, lambda2 second
    """
    return np.sort(np.linalg.eigvals(np.cov(data)))
    
    
def grideigval(x, y, **kwargs):
    """
    Grid search for splitting parameters applied to data.
    
    lags = 1-D array of sample shifts to search over, if None an attempt at finding sensible values is made
    degs = 1-D array of rotations to search over, if None an attempt at finding sensible values is made
    window = Window object (if None will guess an appropriate window)
    rcvcorr = receiver correction parameters in tuple (fast,lag) 
    srccorr = source correction parameters in tuple (fast,lag) 
    """
        
    if 'lags' not in kwargs:
        # default search
        maxlag = int(x.size / 10)
        maxlag = maxlag if maxlag%2==0 else maxlag + 1
        lags = 2 * np.rint(np.linspace(0,0.5*maxlag,30))
        kwargs['lags'] = np.unique(lags).astype(int)
        
    if 'degs' not in kwargs:
        # default search
        stepang = 3
        kwargs['degs'] = np.arange(-90,90,stepang)
        
    if 'window' not in kwargs:
        # make a window by guessing
        nsamps = int(x.size/2)
        nsamps = nsamps if nsamps%2==1 else nsamps + 1
        offset = 0
        kwargs['window'] = Window(nsamps,offset,tukey=None)
                    
    # grid of degs and lags to search over
    degs, lags = np.meshgrid(kwargs['degs'],kwargs['lags'])
    shape = degs.shape
    lam1 = np.zeros(shape)
    lam2 = np.zeros(shape)
    
    # avoid using "dots" in loops for performance
    rotate = core.rotate
    lag = core.lag
    unsplit = core.unsplit
    chop = core.chop
    
    # pre-apply receiver correction
    if 'rcvcorr' in kwargs:
        x,y = core.unsplit(x,y,*kwargs['rcvcorr'])
    
    # make function to do source correction (used in loop)
    if 'srccorr' in kwargs:
        def srccorr(x,y):
            return core.unsplit(x,y,*kwargs['srccorr'])
    else:
        def srccorr(x,y):
            # no source correction so do nothing
            return x,y
    
    for ii in np.arange(shape[1]):
        tx, ty = rotate(x,y,degs[0,ii])
        for jj in np.arange(shape[0]):
            # remove splitting so use inverse operator (negative lag)
            ux, uy = lag(tx,ty,-lags[jj,ii])
            # if requested -- post-apply source correction
            ux, uy = srccorr(ux,uy)
            # chop to analysis window
            ux, uy = chop(ux,uy,window=kwargs['window'])
            # measure eigenvalues of covariance matrix
            lam2[jj,ii], lam1[jj,ii] = eigvalcov(np.vstack((ux,uy)))
            
    return degs,lags,lam1,lam2,kwargs['window']

def ndf(y,window=None,detrend=False):
    """
    Estimates number of degrees of freedom using noise trace y.
    Uses the improvement found by Walsh et al (2013).
    """
        
    if detrend is True:
        # ensure no trend on the noise trace
        y = signal.detrend(y)

    if window is not None:
        # chop trace to window limits
        y = core.chop(y,window=window)
  
    Y = np.fft.fft(y)
    amp = np.absolute(Y)
    
    # estimate E2 and E4 following Walsh et al (2013)
    a = np.ones(Y.size)
    a[0] = a[-1] = 0.5
    E2 = np.sum( a * amp**2)
    E4 = (np.sum( (4 * a**2 / 3) * amp**4))
    
    ndf = 2 * ( 2 * E2**2 / E4 - 1 )
    
    return ndf
    
def ftest(lam2,ndf,alpha=0.05):
    """
    returns lambda2 value at 100(1-alpha)% confidence interval
    by default alpha = 0.05 = 95% confidence interval
    following Silver and Chan (1991)
    """
    lam2min = lam2.min()
    k = 2 # two parameters, phi and dt.
    # R = ((lam2 - lam2min)/k) /  (lam2min/(ndf-k))
    F = stats.f.ppf(1-alpha,k,ndf)
    lam2alpha = lam2min * ( 1 + (k/(ndf-k)) * F)
    return lam2alpha
    

     
