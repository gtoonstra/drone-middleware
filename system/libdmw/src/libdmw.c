#include <string.h>

#include "libdmw.h"
#include "zhelpers.h"
#include "uthash.h"

#define MAX_APP_NAME      32
#define ERR_STRING_LEN    256
#define MAX_TOPIC_LEN     128

static char appname[ MAX_APP_NAME + 1 ];
static char lasterr[ ERR_STRING_LEN ];

static void *context = NULL;
static void *subscriber = NULL;
static void *publisher = NULL;

struct subscription_t {
    char topic[MAX_TOPIC_LEN]; /* key */
    msg_callback_t *cb;
    void *user_data;
    UT_hash_handle hh; /* makes this structure hashable */
};

struct subscription_t *subscriptions = NULL;

static int get_topic( char *topic, const char *msg_class, const char *msg_name, const char *sender );

int dmw_init_pub( const char *name )
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

    if ( !context ) {
        context = zmq_ctx_new ();
    }
    publisher = zmq_socket (context, ZMQ_PUB);
    zmq_connect (publisher, "tcp://localhost:5557");

    return 0;
}

int dmw_init_sub( void )
{
    int i = 0;

    if ( !context ) {
        context = zmq_ctx_new ();
    }
    subscriber = zmq_socket (context, ZMQ_SUB);
    zmq_connect (subscriber, "tcp://localhost:5558");

    return 0;
}

int dmw_subscribe( const char *msg_class, const char *msg_name, const char *sender, msg_callback_t *callback, void *user_data )
{
    char buf[ MAX_TOPIC_LEN + 1 ] = {"\0"};

    if ( !subscriber ) {
        strcpy( lasterr, "Subscribers are not initialized. Call dwm_init_sub first." );
        return -5;
    }

    int rc = get_topic( buf, msg_class, msg_name, sender );
    if ( rc != 0 ) {
        return rc;
    }

    zmq_setsockopt(subscriber, ZMQ_SUBSCRIBE, buf, strlen(buf) );

    struct subscription_t *sub;
    HASH_FIND_STR(subscriptions, buf, sub);
    if (sub==NULL) {
        sub = (struct subscription_t *)malloc( sizeof(struct subscription_t) );
        strcpy( sub->topic, buf );
        sub->cb = callback;
        sub->user_data = user_data;
        HASH_ADD_STR( subscriptions, topic, sub );
    }

    return 0;
}

int dmw_unsubscribe( const char *msg_class, const char *msg_name, const char *sender )
{
    char buf[ MAX_TOPIC_LEN + 1 ] = {"\0"};

    if ( !subscriber ) {
        strcpy( lasterr, "Subscribers are not initialized. Call dwm_init_sub first." );
        return -5;
    }

    int rc = get_topic( buf, msg_class, msg_name, sender );
    if ( rc != 0 ) {
        return rc;
    }

    zmq_setsockopt(subscriber, ZMQ_UNSUBSCRIBE, buf, strlen(buf) );

    struct subscription_t *s;
    HASH_FIND_STR( subscriptions, buf, s );
    if ( s != NULL ) {
        HASH_DEL( subscriptions, s);
        free( s );
    }

    return 0;
}

int dmw_publish( const char *msg_class, const char *msg_name, const char *bytes, int len )
{
    char buf[ MAX_TOPIC_LEN + 1 ] = {"\0"};

    if ( !publisher ) {
        strcpy( lasterr, "Publishing is not initialized. Call dwm_init_pub first." );
        return -6;
    }

    int rc = get_topic( buf, msg_class, msg_name, appname );
    if ( rc != 0 ) {
        return rc;
    }

    // send topic first. This way it's possible to figure out how to route message later.
    int size = zmq_send (publisher, buf, strlen (buf), ZMQ_SNDMORE);
    size = zmq_send (publisher, bytes, len, 0);

    return size;
}

void dmw_get_error( char **errorstring )
{
    if ( strlen( lasterr ) == 0 ) {
        errorstring = NULL;
        return;
    }
    *errorstring = (char *)malloc( strlen( lasterr ) + 1 );
    strcpy( *errorstring, lasterr );
    memset( lasterr, 0x00, ERR_STRING_LEN );
}

int dmw_run()
{
    char *saveptr;
    char *msg_class;
    char *msg_name;
    char *sender;
    char buf[MAX_TOPIC_LEN + 1] = {"\0"};

    if ( !subscriber ) {
        strcpy( lasterr, "Subscribers are not initialized. Call dwm_init_sub first." );
        return -5;
    }

    while (1) {
        char *topic = s_recv (subscriber);
        char *msg = s_recv (subscriber);

        msg_class = strtok_r( topic, ".", &saveptr );
        msg_name = strtok_r( NULL, ".", &saveptr );
        sender = strtok_r( NULL, ".", &saveptr );

        struct subscription_t *s;
        HASH_FIND_STR( subscriptions, topic, s );
        if ( s == NULL ) {
            sprintf( buf, "%s.%s", msg_class, msg_name );
            HASH_FIND_STR( subscriptions, buf, s );
            if ( s == NULL ) {
                HASH_FIND_STR( subscriptions, msg_class, s );
            }
        }

        printf( "topic: %s, find str: %08x\n", topic, s );

        if ( s != NULL ) {
            s->cb( msg_class, msg_name, sender, msg, s->user_data );
        }
        free( topic );
        free( msg );
    }
    return 0;
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

