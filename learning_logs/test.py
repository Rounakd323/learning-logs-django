from mini_vader import MiniVader

an = MiniVader()
print(an.analyze("This movie was not good"))    # likely negative
print(an.analyze("The food was EXCELLENT!!!"))  # strongly positive
print(an.analyze("It was okay, but the ending was AMAZING"))  # handles 'but'
print(an.analyze("I am so sad 😭"))             # emoji adds negative weight
