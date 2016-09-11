/**
	Low level tty access and terminal control.

	Tools for working with teletype devices.
*/
#include <sys/ttycom.h>
#include <sys/ioctl.h>

#include <fault/libc.h>
#include <fault/internal.h>
#include <fault/python/environ.h>

static PyObj
set_controlling_process_group(PyObj self, PyObj args)
{
	int fd, r = 0;
	long pgid;

	if (!PyArg_ParseTuple(args, "il", &fd, &pgid))
		return(NULL);

	if (tcsetpgrp(fd, (pid_t) pgid))
	{
		/* errno set */
		return(PyErr_SetFromErrno(PyExc_OSError));
	}

	Py_RETURN_NONE;
}

static PyObj
dimensions(PyObject *self, PyObject *args)
{
	struct winsize ws;
	int fd, r = 0;
	PyObj rob, h, v;

	if (!PyArg_ParseTuple(args, "i", &fd))
		return(NULL);

	Py_BEGIN_ALLOW_THREADS
	r = ioctl((int) fd, TIOCGWINSZ, &ws);
	Py_END_ALLOW_THREADS

	if (r)
		return(PyErr_SetFromErrno(PyExc_OSError));

	h = PyLong_FromLong(ws.ws_col);
	if (h == NULL)
		return(NULL);
	v = PyLong_FromLong(ws.ws_row);
	if (v == NULL)
		goto herror;

	rob = PyTuple_New(2);
	if (rob == NULL)
		goto error;

	PyTuple_SET_ITEM(rob, 0, h);
	PyTuple_SET_ITEM(rob, 1, v);

	return(rob);

	error:
		Py_DECREF(v);
	herror:
		Py_DECREF(h);

	return(NULL);
}

#define PYTHON_TYPES()

#define scpg_doc "Set the controlling process ground using (system:if)`tcsetpgrp`."

#define MODULE_FUNCTIONS() \
	PYMETHOD(dimensions, dimensions, METH_VARARGS, "get the dimensions of the tty") \
	PYMETHOD(set_controlling_process_group, set_controlling_process_group, METH_VARARGS, scpg_doc)

#include <fault/python/module.h>
INIT(PyDoc_STR("TTY C-API"))
{
	PyObj mod = NULL;

	CREATE_MODULE(&mod);
	if (mod == NULL)
		return(NULL);

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
