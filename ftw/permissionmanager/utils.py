from Acquisition import aq_chain


def update_security_of_objects(objects):
    objects = set(objects)
    for obj in objects.copy():
        parents = set(aq_chain(obj)[1:])
        if parents & objects:
            objects.remove(obj)

    for obj in objects:
        obj.reindexObjectSecurity()
