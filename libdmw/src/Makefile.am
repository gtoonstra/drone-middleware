# additional include pathes necessary to compile the C library
AM_CFLAGS = -I$(top_srcdir)/src @AM_CFLAGS@

###############################################################################
# THE LIBRARIES TO BUILD
###############################################################################

# the library names to build (note we are building static libs only)
lib_LIBRARIES = libdmw.a

#libdmw_a_CFLAGS = $(ZEROMQ_CFLAGS)
#libdmw_a_LIBADD= $(ZEROMQ_LIBS)

# where to install the headers on the system
libdmw_adir = $(includedir)/libdmw

# the list of header files that belong to the library (to be installed later)
libdmw_a_HEADERS =	libdmw.h

# the sources to add to the library and to add to the source distribution
libdmw_a_SOURCES =	$(libdmw_a_HEADERS) \
                    libdmw.c

pkgconfigdir = $(libdir)/pkgconfig
pkgconfig_DATA = libdmw.pc

###############################################################################

