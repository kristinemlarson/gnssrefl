## make_json_input

Before you estimate reflector heights, you need a set of instructions. These are made using <code>make_json_input</code>.
The required inputs are:

* station name
* latitude (degrees)
* longitude (degrees)
* ellipsoidal height (meters).

The station location *does not* have to be cm-level for the reflections code. Within a few hundred meters is
sufficient. For example:

<CODE>make_json_input p101 41.692 -111.236 2016.1</CODE>

If you happen to have the Cartesian coordinates (in meters), you can
set <code>-xyz True</code> and input those instead of lat, long, and height.

If you are using a site that is in the UNR station database, the *a priori* values can be set to zeros:

<CODE>make_json_input p101 0 0 0 </CODE>

[A full listing of the possible inputs and examples for make_json_input can be found here.](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.make_json_input.html)

The json file of instructions will be put in $REFL_CODE/input/p101.json.

The default azimuth inputs are four regions, each of 90 degrees.
You set your preferred azimuth regions using -azlist. Azimuth regions should not be larger
than ~100 degrees. If for example you want to use the region from 0 to
270 degrees, you should not set a region from 0 - 270, but instead a region from 0-90, 90-180, and the last
from 180-270.

Example:

<CODE>make_json_input p101 0 0 0   -azlist 0 90 90 180 180 270</CODE>

We try to enforce homogenous track lengths by using a quality control factor called *ediff*. Its
default value is 2 degrees, which means your arc should be within 2 degrees of the requested elevation angle inputs.
So if you ask for 5 and 25 degrees, your arcs should at least be from 7 to 23 degrees.  To tell
<code>gnssir</code> you want to allow more arcs, just set ediff to a much larger value.

