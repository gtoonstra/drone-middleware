# this is example-file: configure.ac

# initial information about the project
AC_INIT([libpydmw],[0.1],[gtoonstra])
LT_INIT
AM_PATH_PYTHON([2.6])

# check if the source folder is correct
AC_CONFIG_SRCDIR([src/pydmw.c])

# Checks for programs

# check for C compiler and the library compiler
AC_PROG_CC

# automake initialisation (mandatory) and check for minimal automake API version 1.9
AM_INIT_AUTOMAKE([1.9])

# use the C compiler for the following checks
AC_LANG([C])

# Checks for header files.
AC_HEADER_STDC

# Checks for typedefs, structures, and compiler characteristics.
AC_TYPE_SIZE_T

PKG_CHECK_MODULES([LIBDMW], libdmw >= 0.1)
PKG_CHECK_MODULES([PYTHON], python >= 0.1)

# distribute additional compiler and linker flags
# --> set these variables instead of CXXFLAGS or LDFLAGS
AC_SUBST([AM_CFLAGS])
AC_SUBST([AM_LDFLAGS])
AC_SUBST([LIBS])

# files to generate via autotools (.am or .in source files)
AC_CONFIG_FILES([Makefile])
AC_CONFIG_FILES([src/Makefile])

# generate the final Makefile etc.
AC_OUTPUT

