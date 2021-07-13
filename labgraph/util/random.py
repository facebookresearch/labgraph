#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import random
import string


def random_string(
    length: int, characters: str = string.ascii_letters + string.digits
) -> str:
    """
    Generates a random string of a given length from a given character set.

    Args:
        length: The length of the string to generate.
        characters: A string containing characters to choose from.
    """
    return "".join(random.choice(characters) for _ in range(length))
