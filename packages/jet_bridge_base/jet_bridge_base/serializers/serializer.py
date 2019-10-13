from collections import OrderedDict, Mapping, Iterable
import six

from jet_bridge_base.exceptions.validation_error import ValidationError
from jet_bridge_base.fields.field import Field, empty


class SerializerMetaclass(type):

    @classmethod
    def _get_declared_fields(cls, bases, attrs):
        fields = [(field_name, attrs.pop(field_name))
                  for field_name, obj in list(attrs.items())
                  if isinstance(obj, Field)]
        fields.sort(key=lambda x: x[1].creation_counter)

        for base in reversed(bases):
            if hasattr(base, '_declared_fields'):
                fields = [
                    (field_name, obj) for field_name, obj
                    in base._declared_fields.items()
                    if field_name not in attrs
                ] + fields

        return OrderedDict(fields)

    def __new__(cls, name, bases, attrs):
        attrs['_declared_fields'] = cls._get_declared_fields(bases, attrs)
        return super(SerializerMetaclass, cls).__new__(cls, name, bases, attrs)


@six.add_metaclass(SerializerMetaclass)
class Serializer(Field):
    validated_data = None
    fields = []
    errors = None

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        self.data = kwargs.pop('data', None)
        self.meta = getattr(self, 'Meta', None)
        self.partial = kwargs.pop('partial', False)
        super(Serializer, self).__init__(*args, **kwargs)
        self.update_fields()

    def update_fields(self):
        fields = []

        if hasattr(self.meta, 'fields'):
            for field_name in self.meta.fields:
                assert field_name in self._declared_fields, (
                    'No such field %s for serializer %s' % (field_name, self.__class__.__name__)
                )
                field = self._declared_fields.get(field_name)
                field.field_name = field_name
                fields.append(field)

        if hasattr(self.meta, 'dynamic_fields'):
            for field_name, field in self.meta.dynamic_fields.items():
                field.field_name = field_name
                fields.append(field)

        for field_name in dir(self):
            field = self._declared_fields.get(field_name)

            if not isinstance(field, Field):
                continue

            field.field_name = field_name
            fields.append(field)

        self.fields = fields

    @property
    def readable_fields(self):
        if not self.fields or not isinstance(self.fields, Iterable):
            return []
        return list(filter(lambda x: not x.write_only, self.fields))

    @property
    def writable_fields(self):
        if not self.fields or not isinstance(self.fields, Iterable):
            return []
        return list(filter(lambda x: not x.read_only, self.fields))

    def run_validation(self, value):
        value = self.to_internal_value(value)
        return value

    def is_valid(self, raise_exception=False):
        try:
            self.validated_data = self.run_validation(self.data)
            self.errors = None
        except ValidationError as e:
            self.validated_data = None
            self.errors = e.detail

        if self.errors and raise_exception:
            raise ValidationError(self.errors)

        return not bool(self.errors)

    def to_internal_value_item(self, value):
        result = OrderedDict()
        errors = OrderedDict()

        for field in self.writable_fields:
            field_value = field.get_value(value)

            if field.field_name not in value.keys() and self.partial:
                continue

            validate_method = getattr(self, 'validate_' + field.field_name, None)

            try:
                validated_value = field.run_validation(field_value)
                if validate_method is not None:
                    validated_value = validate_method(validated_value)
                result[field.field_name] = validated_value
            except ValidationError as e:
                errors[field.field_name] = e.detail

        if errors:
            raise ValidationError(errors)

        return result

    def to_representation_item(self, value):
        result = OrderedDict()

        for field in self.readable_fields:
            if isinstance(value, Mapping):
                field_value = value[field.field_name]
            else:
                field_value = getattr(value, field.field_name)

            result[field.field_name] = field.to_representation(field_value)

        return result

    @property
    def representation_data(self):
        if self.instance is not None:
            return self.to_representation(self.instance)
        elif self.validated_data is not None:
            return self.to_representation(self.validated_data)

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    def create(self, validated_data):
        raise NotImplementedError('`create()` must be implemented.')

    def save(self, **kwargs):
        assert not self.errors, (
            'You cannot call `.save()` on a serializer with invalid data.'
        )

        validated_data = dict(
            list(self.validated_data.items()) +
            list(kwargs.items())
        )

        if self.instance is not None:
            self.instance = self.update(self.instance, validated_data)
            assert self.instance is not None, (
                '`update()` did not return an object instance.'
            )
        else:
            self.instance = self.create(validated_data)
            assert self.instance is not None, (
                '`create()` did not return an object instance.'
            )

        return self.instance
