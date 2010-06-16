from amara import bindery
import datetime
from matplotlib import pylab as plt
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.axes_grid.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid.inset_locator import mark_inset
from mpl_toolkits.axes_grid.inset_locator import inset_axes
import os
from matplotlib import rc
import copy
import cosmocalc

#check out yuml.me for flow chart creator

#sent to me from JSB on 10/01/11

if not os.environ.has_key("Q_DIR"):
    print "You need to set the environment variable Q_DIR to point to the"
    print "directory where you have Q_DIR installed"
    sys.exit(1)
storepath = os.environ.get("Q_DIR") + '/store/'

# Import matplotlib run commands to set font
rc('font', family='serif')

def parse_grbox_xml():
    filename=storepath+"grboxtxt.xml"
    a = bindery.parse(filename)

    # Parse the xml to grab the grb names and whether there have been certain 
    # types of detections (radio, optical, xray)
    names          = [x.xml_value.encode() for x in a.xml_select(u'/grbs/grb/@index')]
    has_xray  = [x.xml_value.encode() == 'y' for x in a.xml_select(u'/grbs/grb/greiner/@x')]
    has_opt   = [x.xml_value.encode() == 'y' for x in a.xml_select(u'/grbs/grb/greiner/@o')]
    has_radio = [x.xml_value.encode() == 'y' for x in a.xml_select(u'/grbs/grb/greiner/@r')]

    # Define lists to use later
    has_host_z = []
    ignores = ['hostphotz','photz']
    z_list    = []
    zname_list = []
    date_list    = []
    
    grbox_dict = {}
    
    # loop through all the GRB names in the XML file and grab all the redshifts
    # associated with each name (there may be more than one!) 
    for grbname in names:
       ## get all the redshifts
       print grbname
       # Obtain a list of tentative redshifts for every grbname
       tentative_z =[str(x) for x in a.xml_select(u'/grbs/grb[@index="%s"]/redshift/z' % grbname)]
       # if there is an "?" after the redshift number (e.g. <z>1.24?</z>), mark it
       uncertain_z = [str(x).find("?") != -1 for x in tentative_z]
       # Obtain a list of the redshift types
       z_type = [str(x) for x in a.xml_select(u'/grbs/grb[@index="%s"]/redshift/ztype' % grbname)]
       print grbname, [(tentative_z[i],uncertain_z[i],z_type[i]) for i in range(len(tentative_z))]
       use = False
       for i in range(len(tentative_z) - 1,-1,-1):
           use_this_z = True
           for ii in ignores:
               if z_type[i].find(ii) != -1:
                   # this type is to be ignored
                   use_this_z=False
           has_host = False
           if z_type[i].find("hostz") != -1:
               has_host = True

           if use_this_z and not uncertain_z[i]:
               use = True
               zz = tentative_z[i]
       if use:
           zname_list.append(grbname)
           has_host_z.append(has_host)
           z_list.append(float(zz))
           yr = int("19" + grbname[0:2]) if int(grbname[0]) > 8 else int("20" + grbname[0:2])
           mn = int(grbname[2:4])
           dy = int(grbname[4:6])
           date_list.append(datetime.date(yr,mn,dy))
           
           subdict = {grbname:{'grbox_z':float(zz),'has_host_z':has_host}}
           
           grbox_dict.update(subdict)

    # tessellation
    #a = jsbtess.jsbtess(z_list,per=0.03,dolog=True,unlog=True)
    #l = [r[0] for r in a['bb']]
    #w = [r[1] - r[0] for r in a['bb']]

    ## save redshift record
    alll = zip(date_list,z_list,zname_list)
    alll.sort()  # sort by date increasing
    # print "***ZLIST***"
    # print z_list
    # print len(z_list)
    #         
    
    from pprint import pprint 
    # pprint(alll)
    
    pprint(grbox_dict)
    
    return alll


alll = parse_grbox_xml()
z_list = []
zname_list = []
date_list = []


# 'un'zip alll (is there a better way to do this? just assign rather than a for loop?)
for tup in alll:
    date_list.append(tup[0])
    z_list.append(tup[1])
    zname_list.append(tup[2])
print '***All***'
print ' '
print z_list
print len(z_list)


### Print out the most distant GRB as a function of time
zmax = 0.0
rr = []
for grb in alll:
   if grb[1] > zmax:
       rr.append(grb)
       zmax = grb[1]
       print grb[0].year + grb[0].timetuple().tm_yday/365.0, grb[1], "#  ", grb[2]


ax = plt.subplot(111)
n, bins, patches = plt.hist(plt.log10(z_list),bins=29,facecolor='#666666',alpha=0.95)

# Define pre-swift burst index as bursts before 041210
preswifti = plt.where(plt.array(date_list) < datetime.date(2004,12,10))

