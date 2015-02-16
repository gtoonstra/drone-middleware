# additional include pathes necessary to compile the C library
AM_CFLAGS = -I$(top_srcdir)/src @AM_CFLAGS@

###############################################################################
# THE LIBRARIES TO BUILD
###############################################################################

# the library names to build (note we are building static libs only)
pyexec_LTLIBRARIES = libpydmw.la

libpydmw_la_CFLAGS = $(LIBDMW_CFLAGS) $(PYTHON_CFLAGS)
libpydmw_la_LIBADD= $(LIBDMW_LIBS) $(PYTHON_LIBS)

# the sources to add to the library and to add to the source distribution
libpydmw_la_SOURCES =	pydmw.c

###############################################################################

