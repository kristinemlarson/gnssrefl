import numpy as np


class constants:
    omegaEarth = 7.2921151467E-5  # rad/sec
    mu = 3.986005e14  # Earth GM value
    c = 299792458  # m/sec


def elev_limits(snroption):
    """
    For given SNR option, returns elevation angle limits

    Parameters
    ------------
    snroption : integer
        snr file delimeter

    Returns
    ----------
    emin: float
        minimum elevation angle (degrees)
    emax: float
        maximum elevation angle (degrees)
    """
    if (snroption == 99):
        emin = 5; emax = 30
    elif (snroption == 50):
        emin = 0; emax = 10
    elif (snroption == 66):
        emin = 0; emax = 30
    elif (snroption == 88):
        emin = 5; emax = 90
    else:
        emin = 5; emax = 30

    return emin, emax


def propagate_and_azel_sp3(iX, iY, iZ, t, recv, up, East, North, oE, clight):
    """
    Vectorized SP3 orbit propagation with light-time iteration, then azimuth/elevation.

    Parameters
    ----------
    iX, iY, iZ : CubicSpline
        interpolators for satellite ECEF coordinates
    t : ndarray
        observation times (GPS seconds of week), shape (N,)
    recv : ndarray
        receiver ECEF position, shape (3,)
    up, East, North : ndarray
        unit vectors at receiver, shape (3,)
    oE : float
        Earth rotation rate (rad/s)
    clight : float
        speed of light (m/s)

    Returns
    -------
    elv : ndarray, shape (N,)
        elevation angles in degrees
    azm : ndarray, shape (N,)
        azimuth angles in degrees [0, 360)
    """
    # initial guess: 70 ms transmission time
    nx = iX(t - 0.07); ny = iY(t - 0.07); nz = iZ(t - 0.07)
    SatOrb = np.column_stack((nx, ny, nz))
    tau = np.sqrt(np.sum((SatOrb - recv)**2, axis=1)) / clight

    # two light-time iterations (matching scalar satorb_prop_sp3)
    for _k in range(2):
        nx = iX(t - tau); ny = iY(t - tau); nz = iZ(t - tau)
        SatOrb = np.column_stack((nx, ny, nz))
        Th = -oE * tau
        cosT = np.cos(Th); sinT = np.sin(Th)
        xs = SatOrb[:, 0]*cosT - SatOrb[:, 1]*sinT
        ys = SatOrb[:, 0]*sinT + SatOrb[:, 1]*cosT
        SatOrbn = np.column_stack((xs, ys, SatOrb[:, 2]))
        tau = np.sqrt(np.sum((SatOrbn - recv)**2, axis=1)) / clight

    r_vec = SatOrbn - recv
    r_norms = np.sqrt(np.sum(r_vec**2, axis=1))
    cos_zenith = np.clip(r_vec @ up / r_norms, -1.0, 1.0)
    elv = (np.pi/2.0 - np.arccos(cos_zenith)) * 180.0/np.pi
    azm = np.arctan2(r_vec @ East, r_vec @ North) * 180.0/np.pi % 360.0
    return elv, azm
