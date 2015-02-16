#ifndef DMW_AVAHI_H
#define DMW_AVAHI_H

int avahi_init( const char *name );
int avahi_loop( int msecs );
int avahi_get_pub_service( char *ip, int *port );
int avahi_get_sub_service( char *ip, int *port );

#endif

