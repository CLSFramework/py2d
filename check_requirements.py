import sys
from importlib.metadata import version, PackageNotFoundError
from packaging.requirements import Requirement
from packaging.version import Version

def check_requirements(requirements_file='requirements.txt'):
    with open(requirements_file, 'r') as file:
        requirements = file.readlines()

        for requirement_line in requirements:
            requirement_line = requirement_line.strip()
            if not requirement_line or requirement_line.startswith('#'):
                continue

            try:
                req = Requirement(requirement_line)
                try:
                    # Get installed version
                    installed_version = version(req.name)
                    installed = Version(installed_version)

                    # Check if versions matches
                    if req.specifier and not req.specifier.contains(installed):
                        print(f"WARNING: Version conflict for {req.name}. "
                          f"Required: {req.specifier}, installed: {installed_version}")
                    
                except PackageNotFoundError:
                    print(f"ERROR: Package {req.name} not found")
                    sys.exit(1)
                
            except Exception as e:
                print(f"WARNING: Could not parse requirement '{requirement_line}': {str(e)}")

if __name__ == "__main__":
    check_requirements()
