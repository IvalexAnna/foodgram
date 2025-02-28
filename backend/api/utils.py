from datetime import date

from django.utils.formats import date_format

from .constants import (DATE_FORMAT,
                        HEADER_ROW,
                        INGREDIENT_ROW,
                        LETTER_COUNT,
                        RECIPES_ROW
                    )


def generate_shopping_list(user_data, recipe_list, ingredient_list):
    """
    Генерирует текстовый список покупок для заданных рецептов и ингредиентов.
    """

    return "\n".join(
        [
            HEADER_ROW.format(user_data.username,
                              date_format(date.today(),
                                          DATE_FORMAT)),
            "Продукты:",
            *[
                INGREDIENT_ROW.format(
                    index,
                    ingredient.name.capitalize(),
                    ingredient.total_amount,
                    ingredient.measurement_unit,
                )
                for index, ingredient in enumerate(ingredient_list, 1)
            ],
            "Рецепты:",
            *[
                RECIPES_ROW.format(recipe.name[:LETTER_COUNT],
                                   recipe.author.username)
                for recipe in recipe_list
            ],
        ]
    )
