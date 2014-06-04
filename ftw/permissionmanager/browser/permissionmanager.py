from Products.Five import BrowserView


class PermissionManager(BrowserView):

    def __call__(self, *args, **kwargs):
        self.request.set('disable_border', True)
        return super(PermissionManager, self).__call__(*args, **kwargs)
