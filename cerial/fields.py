import cPickle
try:
    from django.utils import simplejson as json
except ImportError:
    import json
from django.db import models
from .serializers import SortedJSONEncoder


class CerialField(models.TextField):
    def loads(self, s):
        """
        Deserialize s
        """
        raise NotImplemented

    def dumps(self, obj):
        """
        Serialize obj
        """
        raise NotImplemented
        
    def value_from_object(self, obj):
        return self.dumps(super(CerialField, self).value_from_object(obj))

    def value_to_string(self, obj):
        return self.dumps(obj.__dict__[self.name])

    def pre_save(self, obj, create):
        value = obj.__dict__[self.name]
        if value is None and self.null:
            return value
        if isinstance(value, basestring):
            #Test deserializing string. Failure means it needs to be serialized
            #as a string
            try:
                self.loads(value)
            except Exception:
                pass
            else:
                return value
        return self.dumps(value)

    def contribute_to_class(self, cls, name):
        super(CerialField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, CerialDescriptor(self))

    def south_field_triple(self):
        from south.modelsinspector import introspector
        args, kwargs = introspector(self)
        return 'django.db.models.TextField', args, kwargs


class CerialDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, obj, owner):
        value = obj.__dict__[self.field.name]
        # we don't try to deserialize empty strings
        if value and isinstance(value, basestring):
            value = self.field.loads(value)
            obj.__dict__[self.field.name] = value
        return value

    def __set__(self, obj, value):
        obj.__dict__[self.field.name] = value


class JSONField(CerialField):
    def loads(self, s):
        return json.loads(s)

    def dumps(self, obj):
        return json.dumps(obj, cls=SortedJSONEncoder)


class PickleField(CerialField):
    def loads(self, s):
        return cPickle.loads(str(s).decode('base64'))

    def dumps(self, obj):
        return cPickle.dumps(obj).encode('base64')

