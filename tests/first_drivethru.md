### Some Use Cases to Help You Test Out gnssrefl

This document provides some use cases for GNSS interferometric reflectometry. 
The goal is to provide you with tests to make sure you have properly installed the code. For details about the technique, 
you should start with reading [Roesler and Larson, 2018](https://link.springer.com/article/10.1007/s10291-018-0744-8), 
which was published open option.  

### Install the gnssrefl code 

Make sure **wget** exists on your machine.  If you type *which wget* and something comes back, you should be good.

Read the [gnssrefl documentation](https://github.com/kristinemlarson/gnssrefl). 
Note that there are some utilities described at the end of the code that you might
find to be useful.

Install either the github or the pypi version of gnssrefl

Make the requested environment variables. 

Put CRX2RNX in the EXE area. Make sure it is executable

If you know how to compile Fortran code, I strongly urge you to download/compile the requested
codes and install those executables in the correct place.  We are currently testing a hybrid 
option (for translator) that allows access to Fortran speed from within python.

For what it is worth, I have had times when I have been blocked from 
downloading files (? after 20 file downloads - so maybe it is 
my internet provider ?). When I turn on my VPN, all is well. I have not investigated this 
in any detail. So take that for what you will. 


### Use Cases (These are still under development)

<table>
<TR>
<TH>Cryosphere</TH>
<TD>

* [Lorne, Ross Ice Shelf, Antarctica](use_cases/lorg_use.md) (lorg)

* [Dye2, Greenland Ice Sheet](use_cases/gls1_use.md) (gls1)

* [Thwaites Glacier, Antarctica](use_cases/lthw_use.md) (lthw)

* [Summit Camp, Greenland](use_cases/smm3_use.md) (smm3)
</TD>
<TH>Lakes and Rivers</TH>
<td>

* [Lake Taupo, New Zealand](use_cases/tgho_use.md) (tgho)

* [Michipicoten, Lake Superior, Canada](use_cases/mchn_use.md) (mchn)

* [St Lawrence River, Montreal, Canada](use_cases/pmtl_use.md) (pmtl)

* Steenbras Reservoir, Republic of South Africa (sbas)

</TD>
<TH>Tides and Storm Surges</TH>
<TD>

* Hurricane Laura (calc)

* St Michael, Alaska (at01)

* Palmer Station, Antarctica (pal2)

</TD>
</TR>

<TR>
<TH>Seasonal Snow</TH>
<TD>

* [Marshall, Colorado](use_cases/p041_use.md) (p041)

* Half Island Park, Idaho (p360)

* Coldfoot, Alaska (ab33)

* Priddis, Alberta, Canada (prds)

</TD>
<TH>Soil Moisture</TH>

<TD>

* TBD

</TD>

</TR>
</Table>