pre_swift_z_list = [z_list[i] for i in list(preswifti[0])]
#print pre_swift_z_list
n, bins1, patches = plt.hist(plt.log10(pre_swift_z_list),bins=bins,facecolor='#999999',alpha=0.6)

ay = ax.twinx()

argg = list(plt.ones(len(z_list)).cumsum().repeat(2))
zz = copy.copy(z_list)
zz.sort()
tmp = list(plt.log10(zz).repeat(2))

tmp.append(1)
yy = [0]
yy.extend(argg)

ay.plot(tmp,yy,linewidth = 4,color='black',alpha=0.95)

argg = list(plt.ones(len(pre_swift_z_list)).cumsum().repeat(2))
zz = copy.copy(pre_swift_z_list)
zz.sort()
tmp = list(plt.log10(zz).repeat(2))

tmp.append(1)
yy = [0]
yy.extend(argg)


ay.plot(tmp,yy,"-",linewidth = 3,color='#222222',alpha=0.85)
ay.set_ylim((0,len(z_list)*1.05))
ay.set_ylabel("Cumulative Number",fontsize=20,family="times")
# formatter for bottom x axis 
def ff(x,pos=None):
   if x < -1:
       return "%.2f" % (10**x)
   elif x < 0:
       return "%.1f" % (10**x)
   elif 10**x == 8.5:
       return "%.1f" % (10**x)
   else:
       return "%i" % (10**x)

formatter = FuncFormatter(ff)
ax.set_xticks([-2,-1,plt.log10(0.3),0,plt.log10(2),plt.log10(3),plt.log10(4),plt.log10(6),plt.log10(8.5)])
ax.xaxis.set_major_formatter(formatter)
ax.set_xlabel("Redshift [z]",fontsize=20,family="times")
ax.set_ylabel("Number",fontsize=20,family="times")

ax.set_xlim( (plt.log10(0.005),plt.log10(10)))

ax2 = ax.twiny()
xlim= ax.get_xlim()
#ax2.set_xscale("log")
ax2.set_xlim( (xlim[0], xlim[1]) )

# Define function for plotting the top X axis; time since big bang in Gyr
def rr(x,pos=None): 
   g = cosmocalc.cosmocalc(10.0**x, H0=71.0)
   if g['zage_Gyr'] < 1:
       return "%.2f" % g['zage_Gyr'] # Return 2 dec place if age < 1; e.g 0.62
   else:
       return "%.1f" % g['zage_Gyr'] # Return 1 dec place if age > 1; e.g. 1.5

ax2.set_xticks([-1.91,-1.3,-0.752,-0.283,0.102,0.349,0.62,plt.log10(8.3)])

formatter1 = FuncFormatter(rr)
ax2.xaxis.set_major_formatter(formatter1)
ax2.set_xlabel("Time since Big Bang [Gyr]",fontsize=20,family="times")

#plt.bar(l,a['yy'],width=w,log=False)
#ax.set_xscale("log",nonposx='clip')

## Now plot inset plot of GRBs greater than z=3.5

axins = inset_axes(ax2,
                  width="30%", # width = 30% of parent_bbox
                  height="30%") # height : 1 inch)

locator=axins.get_axes_locator()
locator.set_bbox_to_anchor((-0.8,-0.45,1.35,1.35), ax.transAxes)
locator.borderpad = 0.0

pre_swift_z_list = [z for z in z_list if z > 3.5]

n, bins, patches = plt.hist(plt.array(pre_swift_z_list),facecolor='#666666',alpha=0.95)
axins.set_xlim(3.5,8.5)
axins.set_xlabel("z")
axins.set_ylabel("N")

preswifti = plt.where(plt.array(date_list) < datetime.date(2004,12,10))
pre_swift_z_list = [z_list[i] for i in list(preswifti[0]) if z_list[i] > 3.5]

n, bins, patches = plt.hist(plt.array(pre_swift_z_list),bins=bins,facecolor='#999999',alpha=0.9)
axins.set_xlim(3.5,8.5)
#mark_inset(ax, axins, loc1=2, loc2=4, fc="none", ec="0.5")

#axins2.set_xlabel("Time since Big Bang [Gyr]",fontsize=20)
ylabels = ax.get_yticklabels()
plt.setp(ylabels, size=14, name='times', weight='light', color='k')

xlabels = ax.get_xticklabels()
plt.setp(xlabels, size=14, name='times', weight='light', color='k')

xlabels = ax2.get_xticklabels()
plt.setp(xlabels, size=14, name='times', weight='light', color='k')

xlabels = ay.get_yticklabels()
plt.setp(xlabels, size=14, name='times', weight='light', color='k')


plt.draw()

#for i in range(len(z_list)):
#    print z_list[i], uncertain_z[i],ztype[i],names[i]