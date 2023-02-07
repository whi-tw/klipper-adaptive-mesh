class BedMesh:
    mesh_min = (25, 25)
    mesh_max = (275, 275)
    probe_count = (7, 7)


class Settings:
    bed_mesh = BedMesh()


class ConfigFile:
    settings = Settings()


class ExcludeObject:
    objects = []


class Printer:
    configfile = ConfigFile()
    exclude_object = ExcludeObject()
