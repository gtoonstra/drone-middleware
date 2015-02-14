#include <Python.h>
#include <libdmw.h>

static PyObject *PyDmwError;


/*
typedef void (msg_callback_t)( const char *msg_class, const char *msg_name, const char *sender, const char *message );
*/

static PyObject *py_dmw_init_pub(PyObject *self, PyObject *args);
static PyObject *py_dmw_init_sub(PyObject *self, PyObject *args);
static PyObject *py_dmw_subscribe(PyObject *self, PyObject *args);
static PyObject *py_dmw_unsubscribe(PyObject *self, PyObject *args);
static PyObject *py_dmw_publish(PyObject *self, PyObject *args);
static PyObject *py_dmw_run(PyObject *self, PyObject *args);

static char py_init_pub_doc[] = "Initialize the publishing functions of the library";
static char py_init_sub_doc[] = "Initialize the subscription functions of the library";
static char py_sub_doc[] = "Subscribe to a topic";
static char py_unsub_doc[] = "Unsubscribe from a topic";
static char py_pub_doc[] = "Publish a message to a topic";
static char py_loop_doc[] = "Start the loop to process messages";

static PyMethodDef DmwMethods[] = {
    {"init_pub", py_dmw_init_pub, METH_VARARGS, py_init_pub_doc},
    {"init_sub", py_dmw_init_sub, METH_VARARGS, py_init_sub_doc},
    {"subscribe", py_dmw_subscribe, METH_VARARGS, py_sub_doc},
    {"unsubscribe", py_dmw_unsubscribe, METH_VARARGS, py_unsub_doc},
    {"publish", py_dmw_publish, METH_VARARGS, py_pub_doc},
    {"run", py_dmw_run, METH_VARARGS, py_loop_doc},
    {NULL, NULL, 0, NULL}
};

static void redirect_callback( const char *msg_class, const char *msg_name, const char *sender, const char *message, void *user_data )
{
    PyObject *arglist;
    PyObject *result;

    printf( "%s.%s.%s.%08x: %s\n", msg_class, msg_name, sender, user_data, message );

    /* Time to call the callback */
    arglist = Py_BuildValue("(ssss)", msg_class, msg_name, sender, message);
    result = PyEval_CallObject(user_data, arglist);
    Py_DECREF(arglist);
}

PyMODINIT_FUNC
initlibpydmw(void)
{
    PyObject *m;

    m = Py_InitModule("libpydmw", DmwMethods);
    if (m == NULL)
        return;

    PyDmwError = PyErr_NewException("pydmw.error", NULL, NULL);
    Py_INCREF(PyDmwError);
    PyModule_AddObject(m, "error", PyDmwError);
}

//int dmw_init_pub( const char *name );
static PyObject *
py_dmw_init_pub(PyObject *self, PyObject *args)
{
    const char *name;
    int rc;

    if (!PyArg_ParseTuple(args, "s", &name))
        return NULL;
    rc = dmw_init_pub( name );
    return PyLong_FromLong(rc);
}

//int dmw_init_sub( void );
static PyObject *
py_dmw_init_sub(PyObject *self, PyObject *args)
{
    int rc = dmw_init_sub();
    return PyLong_FromLong(rc);
}

// int dmw_subscribe( const char *msg_class, const char *msg_name, const char *sender, msg_callback_t *callback, void *user_data );
static PyObject *
py_dmw_subscribe(PyObject *self, PyObject *args)
{
    const char *msg_class;
    const char *msg_name;
    const char *sender;

    PyObject *result = NULL;
    PyObject *temp;

    if (PyArg_ParseTuple(args, "sssO:set_callback", &msg_class, &msg_name, &sender, &temp )) {
        if (!PyCallable_Check(temp)) {
            PyErr_SetString(PyDmwError, "parameter must be callable");
            return NULL;
        }
        Py_XINCREF(temp);         /* Add a reference to new callback */
        // Py_XDECREF(my_callback);  /* Dispose of previous callback */
        // my_callback = temp;       /* Remember new callback */
        /* Boilerplate to return "None" */
        Py_INCREF(Py_None);
        result = Py_None;
    } else {
        PyErr_SetString(PyDmwError, "Could not parse parameters");
        return NULL;
    }

    int rc = dmw_subscribe( msg_class, msg_name, sender, redirect_callback, temp );
    return PyLong_FromLong( rc );
}

//int dmw_unsubscribe( const char *msg_class, const char *msg_name, const char *sender );
static PyObject *
py_dmw_unsubscribe(PyObject *self, PyObject *args)
{
    const char *msg_class;
    const char *msg_name;
    const char *sender;
    int rc;

    if (! PyArg_ParseTuple(args, "sss", &msg_class, &msg_name, &sender ))
        return NULL;

    // TODO: Py_XDECREF(my_callback);
    rc = dmw_unsubscribe( msg_class, msg_name, sender );

    return PyLong_FromLong( rc );
}

//int dmw_publish( const char *msg_class, const char *msg_name, const char *bytes, int len );
static PyObject *
py_dmw_publish(PyObject *self, PyObject *args)
{
    const char *msg_class;
    const char *msg_name;
    const char *bytes;
    int len;
    int rc;

    if (! PyArg_ParseTuple(args, "sssi", &msg_class, &msg_name, &bytes, &len ))
        return NULL;

    rc = dmw_publish( msg_class, msg_name, bytes, len );
    return PyLong_FromLong(rc);
}
//int dmw_run();
static PyObject *
py_dmw_run(PyObject *self, PyObject *args)
{
    int rc = dmw_run();
    return PyLong_FromLong(rc);
}

