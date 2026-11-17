fs = import('fs')

if frida_core_dep.type_name() == 'internal'
  frida_core_subprj = subproject('frida-core')
  frida_core_lib = frida_core_subprj.get_variable('core_public_lib')
  frida_core_header = frida_core_subprj.get_variable('core_public_h')
else
  frida_core_lib = frida_core_dep
  frida_core_includedir = frida_core_dep.get_variable('frida_includedir')
  if fs.exists(frida_core_includedir / 'frida-core.h')
    frida_core_header = frida_core_includedir / 'frida-core.h'
  else
    frida_core_header = frida_core_includedir / 'frida-1.0' / 'frida-core.h'
  endif
endif

host_system = host_machine.system()

glib_archive_args = []
if host_system != 'windows'
  glib_libdir = dependency('glib-2.0').get_variable('libdir')
  glib_archive_args += ['--nm', find_program('nm')]
  foreach name : ['glib-2.0', 'gobject-2.0', 'gio-2.0']
    glib_archive_args += ['--archive', glib_libdir / f'lib@name@.a']
  endforeach
endif

exports = custom_target('frida-exports',
  input: [frida_core_header, 'glib.exports'],
  output: ['Frida.def', 'Frida.version', 'Frida.symbols', 'frida-exports.c'],
  command: [
    find_program('python3'),
    files('generate-exports.py'),
    '--core-header', '@INPUT0@',
    '--glib-exports', '@INPUT1@',
    glib_archive_args,
    '--output-def', '@OUTPUT0@',
    '--output-version-script', '@OUTPUT1@',
    '--output-symbol-list', '@OUTPUT2@',
    '--output-references', '@OUTPUT3@',
  ],
)

wrapper_sources = files('frida-wrapper.c') + [exports[3]]

frida_dll_kwargs = {}
if host_system == 'windows'
  frida_dll_kwargs += {'vs_module_defs': exports[0]}
elif host_system == 'darwin'
  frida_dll_kwargs += {
    'link_args': ['-Wl,-exported_symbols_list,' + exports[2].full_path()],
    'link_depends': exports[2],
  }
else
  frida_dll_kwargs += {
    'link_args': ['-Wl,--version-script,' + exports[1].full_path()],
    'link_depends': exports[1],
  }
endif

frida_dll = shared_library(
  'Frida',
  wrapper_sources,
  name_prefix: '',
  dependencies: [ frida_core_dep ],
  kwargs: frida_dll_kwargs
)

host_cpu = host_machine.cpu_family()
host_os = host_machine.system()

dotnet_platform = ''

if host_os == 'linux'
  if host_cpu == 'x86'
    dotnet_platform = 'linux-x86'
  elif host_cpu == 'x86_64'
    dotnet_platform = 'linux-x86_64'
  elif host_cpu == 'arm'
    dotnet_platform = 'linux-armhf'
  elif host_cpu == 'aarch64'
    dotnet_platform = 'linux-arm64'
  elif host_cpu == 'mips64'
    dotnet_platform = 'linux-mips64'
  endif
elif host_os == 'windows'
  if host_cpu == 'x86'
    dotnet_platform = 'win-x86'
  elif host_cpu == 'x86_64'
    dotnet_platform = 'win-x86_64'
  elif host_cpu == 'aarch64'
    dotnet_platform = 'win-arm64'
  endif
elif host_os == 'darwin'
  dotnet_platform = host_cpu == 'x86_64' ? 'macos-x86_64' : 'macos-arm64'
endif

rid = {
  'win-x86': 'win-x86',
  'win-x86_64': 'win-x64',
  'win-arm64': 'win-arm64',
  'macos-x86_64': 'osx-x64',
  'macos-arm64': 'osx-arm64',
  'linux-x86': 'linux-x86',
  'linux-x86_64': 'linux-x64',
  'linux-armhf': 'linux-arm32',
  'linux-arm64': 'linux-arm64',
  'linux-mips64': 'linux-mips64',
}[dotnet_platform]
library_runtime_output = 'Frida.NET.Runtime.' + rid + '.' + meson.project_version() + '.nupkg'

build_library_runtime = custom_target(
  'build-runtime',
  build_by_default: true,
  input: [
    fs.copyfile('Frida.NET.Runtime.csproj', 'Frida.NET.Runtime.csproj')
  ],
  output: library_runtime_output,
  depends: [frida_dll],
  command: [
    'dotnet',
    'pack',
    '-o', meson.current_build_dir(),
    '-c', 'Release',
    '-p:VersionPrefix=' + meson.project_version(),
    '-p:Platform=' + dotnet_platform,
    '@INPUT0@'
  ]
)