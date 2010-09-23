import pylab
import scipy
import matplotlib

def ColorScatterExample():
    x=scipy.rand(20)
    y=scipy.rand(20)
    z=scipy.rand(20)*50
    ColorScatter(x,y,z,cmap='jet',colorbar=True)


def ColorScatter(x,y,z=None,cmap='jet',colorbar=True):
    if z != None:
        sc = pylab.scatter(x,y,c=z,cmap=cmap)
        if colorbar: pylab.colorbar(sc)
    else:
        sc = pylab.scatter(x,y)

def cmap_discretize(cmap, N):
    """Return a discrete colormap from the continuous colormap cmap.
    
        cmap: colormap instance, eg. cm.jet. 
        N: Number of colors.
    
    Example
        x = resize(arange(100), (5,100))
        djet = cmap_discretize(cm.jet, 5)
        imshow(x, cmap=djet)
    """

    cdict = cmap._segmentdata.copy()
    # N colors
    colors_i = linspace(0,1.,N)
    # N+1 indices
    indices = linspace(0,1.,N+1)
    for key in ('red','green','blue'):
        # Find the N colors
        D = array(cdict[key])
        I = interpolate.interp1d(D[:,0], D[:,1])
        colors = I(colors_i)
        # Place these colors at the correct indices.
        A = zeros((N+1,3), float)
        A[:,0] = indices
        A[1:,1] = colors
        A[:-1,2] = colors
        # Create a tuple for the dictionary.
        L = []
        for l in A:
            L.append(tuple(l))
        cdict[key] = tuple(L)
    # Return colormap object.
    return matplotlib.colors.LinearSegmentedColormap('colormap',cdict,1024)

def GridDataExample():
    import numpy as np
    from matplotlib.mlab import griddata
    import matplotlib.pyplot as plt
    import numpy.ma as ma
    from numpy.random import uniform
    # This was stolen from somewhere
    # make up some randomly distributed data
    npts = 200
    x = uniform(-2,2,npts)
    y = uniform(-2,2,npts)
    z = x*np.exp(-x**2-y**2)
    # define grid.
    xi = np.linspace(-2.1,2.1,100)
    yi = np.linspace(-2.1,2.1,100)
    # grid the data.
    zi = griddata(x,y,z,xi,yi)
    # contour the gridded data, plotting dots at the randomly spaced data points.
    CS = plt.contour(xi,yi,zi,15,linewidths=0.5,colors='k')
    CS = plt.contourf(xi,yi,zi,15,cmap=plt.cm.jet)
    plt.colorbar() # draw colorbar
    # plot data points.
    plt.scatter(x,y,marker='o',c='b',s=5)
    plt.xlim(-2,2)
    plt.ylim(-2,2)
    plt.title('griddata test (%d points)' % npts)
    plt.show()
