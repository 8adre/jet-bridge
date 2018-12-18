from responses.base import Response


class DestroyAPIViewMixin(object):

    def delete(self, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        self.write_response(Response(status=status.HTTP_204_NO_CONTENT))

    def perform_destroy(self, instance):
        instance.delete()
