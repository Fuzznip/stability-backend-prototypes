from sqlalchemy.orm.attributes import flag_modified

def update_jsonb_field(instance, field_name, update_func):
    """
    Helper function to update a JSONB field and mark it as modified.

    Args:
        instance: The SQLAlchemy model instance containing the JSONB field.
        field_name: The name of the JSONB field to update.
        update_func: A function that takes the current value of the field and modifies it.
    """
    field_value = getattr(instance, field_name)
    update_func(field_value)
    flag_modified(instance, field_name)
