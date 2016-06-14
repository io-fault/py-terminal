/*
 * low level tty access
 *
 * Tools for working with teletype devices.
 */
#include <sys/ttycom.h>
#include <sys/ioctl.h>

#include <fault/roles.h>
#include <fault/internal.h>
#include <fault/python/environ.h>

static PyObject *
dimensions(PyObject *self, PyObject *args)
{
	struct winsize ws;
	int fd, r;
	PyObject *rob;

	if (!PyArg_ParseTuple(args, "i", &fd))
		return(NULL);

	Py_BEGIN_ALLOW_THREADS
	r = ioctl((int) fd, TIOCGWINSZ, &ws);
	Py_END_ALLOW_THREADS

	rob = PyTuple_New(2);

	return(rob);
}

#define PYTHON_TYPES()

#define MODULE_FUNCTIONS() \
	PYMETHOD(dimensions, dimensions, METH_NOARGS, "get the dimensions of the tty")

#include <fault/python/module.h>
INIT(PyDoc_STR("TTY C-API"))
{
	PyObj mod = NULL;

	CREATE_MODULE(&mod);
	if (mod == NULL)
		return(NULL); XCOVERAGE

	/*
	 * Initialize Transit types.
	 */
	#define ID(NAME) \
		if (PyType_Ready((PyTypeObject *) &( NAME##Type ))) \
			goto error; \
		if (PyModule_AddObject(mod, #NAME, (PyObj) &( NAME##Type )) < 0) \
			goto error;
		PYTHON_TYPES()
	#undef ID

	return(mod);
error:
	DROP_MODULE(mod);
	return(NULL);
}
/*
 * vim: ts=3:sw=3:noet:
 */
