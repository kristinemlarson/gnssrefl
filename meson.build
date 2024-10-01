project(
  'gnssrefl',
  'fortran', 'c',
  license: 'GPL-3.0-only',
)

py = import('python').find_installation(pure: false)
dep_python = py.dependency()

py_files = run_command('find', 'gnssrefl', '-name', '*.py', check: true).stdout().strip().split('\n')

py.install_sources(py_files, subdir: 'gnssrefl')

lib_names = ['gpssnr', 'gnsssnr', 'gnsssnrbigger', 'xnmeasnr']
libs = {}

foreach lib_name : lib_names
  libs += {lib_name: custom_target(
    lib_name,
    input: f'gnssrefl/@lib_name@.f',
    output: [f'@lib_name@module.c', f'@lib_name@-f2pywrappers.f'],
    install_dir: 'gnssrefl',
    command: [py, '-m', 'numpy.f2py', '@INPUT@', '-m', lib_name, '--backend', 'meson', '--lower']
  )}
endforeach

inc_numpy = run_command(py, '-c', 'import numpy; print(numpy.get_include())', check: true).stdout().strip()
inc_f2py = run_command(py, '-c', 'import numpy.f2py; print(numpy.f2py.get_include())', check: true).stdout().strip()

dep_numpy = declare_dependency(include_directories: include_directories(inc_numpy))
dep_f2py = declare_dependency(include_directories: include_directories(inc_f2py))

foreach lib_name, lib : libs
  py.extension_module(
    lib_name,
    [
      f'gnssrefl/@lib_name@.f',
      lib,
    ],
    inc_f2py / 'fortranobject.c',
    subdir: 'gnssrefl',
    dependencies: [dep_python, dep_numpy, dep_f2py],
    install: true,
  )
endforeach
