from deep_translator import GoogleTranslator

text = input("Enter text: ")

translated = GoogleTranslator(
    source="en",
    target="hi"
).translate(text)

print("\nTranslated:")
print(translated)