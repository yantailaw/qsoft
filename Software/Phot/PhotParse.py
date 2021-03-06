import copy
import matplotlib.pyplot as plt
import numpy as np
from MiscBin.q import maglist2fluxarr
from MiscBin.q import flux2abmag
from MiscBin.q import mag2alpha
from matplotlib import rc
import os
import sys
from ast import literal_eval

if not os.environ.has_key("Q_DIR"):
    print "You need to set the environment variable Q_DIR to point to the"
    print "directory where you have WCSTOOLS installed"
    sys.exit(1)
splinedir = os.environ.get("Q_DIR") + '/trunk/Software/Modelling/'
storepath = os.environ.get("Q_DIR") + '/store/'
loadpath = os.environ.get("Q_DIR") + '/load/'


class ObjBlock:
    '''
    Block of ObsBlocks
    '''
    def __init__(self):
        self.obsdict = {}
        self.utburst = None
        self.galebv = None
        self.redshift = None
        self.xraydict = None
        self.name = None
        
    def updateObj(self,indict):
        if not self.name:
            if 'name' in indict:
                self.name = indict['name']
                
        if not self.utburst:
            if 'utburst' in indict:
                self.utburst = indict['utburst']
        else:
            if 'utburst' in indict:
                if self.utburst != indict['utburst']:
                    raise ValueError('utburst times do not match!')
        
        if not self.galebv:
            if 'galebv' in indict:
                try:
                    self.galebv = float(indict['galebv'])
                except:
                    self.galebv = None
        else:
            if 'galebv' in indict:
                if self.galebv != float(indict['galebv']):
                    raise ValueError('galebv values do not match!')
                    
        
        if not self.redshift:
            if 'redshift' in indict:
                try:
                    self.redshift = float(indict['redshift'])
                except:
                    self.redshift = None
        else:
            if 'redshift' in indict:
                if self.redshift != float(indict['redshift']):
                    if str(self.redshift) != str(indict['redshift']):
                        raise ValueError('redshift values do not match!')
        
        if not self.xraydict:
            if 'xraydict' in indict:
                if indict['xraydict'] != 'unknown':
                    # special handling for xray dict; convert from str to dict
                    self.xraydict = literal_eval(indict['xraydict']) # literal_eval is safe!
                
        
        name = indict['source'] + '_' + indict['filt']
        if not name in self.obsdict:
            newobs = ObsBlock(indict)
            self.obsdict.update({name:newobs})
        else:
            self.obsdict[name].updateObs(indict)
    
    def CalculateFlux(self):
        '''Loop through all the ObsBlock instances in the ObjBlock and 
        calculate the flux for each, assigning them as attributes of the 
        ObsBlock.
        '''
        from Modelling.ExtinctModel import CorrectFluxForGalExt
        
        for key, ob in self.obsdict.iteritems():
            if ob.filt != None:
                ob.fluxarr,ob.fluxerrarr = \
                    maglist2fluxarr(ob.maglist,ob.magerrlist,ob.filt,singlefilt=True)
                if self.galebv != None:
                    # if we know galebv, do gal corrected flux conversion
                    # do we want to do change this function to handle wave objects? Nah..
                    #array of the same wavelength in angstroms
                    wavearr = np.zeros(len(ob.maglist)) + ob.filt.wave_A 
                    ob.gcfluxarr,ob.gcfluxerrarr = \
                        CorrectFluxForGalExt(self.galebv,wavearr,ob.fluxarr,ob.fluxerrarr)
            elif ob.fluxconv != None:
                print "Doing direct flux conversion from count rates for %s of %f" % (ob.source,ob.fluxconv)
                ob.fluxarr = np.array(ob.ctratelist)*ob.fluxconv
                ob.fluxerrarr = np.array(ob.ctrateerrlist)*ob.fluxconv                
            else:
                print "No filter for %s, Skipping flux conversion" % (key)
    
    def PlotXRTlc(self,show=True,save=True,legend=True,
        obslist=['BAT_unknown','XRT_unknown','PAIRITEL_K'],
        xlimits=None,ylimits=None,figsize=None):
        '''
        show: Plot to screen
        save: Save to disk
        legend: include a legend
        obslist: parameters to plot
        xlimits: optional tuple of limits (observer frame)
        ylimits: optional tuple of limits (flux units)
        figsize: figsize tuple in inches
        '''
        # set font
        # EDIT TO SHOW MORE THAN JUST BAT/XRT/KBAND
        
        
        rc('font', family='Times New Roman')
        
        if not figsize:
            fig=plt.figure()
        else:
            fig=plt.figure(figsize=figsize)
        
        ax=fig.add_axes([0.1,0.1,0.8,0.8])
        ax.loglog()
        
        if not 'XRT_unknown' in self.obsdict:
            print 'Cannot find XRT data; skipping plot'
            return
        
        
        
        for obstr in obslist:
            ob = self.obsdict[obstr]
            label= obstr.replace('_',' ')
            label= label.replace(' unknown','')
            detectinds = np.array([not a for a in ob.isupperlist])     
            ax.errorbar(np.array(ob.tmidlist)[detectinds],ob.fluxarr[detectinds],yerr=ob.fluxerrarr[detectinds], color=ob.color, fmt=ob.marker, label=label)
        

        # COPY FROM PlotLC
        old_ylim=ax.get_ylim() # saving for later, as gets modified.. 
        
        ax2=ax.twinx()
        ax3=ax.twiny()
        ax3.loglog()
        
        if xlimits:
            ax.set_xlim(xlimits)
        if ylimits:
            ax.set_ylim(ylimits)
            
        xobstime=ax.get_xlim()
        xresttime0=xobstime[0]/(1+self.redshift)
        xresttime1=xobstime[1]/(1+self.redshift)
        xrest=(xresttime0,xresttime1)
        ax3.set_xlim(xrest)
        
        # duplicate axis for AB mag
        ax.set_ylim(old_ylim)
        ylimflux=ax.get_ylim()
        ylimmag0=flux2abmag(ylimflux[0])
        ylimmag1=flux2abmag(ylimflux[1])
        ylimmag=(ylimmag0,ylimmag1)
        ax2.set_ylim(ylimmag)
        
        # Label the axes
        ax.set_ylabel(r'$F_\nu$ (uJy)',size=16)
        zsubscript=str(self.redshift)
        topxlabel = r'$t_{z=%s}$ (s)'  % zsubscript
        ax.set_xlabel(r'$t$ (s)')
        ax2.set_ylabel('AB Mag',size=16)
        ax3.set_xlabel(topxlabel,size=16)
        
        ax.legend(loc=3,numpoints=1,frameon=False)
        if save:
            filepath = storepath + 'LCxrt_' + self.name.replace('\,','') + '.png' 
            fig.savefig(filepath)
            filepath = storepath + 'LCxrt_' + self.name.replace('\,','') + '.pdf' 
            fig.savefig(filepath)
        if show:        
            fig.show()
        
    
    def PlotResiduals(self,show=True,save=True):
        ## HACK
        pass
    
    def WriteCondensedTable(self):
        contentlist = []
        import pandas as pd
        
        
        phot_table = pd.DataFrame([[0.0,0.0,99.0,99.0,99.0,99.0,99.0,99.0]],columns=['Tmid','exposure','Kmag','Kmagerr','Hmag','Hmagerr','Jmag','Jmagerr'])
        
        
        table_list = []
        # loop through each and build a pandas dataframe to then merge
        for ob in self.obsdict.itervalues():
            
            assert ob.source == "PAIRITEL" # use this only for pairitel tables
            
            assert len(ob.tmidlist) == len(ob.explist)
            assert len(ob.tmidlist) == len(ob.maglist)
            assert len(ob.tmidlist) == len(ob.magerrlist)
            assert len(ob.tmidlist) == len(ob.isupperlist)
            strtmidlist = ["%.2f" % tmid for tmid in ob.tmidlist]
            strexplist = ["%.1f" % exp for exp in ob.explist]
            strmaglist = ["%.2f" % mag if not ob.isupperlist[ob.maglist.index(mag)] == True else '> %.2f' % mag for mag in ob.maglist]
            strmagerrlist = ["%.2f" % magerr if not ob.isupperlist[ob.magerrlist.index(magerr)] == True else '...' for magerr in ob.magerrlist]            
            assert len(strtmidlist) == len(strexplist)
            assert len(strmaglist) == len(strexplist)
            assert len(strmagerrlist) == len(strexplist)
            
            curr_magstr = ob.filtstr[0] + 'mag'
            curr_errstr = ob.filtstr[0] + 'magerr'
            
            tmp_phot_table = pd.DataFrame({'Tmid':strtmidlist,'exposure':strexplist,curr_magstr:strmaglist,curr_errstr:strmagerrlist})
            
            table_list.append(tmp_phot_table)
            # count = 0 
            # while count < len(strexplist):
            #     count += 1 
        self.table_list = table_list
        
        assert len(self.table_list) <= 3 # Pairitel has only 3 filters. Could just be merging 2, though.
        assert len(self.table_list) > 0 # at least one
        
        if len(self.table_list) == 1: 
            print "Warning! Only one table found in WriteCondensedTable."
            self.phot_table = self.table_list[0]
        else:
            phot_table = self.table_list[0]
            for table in self.table_list[1:]:
                phot_table = phot_table.merge(table,how='outer',on=["Tmid","exposure"])
            self.phot_table=phot_table
        
        self.phot_table[['Tmid']] = self.phot_table[['Tmid']].astype(float) # convert column to float values before sorting
        self.phot_table = self.phot_table.fillna('nan') # replacing numeric NaNs with string values
        self.phot_table = self.phot_table.sort('Tmid') # sorting by time
        
        #define formatters to print
        stringformatter  = lambda x: '$%s$ & ' % x
        endformatter = lambda x: '$%s$ \\\\' % x
        
        # create a dictionary of formatters for output 
        formatterdict = {'Tmid':stringformatter,'exposure':stringformatter}
        columnlist = ['Tmid','exposure']  
        colhead1 = "\\colhead{$t_{\\rm mid}$} & \\colhead{Exp} "
        colhead2 = "\\colhead{(s)}        & \\colhead{(s)} "
        if 'Jmag' in self.phot_table:
            formatterdict.update({'Jmag':stringformatter,'Jmagerr':stringformatter})
            columnlist.append('Jmag')
            columnlist.append('Jmagerr')
            colhead1+="& \\colhead{$J$ Mag} & \\colhead{$J$ Mag Err} "
            if 'Hmag' not in self.phot_table and 'Kmag' not in self.phot_table:
                formatterdict['Jmagerr'] = endformatter
        if 'Hmag' in self.phot_table:
            formatterdict.update({'Hmag':stringformatter,'Hmagerr':stringformatter})
            columnlist.append('Hmag')
            columnlist.append('Hmagerr')
            colhead1+="& \\colhead{$H$ Mag} & \\colhead{$H$ Mag Err} "
            if 'Kmag' not in self.phot_table:
                formatterdict['Hmagerr'] = endformatter
        if 'Kmag' in self.phot_table:
            formatterdict.update({'Kmag':stringformatter,'Kmagerr':endformatter})
            columnlist.append('Kmag')
            columnlist.append('Kmagerr')
            colhead1+="& \\colhead{$K$ Mag} & \\colhead{$K$ Mag Err} "
        
        out_str = self.phot_table.to_string(index=False,index_names=False,
            header=False,columns=columnlist,formatters=formatterdict)
        
        self.phot_table_tex = out_str
        
        linestring = 'l'*len(self.phot_table.columns)
        colhead2 += '& \\colhead{} & \\colhead{$1\\sigma$} '*((len(self.phot_table.columns)-2)/2)
        # FIXME
        # Tmid    exposure    Kmag    Kmagerr Hmag    Hmagerr Jmag    Jmagerr
        
        header='''
    \\begin{deluxetable}{%s}
    \\tablecaption{Photometry of %s}
    \\tabletypesize{\scriptsize}
    \\tablewidth{0pt}
    \\tablehead{
    %s  \\\\
    %s   }
    \\startdata

    ''' % (linestring,self.name,colhead1,colhead2)
    
        footer= '''
    \\enddata
    \\tablecomments{Photometric observations of %s. Time is presented as the time since GRB trigger. Values in this table have not been corrected for the expected Galactic extinction of $E(B-V) = %.3f$ }
    \\label{tab:%sphot}
    \\end{deluxetable}
        ''' % (self.name, self.galebv, self.name.replace("\,",""))
    
        content = self.phot_table_tex
        
        tabletext = header + content + footer
        
        try:
            if not self.name:
                outname = ''
            else:
                outname = str(self.name)    
            filename = storepath + 'ptel' + outname.replace("\\,","") + '_photometry.tex'
            f = open(filename,'w')
            f.write(tabletext)
            f.close()

            print ''
            print "Wrote Condensed Pairitel photometry table to storepath"
        except:
            print "FAILED TO WRITE PAIRITEL PHOTOMETRY TABLE"
        
    def WriteTable(self):
        contentlist = []
        
        
        
        for ob in self.obsdict.itervalues():
            assert len(ob.tmidlist) == len(ob.explist)
            assert len(ob.tmidlist) == len(ob.maglist)
            assert len(ob.tmidlist) == len(ob.magerrlist)
            assert len(ob.tmidlist) == len(ob.isupperlist)
            strtmidlist = ["%.2f" % tmid for tmid in ob.tmidlist]
            strexplist = ["%.1f" % exp for exp in ob.explist]
            strmaglist = ["%.2f" % mag if not ob.isupperlist[ob.maglist.index(mag)] == True else '> %.2f' % mag for mag in ob.maglist]
            strmagerrlist = ["%.2f" % magerr if not ob.isupperlist[ob.magerrlist.index(magerr)] == True else '...' for magerr in ob.magerrlist]            
            assert len(strtmidlist) == len(strexplist)
            assert len(strmaglist) == len(strexplist)
            assert len(strmagerrlist) == len(strexplist)
            
            count = 0 
            while count < len(strexplist):
                # newstring=inst  filt  tmid   expt   mag    magerr
                newstring = '%s & $%s$ & $%s$ & $%s$ & $%s$ & $%s$ \\\\' % (ob.source,ob.filtstr,strtmidlist[count],strexplist[count],strmaglist[count],strmagerrlist[count])
                contentlist.append(newstring)
                count+=1

        header='''
    \\begin{deluxetable}{llllllll}
    \\tablecaption{Photometry of %s}
    \\tabletypesize{\scriptsize}
    \\tablewidth{0pt}
    \\tablehead{
    \\colhead{Instrument} & \\colhead{Filter} & \\colhead{$t_{\\rm mid}$} & \\colhead{Exp} & \\colhead{Mag} & \\colhead{MagErr}  \\\\
    \\colhead{}           & \\colhead{}    & \\colhead{(s)}        & \\colhead{(s)}    & \\colhead{} & \\colhead{$1\\sigma$ }}
    \\startdata

    ''' % (self.name)

        footer= '''
    \\enddata
    \\tablecomments{Photometric observations of %s. Time is presented as the time since GRB trigger. Values in this table have not been corrected for the expected Galactic extinction of $E(B-V) = %.3f$ }
    \\label{tab:%sphot}
    \\end{deluxetable}
        ''' % (self.name, self.galebv, self.name.replace("\,",""))

        # do really naiive sorting of the list
        contentlist.sort()
    
        content = ''
        for contentline in contentlist:
            content += ''' %s
    ''' % contentline

        tabletext = header + content + footer
        try:
            if not self.name:
                outname = ''
            else:
                outname = str(self.name)    
            filename = storepath + outname.replace("\\,","") + '_photometry.tex'
            f = open(filename,'w')
            f.write(tabletext)
            f.close()

            print ''
            print "Wrote photometry table to storepath"
        except:
            print "FAILED TO WRITE PHOTOMETRY TABLE"    
            
    def PlotLC(self,show=True,save=True,legend=True,residualscale=False,
        xlimits=None,ylimits=None,figsize=(13,8),incl_xrt=False):
        '''
        show: Plot to screen
        save: Save to disk
        legend: include a legend
        residualscale: BETA. CURRENTLY ONLY FOR USE WITH GRB120119A. HACK.
        xlimits: optional tuple of limits (observer frame)
        ylimits: optional tuple of limits (flux units)      
        figsize: figsize tuple in inches  
        '''
        # set font
        
        rc('font', family='Times New Roman')
        
        fig=plt.figure(figsize=figsize)
        ax=fig.add_axes([0.1,0.1,0.8,0.8])
        ax.loglog()
        
        # Plot the XRT data if desired
        if incl_xrt:
            obslist = ['BAT_unknown','XRT_unknown']
            for obstr in obslist:
                ob = self.obsdict[obstr]
                label= obstr.replace('_',' ')
                label= label.replace(' unknown','')
                detectinds = np.array([not a for a in ob.isupperlist])     
                ax.errorbar(np.array(ob.tmidlist)[detectinds],ob.fluxarr[detectinds],yerr=ob.fluxerrarr[detectinds], color=ob.color, fmt=ob.marker, label=label)
            
            leg=ax.legend(loc=3,borderaxespad=1.2,numpoints=1,frameon=False)
            from pylab import setp
            setp(leg.get_texts(),fontsize=20)
            setp(leg.get_title(),fontsize=20)
        
        ## HACK THiS IS AWFUL AND REMOVES DATA. for use ONLY for one time plots
        if residualscale:
            # first remove the xrt and bat data if it exists
            removelist = ['BAT_unknown','XRT_unknown']
            for key in removelist:
                if key in self.obsdict:
                    del(self.obsdict[key])
            
            
            from Modelling.ExtinctModel import CorrectFluxForGalExt
            
            filtlist=['K','H','J',"z'",'I',"i'",'R',"r'",'V','B'] # liverpool are just estimates!
            
            wave_Alist = []
            # loop through and grab the wavlengths for each filter
            for filttt in filtlist:
                for key, ob in self.obsdict.iteritems():
                    if ob.filtstr == filttt:
                        if ob.filt.wave_A not in wave_Alist:
                            wave_Alist.append(ob.filt.wave_A)
            
            wave_Alist = np.array(wave_Alist)
            removelist=[]
            fluxconv_uncorr = np.array([4312.1,2522.7,1358.6,654.0,456.1,340.6,193.6,160.6,109.9,45])
            fluxconv_uncorrerr=np.array([145.,80.,45.,26.,19,16.,8.2,6.7,5.1,2.5])
            fluxconv,fluxconverr = CorrectFluxForGalExt(self.galebv,wave_Alist,fluxconv_uncorr,fluxconv_uncorrerr)
            fluxconv = list(fluxconv)
            
            sed=zip(filtlist,fluxconv)
            for key, ob in self.obsdict.iteritems():
                if ob.filtstr not in filtlist:
                    removelist.append(key)
                else:
                    index = filtlist.index(ob.filtstr)
                    ob.gcfluxarr*=fluxconv[0]/fluxconv[index]
                    ob.gcfluxerrarr*=fluxconv[0]/fluxconv[index]
            for key in removelist:
                del(self.obsdict[key])
        ##HACK
        
        
        # get list of all sources of observations for use in legend-making
        sources = {}
        filters = []
        for key, ob in self.obsdict.iteritems():
            if ob.filt != None:
                if ob.filtstr not in filters:
                    filters.append(ob.filtstr)
                detectinds = np.array([not a for a in ob.isupperlist])
                if detectinds.any(): # only plot here if we have at least one detection
                    if ob.source not in sources: 
                        sources.update({ob.source:1}) #collecting number of detections for each filter for legend
                    else:
                        sources[ob.source]+=1
        print sources
        
        #HACK to get most number of sources to left. smarts has most. all alphabetical
        sourcenames = sources.keys()
        sourcenames.sort()
        sourcenames = sourcenames[::-1] #reverse; have smarts first
        # CAN HACK AS NECESSARY FOR NEW SOURCES - JUST PUT SOURCENAMES IN THE ORDER YOU WANT
        
        nsourcelist = [] # get the maximum number of instances for each source
        for nsource in sources.itervalues():
            nsourcelist.append(nsource)
        maxsource = max(nsourcelist)
        for key, nsource in sources.iteritems():
            sources[key] = abs(nsource-maxsource) #now the val is how many blank spaces to add for the legend
        print sources
            
        print filters
        
        for source in sourcenames: # loop through each source for ordering purposes
            i=0
            while i < sources[source]:
                ax.errorbar((100,100),(100,100),label=' ',color='white',marker=None)
                i+=1
            ax.errorbar((100,100),(100,100),label=source,color='white',marker=None)
            for key, ob in self.obsdict.iteritems():
                if ob.filt != None and ob.source == source:
                    upperinds = np.array(ob.isupperlist)
                    detectinds = np.array([not a for a in ob.isupperlist])
                    label = ob.filtstr
                    if detectinds.any(): # only plot here if we have at least one detection
                        ax.errorbar(np.array(ob.tmidlist)[detectinds],ob.gcfluxarr[detectinds],yerr=ob.gcfluxerrarr[detectinds], color=ob.color, fmt=ob.marker, label=label)
                    if upperinds.any(): # only plot here if we have at least one upper limit
                        ax.errorbar(np.array(ob.tmidlist)[upperinds],ob.gcfluxarr[upperinds],yerr=ob.gcfluxerrarr[upperinds], color=ob.color, fmt='v')
        # ax.set_ylim(1,1E5)
        
        if xlimits:
            ax.set_xlim(xlimits)
        if ylimits:
            ax.set_ylim(ylimits)        
        
        old_ylim=ax.get_ylim() # saving for later, as gets modified.. 
        
        ax2=ax.twinx()
        ax3=ax.twiny()
        ax3.loglog()
        
        xobstime=ax.get_xlim()
        xresttime0=xobstime[0]/(1+self.redshift)
        xresttime1=xobstime[1]/(1+self.redshift)
        xrest=(xresttime0,xresttime1)
        ax3.set_xlim(xrest)
        
        
        
        # duplicate axis for AB mag
        ax.set_ylim(old_ylim)
        ylimflux=ax.get_ylim()
        ylimmag0=flux2abmag(ylimflux[0])
        ylimmag1=flux2abmag(ylimflux[1])
        ylimmag=(ylimmag0,ylimmag1)
        ax2.set_ylim(ylimmag)
        
        # Label the axes
        ax.set_ylabel(r'$F_\nu$ (uJy)', size=20)
        zsubscript=str(self.redshift)
        topxlabel = r'$t_{z=%s}$ (s)'  % zsubscript
        ax.set_xlabel(r'$t$ (s)', size=20)
        ax2.set_ylabel('AB Mag',size=20)
        ax3.set_xlabel(topxlabel,size=20)
        
        
        for label in ax.xaxis.get_ticklabels():
            # label is a Text instance
            # label.set_color('red')
            # label.set_rotation(45)
            label.set_fontsize(20)
        for label in ax.yaxis.get_ticklabels():
            # label is a Text instance
            # label.set_color('red')
            # label.set_rotation(45)
            label.set_fontsize(20)
        for label in ax2.yaxis.get_ticklabels():
            # label is a Text instance
            # label.set_color('red')
            # label.set_rotation(45)
            label.set_fontsize(20)        
        for label in ax3.xaxis.get_ticklabels():
            # label is a Text instance
            # label.set_color('red')
            # label.set_rotation(45)
            label.set_fontsize(20)
        
        acceptlabels=['K','H','J',"z'","I","i'","R","r'","V","g'","B"]
        
        if legend:
            # hugely convoluted way to get the legend the way I want
            handles, labels = ax.get_legend_handles_labels()
            print handles
            print labels
            newhandles=[]
            newlabels=[]
            # sort the legend symbols
            i=0
            strt=0
            stop=maxsource+1  
            fullindices = np.arange(0,len(labels))   
            while i < len(sources):
                newsublabels=[]
                sorted_labels=[]
                new_lab_ind_tup=[]
                sublabels = labels[strt:stop]
                indices = np.arange(0,maxsource+1)   
                
                lab_ind_tup = zip(sublabels,indices)
                for labtup in lab_ind_tup:                    
                    if labtup[0] in sources or labtup[0] == ' ': #only deal with filters
                        new_lab_ind_tup.append(labtup)
                    else:
                        print acceptlabels.index(labtup[0])
                        sorted_labels.append((acceptlabels.index(labtup[0]),labtup))
                sorted_labels.sort()
                print sorted_labels
                for item in sorted_labels:
                    new_lab_ind_tup.append(item[1])
                print lab_ind_tup     
                print new_lab_ind_tup
                for indxx in np.arange(0,maxsource+1):
                    fullindices[lab_ind_tup[indxx][1]+strt]=new_lab_ind_tup[indxx][1]+strt
                print new_lab_ind_tup
                strt+=maxsource+1
                stop+=maxsource+1
                i+=1
            print fullindices
            for indd in fullindices:
                newlabels.append(labels[indd])
                newhandles.append(handles[indd])
            print newlabels
            leg = ax.legend()
            from pylab import setp
            setp(leg.get_texts(),fontsize=2)
            setp(leg.get_title(),fontsize=2)
            ax.legend(newhandles,newlabels,loc=3,numpoints=1,frameon=False,ncol=len(sources))

        if save:
            xrtstr=''
            if incl_xrt:
                xrtstr = '_xrt'
            filepath = storepath + 'LC_' + self.name.replace('\,','') + xrtstr + '.png' 
            fig.savefig(filepath)
            filepath = storepath + 'LC_' + self.name.replace('\,','') + xrtstr + '.pdf' 
            fig.savefig(filepath)
        if show:        
            fig.show()

            
    def SimpleAlphaVSTime(self):
        '''
        Step through every pair of points in a lightcurve to calculate a very
        rough measurement of alpha based on the slope of those two points.
        '''
        # set font
        rc('font', family='Times New Roman')
        
        fig=plt.figure()
        ax=fig.add_axes([0.1,0.1,0.8,0.8])
        ax.semilogx()

        for key, ob in self.obsdict.iteritems():
            upperinds = np.array(ob.isupperlist)
            detectinds = np.array([not a for a in ob.isupperlist])
        
            tmidarr = np.array(ob.tmidlist)[detectinds]
            magarr = np.array(ob.maglist)[detectinds]
            if detectinds.any(): # only plot here if we have at least one detection
                ind = 0
                # loop through each pair of mags 
                while ind < len(magarr) - 1:
                    mag1 = magarr[ind]
                    mag2 = magarr[ind+1]
                    t1 = tmidarr[ind]
                    t2 = tmidarr[ind+1]
                    tmid = (t1 + t2)/2.0
                    alpha = mag2alpha(mag_1=mag1,mag_2=mag2,t_1=t1,t_2=t2)
                    ax.plot(tmid,alpha, color=ob.color, marker=ob.marker)
                    ind += 1
        
        ax.set_ylabel(r'$\alpha$',size=16)
        ax.set_xlabel(r'$t_{mid}$ (s)',size=16)                
        fig.show()
        
