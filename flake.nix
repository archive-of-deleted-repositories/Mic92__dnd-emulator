{
  description = "D&D Emulator with Claude as Game Master";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
  };

  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];

      perSystem = { pkgs, ... }:
        let
          # Override claude-code to mark it as free
          claude-code = pkgs.claude-code.overrideAttrs (oldAttrs: {
            meta = oldAttrs.meta // { license = pkgs.lib.licenses.free; };
          });
        in
        {
          devShells.default = pkgs.mkShell {
            buildInputs = [
              pkgs.python3
              pkgs.uv
              pkgs.ruff

              # For Claude CLI
              claude-code

              # For running development servers
              pkgs.process-compose
              pkgs.nodejs
            ];

            shellHook = ''
              echo "D&D Emulator Development Environment"
              echo "Python: ${pkgs.python3.version}"
              echo ""
              echo "Commands:"
              echo "  uv sync                            - Install dependencies"
              echo "  nix develop -c process-compose     - Run the app (both backend and frontend)"
              echo "  ruff format .                      - Format all files"
              echo "  ruff check --fix --unsafe-fixes .  - Lint Python code"
              echo "  nix develop -c uv run mypy .       - Type check Python code"
              echo ""
              echo "Frontend commands (run from frontend/ directory):"
              echo "  npm install                        - Install frontend dependencies"
              echo "  npm run dev                        - Start frontend dev server"
              echo "  npm run lint                       - Check TypeScript code with ESLint"
              echo "  npm run lint:fix                   - Fix linting and formatting issues"
              echo "  npm run build                      - Build for production"
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
