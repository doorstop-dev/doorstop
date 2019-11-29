# SPDX-License-Identifier: LGPL-3.0-only

"""Validation of an item's YAML representation."""


class YamlValidator:
    """Validates the schema of the Item's YAML file."""

    @staticmethod
    def validate_item_yaml(item_dict):
        """Validate a dictionary of item's attributes read from YAML."""
        for key, value in item_dict.items():
            if key == 'references':
                if value is None:
                    raise AttributeError(
                        "'references' must be an array with at least one reference element"
                    )

                if not isinstance(value, list):
                    raise AttributeError("'references' must be an array")

                for ref_dict in value:
                    if not isinstance(ref_dict, dict):
                        raise AttributeError("'references' member must be a dictionary")

                    ref_keys = ref_dict.keys()
                    if 'type' not in ref_keys:
                        raise AttributeError(
                            "'references' member must have a 'type' key"
                        )
                    if 'path' not in ref_keys:
                        raise AttributeError(
                            "'references' member must have a 'path' key"
                        )

                    ref_type = ref_dict['type']
                    if ref_type != 'file':
                        raise AttributeError(
                            "'references' member's 'type' value must be a 'file'"
                        )

                    ref_path = ref_dict['path']
                    if not isinstance(ref_path, str):
                        raise AttributeError(
                            "'references' member's path must be a string value"
                        )

                    if 'keyword' in ref_dict:
                        keyword = ref_dict['keyword']
                        if not isinstance(keyword, str):
                            raise AttributeError(
                                "'references' member's 'keyword' must be a string value"
                            )

        return True
