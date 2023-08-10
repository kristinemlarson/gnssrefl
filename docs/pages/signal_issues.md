# Some comments about signals

## GPS L2C

Why do I like L2C? What's not to like? It is a modern **civilian** code without high chipping rate.
That civilian part matters because it means the receiver knows the code and thus
retrievals are far better than a receiver having to do extra processing to 
extract the signal. Here is an example of a receiver that is tracking **both** L2P and L2C.
Originally installed for the Plate Boundary Observatory, it is a Trimble. The archive 
(unavco) chose to provide only L2P in the 15 second default RINEX file.
However, it does have the L2C data in the 1 second files. So that is how I am able to make 
this comparison.  P038 is a very very very flat site.

Here are the L2P retrievals:

<img src="../_static/p038usingL2P.png" width="600"/>

Now look at the L2C retrievals.

<img src="../_static/p038usingL2c.png" width="600"/>

If you were trying to find a periodic signal, which one 
would you want to use?

To further confuse things, when the receiver was updated to a Septentrio, unavco began
providing L2C data in the default 15 second files. This is a good thing - but it is confusing
to people that won't know why the signal quality improved over night.

## GPS L5

Another great signal.  I love it. It does have a high chipping rate, which is 
relevant (i.e. bad) for reflectomtry from very tall sites.

## Aliasing

While it will show up in GPS results too - there seems to be a particularly
bad problem with Glonass L1.  I used an example from Thule. The RH is significant -
~20 meters. So you absolutely have to have at least 15 sec at the site or you violate
the Nyquist. Personally I prefer to use 5 sec - which means I have to download
1 sec and decimate. This is extremely annoying because of how long it takes to 
ftp those files to my local machine. Let's look at L1 solutions using a 5 second file - 
but where I invoke the -dec option for gnssir. That way I can see the impact of the sampling.
I also using the -plt T option. 

This is 5 second GPS L1.

<img src="../_static/thule_l1.png" width="600"/>

This is 15 second GPS L1. You see some funny stuff at 30 meters, and yes, the periodograms
are noisier. But nothing insane.

<img src="../_static/thule_l1_15sec.png" width="600"/>

Now do 5 second Glonass L1

<img src="../_static/not_aliased_101.png" width="600"/>


Contrast with the Glonass L1 results using 15 sec decimation!
So yeah, aliasing is a problem.

<img src="../_static/aliased_101.png" width="600"/>


## E5

Now about RINEX L8 ... also known as E5. This is one of 
the new Galileo signals. Despite the fact that it is near
the frequencies of the other L5 signals, it is **not** the 
same. You can see that 
it in the multipath envelope work of Simsky et al. shown below.

<img src="../_static/multipath-envelope.png" width="600"/>

Most of you will not be familiar with multipath envelopes - 
but for our purposes, we want those envelopes to be big - cause
more multipath, better GNSS-IR. First thing, multipath delay 
shown on the x-axis is NOT the reflector height (RH).  it is 
2*RH*sin(elevation angle). So even a pretty tall RH will not 
be obstructed by the new Galileo codes except for E5.



<img src="../_static/at01_358_205.png" width="600"/>
This is E5a (in our software it is called frequency 205; in RINEX it is called L5)

<img src="../_static/at01_358_208.png" width="600"/>

This is E5. In our software it is called frequency 208 and in RINEX it is called L8).
Note that instead of nice clean peaks, it is 
spread out. You can also see that the E5 retrievals degrades as elevation angle increases,
which is exactly what you would expect with the multipath delay 
increasing with elevation angle. I would just recommend only using
this signal for RH < 5 meters. And even then, if you are tracking
L8, you probably also have L5, L6, and L7, so there is not a ton gained 
by also using L8.

##  What about L1C?

I would be happy to host some results from L1C - please submit a pull request 
with the needed figures and a description of what you are comparing. I imagine
this would require making two snr files - one with L1C and one with L1 C/A. 
And using only the small subset of satellites that transmit L1C.
From what I have seen, it is not much better than L1 C/A - which surprisees me.
But I have to imagine it is receiver dependent (some receivers have terrible C/A SNR).  

<HR>

The multipath envelope figure is taken from:

Title: Experimental Results for the Multipath Performance of Galileo 
Signals Transmitted by GIOVE-A Satellite

Authors: Andrew Simsky,David Mertens,Jean-Marie Sleewaegen,
Martin Hollreiser, and Massimo Crisci

International Journal of Navigation and Observation 
Volume 2008, DOI 10.1155/2008/416380

