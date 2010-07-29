from scipy import log10
from scipy import sqrt
from scipy import optimize
from pylab import errorbar
from pylab import clf
from pylab import subplot
from pylab import plot
from pylab import text
from pylab import title
from pylab import *
from scipy import array
import os

def fit(xdata, ydata, yerr, band):
    '''Power law fitting based on www.scipy.org/Cookbook/FittingData'''

    powerlaw = lambda x, amp, index: amp*(x**index)
    line = lambda x, const, slope: const + x*slope


    logx = log10(xdata)
    #logy = ydata
    #logyerr = yerr/ydata


    fitfunc = lambda p, x: p[0] + p[1] * x
    errfunc = lambda p, x, y, err: (y-fitfunc(p,x))/err

    pinit = [10, 0]
    out = optimize.leastsq(errfunc,pinit,args=(logx, ydata, yerr), full_output = 1)

    pfinal = out[0]
    covar = out[1]
   
    print 'pfinal is' + str(pfinal)

    index = pfinal[1]
    amp = 10.0**pfinal[0]

    indexErr = sqrt(covar[0][0])
    ampErr = sqrt(covar[1][1])*amp

    #plotting data

    if band == 'h':
        plot(logx, line(logx, pfinal[0], pfinal[1]), color = 'green')
        errorbar(logx, ydata, yerr=yerr, fmt='k.', color = 'green', label = 'h') #Data
    elif band == 'j':
        plot(logx, line(logx, pfinal[0], pfinal[1]), color = 'blue')
        errorbar(logx, ydata, yerr=yerr, fmt='k.', color = 'blue', label = 'j') #Data
    elif band == 'k':
        plot(logx, line(logx, pfinal[0], pfinal[1]), color = 'red')
        errorbar(logx, ydata, yerr=yerr, fmt='k.', color = 'red', label = 'k') #Data
        

    title('Best Fit Power Law')
    xlabel('Log Time After Burst (s)')
    ylabel('Magnitude')

    ax = matplotlib.pyplot.gca()
    ax.set_ylim(ax.get_ylim()[::-1])   

def fitplot(dict,exclude=[]): 
    '''Takes a dictionary containing photometry results (such as the output from q_super_photometry.photreturn) and solves for a power law fitting. This function will graph the power law fit and the data points on magnitude vs. log(t_mid) space.'''
    clf()

    kdict = {}
    hdict = {}
    jdict = {}

    for keys in dict:
        if keys not in exclude:
            if 'k' in keys:
                kdict.update({keys:dict[keys]})
            elif 'h' in keys:
                hdict.update({keys:dict[keys]})
            elif 'j' in keys:
                jdict.update({keys:dict[keys]})

    data = []
    err = []

    time = []
    terr = []


#KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK
    timelist = []
    for key in kdict:
        timelist.append((kdict[key]['t_mid'][0], key))
    timelist.sort()
    
    for tup in timelist:
        values = kdict[tup[1]]
        if 'targ_mag' not in values:
            pass
            #data += [values['upper_green'][0]]
            #err += [values['upper_green'][1]]
        elif isnan(values['targ_mag'][0]):
            pass
        else:
            data += [values['targ_mag'][0]]
            err += [values['targ_mag'][1]]
       
        if 'targ_mag' not in values:
            pass
        elif isnan(values['targ_mag'][0]):
            pass
        else:
            time += [values['t_mid'][0]]

    karr = array(data)
    tarr = array(time)
    aerr = array(err) 
    print 'k error is'
    print aerr
    print aerr.mean()

    fit(tarr, karr, aerr, 'k')

#HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
    
    data = []
    err = []
    time = [] 

    timelist = []
    for key in hdict:
        timelist.append((hdict[key]['t_mid'][0], key))
    timelist.sort()
    
    for tup in timelist:
        values = hdict[tup[1]]
        if 'targ_mag' not in values:
            pass
            #data += [values['upper_green'][0]]
            #err += [values['upper_green'][1]]
        elif isnan(values['targ_mag'][0]):
            pass
        else:
            data += [values['targ_mag'][0]]
            err += [values['targ_mag'][1]]

        if 'targ_mag' not in values:
            pass
        elif isnan(values['targ_mag'][0]):
            pass
        else:
            time += [values['t_mid'][0]]

    harr = array(data)
    tarr = array(time)
    aerr = array(err) 
    print 'h error is'
    print aerr
    print aerr.mean()

    fit(tarr, harr, aerr, 'h')

#JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ

    data = []
    err = []
    time = []
   
    timelist = []
    for key in jdict:
        timelist.append((jdict[key]['t_mid'][0], key))
    timelist.sort()
    
    for tup in timelist:
        values = jdict[tup[1]]
        if 'targ_mag' not in values:
            pass
            #data += [values['upper_green'][0]]
            #err += [values['upper_green'][1]]
        elif isnan(values['targ_mag'][0]):
            pass
        else:
            data += [values['targ_mag'][0]]
            err += [values['targ_mag'][1]]

        if 'targ_mag' not in values:
            pass
        elif isnan(values['targ_mag'][0]):
            pass
        else:
            time += [values['t_mid'][0]]

    jarr = array(data)
    tarr = array(time)
    aerr = array(err)
    print 'j error is'
    print aerr
    print aerr.mean()
    
    fit(tarr, jarr, aerr, 'j') 

#putting on legend and saving the plot
    
    legend()
    storepath = os.environ.get("Q_DIR") + '/store/'
    unique_name = dict.keys()[0].split('_')[2]
    filepath = storepath + unique_name + '_power_law_fit.png'
    savefig(filepath)
