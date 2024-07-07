import json

# Открываем оригинальный файл с фикстурой
with open('ingredients.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Преобразуем данные в необходимый формат
formatted_data = []
for i, item in enumerate(data, start=1):
    formatted_data.append({
        "model": "receipts.ingredient",
        "pk": i,
        "fields": item
    })

# Сохраняем преобразованные данные в новый файл
with open('formatted_ingredients.json', 'w', encoding='utf-8') as file:
    json.dump(formatted_data, file, ensure_ascii=False, indent=4)

print("Фикстура преобразована и сохранена в файл formatted_ingredients.json")
