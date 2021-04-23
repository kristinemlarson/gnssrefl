### Some Use Cases to Help You Test Out gnssrefl

This document provides some use cases for GNSS interferometric reflectometry. 
The goal is to provide you with tests to make sure you have properly installed the code. For details about the technique, 
you should start with reading [Roesler and Larson, 2018](https://link.springer.com/article/10.1007/s10291-018-0744-8), 
which was published open option.  

### Install the gnssrefl code 

* Make sure **wget** exists on your machine.  If you type *which wget* and something comes back, you should be good.

* Read the [gnssrefl documentation](https://github.com/kristinemlarson/gnssrefl). 
Note that there are some utilities described at the end of the code that you might
find to be useful.

* Install either the github or the pypi version of gnssrefl

* Make the requested environment variables. 

* Put CRX2RNX in the EXE area. Make sure it is executable

### Use Cases 

<table>
<TR>
<TD>

* [Lorne, Ross Ice Shelf, Antarctica](use_cases/use_lorg.md) (lorg)

* [Dye2, Greenland Ice Sheet](use_cases/use_gls1.md) (gls1)

* [Thwaites Glacier, Antarctica](use_cases/use_lthw.md) (lthw)

* Summit Camp, Greenland (smm3)
</TD>
<td>

* [Michipicoten, Lake Superior, Canada](use_cases/use_mchn.md) (mchn)

* [Lake Taupo, New Zealand](use_cases/use_tgho.md) (tgho)

* [St Lawrence River, Montreal, Canada](use_cases/pmtl_use.md) (pmtl)
</TD>

<TD>
Seasonal Snow Accumulation

* [Marshall, Colorado](use_cases/use_p041.md) (p041)

* [Niwot Ridge, Colorado](use_cases/use_nwot.md) (nwot)

* [Half Island Park, Idaho](use_cases/use_p360) (p360)

</TD>
</TR>
</Table>

The gnssrefl code can be used now for tides, but use cases are still under development.
Our code does not currently support soil moisture applications.