class ObsBlock:
    '''
    Block of Observations of a given Observatory/Filter
    '''
    def __init__(self,indict):
        self.source = indict['source']
        self.filtstr = indict['filt'] 
        self._AssignFilter()
        self._AssignMarker()
        self.maglist=[]
        self.magerrlist=[]
        self.ctratelist=[]
        self.ctrateerrlist=[]
        if self.source.lower() == 'xrt' or self.source.lower() == 'bat':
            self.fluxconv = float(indict['fluxconv'])
        else:
            self.fluxconv = None
        self.isupperlist=[]
        self.tmidlist=[]
        self.explist=[]
        self.updateObs(indict)
    
    def _AssignMarker(self):
        '''
        Given a source, interpret and assign a marker for plotting purposes
        '''
        if self.source.lower()=='pairitel':
            self.marker='o' # circle
        elif self.source.lower()=='prompt':
            self.marker='d' # diamond
        elif self.source.lower()=='smarts':
            self.marker='s' # square
        elif self.source.lower()=='liverpool':
            self.marker='*' # star
        elif self.source.lower()=='p60':
            self.marker='h' # hexagon
        elif self.source.lower()=='xrt':
            self.marker='x' # x
            self.color='#333333'
        elif self.source.lower()=='bat':
            self.marker='+' # .
            self.color='#999999'
        else:
            self.marker='p' # pentagon
            print "unknown source of %s, using default marker" % self.source
    
    def _AssignFilter(self):
        '''
        Given a filtstring, interpret and assign an instance of the filt 
        object'''
        from MiscBin import qObs
        if self.filtstr == 'K' or self.filtstr == 'Ks': 
            self.filt=qObs.Ks
            self.color='#FF9E9E'
            self.color='#CC6677' # override for ptel catalog
        if self.filtstr == 'H': 
            self.filt=qObs.H
            self.color='#FF6969'
            self.color='#117733' # override for ptel catalog
        if self.filtstr == 'J': 
            self.filt=qObs.J
            self.color='#FF2929'
            self.color='#88CCEE' # override for ptel catalog
        if self.filtstr == "z" or self.filtstr == "z'": 
            self.filt=qObs.z
            self.color='#FF0000'
        if self.filtstr == "i" or self.filtstr == "i'": 
            self.filt=qObs.i
            self.color='#FF8400'
        if self.filtstr == 'I' or self.filtstr == 'Ic': 
            self.color='#FF9D00'
            self.filt=qObs.Ic
        if self.filtstr == "r" or self.filtstr == "r'": 
            self.filt=qObs.r
            self.color='#F5C800'
        if self.filtstr == 'R' or self.filtstr == 'Rc': 
            self.color='#F5C800'
            self.filt=qObs.Rc
        if self.filtstr == 'V': 
            self.color='#9CE805'
            self.filt=qObs.V
        if self.filtstr == "g" or self.filtstr == "g'": 
            self.color='#00D912'
            self.filt=qObs.g
        if self.filtstr == 'B': 
            self.color='#0033FF'
            self.filt=qObs.B
        if self.filtstr == "u" or self.filtstr == "u'": 
            self.color='#9000FF'
            self.filt=qObs.u
        if self.filtstr == 'U': 
            self.filt=qObs.U
            self.color='#9000FF'
        
        if not hasattr(self,'filt'): 
            print '  Could not find appropriate filt object for filtstr %s on source %s; assigning as None' % (self.filtstr,self.source)
            self.filt = None
            self.color='#999999'
        
    def updateObs(self,indict):
        # update flux/mag values
        if 'mag' in indict:
            self.maglist.append(float(indict['mag']))
            self.magerrlist.append(float(indict['emag']))
        elif 'ctrate' in indict: # xrt values use counts instead of mag
            self.ctratelist.append(float(indict['ctrate']))
            self.ctrateerrlist.append(float(indict['ectrate']))
        else:
            raise ValueError("Value not given in magnitudes or xrt countrate; cant handle")
        if 'lim' in indict:
            isupperchar = str(indict['lim']).lower()[0] # will return 'n' if None
            if isupperchar == 'n': self.isupperlist.append(False)
            elif isupperchar == 'y' or isupperchar == 'x': self.isupperlist.append(True) 
            else: raise ValueError('Cannot parse whether upper limit or not!')
        else:
            self.isupperlist.append(False)
            
        # TODO: DO CONVERSIONS
        # find tmid and exp values and perform conversions
        # take first character of inunit/expunit to determine conversion
        # Currently convert everything to seconds
        if indict['inunit'][0] == 'd': inmultfactor = 24*3600.
        elif indict['inunit'][0] == 'h': inmultfactor = 3600.
        elif indict['inunit'][0] == 'm': inmultfactor = 60.
        elif indict['inunit'][0] == 's': inmultfactor = 1.0
        else: raise ValueError('Cannot parse determine mult factor inunit!')
        
        if indict['expunit'][0] == 'd': expmultfactor = 24*3600.
        elif indict['expunit'][0] == 'h': expmultfactor = 3600.
        elif indict['expunit'][0] == 'm': expmultfactor = 60.
        elif indict['expunit'][0] == 's': expmultfactor = 1.0
        else: raise ValueError('Cannot parse determine mult factor for exp!')
        
        
        if 'tmid' in indict and 'exp' in indict: 
        #if tmid is in there, just use that for tmid
            tmid = float(indict['tmid'])*inmultfactor
            exp = float(indict['exp'])*expmultfactor
        elif 'tstart' in indict and 'tend' in indict: 
            # take midtime based on start/end
            tstart = float(indict['tstart'])
            tend = float(indict['tend'])
            tmid = ((tstart+tend)/2.0)*inmultfactor
            if 'exp' not in indict:
                # calculate exposure time if not explicit in indict
                # no conversion necessary since already converted inunit
                exp = (tend-tstart)
            else:
                exp = float(indict['exp'])*expmultfactor
        elif 'tstart' in indict and 'exp' in indict:
            # take midtime based on start+exptime/2
            tstart = float(indict['tstart'])*inmultfactor
            exp = float(indict['exp'])*expmultfactor
            tmid = tstart+exp/2.0
        else:
            errmsg = "Cannot determine tmid and/or exp for %s filter %s" % (self.source,self.filtstr)
            raise ValueError(errmsg)    
        
        self.tmidlist.append(tmid)   
        self.explist.append(exp)                 
    


