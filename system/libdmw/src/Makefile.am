# additional include pathes necessary to compile the C library
AM_CFLAGS = -I$(top_srcdir)/src @AM_CFLAGS@

###############################################################################
# THE LIBRARIES TO BUILD
###############################################################################

# the library names to build (note we are building static libs only)
lib_LTLIBRARIES = libdmw.la

libdmw_la_CFLAGS = $(ZEROMQ_CFLAGS) $(AVAHI_CFLAGS)
libdmw_la_LIBADD= $(ZEROMQ_LIBS) $(AVAHI_LIBS)

# where to install the headers on the system
libdmw_ladir = $(includedir)/libdmw

# the list of header files that belong to the library (to be installed later)
libdmw_la_HEADERS =	libdmw.h

# the sources to add to the library and to add to the source distribution
libdmw_la_SOURCES =	$(libdmw_a_HEADERS) \
                    libdmw.c dmw_avahi.c dmwavahi.h

pkgconfigdir = $(libdir)/pkgconfig
pkgconfig_DATA = libdmw.pc

###############################################################################

