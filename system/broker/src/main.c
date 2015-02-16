#include "zhelpers.h"

static void *proxy_capture (void *ctx)
{
    int zerr = 0 ;
    int rRes;
    void *worker = zmq_socket (ctx, ZMQ_DEALER);
    zerr = zmq_connect (worker, "ipc://capture.ipc");

    if (zerr != 0)
    {
        printf ("\n-------------- > proxy_capture bind error : %s\n", zmq_strerror(errno));
        return 0;
    }

    while (1) {
        char buf [256];
        int rc = zmq_recv (worker, buf, 256, 0); 
        assert (rc != -1);
        printf ("Capture value : %s !\n", buf);
        memset( buf, 0x00, 256 );
    }
}

int main (int argc, char *argv[] )
{
    void *context = (void *)zmq_ctx_new();
    void *frontend = zmq_socket (context, ZMQ_XSUB);
    assert (frontend);
    int rc = zmq_bind (frontend, "tcp://*:5557");
    assert( rc == 0 );
    void *backend = zmq_socket (context, ZMQ_XPUB);
    assert (backend);
    rc = zmq_bind (backend, "tcp://*:5558");
    assert( rc == 0 );


    void *capture = zmq_socket (context, ZMQ_DEALER);
    rc = zmq_bind (capture, "ipc://capture.ipc");

    if (rc != 0)
    {
        printf ("\nCapture bind error : %s\n", zmq_strerror(errno));
        return 0;
    }

    pthread_t capworker;
    rc = pthread_create(&capworker, NULL, proxy_capture, context);


    rc = zmq_proxy (frontend, backend, capture);
    //rc = zmq_proxy (frontend, backend, NULL );

    // We never get here…
    zmq_close (frontend);
    zmq_close (backend);
    zmq_ctx_destroy (context);
    return 0;
}

