import logging
import sys
from numpy import *
import math

logger = logging.getLogger( "Conversions" )

f = 1.0/298.257223563 	# Ellipsoid's flatness
e = math.sqrt(f*(2.0-f))		# Ellipsoid's Eccentricity
rp = 6356752.31424518	# [m] ; semiminor axis: radius polar   // b=6356752:31424518
re = 6378137.0 			# [m] ; semimajor axis: radius equator // a=6378137

""" This is an object to perform conversions between the ECEF, tangential plane (TGP, NED, ENU) and WGS-84"""

class Conversions( object ):
    def __init__(self):
        super( Conversions, self ).__init__()
        self.originset = False
        self.T_el = zeros( (3,3), dtype=float )
        self.x0_ecef = zeros( 3, dtype=float )
        logger.info("Initializing conversions")

    def tgp2wgs( self, tgp_x, tgp_y, tgp_z ):
        x,y,z = self.tgp2ecef( tgp_x, tgp_y, tgp_z )
        return self.ecef2wgs( x, y, z )

    def wgs2tgp( self, wgs_lat, wgs_lon, h ):
        x, y, z = self.wgs2ecef( wgs_lat, wgs_lon, h )
        return self.ecef2tgp( x, y, z )

    def ecef2tgp( self, ecef_x, ecef_y, ecef_z ):
        x_l = zeros( 3, dtype=float )
        _x_ecef = zeros( 3, dtype=float )
        _x_ecef[0] = ecef_x
        _x_ecef[1] = ecef_y
        _x_ecef[2] = ecef_z

        if (self.originset):
            x_temp = _x_ecef - self.x0_ecef
            elT = self.T_el.T

            x_l[ 0 ] = elT[0,0] * x_temp[0] + elT[1,0] * x_temp[1] + elT[2,0] * x_temp[2]
            x_l[ 1 ] = elT[0,1] * x_temp[0] + elT[1,1] * x_temp[1] + elT[2,1] * x_temp[2]
            x_l[ 2 ] = elT[0,2] * x_temp[0] + elT[1,2] * x_temp[1] + elT[2,2] * x_temp[2]

            # return x_l[0], x_l[ 1 ], x_l[ 2 ]
            # END, instead of NED
            return x_l[0], x_l[1], x_l[2]
        else:
            return 0.0, 0.0, 0.0

    def tgp2ecef( self, tgp_x, tgp_y, tgp_z ):
        vx_l = zeros( 3, dtype=float )
        _vx_ecef = zeros( 3, dtype=float )

        if (self.originset):
            vx_l[ 0 ] = tgp_x
            vx_l[ 1 ] = tgp_y
            vx_l[ 2 ] = tgp_z

            elT = self.T_el

            _vx_ecef[ 0 ] = elT[0,0] * vx_l[0] + elT[1,0] * vx_l[1] + elT[2,0] * vx_l[2]
            _vx_ecef[ 1 ] = elT[0,1] * vx_l[0] + elT[1,1] * vx_l[1] + elT[2,1] * vx_l[2]
            _vx_ecef[ 2 ] = elT[0,2] * vx_l[0] + elT[1,2] * vx_l[1] + elT[2,2] * vx_l[2]

            _vx_ecef[ 0 ] = _vx_ecef[ 0 ] + self.x0_ecef[0]
            _vx_ecef[ 1 ] = _vx_ecef[ 1 ] + self.x0_ecef[1]
            _vx_ecef[ 2 ] = _vx_ecef[ 2 ] + self.x0_ecef[2]

            return _vx_ecef[0], _vx_ecef[ 1 ], _vx_ecef[ 2 ]
        else:
            return 0.0, 0.0, 0.0

    def setOriginEcef( self, _x0, _y0, _z0 ):
        self.x0_ecef[0] = _x0
        self.x0_ecef[1] = _y0
        self.x0_ecef[2] = _z0

        lat, lon, alt = self.calc_parameters( _x0, _y0, _z0 )

        # Rotation from ECEF to Local
        self.T_el[0,0] = -cos(lon)*sin(lat)
        self.T_el[1,0] = -sin(lon)
        self.T_el[2,0] = -cos(lon)*cos(lat)
        self.T_el[0,1] = -sin(lon)*sin(lat)
        self.T_el[1,1] = cos(lon)
        self.T_el[2,1] = -sin(lon)*cos(lat)
        self.T_el[0,2] = cos(lat)
        self.T_el[1,2] = 0.0
        self.T_el[2,2] = -sin(lat)

        self.originset = True

    def setOriginWgs( self, wgs_north, wgs_east, altitude):
        ecef_x, ecef_y, ecef_z = self.wgs2ecef( wgs_north, wgs_east, altitude )
        self.setOriginEcef( ecef_x, ecef_y, ecef_z )
        self.originset = True

    def ecef2wgs( self, ecef_x, ecef_y, ecef_z ):
        # ECEF 2 Wold Grid System 1984
        lat, lon, alt = self.calc_parameters( ecef_x, ecef_y, ecef_z )
        wgs_lat  = lat * 180.0 / 3.1415926535897932384626433832795
        wgs_lon = lon * 180.0 / 3.1415926535897932384626433832795
        return wgs_lat, wgs_lon, alt

    def wgs2ecef( self, wgs_north, wgs_east, h ):
        lat = wgs_north / 180.0 * 3.1415926535897932384626433832795
        lon = wgs_east / 180.0 * 3.1415926535897932384626433832795

        # WGS -> ECEF
        N = re / math.sqrt(1.0 - e*e*math.sin(lat)*math.sin(lat) )

        return math.cos(lat) * (N + h) * math.cos(lon), math.cos(lat) * (N + h) * math.sin(lon), math.sin(lat) * ((rp*rp)/(re*re)*N + h)

    def velocity_ecef2tgp( self, ecef_vx, ecef_vy, ecef_vz ):
        vx_l = zeros( 3, dtype=float )
        _vx_ecef = zeros( 3, dtype=float )

        if (self.originset):
            _vx_ecef[ 0 ] = ecef_vx
            _vx_ecef[ 1 ] = ecef_vy
            _vx_ecef[ 2 ] = ecef_vz

            elT = self.T_el.T

            vx_l[ 0 ] = elT[0,0] * _vx_ecef[0] + elT[1,0] * _vx_ecef[1] + elT[2,0] * _vx_ecef[2]
            vx_l[ 1 ] = elT[0,1] * _vx_ecef[0] + elT[1,1] * _vx_ecef[1] + elT[2,1] * _vx_ecef[2]
            vx_l[ 2 ] = elT[0,2] * _vx_ecef[0] + elT[1,2] * _vx_ecef[1] + elT[2,2] * _vx_ecef[2]

            #return vx_l[0], vx_l[ 1 ], vx_l[ 2 ]
            # END...
            return vx_l[1], vx_l[0], vx_l[2]
        else:
            return 0.0, 0.0, 0.0

    def velocity_tgp2ecef( self, tgp_vx, tgp_vy, tgp_vz ):
        vx_l = zeros( 3, dtype=float )
        _vx_ecef = zeros( 3, dtype=float )

        if (self.originset):
            vx_l[ 0 ] = tgp_vx
            vx_l[ 1 ] = tgp_vy
            vx_l[ 2 ] = tgp_vz

            elT = self.T_el

            _vx_ecef[ 0 ] = elT[0,0] * vx_l[0] + elT[1,0] * vx_l[1] + elT[2,0] * vx_l[2]
            _vx_ecef[ 1 ] = elT[0,1] * vx_l[0] + elT[1,1] * vx_l[1] + elT[2,1] * vx_l[2]
            _vx_ecef[ 2 ] = elT[0,2] * vx_l[0] + elT[1,2] * vx_l[1] + elT[2,2] * vx_l[2]

            return _vx_ecef[0], _vx_ecef[ 1 ], _vx_ecef[ 2 ]
        else:
            return 0.0, 0.0, 0.0

    def calc_parameters( self, _x0, _y0, _z0 ):
        Xe = _x0
        Ye = _y0
        Ze = _z0

        def SQ(x):
            return x*x

        def CUBIC(x):
            return ((x)*(x)*(x))

        # Earth position from ECEF to NorthEastDown (Local)
        lon = math.atan2(Ye,Xe)

        p  = math.sqrt( SQ(Xe)+SQ(Ye) )
        h = zeros( 2, dtype=float )
        lamdum = zeros( 2, dtype=float )
        N = array( [re, re] )
        alt = 0.0
        for i in arange( 0, 100 ):
            if ( abs(p) > 0.0 ):
                lamdum[1] = math.atan( (Ze + SQ(e) * N[0] * math.sin( lamdum[0] ) ) / p)
            else:
                lamdum[1] = 0.0
            N[1] = re / sqrt(1.0 - SQ(e) * SQ( math.sin(lamdum[0]) )   )
            h[1] = p / cos( lamdum[0] ) - N[0]
            if ( (fabs(h[1])-h[0]) == 0 ):
                alt = h[1]
                break
            h[0]=h[1]
            N[0]=N[1]
            lamdum[0] = lamdum[1]

        E = math.sqrt(re*re-rp*rp)
        F = 54.0 * SQ(rp) * SQ(Ze)
        G = SQ(p) + (1.0 - SQ(e)) * SQ(Ze) - SQ(e) * SQ(E)
        c = ( SQ(SQ(e)) * F * SQ(p) ) / CUBIC(G)
        s = math.pow(( 1.0 + c + sqrt( SQ(c) + 2 * c) ), (1.0/3.0))
        P = F / (3* SQ(s+(1.0/s)+1.0) * SQ(G))
        Q = sqrt(1.0+2.0* SQ(SQ(e)) * P)
        r0= -(P * SQ(e) * p ) / (1.0+Q) + sqrt(0.5 * SQ(re) * (1.0+(1.0/Q))-(P*(1.0-SQ(e))*SQ(Ze))/(Q*(1.0+Q))-0.5 * P * SQ(p))
        V = sqrt( SQ(p- SQ(e) * r0) + (1.0-SQ(e)) * SQ(Ze) )
        z0= ( SQ(rp) * Ze) / (re * V)
        e_a = re * e / rp
        if ( abs(p) > 0.0 ):
            lat = math.atan( ( Ze + SQ(e_a) * z0) / p )
        else:
            lat = 0.0

        return lat, lon, alt

