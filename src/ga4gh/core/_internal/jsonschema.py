"""Support for JSON Schema and GA4GH schema conventions using
python-jsonschema-objects

"""

import logging

import python_jsonschema_objects as pjs

_logger = logging.getLogger(__name__)


############################################################################
# Schema Functions

def build_models(path, standardize_names):
    """load models from json schema at path"""
    builder = pjs.ObjectBuilder(path)
    models = builder.build_classes(standardize_names=False)
    return models


def build_class_referable_attribute_map(models):
    """given a set of json schema models (as from build_models()), return
    a map of classes ⇒ referrable attributes

    The practical meaning is to define a map like
       {"Allele": ["location"], ...}
    for any json schema class that has one or more attributes
    that may be either an object or a CURIE.

    """
    cra_map = {cn: get_referable_attributes(models[cn]) for cn in models}
    return {cn: refatts for cn, refatts in cra_map.items()
            if refatts}


def get_referable_attributes(cls):

    """for a given pjs class, return list of attributes that may be either
    objects or CURIEs

    ie, a list of attributes that may be inlined objects or references
    to them

    """
    if not is_pjs_class(cls):
        return None
    atts = cls.__prop_names__
    refatts = [att for att in atts if is_referable(cls.propinfo(att))]
    return refatts


def is_referable(json_subschema):
    """return True if field is a referable object, or a list of referable
    objects

    """

    if "oneOf" in json_subschema:
        # schema is oneOf of a CURIE and non-CURIE type
        refs = [oo.get("$ref", None) for oo in json_subschema["oneOf"]]
        return (any(r.endswith("/CURIE") for r in refs)
                    and any(not r.endswith("/CURIE") for r in refs))

    if "type" in json_subschema:
        t = json_subschema["type"]
        if t == "array":
            # an array of referable types
            return is_referable(json_subschema["items"])

    return False





############################################################################
# Class Functions

def is_pjs_class(k):
    return pjs.classbuilder.ProtocolBase in k.__mro__


############################################################################
# Instance/object Functions

def is_pjs_instance(o):
    """return True if object is a python jsonschema object"""
    return isinstance(o, pjs.classbuilder.ProtocolBase)


############################################################################
# Attribute Functions

def is_curie(o):
    """return True if object is a python jsonschema class that represents
    a CURIE, e.g., sequence_id"""
    return o.__class__.__name__.endswith("/CURIE")


def is_identifiable(o):
    """return True if object is identifiable

    An object is considered identifiable if it contains an `_id` attribute
    """
    return is_pjs_instance(o) and ("_id" in o)


def is_literal(o):
    """return True if object is a python jsonschema object literal"""
    return isinstance(o, pjs.literals.LiteralValue)


def is_array(o):
    """return True if object is a python jsonschema object array"""
    return getattr(o, "type", None) == "array"