def SmartInterpolation(obsblock,desired_time_array,errestimate='spline',plot=False,
    plotzoom=None,fig=None,value_lims=None,error_lims=None):
    '''Will take an obsblock (lightcurve) and desired array of times to 
    interpolate to. 
    
    It will use qSpline optimizing over a number of nodes using GCV methodology
    the model uncertainty given by the spline fit (grey in Figure X) 
    is not the estimated uncertainty on that point had a photometric measurement been made there.  
     instead, this must be added in quadrature with some estimate of what the 
     uncertainty on a measurement would be at that time.  To achieve this, we 
     take the set of all PAIRITEL photometric uncertainties with time and fit
     another spline fit for interpolating to achieve an instrumental uncertainty estimate.
     The final uncertainty on each interpolated point is given by these two added in quadrature.
     
     plotzoom: float value of time to plot only to a certain end point
     '''
    from Modelling.qSpline import qSpline
    from Modelling.qSpline import qSplinePlot
    
    allowed_error_estimates = ['simple','spline']
    if errestimate not in allowed_error_estimates:
        raise ValueError('Please Specify an allowed Error Estimate type')

    logtarray = np.log10(desired_time_array)
    xoutvals = np.array(logtarray)
        
    # for interpolation to work, the tmidlist must be in increasing order
    detectinds = np.array([not a for a in obsblock.isupperlist])
    
    timevals = np.array(obsblock.tmidlist)[detectinds] # get rid of the upper limits 
    yvals = np.array(obsblock.maglist)[detectinds]
    yerrvals = np.array(obsblock.magerrlist)[detectinds]
    
    if plotzoom:
        x_max=np.log10(plotzoom)
    else:
        x_max = None
    
    xvals = np.log10(timevals)
    
    if fig != None: # if fig given, assume we're doing overplots of multiple magnitudes
        multiplot = True
    else:
        multiplot = False
        
    if multiplot:
        ylab = r"$m$" 
    else: 
        ylab = r"$m_%s$" % obsblock.filtstr
    newyarr, spline_model_errarr = qSpline(xvals,yvals,yerrvals,xoutvals,plot=False)
    if plot:
        if not fig:
            fig=plt.figure(figsize=(8,8))
        ax1=fig.add_axes([0.1,0.4,0.8,0.5])
        qSplinePlot(xvals,yvals,yerrvals,fig=fig,ax_index=0, inverse_y=True,
            xlabel=r'$t$(s)',ylabel=ylab,x_max=x_max,color=obsblock.color) #repeat for plot
        ax1.set_ylabel(ylab,size=16)

    newylist = list(newyarr)
    
    # NOW, ESTIMATE THE AVERAGE OBSERVATIONAL ERROR AS A FUNCTION OF TIME
    # TO ADD IN QUADRATURE TO THE MODEL ERROR     
    print list(spline_model_errarr)
    
    if errestimate == 'simple':
        insterrestimate = np.average(yerrvals)
        
    if errestimate == 'spline':
        yerr_errvals = yerrvals*0.1 # Assume 10% error on the errors??
        if multiplot:
            ylab = r"$m$ err"
        else:
            ylab = r"$m_%s$ err" % obsblock.filtstr
        insterrestimate, error_on_error = qSpline(xvals,yerrvals,yerr_errvals,xoutvals,plot=False)
        if plot:
            ax2=fig.add_axes([0.1,0.1,0.8,0.3])
            qSplinePlot(xvals,yerrvals,yerr_errvals,fig=fig,ax_index=1,x_max=x_max,color=obsblock.color)
            ax2.set_ylabel(ylab,size=16)
            ax2.set_xlabel(r'$t_{obs}$ (s)',size=16)
    
    if plot:
        #touching up the labels. May just adjust to make margins slightly larger rather than removing ticks.
        ax1lim = ax1.get_ylim()
        ax1adjust = (max(ax1lim)-min(ax1lim))*0.05 #range times a small number
        
        ax2lim = ax2.get_ylim()
        ax2adjust = (max(ax2lim)-min(ax2lim))*0.05
        
        if not value_lims: # if value limits not explicitly defined, grab them. Might be awkward with multiple plots
            ax1.set_ylim(ax1.get_ylim()[0]+ax1adjust,ax1.get_ylim()[1]-ax1adjust) # backwards due to inverse mag scale
        else:
            ax1.set_ylim(value_lims[0],value_lims[1])
        if not error_lims:
            ax2.set_ylim(0,ax2.get_ylim()[1]+ax2adjust) # bottom axis is zero, cant have negative error
        else:
            ax2.set_ylim(error_lims[0],error_lims[1])
        # ax1.set_yticks(ax1.get_yticks()[:-1])
        ax1.set_xticks(ax1.get_xticks()[1:-1]) # removing edge xticks for middle plot
        # ax2.set_yticks(ax2.get_yticks()[:-1])
        
        # making sure the x limits are same for top and bottom plot, not sure why i have to do this
        ax1.set_xlim(ax2.get_xlim()[0],ax2.get_xlim()[1]) 
        
        xticks=ax2.get_xticks()
        newxticks = 10**xticks
        strticks=[]
        for tick in newxticks:
            strtick =  '%.1e' % (tick)
            strticks.append(strtick)
        ax2.set_xticklabels(strticks)
        
        if plotzoom:
            zoomstr = str(plotzoom)
        else:
            zoomstr = ''
        filepath = storepath + 'spline' + obsblock.source + '_' + obsblock.filtstr + zoomstr + '.png'
        fig.savefig(filepath)
        filepath = storepath + 'spline' + obsblock.source + '_' + obsblock.filtstr + zoomstr + '.pdf'
        fig.savefig(filepath)
        
    print insterrestimate       #add uncertainties in quadrature
    spline_model_errlist = list(np.sqrt(spline_model_errarr**2 + insterrestimate**2)) 
    print spline_model_errlist 
    
    obsblock.explist = None
    obsblock.fluxarr=None
    obsblock.fluxerrarr=None
    obsblock.gcfluxerrarr=None
    obsblock.gcfluxarr=None
    obsblock.isupperlist=list(np.ones(len(newylist))==1) # since we forced all upper limits out
    
    obsblock.tmidlist=10**logtarray
    obsblock.maglist=newylist
    obsblock.magerrlist=spline_model_errlist
    return obsblock, fig
    
