
### gnssrefl use cases 


<table>
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

* [Michipicoten, Lake Superior, Canada](use_cases/use_mchn.md) 

* [Lake Taupo, New Zealand](use_cases/use_tgho.md) 

* [St Lawrence River, Montreal, Canada](use_cases/use_pmtl.md) 

</TD>
</TR>
<TR>

<TD>
<B>Seasonal Snow Accumulation</B>

* [Marshall, Colorado](use_cases/use_p041.md) 

* [Niwot Ridge, Colorado](use_cases/use_nwot.md) 

* [Half Island Park, Idaho](use_cases/use_p360.md) 

</TD>
<TD>
<B>Ocean Tides</B>

* [Friday Harbor, Washington](use_cases/use_sc02.md) 

* [St Michael, Alaska](use_cases/use_at01.md) 

</TD>
</TR>
</Table>

<P>

### Summary Guide for Installation 

* This code has only been tested for linux and MacOS.

* Make sure **wget** exists on your machine.  If you type *which wget* and something comes back, you should be good.

* gzip, xz, and unix compression (Z) should be supported by your machine

* Install the [github version of gnssrefl](https://github.com/kristinemlarson/gnssrefl). Follow the [documentation guidelines](https://github.com/kristinemlarson/gnssrefl). 

* Make the requested environment variables.

* You can try using the <code>installexe</code> utility. Or you can download the Hatanaka 
translator, CRX2RNX, and put it in the EXE area. Make sure it is executable.

<P>

Our code does not currently support soil moisture applications. It will be added in year 3 of the NASA grant we received to 
build this software.
