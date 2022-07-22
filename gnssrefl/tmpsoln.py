# old code from gps.py that can compute a simple pseudorange
# navigation solution
def tmpsoln(navfilename,obsfilename):
    """
    kristine larson
    inputs are navfile and obsfile names
    should compute a pseudorange solution
    """
    r2d = 180.0/np.pi
#  elevation mask
    emask = 10 
 
    ephemdata = myreadnav(navfilename)
    if len(ephemdata) == 0:
        print("empty ephmeris or does not exist")
        return
    #cartesian coordinates - from the header
    # number of epochs you want to read
    nep = 2
    recv,obs=readobs2(obsfilename,nep)
    print('A priori receiver coordinates', recv)
    if recv[0] == 0.0:
        print('using new a priori')
        recv[0]=-2715532
        recv[1] = -881995
        recv[2] = 5684286
        print('now using', recv)
    lat, lon, h = xyz2llh(recv,1e-8)
    print("%15.7f %15.7f"% (lat*r2d,  lon*r2d) )
    # zenith delay - meters
    zd = zenithdelay(h)
    u,east,north = up(lat,lon)
    epoch = np.unique(obs['TOW'])
    NN=len(epoch)
    NN = 2 # only do two positions
    for j in range(NN):
        print('Epoch', j+1)
        sats = obs['PRN'][np.where(epoch[j]==obs['TOW'])]
        gps_seconds = np.unique(obs['TOW'][np.where(epoch[j]==obs['TOW'])])
        gps_weeks = np.unique(obs['WEEK'][np.where(epoch[j]==obs['TOW'])])
        # not sure this does anything
        gps_weeks = gps_weeks.tolist()
        gps_seconds = gps_seconds.tolist()

        P1 = obs['C1'][np.where(epoch[j]==obs['TOW'])]
        P2 = obs['P2'][np.where(epoch[j]==obs['TOW'])]
#       do not know why this is here
#       S1 = obs['S1'][np.where(epoch[j]==obs['TOW'])]
        print('WEEK', gps_weeks, 'SECONDS', gps_seconds)
        k=0
        # set up the A matrix with empty stuff
        M=len(sats)
        print('Number of Satellites: ' , M)
        A=np.zeros((M,4))
        Y=np.zeros(M)
        elmask = np.zeros(M, dtype=bool)
        for prn in sats:
            closest = myfindephem(gps_weeks, gps_seconds, ephemdata, prn) #           
            p1=P1[k]
            p2=P2[k]
            p3 = ionofree(p1,p2)
            N=len(closest)
            if N > 0:    
                satv, relcorr = propagate(gps_weeks, gps_seconds, closest)
#               print("sat coor",gps_weeks,gps_seconds,satv)
                r=np.subtract(satv,recv)
                elea = elev_angle(u, r) # 
                tropocorr = zd/np.sin(elea)
                R,satv = mygeometric_range(gps_weeks, gps_seconds, prn, recv, closest)
                A[k]=-np.array([satv[0]-recv[0],satv[1]-recv[1],satv[2]-recv[2],R])/R
                elea = elev_angle(u,np.subtract(satv,recv))
                elmask[k] = elea*180/np.pi > emask
#               satellite clock correction
                satCorr = satclock(gps_weeks, gps_seconds, prn, closest)
                # prefit residual, ionosphere free pseudorange - geometric rnage
                # plus SatelliteClock - relativity and troposphere corrections
                Y[k] = p3-R+satCorr  -relcorr-tropocorr
#               print(int(prn), k,p1,R, p1-R)
                print(" {0:3.0f} {1:15.4f} {2:15.4f} {3:15.4f} {4:10.5f}".format(prn, p3, R, Y[k], 180*elea/np.pi))
                k +=1
# only vaguest notion of what is going on here - code from Ryan Hardy                
#       applying an elevation mask
        Y=np.matrix(Y[elmask]).T
        A=np.matrix(A[elmask])
        soln = np.array(np.linalg.inv(A.T*A)*A.T*Y).T[0]
#       update Cartesian coordinates
        newPos = recv+soln[:3]
        print('New Cartesian solution', newPos)
#       receiver clock solution
#        rec_clock = soln[-1]
        lat, lon, h = xyz2llhd(newPos)
        print("%15.7f %15.7f %12.4f "% (lat,  lon,h) )
# print("%15.5f"% xyz[0])
