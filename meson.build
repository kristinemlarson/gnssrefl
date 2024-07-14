project(
  'gnssrefl',
  'fortran', 'c',
  license: 'GPL-3.0-only',
)

py = import('python').find_installation()

gpssnr = custom_target(
  'gpssnr',
  input: 'gnssrefl/gpssnr.f',
  output: 'gpssnrmodule.c',
  install_dir: 'gnssrefl',
  command: [py, '-m', 'numpy.f2py', '@INPUT@', '-m', 'gpssnr', '--backend', 'meson']
)

py.extension_module(
  'gnssrefl.gpssnr',
  [
    'gpssnr.f',
    gpssnr,
  ],
  install: true
)
