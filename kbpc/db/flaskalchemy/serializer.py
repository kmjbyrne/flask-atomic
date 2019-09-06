def get_columns(instance) -> set:
    """
    Pulls all the column keys from an instance
    :param instance: model instance
    :return: set of column keys
    :rtype: set
    """

    return set([col for col in instance.__mapper__.columns.keys()])


def merge_column_sets(columns: set, exclusions: set) -> set:
    """
    Take the column set and subtract the exclusions.
    :param columns: set of columns on the instance
    :param exclusions: set of columns we want to ignore
    :return: set of finalised columns for publication
    :rtype: set
    """

    exclusion_instance = type(exclusions)
    approved_types = [type([]), type(set()), type(())]
    print(exclusion_instance)
    if exclusion_instance not in approved_types:
        raise ValueError('Library requires exclusions to be a iterable object (Supporting: list, tuple or set)')

    return columns.difference(exclusions)


def serialize(instance, exclusions=None) -> dict:
    """
    Extracts a dictionary representation of a SQLAlchemy model instance
    :param instance: raw SQLAlchemy model instance
    :param exclusions: list of columns to be excluded
    :return: dictionary representation of a model
    :rtype: dict
    """

    # Define our model properties here. Columns and Schema relationships
    columns = get_columns(instance)
    resp = {}

    if exclusions is None:
        exclusions = set()

    end_columns = columns.difference(exclusions)

    # First lets map the basic model attributes to key value pairs
    for column in end_columns:
        resp[column] = getattr(instance, column)
    return resp


def unpack(instance: {}, exclusions=None, include_relationship=False) -> dict:
    """
    This utility function dynamically converts Alchemy model classes into a dict using introspective lookups.
    This saves on manually mapping each model and all the fields. However, exclusions should be noted.
    Such as passwords and protected properties.
    :param instance: SQLAlchemy Model definition
    :param exclusions: list of attributes which should not be processed and returned
    :param include_relationship: whether to dive into and convert related models also
    :return: dictionary of defined attributes
    :rtype: dict
    """

    if exclusions is None:
        exclusions = dict()

    model = convert(instance, exclusions.get(get_tablename(instance), set()))

    if include_relationship:
        relationships = get_relationship_keys(instance)
        # Now map the relationships
        for relationship in relationships:
            model[relationship] = convert(
                getattr(instance, relationship), exclusions.get(get_tablename(instance), set())
            )
    return model


def get_tablename(instance: dict) -> str:
    return instance.__tablename__


def get_relationship_keys(instance: dict) -> list:
    """
    Pulls relationship keys from model instance. Assumes FlaskAlchemy code uses __mapper__. This has to be exposed
    in order to effectively pull out the relationship keys bound to the instance.
    :param instance: input model instance
    :return: list of keys
    :rtype: list
    """

    return instance.__mapper__.relationships.keys()
