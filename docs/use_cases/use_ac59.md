# Ursus Head, Alaska


## GNSS-IR at ac59


You need high rate data.  How high?  Use the Nyquist calculator.  For this site I will use 
1-Hz data.

Remember that <code>quickLook</code> is a **quick** look.  It does not have any information
about your site and must use whatever you tell it at the command line.  One of the things
that is missing is the station location which is used in **gnssir** for the refraction correction.
The refraction correction is super important for tall sites, so the periodograms (and RH retrievals)
in quickLook will look funny for tall sites. They will look great in **gnssir** so be aware of that.

The RH retrievals will depend on the wind conditions. Don't assume things aren't working just because
you get not retrievals. Here I will use a day when I know it is not windy. 

L5 doesn't work. It just doesn't. Look at the Signals page for more information.

## Strategy 

Use reflzones or rzones on the web app to pick a mask. 

Pickup and translate the data (but since it is so tall, I am using snr option 50, which is data < elevation angle of 10 degrees)

<code>rinex2snr ac59 2022 94 -archive unavco -rate high -orb gnss -snr 50</code>

<code>quickLook ac59 2022 94 -e1 4 -e2 8 -h1 280 -h2 300 -snr 50</code>

Note that the periodogram is spread out - this is because you didn't correct for refraction.

I am not going to justify my choices in <ocde>gnssir</code>, but I am providing the [json](ac59.json) for you.
Please note the mask, the noise region and frequency choices. I have turned off the required amplitude.
I do not pretend these choices are perfect.

<code>gnssir ac59 2022 94  -snr 50 -plt T</code>

This will bring the RH results to the screen (or make png files if you are using the docker).

<code>subdaily ac59 2022</code>

produces some lovely results ... 


