numbers = [12, 7, 25, 3, 18]
big = float("-inf")
index = -1

for i in range(len(numbers)):
    
    if numbers[i] > big:
        big = numbers[i]
        index = i

print(big)
print(index)
