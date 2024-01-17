import argparse
import gnssrefl.gps as g

def main():
    """
    converts MJD to year, month, day, hour, minute, second
    and prints that to the screen

    Parameters
    ----------
    mjd : float
        modified julian date

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("mjd", help="Modified Julian Date", type=float)

    args = parser.parse_args()
    the_mjd= args.mjd

    filler = g.mjd_to_datetime(the_mjd)
    print(filler)

if __name__ == "__main__":
    main()
