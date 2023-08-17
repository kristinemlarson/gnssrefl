# quickLook 

<CODE>quickLook</code> is meant to provide the user with a visual sense of the data 
at a given site.  It has stored defaults that work for stations with reflectors that are 
lower than 8 meters or so. [You can change those defaults on the command line.](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.quickLook_cl.html) 

## Example from Boulder

<code>quickLook p041 2020 132 </CODE>

That command will produce this periodogram summary :

<img src="../_static/p041-l1.png" width=600>

By default, these are L1 data only. Note that the x-axis does not go beyond 6 meters. This is because
you have used the defaults. Furthermore, note that results on the x-axis begin at 0.5 meters.
Since you are not able to resolve very small reflector heights with this method, this region 
is not allowed. These periodograms give you a sense of whether there is a planar reflector below your antenna. The fact that the 
peaks in the periodograms bunch up around 2 meters means that at 
this site the antenna phase center is ~ 2 meters above the ground. The colors change as you try 
different satellites.  If the data are plotted in gray that means you have a failed reflection. The quadrants are Northwest, Northeast and so on. 

<CODE>quickLook</code> also provides a summary of various quality control metrics:

<img src="../_static/p041_l1_qc.png" width=600>

The top plot shows the sucessful RH retrievals in blue and unsuccessful RH retrievals in gray. 
In the center panel are the peak to noise ratios. The last plot is the amplitude of the spectral peak. The dashed
lines show you what QC metrics quickLook was using. You can control/change these on the command line.

If you want to look at L2C data you just change the frequency on the command line. L2C is designated by 
frequency 20: 

<CODE>quickLook p041 2020 132 -fr 20</CODE>

<img src="../_static/p041-l2c.png" width=600>

**L2C results are always superior to L1 results. They are also superior to L2P data.** If you have 
any influence over a GNSS site, please ask the station operators to 
track modern GPS signals such as L2C and L5 **and** to include it in the archived RINEX file.

## Example for Lake Superior

<code>quickLook ross 2020 170 -e1 5 -e2 15</code>

<img src=../_static/ross-qc.png width=600>

The good RH estimates (in blue in the top panel) are telling us that we were right when we assessed 
reflection zones using 4 meters. We can also see that the best retrievals are in the southeast quadrant (azimuths 90-180 degrees).
This is further emphasized in the next panel, that shows the actual periodograms.

<img src=../_static/ross-lsp.png width=600>

[Example for a site on an ice sheet](../use_cases/use_gls1.md)

[Example for a tall site](../use_cases/use_smm3.md)

In addition to the **peak2noise** and required amplitude (**ampl**) QC metrics, there is a 
couple more QC metrics that are hardwired. One is the length of time 
allowed for an arc - this can be a problem when you have an arc that crosses midnite;
since the gnssrefl code works on elevation angle, it will combine part of 
the arc from the beginning of the day and the rest 
from the end of the day. This is not sensible - and it will reject this arc 
nominally for being far too long. Really it is rejecting it because it is non-physical.  

The code tries to find all eligible arcs between elevation angles **e1 (emin)** and **e2 (emax)**.
Why? In my experience you don't want to use an arc that only goes from 5-10 degrees if you 
are trying to use all arcs between 5 and 25 degrees. The same is true for small
arcs at higher elevation angles (20-25). However, you don't want to be 
too strict, so there is a QC setting called **ediff**.
The default is 2 degrees. For a given emin and emax for your arcs, <code>quickLook</code> 
will allow you to use arcs that are at least within this amount in degrees, i.e. 
(emin +ediff) and (emax - ediff). The net result of this QC setting 
default is to make it less likely you will try to use a very short arc. 
Although this cannot be changed for <code>quickLook</code>, you 
can change it in <code>gnssir</code> in your json file. If you want <code>gnssir</code> to use
everything, just make **ediff** very large. 

Warning: <code>quickLook</code> calculates the minimum observed elevation 
angle in your file and prints that to the screen so you know 
what it is. It also uses that as your emin
value (e1) if the default is smaller. It does this so you don't see all arcs as rejected.
Let's say your file had a receiver-imposed elevation cutoff 
of 10 degrrees. The default minimum elevation angle in <code>quickLook</code> is 5 degrees. 
With the default **ediff** value of 2, not a single arc would reach the minimum 
required value of 7 (5 + 2); everything 
would be rejected. <code>quickLook</code> instead sees that
you have a receiver-imposed minimum of 10 and would substitute that for the default emin. 
<code>gnssir</code> does not do this because at that point you 
are supposed to have chosen a strategy, which is stored in the json file.

<code>quickLook -screenstats True</code> provides more information to the screen 
about why arcs have been rejected.