def DumbInterpolation(obsblock,desired_time_array,fake_error=0.0):
    '''
    if promptr is an obsblock, it has the following attributes:
    In [36]: promptr.
    promptr.color         promptr.fluxarr       promptr.isupperlist   promptr.source
    promptr.explist       promptr.fluxerrarr    promptr.magerrlist    promptr.tmidlist
    promptr.filt          promptr.gcfluxarr     promptr.maglist       promptr.updateObs
    promptr.filtstr       promptr.gcfluxerrarr  promptr.marker
    
    '''
    # for interpolation to work, the tmidlist must be in increasing order
    detectinds = np.array([not a for a in obsblock.isupperlist])
    timevals = np.array(obsblock.tmidlist)[detectinds] # get rid of the upper limits 
    magvals = np.array(obsblock.maglist)[detectinds]
    
    xarray=np.log10(timevals) #log of times is our x array
    assert np.all(np.diff(xarray) > 0)
    yarray = magvals
    logtarray = np.log10(desired_time_array)
    newmaglist = np.interp(logtarray,xarray,yarray,left=0,right=0)
    
    print newmaglist
    logtarray = logtarray[np.nonzero(newmaglist)] # have to have this first before i change newmaglist!
    newmaglist = newmaglist[np.nonzero(newmaglist)] # getting rid of the out of bounds interpolations

    # Figure out some better way to do this..
    errorlist=np.ones(len(newmaglist))
    errorlist*=fake_error
    
    obsblock.explist = None
    obsblock.fluxarr=None
    obsblock.fluxerrarr=None
    obsblock.gcfluxerrarr=None
    obsblock.gcfluxarr=None
    obsblock.isupperlist=list(np.ones(len(newmaglist))==1) # since we forced all upper limits out
    
    obsblock.tmidlist=10**logtarray
    obsblock.maglist=newmaglist
    obsblock.magerrlist=errorlist
    return obsblock
        
