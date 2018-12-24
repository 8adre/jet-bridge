from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker

from filters.model import get_model_filter_class
from serializers.model import get_model_serializer
from serializers.model_description import ModelDescriptionSerializer
from views.base.generic_api import GenericAPIView
from views.mixins.list import ListAPIViewMixin
from views.mixins.retrieve import RetrieveAPIViewMixin

engine = create_engine('postgresql://postgres:password@localhost:5432/jetty')
Session = sessionmaker(bind=engine)


class ModelHandler(ListAPIViewMixin, RetrieveAPIViewMixin, GenericAPIView):
    model = None
    serializer_class = ModelDescriptionSerializer

    def get_model(self):
        if self.model:
            return self.model

        metadata = MetaData()
        metadata.reflect(engine)
        Base = automap_base(metadata=metadata)

        Base.prepare()
        self.model = Base.classes[self.path_kwargs['model']]

        return self.model

    def get_serializer_class(self):
        Model = self.get_model()
        return get_model_serializer(Model)

    def get_filter_class(self):
        return get_model_filter_class(self.get_model())

    def get_queryset(self):
        session = Session()
        Model = self.get_model()

        return session.query(Model)
