#include <stdio.h>
#include <libdmw.h>
#include <pthread.h>

static void test_init_fail_function( const char *appname );

static msg_callback_t subscription_print;

void *rcv_messages(void *threadid)
{
    long tid;
    tid = (long)threadid;
    int rc = dmw_run();
}

void *rcv_messages2(void *threadid)
{
    long tid;
    char *errstr;

    tid = (long)threadid;

    int rc = dmw_init_sub();
    if ( rc != 0 ) {
        dmw_get_error( &errstr );
        printf( "%s\n", errstr );
        return;
    }    

    rc = dmw_subscribe( "telemetry", "position", NULL, subscription_print, NULL );
    if ( rc != 0 ) {
        dmw_get_error( &errstr );
        printf( "%s\n", errstr );
        return;
    }    

    printf( "Now subscribed. Let's listen for messages\n" );

    rc = dmw_run();
}

int main (int argc, char *argv[] )
{
    int rc;
    char *errstr;
    pthread_t thread;

    dmw_init();

    // may not use capitals
    test_init_fail_function( "abcdeF" );
    // may not use non isalnum or spaces
    test_init_fail_function( "abc 235" );
    // 33 is not allowed
    test_init_fail_function( "abcdefghijklmnopqrstuvwxyz1234567" );

    rc = dmw_init_pub( "abcdefghijklmnopq1234567890" );
    if ( rc != 0 ) {
        dmw_get_error( &errstr );
        printf( "%s\n", errstr );
    } 
    
    rc = pthread_create(&thread, NULL, rcv_messages, (void *)1);
    usleep( 500000 );

    rc = dmw_subscribe( "telemetry", "position", NULL, subscription_print, NULL );
    if ( rc != 0 ) {
        printf("Ok, failed because need to init first.\n" );
        dmw_get_error( &errstr );
        printf( "%s\n", errstr );
    }

    // now using correctly separate thread to keep correct context.
    rc = pthread_create(&thread, NULL, rcv_messages2, (void *)1);
    usleep( 1000000 );

    rc = dmw_publish( "telemetry", "position", "hello", 5 );
    if ( rc <= 0 ) {
        printf("Publish failed\n" );
        dmw_get_error( &errstr );
        printf( "%s\n", errstr );
        return -1;
    }
    printf( "Ok, published. Should have received something too.\n" );

    // Waiting for unsubscribe
    usleep( 500000 );

    rc = dmw_publish( "telemetry", "position", "hello", 5 );
    if ( rc <= 0 ) {
        printf("Publish failed\n" );
        dmw_get_error( &errstr );
        printf( "%s\n", errstr );
        return -1;
    }
    printf( "Ok, published again.\n" );

    usleep( 5000000 );

    return 0;
}

static void test_init_fail_function( const char *appname )
{
    int rc = dmw_init_pub( appname );
    char *errstr;

    if ( rc == 0 ) {
        printf( "FAIL: %s allowed. should not happen.\n", appname );
        return;
    }
    dmw_get_error( &errstr );
    printf( "%s\n", errstr );
}

static void subscription_print( const char *msg_class, const char *msg_name, const char *sender, const char *message, void *user_data )
{
    char *errstr;

    printf( "callback: %s.%s.%s %s\n", msg_class, msg_name, sender, message );

    int rc = dmw_unsubscribe( "telemetry", "position", NULL );
    if ( rc != 0 ) {
        printf("Unsubscribe failed\n" );
        dmw_get_error( &errstr );
        printf( "%s\n", errstr );
    }
    printf( "Ok, unsubscribed.\n" );
}