def PhotParse(filename,verbose=False):
    '''
    
    @xraydict={'refflux':9.98,'refeflux':0.1,'refwave':12.398,'xbeta':0.78,'xbetapos':0.91,'xbetaneg':0.66}
    Handling of xray dictionary - FOR USE IN SED FITS ONLY. i.e. do not use this if you have multiple epochs
    refflux:
        xray flux and uncertainty at reference time
    refwave:
        effective wavelength of xray data (12.398 is 1keV in angstroms)
    xbeta: 
        # can obtain these from Gamma in xrt /specpc_report.txt summary report
        # gamma = 1+beta (for f=f_0 * nu^-beta; note i usually use the opposite convention)
        These are used for plotting purposes. The beta inferred from XRT data alone.
    '''
    object_block = ObjBlock()
    f=file(filename)
    wholefile=f.read() # read in the whole file as a string
    f.close()
    
    # split the string into blocks where there are two line breaks
    strblocks = wholefile.split('\n\n')
    
    headblock=strblocks[0]
    bodyblocks=strblocks[1:]
    
    # set the default for keydict, which will be updated for each block
    default_keydict={'inunit':'sec',
            'expunit':'sec',
            'filt':'unknown',
            'source':'unkown',
            'utburst':'unknown',
            'galebv':'unknown',
            'redshift':'unknown',
            'name':'unknown',
            'fluxconv':'unknown',
            'xraydict':'unknown'
            }
    
    parseable_names=['tmid','tstart','tend','exp','mag','emag','filt','lim','ctrate','ectrate']
    name_replace_dict={'filter':'filt',
                        'exptime':'exp',
                        'exposure':'exp',
                        'magnitude':'mag',
                        'limit':'lim',
                        'ulim':'lim',
                        'upper':'lim',
                        'isupper':'lim',
                        't_mid':'tmid',
                        'tstop':'tend'
                        }
    
    # the header should only contain keydict stuff such as: 
    # @inunit=sec
    # @expunit=sec
    # @utburst=04:04:30.21
    # these default values will be used unless otherwise specified in
    # further text blocks.
    for head in headblock.split('\n'):
        if head == '':
            continue #blank lines
        if head[0] == '@': #special delimiter denoting default param
            key, val = head[1:].split('=')
            if key not in default_keydict:
                print ' I do not know how to handle key %s in the header, skipping' % (key)
            else:
                default_keydict.update({key:val})
    
    # now loop through the bodyblocks
    for body in bodyblocks:
        if verbose: print "*Moving on to next source...*"
        bodylines = body.split('\n')
        keydict = copy.copy(default_keydict) # set as default but update if @s are defined
        for bodyline in bodylines: # loop through each line in the bodyblock
            if not bodyline: #if blank line, skip
                continue
            if bodyline[0] == '#': #if comment line, skip
                continue 
            #### Grab the HEADERS of the bodyblock to get the default values
            if bodyline[0] == '@': #special delimiter denoting default param
                key, val = bodyline[1:].split('=')
                # replace names as necessary
                if key in name_replace_dict:
                    key = name_replace_dict[key]
                if key not in keydict:
                    print ' I do not know how to handle key %s in the photometry, skipping' % (key)
                else:
                    keydict.update({key:val})
                    if key == 'source' and verbose:
                        print ' Now reading in data for source %s' % (val)
                    
            #### Grab the FORMAT of the remaining lines
            elif bodyline[0] == '%': #special delimiter of the format line
                fmtlist = bodyline[1:].split()
                #convert to lowercase
                fmtlist = [fmt.lower() for fmt in fmtlist]
                # replace the names
                for name, replacename in name_replace_dict.iteritems():
                    fmtlist = [fmt.replace(name,replacename) for fmt in fmtlist]
                if verbose:
                    # rename the format list if necessary
                    for fmtname in fmtlist:
                        if fmtname not in parseable_names:
                            print "  Cannot parse %s, skipping this column" % fmtname
                        
            
            #### Otherwise it is a line of numbers; split and parse and update relevant ObsBlock
            else:
                datalist = bodyline.strip().split()
                current_data_dict={}
                for fmt in fmtlist:
                    if fmt not in parseable_names:
                        pass
                    else:
                        try:
                            current_val = datalist[fmtlist.index(fmt)]
                        # if the format list is longer than the value list,
                        # we assume its blank lines at the end and assign None
                        except(IndexError): 
                            current_val = None   
                        current_data_dict.update({fmt:current_val})
                
                keydict.update(current_data_dict) # override any defaults with current
                if not 'filt' in keydict and not 'source' in keydict:
                    raise Exeption('Dont have both filt and source!')
                
                # if keydict['source']=='PAIRITEL':
                #     raise Exception
                object_block.updateObj(keydict)
    
    object_block.CalculateFlux()            
    
    return object_block
    