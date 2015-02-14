#ifndef LIBDMW_H
#define LIBDMW_H

typedef void (msg_callback_t)( const char *msg_class, const char *msg_name, const char *message );

int dmw_init( const char *name );
int dmw_subscribe( const char *msg_class, const char *msg_name, const char *sender, msg_callback_t *callback );
int dmw_unsubscribe( const char *msg_class, const char *msg_name, const char *sender );
int dmw_publish( const char *msg_class, const char *msg_name, const char *bytes, int len );
void dmw_get_error( char *errorstring );

#endif

