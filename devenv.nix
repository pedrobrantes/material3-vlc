{ pkgs, lib, ... }:

{
  # Avoid trusted-users error when devenv.cachix.org is not configured in /etc/nix/nix.conf
  cachix.enable = false;

  languages.python = {
    enable = true;
    uv.enable = true;
  };

  packages = [
    pkgs.zlib
    pkgs.stdenv.cc.cc.lib
    pkgs.git
  ];

  # Expose native shared libs for Python wheels (lxml, pillow, resvg-py, materialyoucolor)
  env.LD_LIBRARY_PATH = lib.makeLibraryPath [
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
  ];

  enterShell = ''
    echo "material3-vlc development environment"
    python --version
    uv --version
  '';
}
