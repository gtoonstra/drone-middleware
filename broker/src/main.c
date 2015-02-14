#include "zhelpers.h"

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

    rc = zmq_proxy (frontend, backend, NULL);

    // We never get here…
    zmq_close (frontend);
    zmq_close (backend);
    zmq_ctx_destroy (context);
    return 0;
}

