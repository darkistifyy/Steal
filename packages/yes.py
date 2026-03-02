import pkg_resources

installed_packages = [
    f"{d.project_name}=={d.version}" for d in pkg_resources.working_set
]

with open("packages.txt", "w+") as fp:
    for package in installed_packages:
        fp.writelines(f"{package}\n")

print(installed_packages)
