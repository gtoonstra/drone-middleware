#ifndef LIBDMW_H
#define LIBDMW_H

typedef void (msg_callback_t)( const char *msg_class, const char *msg_name, const char *sender, const char *message, void *user_data );

int dmw_init_pub( const char *name );
int dmw_init_sub( void );
int dmw_subscribe( const char *msg_class, const char *msg_name, const char *sender, msg_callback_t *callback, void *user_data );
int dmw_unsubscribe( const char *msg_class, const char *msg_name, const char *sender );
int dmw_publish( const char *msg_class, const char *msg_name, const char *bytes, int len );
void dmw_get_error( char **errorstring );
int dmw_run();

#endif

