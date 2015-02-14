# this is example-file: configure.ac

# initial information about the project
AC_INIT([dmwtest],[0.1],[Gerard Toonstra])

# check if the source folder is available
AC_CONFIG_SRCDIR([src/main.c])

# check for C preprocessor and compiler
AC_PROG_CC

# automake initialization (mandatory) including a check for automake API version >= 1.9
AM_INIT_AUTOMAKE([1.9])

# use the C compiler for the following checks
AC_LANG([C])

# Checks for header files.
AC_HEADER_STDC

# Checks for typedefs, structures, and compiler characteristics.
AC_TYPE_SIZE_T

PKG_CHECK_MODULES([DMW], libdmw >= 0.1)

# distribute additional compiler and linker flags among Makefiles
# --> set and change these variables instead of CXXFLAGS or LDFLAGS (for user only)
AC_SUBST([AM_CFLAGS])
AC_SUBST([AM_LDFLAGS])

# files to generate via autotools (prepare .am or .in source files)
AC_CONFIG_FILES([Makefile])
AC_CONFIG_FILES([src/Makefile])

# finally this generates the Makefiles etc. for the build
AC_OUTPUT

