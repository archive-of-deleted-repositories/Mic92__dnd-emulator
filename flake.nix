{
  description = "D&D Emulator with Claude as Game Master";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    treefmt-nix.url = "github:numtide/treefmt-nix";
  };

  outputs = inputs@{ self, nixpkgs, flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];

      imports = [
        inputs.treefmt-nix.flakeModule
      ];

      perSystem = { config, self', inputs', pkgs, system, ... }:
        let
          python = pkgs.python313;
          pythonEnv = python.withPackages (ps: with ps; [
            # Dependencies will be managed by uv
          ]);

          # Override claude-code to mark it as free
          claude-code = pkgs.claude-code.overrideAttrs (oldAttrs: {
            meta = oldAttrs.meta // { license = pkgs.lib.licenses.free; };
          });
        in
        {
          # Formatter configuration
          treefmt = {
            projectRootFile = "flake.nix";
            programs = {
              ruff = {
                enable = true;
                check = true;
              };
              nixpkgs-fmt.enable = true;
              prettier = {
                enable = true;
                includes = [
                  "*.md"
                  "*.json"
                  "*.yml"
                  "*.yaml"
                  "*.html"
                  "*.css"
                  "*.js"
                ];
              };
            };
          };

          devShells.default = pkgs.mkShell {
            buildInputs = with pkgs; [
              pythonEnv
              uv
              ruff
              mypy

              # Additional tools
              fd
              ripgrep
              dnsutils
              lsof
              gh
              tea

              # For Claude CLI
              claude-code

              # Formatting
              config.treefmt.build.wrapper
            ];

            shellHook = ''
              echo "D&D Emulator Development Environment"
              echo "Python: ${python.version}"
              echo "uv: $(uv --version)"
              echo ""
              echo "Commands:"
              echo "  uv sync          - Install dependencies"
              echo "  uv run python app.py - Run the app"
              echo "  treefmt          - Format all files"
              echo "  ruff check .     - Lint Python code"
              echo "  mypy .           - Type check Python code"
            '';
          };

          packages.default = pkgs.python313Packages.buildPythonPackage {
            pname = "dnd-emulator";
            version = "0.1.0";
            src = ./.;
            format = "pyproject";

            propagatedBuildInputs = with pkgs.python313Packages; [
              flask
              flask-socketio
              python-socketio
              flask-cors
              python-dotenv
            ];
          };
        };
    };
}
