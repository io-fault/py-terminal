/*
 * Cell usage count for string display.
 */
#include <wchar.h>
#include <fault/roles.h>
#include <fault/python/environ.h>
#include <fault/python/module.h>

static PyObj
cells(PyObj self, PyObj str)
{
	int width;
	wchar_t *wstr;
	Py_ssize_t size;

	if (!PyUnicode_Check(str))
	{
		PyErr_Format(PyExc_ValueError, "second argument must be str");
		return(NULL);
	}

	if (PyUnicode_IS_ASCII(str))
	{
		return(PyLong_FromSsize_t(PyUnicode_GET_SIZE(str)));
	}

	wstr = PyUnicode_AsWideCharString(str, &size);
	if (wstr == NULL)
		return(NULL);

	width = wcswidth(wstr, (size_t) size);

	PyMem_Free(wstr);

	return(PyLong_FromLong((long) width));
}

/* METH_O, METH_VARARGS, METH_VARKEYWORDS, METH_NOARGS */
METHODS() = {
	{"cells", (PyCFunction) cells, METH_O,
		PyDoc_STR("get the number of cells the given unicode string requires for display")},
	{NULL}
};

INIT("functions for calculating the number of cells used by a unicode string for display")
{
	PyObj mod = NULL;

	CREATE_MODULE(&mod);
	if (mod == NULL)
		return(NULL);

	return(mod);

fail:
	DROP_MODULE(mod);
	return(NULL);
}
/*
 * vim: ts=3:sw=3:noet:
 */
