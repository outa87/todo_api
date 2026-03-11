numbers = [1, 2, 2, 3, 3, 3,]

counts = {}

for num in numbers:
    
    if num in counts:
        counts[num] += 1 #中身を更新

    else:
        counts[num] = 1 # 新しく作る

print(counts)