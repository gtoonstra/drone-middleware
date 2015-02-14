#include <string.h>

#include "libdmw.h"
#include "zhelpers.h"

#define MAX_APP_NAME      32
#define ERR_STRING_LEN    256
#define MAX_TOPIC_LEN     128

static char appname[ MAX_APP_NAME + 1 ];
static char lasterr[ ERR_STRING_LEN ];

static void *context;
static void *subscriber;
static void *publisher;

static int get_topic( char *topic, const char *msg_class, const char *msg_name, const char *sender );

int dmw_init( const char *name )
{
    int i = 0;

    if (strlen( name ) > MAX_APP_NAME ) {
        strcpy( lasterr, "Application name too long." );
        return -1;
    }
    for ( i = 0; i < strlen( name ); i++ ) {
        if ( !isalnum( name[i] ) || isupper( name[i] ) ) {
            strcpy( lasterr, "Application name contains invalid character. Only lower-case and digits allowed." );
            return -2;
        }
    }
    strcpy( appname, name );

    context = zmq_ctx_new ();
    subscriber = zmq_socket (context, ZMQ_SUB);
    zmq_connect (subscriber, "tcp://localhost:5558");
    publisher = zmq_socket (context, ZMQ_PUB);
    zmq_connect (publisher, "tcp://localhost:5557");

    return 0;
}

int dmw_subscribe( const char *msg_class, const char *msg_name, const char *sender, msg_callback_t *callback )
{
    char buf[ MAX_TOPIC_LEN + 1 ] = {"\0"};

    int rc = get_topic( buf, msg_class, msg_name, sender );
    if ( rc != 0 ) {
        return rc;
    }

    zmq_setsockopt(subscriber, ZMQ_SUBSCRIBE, buf, strlen(buf) );
    return 0;
}

int dmw_unsubscribe( const char *msg_class, const char *msg_name, const char *sender )
{
    char buf[ MAX_TOPIC_LEN + 1 ] = {"\0"};

    int rc = get_topic( buf, msg_class, msg_name, sender );
    if ( rc != 0 ) {
        return rc;
    }

    zmq_setsockopt(subscriber, ZMQ_UNSUBSCRIBE, buf, strlen(buf) );
    return 0;
}

int dmw_publish( const char *msg_class, const char *msg_name, const char *bytes, int len )
{
    char buf[ MAX_TOPIC_LEN + 1 ] = {"\0"};

    int rc = get_topic( buf, msg_class, msg_name, appname );
    if ( rc != 0 ) {
        return rc;
    }

    int size = zmq_send (publisher, bytes, len, 0);
    return size;
}

void dmw_get_error( char *errorstring )
{
    if ( strlen( lasterr ) == 0 ) {
        errorstring = NULL;
        return;
    }
    errorstring = (char *)malloc( strlen( lasterr ) + 1 );
    strcpy( errorstring, lasterr );
    memset( lasterr, 0x00, ERR_STRING_LEN );
}

static int get_topic( char *topic, const char *msg_class, const char *msg_name, const char *sender )
{
    int len = 0;

    if ( ( msg_class == NULL ) || ( strlen( msg_class ) == 0 ) ) {
        strcpy( lasterr, "The message class must have a value." );
        return -3;
    }
    len = strlen( msg_class ) + 2;
    if (( msg_name != NULL ) && ( strlen( msg_name ) > 0 ) ) {
        len += strlen( msg_name );
        if ( len > MAX_TOPIC_LEN ) {
            strcpy( lasterr, "The topic name would be too long (max 128 characters)." );
            return -4;
        }
        if (( sender != NULL ) && ( strlen( sender ) > 0 ) ) {
            len += strlen( sender );
            if ( len > MAX_TOPIC_LEN ) {
                strcpy( lasterr, "The topic name would be too long (max 128 characters)." );
                return -4;
            }
            // all parameters filled in.
            sprintf( topic, "%s.%s.%s", msg_class, msg_name, sender );
        } else {
            // only msg class and msg name 
            sprintf( topic, "%s.%s", msg_class, msg_name );
        }    
    } else {
        // only msg class 
        sprintf( topic, "%s", msg_class );
    }
    return 0;
}

