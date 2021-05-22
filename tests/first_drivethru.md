<center>
### gnssrefl use cases 
</Center>


<table align=center>
<TR>
<TD>
<B>Greenland/Antarctica</B>

* [Lorne, Ross Ice Shelf, Antarctica](use_cases/use_lorg.md) (lorg)

* [Dye2, Greenland Ice Sheet](use_cases/use_gls1.md) (gls1)

* [Thwaites Glacier, Antarctica](use_cases/use_lthw.md) (lthw)

* [Summit Camp, Greenland](use_cases/use_smm3.md) (smm3)

</TD>
<td>
<B>Lakes and Rivers</B>

* [Michipicoten, Lake Superior, Canada](use_cases/use_mchn.md) (mchn)

* [Lake Taupo, New Zealand](use_cases/use_tgho.md) (tgho)

* [St Lawrence River, Montreal, Canada](use_cases/use_pmtl.md) (pmtl)
</TD>
</TR>
<TR>

<TD>
<B>Seasonal Snow Accumulation</B>

* [Marshall, Colorado](use_cases/use_p041.md) (p041)

* [Niwot Ridge, Colorado](use_cases/use_nwot.md) (nwot)

* [Half Island Park, Idaho](use_cases/use_p360.md) (p360)

</TD>
<TD>
<B>Ocean Tides</B>

* [Friday Harbor, WA](use_cases/use_sc02.md) (sc02)

* [St Michael, AK](use_cases/use_at01.md) (at01)

</TD>
</TR>
</Table>

The gnssrefl code can also be used for tides, but use cases are still under development. 
Our code does not currently support soil moisture applications.
For more details about the technique, please see [Roesler and Larson, 2018](https://link.springer.com/article/10.1007/s10291-018-0744-8). 
<P>

### Summary Guide for Installation 

* Make sure **wget** exists on your machine.  If you type *which wget* and something comes back, you should be good.

* gzip, xz, and unix compression (Z) should be supported by your machine

* Install the [github version of gnssrefl](https://github.com/kristinemlarson/gnssrefl). Follow the documentation guidelines. 

* Make the requested environment variables.

* Download the Hatanaka translator, CRX2RNX, and put it in the EXE area. Make sure it is executable.

