# marked for deletion
import os.path
import socket
import getpass

def gather(environment = '::'):
	'gather basic context about the system'
	user = getpass.getuser()
	pwd = os.path.realpath(os.curdir)
	hostname = socket.gethostname()

	if pwd == os.path.expanduser('~'):
		pwd = '~'
	else:
		pwd = '/'.join(pwd.split('/')[-3:])

	return {
		'depth': int(os.environ.get('SHLVL', 0)) - 1,
		'user': user,
		'host': hostname.split('.')[0],
		'env' : environment,
		'path': pwd,
	}
