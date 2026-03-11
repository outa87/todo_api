name = input("あなたの名前を入力してね:")
age  = int(input("あなたの年齢を入力してね"))

if age >=18:
    print(f"{name}は大人だよ")
else:
    print(f"{name}は未成年だよ")

my_name = input("私の名前を決めてね:")
print(f"こんにちは、{name}。私の名前は{my_name}、よろしくね。")

count = 0

for i in range(1, 51):
    if i % 2 == 1:
        count = count + 1

print(count)

a = int(input("何回筋トレがいいですか？回数を入力してください"))

for rep in range(1,a + 1):
    print("筋トレしろ")









     