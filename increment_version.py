import os
from version import VERSION

if __name__ == '__main__':
    base_path = os.path.dirname(os.path.abspath(__file__))
    version_file = os.path.join(base_path, 'version.py')
    major, minor = VERSION.split('.')
    minor = int(minor) + 1
    with open(version_file, 'w') as v_file:
        v_file.write("VERSION='%s.%s'" % (major, minor))
    print("{}.{}".format(major, minor))
