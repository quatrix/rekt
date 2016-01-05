import click
import time
import string
import random
import fcntl
import os
import logging
import sys

from contextlib import contextmanager

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

@contextmanager
def flocked(fd):
    """ Locks FD before entering the context, always releasing the lock. """
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)


def gen_rand_string(l):
	return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(l))


@click.command()
@click.option('--work-dir')
@click.option('--session-id')
@click.option('--length', type=int)
@click.option('--delay', type=float)
@click.option('--chunk-size', default=8096)
def main(work_dir, session_id, length, delay, chunk_size):
	filename = os.path.join(work_dir, '{}.mp3'.format(session_id))

	with open(filename, 'wb') as f:
		logging.info('opened {} for writing, getting lock...'.format(filename))
		with flocked(f):
			logging.info('locked')
			while length != 0:
				to_write = min(chunk_size, length)
				f.write(gen_rand_string(to_write))
				length -= to_write
				logging.info('written {}/{}'.format(to_write, length))
				logging.info('sleeping for {} sec'.format(delay))
				time.sleep(delay)


if __name__ == '__main__':
	main()
